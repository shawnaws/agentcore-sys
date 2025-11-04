
# Multi-stage Dockerfile for ARM64 MCP Server deployment to Agent Core Runtime

# Build stage - ensure ARM64 architecture
FROM public.ecr.aws/docker/library/python:3.13-slim

# Set working directory
WORKDIR /app

COPY requirements.txt requirements.txt
# Install from requirements file
RUN pip install -r requirements.txt

RUN pip install aws-opentelemetry-distro>=0.10.1


ENV AWS_REGION=us-west-2
ENV AWS_DEFAULT_REGION=us-west-2

# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Verify we're running on ARM64 architecture (required for Agent Core Runtime)
RUN echo "Architecture verification:" && uname -m && \
    [ "$(uname -m)" = "aarch64" ] || (echo "ERROR: Not ARM64 architecture!" && exit 1)

# Install dumb-init for proper process handling
# RUN apk add --no-cache dumb-init

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

# Expose port 8000 for MCP protocol
EXPOSE 8000
EXPOSE 8080

COPY . .

# Set environment variables for MCP Agent Core Runtime
ENV NODE_ENV=production
ENV MCP_PORT=8000

# # Health check for container
# HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
#   CMD node -e "const http = require('http'); \
#     const options = { hostname: 'localhost', port: 8000, path: '/mcp', method: 'POST', \
#     headers: {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}, timeout: 3000 }; \
#     const req = http.request(options, (res) => process.exit(res.statusCode === 200 ? 0 : 1)); \
#     req.on('error', () => process.exit(1)); \
#     req.on('timeout', () => process.exit(1)); \
#     req.write('{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"ping\"}'); \
#     req.end();"

# Use dumb-init to properly handle signals
#ENTRYPOINT ["dumb-init", "--"]

# Start the MCP server using run.js for proper secret handling
CMD ["opentelemetry-instrument", "python", "-m", "main"]
