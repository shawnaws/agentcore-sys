import contextlib
import os
import sys
import boto3
import asyncio
import dotenv
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from strands_tools import current_time
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
from contextlib import asynccontextmanager


# Add utils directory to Python path
from remote_client import create_streamable_http_transport_sigv4

print("Initializing bedrock agentcore app")
app = BedrockAgentCoreApp()

logger = app.logger
model_id = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"

region="us-west-2"
service = "bedrock-agentcore"
# Create a custom boto3 session
print("Initializing boto3 session")
session = boto3.Session(
    region_name=region,
)

sts = boto3.client('sts')
aws_account_id = sts.get_caller_identity()["Account"]

def _get_bedrock_model(m_id):
    return BedrockModel(
        model_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
    )



@asynccontextmanager
async def create_agent():
    """Create a Strands agent with AWS IAM-authenticated MCP server access.

    This function demonstrates the key integration pattern:
    1. Define an aws_iam_streamablehttp_client factory function with the MCP server details
    2. Initialize a Strands MCPClient with the client factory
    3. Retrieve the available tools from the MCP server
    4. Create an agent with access to those tools
    5. Return a callable interface to communicate with the agent
    """

    def get_mcp_params(name):
        runtime_id = os.getenv(name, 'foobar'),
        logger.info(f"RUNTIMEID: %s", runtime_id[0])
        agent_arn = f"arn:aws:bedrock-agentcore:{region}:{aws_account_id}:runtime/{runtime_id[0]}"
        print(agent_arn)
        # URL encode the ARN using the same method as remote_client.py
        encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
        url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        print(url)
        mcp_region = region
        mcp_service = 'bedrock-agentcore'
        return url

    # Define an MCP client factory function for AWS IAM authentication

    def agent_factory(agent_id):
        def mcp_factory():
            mcp_url = get_mcp_params(agent_id)
            return aws_iam_streamablehttp_client(
                endpoint=mcp_url, aws_region=region, aws_service=service
            )
        return mcp_factory

    supported_agents = [ "agent002", "agent003", "agent004", "agent005", "agent006", "agent007"]
    # Create a Strands MCP client and retrieve the tools from the server
    agent_clients = []
    for agent_id in supported_agents:
        factory = agent_factory(agent_id)
        agent_clients.append(MCPClient(factory))

    with contextlib.ExitStack() as stack:
        mcp_tools = [current_time]
        for client in agent_clients:
            context_client = stack.enter_context(client)
            mcp_tools.append(context_client.list_tools_sync())

        system_prompt = """You are an NFL game prediction orchestrator with access to specialized tools for weather, schedules, scores, teams, stats, and predictions.

**Operational Workflow:**
When asked about NFL game predictions or outcomes, follow this sequence:

1. **Identify Teams**: Extract the specific team(s) mentioned in the query
2. **Get Schedule**: Use getNFLSchedule to find the game details (date, opponent, location)
3. **Gather Intelligence**: For both teams playing:
   - Use getNFLScores for recent game results
   - Use getNFLStats for team/player statistics
4. **Check Weather**: Use getWeather for the game location
   - Determine if stadium is domed or outdoor
   - Get forecast for game day if outdoor
5. **Generate Prediction**: Use getNFLPrediction with all gathered data

**Example Flow:**
User: "Will the Giants win this weekend?"
1. Team: New York Giants
2. Schedule: Giants @ Lions, Sunday Nov 23
3. Stats: Get Giants recent scores + Lions recent scores + team stats
4. Weather: Check Detroit weather (Ford Field is domed - note this)
5. Prediction: Send all data to predictor

**Guidelines:**
- Always gather complete data before making predictions
- Note stadium type (dome vs outdoor) when checking weather
- If data is missing, explain what's unavailable
- Be concise but thorough in your analysis"""

        agent = Agent(
            system_prompt=system_prompt,
            model=_get_bedrock_model(model_id),
            tools=mcp_tools,
            callback_handler=None
        )

        # Yield a callable interface to the agent
        async def agent_callable(user_input: str) -> str:
            """Send a message to the agent and return its response."""
            result = agent(user_input)
            return str(result)

        yield agent_callable


async def main():
    """Run the agent example by asking it to list its available tools."""
    # Validate required environment variables
    # if not MCP_URL or not MCP_REGION or not MCP_SERVICE:
    #     raise ValueError(
    #         'Please set MCP_SERVER_URL, MCP_SERVER_REGION, and MCP_SERVER_AWS_SERVICE environment variables or create an .env file.'
    #     )

    # Get user input from command line or use default
    import json
    if len(sys.argv) > 1:
        try:
            event = json.loads(sys.argv[1])
            user_input = event.get('prompt', 'Whats the weather in NYC')
        except json.JSONDecodeError:
            user_input = sys.argv[1]
    else:
        user_input = 'Whats the weather in NYC'

    # Create and run the agent
    async with create_agent() as agent:
        result = await agent(user_input)
        print(f'\n{result}')


if __name__ == '__main__':
    asyncio.run(main())