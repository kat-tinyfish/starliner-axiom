# Configuration Guide

This guide will help you configure all the services needed for the Web Agent Arena.

## 📝 Quick Checklist

- [ ] Configure Supabase database
- [ ] Get Agent API keys
- [ ] Update `.env` file
- [ ] (Optional) Set up AWS Lambda

## 1️⃣ Supabase Setup (Required)

### Create Supabase Project

1. Go to [supabase.com](https://supweabase.com)
2. Sign up/Sign in
3. Click "New Project"
4. Fill in:
   - **Name**: `web-agent-arena`
   - **Database Password**: (save this!)
   - **Region**: Choose closest to you
5. Click "Create new project"

### Get Supabase Credentials

Once created, go to **Settings → API**:

- **Project URL**: Copy this
- **anon/public key**: Copy this
- **service_role key**: Copy this (keep it secret!)

### Create Database Tables

1. Go to **SQL Editor** in Supabase
2. Click "New Query"
3. Paste and run this SQL:

```sql
-- Create agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create races table
CREATE TABLE races (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    prompt_domains JSONB,
    prompt_schema JSONB,
    agent_a_id UUID REFERENCES agents(id),
    agent_b_id UUID REFERENCES agents(id),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create agent_executions table
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_id UUID REFERENCES races(id),
    agent_id UUID REFERENCES agents(id),
    checkpoints JSONB,
    output JSONB,
    error_message TEXT,
    execution_time FLOAT,
    final_status VARCHAR(20) NOT NULL
);

-- Create user_preferences table
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_id UUID REFERENCES races(id),
    preferred_agent_id UUID REFERENCES agents(id),
    preference_type VARCHAR(20) NOT NULL,
    feedback_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create leaderboard_cache table
CREATE TABLE leaderboard_cache (
    agent_id UUID PRIMARY KEY REFERENCES agents(id),
    total_races INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate FLOAT DEFAULT 0.0,
    avg_execution_time FLOAT DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_races_created_at ON races(created_at);
CREATE INDEX idx_user_preferences_agent ON user_preferences(preferred_agent_id);
CREATE INDEX idx_agent_executions_agent ON agent_executions(agent_id);

-- Insert default agents
INSERT INTO agents (name, version, description) VALUES
    ('gpt4_web_agent', '1.0', 'OpenAI GPT-4 Turbo with web navigation capabilities'),
    ('claude_web_agent', '1.0', 'Anthropic Claude 3.5 Sonnet with advanced reasoning'),
    ('gemini_web_agent', '1.0', 'Google Gemini 2.0 Flash with multimodal capabilities'),
    ('tinyfish_agent', '1.0', 'TinyFish custom web agent with specialized capabilities');
```

4. You should see "Success. No rows returned"

### Enable Row Level Security (Optional but Recommended)

For now, we'll allow anonymous access. In production, you'd want to add RLS policies.

1. Go to **Authentication → Policies**
2. For each table, you can add policies later

### Update Your Config

Add your Supabase credentials to `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

## 2️⃣ Agent API Keys (Required)

You need API keys for the 4 agents:

### OpenAI (GPT-4)

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up/Sign in
3. Click on your profile → "API keys"
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Anthropic (Claude)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up/Sign in
3. Go to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### Google AI (Gemini)

1. Go to [ai.google.dev](https://ai.google.dev)
2. Click "Get API key in Google AI Studio"
3. Sign in with Google account
4. Click "Create API Key"
5. Copy the key
6. Add to `.env`: `GOOGLE_API_KEY=...`

### TinyFish (Custom)

If you have a TinyFish API key:
1. Add to `.env`: `TINYFISH_API_KEY=...`

Otherwise, leave as placeholder for now.

## 3️⃣ AWS Lambda (Optional - Can Skip for MVP)

AWS Lambda is used for browser execution. For initial development, you can skip this and run browsers locally.

To set up later:
1. Follow instructions in `lambda/README.md`
2. Deploy Lambda function with Playwright
3. Update `.env` with Lambda URL

## 4️⃣ Verify Configuration

Test your database connection:

```bash
python -c "from database.connection import test_connection; print('✅ Database connected!' if test_connection() else '❌ Database connection failed')"
```

## 5️⃣ Run the App

```bash
streamlit run app.py
```

## 🔒 Security Notes

- **Never commit `.env` or `secrets.toml`** to git (already in `.gitignore`)
- **Keep service_role_key secret** - it has full database access
- **Use environment variables** in production
- **Rotate keys regularly**

## 🆘 Troubleshooting

### Database Connection Failed

- Check Supabase URL and keys are correct
- Verify Supabase project is active
- Check your internet connection

### API Key Not Working

- Make sure you copied the entire key
- Check for extra spaces or quotes
- Verify the API service is active

### Module Not Found

- Make sure conda environment is activated: `conda activate axiom`
- Reinstall dependencies: `pip install -r requirements.txt`

## 📚 Next Steps

Once configuration is complete:
1. Test the app: `streamlit run app.py`
2. Start Phase 2 agent implementation
3. Test with real API calls
4. Build out the full arena functionality

## 🔗 Useful Links

- [Supabase Docs](https://supabase.com/docs)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic API Docs](https://docs.anthropic.com)
- [Google AI Docs](https://ai.google.dev/docs)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)

