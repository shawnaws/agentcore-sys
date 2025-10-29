import * as cdk from 'aws-cdk-lib';
import {
  Repository
} from 'aws-cdk-lib/aws-ecr'
import path from 'path';
import {
  OAuthScope,
  UserPool,
  ResourceServerScope,
  AccountRecovery,
  UserPoolClient,

} from 'aws-cdk-lib/aws-cognito';

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

import { Gateway, GatewayCredentialProvider, ProtocolType } from '@krokoko/agentcore-cdk-constructs/lib/cdk-lib/bedrock-agentcore';
import { Protocol } from 'aws-cdk-lib/aws-ec2';

export enum AuthProviderType {
  'OAUTH',
  'APIKEY'
}

type OpenApiConfig = {
  description: string
  apiName: string
  schemaPath: string
  providerArn: string,
  secretArn: string
  credentialProviderParamName: string
  authProviderType: AuthProviderType
  scopes?: string[]
}

type McpTargetConfig = {
  agentName: string
  protocol: ProtocolType
  host: string
  port: number
}

type EnvVars = {
  [key: string]: string;
}

type AgentConfig = {
  agentName: string
  sourcePath: string
  envVars: EnvVars
  protocol?: string
}

interface AgentCoreDevelopmentProps extends StackProps {
  stackBaseName: string
  openApiConfigs: OpenApiConfig[]
  agentConfigs: AgentConfig[]
}

