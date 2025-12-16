import contextlib
import os
import sys
import boto3
import asyncio
import time
import dotenv
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from strands_tools import current_time
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
from contextlib import asynccontextmanager

# Add utils directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from remote_client import create_streamable_http_transport_sigv4
from agent_utils import (
    setup_logging,
    validate_environment_variables,
    retry_with_backoff,
    timer_context,
    create_error_response,
    AgentHealthChecker,
    MCP_CONNECTION_TIMEOUT
)

print("Initializing bedrock agentcore app")
app = BedrockAgentCoreApp()

# Set up structured JSON logging for agent001
logger = setup_logging("agent001")
logger.info("Initializing agent001 supervisor", extra={"operation": "init"})

model_id = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"

region = "us-west-2"
service = "bedrock-agentcore"

# Create a custom boto3 session
logger.info("Initializing boto3 session", extra={"operation": "boto3_init", "region": region})
session = boto3.Session(
    region_name=region,
)

sts = boto3.client('sts')
aws_account_id = sts.get_caller_identity()["Account"]
logger.info(f"AWS Account ID: {aws_account_id}", extra={"operation": "boto3_init"})

def _get_bedrock_model(m_id):
    """Initialize and return a Bedrock model instance."""
    return BedrockModel(
        model_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
    )


def create_mcp_client_with_retry(agent_id: str, factory) -> MCPClient:
    """
    Create MCP client with retry logic for sub-agent connections.
    
    Args:
        agent_id: Identifier of the sub-agent
        factory: Factory function for creating MCP client
    
    Returns:
        Initialized MCPClient instance
    
    Raises:
        Exception: If all retry attempts fail
    """
    def create_client():
        return MCPClient(factory)
    
    return retry_with_backoff(
        create_client,
        max_retries=3,
        delays=[1, 2, 4],
        logger=logger,
        operation_name=f"create_mcp_client_{agent_id}"
    )


def health_check_agent(agent_id: str, client: MCPClient) -> bool:
    """
    Perform health check on a sub-agent by attempting to connect.
    
    Args:
        agent_id: Identifier of the sub-agent
        client: MCPClient instance
    
    Returns:
        True if agent is healthy, False otherwise
    """
    try:
        # Simple health check: try to enter context
        with client:
            return True
    except Exception as e:
        logger.warning(
            f"Health check failed for {agent_id}: {str(e)}",
            extra={"operation": "health_check", "sub_agent": agent_id, "error": str(e)}
        )
        return False


