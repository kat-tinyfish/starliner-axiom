# 🔐 Streamlit Cloud Secrets Configuration

**IMPORTANT**: Your app is failing because BrowserBase credentials are missing!

---

## ⚠️ **Current Error:**

```
BrowserBase connection required.
Local Playwright not supported in cloud deployments.
Please configure BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID.
```

---

## ✅ **Required Secrets for Streamlit Cloud:**

### **Step 1: Go to Streamlit Cloud**
1. Open your app dashboard: https://share.streamlit.io
2. Find your app: `starliner-axiom`
3. Click "⚙️ Settings" → "Secrets"

### **Step 2: Copy This TOML Configuration**

Copy ALL of the following into the Secrets box:

```toml
# ============================================================================
# DATABASE (REQUIRED)
# ============================================================================
SUPABASE_URL = "https://opuyqbpugxhjhmouktcm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9wdXlxYnB1Z3hoamhtb3VrdGNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI5NzUwMDIsImV4cCI6MjA3ODU1MTAwMn0.Se2lCMt8wCINHAnyavx_nd5eM91GAulKs65_cN0evwo"

# ============================================================================
# BROWSERBASE (REQUIRED FOR BROWSER AUTOMATION)
# ============================================================================
# Without these, agents cannot run browser sessions!
BROWSERBASE_API_KEY = "bb_live_JUbLLjr2DDs3nmbRAbBlhxOj738"
BROWSERBASE_PROJECT_ID = "dd9360e0-adfa-4510-a01f-b1635d374be4"

# ============================================================================
# AGENT API KEYS (AT LEAST ONE REQUIRED)
# ============================================================================
# ⚠️ REPLACE WITH YOUR ACTUAL KEYS!

# OpenAI (for GPT-4 agent)
OPENAI_API_KEY = "sk-proj-YOUR_OPENAI_KEY_HERE"

# Anthropic (for Claude agent)
ANTHROPIC_API_KEY = "sk-ant-YOUR_ANTHROPIC_KEY_HERE"

# Google (for Gemini agent)
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"
```

### **Step 3: Save and Reboot**
1. Click "Save"
2. Click "Reboot app"
3. Wait ~2 minutes for deployment

---

## 📋 **What Each Secret Does:**

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `SUPABASE_URL` | Database connection | ✅ **YES** |
| `SUPABASE_KEY` | Database authentication | ✅ **YES** |
| `BROWSERBASE_API_KEY` | Browser automation access | ✅ **YES** |
| `BROWSERBASE_PROJECT_ID` | BrowserBase project | ✅ **YES** |
| `OPENAI_API_KEY` | GPT-4 agent | ⚠️ At least one |
| `ANTHROPIC_API_KEY` | Claude agent | ⚠️ At least one |
| `GOOGLE_API_KEY` | Gemini agent | ⚠️ At least one |

---

## 🔧 **Why BrowserBase is Required:**

Streamlit Cloud **cannot run local Playwright browsers** because:
- ❌ No browser binaries installed
- ❌ No permissions to install them
- ❌ Sandboxed environment

**Solution**: BrowserBase provides cloud browsers that work perfectly with Streamlit Cloud!

---

## ✅ **Verification:**

After adding secrets and rebooting, you should see:
```
✅ Supabase client initialized
✅ Using BrowserBase for browser execution
```

If you see:
```
❌ BrowserBase connection required
```

Then secrets weren't configured correctly - check the TOML format!

---

## 🆘 **Troubleshooting:**

### **Error: "BROWSERBASE_API_KEY is required"**
→ Make sure you copied the TOML exactly (including quotes!)

### **Error: "Failed to create BrowserBase session"**
→ Check that your BrowserBase API key is valid
→ Verify project ID is correct

### **Error: "OPENAI_API_KEY not found"**
→ You need at least ONE agent API key
→ Add OpenAI, Anthropic, or Google key

---

## 📖 **Where to Get Keys:**

### **BrowserBase** (Required)
1. Sign up: https://www.browserbase.com
2. Get API key from dashboard
3. Create project → Copy project ID

### **OpenAI** (Optional)
- https://platform.openai.com/api-keys

### **Anthropic** (Optional)
- https://console.anthropic.com/settings/keys

### **Google AI** (Optional)
- https://makersuite.google.com/app/apikey

---

## 🚀 **After Configuration:**

Your app will:
1. ✅ Connect to Supabase database
2. ✅ Create BrowserBase sessions
3. ✅ Run agents with native tool calling
4. ✅ Display live browser screenshots
5. ✅ Track leaderboard data

---

**Copy the secrets above, paste into Streamlit Cloud, save, and reboot!** 🎉

