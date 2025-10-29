import os
from strands import Agent
from strands_tools import http_request
from strands.models import BedrockModel
from mcp.server.fastmcp import FastMCP
import boto3

model_id = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"

ESPN_NFL_SYSTEM_PROMPT = """You are an NFL information assistant with HTTP capabilities. You can:

1. Make HTTP requests to the ESPN NFL API
2. Retrieve and display NFL team information
3. Provide details about NFL teams including their records, logos, and venue information

When retrieving NFL team information:
1. Use the ESPN NFL Teams API: https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams
2. You can get all teams or filter by specific team abbreviations
3. Parse the JSON response to extract relevant team details

When displaying responses:
- Format team data in a human-readable way
- Highlight key information like team name, abbreviation, record, and location
- Include links to team logos and additional resources when available
- Handle errors appropriately
- Present information in a clear, organized manner

Always provide accurate and up-to-date NFL team information based on the API response.
"""

# Create a custom boto3 session
print("Initializing boto3 session")
session = boto3.Session(
    region_name='us-west-2',
)

# Create an MCP server
mcp = FastMCP("NFL Teams Server", host="0.0.0.0", stateless_http=True)

def _get_bedrock_model(m_id):
    return BedrockModel(
        inference_profile_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
    )

# Define a tool
@mcp.tool(description="NFL team lookup tool which returns information about NFL teams from the ESPN API based on the input query.")
def getNFLTeams(teamQuery: str) -> str:
    """
    Retrieve NFL team information from the ESPN API.
    
    Args:
        teamQuery: A query about NFL teams (e.g., "all teams", "Dallas Cowboys", "NFC East teams")
    
    Returns:
        Formatted information about NFL teams
    """
    agent = Agent(
        system_prompt=ESPN_NFL_SYSTEM_PROMPT,
        model=_get_bedrock_model(model_id),
        tools=[http_request]
    )
    return agent(teamQuery)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
