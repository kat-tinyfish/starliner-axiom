# 🚀 Quick Start Guide

Get the Web Agent Arena running in 5 minutes!

## Prerequisites

- ✅ Conda environment `axiom` is available
- ✅ You're in the project directory: `/Users/kat.tinyfish/starliner/starliner-axiom`

## Installation (One Command)

```bash
# Activate conda environment
conda activate axiom

# Run installation script
./install.sh
```

The script will:
1. ✅ Check conda environment
2. 📦 Install all Python dependencies
3. 🎭 Install Playwright browsers
4. 📝 Create configuration templates

## Manual Installation (Alternative)

If you prefer manual installation:

```bash
# 1. Activate environment
conda activate axiom

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright
playwright install chromium

# 4. Create config files
cp .env.template .env
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

## Run the App

```bash
# Make sure axiom is activated
conda activate axiom

# Start Streamlit
streamlit run app.py
```

The app will open at: **http://localhost:8501**

## What You'll See

The current version includes:
- ✅ Arena interface (placeholder)
- ✅ Dashboard interface (placeholder)
- ✅ Agent selection (4 agents)
- ✅ Task input
- ✅ Control buttons
- ⚠️ **Note**: Most features are placeholders waiting for Phase 2 implementation

## Configuration (Optional for Now)

To fully configure the app (required for Phase 2+):

### 1. Supabase Setup
Edit `.env` or `.streamlit/secrets.toml`:
```toml
[supabase]
url = "https://your-project.supabase.co"
key = "your-anon-key"
```

### 2. Agent API Keys
Add your API keys:
```toml
[agents]
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."
google_api_key = "..."
tinyfish_api_key = "..."
```

## Verify Installation

Test that everything is installed:

```bash
python -c "import streamlit, playwright, supabase, sqlalchemy, pandas, plotly; print('✅ All dependencies working!')"
```

## Next Steps

1. **Phase 1 Complete** ✅ - Project structure is ready!
2. **Start Phase 2** - Begin agent integration
   - See `EXECUTION_PLAN.md` for detailed roadmap
   - Start with OpenAI agent implementation
3. **Set up Supabase** - Create database tables
4. **Deploy AWS Lambda** - For browser execution

## Troubleshooting

### Streamlit won't start
```bash
# Check if port is in use
lsof -i :8501

# Try a different port
streamlit run app.py --server.port 8502
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Playwright browser not found
```bash
# Reinstall browsers
python -m playwright install chromium
```

## Project Structure

```
starliner-axiom/
├── app.py              # 👈 START HERE - Main app
├── agents/             # Agent implementations
├── components/         # UI components
├── database/           # Database models
├── utils/              # Utilities
├── lambda/             # AWS Lambda functions
├── static/             # CSS and assets
└── *.md                # Documentation
```

## Documentation

- 📖 `README.md` - Project overview
- 📋 `EXECUTION_PLAN.md` - 6-week implementation plan
- ✅ `PROJECT_STATUS.md` - Current status (Phase 1 complete!)
- 🛠️ `SETUP.md` - Detailed setup guide
- 🚀 `QUICKSTART.md` - This file

## Support

- Check console output for errors
- Review browser console (F12)
- Read TODO comments in code
- See EXECUTION_PLAN.md for architecture

---

**🎉 You're all set! The foundation is complete. Time to build the arena!**

