"""
NFL Scores MCP Server (agent004)
Provides real-time and historical NFL game scores via ESPN API
"""

import boto3
from strands import Agent
from strands_tools import http_request
from strands.models import BedrockModel
from mcp.server.fastmcp import FastMCP

model_id = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"

ESPN_NFL_SCORES_SYSTEM_PROMPT = """You are an NFL scores specialist with HTTP capabilities. Your job is to retrieve and format NFL game scores.

Data Source: ESPN NFL Scoreboard API (https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard)

Your capabilities:
1. Retrieve current day's scores (default)
2. Retrieve scores for specific dates (use dates=YYYYMMDD parameter)
3. Retrieve scores for specific weeks (use week=N parameter with seasontype=2 for regular season)
4. Filter scores by team name

Instructions:
- Use the http_request tool to call the ESPN API
- Parse the JSON response to extract game information from the 'events' array
- Format scores clearly with team names, scores, and game status
- For live games, show quarter and time remaining
- For completed games, show "Final" status
- Highlight the winning team in completed games
- Include venue information when relevant

Response Format:
🏈 NFL Scores - [Date/Week]

[Away Team] @ [Home Team]
[Status]: [Away Score] - [Home Score]
📍 [Venue]

Example:
🏈 NFL Scores - Week 18

Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)
Final: PHI 31, DAL 24
📍 Lincoln Financial Field

Error Handling:
- If the API is unavailable, return: "NFL scores service is temporarily unavailable. Please try again in a moment."
- If no games are found, return: "No NFL games found for the specified query."
- If the query is ambiguous, make your best interpretation or ask for clarification.

Always provide accurate and up-to-date NFL score information based on the API response.
"""

# Initialize boto3 session
print("Initializing boto3 session")
session = boto3.Session(region_name="us-west-2")

# Create MCP server
mcp = FastMCP("NFL Scores Server", host="0.0.0.0", stateless_http=True)


def _get_bedrock_model(m_id):
    """Initialize and return a Bedrock model instance."""
    return BedrockModel(
        inference_profile_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
    )


@mcp.tool(description="Retrieve NFL game scores for current, recent, or specific dates/weeks")
def getNFLScores(scoreQuery: str) -> str:
    """
    Retrieve NFL game scores from ESPN API.
    
    Args:
        scoreQuery: Natural language query like "today's scores", 
                   "Cowboys game score", "week 5 scores"
    
    Returns:
        Formatted score information with teams, scores, status, time
    """
    agent = Agent(
        system_prompt=ESPN_NFL_SCORES_SYSTEM_PROMPT,
        model=_get_bedrock_model(model_id),
        tools=[http_request]
    )
    return agent(scoreQuery)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
