# Web Agent Arena - Execution Plan

## Project Overview
A Streamlit-based web agent comparison platform that enables users to pit two web agents against each other in real-time, watching their performance via iframe browser sessions, with competitive timing and outcome tracking.

---

## Phase 1: Project Setup & Architecture (Week 1)

### 1.1 Environment Setup
- **Python Environment**: Python 3.11+ with virtual environment
- **Core Dependencies**:
  - `streamlit` (UI framework)
  - `streamlit-autorefresh` (for real-time updates)
  - `playwright` (browser automation)
  - `supabase` (database client)
  - `sqlalchemy` (database ORM)
  - `pandas` (data manipulation for leaderboard)
  - `plotly` (interactive charts for dashboard)
  - `openai` (GPT-4 agent API)
  - `anthropic` (Claude agent API)
  - `google-generativeai` (Gemini agent API)
  - `requests` (HTTP client for TinyFish API and Lambda invocation)
  - `asyncio` (concurrent agent execution)
  - `websockets` (for VNC streaming)
  
### 1.2 Repository Structure
```
starliner-axiom/
├── app.py                      # Main Streamlit entry point
├── requirements.txt            # Python dependencies
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Abstract base agent class
│   ├── agent_registry.py      # Agent registration system (4 agents)
│   └── implementations/       # Individual agent implementations
│       ├── openai_agent.py    # GPT-4 Web Agent
│       ├── anthropic_agent.py # Claude 3.5 Sonnet Agent
│       ├── google_agent.py    # Gemini 2.0 Agent
│       └── tinyfish/          # TinyFish custom agent
│           ├── __init__.py
│           ├── agent.py
│           └── README.md
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models
│   └── connection.py          # Database connection logic
├── components/
│   ├── __init__.py
│   ├── arena.py               # Main arena UI component
│   ├── dashboard.py           # Leaderboard & analytics
│   ├── checkpoint_tracker.py  # Progress visualization
│   ├── tool_call_panel.py     # Tool call display (left sidebar)
│   ├── timer.py               # Race timer component
│   └── vnc_viewer.py          # noVNC iframe component
├── utils/
│   ├── __init__.py
│   ├── browser_session.py     # Browser session management
│   ├── lambda_client.py       # AWS Lambda invocation client
│   └── prompt_parser.py       # Parse user prompts
├── lambda/                    # AWS Lambda function code
│   ├── requirements.txt       # Lambda-specific dependencies
│   ├── handler.py             # Lambda entry point
│   └── agent_executor.py      # Browser execution logic
├── static/
│   └── styles.css             # Custom CSS
└── README.md
```

### 1.3 Deployment Architecture
**Platform**: **Streamlit Community Cloud** for hosting the application

**Advantages**:
- Native Streamlit support with zero configuration
- Free tier with auto-scaling
- Direct GitHub integration for CI/CD
- Built-in secrets management
- Custom domain support
- Excellent performance for Python backends

**Infrastructure Components**:
- **App Hosting**: Streamlit Community Cloud
- **Database**: Supabase (PostgreSQL)
- **Browser Execution**: AWS Lambda + Playwright
- **File Storage**: Supabase Storage (for screenshots/recordings)

---

## Phase 2: Core Agent Infrastructure (Week 2)

### 2.1 Base Agent Architecture
Informed by **BrowserArena** methodology:

- **Abstract Base Agent Class** (`agents/base_agent.py`):
  ```python
  - execute(prompt: str, constraints: dict) -> AgentResult
  - get_current_checkpoint() -> str
  - stop_execution() -> None
  - get_browser_session() -> BrowserSession
  ```

- **Agent Registry** (`agents/agent_registry.py`):
  - Dynamic agent discovery and registration
  - Metadata: name, version, description, capabilities
  - Easy addition of new agents

