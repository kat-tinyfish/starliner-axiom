# Phase 3: Database Integration Setup Guide

Complete guide for setting up Supabase and integrating it with your Web Agent Arena.

---

## 🎯 What You'll Accomplish

By the end of Phase 3, you'll have:
- ✅ Supabase PostgreSQL database
- ✅ Persistent race results
- ✅ Real leaderboard with actual data
- ✅ User preference tracking
- ✅ Historical analytics

---

## 📋 Step 1: Create Supabase Account (5 minutes)

### 1.1 Sign Up

1. Go to **https://supabase.com**
2. Click **"Start your project"**
3. Sign up with:
   - GitHub (recommended - instant)
   - OR email/password

### 1.2 Create New Project

1. Click **"New Project"**
2. Fill in details:
   - **Name**: `web-agent-arena`
   - **Database Password**: Create a strong password (save it!)
   - **Region**: Choose closest to you (e.g., `us-east-1`)
   - **Pricing Plan**: Free (perfect for development)

3. Click **"Create new project"**
4. Wait 2-3 minutes for setup

---

## 📋 Step 2: Get Database Credentials (2 minutes)

### 2.1 Find Your Credentials

Once project is ready:

1. Go to **Settings** (left sidebar, gear icon)
2. Click **API**
3. Copy these values:

   **Project URL:**
   ```
   https://xxxxxxxxxxxxx.supabase.co
   ```

   **anon/public key:**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...
   ```

   **service_role key:** (keep this secret!)
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...
   ```

### 2.2 Save to .env File

Open your `.env` file and update:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📋 Step 3: Create Database Tables (3 minutes)

### 3.1 Open SQL Editor

1. In Supabase dashboard, click **SQL Editor** (left sidebar)
2. Click **"New Query"**

### 3.2 Run Database Setup SQL

Copy and paste this SQL into the editor:

