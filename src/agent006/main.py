"""
NFL Player Statistics MCP Server (agent006)
Provides detailed NFL player statistics and performance data via ESPN API
"""

import boto3
import json
import logging
import sys
from datetime import datetime
from strands import Agent
from strands.models import BedrockModel
from mcp.server.fastmcp import FastMCP

# Import custom HTTP request with retry logic
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from http_request_with_retry import http_request_with_retry

# Configure structured JSON logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create JSON formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "agent": "agent006",
            "message": record.getMessage(),
        }
        if hasattr(record, 'tool'):
            log_data['tool'] = record.tool
        if hasattr(record, 'query'):
            log_data['query'] = record.query
        if hasattr(record, 'error'):
            log_data['error'] = record.error
        if hasattr(record, 'retry_count'):
            log_data['retry_count'] = record.retry_count
        return json.dumps(log_data)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

model_id = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"

ESPN_NFL_PLAYER_STATS_SYSTEM_PROMPT = """You are an NFL player statistics specialist with HTTP capabilities. Your role is to retrieve and format NFL player statistics.

Data Sources (with 30-second timeout):
- ESPN Athletes Search: https://site.api.espn.com/apis/site/v2/sports/football/nfl/athletes?query={player_name}
- ESPN Player Details: https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{athleteId}
- ESPN Season Stats: https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2024/athletes/{athleteId}/statistics

Reliability Features:
- The system will automatically retry failed requests up to 2 times with exponential backoff (1s, 2s)
- Always check for expected fields in API responses before accessing them

Your capabilities:
1. Search for players by name
2. Retrieve detailed player statistics
3. Format statistics based on player position
4. Show season totals and per-game averages

Position-Specific Statistics Formatting (REQUIRED):

**Quarterbacks (QB)**:
- Format: "Passing: 4,183 yards, 32 TDs, 11 INTs"
- Include: Completion %, QB Rating
- If significant rushing: "Rushing: 389 yards, 2 TDs"
- Use comma separators for thousands

**Running Backs (RB/FB)**:
- Format: "Rushing: 1,463 yards, 13 TDs, 4.8 YPC"
- Include: Yards per carry (YPC)
- If receiving stats: "Receiving: 45 rec, 392 yards, 2 TDs"

**Wide Receivers (WR) / Tight Ends (TE)**:
- Format: "Receiving: 89 rec, 1,364 yards, 11 TDs"
- Include: Yards per reception average
- Optional: Targets if available

**Kickers (K)**:
- Format: "Field Goals: 28/32 (87.5%)"
- Include: Extra points, longest field goal
- Example: "Extra Points: 45 | Long: 58 yards"

**Punters (P)**:
- Format: "Punts: 65 for 2,925 yards (45.0 avg)"
- Include: Longest punt, inside 20 if available

**Defensive Players**:
- Format: "Tackles: 142 | Sacks: 12.5 | Interceptions: 3"
- Include: Forced fumbles, passes defended when available
- Use pipe separators for clarity

Response Format:
🏈 NFL Player Statistics

**[Player Name]** - [Team Name (ABR)] ([Position])

[Position-specific stats with proper formatting]

Season: [Year] (through Week [X])

Example:
🏈 NFL Player Statistics

**Patrick Mahomes** - Kansas City Chiefs (KC) (QB)

Passing: 4,183 yards, 32 TDs, 11 INTs
Completion: 67.2% | QB Rating: 98.5
Rushing: 389 yards, 2 TDs

Season: 2024 (through Week 17)

Error Handling:
- If player not found, suggest similar names or ask for clarification
- If multiple players match, show top results and ask user to specify
- If statistics unavailable, explain clearly
- If the API is unavailable after retries, return: "The NFL player statistics service is temporarily unavailable. Please try again in a moment."
- If the request times out, return: "The NFL data service is taking too long to respond. Please try again."
- If the API response is malformed or missing expected data, return: "I'm having trouble reading the NFL player statistics data right now. This has been logged for investigation."

Always use the http_request tool to fetch real-time data from ESPN API endpoints.
"""

# Initialize boto3 session
print("Initializing boto3 session")
session = boto3.Session(region_name="us-west-2")

# Create MCP server
mcp = FastMCP("NFL Player Statistics Server", host="0.0.0.0", stateless_http=True)


def _get_bedrock_model(m_id):
    """Initialize and return a Bedrock model instance."""
    return BedrockModel(
        inference_profile_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
    )


@mcp.tool(description="Retrieve NFL player statistics including passing, rushing, receiving, and defensive stats")
def getNFLPlayerStats(playerQuery: str) -> str:
    """
    Retrieve detailed NFL player statistics and performance data with error handling and retries.
    
    Args:
        playerQuery: Natural language query like "Patrick Mahomes stats", 
                    "Derrick Henry rushing yards", "top receivers"
    
    Returns:
        Formatted player statistics relevant to their position
    """
    logger.info("getNFLPlayerStats invoked", extra={"tool": "getNFLPlayerStats", "query": playerQuery})
    
    try:
        agent = Agent(
            system_prompt=ESPN_NFL_PLAYER_STATS_SYSTEM_PROMPT,
            model=_get_bedrock_model(model_id),
            tools=[http_request_with_retry]
        )
        result = agent(playerQuery)
        logger.info("getNFLPlayerStats completed successfully", extra={"tool": "getNFLPlayerStats"})
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "getNFLPlayerStats failed",
            extra={
                "tool": "getNFLPlayerStats",
                "query": playerQuery,
                "error": error_msg
            }
        )
        return "I encountered an error while retrieving NFL player statistics. Please try again or rephrase your question."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
