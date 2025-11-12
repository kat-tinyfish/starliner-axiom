#!/bin/bash
# Configuration Setup Script

echo "🔧 Web Agent Arena - Configuration Setup"
echo "========================================"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Local Development Environment Variables

# Supabase (get from https://supabase.com)
SUPABASE_URL=your-project-url-here
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# AWS Lambda (optional for now)
AWS_LAMBDA_FUNCTION_URL=not-configured-yet
AWS_REGION=us-east-1

# Agent API Keys
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here
TINYFISH_API_KEY=your-tinyfish-key-here

# Application Settings
MAX_RACE_DURATION=300
CONCURRENT_RACE_LIMIT=10
DEBUG=True
EOF
    echo "✅ Created .env file"
else
    echo "ℹ️  .env file already exists"
fi

echo ""
echo "📝 Next steps:"
echo "   1. Edit .env and add your API keys"
echo "   2. Follow CONFIGURATION.md for detailed setup"
echo "   3. Run: streamlit run app.py"
echo ""

