# 🚀 AWS Lambda Setup - START HERE

This guide will help you deploy your Web Agent Executor Lambda function in **~10 minutes**.

## 📍 You Are Here

```
Project Structure:
├── app.py                    ✅ Streamlit app (done)
├── components/               ✅ UI components (done)
├── database/                 ✅ Supabase integration (done)
├── agents/                   ✅ Agent implementations (done)
└── lambda/                   ⬅️ YOU ARE HERE
    ├── handler.py            ✅ Lambda entry point (ready)
    ├── agent_executor.py     ✅ Browser automation (ready)
    ├── function.zip          ✅ Deployment package (ready)
    └── 📖 Setup guides       ⬅️ READ THESE
```

---

## 🎯 What You're Setting Up

**AWS Lambda Function** that:
- Receives agent execution requests from your Streamlit app
- Runs Playwright browser automation
- Calls LLM APIs (OpenAI, Anthropic, Google, TinyFish)
- Returns results back to your app

**Why Lambda?**
- ✅ Serverless (no servers to manage)
- ✅ Auto-scales
- ✅ Pay per use
- ✅ Always available

---

## 📚 Choose Your Path

### Option 1: AWS Console (Recommended for First Time) ⭐

**Best for**: Beginners, visual learners, first-time setup

**Time**: 10 minutes

**Steps**:
1. ✅ Read: [`LAMBDA_CHECKLIST.md`](./LAMBDA_CHECKLIST.md) - Quick checklist
2. 📖 Follow: [`AWS_CONSOLE_SETUP.md`](./AWS_CONSOLE_SETUP.md) - Detailed guide
3. ✅ Result: Working Lambda function with public URL

### Option 2: AWS CLI (For Developers)

**Best for**: Terminal users, automated deployments, CI/CD

**Time**: 5 minutes (if AWS CLI configured)

**Steps**:
1. Configure AWS CLI: `aws configure`
2. Run: `./deploy.sh`
3. ✅ Result: Deployed function with Function URL

### Option 3: Docker (Advanced - Full Browser Support)

**Best for**: Production, VNC streaming, complex browser tasks

**Time**: 15 minutes

**Steps**:
1. 📖 Read: [`deploy_docker.sh`](./deploy_docker.sh)
2. Build and deploy Docker container
3. ✅ Result: Full Chromium browser support

---

## ⚡ Quick Start (10 Minutes)

Follow these steps to get Lambda running:

### Step 1: Prepare (1 min)

You already have `function.zip` ready! ✅

Location: `/Users/kat.tinyfish/starliner/starliner-axiom/lambda/function.zip`

### Step 2: AWS Console Setup (8 min)

Open the checklist and follow along:

**👉 [`LAMBDA_CHECKLIST.md`](./LAMBDA_CHECKLIST.md) 👈**

The checklist has:
- ✅ Exact settings to use
- ✅ Screenshots of what to click
- ✅ Test commands
- ✅ Troubleshooting tips

### Step 3: Get Your Function URL (1 min)

After creating the function, you'll get a URL like:

```
https://abc123xyz.lambda-url.us-east-1.on.aws/
```

**Save this URL!** You'll need it for Streamlit.

---

## 🔑 What You Need

### Required

- [ ] **AWS Account** (free tier is fine)
- [ ] **OpenAI API Key** (for GPT-4 agent)
  - Get it: https://platform.openai.com/api-keys

### Optional (for other agents)

- [ ] **Anthropic API Key** (for Claude)
- [ ] **Google API Key** (for Gemini)
- [ ] **TinyFish API Key** (for TinyFish agent)

**For MVP**: Just OpenAI is enough!

---

## 📋 Setup Checklist

### Pre-Setup
- [ ] AWS account created
- [ ] At least OpenAI API key ready
- [ ] Located `function.zip` in lambda directory

### AWS Console Steps
- [ ] Create Lambda function
- [ ] Upload function.zip
- [ ] Set memory to 2048 MB
- [ ] Set timeout to 5 minutes
- [ ] Add environment variables
- [ ] Enable Function URL
- [ ] Test with health check

### Integration
- [ ] Copy Function URL
- [ ] Add URL to `.env` file
- [ ] Test from Streamlit app

---

## 🧪 Test Your Lambda

### Test 1: Health Check

Use curl or any HTTP client:

