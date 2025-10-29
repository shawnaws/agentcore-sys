# Design Document

## Overview

This design document outlines the architecture and implementation approach for expanding the NFL multi-agent system with four new specialized MCP server agents. The expansion builds upon the existing three-agent foundation (agent001: main chat interface, agent002: weather MCP server, agent003: NFL teams MCP server) by adding agents for live scores (agent004), schedules (agent005), player statistics (agent006), and game predictions (agent007).

The design maintains architectural consistency with the existing system, using the Strands framework, FastMCP for MCP server implementation, AWS Bedrock for LLM capabilities, and CDK for infrastructure deployment.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    agent001 (Main Chat Agent)                   │
│                  - Orchestrates conversations                   │
│                  - Routes to specialized agents                 │
│                  - Aggregates responses                         │
└─────────┬───────────────────────────────────────────────────────┘
          │
          │ MCPClient connections
          │
          ├──────────┬──────────┬──────────┬──────────┬──────────┐
          ▼          ▼          ▼          ▼          ▼          ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│   agent002  │ │ agent003│ │ agent004│ │ agent005│ │ agent006│ │ agent007│
│   Weather   │ │NFL Teams│ │NFL Scores│ │NFL Sched│ │NFL Stats│ │NFL Pred │
│ MCP Server  │ │MCP Server│ │MCP Server│ │MCP Server│ │MCP Server│ │MCP Server│
└──────┬──────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
       │             │             │             │             │             │
       ▼             ▼             ▼             ▼             ▼             ▼
┌─────────────┐ ┌──────────────────────────────────────────────────────────┐
│ Weather.gov │ │              ESPN NFL API Endpoints                      │
│     API     │ │  - /teams  - /scoreboard  - /schedule  - /athletes       │
└─────────────┘ └──────────────────────────────────────────────────────────┘
```

### Agent Communication Flow

1. **User → agent001**: User sends natural language query
2. **agent001 → MCPClient**: Main agent discovers available tools from connected MCP servers
3. **agent001 → MCP Server(s)**: Routes request to appropriate specialized agent(s)
4. **MCP Server → ESPN API**: Specialized agent makes HTTP request to ESPN API
5. **MCP Server → agent001**: Returns formatted response
6. **agent001 → User**: Delivers final response with aggregated information

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Account                              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              AgentCore Gateway                            │ │
│  │  - MCP protocol routing                                   │ │
│  │  - Semantic search for tools                              │ │
│  │  - OpenAPI target integration                             │ │
│  └─────────────────────┬─────────────────────────────────────┘ │
│                        │                                         │
│  ┌─────────────────────┴─────────────────────────────────────┐ │
│  │           AgentCore Runtime Environments                  │ │
│  │                                                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │ │
│  │  │ agent001 │  │ agent002 │  │ agent003 │  │ agent004 │ │ │
│  │  │  (HTTP)  │  │  (MCP)   │  │  (MCP)   │  │  (MCP)   │ │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │ │
│  │                                                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │ │
│  │  │ agent005 │  │ agent006 │  │ agent007 │               │ │
│  │  │  (MCP)   │  │  (MCP)   │  │  (MCP)   │               │ │
│  │  └──────────┘  └──────────┘  └──────────┘               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Amazon Bedrock                               │ │
│  │  - Claude Sonnet 4.5 model                                │ │
│  │  - Cross-region inference profiles                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              AWS Cognito                                  │ │
│  │  - User pool for OAuth2                                   │ │
│  │  - Client credentials flow                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Amazon ECR                                   │ │
│  │  - Docker images for each agent                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Component 1: NFL Scores MCP Server (agent004)

**Purpose**: Provide real-time and historical NFL game scores

**Key Components**:
- FastMCP server with `getNFLScores` tool
- ESPN Scoreboard API integration
- Score formatting and presentation logic

**ESPN API Endpoints**:
- `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard` - Current/recent games
- Query parameters: `dates=YYYYMMDD`, `week=N`, `seasontype=2` (regular season)

**Tool Interface**:
```python
@mcp.tool(description="Retrieve NFL game scores for current, recent, or specific dates/weeks")
def getNFLScores(scoreQuery: str) -> str:
    """
    Args:
        scoreQuery: Natural language query like "today's scores", 
                   "Cowboys game score", "week 5 scores"
    Returns:
        Formatted score information with teams, scores, status, time
    """
