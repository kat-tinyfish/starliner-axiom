# 🏆 Web Agent Arena

A live web agent comparison platform that enables users to pit two AI agents against each other in real-time browser tasks, watching their performance via VNC streaming with competitive timing and outcome tracking.

## 🌟 Features

- **Head-to-Head Agent Battles**: Compare two web agents side-by-side on the same task
- **Real-time VNC Streaming**: Watch agents navigate browsers in real-time
- **Tool Call Visibility**: See each agent's actions (clicks, navigation, typing) as they happen
- **Checkpoint Tracking**: Visual progress indicators showing execution stages
- **Race Timer**: Competitive timing creates urgency and excitement
- **User Preference Collection**: Vote for the better agent after each race
- **Leaderboard & Analytics**: Track agent performance and popular matchups
- **4 Agents at Launch**: GPT-4, Claude 3.5 Sonnet, Gemini 2.0, and TinyFish

## 🏗️ Architecture

- **Frontend**: Streamlit
- **Hosting**: Streamlit Community Cloud
- **Database**: Supabase (PostgreSQL)
- **Browser Execution**: AWS Lambda + Playwright
- **Browser Streaming**: VNC + noVNC
- **Agents**: OpenAI, Anthropic, Google, TinyFish APIs

## 🚀 Quick Start (Conda Environment)

### Prerequisites

- Conda or Miniconda installed
- Python 3.11+
- Git

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/your-org/starliner-axiom.git
cd starliner-axiom
```

2. **Create conda environment from environment.yml**:
```bash
conda env create -f environment.yml
conda activate axiom
```

Alternatively, if you already have the `axiom` environment:
```bash
conda activate axiom
pip install -r requirements.txt
```

3. **Install Playwright browsers**:
```bash
playwright install chromium
```

4. **Set up environment variables**:
```bash
cp .env.template .env
# Edit .env with your API keys and configuration
```

For Streamlit deployment:
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit secrets.toml with your credentials
```

5. **Set up Supabase**:
- Create a new project at [supabase.com](https://supabase.com)
- Run the SQL migrations in `database/migrations/`
- Update `.env` with your Supabase credentials

6. **Run the application**:
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## 📁 Project Structure

```
starliner-axiom/
├── app.py                      # Main Streamlit entry point
├── requirements.txt            # Python dependencies
├── environment.yml             # Conda environment specification
├── .streamlit/
│   ├── config.toml            # Streamlit configuration
│   └── secrets.toml           # API keys (not in git)
├── agents/
│   ├── base_agent.py          # Abstract base agent class
│   ├── agent_registry.py      # Agent registration
│   └── implementations/       # Agent implementations
├── database/
│   ├── models.py              # SQLAlchemy models
│   ├── connection.py          # Database connection
│   └── migrations/            # Alembic migrations
├── components/
│   ├── arena.py               # Main arena UI
│   ├── dashboard.py           # Leaderboard & analytics
│   ├── tool_call_panel.py     # Tool call display
│   └── vnc_viewer.py          # VNC iframe component
├── utils/
│   ├── browser_session.py     # Browser management
│   ├── lambda_client.py       # AWS Lambda client
│   └── prompt_parser.py       # Prompt parsing
└── lambda/                    # AWS Lambda functions
```

## 🔧 Configuration

### Agent API Keys

You'll need API keys for:
- **OpenAI**: [platform.openai.com](https://platform.openai.com)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com)
- **Google AI**: [ai.google.dev](https://ai.google.dev)
- **TinyFish**: [api.tinyfish.ai](https://api.tinyfish.ai)

### AWS Lambda Setup

For browser execution, set up an AWS Lambda function:
1. Follow the guide in `lambda/README.md`
2. Deploy the Lambda function with Playwright layer
3. Update `.env` with the Lambda function URL

### Supabase Setup

1. Create tables using migrations in `database/migrations/`
2. Set up Row Level Security (RLS) policies
3. Create storage buckets for screenshots and recordings

## 📊 Database Schema

- **agents**: Agent metadata and configuration
- **races**: Race execution details and results
- **agent_executions**: Individual agent performance data
- **user_preferences**: User votes and preferences
- **leaderboard_cache**: Aggregated leaderboard statistics

## 🎯 Usage

1. **Enter a task**: Describe what you want the agents to do
2. **Select agents**: Choose two agents to compete
3. **Start the race**: Watch both agents work in real-time
4. **Review outputs**: Compare the results from each agent
5. **Vote**: Select which agent performed better
6. **Check leaderboard**: See how agents rank over time

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

### Adding a New Agent

1. Create a new implementation in `agents/implementations/`
2. Inherit from `BaseAgent` class
3. Register in `agents/agent_registry.py`
4. Add API configuration to `.env`

## 📝 License

[Apache 2.0 License](LICENSE)

## 🙏 Acknowledgements

This project is informed by:
- **BrowserArena** ([paper](https://arxiv.org/pdf/2510.02418), [repo](https://github.com/sagnikanupam/browserarena))
- **arena.browserbase.com** for UI inspiration

## 📧 Contact

For questions or support, please open an issue or contact [your-email].

## 🗺️ Roadmap

- [ ] Phase 1: Project setup and core infrastructure ⏳
- [ ] Phase 2: Agent integration and execution engine
- [ ] Phase 3: UI development (arena + dashboard)
- [ ] Phase 4: Database and data storage
- [ ] Phase 5: VNC streaming integration
- [ ] Phase 6: Testing and deployment
- [ ] Future: Multi-agent races (3+ agents)
- [ ] Future: Custom agent uploads
- [ ] Future: Replay feature

