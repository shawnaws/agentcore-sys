import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
import boto3

print("Initializing bedrock agentcore app")
app = BedrockAgentCoreApp()

model_id = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"

# Create a custom boto3 session
print("Initializing boto3 session")
session = boto3.Session(
    region_name='us-west-2',
)

def _get_bedrock_model(m_id):
    return BedrockModel(
        inference_profile_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
    )

def _initialize_mcp_clients():
    """
    Initialize MCP client connections for all MCP servers.
    Returns a dictionary of client names to MCPClient instances.
    Handles missing environment variables gracefully.
    """
    mcp_servers = {
        'weather': os.environ.get('AGENT002_URL'),
        'nfl_teams': os.environ.get('AGENT003_URL'),
        'nfl_scores': os.environ.get('AGENT004_URL'),
        'nfl_schedule': os.environ.get('AGENT005_URL'),
        'nfl_stats': os.environ.get('AGENT006_URL'),
        'nfl_predictions': os.environ.get('AGENT007_URL'),
    }
    
    mcp_clients = {}
    for client_name, url in mcp_servers.items():
        if url:
            try:
                print(f"Initializing MCP client for {client_name} at {url}")
                mcp_clients[client_name] = MCPClient(url=url)
            except Exception as e:
                print(f"Warning: Failed to initialize MCP client for {client_name}: {e}")
        else:
            print(f"Warning: No URL configured for {client_name} (environment variable not set)")
    
    return mcp_clients

def _aggregate_tools(mcp_clients):
    """
    Discover and aggregate tools from all available MCP servers.
    Returns a list of all available tools.
    Handles unavailable servers gracefully.
    """
    all_tools = []
    
    for client_name, client in mcp_clients.items():
        try:
            print(f"Discovering tools from {client_name}")
            with client:
                tools = client.list_tools_sync()
                all_tools.extend(tools)
                print(f"Found {len(tools)} tool(s) from {client_name}")
        except Exception as e:
            print(f"Warning: Failed to retrieve tools from {client_name}: {e}")
            print(f"Continuing with other available MCP servers...")
    
    print(f"Total tools aggregated: {len(all_tools)}")
    return all_tools

# Initialize MCP clients at startup
print("Initializing MCP clients...")
mcp_clients = _initialize_mcp_clients()

# Aggregate tools from all MCP servers
print("Aggregating tools from MCP servers...")
available_tools = _aggregate_tools(mcp_clients)

@app.entrypoint
def invoke(payload):
    """
    Process user input and return a response.
    Uses aggregated tools from all available MCP servers.
    """
    print("Processing user input")
    user_message = payload.get("prompt", "Hello! How can I help you today?")
    
    # Create agent with all available tools
    agent = Agent(
        model=_get_bedrock_model(model_id),
        tools=available_tools
    )
    
    try:
        response = agent(user_message)
        return response
    except Exception as e:
        error_message = f"Error processing request: {str(e)}"
        print(error_message)
        return {"error": error_message}

if __name__ == "__main__":
    app.run()
