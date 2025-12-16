# AgentCore Multi-Agent System

A multi-agent system built with Strands Agents framework and deployed on Amazon Bedrock AgentCore Runtime using AWS CDK.

## Overview

This project demonstrates a production-ready multi-agent architecture with:
- Multiple specialized agents (agent001-007) with different capabilities
- Shared infrastructure deployed via AWS CDK
- MCP (Model Context Protocol) integration
- OpenAPI gateway for external API integration
- Cognito-based authentication

## Prerequisites

- Python 3.10+
- Node.js 18+ (for CDK)
- AWS account with appropriate permissions
- AWS credentials configured
- Docker/Finch/Podman (for local testing)

## Project Structure

```
.
├── src/                    # Agent implementations
│   ├── agent001/          # Example agents
│   ├── agent002/          # Weather agent with MCP
│   ├── ...
│   ├── utils/             # Shared utilities
│   └── openapi/           # OpenAPI specifications
├── infra/                 # AWS CDK infrastructure
│   ├── lib/               # Stack definitions
│   └── bin/               # CDK app entry
├── Dockerfile.agentcore   # Shared agent container
└── package.json           # Root dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies (root)
pip install -r requirements.txt

# CDK dependencies
cd infra
npm install
cd ..
```

### 2. Deploy Infrastructure

```bash
cd infra
npm run build
npm run cdk deploy
```

This deploys:
- AgentCore Runtime for all agents
- AgentCore Gateway with MCP and OpenAPI targets
- Cognito user pools for authentication
- S3 buckets for data sources

### 3. Test an Agent Locally

```bash
cd src/agent001
python main.py
```

Test with curl:
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world!"}'
```

## Agent Descriptions

- **agent001**: Base agent with MCP gateway integration
- **agent002**: Weather agent with custom MCP server
- **agent003-007**: Specialized agents for various tasks

## Development

### Adding a New Agent

1. Create agent directory: `src/agentXXX/`
2. Add `main.py`, `requirements.txt`
3. Symlink Dockerfile: `ln -s ../../Dockerfile.agentcore Dockerfile`
4. Update `infra/lib/agent-core-development.ts` to include new agent

### Infrastructure Changes

```bash
cd infra
npm run build
npm run cdk diff    # Preview changes
npm run cdk deploy  # Deploy changes
```

## Resources

- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
