# BrowserBase Setup Guide

BrowserBase replaces our Lambda/Playwright setup with a managed browser infrastructure that "just works." This guide will get you set up in ~5 minutes.

## Why BrowserBase?

✅ **Works immediately** - No browser compatibility issues  
✅ **Free tier** - 1 hour/month, perfect for testing  
✅ **Production ready** - Used by Vercel, Chronicle, and other companies  
✅ **Scales** - From free to enterprise without code changes  
✅ **Features** - Stealth mode, proxies, captcha solving (paid tiers)

## Step 1: Sign Up (2 minutes)

1. Go to https://www.browserbase.com/sign-up
2. Fill out the sign-up form:
   - First name
   - Last name
   - Email
   - Phone number
   - Organization name
   - Password
3. Click **Continue**
4. Verify your email (check inbox)

## Step 2: Get API Credentials (2 minutes)

1. Log in to https://www.browserbase.com/sign-in
2. Navigate to **Settings** → **API Keys**
3. Click **Create API Key**
4. Copy the API key (save it - you won't see it again!)
5. Navigate to **Projects**
6. Copy your **Project ID** (looks like `proj_...`)

## Step 3: Add to Environment Variables (1 minute)

### For Local Development

Add to `.env`:

```bash
# BrowserBase Configuration (Free Tier)
BROWSERBASE_API_KEY=bb_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BROWSERBASE_PROJECT_ID=proj_xxxxxxxxxxxxxxxx
```

### For Streamlit Cloud

Add to your secrets (Settings → Secrets):

```toml
[default]
# ... existing secrets ...

# BrowserBase
BROWSERBASE_API_KEY = "bb_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
BROWSERBASE_PROJECT_ID = "proj_xxxxxxxxxxxxxxxx"
```

### For AWS Lambda (if still using)

Add environment variables:

```bash
aws lambda update-function-configuration \
  --function-name web-agent-executor \
  --environment "Variables={
    BROWSERBASE_API_KEY=bb_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx,
    BROWSERBASE_PROJECT_ID=proj_xxxxxxxxxxxxxxxx
  }" \
  --region us-east-1
```

## Step 4: Test the Integration (1 minute)

```bash
# Test locally
cd /path/to/starliner-axiom
python lambda/browserbase_client.py
```

You should see:

```
🧪 Testing BrowserBase integration...

✅ Success: True
📸 Screenshots: 2-3
⏱️  Execution time: 5-6s
🚩 Checkpoints: 4
```

## Free Tier Limits

✅ **1 browser hour** per month  
✅ **1 concurrent browser**  
✅ **15 minutes per session**  
✅ **5 sessions per minute**  
✅ **7 day data retention**

**That's enough for:**
- ~100 test runs (5 minutes each)
- Building and demoing the UI
- Initial user testing
- Proof of concept

## Upgrade When Ready

When you need more:

### Developer - $20/month
- 100 browser hours (~2,000 test runs)
- 25 concurrent browsers
- Stealth mode + captcha solving
- Great for production MVP

### Startup - $99/month
- 500 browser hours (~10,000 runs)
- 100 concurrent browsers
- 30 day retention
- Priority support

## API Documentation

- **Docs**: https://docs.browserbase.com/
- **API Reference**: https://docs.browserbase.com/reference/introduction
- **SDKs**: Python, JavaScript, Go
- **Integrations**: Playwright, Puppeteer, Selenium

## Next Steps

1. ✅ Sign up and get credentials
2. ✅ Add to `.env` and Streamlit secrets
3. ✅ Test with `python lambda/browserbase_client.py`
4. 🔄 Update Lambda handler to use BrowserBase (optional)
5. 🚀 Deploy and test live browser streaming!

## Troubleshooting

### "BROWSERBASE_API_KEY is required"

Make sure your `.env` file has the key set correctly:

```bash
BROWSERBASE_API_KEY=bb_live_...
```

(No quotes, no spaces)

### "Failed to create session: 401"

Your API key is invalid. Get a new one from Settings → API Keys.

### "Failed to create session: 402"

You've exceeded your free tier limit. Either:
- Wait until next month
- Upgrade to Developer tier ($20/month)

### "Session timeout"

Free tier sessions max out at 15 minutes. Make sure your tasks complete within this window or upgrade to Developer tier (6 hour sessions).

## Support

- **Status**: https://status.browserbase.com
- **Email**: support@browserbase.com (Free tier gets email support)
- **Discord**: Ask the community (link in docs)

---

**🎉 That's it! You're ready to build with BrowserBase.**

The browser infrastructure "just works" so you can focus on building your agent arena.

