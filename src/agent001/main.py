import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
import boto3

print("initializing bedrock agentcore app")
app = BedrockAgentCoreApp()

model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0"

# Create a custom boto3 session
print("Initializing boto3 session")
session = boto3.Session(
    region_name='us-west-2',
)

print("Initializing agent")
agent = Agent(model=model)

# def _create_streamable_http_transport(headers=None):
#     url = {os.environ.get('GATEWAY_URL')}
#     access_token = {AccessToken}
#     headers = {**headers} if headers else {}
#     headers["Authorization"] = f"Bearer {access_token}"
#     return streamablehttp_client(
#         url,
#         headers=headers
#     )

def _get_bedrock_model(m_id):
    return BedrockModel(
        inference_profile_id=m_id,
        temperature=0.0,
        streaming=True,
        boto_session=session
   )

@app.entrypoint
def invoke(payload):
    print("Process user input and return a response")
    user_message = payload.get("prompt", "Hello! How can I help you today?")
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=_get_bedrock_model(model_id),
            tools=tools
        )
        return agent(prompt)

if __name__ == "__main__":
    app.run()
