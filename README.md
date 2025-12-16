# AgentCore Multi-Agent System

A production-ready multi-agent system built with Strands Agents framework and deployed on Amazon Bedrock AgentCore Runtime using AWS CDK. Features a supervisor-worker architecture with graceful degradation, comprehensive error handling, and structured logging.

## Overview

This project demonstrates a production-ready multi-agent architecture with:
- **Supervisor-worker pattern**: agent001 orchestrates specialized sub-agents (agent002-007)
- Multiple specialized agents with different capabilities
- **Graceful degradation**: System continues operating when some sub-agents are unavailable
- **Comprehensive error handling**: Retry logic, timeouts, and structured error responses
- **Structured logging**: JSON-formatted logs for easy parsing and monitoring
- Shared infrastructure deployed via AWS CDK
- MCP (Model Context Protocol) integration for agent communication
- OpenAPI gateway for external API integration
- Cognito-based authentication

## System Architecture

### Supervisor-Worker Pattern

```
User Query
    ↓
agent001 (Supervisor) ← Orchestrates and aggregates tools
    ↓ (MCP Protocol over AWS SigV4)
    ├→ agent002 (Weather) ← getWeather tool
    ├→ agent003 (NFL Teams) ← getNFLTeams tool
    ├→ agent004 (NFL Scores) ← getNFLScores tool
    ├→ agent005 (NFL Schedule) ← getNFLSchedule tool
    ├→ agent006 (NFL Stats) ← getNFLPlayerStats tool
    └→ agent007 (NFL Predictions) ← predictNFLGame tool
```

### Key Features

**Graceful Degradation**: 
- Supervisor continues operating even if some sub-agents are unavailable
- Only fails if ALL sub-agents are down
- Logs which agents are unavailable and which tools are accessible

**Error Handling**:
- Validates environment variables before initialization
- Retry logic with exponential backoff (1s, 2s, 4s delays)
- Comprehensive error logging with full stack traces
- Handles malformed tool schemas and connection failures

**Health Monitoring**:
- Tracks connection status for each sub-agent
- Logs successful and failed connections
- Provides detailed summary of system health

**Structured Logging**:
- JSON-formatted logs with timestamps, agent IDs, and operation types
- Contextual information (tool counts, retry attempts, error details)
- Easy parsing for monitoring and debugging tools

## Prerequisites

- Python 3.10+
- Node.js 18+ (for CDK)
- AWS account with appropriate permissions
- AWS credentials configured
- Docker/Finch/Podman (for local testing)

## Environment Variables

### Supervisor Agent (agent001)

The supervisor requires environment variables for each sub-agent it manages:

```bash
# Sub-agent runtime IDs (REQUIRED for each agent you want to use)
export agent002=<runtime-id>  # Weather agent
export agent003=<runtime-id>  # NFL Teams agent
export agent004=<runtime-id>  # NFL Scores agent
export agent005=<runtime-id>  # NFL Schedule agent
export agent006=<runtime-id>  # NFL Stats agent
export agent007=<runtime-id>  # NFL Predictions agent

# AWS Configuration (automatically set in AgentCore runtime)
# AWS_REGION=us-west-2
# AWS_ACCOUNT_ID=<your-account-id>
```

**Note**: The supervisor will work with a subset of sub-agents if not all environment variables are set. It will log warnings for missing agents and continue with available tools.

### Sub-agents (agent002-007)

Each sub-agent requires:
- AWS credentials (automatically provided in AgentCore runtime)
- Region configuration (defaults to us-west-2)

No additional environment variables needed for sub-agents.

## Project Structure

```
.
├── src/                    # Agent implementations
│   ├── agent001/          # Supervisor agent (orchestrates sub-agents)
│   ├── agent002/          # Weather agent with MCP
│   ├── agent003/          # NFL Teams data
│   ├── agent004/          # NFL Scores
│   ├── agent005/          # NFL Schedules
│   ├── agent006/          # NFL Player Statistics
│   ├── agent007/          # NFL Game Predictions
│   ├── utils/             # Shared utilities
│   │   ├── agent_utils.py         # Common agent utilities
│   │   ├── http_request_with_retry.py  # HTTP with retry logic
│   │   ├── remote_client.py       # MCP client utilities
│   │   └── streamable_http_sigv4.py    # AWS SigV4 auth
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

After deployment, note the runtime IDs for each agent from the CDK outputs.

### 3. Configure Environment Variables

```bash
# Set runtime IDs from CDK outputs
export agent002=<runtime-id-from-output>
export agent003=<runtime-id-from-output>
export agent004=<runtime-id-from-output>
export agent005=<runtime-id-from-output>
export agent006=<runtime-id-from-output>
export agent007=<runtime-id-from-output>
```

### 4. Test an Agent Locally

```bash
cd src/agent001
python main.py '{"prompt": "What is the weather in New York?"}'
```

Test with curl (if running as HTTP server):
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Predict the Cowboys game this Sunday"}'
```

