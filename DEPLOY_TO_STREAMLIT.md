# 🚀 Deploy to Streamlit Cloud - Quick Guide

Last Updated: 2025-11-13

## ✅ Pre-Deployment Checklist

- [x] All code committed to GitHub
- [x] BrowserBase integration working locally
- [x] Database connected (Supabase)
- [x] Secrets prepared

---

## 🎯 Deployment Steps

### **Step 1: Go to Streamlit Cloud**

1. Visit: https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click **"New app"**

---

### **Step 2: Connect Repository**

1. **Repository**: `kat-tinyfish/starliner-axiom`
2. **Branch**: `main`
3. **Main file path**: `app.py`
4. Click **"Advanced settings"** (before deploying)

---

### **Step 3: Configure Secrets**

In the **Secrets** text box, paste your secrets in TOML format:

```toml
# =============================================================================
# REQUIRED - Supabase Database
# =============================================================================
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key-here"

# =============================================================================
# REQUIRED - BrowserBase (for live browser sessions)
# =============================================================================
BROWSERBASE_API_KEY = "bb_live_xxxxxxxx"
BROWSERBASE_PROJECT_ID = "proj_xxxxxxxx"

# =============================================================================
# REQUIRED - Agent API Keys (at least one)
# =============================================================================
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "..."

# =============================================================================
# OPTIONAL
# =============================================================================
# TINYFISH_API_KEY = "..."
# AWS_LAMBDA_FUNCTION_URL = "https://..."  # Only if using Lambda
```

**👉 Replace with YOUR actual values from `.env` file!**

---

### **Step 4: Deploy!**

1. Click **"Deploy!"**
2. Wait 2-3 minutes for deployment
3. Your app will be live at: `https://[app-name].streamlit.app`

---

## 🧪 Testing Your Deployment

Once deployed, test these features:

1. **Arena Tab**:
   - Enter a task: "Go to example.com"
   - Select two agents
   - Click "Start Race"
   - **Watch for**: Screenshots updating every 2 seconds
   - **Vote** for a winner

2. **Dashboard Tab**:
   - Check leaderboard populates after voting
   - Verify win rates update
   - Check performance charts

---

## 🔍 Troubleshooting

### **App won't start**
- Check logs in Streamlit Cloud console
- Verify all required secrets are set
- Make sure secret names match exactly (case-sensitive)

### **"BROWSERBASE_API_KEY is required" error**
- Go to App Settings → Secrets
- Add BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID
- Restart app

### **"No module named X" error**
- Check `requirements.txt` is in repo root
- Verify all dependencies are listed
- Restart app

### **Database connection fails**
- Verify SUPABASE_URL and SUPABASE_KEY are correct
- Check Supabase project is active
- Verify tables exist (run schema.sql if needed)

### **Agents not executing**
- Check API keys are valid and have credits
- Verify at least one agent API key is configured
- Check BrowserBase has available session time

---

## 📊 What Works in Deployed Version

✅ **Full Feature Set:**
- Real-time agent races with live tool calls
- Browser screenshots (via BrowserBase)
- Progress tracking with checkpoints
- Voting system
- Leaderboard with statistics
- Dashboard analytics
- Database persistence

✅ **4 Agents Available:**
- GPT-4 Web Agent (OpenAI)
- Claude 3.5 Sonnet Agent (Anthropic)
- Gemini 2.0 Agent (Google)
- TinyFish Agent (if configured)

✅ **Performance:**
- ~6-10 second race execution
- 2-second screenshot refresh
- Responsive UI with auto-refresh

---

## 🎉 Post-Deployment

**Share your app:**
- URL will be: `https://[your-app-name].streamlit.app`
- Share with testers
- Monitor usage in Streamlit Cloud dashboard

**Monitor costs:**
- BrowserBase: Free tier = 1 hour/month
- Upgrade to Developer tier ($49/mo) for more usage
- Supabase: Free tier = 500MB database + 2GB bandwidth

**Next steps:**
- Gather user feedback
- Monitor error logs
- Track which agents perform best
- Consider adding more agents or features

---

## 📞 Support

**If deployment fails:**
1. Check Streamlit Cloud logs (click "Manage app" → "Logs")
2. Verify all secrets are configured
3. Test locally first: `streamlit run app.py`
4. Check GitHub repo is public or Streamlit has access

**Common issues:**
- Missing secrets → Add in App Settings
- Wrong Python version → Streamlit Cloud uses Python 3.9+
- Missing dependencies → Check requirements.txt

---

**Ready to deploy? Let's go! 🚀**