```bash
curl -X POST "YOUR_FUNCTION_URL_HERE" \
  -H "Content-Type: application/json" \
  -d '{"action":"health_check"}'
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Lambda function is running",
  "playwright_available": true
}
```

### Test 2: Agent Execution

```bash
curl -X POST "YOUR_FUNCTION_URL_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "execute",
    "agent_config": {
      "agent_id": "gpt4-agent",
      "name": "GPT-4 Web Agent",
      "api_provider": "openai",
      "model": "gpt-4-turbo"
    },
    "prompt": "Go to https://example.com",
    "constraints": {}
  }'
```

---

## 🔗 Connect to Streamlit

After Lambda is set up, update your `.env`:

```bash
# Add this line
AWS_LAMBDA_FUNCTION_URL=https://your-function-url-here.lambda-url.us-east-1.on.aws/
```

Then your Streamlit app can call Lambda!

---

## 📖 Documentation Quick Links

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [`START_HERE.md`](./START_HERE.md) | Overview & guidance | **You are here!** |
| [`LAMBDA_CHECKLIST.md`](./LAMBDA_CHECKLIST.md) | Quick setup steps | **Use this to set up** |
| [`AWS_CONSOLE_SETUP.md`](./AWS_CONSOLE_SETUP.md) | Detailed console guide | Need more details |
| [`README.md`](./README.md) | Lambda code overview | Understanding the code |
| [`deploy.sh`](./deploy.sh) | CLI deployment | Automated setup |
| [`AWS_SETUP_GUIDE.md`](./AWS_SETUP_GUIDE.md) | Advanced AWS config | Production setup |

---

## ❓ FAQ

### Do I need a credit card for AWS?

Yes, but Lambda has a generous free tier:
- **1M free requests/month**
- **400,000 GB-seconds of compute**

For development/testing, you'll likely stay in free tier.

### What if I don't have all API keys?

Start with just OpenAI! You can add others later. Just set:
```
OPENAI_API_KEY=sk-...
```

### Can I use this in production?

Yes! For production:
1. Enable IAM authentication (instead of NONE)
2. Set up API Gateway
3. Use proper CORS settings
4. Add monitoring/alerts

See [`AWS_SETUP_GUIDE.md`](./AWS_SETUP_GUIDE.md) for production setup.

### What about VNC streaming?

For MVP, Lambda runs browsers in headless mode (no visual).
For VNC streaming, you'll need EC2 or Docker deployment.

See [`deploy_docker.sh`](./deploy_docker.sh) for VNC-enabled setup.

---

## 🎯 Success Criteria

You're done when:

- ✅ Lambda function shows "Active" in AWS Console
- ✅ Health check returns `{"status": "healthy"}`
- ✅ Function URL is in your `.env` file
- ✅ Test execution completes without errors

---

## 🚨 Troubleshooting

### "Unable to import module 'handler'"

**Fix**: Verify zip structure:
```bash
unzip -l function.zip
# Should show handler.py and agent_executor.py at root
```

### "Task timed out"

**Fix**: Increase timeout:
- AWS Console → Configuration → General → Timeout → 5 min

### "No module named 'playwright'"

**Expected for MVP**: Full Playwright needs a layer (optional for now)

### Function URL returns 403

**Fix**: Check CORS settings in Function URL configuration

---

## 💬 Need Help?

1. Check [`AWS_CONSOLE_SETUP.md`](./AWS_CONSOLE_SETUP.md) for detailed steps
2. Look at CloudWatch Logs in AWS Console
3. Review error messages carefully
4. Test with health check first before complex requests

---

## 🎉 Next Steps

After Lambda is working:

1. ✅ Test health check endpoint
2. ✅ Test with a simple agent execution
3. ✅ Connect to Streamlit app
4. ✅ Run an end-to-end race
5. 🚀 Deploy to Streamlit Cloud!

---

## 📞 Summary

**Goal**: Deploy Lambda function for agent execution

**Time**: ~10 minutes

**Action**: Open [`LAMBDA_CHECKLIST.md`](./LAMBDA_CHECKLIST.md) and follow the steps!

**Result**: Working Lambda function accessible from your Streamlit app

---

**Ready? Let's do this! 👉 [`LAMBDA_CHECKLIST.md`](./LAMBDA_CHECKLIST.md)**