### 2.2 Browser Session Management
- **Headless Browser Instances**: Using Playwright for each agent
- **Session Isolation**: Separate browser contexts per agent
- **Screen Capture**: Real-time screenshot streaming for iframe display
- **VNC/WebRTC Integration**: For live browser viewing (via noVNC or similar)

### 2.3 Checkpoint & Tool Call System
Inspired by BrowserArena's task decomposition and arena.browserbase.com's interface:

**Checkpoint System**:
- **Predefined Checkpoints**:
  1. "Initialization" - Agent started
  2. "Navigation" - Navigating to target domain
  3. "Interaction" - Interacting with page elements
  4. "Data Extraction" - Extracting/processing information
  5. "Validation" - Verifying task completion
  6. "Completion" - Task finished

- **Dynamic Checkpoints**: Agents can define custom checkpoints based on task
- **Visual Indicators**: Progress bar + emoji flags (🏁 🎯 ⚡ ✅)

**Tool Call Display Panel** (inspired by arena.browserbase.com):
- **Left sidebar** showing real-time tool calls for each agent
- **Tool call types**: navigate, click, type, scroll, extract, etc.
- **Timestamped entries**: Each tool call shows execution time
- **Status indicators**: Success (✅), In Progress (⏳), Error (❌)
- **Collapsible view**: Auto-scroll to latest, expandable for details
- **Action parameters**: Show URL, selectors, input values in compact format

---

## Phase 3: Streamlit UI Development (Week 3)

### 3.1 Main Arena Interface (`app.py` + `components/arena.py`)

#### Layout Structure:
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🏆 Web Agent Arena                              [Arena] [Dashboard]          │
├──────────────────────────────────────────────────────────────────────────────┤
│  Task Input                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │ Enter your task in natural language...                                   ││
│  │ Optional: Domain hints, JSON schema                                      ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
│  Agent Selection:                                                             │
│  [Agent A ▼]                      vs                      [Agent B ▼]        │
│                                                                               │
│  [▶️ Start Race]  [⏸️ Pause]  [⏹️ Stop]  [🔄 Reset]        ⏱️ Timer: 00:45.23│
│                                                                               │
├──────────────────────────────────────┬──────────────────────────────────────┤
│           AGENT A                    │           AGENT B                    │
├────────┬─────────────────────────────┼────────┬─────────────────────────────┤
│ Tool   │   Browser                   │ Tool   │   Browser                   │
│ Calls  │   ┌─────────────────────┐   │ Calls  │   ┌─────────────────────┐   │
│ ─────  │   │                     │   │ ─────  │   │                     │   │
│ ⏳ nav │   │  [VNC STREAM]       │   │ ✅ nav │   │  [VNC STREAM]       │   │
│ ✅ type│   │                     │   │ ✅ click│  │                     │   │
│ ⏳ click│  │                     │   │ ✅ type│   │                     │   │
│ ...    │   │                     │   │ ✅ extr│   │                     │   │
│        │   └─────────────────────┘   │        │   └─────────────────────┘   │
│        │                             │        │                             │
│        │   Progress:                 │        │   Progress:                 │
│        │   🏁→🎯→⚡→⏳ Extract        │        │   🏁→🎯→⚡→✅ Complete       │
├────────┴─────────────────────────────┴────────┴─────────────────────────────┤
│  📊 Outputs                                                                   │
│  ┌──────────────────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Agent A Output                   │  │ Agent B Output                   │ │
│  │ JSON/Text result...              │  │ JSON/Text result...              │ │
│  └──────────────────────────────────┘  └──────────────────────────────────┘ │
│                                                                               │
│  🗳️ Which agent performed better?                                            │
│  ( ) Agent A                          ( ) Agent B                            │
│  [Submit Preference]                                                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Key Components:
1. **Prompt Input**: `st.text_area()` with advanced options in expander
2. **Agent Dropdowns**: `st.selectbox()` populated from agent registry
3. **Control Buttons**: `st.button()` with session state management
4. **Timer**: `st.metric()` with auto-refresh using `streamlit-autorefresh`
5. **Tool Call Panels**: Custom `st.container()` with scrollable list of tool calls (left sidebar per agent)
   - Real-time streaming of agent actions
   - Timestamped entries with status icons
   - Expandable details for parameters
