# Multi-Agent System Coordination Analysis

**Date**: December 16, 2024  
**Repository**: agentcore-sys  
**Scope**: Supervisor agent (agent001) and sub-agents (agent002-007) coordination

## Executive Summary

This analysis identifies critical coordination issues in the multi-agent system that prevent the supervisor agent (agent001) from effectively orchestrating sub-agents (agent002-007). The primary problems include:

1. **Tool aggregation failures** due to improper flattening and synchronous/asynchronous pattern mixing
2. **Environment variable bug** causing tuple instead of string for runtime IDs
3. **Lack of error handling** around MCP client initialization and tool discovery
4. **Missing health checks and graceful degradation** when sub-agents are unavailable
5. **Inconsistent logging and observability** across the agent hierarchy

**Impact**: The supervisor cannot reliably discover and utilize tools from sub-agents, leading to failed queries and inconsistent behavior.

**Priority**: HIGH - System cannot function as designed without these fixes.

---

## Table of Contents

1. [Current Architecture Assessment](#1-current-architecture-assessment)
2. [Identified Coordination Issues](#2-identified-coordination-issues)
3. [Root Cause Analysis](#3-root-cause-analysis)
4. [Recommended Solutions](#4-recommended-solutions)
5. [Implementation Approach](#5-implementation-approach)
6. [Priority Rankings](#6-priority-rankings)

---

## 1. Current Architecture Assessment

### 1.1 System Design

The system follows a **supervisor-worker pattern**:

- **Supervisor (agent001)**: Orchestrates multiple sub-agents, aggregates their tools, and routes user queries
- **Workers (agent002-007)**: Specialized agents exposing domain-specific tools via MCP servers
  - agent002: Weather information
  - agent003: NFL Teams data
  - agent004: NFL Scores
  - agent005: NFL Schedules
  - agent006: NFL Player Statistics
  - agent007: NFL Game Predictions

### 1.2 Communication Flow

```
User Query
    ↓
agent001 (Supervisor)
    ↓ (MCP Protocol over AWS SigV4)
    ├→ agent002 (Weather) ← tools: getWeather
    ├→ agent003 (Teams) ← tools: getNFLTeams
    ├→ agent004 (Scores) ← tools: getNFLScores
    ├→ agent005 (Schedule) ← tools: getNFLSchedule
    ├→ agent006 (Stats) ← tools: getNFLPlayerStats
    └→ agent007 (Predictions) ← tools: predictNFLGame
```

### 1.3 Technology Stack

**Supervisor (agent001)**:
- Framework: Strands Agents
- MCP Client: `mcp_proxy_for_aws.client.aws_iam_streamablehttp_client`
- Authentication: AWS SigV4 via boto3 credentials
- Model: Claude Sonnet 4.5

**Sub-agents (agent002-007)**:
- Framework: FastMCP (stateless HTTP)
- Server: MCP server exposing tools
- Internal: Each wraps a Strands Agent for execution
- Model: Claude Sonnet 4.5

### 1.4 Current Working Mechanisms

✅ **What Works**:
1. Individual sub-agents function correctly when invoked directly
2. FastMCP servers expose tools with proper schemas
3. Infrastructure deployment via CDK successfully creates all runtimes
4. IAM permissions grant supervisor access to invoke sub-agents
5. Sub-agents have structured logging and error handling

---

## 2. Identified Coordination Issues

### 2.1 CRITICAL: Tool Aggregation Failure

**Location**: `src/agent001/main.py:88-92`

```python
with contextlib.ExitStack() as stack:
    mcp_tools = [current_time]
    for client in agent_clients:
        context_client = stack.enter_context(client)
        mcp_tools.append(context_client.list_tools_sync())  # ❌ ISSUE
```

**Problem**: 
- `list_tools_sync()` returns a **ToolsList object**, not individual tools
- Appending the entire object creates nested structures: `[Tool, ToolsList, ToolsList, ...]`
- Agent receives improperly formatted tools and cannot invoke them
- Should use: `mcp_tools.extend(context_client.list_tools_sync())` to flatten

**Impact**: Supervisor cannot access any sub-agent tools effectively.

### 2.2 CRITICAL: Environment Variable Bug

**Location**: `src/agent001/main.py:59`

```python
runtime_id = os.getenv(name, 'foobar'),  # ❌ Trailing comma creates tuple
logger.info(f"RUNTIMEID: %s", runtime_id[0])  # Workaround with [0]
agent_arn = f"arn:aws:bedrock-agentcore:{region}:{aws_account_id}:runtime/{runtime_id[0]}"
```

**Problem**:
- Trailing comma makes `runtime_id` a tuple: `('agent002-xyz',)` instead of string `'agent002-xyz'`
- Code works accidentally via `runtime_id[0]` indexing, but fragile
- Confusing for debugging and maintenance

**Fix**: Remove trailing comma: `runtime_id = os.getenv(name, 'foobar')`

### 2.3 HIGH: Missing Error Handling

**Location**: `src/agent001/main.py:83-92`

```python
agent_clients = []
for agent_id in supported_agents:
    factory = agent_factory(agent_id)
    agent_clients.append(MCPClient(factory))  # No try-catch

with contextlib.ExitStack() as stack:
    mcp_tools = [current_time]
    for client in agent_clients:
        context_client = stack.enter_context(client)  # No error handling
        mcp_tools.append(context_client.list_tools_sync())  # Can fail silently
```

**Problems**:
1. No validation if MCPClient initialization succeeds
2. No try-catch around `enter_context()` - entire supervisor fails if one agent is down
3. No try-catch around `list_tools_sync()` - connection failures crash supervisor
4. No logging of which agents connected successfully
5. No graceful degradation if subset of agents unavailable

**Impact**: Single sub-agent failure crashes entire supervisor.


### 2.4 HIGH: Sync/Async Pattern Confusion

**Location**: `src/agent001/main.py:46-136`

**Problems**:
```python
@asynccontextmanager
async def create_agent():  # ✅ Async function
    # ...
    with contextlib.ExitStack() as stack:  # ❌ Sync context manager
        mcp_tools = [current_time]
        for client in agent_clients:
            context_client = stack.enter_context(client)  # ❌ Sync enter
            mcp_tools.append(context_client.list_tools_sync())  # ❌ Sync call
```

**Issues**:
1. `@asynccontextmanager` decorator but uses synchronous context managers inside
2. MCPClient likely supports async operations but using sync methods
3. Blocking operations in async context prevents concurrent tool discovery
4. No benefit from async/await pattern as currently implemented

**Consequence**: Cannot leverage concurrent connections to sub-agents, slower initialization.

### 2.5 MEDIUM: Missing Environment Variable Validation

**Location**: `src/agent001/main.py:58-69`

```python
def get_mcp_params(name):
    runtime_id = os.getenv(name, 'foobar'),  # Default is 'foobar' string
    logger.info(f"RUNTIMEID: %s", runtime_id[0])
    agent_arn = f"arn:aws:bedrock-agentcore:{region}:{aws_account_id}:runtime/{runtime_id[0]}"
    # No validation if runtime_id is actually set or is default 'foobar'
```

**Problems**:
1. Silent fallback to 'foobar' if environment variable missing
2. No error raised if required agent runtime ID not provided
3. Results in invalid ARN construction
4. Difficult to debug when deployment configuration is wrong

**Impact**: Configuration errors go undetected until runtime failures occur.

### 2.6 MEDIUM: Inconsistent Dependency Management

**Location**: Requirements files across agents

**agent001 dependencies**:
```
strands-agents
strands-agents-tools
bedrock-agentcore
mcp_proxy_for_aws @ git+https://github.com/aws/mcp-proxy-for-aws.git
boto3
```

**agent002-007 dependencies**:
```
strands-agents
strands-agents-tools
bedrock-agentcore
boto3
mcp  # Different from supervisor
```

**Problems**:
1. Supervisor uses `mcp_proxy_for_aws` while sub-agents use `mcp` package
2. Different authentication mechanisms between layers
3. Potential version conflicts when shared libraries updated
4. No centralized dependency management

### 2.7 MEDIUM: No Health Check Mechanism

**Issue**: No verification that sub-agents are running and responsive before attempting tool aggregation.

**Missing Capabilities**:
- Pre-connection health checks
- Timeout configuration for MCP connections
- Retry logic for transient failures
- Circuit breaker pattern for failed agents
- Fallback behavior when agents unavailable

**Impact**: Poor user experience when sub-agents are down or slow.

### 2.8 LOW: Missing Observability

**Location**: `src/agent001/main.py` - entire file

**Problems**:
1. No structured logging in supervisor (sub-agents have JSON logging)
2. No timing metrics for tool discovery
3. No correlation IDs for tracing requests across agents
4. No logging of which tools came from which agent
5. Difficult to debug coordination issues in production

**Comparison with sub-agents**:
```python
# agent004-007 have structured logging:
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "agent": "agent004",
            "message": record.getMessage(),
        }
```

agent001 has no equivalent structured logging.

---

## 3. Root Cause Analysis

### 3.1 Design Decisions

**Root Cause**: The system was built incrementally without a unified coordination strategy.

**Evidence**:
1. Sub-agents (002-007) evolved from simple examples to production agents
2. Supervisor (001) retrofitted to coordinate existing agents
3. No common coordination library or pattern enforced
4. Mixed synchronous/asynchronous patterns indicate lack of upfront design

### 3.2 Technical Debt

**Accumulated Issues**:
1. **Prototype code in production**: agent001 has exploratory code patterns (tuple bug, sync in async)
2. **Inconsistent error handling**: Sub-agents robust, supervisor fragile
3. **No integration tests**: Agents tested individually but not as a system
4. **Documentation lag**: README doesn't cover coordination failures

### 3.3 Specific Code Issues

**Issue #1: Tool Aggregation Logic**
- **Root Cause**: Misunderstanding of MCPClient API
- `list_tools_sync()` returns a container object, not a list
- Should iterate/extend, not append

**Issue #2: Environment Variable Bug**
- **Root Cause**: Python syntax error (trailing comma)
- Went unnoticed due to workaround with `[0]` indexing
- No type hints to catch this

**Issue #3: Error Handling Gap**
- **Root Cause**: Optimistic assumption all agents always available
- No defensive programming around network calls
- Fail-fast approach instead of resilient design

---

## 4. Recommended Solutions

### 4.1 Immediate Fixes (P0 - Critical)

#### Fix 1: Correct Tool Aggregation
**File**: `src/agent001/main.py:88-92`

**Current**:
```python
mcp_tools = [current_time]
for client in agent_clients:
    context_client = stack.enter_context(client)
    mcp_tools.append(context_client.list_tools_sync())
```

**Fixed**:
```python
mcp_tools = [current_time]
for client in agent_clients:
    context_client = stack.enter_context(client)
    tools = context_client.list_tools_sync()
    if tools:
        mcp_tools.extend(tools)  # ✅ Flatten list
```

#### Fix 2: Remove Environment Variable Bug
**File**: `src/agent001/main.py:59`

**Current**:
```python
runtime_id = os.getenv(name, 'foobar'),
```

**Fixed**:
```python
runtime_id = os.getenv(name)
if not runtime_id:
    raise ValueError(f"Missing required environment variable: {name}")
```

#### Fix 3: Add Error Handling for Tool Discovery
**File**: `src/agent001/main.py:88-92`

**Current**: No error handling

**Fixed**:
```python
mcp_tools = [current_time]
failed_agents = []

for idx, client in enumerate(agent_clients):
    agent_id = supported_agents[idx]
    try:
        context_client = stack.enter_context(client)
        tools = context_client.list_tools_sync()
        if tools:
            logger.info(f"Successfully loaded {len(tools)} tools from {agent_id}")
            mcp_tools.extend(tools)
        else:
            logger.warning(f"No tools returned from {agent_id}")
    except Exception as e:
        logger.error(f"Failed to connect to {agent_id}: {e}", exc_info=True)
        failed_agents.append(agent_id)

if len(mcp_tools) == 1:  # Only current_time tool
    raise RuntimeError(f"No sub-agent tools available. Failed agents: {failed_agents}")

logger.info(f"Loaded {len(mcp_tools)} total tools. Failed agents: {failed_agents or 'None'}")
```

### 4.2 Short-term Improvements (P1 - High)

#### Solution 1: Add Structured Logging

Create `src/agent001/logging_config.py`:
```python
import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "agent": "agent001",
            "message": record.getMessage(),
        }
        if hasattr(record, 'sub_agent'):
            log_data['sub_agent'] = record.sub_agent
        if hasattr(record, 'tool_count'):
            log_data['tool_count'] = record.tool_count
        if hasattr(record, 'error'):
            log_data['error'] = record.error
        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    return logger
```

#### Solution 2: Add Connection Timeouts

**File**: `src/agent001/main.py`

Add timeout configuration:
```python
MCP_CONNECTION_TIMEOUT = 10  # seconds
MCP_TOOL_DISCOVERY_TIMEOUT = 5  # seconds

def agent_factory(agent_id):
    def mcp_factory():
        mcp_url = get_mcp_params(agent_id)
        return aws_iam_streamablehttp_client(
            endpoint=mcp_url, 
            aws_region=region, 
            aws_service=service,
            timeout=MCP_CONNECTION_TIMEOUT  # Add timeout
        )
    return mcp_factory
```

#### Solution 3: Implement Proper Async Pattern

**Option A**: Make everything truly async:
```python
@asynccontextmanager
async def create_agent():
    # Use async MCP client operations
    async with contextlib.AsyncExitStack() as stack:
        mcp_tools = [current_time]
        for client in agent_clients:
            try:
                context_client = await stack.enter_async_context(client)
                tools = await context_client.list_tools()  # Async version
                if tools:
                    mcp_tools.extend(tools)
            except Exception as e:
                logger.error(f"Failed to load tools: {e}")
```

**Option B**: Make everything synchronous (simpler):
```python
def create_agent():  # Remove @asynccontextmanager
    # Use synchronous patterns consistently
    with contextlib.ExitStack() as stack:
        # ... sync operations
    
    def agent_callable(user_input: str) -> str:
        result = agent(user_input)
        return str(result)
    
    return agent_callable
```

### 4.3 Medium-term Enhancements (P2 - Medium)

#### Enhancement 1: Health Check Service

Create `src/agent001/health_check.py`:
```python
import asyncio
from typing import List, Dict
from mcp import ClientSession

async def check_agent_health(agent_id: str, mcp_url: str, timeout: int = 5) -> Dict:
    """Check if an agent is responsive."""
    try:
        # Attempt to initialize MCP session with timeout
        async with asyncio.timeout(timeout):
            transport = create_transport(mcp_url)
            async with ClientSession(*transport) as session:
                await session.initialize()
                return {
                    "agent_id": agent_id,
                    "status": "healthy",
                    "response_time_ms": ...
                }
    except asyncio.TimeoutError:
        return {"agent_id": agent_id, "status": "timeout"}
    except Exception as e:
        return {"agent_id": agent_id, "status": "unhealthy", "error": str(e)}

async def check_all_agents(agent_ids: List[str]) -> Dict[str, Dict]:
    """Run health checks on all agents concurrently."""
    tasks = [check_agent_health(agent_id, get_url(agent_id)) for agent_id in agent_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {r['agent_id']: r for r in results if isinstance(r, dict)}
```

#### Enhancement 2: Tool Registry

Create `src/agent001/tool_registry.py`:
```python
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ToolInfo:
    name: str
    agent_id: str
    description: str
    schema: Dict[str, Any]

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}
        self.agent_tools: Dict[str, List[str]] = {}
    
    def register(self, agent_id: str, tools: List[Any]):
        """Register tools from an agent."""
        for tool in tools:
            tool_name = tool.name
            if tool_name in self.tools:
                logger.warning(
                    f"Tool name collision: {tool_name} from {agent_id} "
                    f"already registered by {self.tools[tool_name].agent_id}"
                )
            self.tools[tool_name] = ToolInfo(
                name=tool_name,
                agent_id=agent_id,
                description=tool.description,
                schema=tool.inputSchema
            )
            self.agent_tools.setdefault(agent_id, []).append(tool_name)
    
    def get_tools_by_agent(self, agent_id: str) -> List[str]:
        return self.agent_tools.get(agent_id, [])
    
    def get_all_tools(self) -> List[Any]:
        return list(self.tools.values())
```

#### Enhancement 3: Retry Logic with Exponential Backoff

Similar to the retry logic in sub-agents:
```python
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # seconds

def connect_with_retry(agent_id: str, factory) -> MCPClient:
    """Connect to agent with retry logic."""
    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = RETRY_DELAYS[attempt - 1]
                logger.info(f"Retrying {agent_id} after {delay}s", 
                           extra={"sub_agent": agent_id, "retry": attempt})
                time.sleep(delay)
            
            client = MCPClient(factory)
            # Validate connection
            return client
        except Exception as e:
            last_exception = e
            logger.warning(f"Connection attempt {attempt + 1} failed for {agent_id}: {e}")
    
    raise last_exception
```

### 4.4 Long-term Improvements (P3 - Nice to Have)

1. **Circuit Breaker Pattern**: Prevent repeated calls to failing agents
2. **Tool Caching**: Cache tool schemas to speed up initialization
3. **Dynamic Agent Discovery**: Auto-discover agents instead of hardcoding list
4. **Load Balancing**: Route queries to least-busy agents
5. **Metrics & Monitoring**: Export Prometheus metrics for dashboards
6. **Integration Tests**: Test full supervisor-worker flow

---

## 5. Implementation Approach

### 5.1 Phase 1: Critical Fixes (Week 1)

**Goal**: Make the system functional

**Tasks**:
1. ✅ Fix tool aggregation (extend vs append)
2. ✅ Remove environment variable bug (trailing comma)
3. ✅ Add try-catch around tool discovery
4. ✅ Add validation for required environment variables
5. ✅ Add basic logging of tool discovery success/failure

**Testing**:
- Deploy all agents to AgentCore
- Test supervisor can discover tools from all sub-agents
- Test supervisor handles missing/failed sub-agents gracefully
- Verify NFL prediction workflow end-to-end

### 5.2 Phase 2: Robustness (Week 2)

**Goal**: Make the system resilient

**Tasks**:
1. Implement structured JSON logging for agent001
2. Add connection timeouts for MCP clients
3. Implement retry logic for agent connections
4. Add health check before tool discovery
5. Create tool registry for collision detection

**Testing**:
- Simulate sub-agent failures
- Test timeout handling
- Verify logs are parseable and useful
- Load test with concurrent requests

### 5.3 Phase 3: Consistency (Week 3)

**Goal**: Standardize patterns across all agents

**Tasks**:
1. Unify async/sync patterns (choose one)
2. Standardize dependency versions
3. Create shared utility library for common patterns
4. Document coordination architecture
5. Add integration tests

**Testing**:
- Full regression test suite
- Performance benchmarks
- Documentation review

### 5.4 Phase 4: Enhancement (Week 4+)

**Goal**: Add advanced features

**Tasks**:
1. Implement circuit breaker pattern
2. Add tool caching
3. Create monitoring dashboards
4. Implement dynamic agent discovery
5. Add load balancing logic

---

## 6. Priority Rankings

### P0 - Critical (Must Fix Immediately)

| Priority | Issue | Impact | Effort | File |
|----------|-------|--------|--------|------|
| P0.1 | Tool aggregation bug (append vs extend) | HIGH | LOW | agent001/main.py:92 |
| P0.2 | Environment variable tuple bug | HIGH | LOW | agent001/main.py:59 |
| P0.3 | Missing error handling in tool discovery | HIGH | LOW | agent001/main.py:88-92 |

**Estimated Time**: 2-4 hours  
**Risk if not fixed**: System completely non-functional

### P1 - High (Fix This Week)

| Priority | Issue | Impact | Effort | File |
|----------|-------|--------|--------|------|
| P1.1 | Missing structured logging | MEDIUM | LOW | agent001/main.py |
| P1.2 | No connection timeouts | MEDIUM | LOW | agent001/main.py:75-78 |
| P1.3 | Environment variable validation | MEDIUM | LOW | agent001/main.py:58-69 |
| P1.4 | Sync/async pattern confusion | MEDIUM | MEDIUM | agent001/main.py:46-136 |

**Estimated Time**: 1-2 days  
**Risk if not fixed**: Frequent failures, difficult debugging

### P2 - Medium (Fix This Sprint)

| Priority | Issue | Impact | Effort | File |
|----------|-------|--------|--------|------|
| P2.1 | No health checks | LOW | MEDIUM | New file |
| P2.2 | No retry logic | LOW | MEDIUM | agent001/main.py |
| P2.3 | Tool name collision detection | LOW | MEDIUM | New file |
| P2.4 | Inconsistent dependencies | LOW | LOW | requirements.txt |

**Estimated Time**: 3-5 days  
**Risk if not fixed**: Reduced reliability, maintenance burden

### P3 - Low (Future Enhancement)

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| P3.1 | Circuit breaker pattern | LOW | HIGH |
| P3.2 | Tool caching | LOW | MEDIUM |
| P3.3 | Dynamic agent discovery | LOW | HIGH |
| P3.4 | Monitoring & metrics | LOW | HIGH |

**Estimated Time**: 2-4 weeks  
**Risk if not fixed**: Suboptimal performance, limited observability

---

## 7. Appendix

### 7.1 Test Scenarios

**Test 1: All Agents Available**
- Deploy all 7 agents
- Invoke supervisor with "Predict the Cowboys game this Sunday"
- Verify: Tools from all agents discovered and utilized

**Test 2: One Agent Down**
- Stop agent004 (scores)
- Invoke supervisor with same query
- Verify: Graceful degradation, partial results returned

**Test 3: Missing Environment Variable**
- Remove agent003 env var
- Start supervisor
- Verify: Clear error message, startup fails or agent skipped

**Test 4: Slow Agent Response**
- Add artificial delay to agent005
- Invoke supervisor
- Verify: Timeout handling, other agents still work

### 7.2 Code Review Checklist

Before deploying fixes:
- [ ] All P0 issues addressed
- [ ] Error handling added around all network calls
- [ ] Logging shows clear success/failure for each agent
- [ ] Environment variables validated at startup
- [ ] Integration test passes with all agents
- [ ] Integration test passes with subset of agents
- [ ] Documentation updated

### 7.3 References

- Strands Agents Documentation: https://strandsagents.com/
- MCP Protocol Spec: https://modelcontextprotocol.io/
- AgentCore Runtime Guide: AWS Bedrock documentation
- Related Issues: (Track in your issue tracker)

---

**Document Version**: 1.0  
**Last Updated**: December 16, 2024  
**Next Review**: After P0 fixes implemented
