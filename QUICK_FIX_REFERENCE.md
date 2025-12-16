# Quick Fix Reference - Critical Issues

This document provides side-by-side comparisons of the critical bugs and their fixes.

## Issue 1: Tool Aggregation Bug

**Location**: `src/agent001/main.py` line 92

### ❌ Current (Broken)
```python
with contextlib.ExitStack() as stack:
    mcp_tools = [current_time]
    for client in agent_clients:
        context_client = stack.enter_context(client)
        mcp_tools.append(context_client.list_tools_sync())  # WRONG: appends ToolsList object
```

**Problem**: Appending a ToolsList object creates nested structure `[Tool, ToolsList, ToolsList]` instead of flat list.

### ✅ Fixed
```python
with contextlib.ExitStack() as stack:
    mcp_tools = [current_time]
    for client in agent_clients:
        context_client = stack.enter_context(client)
        tools = context_client.list_tools_sync()
        if tools:
            mcp_tools.extend(tools)  # CORRECT: flattens list
```

---

## Issue 2: Environment Variable Tuple Bug

**Location**: `src/agent001/main.py` line 59

### ❌ Current (Broken)
```python
runtime_id = os.getenv(name, 'foobar'),  # WRONG: trailing comma creates tuple
logger.info(f"RUNTIMEID: %s", runtime_id[0])  # Workaround with indexing
agent_arn = f"arn:aws:bedrock-agentcore:{region}:{aws_account_id}:runtime/{runtime_id[0]}"
```

**Problem**: Trailing comma makes `runtime_id = ('value',)` a tuple instead of string.

### ✅ Fixed
```python
runtime_id = os.getenv(name)  # CORRECT: returns string
if not runtime_id:
    raise ValueError(f"Missing required environment variable: {name}")
logger.info(f"RUNTIMEID: %s", runtime_id)
agent_arn = f"arn:aws:bedrock-agentcore:{region}:{aws_account_id}:runtime/{runtime_id}"
```

---

## Issue 3: Missing Error Handling

**Location**: `src/agent001/main.py` lines 83-92

### ❌ Current (Broken)
```python
agent_clients = []
for agent_id in supported_agents:
    factory = agent_factory(agent_id)
    agent_clients.append(MCPClient(factory))  # No error handling

with contextlib.ExitStack() as stack:
    mcp_tools = [current_time]
    for client in agent_clients:
        context_client = stack.enter_context(client)  # Will crash if one fails
        mcp_tools.append(context_client.list_tools_sync())  # Will crash if one fails
```

**Problem**: Any single agent failure crashes entire supervisor.

### ✅ Fixed
```python
agent_clients = []
for agent_id in supported_agents:
    try:
        factory = agent_factory(agent_id)
        agent_clients.append((agent_id, MCPClient(factory)))
    except Exception as e:
        logger.error(f"Failed to create MCP client for {agent_id}: {e}")

with contextlib.ExitStack() as stack:
    mcp_tools = [current_time]
    failed_agents = []
    
    for agent_id, client in agent_clients:
        try:
            context_client = stack.enter_context(client)
            tools = context_client.list_tools_sync()
            if tools:
                logger.info(f"Loaded {len(tools)} tools from {agent_id}")
                mcp_tools.extend(tools)
            else:
                logger.warning(f"No tools returned from {agent_id}")
        except Exception as e:
            logger.error(f"Failed to connect to {agent_id}: {e}", exc_info=True)
            failed_agents.append(agent_id)
    
    # Only fail if NO tools available
    if len(mcp_tools) == 1:  # Only current_time
        raise RuntimeError(f"No sub-agent tools available. Failed: {failed_agents}")
    
    logger.info(f"Loaded {len(mcp_tools)} total tools. Failed: {failed_agents or 'None'}")
```

---

## Complete Fixed Version

**File**: `src/agent001/main.py` - `create_agent()` function

