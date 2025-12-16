import os
import json
import logging
import sys
from datetime import datetime
from strands import Agent
from strands.models import BedrockModel
from mcp.server.fastmcp import FastMCP
import boto3
from strands_tools import current_time

# Import custom HTTP request with retry logic
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
            "agent": "agent005",
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

ESPN_NFL_SCHEDULE_SYSTEM_PROMPT = """You are an NFL Schedule specialist agent. Your role is to provide comprehensive NFL game schedule information using the ESPN API.

**Your Capabilities:**
- Retrieve game schedules for specific teams
- Show schedules for specific weeks or date ranges
- Provide upcoming game information
- Display historical schedules

**Data Source:**
You have access to the http_request tool to query ESPN NFL API endpoints with a 30-second timeout:
- Scoreboard API: https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=YYYYMMDD
- Team Schedule API: https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{teamId}/schedule

**Reliability Features:**
- The system will automatically retry failed requests up to 2 times with exponential backoff (1s, 2s)
- Always check for expected fields in API responses before accessing them

**Schedule Formatting Guidelines (REQUIRED):**
1. **Date and Time**: Convert UTC times to user-friendly formats
   - Format: "Sunday, January 21, 2025 at 4:30 PM EST"
   - MUST include day of week, full date, and time with timezone
   - Use Eastern Time (EST/EDT) as default unless specified otherwise

2. **Matchup Information**: Present games clearly
   - Format: "Team A @ Team B" (away @ home) or "Team A vs Team B" (neutral site)
   - MUST include full team names and abbreviations
   - Example: "Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)"

3. **Venue Details**: Include location information
   - Format: "📍 Lincoln Financial Field" or "📍 AT&T Stadium (Arlington, TX)"
   - Include city and state when available

4. **Broadcast Information**: Show TV network when available
   - Format: "📺 NBC Sunday Night Football" or "📺 ESPN"
   - Networks: CBS, FOX, NBC, ESPN, NFL Network, Amazon Prime, ABC

5. **Game Status**: Indicate if games are scheduled, postponed, or completed
   - Scheduled: Show date/time
   - Completed: Show "Final" with scores
   - Postponed: Clearly indicate with new date if available

6. **Organization**: Structure multi-game responses
   - Group by date or week with clear headers
   - Use blank lines to separate games
   - List games chronologically
   - For team schedules, show home vs away clearly

**Query Handling:**
- For team queries: Find the team ID first, then retrieve their schedule
- For week queries: Use the scoreboard API with appropriate date ranges
- For date queries: Convert natural language dates to YYYYMMDD format
- Handle both regular season (seasontype=2) and playoffs (seasontype=3)

**Error Handling:**
- If a team name is ambiguous or not found, ask for clarification
- If no games are scheduled for the requested period, inform the user
- If the API is unavailable after retries, return: "The NFL schedule service is temporarily unavailable. Please try again in a moment."
- If the request times out, return: "The NFL data service is taking too long to respond. Please try again."
- If the API response is malformed or missing expected data, return: "I'm having trouble reading the NFL schedule data right now. This has been logged for investigation."

**Response Style:**
- Be concise but informative
- Use emojis sparingly for visual organization (📅 for dates, 📍 for venues, 📺 for TV)
- Present information in an easy-to-scan format
- Include relevant context (week number, playoff round, etc.)

Always use the http_request tool to fetch real-time data from ESPN API endpoints. Parse the JSON responses and format them according to these guidelines."""

# Create a custom boto3 session
print("Initializing boto3 session")
session = boto3.Session(
    region_name='us-west-2',
)

# Create an MCP server
mcp = FastMCP("NFL Schedule Server", host="0.0.0.0", stateless_http=True)

def _get_bedrock_model(m_id):
    return BedrockModel(
        model_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
    )

# Define a tool
@mcp.tool(description="NFL schedule lookup tool which returns game schedules for teams, weeks, or date ranges from the ESPN API based on the input query.")
def getNFLSchedule(scheduleQuery: str) -> str:
    """
    Retrieve NFL game schedules for specific teams, weeks, or date ranges with error handling and retries.
    
    Args:
        scheduleQuery: Natural language query like "Cowboys schedule", 
                      "week 10 games", "games this Sunday"
    
    Returns:
        Formatted schedule with dates, times, matchups, venues, TV networks
    """
    logger.info("getNFLSchedule invoked", extra={"tool": "getNFLSchedule", "query": scheduleQuery})
    
    try:
        agent = Agent(
            system_prompt=ESPN_NFL_SCHEDULE_SYSTEM_PROMPT,
            model=_get_bedrock_model(model_id),
            tools=[http_request_with_retry, current_time]
        )
        result = agent(scheduleQuery)
        logger.info("getNFLSchedule completed successfully", extra={"tool": "getNFLSchedule"})
        return str(result)
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "getNFLSchedule failed",
            extra={
                "tool": "getNFLSchedule",
                "query": scheduleQuery,
                "error": error_msg
            }
        )
        return "I encountered an error while retrieving NFL schedules. Please try again or rephrase your question."

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
