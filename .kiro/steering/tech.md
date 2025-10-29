# Technology Stack

## Languages & Frameworks

### Python (Agents)
- **Python Version**: 3.10+
- **Framework**: Strands Agents framework
- **Runtime**: Amazon Bedrock AgentCore Runtime
- **Model**: Anthropic Claude (via Bedrock)
- **Key Libraries**:
  - `bedrock-agentcore-runtime` - AgentCore integration
  - `strands` - Agent framework
  - `strands-tools` - HTTP and tool utilities
  - `mcp` - Model Context Protocol client/server
  - `boto3` - AWS SDK

### TypeScript (Infrastructure)
- **TypeScript Version**: ~5.6.3
- **Framework**: AWS CDK 2.x
- **Key Libraries**:
  - `aws-cdk-lib` ^2.220.0
  - `@krokoko/agentcore-cdk-constructs` - Custom AgentCore constructs
  - `@aws-cdk/aws-bedrock-alpha` - Bedrock alpha constructs

## Build & Development Commands

### Python Agents
```bash
# Install dependencies
pip install -r requirements.txt

# Run agent locally (from agent directory)
python main.py

# Test with curl
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world!"}'
```

### Infrastructure (CDK)
```bash
# Navigate to infra directory
cd infra

# Install dependencies
npm install

# Build TypeScript
npm run build

# Watch mode for development
npm run watch

# Run tests
npm test

# CDK commands
npm run cdk synth    # Synthesize CloudFormation
npm run cdk deploy   # Deploy to AWS
npm run cdk diff     # Show changes
```

## AWS Services Used

- **Amazon Bedrock**: Foundation models (Claude, Nova)
- **AgentCore**: Agent runtime and gateway
- **Cognito**: User authentication and OAuth2
- **ECR**: Container registry for agent images
- **S3**: Data source storage
- **IAM**: Permissions and roles

## Development Tools

- **Docker/Finch/Podman**: Local container testing
- **Jest**: TypeScript testing
- **AWS CLI**: AWS resource management
