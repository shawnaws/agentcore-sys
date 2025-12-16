# Project Structure

## Root Directory

```
.
├── src/                    # Agent implementations
├── infra/                  # AWS CDK infrastructure code
├── Dockerfile.agentcore    # Shared Dockerfile for all agents
├── package.json            # Root dependencies (agentcore constructs)
├── README.md              # Project documentation
└── .venv/                 # Python virtual environment
```

## Agent Source (`src/`)

Each agent has its own directory with a consistent structure:

```
src/
├── agent001/              # Agent with MCP gateway integration
│   ├── main.py           # Agent entrypoint
│   ├── remote_client.py  # Remote MCP client
│   ├── streamable_http_sigv4.py  # AWS SigV4 auth
│   ├── Dockerfile        # Symlink to shared Dockerfile
│   └── requirements.txt  # Python dependencies
├── agent002/              # Weather agent
│   ├── main.py           # Agent entrypoint
│   ├── Dockerfile        # Symlink to shared Dockerfile
│   └── requirements.txt  # Python dependencies
├── agent003-007/          # Additional specialized agents
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── utils/                 # Shared utilities
│   ├── remote_client.py  # MCP client utilities
│   ├── streamable_http_sigv4.py  # AWS SigV4 auth
│   ├── http_request_with_retry.py  # HTTP retry logic
│   ├── nfl_formatters.py # NFL data formatting
│   └── *.md              # Documentation
└── openapi/               # OpenAPI specifications
    ├── sampleapi.json
    └── weather-agent.json
```

### Agent Conventions

- **main.py**: Contains the BedrockAgentCoreApp entrypoint and agent initialization
- **Dockerfile**: Symlink to `../../Dockerfile.agentcore` (shared across all agents)
- **requirements.txt**: Lists Python dependencies
- Each agent is self-contained and independently deployable
- All agents use the same Dockerfile for consistency and easier maintenance
- Shared utilities in `utils/` can be imported by any agent

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
