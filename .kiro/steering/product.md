# Product Overview

This project deploys Strands AI agents on Amazon Bedrock AgentCore Runtime. It provides infrastructure and agent implementations that integrate with AWS services, MCP (Model Context Protocol) servers, and external APIs.

## Key Components

- **Agent Runtimes**: Python-based agents using the Strands framework with Bedrock models
- **MCP Integration**: Support for Model Context Protocol servers and tools
- **API Gateway**: AgentCore Gateway for connecting to external APIs and MCP tools
- **Authentication**: AWS Cognito-based OAuth2 authentication for secure access
- **Infrastructure**: AWS CDK-based deployment with TypeScript constructs

## Use Cases

- Deploy conversational AI agents with tool-calling capabilities
- Integrate external APIs (OpenAPI specs) as agent tools
- Connect MCP servers for extended functionality
- Secure agent access with OAuth2 authentication