6. **Browser IFrames**: `st.components.v1.iframe()` or custom HTML component for VNC streaming
7. **Checkpoint Tracker**: Custom `st.progress()` + icons
8. **Output Display**: `st.json()` for JSON, `st.code()` for text
9. **Preference Selection**: `st.radio()` with two options (Agent A or Agent B) + `st.button()`

### 3.2 Dashboard Tab (`components/dashboard.py`)

#### Dashboard Sections:
```
┌─────────────────────────────────────────────────────────┐
│  📊 Dashboard                          [Arena] [Dashboard]│
├─────────────────────────────────────────────────────────┤
│  🏆 Leaderboard                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Rank  Agent        Wins  Losses  Win Rate  Avg Time ││
│  │  1    Agent Alpha   47     15     75.8%    42.3s    ││
│  │  2    Agent Beta    38     21     64.4%    38.7s    ││
│  │  3    Agent Gamma   31     30     50.8%    51.2s    ││
│  │  4    TinyFish      28     25     52.8%    45.1s    ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  🔥 Top Matchups (Last 30 Days)                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Matchup              Races  Favorite  Win %         ││
│  │ Alpha vs Beta         142   Alpha     64%           ││
│  │ Beta vs Gamma          98   Beta      57%           ││
│  │ Alpha vs TinyFish      87   Alpha     59%           ││
│  │ TinyFish vs Gamma      76   TinyFish  54%           ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  📈 Performance Over Time                                │
│  [Interactive Plotly Chart]                              │
│                                                          │
│  📋 Recent Races                                         │
│  [Table with filters: date, agents, task type]          │
└─────────────────────────────────────────────────────────┘
```

#### Metrics to Display:
- **Leaderboard**: Elo rating or simple win/loss record (no ties)
- **Top Matchups**: Most frequent agent pairings with outcomes
- **Performance Trends**: Time-series charts of agent performance
- **Task Categories**: Breakdown by task type (navigation, data extraction, etc.)
- **Average Completion Time**: Per agent
- **User Preference Trends**: Head-to-head win rates, bar charts

---

## Phase 4: Database Design (Week 3)

### 4.1 Database Schema (`database/models.py`)

**Technology**: PostgreSQL (via Supabase for easy deployment) or SQLite for development

#### Tables:

**1. `agents` Table**
```sql
- id: UUID (PK)
- name: VARCHAR
- version: VARCHAR
- description: TEXT
- created_at: TIMESTAMP
```

**2. `races` Table**
```sql
- id: UUID (PK)
- prompt: TEXT
- prompt_domains: TEXT (JSON array)
- prompt_schema: TEXT (JSON)
- agent_a_id: UUID (FK -> agents)
- agent_b_id: UUID (FK -> agents)
- started_at: TIMESTAMP
- completed_at: TIMESTAMP
- duration_seconds: FLOAT
- status: ENUM (running, completed, stopped, error)
- created_at: TIMESTAMP
```

**3. `agent_executions` Table**
```sql
- id: UUID (PK)
- race_id: UUID (FK -> races)
- agent_id: UUID (FK -> agents)
- checkpoints: TEXT (JSON array of checkpoint timestamps)
- output: TEXT (JSON)
- error_message: TEXT
- execution_time: FLOAT
- final_status: ENUM (success, failure, stopped)
```

**4. `user_preferences` Table**
```sql
- id: UUID (PK)
- race_id: UUID (FK -> races)
- preferred_agent_id: UUID (FK -> agents)
- preference_type: ENUM (agent_a, agent_b)
- feedback_notes: TEXT (optional)
- created_at: TIMESTAMP
```