```

**System Prompt Focus**:
- Parse score data including quarter/final status
- Format time remaining and game clock
- Highlight winning team in completed games
- Show live game status (1st Quarter, Halftime, etc.)

### Component 2: NFL Schedule MCP Server (agent005)

**Purpose**: Provide upcoming and historical NFL game schedules

**Key Components**:
- FastMCP server with `getNFLSchedule` tool
- ESPN Calendar/Schedule API integration
- Date/time formatting with timezone handling

**ESPN API Endpoints**:
- `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=YYYYMMDD` - Schedule for specific date
- `https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{teamId}/schedule` - Team-specific schedule

**Tool Interface**:
```python
@mcp.tool(description="Retrieve NFL game schedules for teams, weeks, or date ranges")
def getNFLSchedule(scheduleQuery: str) -> str:
    """
    Args:
        scheduleQuery: Natural language query like "Cowboys schedule", 
                      "week 10 games", "games this Sunday"
    Returns:
        Formatted schedule with dates, times, matchups, venues, TV networks
    """
```

**System Prompt Focus**:
- Convert UTC times to user-friendly formats
- Include venue information and location
- Show broadcast network (CBS, FOX, NBC, ESPN, etc.)
- Distinguish between home and away games

### Component 3: NFL Player Statistics MCP Server (agent006)

**Purpose**: Provide detailed NFL player statistics and performance data

**Key Components**:
- FastMCP server with `getNFLPlayerStats` tool
- ESPN Athletes API integration
- Position-specific stat formatting

**ESPN API Endpoints**:
- `https://site.api.espn.com/apis/site/v2/sports/football/nfl/athletes` - Search players
- `https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{athleteId}` - Player details
- `https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{year}/athletes/{athleteId}/statistics` - Season stats

**Tool Interface**:
```python
@mcp.tool(description="Retrieve NFL player statistics including passing, rushing, receiving, and defensive stats")
def getNFLPlayerStats(playerQuery: str) -> str:
    """
    Args:
        playerQuery: Natural language query like "Patrick Mahomes stats", 
                    "Derrick Henry rushing yards", "top receivers"
    Returns:
        Formatted player statistics relevant to their position
    """
```

**System Prompt Focus**:
- Position-aware stat selection (QB: passing, RB: rushing, WR: receiving, etc.)
- Season totals and per-game averages
- Recent game performance
- Career highlights and records

### Component 4: NFL Game Predictions MCP Server (agent007)

**Purpose**: Generate AI-powered predictions for upcoming NFL games

**Key Components**:
- FastMCP server with `predictNFLGame` tool
- Multi-source data aggregation (team stats, recent performance, head-to-head)
- Bedrock model for analysis and prediction generation

**Data Sources** (via HTTP requests):
- Team statistics from ESPN API
- Recent game results and trends
- Head-to-head historical data
- Current season standings and records

**Tool Interface**:
```python
@mcp.tool(description="Generate AI-powered predictions for upcoming NFL games with win probability and analysis")
def predictNFLGame(matchupQuery: str) -> str:
    """
    Args:
        matchupQuery: Natural language query like "Cowboys vs Eagles prediction", 
                     "who will win Sunday night game"
    Returns:
        Prediction with win probability, predicted score, key factors
    """
```

**System Prompt Focus**:
- Gather team statistics (offensive/defensive rankings, points per game)
- Analyze recent performance (last 3-5 games)
- Consider home field advantage
- Evaluate head-to-head history
- Generate win probability and score prediction
- Explain key factors influencing prediction

**Prediction Methodology**:
1. Retrieve both teams' current season statistics
2. Analyze recent game performance and trends
3. Consider home/away advantage
4. Review head-to-head historical matchups
5. Use Bedrock model to synthesize data and generate prediction
6. Format output with confidence level and reasoning

### Component 5: Main Chat Agent (agent001) - Enhanced Integration

**Current State**: Basic structure exists but needs MCP client integration

**Required Enhancements**:
- Initialize MCPClient connections to all MCP servers (agent002-007)
- Implement tool discovery and routing logic
- Add response aggregation for multi-tool queries
- Enhance error handling for MCP server failures

**Updated Structure**:
```python
from strands.tools.mcp.mcp_client import MCPClient

# Initialize MCP clients for each server
mcp_clients = {
    'weather': MCPClient(url=os.environ.get('AGENT002_URL')),
    'nfl_teams': MCPClient(url=os.environ.get('AGENT003_URL')),
    'nfl_scores': MCPClient(url=os.environ.get('AGENT004_URL')),
    'nfl_schedule': MCPClient(url=os.environ.get('AGENT005_URL')),
    'nfl_stats': MCPClient(url=os.environ.get('AGENT006_URL')),
    'nfl_predictions': MCPClient(url=os.environ.get('AGENT007_URL')),
}

# Aggregate tools from all MCP servers
all_tools = []
for client_name, client in mcp_clients.items():
    with client:
        tools = client.list_tools_sync()
        all_tools.extend(tools)

# Create agent with all available tools
agent = Agent(
    model=_get_bedrock_model(model_id),
    tools=all_tools
)
```