export class AgentCoreDevelopment extends Stack {
  private s3DataSource: Bucket;
  constructor(scope: Construct, id: string, props: AgentCoreDevelopmentProps) {
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

    /**
     * Add cognito user pool to the stack so it can be used by AgentCore Gateway as an authorization methodology.
     */
    const { userPool, userPoolClient } = this.createUserPoolForOauth(props);

    const extraVars: EnvVars = {
      USER_POOL_ID: userPool.userPoolId,
      USER_POOL_CLIENT_ID: userPoolClient.userPoolClientId,
    }


    const gateway = new agentcore.Gateway(this, props.stackBaseName + "SysGateway", {
      gatewayName: props.stackBaseName.toLowerCase() + "-sys",
      protocolConfiguration: new agentcore.McpProtocolConfiguration({
        instructions: "Use this gateway to connect to external MCP tools",
        searchType: agentcore.McpGatewaySearchType.SEMANTIC,
        supportedVersions: [agentcore.MCPProtocolVersion.MCP_2025_03_26],
      }),
      exceptionLevel: agentcore.GatewayExceptionLevel.DEBUG
    });

    if (gateway.gatewayUrl !== undefined) {
      extraVars['GATEWAY_URL'] = gateway.gatewayUrl
    }

    const openApiTargets = this.createOpenApiTargets(gateway, props, userPool, userPoolClient);

    const agents = []
    for (const config of props?.agentConfigs || []) {
      const agent = this.createRuntimeAgent(config.agentName, config.sourcePath, config, extraVars, userPool, userPoolClient);
      this.allowAgentInvokeAmazonAnthropic(agent);
      gateway.grantRead(agent.role)
      gateway.grant(agent.role, 'bedrock-agentcore:InvokeGateway')
      agents.push(agent)
    }

    for (const agent of agents) {

      new cdk.CfnOutput(this, 'RuntimeIdfor' + agent.agentRuntimeName, {
        value: agent.agentRuntimeId
      });
      new cdk.CfnOutput(this, 'RuntimeArnfor' + agent.agentRuntimeName, {
        value: agent.agentRuntimeArn
      });
    }

    new cdk.CfnOutput(this, props.stackBaseName + 'SysGatewayId', {
      value: gateway.gatewayId
    });

    new cdk.CfnOutput(this, 'UserPoolId', {
      value: userPool.userPoolId,
      description: 'Cognito User Pool ID for AgentCore Gateway authorization',
    });

    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID',
    });
  }

  private createUserPoolForOauth(props: AgentCoreDevelopmentProps) {
    const userPool = new UserPool(this, props.stackBaseName + 'UserPool', {
      userPoolName: 'agentcore-user-pool',
      selfSignUpEnabled: true,
      signInAliases: {
        email: true,
      },
      autoVerify: {
        email: true,
      },
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
      },
      passwordPolicy: {
        minLength: 12,
      },
      accountRecovery: AccountRecovery.EMAIL_ONLY,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const scopes = [
      {
        scopeName: 'read',
        scopeDescription: 'Read access to application data',
      },
      {
        scopeName: 'write',
        scopeDescription: 'Write access to application data',
      },
      {
        scopeName: 'admin',
        scopeDescription: 'Administrative access to application data',
      },
    ];
    const resourceScopes: ResourceServerScope[] = scopes.map(item => {
      return {
        scopeName: item.scopeName,
        scopeDescription: item.scopeDescription
      };
    });
    const resourceServer = userPool.addResourceServer(props.stackBaseName + 'Resource', {
      userPoolResourceServerName: props.stackBaseName + 'Api',
      identifier: 'api',
      scopes: scopes,
    });
    const oauthScopes: OAuthScope[] = [];
    for (let index in scopes) {
      const oauthScope = OAuthScope.resourceServer(resourceServer!, resourceScopes[index]);
      oauthScopes.push(oauthScope);
    }

    const userPoolClient = userPool.addClient(props.stackBaseName + 'UserPoolClient', {
      userPoolClientName: 'agentcore-client',
      generateSecret: true,
      authFlows: {
        adminUserPassword: true,
        userPassword: true,
        userSrp: false,
        custom: true,
      },
      oAuth: {
        flows: {
          clientCredentials: true,
          authorizationCodeGrant: false,
          implicitCodeGrant: false,
        },
        scopes: [
          ...oauthScopes
        ]
      }
    });
    return { userPool, userPoolClient };
  }

  private createOpenApiTargets(gateway: Gateway, props?: AgentCoreDevelopmentProps, userPool?: UserPool, userPoolClient?: UserPoolClient) {
    const openApiTargets = [];
    for (const config of props?.openApiConfigs || []) {
      const schema = agentcore.ApiSchema.fromLocalAsset(
        path.join(__dirname, config.schemaPath)
      );

      let credentialProvider: agentcore.ApiKeyCredentialProviderConfiguration | agentcore.OAuthCredentialProviderConfiguration;
      if (config.authProviderType == AuthProviderType.OAUTH && config.scopes !== undefined) {
        credentialProvider = agentcore.GatewayCredentialProvider.oauth({
          providerArn: config.providerArn, 
          secretArn: config.secretArn,
          scopes: config?.scopes
        });
      } else if (config.authProviderType == AuthProviderType.APIKEY) {
        credentialProvider = agentcore.GatewayCredentialProvider.apiKey({
          providerArn: config.providerArn,
          secretArn: config.secretArn,
          credentialLocation: agentcore.ApiKeyCredentialLocation.header({
            credentialParameterName: config.credentialProviderParamName,
          })
        });

      } else {
        throw new Error(`Unknown auth provider type: ${config.authProviderType}`);
      }
      
      credentialProvider.grantNeededPermissionsToRole(gateway.role);
      const targetConfig = agentcore.OpenApiTargetConfiguration.create(schema);

      const target = new agentcore.GatewayTarget(this, 'target-' + config.apiName, {
        gatewayTargetName: config.apiName,
        description: config.description,
        credentialProviderConfigurations: [credentialProvider],
        gateway: gateway,
        targetConfiguration: targetConfig,
      });

      openApiTargets.push(target);
    }
    return openApiTargets;
  }

  private createRuntimeAgent(name: string, assetPath: string, config: AgentConfig, extraVars: EnvVars, userPool?: UserPool, userPoolClient) {

    const newAgentArtifact = agentcore.AgentRuntimeArtifact.fromAsset(
      path.join(__dirname, assetPath)
    )
    const protocol = config?.protocol ? config.protocol : 'HTTP';
    var protocolType = ProtocolType.HTTP
    if (protocol.toUpperCase() == ProtocolType.MCP.valueOf()) {
      protocolType = ProtocolType.MCP
    } else if (protocol.toUpperCase() == ProtocolType.HTTP.valueOf()) {
      protocolType = ProtocolType.HTTP
    } else {
      throw new Error(`Unknown protocol ${protocol}`)
    }
    const newAgent = new agentcore.Runtime(this, `runtime-${name}`, {
      runtimeName: name,
      agentRuntimeArtifact: newAgentArtifact,
      environmentVariables: {
        ...config.envVars,
        ...extraVars
      },
      protocolConfiguration: protocolType
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
