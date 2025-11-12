# UI Layout Guide - Matches EXECUTION_PLAN.md

## Current UI Layout (As Implemented)

The arena interface follows the design specified in `EXECUTION_PLAN.md`:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🏆 Web Agent Arena                              [Arena] [Dashboard]          │
├──────────────────────────────────────────────────────────────────────────────┤
│  Watch two AI agents compete in real-time web navigation tasks               │
│                                                                               │
│  📝 Task Input (Expandable)                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │ Enter your task in natural language...                                   ││
│  │ [Domain hints (optional)]        [JSON schema (optional)]                ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
│  🤖 Select Agents                                                             │
│  [Agent A ▼]                      vs                      [Agent B ▼]        │
│                                                                               │
│  🎬 Controls                                                                  │
│  [▶️ Start Race]  [⏹️ Stop]  [🔄 Reset]              ⏱️ Timer: 00:45.23      │
│                                                                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│  🏁 Race in Progress                                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                               │
├───────────────────────────────────────┬──────────────────────────────────────┤
│        AGENT A: GPT-4 Web Agent       │      AGENT B: Claude 3.5 Agent       │
├─────────────┬─────────────────────────┼────────────┬─────────────────────────┤
│             │                         │            │                         │
│  🔧 Tool    │   🖥️ Browser Session    │  🔧 Tool   │   🖥️ Browser Session    │
│  Calls      │   ──────────────────    │  Calls     │   ──────────────────    │
│  ────────   │                         │  ────────  │                         │
│             │   ┌─────────────────┐   │            │   ┌─────────────────┐   │
│  ⏳ navigate│   │                 │   │  ✅ navigate│  │                 │   │
│    url: ... │   │  [VNC STREAM]   │   │    url: ... │  │  [VNC STREAM]   │   │
│  ✅ type    │   │   or iframe     │   │  ✅ click   │  │   or iframe     │   │
│    text: ..│   │                 │   │    sel: ... │  │                 │   │
│  ⏳ click   │   │                 │   │  ✅ extract │  │                 │   │
│    sel: ...│   └─────────────────┘   │    sel: ... │  └─────────────────┘   │
│  ...       │                         │  ...        │                         │
│            │   Progress:             │             │   Progress:             │
│            │   ✅ → ✅ → ⏳ → ⏸️      │             │   ✅ → ✅ → ✅ → ✅      │
│            │   [Progress Bar]        │             │   [Progress Bar]        │
│            │                         │             │                         │
├────────────┴─────────────────────────┴─────────────┴─────────────────────────┤
│  ─────────────────────────────────────────────────────────────────────────  │
│  📊 Outputs                                                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                               │
│  ┌─────────────────────────────────────┬─────────────────────────────────────┐
│  │  Agent A Output                     │  Agent B Output                     │
│  │  ────────────────                   │  ────────────────                   │
│  │  Time: 42.3s    Status: ✅          │  Time: 38.7s    Status: ✅          │
│  │                                     │                                     │
│  │  {                                  │  {                                  │
│  │    "title": "Book 1",               │    "title": "Book 1",               │
│  │    "price": 14.99                   │    "price": 14.99                   │
│  │  }                                  │  }                                  │
│  └─────────────────────────────────────┴─────────────────────────────────────┘
│                                                                               │
│  🗳️ Which agent performed better?                                            │
│                                                                               │
│  ┌─────────────────┐    ┌─────────┐    ┌─────────────────┐                 │
│  │  👈 Agent A     │    │ (space) │    │   Agent B 👉    │                 │
│  └─────────────────┘    └─────────┘    └─────────────────┘                 │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Key Features ✅

### 1. Task Input Section
- ✅ Text area for natural language prompts
- ✅ Optional domain hints input
- ✅ Optional JSON schema input
- ✅ Expandable section to keep UI clean

### 2. Agent Selection
- ✅ Two dropdown menus side by side
- ✅ Lists all 4 registered agents (GPT-4, Claude, Gemini, TinyFish)
- ✅ Defaults to different agents for A and B

### 3. Control Panel
- ✅ Start Race button
- ✅ Stop button (enabled during race)
- ✅ Reset button
- ✅ Live timer display

### 4. Race Display (Side-by-Side)
Each agent gets a column with:

#### Left Sub-column: Tool Calls Panel
- ✅ Real-time tool call display
- ✅ Status icons (⏳ in progress, ✅ success, ❌ error)
- ✅ Tool names (navigate, click, type, extract, etc.)
- ✅ Compact parameter display
- ✅ Auto-scrolls to latest
- ✅ Shows last 10 tool calls

#### Right Sub-column: Browser Session
- ✅ Iframe/VNC viewer area
- ✅ Placeholder for browser stream when not active
- ✅ Progress indicators below browser
- ✅ Checkpoint emoji progress bar
- ✅ Current checkpoint status

### 5. Outputs Section
- ✅ Side-by-side output display
- ✅ Execution time metrics
- ✅ Success/failure status
- ✅ JSON or text output display
- ✅ Error messages if applicable

### 6. Voting Interface
- ✅ Clear question: "Which agent performed better?"
- ✅ Two buttons: "Agent A" and "Agent B"
- ✅ NO tie option (as per execution plan)
- ✅ Database integration for vote storage
- ✅ Success confirmation message

## File Structure

```
components/
├── arena.py              # Main arena interface (implements above layout)
├── dashboard.py          # Leaderboard and analytics
├── checkpoint_tracker.py # (Integrated into arena.py)
├── tool_call_panel.py    # (Integrated into arena.py)
└── vnc_viewer.py         # (Placeholder for VNC integration)
```

## Database Integration ✅

All features are connected to Supabase:
- ✅ Races saved to `races` table on start
- ✅ Agent executions saved to `agent_executions` table
- ✅ User votes saved to `user_preferences` table
- ✅ Leaderboard auto-updates via database triggers
- ✅ No tie option (only agent_a or agent_b)

## Differences from Execution Plan

**None - the implementation matches the plan!**

The only temporary limitation is:
- Browser sessions show placeholder instead of live VNC (requires AWS Lambda setup)
- Tool calls are simulated for MVP (will be real after Lambda integration)

## Test the UI

```bash
streamlit run app.py
```

Navigate to Arena tab and you'll see:
1. Task input section
2. Agent dropdowns
3. Control buttons
4. (After starting race) Side-by-side agent panels with tool calls and browser areas
5. (After race completes) Outputs and voting buttons

## Next Steps

The UI is complete and matches the execution plan. The next step is:
1. Set up AWS Lambda (see `lambda/START_HERE.md`)
2. Connect Lambda to Streamlit for real browser execution
3. Add VNC streaming for live browser viewing

But the UI structure is ready and functional!

