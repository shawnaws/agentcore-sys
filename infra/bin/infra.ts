#!/opt/homebrew/opt/node/bin/node
import * as cdk from 'aws-cdk-lib';
import { AgentCoreDevelopment, AuthProviderType } from '../lib/agent-core-development';

const app = new cdk.App();
new AgentCoreDevelopment(app, 'AgentCoreDev', {
  stackBaseName: 'AgentCore',
  openApiConfigs: [
    {
      description: "Weather Agent",
      apiName: 'weather-agent',
      schemaPath: '../../src/openapi/weather-agent.json',
      providerArn: 'arn:aws:bedrock-agentcore:us-west-2:376998848592:token-vault/default/apikeycredentialprovider/national-weather-service-user-agent',
      secretArn: 'arn:aws:secretsmanager:us-west-2:376998848592:secret:bedrock-agentcore-identity!default/apikey/national-weather-service-user-agent-m8YDsG',
      credentialProviderParamName: 'User-Agent',
      authProviderType: AuthProviderType.APIKEY
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
      protocol: "MCP",
      envVars: {},
    }
  ],
});