**Tool Routing Strategy**:
- Automatic routing based on tool selection by Bedrock model
- No explicit routing logic needed - model chooses appropriate tool
- Error handling for unavailable MCP servers

## Data Models

### ESPN API Response Models

**Scoreboard Response**:
```json
{
  "events": [
    {
      "id": "401671716",
      "name": "Dallas Cowboys at Philadelphia Eagles",
      "date": "2025-01-15T21:30Z",
      "competitions": [
        {
          "competitors": [
            {
              "team": {"displayName": "Dallas Cowboys", "abbreviation": "DAL"},
              "score": "24",
              "homeAway": "away"
            },
            {
              "team": {"displayName": "Philadelphia Eagles", "abbreviation": "PHI"},
              "score": "31",
              "homeAway": "home"
            }
          ],
          "status": {
            "type": {"completed": true, "description": "Final"},
            "displayClock": "0:00",
            "period": 4
          },
          "venue": {"fullName": "Lincoln Financial Field"}
        }
      ]
    }
  ]
}
```

**Team Response**:
```json
{
  "sports": [
    {
      "leagues": [
        {
          "teams": [
            {
              "team": {
                "id": "6",
                "displayName": "Dallas Cowboys",
                "abbreviation": "DAL",
                "record": {"items": [{"summary": "12-5"}]}
              }
            }
          ]
        }
      ]
    }
  ]
}
```

**Athlete Response**:
```json
{
  "displayName": "Patrick Mahomes",
  "position": {"abbreviation": "QB"},
  "statistics": {
    "splits": {
      "categories": [
        {
          "name": "passing",
          "stats": [
            {"name": "passingYards", "value": 4183},
            {"name": "passingTouchdowns", "value": 32}
          ]
        }
      ]
    }
  }
}
```

### Internal Data Models

**Formatted Score Output**:
```
🏈 NFL Scores - Week 18

Dallas Cowboys (DAL) @ Philadelphia Eagles (PHI)
Final: PHI 31, DAL 24
📍 Lincoln Financial Field

Kansas City Chiefs (KC) vs Buffalo Bills (BUF)
Live - 3rd Quarter, 8:42 remaining
Current: KC 21, BUF 17
```

**Formatted Schedule Output**:
```
📅 Dallas Cowboys Schedule - Week 19 (Playoffs)

Sunday, January 21, 2025 at 4:30 PM EST
Dallas Cowboys @ San Francisco 49ers
📍 Levi's Stadium
📺 FOX
```

**Formatted Player Stats Output**:
```
🏈 Patrick Mahomes - Kansas City Chiefs (QB)

2024 Season Statistics:
• Passing Yards: 4,183 (261.4 per game)
• Touchdowns: 32
• Interceptions: 11
• Completion %: 67.8%
• QB Rating: 98.5
```

## Error Handling

### ESPN API Error Scenarios

**1. Rate Limiting**:
- ESPN API may throttle requests
- Implement exponential backoff (1s, 2s, 4s)
- Maximum 2 retry attempts
- Return user-friendly message: "NFL data service is temporarily busy. Please try again in a moment."

**2. Invalid Team/Player Names**:
- ESPN API returns empty results for unknown entities
- Detect empty response arrays
- Return helpful message: "I couldn't find information for '{query}'. Please check the spelling or try a different search."

**3. Network Timeouts**:
- Set 30-second timeout for HTTP requests
- Catch timeout exceptions
- Return message: "The NFL data service is taking too long to respond. Please try again."

**4. API Endpoint Changes**:
- ESPN may change API structure without notice
- Implement defensive parsing with try-catch blocks
- Log parsing errors to CloudWatch
- Return message: "I'm having trouble reading the NFL data right now. This has been logged for investigation."

### MCP Server Error Handling

**1. Server Unavailable**:
- MCPClient connection fails
- Main agent detects missing tools
- Return message: "The {capability} service is temporarily unavailable. Other features are still working."

**2. Tool Execution Failure**:
- MCP tool raises exception
- Catch and log exception
- Return message: "I encountered an error while retrieving {data type}. Please try again or rephrase your question."

