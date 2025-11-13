# Lambda Playwright Fix Guide

## Problem

Lambda function crashes because it tries to import Playwright, which isn't installed yet.

```
ERROR: Unable to import module 'handler': No module named 'playwright'
```

## Solution

Replace `handler.py` in AWS Lambda Console with the fixed version that handles missing Playwright gracefully.

---

## Option 1: Edit in AWS Console (Quickest)

### Step 1: Open Lambda Function

1. Go to AWS Lambda Console
2. Click on your function: `web-agent-executor`
3. Go to the **Code** tab

### Step 2: Copy Fixed Code

The fixed code is in: `lambda/handler_fixed.py`

**Key improvements:**
- ✅ Checks if Playwright is available before importing
- ✅ Health check works without Playwright
- ✅ Returns helpful error messages
- ✅ Shows what's available vs what's missing

### Step 3: Replace handler.py

1. In AWS Console, click on `handler.py` in the file tree (left side)
2. **Select all** the existing code (Cmd+A / Ctrl+A)
3. **Delete it**
4. **Copy the entire contents** of `lambda/handler_fixed.py`
5. **Paste** into the AWS editor
6. Click **Deploy** (orange button at top)

### Step 4: Test Health Check

1. Go to **Test** tab
2. Use your existing `health-check` test event
3. Click **Test**

**Expected Response:**
```json
{
  "statusCode": 200,
  "body": {
    "status": "healthy",
    "message": "Lambda function is running",
    "playwright_available": false,
    "agent_executor_available": true/false,
    "python_version": "3.11...",
    "environment": "aws_lambda"
  }
}
```

✅ **Success!** `playwright_available: false` is expected and OK for MVP.

---

## Option 2: Upload New Package

If you prefer to upload a new ZIP:

```bash
cd /Users/kat.tinyfish/starliner/starliner-axiom/lambda

# Copy fixed version
cp handler_fixed.py handler.py

# Create new package
zip -r function.zip handler.py agent_executor.py

# Upload in AWS Console:
# Code tab → Upload from → .zip file → Select function.zip
```

---

## What This Fixes

### Before (Broken):
```python
from agent_executor import AgentExecutor  # ❌ This imports playwright immediately
```

Lambda crashes on startup because agent_executor.py imports playwright.

### After (Fixed):
```python
# Check Playwright first
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Playwright not available...")

# Conditional import
try:
    from agent_executor import AgentExecutor
    AGENT_EXECUTOR_AVAILABLE = True
except ImportError:
    AgentExecutor = None
```

Lambda starts successfully and tells you what's missing.

---

## Understanding the Response

### Health Check Response Fields:

| Field | Meaning |
|-------|---------|
| `playwright_available: false` | Playwright not installed (expected for now) |
| `agent_executor_available: true` | Agent executor code loaded OK |
| `agent_executor_available: false` | Agent executor also failed (probably due to playwright import) |
| `python_version` | Shows Python 3.11.x |
| `environment: "aws_lambda"` | Confirms running in Lambda |

### What You Want to See:
```json
{
  "status": "healthy",
  "playwright_available": false,  ← OK for MVP
  "agent_executor_available": false,  ← Expected (agent_executor needs playwright)
}
```

This means Lambda is working, just missing browser support (which is fine for testing the infrastructure).

---

## Next Steps After This Fix

### Immediate (Health Check Works):
1. ✅ Lambda responds to health checks
2. ✅ Function URL works
3. ✅ Can test Lambda is deployed correctly
4. ✅ Others can verify deployment

### Later (For Browser Automation):
1. Add Playwright Lambda layer
2. Test browser execution
3. Connect to Streamlit

---

## For Streamlit Integration

Once health check works, you can connect Streamlit:

**Add to `.env`:**
```bash
AWS_LAMBDA_FUNCTION_URL=https://your-function-url.lambda-url.us-east-1.on.aws/
```

**In Streamlit, check Lambda status:**
```python
import requests
import os

lambda_url = os.getenv("AWS_LAMBDA_FUNCTION_URL")
response = requests.post(lambda_url, json={"action": "health_check"})
status = response.json()

if status["status"] == "healthy":
    st.success("✅ Lambda is connected!")
    if not status["playwright_available"]:
        st.warning("⚠️ Playwright not available yet (browser automation disabled)")
```

---

## Troubleshooting

### Still getting import errors?

1. **Check handler setting**: Should be `handler.lambda_handler`
2. **Check you clicked Deploy**: Orange button after editing
3. **Check file structure**: `handler.py` should be at root of ZIP
4. **Try the test locally**:
   ```bash
   cd lambda/
   python handler_fixed.py
   ```

### Health check passes but execute fails?

That's expected! Execute needs Playwright. The fix allows health checks to work so you can:
- ✅ Verify Lambda deployment
- ✅ Test Function URL
- ✅ Connect Streamlit
- ⏸️ Add Playwright layer later for browser automation

---

## Summary

**Quick Fix:**
1. Copy `handler_fixed.py` content
2. Paste into AWS Console `handler.py`
3. Click Deploy
4. Test health check → Should pass!

**Result:**
- ✅ Lambda works without Playwright
- ✅ Health check returns useful status
- ✅ Ready for others to test
- ⏸️ Browser automation waits for Playwright layer

---

**This gets you to a deployable state!** Health check working = Lambda is correctly deployed and accessible.

