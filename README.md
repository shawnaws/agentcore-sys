# Strands Agent on Amazon Bedrock AgentCore

A minimal Python project using Strands Agents framework deployed on Amazon Bedrock AgentCore Runtime.

## Prerequisites

- Python 3.10+
- AWS account with appropriate permissions
- AWS credentials configured

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test Locally

```bash
python agent.py
```

Test with curl:
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world!"}'
```

## Deployment to AgentCore

### Option A: Using Starter Toolkit (Recommended)

```bash
# Install the toolkit
pip install bedrock-agentcore-starter-toolkit

# Configure your agent
agentcore configure --entrypoint agent.py

# Optional: Test locally (requires Docker/Finch/Podman)
agentcore launch --local

# Deploy to AWS
agentcore launch

# Test your deployed agent
agentcore invoke '{"prompt": "Hello from AgentCore!"}'
```

### Option B: Manual Deployment

See the custom deployment section in the Strands documentation for building and pushing Docker images to ECR.

## Project Structure

```
.
├── agent.py           # Main agent code with AgentCore integration
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Customization

### Adding Tools

```python
from strands import Agent, tool

@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: Sunny, 72°F"

agent = Agent(tools=[get_weather])
```

### Streaming Responses

```python
@app.entrypoint
async def invoke(payload):
    user_message = payload.get("prompt", "Hello")
    stream = agent.stream_async(user_message)
    async for event in stream:
        yield event
```

## Resources

- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [Deployment Guide](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/)