**5. `leaderboard_cache` Table** (for performance)
```sql
- agent_id: UUID (PK, FK -> agents)
- total_races: INTEGER
- wins: INTEGER
- losses: INTEGER
- win_rate: FLOAT
- avg_execution_time: FLOAT
- last_updated: TIMESTAMP
```

### 4.2 Database Operations
- **Platform**: Supabase (managed PostgreSQL with REST API)
- **Connection Pooling**: SQLAlchemy engine with connection pool via Supabase connection string
- **Async Operations**: For non-blocking database writes
- **Caching**: Supabase built-in caching or in-memory cache for leaderboard data
- **Migrations**: Alembic for schema versioning or Supabase migrations UI
- **Storage**: Supabase Storage for screenshots, recordings, and agent assets

---

## Phase 5: Agent Execution Engine (Week 4)

### 5.1 Race Orchestrator (`utils/race_orchestrator.py`)

Key responsibilities:
1. **Parallel Execution**: Run both agents concurrently using `asyncio`
2. **State Management**: Track execution state in Streamlit session state
3. **Browser Management**: Create isolated browser sessions
4. **Checkpoint Monitoring**: Poll agents for checkpoint updates
5. **Timeout Handling**: Max execution time limits
6. **Error Recovery**: Graceful failure handling

### 5.2 Browser Session Streaming

**Selected Approach: VNC Streaming via noVNC**

**Implementation**:
- Use **noVNC** (HTML5 VNC client) for browser session streaming
- Each agent gets a dedicated VNC server connection
- Real-time, low-latency browser display
- Support for visual feedback of agent actions

**Architecture**:
1. **VNC Server**: Run on AWS Lambda or EC2 with Xvfb (virtual display)
2. **noVNC Client**: Embedded in Streamlit via custom HTML component
3. **WebSocket Connection**: Between noVNC client and VNC server
4. **Playwright/Selenium**: Connects to Xvfb display for browser automation

**Benefits**:
- True real-time viewing experience
- Standard VNC protocol (battle-tested)
- Works with any browser automation tool
- Can capture full session recordings

### 5.3 Prompt Parser (`utils/prompt_parser.py`)
Extracts structured information from natural language:
- Domain hints (URLs, domains)
- JSON schema requirements
- Task type classification
- Constraint extraction

Potentially use LLM (GPT-4) for advanced parsing

---

## Phase 6: Integration with BrowserArena Methodology (Week 4)

### 6.1 Task Design Principles (from paper)
Based on the **BrowserArena** research paper insights:

1. **Real-world Tasks**: Use actual websites, not simulations
2. **Task Decomposition**: Break complex tasks into checkpoint stages
3. **Evaluation Metrics**:
   - Task completion rate
   - Execution time
   - Error rate
   - User preference (our addition)

### 6.2 Agent Compatibility
- **Standardized Interface**: Ensure agents follow BrowserArena agent protocol
- **Action Space**: Support common actions (click, type, navigate, wait)
- **Observation Space**: HTML, screenshots, accessibility tree

### 6.3 Benchmark Tasks (Optional Enhancement)
Pre-configured tasks inspired by BrowserArena:
- E-commerce checkout
- Form filling
- Data extraction from tables
- Multi-step navigation
- Search and filter operations

---

## Phase 7: Deployment Strategy (Week 5)

### 7.1 Streamlit Community Cloud Deployment

**Steps**:
1. Push code to GitHub repository
2. Sign in to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repository
4. Configure secrets for:
   - Supabase database URL
   - Supabase API keys
   - AWS Lambda function URLs
   - Agent API keys (OpenAI, Anthropic, Google, TinyFish)
5. Deploy with auto-scaling

**Configuration** (`.streamlit/config.toml`):
```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
```

