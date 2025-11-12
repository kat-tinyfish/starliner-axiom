# AWS Lambda - Quick Start Guide

**Goal:** Deploy your Web Agent Executor to AWS Lambda in under 10 minutes.

---

## 🚀 One-Command Deploy

```bash
cd lambda
./deploy.sh
```

That's it! The script handles everything automatically.

---

## ✅ What You'll Get

After deployment:
- ✅ AWS Lambda function with Playwright
- ✅ Public HTTPS endpoint (Function URL)
- ✅ Browser automation capabilities
- ✅ API keys configured from .env
- ✅ 2GB memory, 5-minute timeout
- ✅ CloudWatch logging enabled

---

## 📋 Prerequisites (5 minutes)

### 1. AWS Account
Sign up at [aws.amazon.com](https://aws.amazon.com) if you don't have one.

### 2. Install AWS CLI

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
Download from: https://aws.amazon.com/cli/

### 3. Configure AWS

```bash
aws configure
```

Enter:
- **AWS Access Key ID**: From AWS Console → IAM
- **AWS Secret Access Key**: From AWS Console → IAM
- **Default region**: `us-east-1` (recommended)
- **Default output**: `json`

**Don't have access keys?** Create them:
1. Go to AWS Console → IAM → Users → Your user
2. Security credentials → Create access key
3. Choose "CLI" usage
4. Copy the keys

---

## 🚀 Deploy Steps

### Step 1: Navigate to Lambda Directory

```bash
cd /Users/kat.tinyfish/starliner/starliner-axiom/lambda
```

### Step 2: Run Deployment Script

```bash
./deploy.sh
```

**What it does:**
1. Creates Playwright Lambda layer (~2 minutes)
2. Packages your function code
3. Creates Lambda function
4. Sets up public URL
5. Configures API keys from .env

**Expected output:**
```
╔══════════════════════════════════════════════════════════════╗
║  ✅ Deployment Complete!                                     ║
╚══════════════════════════════════════════════════════════════╝

Function URL:
  https://abc123.lambda-url.us-east-1.on.aws/

Update your .env file with:
  AWS_LAMBDA_FUNCTION_URL=https://abc123.lambda-url.us-east-1.on.aws/
```

### Step 3: Save Function URL

Copy the Function URL and add it to your `.env` file:

```bash
# Edit .env
nano ../.env

# Add this line:
AWS_LAMBDA_FUNCTION_URL=https://your-url-here.lambda-url.us-east-1.on.aws/
```

---

## 🧪 Test Your Function

### Quick Test

```bash
./test_lambda.sh https://your-url-here.lambda-url.us-east-1.on.aws/
```

### Manual Test

```bash
curl -X POST https://your-url-here.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"action": "health_check"}'
```

**Expected response:**
```json
{
  "status": "healthy",
  "message": "Lambda function is running",
  "playwright_available": true
}
```

✅ **If you see this, you're done!**

---

## 💰 Cost

**With AWS Free Tier:**
- First 1 million requests: FREE
- First 400,000 GB-seconds: FREE

**After free tier:**
- ~$0.001 per race (2GB, 30s)
- 1,000 races/month = ~$1
- 10,000 races/month = ~$10

For testing/development, you'll likely stay within free tier.

---

## 🔄 Update Function

Made changes to `handler.py` or `agent_executor.py`?

```bash
./deploy.sh  # Re-run deployment (much faster, ~30 seconds)
```

---

## 🐛 Common Issues

### "AWS CLI not found"
```bash
# Install AWS CLI first
brew install awscli  # macOS
```

### "Credentials not configured"
```bash
aws configure
```

### "Permission denied: ./deploy.sh"
```bash
chmod +x deploy.sh
./deploy.sh
```

### "Role already exists" error
This is fine - the script will use the existing role.

### Function takes > 60 seconds
This is normal for first execution (cold start). Subsequent calls are faster.

---

## 📚 Next Steps

1. ✅ **Test in Arena**: Your Streamlit app can now use Lambda for browser automation
2. ✅ **Monitor**: Check CloudWatch Logs for execution details
3. ✅ **Scale**: Lambda auto-scales with demand
4. ✅ **Optimize**: Adjust memory/timeout based on actual usage

---

## 🎯 Using in Your App

Update your agent code to use Lambda:

```python
import requests

def execute_via_lambda(prompt, agent_config):
    lambda_url = os.getenv("AWS_LAMBDA_FUNCTION_URL")
    
    response = requests.post(lambda_url, json={
        "action": "execute",
        "agent_config": agent_config,
        "prompt": prompt,
        "constraints": {}
    })
    
    return response.json()
```

---

## 📖 More Information

- **Detailed Setup**: See `AWS_SETUP_GUIDE.md`
- **Manual Deployment**: See `README.md`
- **Troubleshooting**: See `AWS_SETUP_GUIDE.md` → Troubleshooting

---

## ✅ Deployment Checklist

- [ ] AWS CLI installed
- [ ] AWS credentials configured
- [ ] Ran `./deploy.sh`
- [ ] Got Function URL
- [ ] Updated `.env` with URL
- [ ] Tested with `./test_lambda.sh`
- [ ] Health check returns "healthy"

**All checked?** You're ready to go! 🎉

---

**Need help?** See `AWS_SETUP_GUIDE.md` for detailed troubleshooting.

