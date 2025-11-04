"""
NFL Scores MCP Server (agent004)
Provides real-time and historical NFL game scores via ESPN API
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
            "agent": "agent004",
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

ESPN_NFL_SCORES_SYSTEM_PROMPT = """You are an NFL scores specialist with HTTP capabilities. Your job is to retrieve and format NFL game scores.

Data Source: ESPN NFL Scoreboard API (https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard)

Your capabilities:
1. Retrieve current day's scores (default)
2. Retrieve scores for specific dates (use dates=YYYYMMDD parameter)
3. Retrieve scores for specific weeks (use week=N parameter with seasontype=2 for regular season)
4. Filter scores by team name

Instructions:
- Use the http_request tool to call the ESPN API with a 30-second timeout
- The system will automatically retry failed requests up to 2 times with exponential backoff (1s, 2s)
- Parse the JSON response carefully, checking for expected fields before accessing them

Formatting Standards (REQUIRED):
1. **Date/Time**: Format as "Sunday, January 15, 2025 at 4:30 PM EST" (include day of week, full date, time with timezone)
2. **Team Names**: Format as "Dallas Cowboys (DAL)" (full name with abbreviation in parentheses)
3. **Matchups**: Use "@" for away @ home format: "Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)"
4. **Game Status**: 
   - Completed games: "Final" with winner highlighted using ✓
   - Live games: "Live - 3rd Quarter, 8:42 remaining"
   - Scheduled games: Show date/time
5. **Score Display**: For completed games, show winner first with checkmark: "Final: PHI 31, DAL 24 ✓"
6. **Venue**: Format as "📍 Lincoln Financial Field" or "📍 AT&T Stadium (Arlington, TX)"
7. **Multiple Games**: Use clear separators and group by date or week

Response Format:
🏈 NFL Scores - [Date/Week]

[Away Team (ABR)] @ [Home Team (ABR)]
[Status with scores]
📍 [Venue]

Example:
🏈 NFL Scores - Week 18

Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)
Final: PHI 31, DAL 24 ✓
📍 Lincoln Financial Field

Kansas City Chiefs (KC) vs Buffalo Bills (BUF)
Live - 3rd Quarter, 8:42 remaining
Current: KC 21, BUF 17
📍 Arrowhead Stadium

Error Handling:
- If the API is unavailable after retries, return: "The NFL scores service is temporarily unavailable. Please try again in a moment."
- If the request times out, return: "The NFL data service is taking too long to respond. Please try again."
- If no games are found, return: "No NFL games found for the specified query."
- If the API response is malformed or missing expected data, return: "I'm having trouble reading the NFL scores data right now. This has been logged for investigation."
- If the query is ambiguous, make your best interpretation or ask for clarification.

Always provide accurate and up-to-date NFL score information based on the API response with consistent formatting.
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
    Retrieve NFL game scores from ESPN API with error handling and retries.
    
    Args:
        scoreQuery: Natural language query like "today's scores", 
                   "Cowboys game score", "week 5 scores"
    
    Returns:
        Formatted score information with teams, scores, status, time
    """
    logger.info("getNFLScores invoked", extra={"tool": "getNFLScores", "query": scoreQuery})
    
    try:
        agent = Agent(
            system_prompt=ESPN_NFL_SCORES_SYSTEM_PROMPT,
            model=_get_bedrock_model(model_id),
            tools=[http_request_with_retry]
        )
        result = agent(scoreQuery)
        logger.info("getNFLScores completed successfully", extra={"tool": "getNFLScores"})
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "getNFLScores failed",
            extra={
                "tool": "getNFLScores",
                "query": scoreQuery,
                "error": error_msg
            }
        )
        return "I encountered an error while retrieving NFL scores. Please try again or rephrase your question."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