```sql
-- ============================================================================
-- Web Agent Arena Database Schema
-- ============================================================================

-- Drop existing tables if they exist (for fresh setup)
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS agent_executions CASCADE;
DROP TABLE IF EXISTS races CASCADE;
DROP TABLE IF EXISTS leaderboard_cache CASCADE;
DROP TABLE IF EXISTS agents CASCADE;

-- ============================================================================
-- 1. AGENTS TABLE
-- ============================================================================
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    api_provider VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert the 4 launch agents
INSERT INTO agents (name, display_name, version, description, api_provider, model) VALUES
    ('gpt4_web_agent', 'GPT-4 Web Agent', '1.0', 'OpenAI GPT-4 Turbo with web navigation capabilities', 'openai', 'gpt-4-turbo'),
    ('claude_web_agent', 'Claude 3.5 Sonnet Agent', '1.0', 'Anthropic Claude 3.5 Sonnet with advanced reasoning', 'anthropic', 'claude-3-5-sonnet-20241022'),
    ('gemini_web_agent', 'Gemini 2.0 Agent', '1.0', 'Google Gemini 2.0 Flash with multimodal capabilities', 'google', 'gemini-2.0-flash-exp'),
    ('tinyfish_agent', 'TinyFish Agent', '1.0', 'Custom TinyFish web agent with specialized capabilities', 'custom', 'tinyfish-v1');

-- ============================================================================
-- 2. RACES TABLE
-- ============================================================================
CREATE TABLE races (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    prompt_domains TEXT[],
    prompt_schema JSONB,
    agent_a_id UUID NOT NULL REFERENCES agents(id),
    agent_b_id UUID NOT NULL REFERENCES agents(id),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'stopped', 'error')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT different_agents CHECK (agent_a_id != agent_b_id)
);

-- Index for performance
CREATE INDEX idx_races_created_at ON races(created_at DESC);
CREATE INDEX idx_races_status ON races(status);
CREATE INDEX idx_races_agents ON races(agent_a_id, agent_b_id);

-- ============================================================================
-- 3. AGENT EXECUTIONS TABLE
-- ============================================================================
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_id UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id),
    checkpoints JSONB,
    tool_calls JSONB,
    output JSONB,
    error_message TEXT,
    execution_time FLOAT,
    final_status VARCHAR(20) NOT NULL CHECK (final_status IN ('success', 'error', 'timeout', 'stopped')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for performance
CREATE INDEX idx_agent_executions_race ON agent_executions(race_id);
CREATE INDEX idx_agent_executions_agent ON agent_executions(agent_id);

-- ============================================================================
-- 4. USER PREFERENCES TABLE
-- ============================================================================
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_id UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    preferred_agent_id UUID NOT NULL REFERENCES agents(id),
    preference_type VARCHAR(20) NOT NULL CHECK (preference_type IN ('agent_a', 'agent_b')),
    feedback_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for performance
CREATE INDEX idx_user_preferences_race ON user_preferences(race_id);
CREATE INDEX idx_user_preferences_agent ON user_preferences(preferred_agent_id);

-- ============================================================================
-- 5. LEADERBOARD CACHE TABLE
-- ============================================================================
CREATE TABLE leaderboard_cache (
    agent_id UUID PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    total_races INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate FLOAT DEFAULT 0.0,
    avg_execution_time FLOAT DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Initialize leaderboard for all agents
INSERT INTO leaderboard_cache (agent_id, total_races, wins, losses, win_rate, avg_execution_time)
SELECT id, 0, 0, 0, 0.0, 0.0 FROM agents;

-- ============================================================================
-- 6. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update leaderboard cache
CREATE OR REPLACE FUNCTION update_leaderboard_cache()
RETURNS TRIGGER AS $$
BEGIN
    -- Update statistics for the preferred agent (winner)
    UPDATE leaderboard_cache
    SET 
        total_races = total_races + 1,
        wins = wins + 1,
        win_rate = (wins + 1.0) / (total_races + 1.0),
        last_updated = NOW()
    WHERE agent_id = NEW.preferred_agent_id;
    
    -- Update statistics for the other agent (loser)
    UPDATE leaderboard_cache
    SET 
        total_races = total_races + 1,
        losses = losses + 1,
        win_rate = wins::FLOAT / (total_races + 1.0),
        last_updated = NOW()
    WHERE agent_id IN (
        SELECT agent_a_id FROM races WHERE id = NEW.race_id
        UNION
        SELECT agent_b_id FROM races WHERE id = NEW.race_id
    ) AND agent_id != NEW.preferred_agent_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update leaderboard when preference is added
CREATE TRIGGER trigger_update_leaderboard
AFTER INSERT ON user_preferences
FOR EACH ROW
EXECUTE FUNCTION update_leaderboard_cache();

-- Function to update agent's average execution time
CREATE OR REPLACE FUNCTION update_agent_avg_execution_time()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE leaderboard_cache
    SET 
        avg_execution_time = (
            SELECT AVG(execution_time)
            FROM agent_executions
            WHERE agent_id = NEW.agent_id
            AND final_status = 'success'
        ),
        last_updated = NOW()
    WHERE agent_id = NEW.agent_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update avg execution time
CREATE TRIGGER trigger_update_avg_execution_time
AFTER INSERT ON agent_executions
FOR EACH ROW
EXECUTE FUNCTION update_agent_avg_execution_time();

-- ============================================================================
-- 7. ROW LEVEL SECURITY (Optional - enable for production)
-- ============================================================================

-- For now, we'll allow anonymous access for MVP
-- Uncomment these in production with proper authentication

-- ALTER TABLE races ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_executions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Create policies (example for anonymous read access)
-- CREATE POLICY "Allow anonymous read access" ON races FOR SELECT USING (true);

-- ============================================================================
-- SETUP COMPLETE!
-- ============================================================================

-- Verify tables were created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

### 3.3 Run the Query

1. Click **"Run"** (or press Cmd/Ctrl + Enter)
2. You should see: **"Success. No rows returned"**
3. Verify tables in the **Table Editor** (left sidebar)

You should see 5 tables:
- ✅ `agents` (4 rows)
- ✅ `races`
- ✅ `agent_executions`
- ✅ `user_preferences`
- ✅ `leaderboard_cache` (4 rows)

---

## ✅ Verification Checklist

After completing the steps above:

- [ ] Supabase account created
- [ ] Project created and running
- [ ] Copied Project URL to .env
- [ ] Copied anon key to .env
- [ ] Copied service_role key to .env
- [ ] Ran database setup SQL
- [ ] Verified 5 tables exist
- [ ] Verified agents table has 4 rows

---

## 🎯 Next Steps

Once you've completed this setup:

1. **Test Connection** - I'll create a connection test script
2. **Implement Database Operations** - CRUD functions for races
3. **Update Arena UI** - Save races to database
4. **Update Dashboard** - Show real leaderboard data
5. **Test End-to-End** - Full race with persistence

---

## 🐛 Troubleshooting

### Can't access Supabase

- Check your internet connection
- Try different browser
- Clear browser cache

### SQL errors

- Make sure you copied the entire SQL block
- Run in SQL Editor (not Terminal)
- Check for any error messages

### Missing credentials

- Go to Settings → API in Supabase dashboard
- Make sure you copied the right keys
- Check for extra spaces when pasting

---

## 📚 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Supabase Python Client](https://supabase.com/docs/reference/python)

---

**Ready?** Let me know when you've completed these steps and I'll help you with the next part! 🚀