**3. Malformed Responses**:
- MCP server returns unexpected format
- Validate response structure
- Return partial data if possible, or error message

### Error Logging Strategy

**CloudWatch Logs**:
- All agents log to CloudWatch Logs
- Log levels: INFO (requests), WARNING (retries), ERROR (failures)
- Include request ID, timestamp, error details
- Structured logging with JSON format

**Log Format**:
```json
{
  "timestamp": "2025-01-15T20:30:00Z",
  "level": "ERROR",
  "agent": "agent004",
  "tool": "getNFLScores",
  "error": "ESPN API timeout",
  "query": "today's scores",
  "retry_count": 2
}
```

## Testing Strategy

### Local Testing Approach

**1. Individual Agent Testing**:
Each agent can be tested locally before deployment:

```bash
# Start agent locally
cd src/agent004
python main.py

# Test with curl
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "getNFLScores",
    "arguments": {"scoreQuery": "today'\''s scores"}
  }'
```

**2. MCP Server Testing**:
Test MCP protocol compliance:

```bash
# Test tool listing
curl -X POST http://localhost:8080/mcp/tools/list \
  -H "Content-Type: application/json"

# Test tool invocation
curl -X POST http://localhost:8080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "getNFLScores",
    "arguments": {"scoreQuery": "Cowboys score"}
  }'
```

**3. ESPN API Integration Testing**:
Verify API responses and parsing:

```python
# Test script for ESPN API
import requests

def test_scoreboard_api():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    response = requests.get(url)
    assert response.status_code == 200
    data = response.json()
    assert 'events' in data
    print(f"Found {len(data['events'])} games")

def test_teams_api():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
    response = requests.get(url)
    assert response.status_code == 200
    data = response.json()
    teams = data['sports'][0]['leagues'][0]['teams']
    print(f"Found {len(teams)} teams")
```

**4. Integration Testing with Main Agent**:
Test agent001 with MCP server connections:

```python
# Mock MCP servers for testing
# Test tool discovery
# Test query routing
# Test response aggregation
```

### Deployment Testing

**1. CDK Synthesis Validation**:
```bash
cd infra
npm run build
npm run cdk synth
# Verify CloudFormation template
```

**2. Deployment Smoke Tests**:
After deployment, verify each agent:
- Check CloudWatch logs for initialization
- Invoke each agent via AgentCore Gateway
- Verify tool availability
- Test sample queries

**3. End-to-End Testing**:
Test complete user workflows:
- "What's the Cowboys score?" → agent004
- "When do the Cowboys play next?" → agent005
- "Show me Patrick Mahomes stats" → agent006
- "Predict Cowboys vs Eagles" → agent007
- "What's the weather in Dallas and when do the Cowboys play?" → agent002 + agent005

### Test Data Strategy

**Mock ESPN API Responses**:
- Create sample JSON responses for each endpoint
- Use for unit testing without API calls
- Ensure consistent test data

**Test Queries**:
- Maintain list of test queries for each agent
- Cover common use cases and edge cases
- Include ambiguous queries to test error handling

## Infrastructure Configuration

### CDK Stack Updates

**New Agent Configurations** (infra/bin/infra.ts):

```typescript
agentConfigs: [
  {
    agentName: 'agent001',
    sourcePath: '../../src/agent001',
    protocol: 'HTTP',
    envVars: {
      "USEGATEWAY": "true",
      "AGENT002_URL": "${GATEWAY_URL}/mcp/agent002",
      "AGENT003_URL": "${GATEWAY_URL}/mcp/agent003",
      "AGENT004_URL": "${GATEWAY_URL}/mcp/agent004",
      "AGENT005_URL": "${GATEWAY_URL}/mcp/agent005",
      "AGENT006_URL": "${GATEWAY_URL}/mcp/agent006",
      "AGENT007_URL": "${GATEWAY_URL}/mcp/agent007",
    },
  },
  {
    agentName: 'agent002',
    sourcePath: '../../src/agent002',
    protocol: 'MCP',
    envVars: {},
  },
  {
    agentName: 'agent003',
    sourcePath: '../../src/agent003',
    protocol: 'MCP',
    envVars: {},
  },
  {
    agentName: 'agent004',
    sourcePath: '../../src/agent004',
    protocol: 'MCP',
    envVars: {},
  },
  {
    agentName: 'agent005',
    sourcePath: '../../src/agent005',
    protocol: 'MCP',
    envVars: {},
  },
  {
    agentName: 'agent006',
    sourcePath: '../../src/agent006',
    protocol: 'MCP',
    envVars: {},
  },
  {
    agentName: 'agent007',
    sourcePath: '../../src/agent007',
    protocol: 'MCP',
    envVars: {},
  },
]
```

