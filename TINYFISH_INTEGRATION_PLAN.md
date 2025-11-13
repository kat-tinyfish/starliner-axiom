# TinyFish Agent Integration Plan

## Overview

TinyFish is an external Web Agent API that uses Gemini-based browser automation. This document outlines the integration strategy for adding TinyFish as the 4th agent in the Web Agent Arena.

## TinyFish API Details

**Base URL:** `http://54.67.10.91:8000`

**Key Endpoints:**
1. **Create Session:** `POST /apps/eva_agent/users/{user_id}/sessions/{session_id}`
   - Body: `{"task_instruction": "...", "browser_type": "tetra", "use_proxy": false}`
   - Returns: Session creation confirmation

2. **Run SSE Stream:** `POST /run_sse`
   - Body: `{"app_name": "eva_agent", "user_id": "...", "session_id": "...", "new_message": {...}}`
   - Returns: SSE stream of execution events

3. **Get Session History:** `GET /apps/eva_agent/users/{user_id}/sessions/{session_id}`
   - Returns: Complete session history

4. **Abort Session:** `POST /run`
   - Body: `{"new_message": {"role": "user", "parts": [{"text": "tf_stop_agent"}]}}`

## Integration Architecture

### Option 1: Direct API Integration (RECOMMENDED)

**Pros:**
- Uses TinyFish's native execution environment
- No need to replicate complex browser automation
- Authentic TinyFish performance
- SSE provides real-time updates

**Cons:**
- Depends on external API availability
- Different architecture than other agents
- Need to handle SSE parsing

**Implementation:**
```python
class TinyFishAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, api_key: Optional[str] = None):
        super().__init__(agent_id, name, api_key)
        self.api_base = "http://54.67.10.91:8000"
        self.user_id = "arena-user"  # Static or from env
        
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        # 1. Create session
        session_id = str(uuid.uuid4())
        await self._create_session(session_id, prompt)
        
        # 2. Stream execution via SSE
        async for event in self._run_sse_stream(session_id, prompt):
            # Parse events, update checkpoints, tool calls
            self._process_sse_event(event)
        
        # 3. Get final results
        history = await self._get_session_history(session_id)
        
        # 4. Return AgentResult
        return AgentResult(...)
```

### Option 2: Hybrid Approach

Use TinyFish API but translate to our universal browser tools for consistency:

**Pros:**
- Consistent tool call display across all agents
- Fair comparison (same tool definitions)
- Can still use TinyFish's Gemini execution

**Cons:**
- More complex translation layer
- Potential loss of TinyFish-specific optimizations

## Implementation Steps

### Phase 1: Basic Integration (Priority 1)
- [ ] Create `TinyFishAPIClient` in `utils/`
- [ ] Implement session creation
- [ ] Implement SSE streaming
- [ ] Parse SSE events into checkpoints/tool calls
- [ ] Test with simple tasks

### Phase 2: Arena Integration (Priority 2)
- [ ] Integrate with `BaseAgent` interface
- [ ] Map SSE events to our checkpoint system
- [ ] Extract tool calls from execution logs
- [ ] Handle screenshots (if available from TinyFish)
- [ ] Error handling and timeout management

### Phase 3: UI Integration (Priority 3)
- [ ] Update `agent_registry.py` with correct endpoint
- [ ] Test in Streamlit Arena UI
- [ ] Verify voting and leaderboard work
- [ ] Performance testing vs other agents

### Phase 4: Screenshots & Polish (Priority 4)
- [ ] Investigate if TinyFish API provides screenshots
- [ ] If not, proxy through BrowserBase for consistency
- [ ] Add TinyFish-specific metrics
- [ ] Documentation and examples

## SSE Event Structure

Based on `evb/backend/evb/services/web_agent_api.py`, TinyFish SSE events contain:

```json
{
  "content": {...},  // Main event data
  // Additional fields TBD
}
```

Need to analyze actual SSE events to determine:
- How to extract checkpoints
- How to extract tool calls
- How to get execution status
- How to retrieve final output

## Testing Strategy

1. **Unit Tests:** Test API client methods
2. **Integration Tests:** Test full agent execution
3. **Arena Tests:** Test head-to-head vs GPT-4/Claude
4. **Performance Tests:** Measure execution time, success rate

## Fallback Strategy

If TinyFish API is unavailable:
- [ ] Implement mock TinyFish agent for demos
- [ ] Use Gemini Computer Use directly (Plan B)
- [ ] Gracefully disable TinyFish in UI

## Configuration

**Environment Variables:**
```bash
TINYFISH_API_URL=http://54.67.10.91:8000
TINYFISH_API_TIMEOUT=300  # 5 minutes for long tasks
TINYFISH_USER_ID=arena-user
```

**Streamlit Secrets:**
```toml
TINYFISH_API_URL = "http://54.67.10.91:8000"
TINYFISH_USER_ID = "arena-user"
```

## Gemini Computer Use (Alternative)

If we need to implement a Gemini agent directly instead of using TinyFish API:

**Model:** `gemini-2.5-computer-use-preview-10-2025`

**Key Differences from Anthropic:**
- Uses `gemini_computer_use_tool` (predefined tool)
- Different action format
- Different safety mechanism

**Pros:**
- Direct control over execution
- Consistent with GPT-4/Claude architecture
- Can use our BrowserBase setup

**Cons:**
- Not the "real" TinyFish agent
- Need to implement computer use logic
- Different from production TinyFish

## Recommendation

**Phase 1:** Integrate with actual TinyFish API (Option 1)
- Authentic TinyFish performance
- Faster time-to-value
- Real-world testing

**Phase 2 (Optional):** Add Gemini Computer Use as "Gemini Agent"
- Would give us 5 agents total
- Separate from TinyFish
- Better comparison of LLM capabilities

## Next Steps

1. **Explore TinyFish API:** Test endpoints manually
2. **Analyze SSE Events:** Understand data structure
3. **Implement Client:** Create API wrapper
4. **Integrate Agent:** Connect to BaseAgent
5. **Test in Arena:** Validate functionality

## Questions to Answer

- [ ] Does TinyFish API provide screenshots?
- [ ] What's in the SSE event structure?
- [ ] How are tool calls logged?
- [ ] What's the typical execution time?
- [ ] What's the API rate limit?
- [ ] Is authentication required?
- [ ] Can we run parallel sessions?

---

**Status:** Planning → Ready for Implementation
**Estimated Time:** 4-6 hours for full integration
**Risk Level:** Medium (depends on API availability and documentation)

