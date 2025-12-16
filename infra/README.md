# AgentCore Infrastructure

AWS CDK infrastructure for deploying multiple Strands agents to Amazon Bedrock AgentCore Runtime.

## Overview

This CDK project deploys:
- **AgentCore Runtime**: Serverless execution environment for all agents
- **AgentCore Gateway**: MCP and OpenAPI integration layer
- **Cognito User Pools**: OAuth2 authentication
- **S3 Buckets**: Data source storage
- **IAM Roles**: Permissions for agent execution

## Structure

```
infra/
├── bin/
│   └── infra.ts              # CDK app entry point
├── lib/
│   └── agent-core-development.ts  # Main stack definition
├── test/
│   └── infra.test.ts         # Infrastructure tests
├── cdk.json                  # CDK configuration
├── package.json              # Node dependencies
└── tsconfig.json             # TypeScript config
```

## Commands

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Watch for changes
npm run watch

# Run tests
npm test

# Synthesize CloudFormation
npm run cdk synth

# Show deployment diff
npm run cdk diff

# Deploy to AWS
npm run cdk deploy

# Destroy stack
npm run cdk destroy
```

## Stack Configuration

The main stack (`AgentCoreDevelopment`) is configured in `lib/agent-core-development.ts` and includes:

### Agents
- agent001-007 deployed from `../src/` directories
- Each agent uses shared `Dockerfile.agentcore`
- Runtime IDs exported as stack outputs

### Gateway
- MCP server integration
- OpenAPI target configurations
- Gateway ID exported for client access

### Authentication
- Cognito user pool for OAuth2
- User pool ID and client ID exported

### Data Sources
- S3 buckets for agent data
- Bucket names exported

## Adding a New Agent

1. Create agent in `../src/agentXXX/`
2. Update `lib/agent-core-development.ts`:

```typescript
const agent008 = new AgentCoreRuntime(this, 'Agent008', {
  agentName: 'agent008',
  sourceDirectory: path.join(__dirname, '../../src/agent008'),
  // ... other config
});
```

3. Deploy:
```bash
npm run build
npm run cdk deploy
```

## Outputs

After deployment, the stack exports:
- Runtime IDs for each agent
- Gateway ID for MCP/API access
- Cognito user pool details
- S3 bucket names

Access outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name AgentCoreDevelopment \
  --query 'Stacks[0].Outputs'
```

## Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AgentCore CDK Constructs](https://github.com/krokoko/agentcore-cdk-constructs)
- [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/)
