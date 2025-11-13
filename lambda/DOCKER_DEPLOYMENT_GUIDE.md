# Docker-Based Lambda Deployment Guide

## Full Playwright + Chromium Support

This guide will help you deploy your Lambda function with full Playwright and Chromium browser support using Docker containers.

---

## Why Docker Lambda?

✅ **Full browser support** - Includes complete Chromium binary  
✅ **No size limits** - Container images can be larger than zip files  
✅ **Production ready** - Most reliable approach for browser automation  
✅ **Easy updates** - Just rebuild and redeploy the image  

---

## Prerequisites

### 1. Docker Installed ✅
You have: Docker version 28.2.2

### 2. AWS CLI Configured ⏸️
**You need to do this first:**

```bash
aws configure
```

When prompted, enter:
- **AWS Access Key ID**: Get from AWS Console → Security credentials
- **AWS Secret Access Key**: Get from AWS Console → Security credentials  
- **Default region**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

**How to get Access Keys:**
1. AWS Console → Click your name (top right) → Security credentials
2. Scroll to "Access keys" → Click "Create access key"
3. Purpose: "Command Line Interface (CLI)"
4. Copy both keys

---

## Deployment Steps

### Step 1: Navigate to Lambda Directory

```bash
cd /Users/kat.tinyfish/starliner/starliner-axiom/lambda
```

### Step 2: Create Dockerfile

The `deploy_docker.sh` script will create this automatically, or create manually:

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for Playwright/Chromium
RUN yum install -y \
    atk cups-libs gtk3 libXcomposite libXcursor \
    libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango xdg-utils wget \
    && yum clean all

# Copy function code
COPY handler.py agent_executor.py ${LAMBDA_TASK_ROOT}/

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Install Playwright and Chromium browser
RUN pip install playwright --target "${LAMBDA_TASK_ROOT}"
RUN python -m playwright install chromium

# Set handler
CMD [ "handler.lambda_handler" ]
```

### Step 3: Run Deployment Script

```bash
chmod +x deploy_docker.sh
./deploy_docker.sh
```

**What this does:**
1. Creates Dockerfile
2. Creates AWS ECR repository (container registry)
3. Builds Docker image with Playwright + Chromium
4. Pushes image to ECR
5. Deletes old Lambda function (if exists)
6. Creates new Lambda function from container image
7. Configures memory (3GB), timeout (5 min)
8. Creates Function URL for public access

**Expected output:**
```
✅ Docker image built
✅ Image pushed to ECR
✅ Lambda function created
✅ Function URL: https://xxxxx.lambda-url.us-east-1.on.aws/
```

### Step 4: Add Environment Variables

The script creates the function, but you need to add API keys:

```bash
aws lambda update-function-configuration \
  --function-name web-agent-executor \
  --environment Variables="{
    OPENAI_API_KEY=sk-your-key-here,
    ANTHROPIC_API_KEY=sk-ant-your-key-here,
    GOOGLE_API_KEY=your-key-here,
    TINYFISH_API_KEY=your-key-here
  }"
```

Or add them manually in AWS Console:
1. Lambda Console → web-agent-executor → Configuration → Environment variables
2. Click Edit → Add environment variable for each API key

### Step 5: Test the Function

```bash
# Health check
curl -X POST "YOUR_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{"action":"health_check"}'

# Expected response:
# {
#   "statusCode": 200,
#   "body": "{\"status\":\"healthy\",\"playwright_available\":true}"
# }
```

### Step 6: Test Agent Execution

```bash
curl -X POST "YOUR_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "execute",
    "agent_config": {
      "agent_id": "gpt4-agent",
      "name": "GPT-4 Web Agent",
      "api_provider": "openai",
      "model": "gpt-4-turbo"
    },
    "prompt": "Go to https://example.com and get the page title",
    "constraints": {}
  }'