## Agent Descriptions

### agent001 - Supervisor (Orchestrator)
- **Purpose**: Coordinates multiple sub-agents and aggregates their tools
- **Communication**: MCP Protocol with AWS SigV4 authentication
- **Features**:
  - Tool aggregation from all sub-agents
  - Graceful degradation when agents fail
  - Retry logic with exponential backoff
  - Comprehensive error handling
  - Structured JSON logging

### agent002 - Weather Agent
- **Purpose**: Retrieves weather information using National Weather Service API
- **Tool**: `getWeather(weatherQuery: str)`
- **Data Source**: https://api.weather.gov

### agent003 - NFL Teams Agent
- **Purpose**: Provides NFL team information
- **Tool**: `getNFLTeams(teamQuery: str)`
- **Data Source**: ESPN API

### agent004 - NFL Scores Agent
- **Purpose**: Retrieves current and historical NFL game scores
- **Tool**: `getNFLScores(scoreQuery: str)`
- **Data Source**: ESPN Scoreboard API
- **Features**: HTTP retry logic, structured logging

### agent005 - NFL Schedule Agent
- **Purpose**: Provides NFL game schedules
- **Tool**: `getNFLSchedule(scheduleQuery: str)`
- **Data Source**: ESPN API

### agent006 - NFL Player Stats Agent
- **Purpose**: Retrieves player and team statistics
- **Tool**: `getNFLPlayerStats(statsQuery: str)`
- **Data Source**: ESPN Stats API

### agent007 - NFL Predictions Agent
- **Purpose**: Generates game predictions based on data analysis
- **Tool**: `predictNFLGame(predictionQuery: str)`
- **Logic**: Analyzes schedule, scores, stats, and weather data

## Error Handling and Graceful Degradation

### Connection Failures

When a sub-agent is unavailable, the supervisor:

1. **Logs the failure** with detailed error information
2. **Continues initialization** with remaining agents
3. **Provides partial functionality** with available tools
4. **Informs users** about degraded capabilities in responses

Example log output:
```json
{
  "timestamp": "2024-12-16T10:30:45Z",
  "level": "WARNING",
  "agent": "agent001",
  "message": "Operating with degraded functionality. Failed agents: ['agent003']",
  "operation": "tool_discovery",
  "failed_agents": ["agent003"],
  "status": "degraded"
}
```

### Environment Variable Validation

The system validates environment variables at startup:

- **Missing variables**: Logs warning and skips that agent
- **No variables**: Fails with clear error message
- **Partial configuration**: Continues with available agents

### Retry Logic

All network operations include retry logic:
- **Maximum retries**: 3 attempts
- **Delays**: Exponential backoff (1s, 2s, 4s)
- **Logging**: Each attempt is logged with context
- **Failure handling**: Clear error messages after all retries exhausted

Example:
```json
{
  "timestamp": "2024-12-16T10:30:45Z",
  "level": "WARNING",
  "agent": "agent001",
  "message": "Retrying create_mcp_client_agent004 (attempt 2/4) after 2s delay",
  "operation": "create_mcp_client_agent004",
  "retry_count": 1,
  "delay_seconds": 2
}
```

### Timeout Configuration

All operations have timeouts to prevent hanging:
- **MCP Connection**: 10 seconds (configurable in agent_utils.py)
- **Tool Discovery**: 5 seconds (configurable in agent_utils.py)
- **HTTP Requests**: 30 seconds (sub-agents)

## Health Monitoring and Troubleshooting

### Checking System Health

The supervisor logs detailed health information during initialization:

```json
{
  "timestamp": "2024-12-16T10:30:45Z",
  "level": "INFO",
  "agent": "agent001",
  "message": "Tool discovery complete: 7 total tools from 6 agents",
  "operation": "tool_discovery",
  "total_tools": 7,
  "successful_agents": 6,
  "failed_agents": 0,
  "status": "success"
}
```

### Common Issues and Solutions

#### Issue: "Missing required environment variable: agentXXX"
**Cause**: Environment variable not set for a sub-agent  
**Solution**: 
```bash
export agentXXX=<runtime-id-from-cdk-output>
```

#### Issue: "No sub-agent tools available"
**Cause**: All sub-agents failed to connect  
**Solution**: 
1. Check environment variables are set correctly
2. Verify sub-agents are deployed and running
3. Check AWS credentials and permissions
4. Review logs for specific connection errors

