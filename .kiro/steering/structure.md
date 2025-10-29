# Project Structure

## Root Directory

```
.
├── src/                    # Agent implementations
├── infra/                  # AWS CDK infrastructure code
├── package.json            # Root dependencies (agentcore constructs)
├── README.md              # Project documentation
└── .venv/                 # Python virtual environment
```

## Agent Source (`src/`)

Each agent has its own directory with a consistent structure:

```
src/
├── agent001/              # Example agent 1
│   ├── main.py           # Agent entrypoint
│   ├── Dockerfile        # Container definition
│   └── requirements.txt  # Python dependencies
├── agent002/              # Example agent 2 (weather agent)
│   ├── main.py           # Agent with MCP server
│   ├── calc.py           # Tool implementations
│   ├── client.py         # MCP client utilities
│   ├── remote_client.py  # Remote client helpers
│   ├── streamable_http_sigv4.py  # AWS SigV4 auth
│   ├── Dockerfile
│   └── requirements.txt
└── openapi/               # OpenAPI specifications
    ├── sampleapi.json
    └── weather-agent.json
```

### Agent Conventions

- **main.py**: Contains the BedrockAgentCoreApp entrypoint and agent initialization
- **Dockerfile**: Defines the container image for deployment
- **requirements.txt**: Lists Python dependencies
- Each agent is self-contained and independently deployable

## Infrastructure (`infra/`)

CDK-based infrastructure as code:

```
infra/
├── bin/                   # CDK app entry point
├── lib/                   # Stack definitions
│   └── agent-core-development.ts  # Main stack
├── test/                  # Infrastructure tests
│   └── infra.test.ts
├── cdk.json              # CDK configuration
├── cdk.out/              # Synthesized CloudFormation (gitignored)
├── package.json          # Node dependencies
├── tsconfig.json         # TypeScript config
└── synth.yaml            # Synthesis configuration
```

### Infrastructure Patterns

- **Stacks**: Defined in `lib/` directory
- **Constructs**: Custom AgentCore constructs from `@krokoko/agentcore-cdk-constructs`
- **Configuration**: Stack accepts configs for agents, OpenAPI targets, and auth providers
- **Outputs**: Runtime IDs, ARNs, Gateway IDs, and Cognito details

## Key Files

- **infra/lib/agent-core-development.ts**: Main CDK stack that creates:
  - AgentCore Gateway for MCP and API integration
  - Runtime agents from source directories
  - Cognito user pools for OAuth2
  - S3 buckets for data sources
  - IAM roles and permissions

## Deployment Artifacts

- **agentcore-cdk-constructs@0.0.0.jsii.tgz**: Local CDK construct library (appears in both root and infra/)
- **cdk.out/**: Generated CloudFormation templates (not committed)
