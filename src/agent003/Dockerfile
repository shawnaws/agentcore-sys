FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for AgentCore
EXPOSE 8080

# Run the agent
CMD ["python", "main.py"]