### Docker Configuration

Each agent requires a Dockerfile following this pattern:

```dockerfile
FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
```

### Environment Variables

**agent001 (Main Chat Agent)**:
- `USEGATEWAY`: "true"
- `GATEWAY_URL`: AgentCore Gateway URL (injected by CDK)
- `USER_POOL_ID`: Cognito User Pool ID (injected by CDK)
- `USER_POOL_CLIENT_ID`: Cognito Client ID (injected by CDK)
- `AGENT00X_URL`: URLs for each MCP server (injected by CDK)

**agent004-007 (MCP Servers)**:
- No additional environment variables required
- Use boto3 default credential chain
- Region: us-west-2 (hardcoded in agent)

### IAM Permissions

Each agent requires:
- `bedrock:InvokeModel` for Claude Sonnet 4.5
- `bedrock:InvokeModelWithResponseStream` for streaming responses
- `bedrock:ListFoundationModels` for model discovery
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` for CloudWatch

agent001 additionally requires:
- `bedrock-agentcore:InvokeGateway` for MCP server access
- Gateway read permissions

### Deployment Process

1. **Build Phase**:
   - CDK synthesizes CloudFormation template
   - Docker images built for each agent
   - Images pushed to ECR repositories

2. **Deploy Phase**:
   - CloudFormation creates/updates resources
   - AgentCore Runtime environments provisioned
   - Gateway configured with MCP routing
   - Environment variables injected

3. **Verification Phase**:
   - Check CloudWatch logs for agent initialization
   - Verify Gateway connectivity
   - Test sample queries to each agent

## Design Decisions and Rationales

### Decision 1: Separate MCP Server per Capability

**Rationale**:
- Follows single responsibility principle
- Easier to maintain and debug individual capabilities
- Allows independent scaling and deployment
- Consistent with existing architecture (agent002, agent003)
- Enables selective feature rollout

**Alternative Considered**: Single NFL MCP server with multiple tools
- Rejected due to complexity and reduced modularity

### Decision 2: ESPN API as Primary Data Source

**Rationale**:
- Free, public API with no authentication required
- Comprehensive NFL data coverage
- Reliable uptime and performance
- Well-documented JSON responses
- Used by millions of applications

**Alternative Considered**: NFL.com official API
- Rejected due to authentication requirements and rate limits

### Decision 3: Agent-Based Prediction vs. External Service

**Rationale**:
- Leverages existing Bedrock model capabilities
- No additional service dependencies
- Flexible prediction methodology
- Can incorporate multiple data sources
- Consistent with agent architecture

**Alternative Considered**: Third-party prediction API
- Rejected due to cost and reduced control over prediction logic

### Decision 4: Streamable HTTP Transport for MCP

**Rationale**:
- Consistent with agent002 and agent003
- Supports AgentCore Gateway integration
- Enables stateless operation
- Compatible with CDK deployment model

**Alternative Considered**: WebSocket transport
- Rejected due to complexity and stateful requirements

### Decision 5: No Caching Layer

**Rationale**:
- ESPN API is fast enough for real-time queries
- Scores and schedules change frequently
- Simplifies architecture
- Reduces infrastructure costs

**Alternative Considered**: Redis cache for API responses
- Deferred to future optimization if needed

## Future Enhancements

### Phase 2 Capabilities (Not in Current Scope)

1. **Historical Data Analysis**:
   - Multi-season trend analysis
   - Player career statistics
   - Team performance over time

2. **Fantasy Football Integration**:
   - Player rankings and projections
   - Lineup optimization
   - Trade analysis

3. **Betting Odds Integration**:
   - Real-time odds from sportsbooks
   - Line movement tracking
   - Betting recommendations

4. **Notification System**:
   - Score alerts for favorite teams
   - Game start reminders
   - Injury report notifications

5. **Advanced Analytics**:
   - Expected points added (EPA)
   - Win probability graphs
   - Advanced defensive metrics

### Scalability Considerations

- Current design supports up to 1000 requests/minute per agent
- ESPN API has no published rate limits but recommend respectful usage
- Can add CloudFront caching if needed
- Can implement request queuing for high traffic

### Monitoring and Observability

- CloudWatch Logs for all agents
- CloudWatch Metrics for request counts and latencies
- X-Ray tracing for distributed request tracking
- Custom metrics for ESPN API response times