#### Issue: "Failed to connect to agentXXX: Connection timeout"
**Cause**: Sub-agent not responding within timeout period  
**Solution**:
1. Verify sub-agent is running: `aws bedrock-agentcore get-runtime --runtime-id <id>`
2. Check sub-agent logs for errors
3. Increase timeout in `src/utils/agent_utils.py` if needed
4. The system will retry automatically with exponential backoff

#### Issue: Agent works with some tools missing
**Cause**: Some sub-agents failed, but others succeeded (graceful degradation)  
**Solution**: This is expected behavior! Check logs to see which agents failed and why. The system continues operating with available tools.

### Log Analysis

Logs are structured as JSON for easy parsing:

```bash
# Find all errors
cat logs.json | jq 'select(.level=="ERROR")'

# Find tool discovery issues
cat logs.json | jq 'select(.operation=="tool_discovery")'

# Find retry attempts
cat logs.json | jq 'select(.retry_count != null)'

# Check agent health summary
cat logs.json | jq 'select(.operation=="tool_discovery") | {successful_agents, failed_agents, total_tools}'
```

## Development

### Adding a New Agent

1. Create agent directory: `src/agentXXX/`
2. Add `main.py`, `requirements.txt`
3. Symlink Dockerfile: `ln -s ../../Dockerfile.agentcore Dockerfile`
4. Update `infra/lib/agent-core-development.ts` to include new agent
5. Add agent to supervisor's `supported_agents` list in `src/agent001/main.py`

### Using Common Utilities

The `src/utils/agent_utils.py` library provides:

```python
from agent_utils import (
    setup_logging,              # Structured JSON logging
    validate_environment_variables,  # Env var validation
    retry_with_backoff,         # Retry logic
    timer_context,              # Operation timing
    create_error_response,      # Standardized errors
    AgentHealthChecker          # Health monitoring
)

# Set up logging
logger = setup_logging("agent001")

# Validate environment variables
env_vars = validate_environment_variables(["VAR1", "VAR2"], logger)

# Retry with backoff
result = retry_with_backoff(
    lambda: risky_operation(),
    max_retries=3,
    logger=logger,
    operation_name="risky_operation"
)

# Time operations
with timer_context(logger, "data_processing"):
    process_data()
```

### Infrastructure Changes

```bash
cd infra
npm run build
npm run cdk diff    # Preview changes
npm run cdk deploy  # Deploy changes
```

### Testing

#### Unit Testing
```bash
# Test individual agent
cd src/agentXXX
python main.py

# Test with specific query
python main.py '{"prompt": "your query here"}'
```

#### Integration Testing
```bash
# Test supervisor with all sub-agents
cd src/agent001
export agent002=<id>
export agent003=<id>
# ... set all agent IDs
python main.py '{"prompt": "Predict the Cowboys game"}'
```

#### Failure Testing
```bash
# Test with missing agent
unset agent003
python main.py '{"prompt": "What teams are in the NFC?"}'
# Should work with degraded functionality

# Test with all agents missing
unset agent002 agent003 agent004 agent005 agent006 agent007
python main.py
# Should fail with clear error message
```

## Monitoring and Observability

### Structured Logging

All agents use JSON-formatted logs with standard fields:
- `timestamp`: ISO 8601 UTC timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `agent`: Agent identifier
- `message`: Human-readable message
- `operation`: Operation being performed
- `status`: Success/failure status
- `error`: Error message (if applicable)
- `retry_count`: Retry attempt number (if applicable)
- `duration_ms`: Operation duration in milliseconds

### Key Metrics to Monitor

- **Tool discovery success rate**: Percentage of sub-agents successfully connected
- **Query processing time**: Duration from request to response
- **Retry frequency**: How often operations need retries
- **Error rates**: Failed operations per agent
- **Availability**: Uptime of each sub-agent

### CloudWatch Integration

Logs are automatically sent to CloudWatch when running in AgentCore:
- Log group: `/aws/bedrock-agentcore/runtimes/<runtime-id>`
- Parse JSON logs using CloudWatch Insights queries
- Set up alarms for error rates and availability

Example CloudWatch Insights query:
```
fields timestamp, agent, operation, status, error
| filter level = "ERROR"
| stats count() by agent, operation
```

## Resources

- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)
- [MULTI_AGENT_COORDINATION_ANALYSIS.md](./MULTI_AGENT_COORDINATION_ANALYSIS.md) - Detailed analysis of coordination patterns
- [QUICK_FIX_REFERENCE.md](./QUICK_FIX_REFERENCE.md) - Quick reference for critical fixes

## Contributing

When making changes to agents:
1. Follow existing code conventions
2. Use structured logging from `agent_utils`
3. Implement error handling and retry logic
4. Update documentation
5. Test with graceful degradation scenarios
6. Run integration tests with all agents

## License

See LICENSE file for details.