```python
@asynccontextmanager
async def create_agent():
    """Create a Strands agent with AWS IAM-authenticated MCP server access."""
    
    def get_mcp_params(name):
        runtime_id = os.getenv(name)  # ✅ Fixed: removed trailing comma
        if not runtime_id:  # ✅ Fixed: validate env var
            raise ValueError(f"Missing required environment variable: {name}")
        
        logger.info(f"RUNTIMEID: %s", runtime_id)
        agent_arn = f"arn:aws:bedrock-agentcore:{region}:{aws_account_id}:runtime/{runtime_id}"
        print(agent_arn)
        
        encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
        url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        print(url)
        return url

    def agent_factory(agent_id):
        def mcp_factory():
            mcp_url = get_mcp_params(agent_id)
            return aws_iam_streamablehttp_client(
                endpoint=mcp_url, aws_region=region, aws_service=service
            )
        return mcp_factory

    supported_agents = ["agent002", "agent003", "agent004", "agent005", "agent006", "agent007"]
    
    # ✅ Fixed: Create clients with error handling
    agent_clients = []
    for agent_id in supported_agents:
        try:
            factory = agent_factory(agent_id)
            agent_clients.append((agent_id, MCPClient(factory)))
        except Exception as e:
            logger.error(f"Failed to create MCP client for {agent_id}: {e}")

    # ✅ Fixed: Tool discovery with error handling and proper list flattening
    with contextlib.ExitStack() as stack:
        mcp_tools = [current_time]
        failed_agents = []
        
        for agent_id, client in agent_clients:
            try:
                context_client = stack.enter_context(client)
                tools = context_client.list_tools_sync()
                if tools:
                    logger.info(f"Successfully loaded {len(tools)} tools from {agent_id}")
                    mcp_tools.extend(tools)  # ✅ Fixed: extend instead of append
                else:
                    logger.warning(f"No tools returned from {agent_id}")
            except Exception as e:
                logger.error(f"Failed to connect to {agent_id}: {e}", exc_info=True)
                failed_agents.append(agent_id)
        
        # ✅ Fixed: Only fail if no tools available at all
        if len(mcp_tools) == 1:  # Only current_time tool
            raise RuntimeError(
                f"No sub-agent tools available. Failed agents: {failed_agents}"
            )
        
        logger.info(
            f"Loaded {len(mcp_tools)} total tools. Failed agents: {failed_agents or 'None'}"
        )

        system_prompt = """You are an NFL game prediction orchestrator..."""

        agent = Agent(
            system_prompt=system_prompt,
            model=_get_bedrock_model(model_id),
            tools=mcp_tools,
            callback_handler=None
        )

        async def agent_callable(user_input: str) -> str:
            result = agent(user_input)
            return str(result)

        yield agent_callable
```

---

## Testing the Fixes

### Test 1: All Agents Available
```bash
# Set all environment variables
export agent002=<runtime-id>
export agent003=<runtime-id>
# ... etc

# Run supervisor
cd src/agent001
python main.py '{"prompt": "Predict the Cowboys game this Sunday"}'
```

**Expected**: All tools discovered, query succeeds.

### Test 2: One Agent Missing
```bash
# Unset one agent
unset agent003

# Run supervisor
python main.py '{"prompt": "What teams are in the NFC?"}'
```

**Expected**: 
- Warning logged about agent003
- Other agents still work
- Query succeeds with available tools

### Test 3: Missing Environment Variable
```bash
# Unset critical agent
unset agent002

# Run supervisor
python main.py
```

**Expected**: Clear error message about missing environment variable.

---

## Verification Checklist

After applying fixes:

- [ ] Tool aggregation uses `extend()` instead of `append()`
- [ ] No trailing comma on environment variable reads
- [ ] Try-catch blocks around all MCP operations
- [ ] Environment variables validated before use
- [ ] Logging shows success/failure for each agent
- [ ] System works with all agents available
- [ ] System works with subset of agents available
- [ ] Clear error messages when configuration is wrong

---

**Estimated Time to Apply**: 30-60 minutes  
**Testing Time**: 1-2 hours  
**Total**: 2-4 hours for complete P0 fixes