```

---

## What Happens Behind the Scenes

### 1. Docker Build Process
- Starts with AWS Lambda Python 3.11 base image
- Installs Linux packages needed for Chromium
- Copies your Lambda function code
- Installs Python dependencies (Playwright, OpenAI, etc.)
- Downloads and installs full Chromium browser (~200MB)
- Creates container image (~500MB total)

### 2. ECR (Elastic Container Registry)
- AWS's Docker registry service
- Stores your container image
- Lambda pulls image from ECR when executing

### 3. Lambda Container Execution
- Lambda runs your container on demand
- Full Chromium browser available
- Playwright can control browser
- Real browser automation (not simulated!)

---

## Advantages vs Zip Deployment

| Feature | Zip (Current) | Docker (New) |
|---------|---------------|--------------|
| Max size | 50 MB (250 MB unzipped) | 10 GB |
| Browser support | ❌ (requires layer) | ✅ Full Chromium |
| Setup complexity | Easy | Moderate |
| Update process | Upload zip | Rebuild image |
| Production ready | Limited | ✅ Full |

---

## Configuration Details

### Lambda Function Settings

After deployment, your function will have:

| Setting | Value | Purpose |
|---------|-------|---------|
| Runtime | Container image | Docker-based |
| Memory | 3008 MB (3 GB) | Chromium needs RAM |
| Timeout | 300 seconds (5 min) | Agent execution time |
| Storage | 512 MB | Default ephemeral storage |

### Function URL

The deployment script automatically creates a public Function URL with:
- **Auth**: NONE (public access for testing)
- **CORS**: Enabled for Streamlit app
- **Allowed methods**: POST
- **Allowed origins**: * (all origins)

⚠️ **Production Note**: For production, change auth to AWS_IAM and restrict origins.

---

## Troubleshooting

### Issue: "Error: No basic auth credentials"

**Solution**: Your AWS CLI credentials expired or are incorrect. Run:
```bash
aws configure
```

### Issue: "Docker daemon not running"

**Solution**: Start Docker Desktop application.

### Issue: "ECR repository already exists"

**Solution**: This is fine! The script continues with the existing repository.

### Issue: "Function already exists"

**Solution**: The script will delete and recreate it. Or manually delete first:
```bash
aws lambda delete-function --function-name web-agent-executor
```

### Issue: Build takes a long time

**Expected**: Docker build takes 5-10 minutes first time due to:
- Installing system packages
- Downloading Chromium (~200MB)
- Installing Python dependencies

**Subsequent builds**: Much faster (~2 minutes) due to Docker caching.

### Issue: "Playwright browser not found"

**Solution**: Make sure the Dockerfile includes:
```dockerfile
RUN python -m playwright install chromium
```

---

## Updating Your Function

After initial deployment, to update your code:

```bash
# 1. Make changes to handler.py or agent_executor.py

# 2. Rebuild and redeploy
./deploy_docker.sh

# That's it! The script handles everything.
```

---

## Cost Considerations

### ECR Storage
- ~$0.10 per GB per month
- Your image: ~500 MB = ~$0.05/month

### Lambda Execution
- Free tier: 1M requests/month, 400,000 GB-seconds
- After free tier: ~$0.20 per 1M requests
- Memory cost: ~$0.0000166667 per GB-second

**Example**: 1,000 races/month, 30 seconds each, 3GB memory
- Execution: 1,000 × 30s × 3GB = 90,000 GB-seconds
- Cost: 90,000 × $0.0000166667 = **~$1.50/month**
- Well within free tier for testing!

---

## Next Steps After Deployment

1. ✅ Lambda function deployed with Playwright
2. ✅ Function URL obtained
3. ➡️ Add Function URL to your `.env` file:
   ```bash
   AWS_LAMBDA_FUNCTION_URL=https://your-url.lambda-url.us-east-1.on.aws/
   ```
4. ➡️ Test from Streamlit app
5. ➡️ Deploy Streamlit to Streamlit Cloud

---

## Alternative: Manual Docker Deployment

If you prefer manual control:

```bash
# 1. Build image
docker build -t web-agent-executor .

# 2. Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 3. Tag image
docker tag web-agent-executor:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/web-agent-executor:latest

# 4. Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/web-agent-executor:latest

# 5. Create Lambda function
aws lambda create-function \
  --function-name web-agent-executor \
  --package-type Image \
  --code ImageUri=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/web-agent-executor:latest \
  --role YOUR_LAMBDA_EXECUTION_ROLE_ARN \
  --memory-size 3008 \
  --timeout 300
```

---

## Support

If you encounter issues:
- Check CloudWatch Logs: Lambda Console → Monitor → View CloudWatch logs
- Verify Docker is running: `docker ps`
- Verify AWS credentials: `aws sts get-caller-identity`
- Check ECR repository: `aws ecr describe-repositories`

---

## Summary

**Current Status**: Ready to deploy Docker Lambda  
**Time Required**: ~15 minutes first time (mostly build time)  
**Result**: Full Playwright + Chromium support in Lambda  
**Next Action**: Run `./deploy_docker.sh` after configuring AWS CLI  

---

**Ready to deploy? Configure AWS CLI credentials, then run the deployment script!**

