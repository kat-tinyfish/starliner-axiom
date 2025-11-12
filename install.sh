#!/bin/bash
# Installation script for Web Agent Arena
# Run this after activating the axiom conda environment

set -e  # Exit on error

echo "🏆 Web Agent Arena - Installation Script"
echo "========================================"
echo ""

# Check if conda environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "axiom" ]]; then
    echo "❌ Error: Please activate the axiom conda environment first:"
    echo "   conda activate axiom"
    exit 1
fi

echo "✅ Conda environment 'axiom' is active"
echo ""

# Determine which Python command to use
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Error: Python not found in conda environment"
    echo "   Installing Python in conda environment..."
    conda install -y python=3.11
    PYTHON_CMD="python"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "📍 Python version: $PYTHON_VERSION"
echo "📍 Python command: $PYTHON_CMD"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Python dependencies installed"
echo ""

# Install Playwright browsers
echo "🎭 Installing Playwright Chromium browser..."
playwright install chromium
echo "✅ Playwright browser installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env and add your API keys!"
fi

# Create secrets.toml if it doesn't exist
if [ ! -f .streamlit/secrets.toml ]; then
    echo "📝 Creating secrets.toml from template..."
    cp .streamlit/secrets.toml.template .streamlit/secrets.toml
    echo "⚠️  Please edit .streamlit/secrets.toml and add your credentials!"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Edit .env with your API keys"
echo "   2. Edit .streamlit/secrets.toml with your credentials"
echo "   3. Set up Supabase database (see EXECUTION_PLAN.md)"
echo "   4. Run the app: streamlit run app.py"
echo ""
echo "📚 Documentation:"
echo "   - SETUP.md: Setup guide"
echo "   - EXECUTION_PLAN.md: Full implementation plan"
echo "   - PROJECT_STATUS.md: Current status"
echo "   - README.md: Project overview"
echo ""
echo "🚀 Ready to start Phase 2!"