**Secrets Configuration** (`.streamlit/secrets.toml`):
```toml
[supabase]
url = "https://your-project.supabase.co"
key = "your-anon-key"

[aws]
lambda_function_url = "https://your-lambda-url.amazonaws.com"
region = "us-east-1"

[agents]
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."
google_api_key = "..."
tinyfish_api_key = "..."
```

### 7.2 Supabase Setup

**Database Configuration**:
1. Create new Supabase project at [supabase.com](https://supabase.com)
2. Run SQL migrations for tables (agents, races, agent_executions, user_preferences, leaderboard_cache)
3. Enable Row Level Security (RLS) policies for anonymous access
4. Set up database indexes for performance:
   - Index on `races.created_at` for recent races query
   - Index on `user_preferences.preferred_agent_id` for leaderboard aggregation
   - Index on `agent_executions.agent_id` for agent performance lookup

**Supabase Storage Setup**:
1. Create bucket: `agent-screenshots` (public read access)
2. Create bucket: `agent-recordings` (public read access)
3. Create bucket: `agent-assets` (public read access for TinyFish agent code)
4. Set up lifecycle policies for auto-deletion after 30 days (optional)

**Connection in App**:
```python
import os
from supabase import create_client, Client

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)
```

### 7.3 AWS Lambda + Playwright for Browser Execution

**Why AWS Lambda?**
- Serverless, pay-per-execution pricing
- Scales automatically with concurrent races
- Playwright officially supports Lambda deployment
- Can run headless browsers with Xvfb

**Lambda Function Setup**:

1. **Create Lambda Layer for Playwright**:
   - Use [playwright-aws-lambda](https://github.com/JupiterOne/playwright-aws-lambda) package
   - Include Chromium binary in layer
   - Python 3.11 runtime

2. **Lambda Function Code** (example):
```python
import json
import asyncio
from playwright.async_api import async_playwright

async def execute_agent(prompt, agent_config):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Agent execution logic here
        # Stream tool calls and checkpoints back to Streamlit
        await browser.close()
    return {"status": "success", "output": "..."}

def lambda_handler(event, context):
    prompt = event['prompt']
    agent_config = event['agent_config']
    result = asyncio.run(execute_agent(prompt, agent_config))
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

3. **Configuration**:
   - Memory: 2048 MB (minimum for Chromium)
   - Timeout: 5 minutes (max execution time)
   - Environment variables: Agent API keys
   - Function URL: Enable for HTTPS invocation from Streamlit

4. **VNC Streaming Consideration**:
   - Lambda functions can't run VNC servers directly
   - Alternative: Use EC2 instance with auto-scaling for VNC+browsers
   - Or: Stream screenshots from Lambda, upgrade to EC2 for VNC later

**Recommended Architecture**:
- **Phase 1 (MVP)**: Lambda for browser execution, screenshot streaming
- **Phase 2 (Enhanced)**: Migrate to EC2 Auto Scaling with VNC for real-time streaming

### 7.4 Agent API Integration

**Agent Registry Configuration**:

```python
# agents/agent_registry.py
AGENTS = {
    "gpt4-agent": {
        "name": "GPT-4 Web Agent",
        "api": "openai",
        "model": "gpt-4-turbo",
        "api_key_env": "OPENAI_API_KEY"
    },
    "claude-agent": {
        "name": "Claude Sonnet 4.5 Agent",
        "api": "anthropic",
        "model": "claude-sonnet-4-5",
        "api_key_env": "ANTHROPIC_API_KEY"
    },
    "gemini-agent": {
        "name": "Gemini 2.0 Agent",
        "api": "google",
        "model": "gemini-2.0-flash-exp",
        "api_key_env": "GOOGLE_API_KEY"
    },
    "tinyfish-agent": {
        "name": "TinyFish Agent",
        "api": "custom",
        "endpoint": "https://api.tinyfish.ai/v1/agent",
        "api_key_env": "TINYFISH_API_KEY",
        "codebase_url": "https://github.com/your-org/tinyfish-agent"
    }
}
```

**TinyFish Agent Integration**:
- Store TinyFish agent codebase in `/agents/implementations/tinyfish/`
- Link to codebase from dashboard
- Highlight as "custom agent" in UI
- Use Supabase Storage to host agent documentation/specs

---

## Phase 8: Testing & Optimization (Week 6)

### 8.1 Testing Strategy
- **Unit Tests**: Agent logic, database operations
- **Integration Tests**: Full race execution
- **UI Tests**: Streamlit component rendering
- **Load Tests**: Multiple concurrent races
- **User Acceptance Testing**: Beta user feedback

### 8.2 Performance Optimizations
- **Caching**: `@st.cache_data` for leaderboard queries
- **Lazy Loading**: Load browser sessions on demand
- **Database Indexing**: Index foreign keys and timestamp columns
- **Connection Pooling**: Reuse database connections
- **CDN**: Static assets via CDN

### 8.3 Monitoring
- **Logging**: Structured logging for debugging
- **Error Tracking**: Sentry or similar
- **Analytics**: Usage metrics, popular matchups
- **Performance Monitoring**: Response times, execution duration

---

## Phase 9: Documentation & Launch (Week 6)

### 9.1 Documentation
- **README.md**: Project overview, setup instructions
- **CONTRIBUTING.md**: Guide for adding new agents
- **API.md**: Agent interface specification
- **DEPLOYMENT.md**: Deployment guide
- **USER_GUIDE.md**: End-user documentation

### 9.2 Launch Checklist
- [ ] All core features implemented
- [ ] Database migrations run
- [ ] Secrets configured
- [ ] Performance tested
- [ ] Security review completed
- [ ] Documentation finalized
- [ ] Beta testing completed
- [ ] Monitoring tools configured
- [ ] Deployed to production
- [ ] Launch announcement prepared

---

## Technical Considerations & Challenges

### Challenge 1: Browser Session in IFrames
**Problem**: Security restrictions prevent direct iframe of local browser sessions

**Solution** (based on [browserarena repo](https://github.com/sagnikanupam/browserarena)):
- The BrowserArena project uses **FastChat** with **browser-use** integration
- Browser sessions are rendered through Gradio's interface components
- They integrate Playwright with a visual display system
- For our implementation: Use **VNC-over-WebSocket (noVNC)** for real-time streaming
  - Run VNC server with Xvfb (virtual display) on AWS Lambda/EC2
  - Embed noVNC HTML5 client in Streamlit custom component
  - Stream browser session via WebSocket to iframe
  - Capture tool calls from agent and display in left panel

### Challenge 2: Real-time Updates in Streamlit
**Problem**: Streamlit reruns entire script on interaction

**Solutions**:
- Use `st.session_state` for persistence
- `streamlit-autorefresh` for polling
- WebSocket connection for live updates (custom component)
- Asyncio with Streamlit's event loop

### Challenge 3: Agent Isolation & Security
**Problem**: Agents may access sensitive data or cause system issues

**Solutions** (not a significant concern for API-based agents):
- Using **API-based agents** (OpenAI, Anthropic, Google, TinyFish) eliminates most security risks
- Agents run in provider's infrastructure, not our servers
- Sandboxed browser contexts in Lambda/EC2 for execution environment
- Timeout limits (5 minutes max per race)
- Rate limiting on API calls
- Network isolation for browser instances
- No direct system access for agents

### Challenge 4: Scalability
**Problem**: Multiple concurrent races require significant resources

**Solutions**:
- Queue system for races
- Limit concurrent executions
- Scale browser instances separately
- Use cloud browser services
- Implement race scheduling

---

## Future Enhancements (Post-MVP)

1. **Multi-Agent Races**: Compare 3+ agents simultaneously
2. **Custom Agent Upload**: Users can upload their own agents
3. **Task Templates**: Pre-built tasks for common scenarios
4. **Replay Feature**: Replay past races
5. **Agent Training Data**: Use preference data to improve agents
6. **Collaborative Filtering**: Recommend agent matchups
7. **Real-time Collaboration**: Multiple users watch same race
8. **API Access**: Programmatic access to arena
9. **Mobile Support**: Responsive design for mobile viewing
10. **Advanced Analytics**: ML-based performance prediction

---

## Timeline Summary

| Week | Phase | Deliverables | Status |
|------|-------|-------------|---------|
| 1 | Setup & Architecture | Repo structure, dependencies, architecture doc | ✅ COMPLETE |
| 2 | Agent Infrastructure | Base agent class, registry, 2+ sample agents | ✅ COMPLETE |
| 3 | UI Development | Arena interface, dashboard, basic styling | ✅ COMPLETE |
| 3 | Database | Schema design, models, basic queries | ✅ COMPLETE |
| 4 | Execution Engine | Race orchestrator, browser sessions, checkpoints | ✅ COMPLETE |
| 4 | BrowserArena Integration | Task design, agent compatibility | ⏳ IN PROGRESS |
| 5 | Deployment | Production deployment, database hosting | 🔄 AWS Lambda Setup |
| 6 | Testing & Polish | Testing, optimization, documentation | ⏸️ PENDING |
| 6 | Launch | Public launch, monitoring | ⏸️ PENDING |

**Total Estimated Time**: 6 weeks for MVP
**Current Progress**: ~70% Complete (Week 4-5)

---

## Success Metrics

1. **User Engagement**: 
   - Daily active users
   - Races per user
   - Preference submission rate

2. **Agent Performance**:
   - Task completion rate
   - Average execution time
   - Error rate

3. **Platform Performance**:
   - Page load time < 3s
   - Race execution latency < 1s
   - System uptime > 99%

4. **Data Collection**:
   - Preferences collected per week
   - Unique agent matchups tested
   - Dataset size for agent improvement

---

## Implementation Decisions

1. **Agent Integration**: ✅ **Using API-based agents** (OpenAI, Anthropic, Google) + TinyFish custom agent
   - TinyFish agent codebase will be included and linked in the arena
   - No need to build agents from scratch
   - Focus on integration layer and UI

2. **Browser Sessions**: ✅ **VNC streaming via noVNC**
   - Real-time viewing experience
   - Better user engagement
   - Standard protocol, battle-tested

3. **Deployment Platform**: ✅ **Streamlit Community Cloud**
   - Native support, easy deployment
   - Free tier with auto-scaling

4. **Database**: ✅ **PostgreSQL via Supabase**
   - Managed service, easy setup
   - Built-in storage for assets
   - REST API for frontend integration

5. **Authentication**: ✅ **Anonymous users** (for now)
   - Lower barrier to entry
   - Focus on collecting preference data
   - Can add auth later for personalization

6. **Agent Selection**: ✅ **4 agents at launch**
   - GPT-4 Web Agent (OpenAI)
   - Claude 3.5 Sonnet Agent (Anthropic)
   - Gemini 2.0 Agent (Google)
   - TinyFish Agent (custom)

---

## References

- **BrowserArena Paper**: https://arxiv.org/pdf/2510.02418
- **BrowserArena Repo**: https://github.com/sagnikanupam/browserarena
- **Streamlit Docs**: https://docs.streamlit.io
- **Playwright Docs**: https://playwright.dev
- **noVNC**: https://github.com/novnc/noVNC

---

---

## Current Status (November 12, 2024)

### ✅ Completed Components

**Phase 1 - Foundation:**
- ✅ Conda environment with Python 3.11
- ✅ All dependencies installed
- ✅ Repository structure established
- ✅ Git initialized

**Phase 2 - Agent Infrastructure:**
- ✅ `BaseAgent` abstract class with `ToolCall`, `Checkpoint`, `AgentResult` models
- ✅ `AgentRegistry` with 4 configured agents
- ✅ Agent implementations for OpenAI, Anthropic, Google, TinyFish
- ✅ Simulated tool calling and checkpoints for MVP

**Phase 3 - Database Integration:**
- ✅ Supabase PostgreSQL database configured
- ✅ All 5 tables created with proper relationships
- ✅ Database triggers for automatic leaderboard updates
- ✅ CRUD operations implemented
- ✅ Connection pooling via Supabase client

**Phase 3 - UI Development:**
- ✅ Main arena interface with side-by-side layout
- ✅ Tool Calls (left) | Browser (right) for each agent
- ✅ Task input with domains and JSON schema
- ✅ Agent selection dropdowns
- ✅ Control panel (Start, Stop, Reset, Timer)
- ✅ Real-time progress indicators
- ✅ Output display (Agent A | Agent B)
- ✅ Voting interface (Agent A or Agent B, no tie)
- ✅ Dashboard with leaderboard, matchups, and performance stats
- ✅ Database integration for all UI components

**Phase 4 - Execution Engine:**
- ✅ `RaceOrchestrator` managing concurrent agent execution
- ✅ Async race execution with `asyncio.gather()`
- ✅ Session state management
- ✅ Results collection and storage
- ✅ Race lifecycle (initialize → execute → complete → vote)

### 🔄 In Progress

**Phase 5 - AWS Lambda Deployment:**
- ✅ Lambda function code created (`handler.py`, `agent_executor.py`)
- ✅ Deployment package created (`function.zip`)
- ✅ Documentation created (setup guides, checklists)
- 🔄 Lambda function deployed to AWS (handler configured)
- ⏸️ Playwright layer (optional, not needed for MVP)
- ⏸️ VNC streaming integration

### ⏸️ Pending

**Phase 6 - Testing & Polish:**
- Unit tests for components
- Integration tests for full race flow
- Performance optimization
- Error handling improvements

**Phase 7 - Deployment:**
- Streamlit Cloud deployment
- Environment secrets configuration
- Production monitoring

### 📝 Known Limitations (MVP)

1. **Browser Sessions**: Placeholder iframes (waiting for VNC streaming)
2. **Tool Calls**: Simulated for testing (will be real with Lambda integration)
3. **Agent Execution**: Local simulation (transitioning to Lambda)
4. **Authentication**: Anonymous users only
5. **Rate Limiting**: Not implemented yet

### 🎯 Next Immediate Steps

1. **Complete Lambda Setup:**
   - Make Playwright import optional in Lambda code
   - Test health check endpoint
   - Test basic agent execution
   - Get Lambda Function URL

2. **Connect Lambda to Streamlit:**
   - Add Function URL to `.env`
   - Create `utils/lambda_client.py`
   - Update agent implementations to call Lambda

3. **Test End-to-End:**
   - Run full race with Lambda execution
   - Verify database storage
   - Test voting and leaderboard updates

4. **Deploy to Streamlit Cloud:**
   - Push to GitHub
   - Configure secrets
   - Deploy application

### 📚 Documentation Files Created

- `README.md` - Project overview
- `EXECUTION_PLAN.md` - This file
- `CONFIGURATION.md` - Supabase setup guide
- `PHASE2_COMPLETE.md` - Agent implementation summary
- `PHASE3_COMPLETE.md` - Database integration summary
- `UI_FIXES.md` - UI improvements log
- `QUICK_FIX_SUMMARY.md` - Latest fixes applied
- `lambda/START_HERE.md` - Lambda setup entry point
- `lambda/LAMBDA_CHECKLIST.md` - Quick setup guide
- `lambda/AWS_CONSOLE_SETUP.md` - Detailed Lambda setup
- `lambda/README.md` - Lambda code documentation

---

**Next Steps**: Complete AWS Lambda setup, then deploy to Streamlit Cloud.

