# Setup Guide for Web Agent Arena (Conda Environment: axiom)

This guide will help you set up the Web Agent Arena project in your conda environment named `axiom`.

## Prerequisites

- Conda installed (Miniconda or Anaconda)
- Python 3.11+
- Git
- Active conda environment named `axiom`

## Setup Steps

### 1. Activate Conda Environment

```bash
conda activate axiom
```

### 2. Install Dependencies

You have two options:

#### Option A: Using environment.yml (Recommended for fresh setup)

```bash
# Update the conda environment with all dependencies
conda env update -f environment.yml --prune
```

#### Option B: Using pip requirements.txt (If environment already exists)

```bash
# Make sure axiom environment is activated
conda activate axiom

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Playwright Browsers

```bash
# Install Chromium browser for Playwright
playwright install chromium
```

### 4. Set Up Environment Variables

#### For Local Development:

Create a `.env` file in the project root:

```bash
cp .env.template .env
```

Edit `.env` and add your API keys and configuration.

#### For Streamlit Deployment:

Create `.streamlit/secrets.toml`:

```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Edit `secrets.toml` and add your credentials.

### 5. Verify Installation

```bash
# Test that all imports work
python -c "import streamlit; import playwright; import supabase; print('✅ All dependencies installed successfully!')"
```

### 6. Run the Application

```bash
# Start the Streamlit app
streamlit run app.py
```

The app should open in your browser at `http://localhost:8501`

## Configuration Checklist

Before running the app, ensure you have:

- [ ] Supabase project created at [supabase.com](https://supabase.com)
- [ ] Database tables created (see `database/models.py`)
- [ ] Supabase credentials in `.env` or `secrets.toml`
- [ ] API keys for agents (OpenAI, Anthropic, Google, TinyFish)
- [ ] AWS Lambda function deployed (optional for MVP, can use placeholder)

## Common Issues

### Issue: `playwright` command not found

**Solution**: Make sure playwright is installed and run:
```bash
python -m playwright install chromium
```

### Issue: Database connection failed

**Solution**: 
1. Check Supabase credentials in `.env`
2. Verify Supabase project is active
3. Run database migrations

### Issue: Import errors

**Solution**: Reinstall dependencies:
```bash
conda activate axiom
pip install -r requirements.txt --force-reinstall
```

### Issue: Streamlit not starting

**Solution**: Check that port 8501 is not in use:
```bash
lsof -i :8501  # On macOS/Linux
# Kill the process if needed
```

## Development Workflow

1. **Start development server**:
   ```bash
   conda activate axiom
   streamlit run app.py
   ```

2. **The app will auto-reload when you save changes to Python files**

3. **Check logs in terminal for errors**

4. **Test changes before committing**

## Next Steps

After setup, refer to `EXECUTION_PLAN.md` for:
- Phase 2: Agent integration
- Phase 3: UI development
- Phase 4: Database setup
- Phase 5: AWS Lambda deployment
- Phase 6: Testing and deployment

## Updating Dependencies

When new dependencies are added:

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Or update specific package
pip install --upgrade package-name
```

## Troubleshooting

For issues, check:
1. Console output in terminal
2. Browser console (F12 → Console tab)
3. Streamlit logs
4. Database connection status

## Support

- Check `EXECUTION_PLAN.md` for architecture details
- Review `README.md` for project overview
- See individual module READMEs for specific components

