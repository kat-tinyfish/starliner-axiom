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
    ('claude_web_agent', 'Claude Sonnet 4.5 Agent', '1.0', 'Anthropic Claude Sonnet 4.5 with advanced reasoning', 'anthropic', 'claude-sonnet-4-5'),
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
    UPDATE leaderboard_cache
    SET 
        total_races = total_races + 1,
        wins = wins + 1,
        win_rate = (wins + 1.0) / (total_races + 1.0),
        last_updated = NOW()
    WHERE agent_id = NEW.preferred_agent_id;
    
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

CREATE TRIGGER trigger_update_avg_execution_time
AFTER INSERT ON agent_executions
FOR EACH ROW
EXECUTE FUNCTION update_agent_avg_execution_time();
