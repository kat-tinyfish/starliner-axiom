# 🚀 Streamlit Cloud Deployment Guide

## Prerequisites

- ✅ GitHub repository: https://github.com/kat-tinyfish/starliner-axiom
- ✅ Streamlit Cloud account (free): https://share.streamlit.io
- ✅ Supabase project with tables created
- ✅ Lambda function deployed (optional - app works without it)

---

## Step 1: Push Latest Code to GitHub

Make sure all your changes are committed and pushed:

```bash
cd /Users/kat.tinyfish/starliner/starliner-axiom
git status  # Check for uncommitted changes
git add .
git commit -m "Ready for deployment"
git push origin main
```

---

## Step 2: Deploy to Streamlit Cloud

### 2.1 Go to Streamlit Cloud

1. Navigate to: https://share.streamlit.io
2. Sign in with GitHub
3. Click **"New app"**

### 2.2 Configure App

**Repository:**
- Repository: `kat-tinyfish/starliner-axiom`
- Branch: `main`
- Main file path: `app.py`

**App URL** (optional):
- Choose a custom subdomain or use auto-generated

### 2.3 Advanced Settings

Click **"Advanced settings"** to add environment variables.

---

## Step 3: Add Environment Variables

Add these **Secrets** in Streamlit Cloud:

### Required Variables

```toml
# Supabase Configuration
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key-here"

# Agent API Keys (add the ones you have)
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "..."

# Optional - Lambda Backend (leave blank if not using yet)
AWS_LAMBDA_FUNCTION_URL = "https://your-function-url.lambda-url.us-east-1.on.aws/"
```

### How to Add Secrets

1. In Streamlit Cloud, go to your app settings
2. Click **"Secrets"** in the left sidebar
3. Paste the TOML format above with your actual values
4. Click **"Save"**

### Where to Find Your Values

**Supabase:**
- Go to: https://supabase.com/dashboard
- Select your project
- Settings → API
- Copy `URL` and `anon/public` key

**OpenAI:**
- Go to: https://platform.openai.com/api-keys
- Create new key

**Anthropic:**
- Go to: https://console.anthropic.com/settings/keys
- Create new key

**Google:**
- Go to: https://makersuite.google.com/app/apikey
- Create API key

**Lambda (Optional):**
- AWS Lambda Console → Your function → Function URL
- Copy the URL (format: `https://abc123.lambda-url.us-east-1.on.aws/`)

---

## Step 4: Deploy!

1. Click **"Deploy!"** button
2. Wait 2-5 minutes for deployment
3. Watch the build logs

**Expected output:**
```
✅ Supabase client initialized
✅ App deployed successfully
```

---

## Step 5: Test Your Deployment

### 5.1 Access Your App

Your app will be available at:
```
https://your-app-name.streamlit.app
```

### 5.2 Test Basic Functionality

1. ✅ **Arena Tab** - Should load without errors
2. ✅ **Dashboard Tab** - Should show leaderboard (empty if no data)
3. ✅ **Start Race** - Configure and start a race
4. ✅ **Voting** - Vote for an agent
5. ✅ **Database** - Check if votes appear in dashboard

### 5.3 Verify Database Connection

Go to **Dashboard** tab:
- Should see "Top Matchups" (empty initially)
- Should see "Agent Leaderboard" with 4 agents
- No error messages about database connection

---

## Troubleshooting

### "ModuleNotFoundError"
**Solution:** Make sure `requirements.txt` is in the root directory and contains all dependencies.

### "Supabase connection failed"
**Solution:** 
1. Check `SUPABASE_URL` and `SUPABASE_KEY` in Secrets
2. Make sure keys don't have extra spaces or quotes
3. Verify Supabase project is active

### "No API key found"
**Solution:**
1. Add the required API keys to Secrets
2. App will work for UI/database even without API keys
3. Agent execution requires API keys

### App is slow/timing out
**Solution:**
1. This is normal for first load (Streamlit Cloud warms up)
2. Subsequent loads will be faster
3. Consider upgrading to Streamlit Cloud paid tier for better performance

### Lambda connection fails
**Solution:**
1. Lambda is optional - app works without it
2. Check `AWS_LAMBDA_FUNCTION_URL` format (include `https://`)
3. Verify Lambda function has CORS enabled
4. Test Lambda separately in AWS Console first

---

## Post-Deployment

### Monitor Your App

1. **Logs:** Streamlit Cloud → Your App → Logs
2. **Analytics:** Streamlit Cloud → Your App → Analytics
3. **Resources:** Check memory/CPU usage

### Update Your App

When you push to GitHub, Streamlit Cloud auto-deploys:

```bash
git add .
git commit -m "Update feature X"
git push origin main
# Wait 1-2 minutes, app will auto-update
```

### Custom Domain (Optional)

1. Streamlit Cloud → Your App → Settings
2. Add custom domain (paid feature)
3. Follow DNS configuration instructions

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ Yes | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ Yes | Supabase anon/public key |
| `OPENAI_API_KEY` | ⚠️ Optional* | For GPT-4 agent execution |
| `ANTHROPIC_API_KEY` | ⚠️ Optional* | For Claude agent execution |
| `GOOGLE_API_KEY` | ⚠️ Optional* | For Gemini agent execution |
| `TINYFISH_API_KEY` | ❌ No | For TinyFish agent (if available) |
| `AWS_LAMBDA_FUNCTION_URL` | ❌ No | For live browser automation |

*Optional: App UI and database work without these. Only needed for actual agent execution.

---

## Success Checklist

Before sharing your app, verify:

- [ ] App loads without errors
- [ ] Dashboard shows agent leaderboard
- [ ] Can start a race (even if simulated)
- [ ] Can vote for agents
- [ ] Votes appear in dashboard
- [ ] No errors in Streamlit Cloud logs
- [ ] Database connection working

---

## Sharing Your App

Once deployed, share your app:

```
🌐 Live Demo: https://your-app-name.streamlit.app
📊 GitHub: https://github.com/kat-tinyfish/starliner-axiom
```

Post on:
- Twitter/X
- LinkedIn
- Hacker News
- Reddit (r/datascience, r/MachineLearning)

---

## Costs

**Streamlit Cloud:**
- Free tier: 1 app, community resources
- Enough for demo and testing
- Upgrade if needed for production

**Supabase:**
- Free tier: 500MB database, 2GB bandwidth/month
- Enough for thousands of races
- Upgrade only if you get popular

**Lambda:**
- Pay-per-use: ~$0.000016 per second
- Typical race: ~60 seconds = ~$0.001 per race
- Very cheap at low volume

**Total:** $0-5/month for development, scales as needed

---

## Next Steps After Deployment

1. **Test thoroughly** with real users
2. **Monitor usage** in Streamlit Cloud
3. **Add Lambda** if you want live browser streaming
4. **Scale database** if needed (Supabase metrics)
5. **Collect feedback** and iterate

---

## Need Help?

- **Streamlit Docs:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app
- **Supabase Docs:** https://supabase.com/docs
- **Your Logs:** Check Streamlit Cloud → App → Logs for errors

---

## 🎉 You're Done!

Your Web Agent Arena is now live and accessible to the world!

Share the link and start collecting agent comparison data! 🚀

