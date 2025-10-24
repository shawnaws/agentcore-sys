#!/opt/homebrew/opt/node/bin/node
import * as cdk from 'aws-cdk-lib';
import { AgentCoreDevelopment } from '../lib/agent-core-development';

const app = new cdk.App();
new AgentCoreDevelopment(app, 'AgentCoreDev', {

  openApiConfigs: [
    {
      description: "National Weather Service API Integration",
      apiName: 'national-weather-service',
      schemaPath: '../../src/openapi/sampleapi.json',
      providerArn: 'arn:aws:bedrock-agentcore:us-west-2:376998848592:token-vault/default/apikeycredentialprovider/national-weather-service-user-agent',
      secretArn: 'arn:aws:secretsmanager:us-west-2:376998848592:secret:bedrock-agentcore-identity!default/apikey/national-weather-service-user-agent-m8YDsG',
      credentialProviderParamName: 'User-Agent'
    },
  ],
  agentConfigs: [
    {
      agentName: 'agent001',
      sourcePath: '../../src/agent001',
      envVars: {
        "USEGATEWAY": "true",
      },
    },
    {
      agentName: 'agent002',
      sourcePath: '../../src/agent002',
      envVars: {
        "USEGATEWAY": "true",
      },
    }
  ],
  /* If you don't specify 'env', this stack will be environment-agnostic.
   * Account/Region-dependent features and context lookups will not work,
   * but a single synthesized template can be deployed anywhere. */

  /* Uncomment the next line to specialize this stack for the AWS Account
   * and Region that are implied by the current CLI configuration. */
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },

  /* Uncomment the next line if you know exactly what Account and Region you
   * want to deploy the stack to. */
  // env: { account: '123456789012', region: 'us-east-1' },

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
});