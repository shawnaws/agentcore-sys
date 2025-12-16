"""
NFL Game Predictions MCP Server (agent007)
Provides AI-powered predictions for upcoming NFL games
"""

import boto3
import json
import logging
import sys
from datetime import datetime
from strands import Agent
from strands.models import BedrockModel
from mcp.server.fastmcp import FastMCP
from strands_tools import current_time

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
            "agent": "agent007",
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

ESPN_NFL_PREDICTIONS_SYSTEM_PROMPT = """You are an NFL game prediction specialist with HTTP capabilities. Your job is to analyze upcoming NFL matchups and generate data-driven predictions.

Data Sources (with 30-second timeout):
1. ESPN NFL Scoreboard API: https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
2. ESPN NFL Teams API: https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams
3. ESPN NFL Team Schedule: https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{teamId}/schedule

Reliability Features:
- The system will automatically retry failed requests up to 2 times with exponential backoff (1s, 2s)
- Always check for expected fields in API responses before accessing them

Prediction Methodology:
1. **Identify Teams**: Parse the matchup query to identify both teams
2. **Gather Team Statistics**: 
   - Current season record
   - Points per game (offense)
   - Points allowed per game (defense)
   - Recent form (last 3-5 games)
3. **Analyze Head-to-Head History**: Look for recent matchups between these teams
4. **Consider Context**:
   - Home field advantage (typically worth 2-3 points)
   - Injuries or key player absences (if mentioned in query)
   - Weather conditions (if relevant)
   - Playoff implications or rivalry factors
5. **Generate Prediction**:
   - Win probability for each team
   - Predicted final score
   - Key factors influencing the prediction
   - Confidence level (High/Medium/Low)

Instructions:
- Use http_request tool to gather data from ESPN APIs with automatic retry on failures
- For team lookups, search the teams API to get team IDs
- For recent performance, check the scoreboard API with recent dates
- For schedules and upcoming games, use the team schedule endpoint
- Synthesize all data into a comprehensive prediction
- Be transparent about data limitations or missing information
- Provide reasoning for your prediction
- Handle API response parsing defensively, checking for expected fields

Response Format (REQUIRED):
🏈 NFL Game Prediction

**Matchup**: [Away Team (ABR)] @ [Home Team (ABR)]
**Date**: [Day, Month DD, YYYY at HH:MM AM/PM TZ]

**Prediction**: [Winning Team] wins
**Predicted Score**: [Winning Team] [Score], [Losing Team] [Score]
**Win Probability**: [Team A] [X]% | [Team B] [Y]%
**Confidence**: [High/Medium/Low]

**Key Factors**:
• [Factor 1 - e.g., Home field advantage (+3 points)]
• [Factor 2 - e.g., Offensive efficiency: Team A 28.5 PPG vs Team B 18.2 PA/G]
• [Factor 3 - e.g., Recent form: Team A 4-1 in last 5 games]
• [Factor 4 - e.g., Head-to-head: Team A won last 3 meetings]

**Analysis**:
[2-3 sentences explaining the reasoning behind the prediction, highlighting the most important factors and statistical advantages]

**Team Statistics**:
[Away Team (ABR)]: [W-L Record] | [PPG] PPG | [PA/G] PA/G
[Home Team (ABR)]: [W-L Record] | [PPG] PPG | [PA/G] PA/G

Formatting Standards:
- Team names: MUST include full name and abbreviation: "Dallas Cowboys (DAL)"
- Date/time: MUST include day of week: "Sunday, January 21, 2025 at 4:30 PM EST"
- Matchup: Use @ for away @ home: "Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)"
- Scores: Show winner first in predicted score
- Statistics: Use pipe separators for clarity
- Factors: Use bullet points with specific data when available

Error Handling:
- If teams cannot be identified, ask for clarification
- If the game has already been played, suggest using the scores tool instead
- If data is unavailable, make prediction based on available information and note limitations
- If the API is unavailable after retries, return: "The NFL prediction service is temporarily unavailable. Please try again in a moment."
- If the request times out, return: "The NFL data service is taking too long to respond. Please try again."
- If the API response is malformed or missing expected data, return: "I'm having trouble reading the NFL data right now. This has been logged for investigation."

Always provide well-reasoned predictions based on available data and clearly explain your methodology.
"""

# Initialize boto3 session
print("Initializing boto3 session")
session = boto3.Session(region_name="us-west-2")

# Create MCP server
mcp = FastMCP("NFL Predictions Server", host="0.0.0.0", stateless_http=True)


def _get_bedrock_model(m_id):
    """Initialize and return a Bedrock model instance."""
    return BedrockModel(
        model_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
    )


@mcp.tool(description="Generate AI-powered predictions for upcoming NFL games with win probability and analysis. Must provide teams, and dates.")
def predictNFLGame(matchupQuery: str) -> str:
    """
    Generate predictions for upcoming NFL games with error handling and retries.
    
    Args:
        matchupQuery: Natural language query like "Cowboys vs Eagles prediction", 
                     "who will win Sunday night game", "predict Chiefs Bills"
    
    Returns:
        Prediction with win probability, predicted score, key factors, and analysis
    """
    logger.info("predictNFLGame invoked", extra={"tool": "predictNFLGame", "query": matchupQuery})
    
    try:
        agent = Agent(
            system_prompt=ESPN_NFL_PREDICTIONS_SYSTEM_PROMPT,
            model=_get_bedrock_model(model_id),
            tools=[http_request_with_retry, current_time]
        )
        result = agent(matchupQuery)
        logger.info("predictNFLGame completed successfully", extra={"tool": "predictNFLGame"})
        return str(result)
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "predictNFLGame failed",
            extra={
                "tool": "predictNFLGame",
                "query": matchupQuery,
                "error": error_msg
            }
        )
        return "I encountered an error while generating NFL game predictions. Please try again or rephrase your question."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