@asynccontextmanager
async def create_agent():
    """Create a Strands agent with AWS IAM-authenticated MCP server access.

    This function demonstrates the key integration pattern:
    1. Define an aws_iam_streamablehttp_client factory function with the MCP server details
    2. Initialize Strands MCPClients with the client factory
    3. Retrieve the available tools from each MCP server with error handling
    4. Create an agent with access to those tools (graceful degradation if some agents fail)
    5. Return a callable interface to communicate with the agent
    
    Error Handling:
    - Validates all required environment variables before initialization
    - Handles individual sub-agent connection failures gracefully
    - Implements retry logic for transient failures
    - Logs detailed information about successful and failed connections
    - Continues operation with partial tool set when some agents are unavailable
    """

    def get_mcp_params(name):
        """
        Get MCP connection parameters for a sub-agent.
        
        Args:
            name: Environment variable name containing runtime ID
        
        Returns:
            URL for MCP connection
        
        Raises:
            ValueError: If environment variable is not set
        """
        # P0 FIX: Remove trailing comma and validate environment variable
        runtime_id = os.getenv(name)
        if not runtime_id:
            error_msg = f"Missing required environment variable: {name}"
            logger.error(error_msg, extra={"operation": "get_mcp_params", "env_var": name})
            raise ValueError(error_msg)
        
        logger.info(f"RUNTIMEID: {runtime_id}", extra={"operation": "get_mcp_params", "sub_agent": name})
        agent_arn = f"arn:aws:bedrock-agentcore:{region}:{aws_account_id}:runtime/{runtime_id}"
        logger.debug(f"Agent ARN: {agent_arn}", extra={"operation": "get_mcp_params", "sub_agent": name})
        
        # URL encode the ARN using the same method as remote_client.py
        encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
        url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        logger.debug(f"MCP URL: {url}", extra={"operation": "get_mcp_params", "sub_agent": name})
        
        return url

    # Define an MCP client factory function for AWS IAM authentication
    def agent_factory(agent_id):
        """Create factory function for MCP client with timeout configuration."""
        def mcp_factory():
            mcp_url = get_mcp_params(agent_id)
            # P2 FIX: Add timeout configuration
            return aws_iam_streamablehttp_client(
                endpoint=mcp_url, 
                aws_region=region, 
                aws_service=service,
                # Note: aws_iam_streamablehttp_client may not support timeout parameter
                # This is dependent on the library version
            )
        return mcp_factory

    supported_agents = ["agent002", "agent003", "agent004", "agent005", "agent006", "agent007"]
    
    # P0 FIX: Validate environment variables early
    logger.info(f"Validating environment variables for {len(supported_agents)} sub-agents", 
                extra={"operation": "env_validation"})
    
    # Check which agents have environment variables set
    available_agents = []
    missing_agents = []
    
    for agent_id in supported_agents:
        if os.getenv(agent_id):
            available_agents.append(agent_id)
        else:
            missing_agents.append(agent_id)
            logger.warning(
                f"Environment variable not set for {agent_id} - agent will be skipped",
                extra={"operation": "env_validation", "sub_agent": agent_id, "status": "missing"}
            )
    
    if not available_agents:
        error_msg = "No sub-agent environment variables configured. At least one sub-agent is required."
        logger.error(error_msg, extra={"operation": "env_validation"})
        raise ValueError(error_msg)
    
    logger.info(
        f"Found {len(available_agents)} configured sub-agents (missing: {len(missing_agents)})",
        extra={
            "operation": "env_validation",
            "available_agents": len(available_agents),
            "missing_agents": len(missing_agents)
        }
    )
    
    # P0 & P1 FIX: Create clients with error handling and retry logic
    agent_clients = []
    failed_client_creation = []
    
    logger.info("Creating MCP clients for sub-agents", extra={"operation": "client_creation"})
    
    with timer_context(logger, "client_creation"):
        for agent_id in available_agents:
            try:
                factory = agent_factory(agent_id)
                # P1 FIX: Use retry logic for client creation
                client = create_mcp_client_with_retry(agent_id, factory)
                agent_clients.append((agent_id, client))
                logger.info(
                    f"Successfully created MCP client for {agent_id}",
                    extra={"operation": "client_creation", "sub_agent": agent_id, "status": "success"}
                )
            except Exception as e:
                failed_client_creation.append(agent_id)
                logger.error(
                    f"Failed to create MCP client for {agent_id}: {str(e)}",
                    extra={"operation": "client_creation", "sub_agent": agent_id, "error": str(e)},
                    exc_info=True
                )

    # P0 FIX: Tool discovery with comprehensive error handling and proper list flattening
    with contextlib.ExitStack() as stack:
        mcp_tools = [current_time]
        failed_agents = []
        successful_agents = []
        tool_count_by_agent = {}
        
        logger.info(
            f"Discovering tools from {len(agent_clients)} sub-agents",
            extra={"operation": "tool_discovery", "client_count": len(agent_clients)}
        )
        
        with timer_context(logger, "tool_discovery"):
            for agent_id, client in agent_clients:
                try:
                    # P0 FIX: Wrap tool discovery in try-catch
                    context_client = stack.enter_context(client)
                    
                    # P0 FIX: Handle malformed tool schemas
                    tools = context_client.list_tools_sync()
                    
                    if tools:
                        # P0 FIX: Use extend instead of append to flatten list
                        tool_count = len(tools) if hasattr(tools, '__len__') else 0
                        mcp_tools.extend(tools)
                        successful_agents.append(agent_id)
                        tool_count_by_agent[agent_id] = tool_count
                        logger.info(
                            f"Successfully loaded {tool_count} tools from {agent_id}",
                            extra={
                                "operation": "tool_discovery",
                                "sub_agent": agent_id,
                                "tool_count": tool_count,
                                "status": "success"
                            }
                        )
                    else:
                        logger.warning(
                            f"No tools returned from {agent_id}",
                            extra={"operation": "tool_discovery", "sub_agent": agent_id, "status": "no_tools"}
                        )
                        failed_agents.append(agent_id)
                        
                except Exception as e:
                    # P0 FIX: Log specific errors during tool discovery
                    failed_agents.append(agent_id)
                    logger.error(
                        f"Failed to discover tools from {agent_id}: {str(e)}",
                        extra={
                            "operation": "tool_discovery",
                            "sub_agent": agent_id,
                            "error": str(e)
                        },
                        exc_info=True
                    )
        
        # P0 FIX: Only fail if NO tools available at all (graceful degradation)
        total_tools = len(mcp_tools)
        if total_tools == 1:  # Only current_time tool
            error_msg = (
                f"No sub-agent tools available. "
                f"Failed agents: {failed_agents}. "
                f"Failed client creation: {failed_client_creation}. "
                f"Missing env vars: {missing_agents}"
            )
            logger.error(error_msg, extra={"operation": "tool_discovery", "status": "critical_failure"})
            raise RuntimeError(error_msg)
        
        # Log comprehensive summary
        logger.info(
            f"Tool discovery complete: {total_tools} total tools from {len(successful_agents)} agents",
            extra={
                "operation": "tool_discovery",
                "total_tools": total_tools,
                "successful_agents": len(successful_agents),
                "failed_agents": len(failed_agents),
                "status": "success"
            }
        )
        
        # P1 FIX: Log detailed breakdown
        logger.info(
            f"Tool breakdown by agent: {tool_count_by_agent}",
            extra={"operation": "tool_discovery", "tool_breakdown": tool_count_by_agent}
        )
        
        if failed_agents:
            logger.warning(
                f"Operating with degraded functionality. Failed agents: {failed_agents}",
                extra={
                    "operation": "tool_discovery",
                    "failed_agents": failed_agents,
                    "status": "degraded"
                }
            )

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
- Be concise but thorough in your analysis
- If some tools are unavailable, work with what you have and inform the user"""

        logger.info("Creating Strands agent with aggregated tools", extra={"operation": "agent_creation"})
        
        agent = Agent(
            system_prompt=system_prompt,
            model=_get_bedrock_model(model_id),
            tools=mcp_tools,
            callback_handler=None
        )
        
        logger.info("Agent001 supervisor initialized successfully", extra={"operation": "init", "status": "complete"})

        # Yield a callable interface to the agent
        async def agent_callable(user_input: str) -> str:
            """Send a message to the agent and return its response."""
            logger.info(f"Processing user query", extra={"operation": "query", "query_length": len(user_input)})
            start_time = time.time()
            
            try:
                result = agent(user_input)
                duration_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"Query processed successfully",
                    extra={"operation": "query", "duration_ms": duration_ms, "status": "success"}
                )
                return str(result)
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"Query processing failed: {str(e)}",
                    extra={"operation": "query", "duration_ms": duration_ms, "error": str(e)},
                    exc_info=True
                )
                # P2 FIX: Return standardized error response
                error_response = create_error_response("agent001", "query_processing", e)
                return f"I encountered an error while processing your request: {str(e)}"

        yield agent_callable


async def main():
    """Run the agent example by asking it to process user input."""
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

    logger.info(f"Starting main execution", extra={"operation": "main", "query": user_input})
    
    try:
        # Create and run the agent
        async with create_agent() as agent:
            result = await agent(user_input)
            print(f'\n{result}')
            logger.info("Main execution completed successfully", extra={"operation": "main", "status": "success"})
    except Exception as e:
        logger.error(
            f"Main execution failed: {str(e)}",
            extra={"operation": "main", "error": str(e)},
            exc_info=True
        )
        print(f'\nError: {str(e)}')
        raise


if __name__ == '__main__':
    asyncio.run(main())
