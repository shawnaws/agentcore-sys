import os
import string
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands_tools import http_request
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from utils import streamable_http_sigv4

import boto3

auth_provider = AWSCognitoProvider(
    user_pool_id="",   # Your AWS Cognito user pool ID
    aws_region="eu-central-1",               # AWS region (defaults to eu-central-1)
    client_id="your-app-client-id",          # Your app client ID
    client_secret="your-app-client-secret",  # Your app client Secret
    base_url="http://localhost:8000",        # Must match your callback URL
    # redirect_path="/auth/callback"         # Default value, customize if needed
)

model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0"

WEATHER_SYSTEM_PROMPT = """You are a weather assistant with HTTP capabilities. You can:

1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States

When retrieving weather information:
1. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
2. Then use the returned forecast URL to get the actual forecast

When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.
"""

# Create a custom boto3 session
print("Initializing boto3 session")
session = boto3.Session(
    region_name='us-west-2',
)

# Create an MCP server
mcp = FastMCP("Weather Server", host="0.0.0.0", stateless_http=True)

def _get_bedrock_model(m_id):
    return BedrockModel(
        inference_profile_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
   )

# Define a tool
@mcp.tool(description="Weather tool which returns the weather based on the input query.")
def getWeather(weatherQuery: str) -> str:    
    agent = Agent(
        system_prompt=WEATHER_SYSTEM_PROMPT,
        model=_get_bedrock_model(model_id),
        tools=[http_request]
    )
    return agent(prompt)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
