# Implementation Plan

- [x] 1. Create NFL Scores MCP Server (agent004)
  - Create agent004 directory structure with main.py, Dockerfile, and requirements.txt
  - Implement getNFLScores tool using FastMCP framework with ESPN Scoreboard API integration
  - Add system prompt for score formatting and game status interpretation
  - Configure boto3 session and Bedrock model initialization
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 2. Create NFL Schedule MCP Server (agent005)
  - Create agent005 directory structure with main.py, Dockerfile, and requirements.txt
  - Implement getNFLSchedule tool using FastMCP framework with ESPN API integration
  - Add system prompt for schedule formatting with date/time and venue information
  - Configure boto3 session and Bedrock model initialization
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 3. Create NFL Player Statistics MCP Server (agent006)
  - Create agent006 directory structure with main.py, Dockerfile, and requirements.txt
  - Implement getNFLPlayerStats tool using FastMCP framework with ESPN Athletes API
  - Add system prompt for position-aware statistics formatting
  - Configure boto3 session and Bedrock model initialization
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Create NFL Game Predictions MCP Server (agent007)
  - Create agent007 directory structure with main.py, Dockerfile, and requirements.txt
  - Implement predictNFLGame tool using FastMCP framework with multi-source data aggregation
  - Add system prompt for prediction analysis methodology and output formatting
  - Configure boto3 session and Bedrock model initialization
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 5. Enhance Main Chat Agent (agent001) with MCP Integration
  - Update agent001/main.py to initialize MCPClient connections for all MCP servers
  - Implement tool discovery logic to aggregate tools from agent002 through agent007
  - Add environment variable handling for MCP server URLs (AGENT002_URL through AGENT007_URL)
  - Configure agent with aggregated tools from all MCP servers
  - Implement error handling for unavailable MCP servers with graceful degradation
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6. Update CDK Infrastructure Configuration
  - Update infra/bin/infra.ts to add agent004, agent005, agent006, and agent007 configurations
  - Add MCP server URL environment variables to agent001 configuration
  - Ensure protocol is set to "MCP" for new agents (agent004-007)
  - Verify agent naming convention follows sequential pattern
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 7. Implement Error Handling and Resilience
  - Add HTTP timeout configuration (30 seconds) to all MCP server agents
  - Implement exponential backoff retry logic (1s, 2s) with maximum 2 attempts
  - Add user-friendly error messages for API failures, timeouts, and invalid queries
  - Configure CloudWatch logging with structured JSON format for all agents
  - Add defensive parsing with try-catch blocks for ESPN API responses
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 8. Implement Data Formatting Standards
  - Add date/time formatting functions for user-friendly display (e.g., "Sunday, January 15, 2025 at 4:30 PM EST")
  - Implement team name formatting with full names and abbreviations
  - Add score highlighting and game status formatting for live and completed games
  - Create structured list formatting for multi-item responses (multiple games, players)
  - Implement position-aware statistics formatting for player data
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 9. Create Dockerfiles for New Agents
  - Create Dockerfile for agent004 using Python 3.11-slim base image
  - Create Dockerfile for agent005 using Python 3.11-slim base image
  - Create Dockerfile for agent006 using Python 3.11-slim base image
  - Create Dockerfile for agent007 using Python 3.11-slim base image
  - Ensure all Dockerfiles expose port 8080 and use "python main.py" as CMD
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 10. Create Requirements Files for New Agents
  - Create requirements.txt for agent004 with bedrock-agentcore-runtime, strands, strands-tools, mcp, boto3
  - Create requirements.txt for agent005 with bedrock-agentcore-runtime, strands, strands-tools, mcp, boto3
  - Create requirements.txt for agent006 with bedrock-agentcore-runtime, strands, strands-tools, mcp, boto3
  - Create requirements.txt for agent007 with bedrock-agentcore-runtime, strands, strands-tools, mcp, boto3
  - Ensure version consistency with existing agents (agent002, agent003)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 11. Create Local Testing Scripts
  - Create test script for agent004 with sample curl commands for score queries
  - Create test script for agent005 with sample curl commands for schedule queries
  - Create test script for agent006 with sample curl commands for player stats queries
  - Create test script for agent007 with sample curl commands for prediction queries
  - Create ESPN API integration test script to verify endpoint availability and response formats
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 12. Create Documentation
  - Document ESPN API endpoints used by each agent with example requests and responses
  - Create README for each new agent explaining its purpose, tools, and local testing
  - Update main project README with information about new NFL agents
  - Document environment variables required for agent001 MCP integration
  - Create troubleshooting guide for common ESPN API errors and MCP connection issues
  - _Requirements: 7.5, 9.4_
