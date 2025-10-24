import * as cdk from 'aws-cdk-lib';
import {
  Repository
} from 'aws-cdk-lib/aws-ecr'
import path from 'path';

import {
  bedrock_agentcore as agentcore
} from "@krokoko/agentcore-cdk-constructs"

import * as bedrock from '@aws-cdk/aws-bedrock-alpha';


import {
  RemovalPolicy,
  Stack,
  StackProps,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { 
  Bucket, 
  BucketEncryption 
} from 'aws-cdk-lib/aws-s3';
import { 
  Effect,
  AnyPrincipal
} from 'aws-cdk-lib/aws-iam';
import {
  BedrockAgentCoreRuntimeAgent,
} from 'bedrock-agentcore-cdk-constructs';
import { notEqual } from 'assert';
import { open } from 'fs';

type OpenApiConfig = {
  description: string
  apiName: string
  schemaPath: string
  providerArn: string,
  secretArn: string
  credentialProviderParamName: string
}

type EnvVars = {
  [key: string]: string;
}

type AgentConfig = {
  agentName: string
  sourcePath: string
  envVars: EnvVars
}

interface AgentCoreDevelopmentProps extends StackProps {
  openApiConfigs: OpenApiConfig[]
  agentConfigs: AgentConfig[]
}

export class AgentCoreDevelopment extends Stack {
  private s3DataSource: Bucket;
  constructor(scope: Construct, id: string, props?: AgentCoreDevelopmentProps) {
    super(scope, id, props);
    
    

    // The code below creates an S3 bucket
    this.s3DataSource = new Bucket(this, 'S3DataSource', {
      blockPublicAccess: cdk.aws_s3.BlockPublicAccess.BLOCK_ALL,
      encryption: BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    this.s3DataSource.addToResourcePolicy(
      new cdk.aws_iam.PolicyStatement({
        sid: 'DenyInsecureConnections',
        effect: Effect.DENY,
        principals: [new cdk.aws_iam.AnyPrincipal()],
        actions: ['s3:*'],
        resources: [
          this.s3DataSource.bucketArn,
          `${this.s3DataSource.bucketArn}/*`
        ],
        conditions: {
          Bool: {
            'aws:SecureTransport': 'false'
          }
        }
      })
    );
    const extraVars: EnvVars = {

    }

    const gateway = new agentcore.Gateway(this, "AgentCoreSysGateway", {
      gatewayName:"agentcore-sys",
      protocolConfiguration: new agentcore.McpProtocolConfiguration({
        instructions: "Use this gateway to connect to external MCP tools",
        searchType: agentcore.McpGatewaySearchType.SEMANTIC,
        supportedVersions: [agentcore.MCPProtocolVersion.MCP_2025_03_26],
      }),
      exceptionLevel: agentcore.GatewayExceptionLevel.DEBUG
    });

    if (gateway.gatewayUrl !== undefined ) {
      extraVars['GATEWAY_URL'] = gateway.gatewayUrl
    }
    
    const openApiTargets = []
    for (const config of props?.openApiConfigs || []) {
       const schema = agentcore.ApiSchema.fromLocalAsset(
        path.join(__dirname, config.schemaPath),
      );

      const apikeyConfig = agentcore.GatewayCredentialProvider.apiKey({
        providerArn: config.providerArn,
        secretArn: config.secretArn,
        credentialLocation: agentcore.ApiKeyCredentialLocation.header({
          credentialParameterName: config.credentialProviderParamName,
        }),
      })
      apikeyConfig.grantNeededPermissionsToRole(gateway.role)

      const targetConfig = agentcore.OpenApiTargetConfiguration.create(schema)

      const target = new agentcore.GatewayTarget(this, 'target-' + config.apiName, {
        gatewayTargetName: config.apiName,
        description: config.description,
        credentialProviderConfigurations: [apikeyConfig],
        gateway: gateway,
        targetConfiguration: targetConfig,
      })
      
      // const target = gateway.addOpenApiTarget(config.apiName, {
      //   gatewayTargetName: config.apiName,
      //   description: config.description,
      //   credentialProviderConfigurations: [apikeyConfig],
      //   apiSchema: schema,
      // })
      openApiTargets.push(target)
    }

    const agents = []
    for (const config of props?.agentConfigs || []) {
      const agent = this.createRuntimeAgent(config.agentName, config.sourcePath, config, extraVars);
      this.allowAgentInvokeAmazonAnthropic(agent);
      gateway.grantRead(agent.role)
      gateway.grant(agent.role,'bedrock-agentcore:InvokeGateway')
      agents.push(agent)
    }
    
    for (const agent of agents) {
      new cdk.CfnOutput(this, 'RuntimeIdfor' + agent.agentRuntimeName, {
      value: agent.agentRuntimeId
    });
    }

    new cdk.CfnOutput(this, 'AgentCoreSysGatewayId', {
      value: gateway.gatewayId
    });

  }

  private createRuntimeAgent(name: string, assetPath: string, config: AgentConfig, extraVars: EnvVars) {

    const newAgentArtifact = agentcore.AgentRuntimeArtifact.fromAsset(
      path.join(__dirname, assetPath)
    )

    const newAgent = new agentcore.Runtime(this, `runtime-${name}`, {
      runtimeName: name,
      agentRuntimeArtifact: newAgentArtifact,
       environmentVariables: { 
        ...config.envVars,
        ...extraVars 
      },
    });

    return newAgent
  }

  private allowAgentInvokeAmazonAnthropic(agent: agentcore.Runtime) {
    agent.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        effect: Effect.ALLOW,
        actions: [
          'bedrock:InvokeModel',
          'bedrock:InvokeModelWithResponseStream'
        ],
        resources: [
          "arn:aws:bedrock:*::foundation-model/anthropic.claude*",
          "arn:aws:bedrock:*::foundation-model/amazon.nova*",
          // Cross-region inference profiles
          "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude*",
          "arn:aws:bedrock:*:*:inference-profile/eu.anthropic.claude*",
          "arn:aws:bedrock:*:*:inference-profile/us.amazon.nova*",
          "arn:aws:bedrock:*:*:inference-profile/eu.amazon.nova*"
        ],        
      })
    )

    agent.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        effect: Effect.DENY,
        actions: [
          'bedrock:InvokeModel',
          'bedrock:InvokeModelWithResponseStream'
        ],
        resources: ['*'],
        conditions: {
          StringNotLike: {
            "bedrock:ModelId": [
              "anthropic.claude*",
              "amazon.nova*",
              "*.anthropic.claude*",
              "*.amazon.nova*"              
            ]
          }
        }
      })
    )

    agent.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        effect: Effect.ALLOW,
        actions: [
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel",
          "bedrock:ListCrossRegionInferenceProfiles",
          "bedrock:GetCrossRegionInferenceProfile"
        ],
        resources: ["*"]
      })
    )
  }
}
