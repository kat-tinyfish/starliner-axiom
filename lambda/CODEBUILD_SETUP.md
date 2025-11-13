# AWS CodeBuild Setup Guide

This guide will help you build and push the Docker image to ECR using AWS CodeBuild.

## Prerequisites

✅ GitHub repository: https://github.com/kat-tinyfish/starliner-axiom  
✅ AWS Account: 344735855159  
✅ ECR Repository: `web-agent-executor` (already created)

---

## Step 1: Commit and Push buildspec.yml

First, let's commit the buildspec.yml file to your repository:

```bash
cd /Users/kat.tinyfish/starliner/starliner-axiom
git add lambda/buildspec.yml lambda/CODEBUILD_SETUP.md
git commit -m "Add CodeBuild configuration for Lambda Docker deployment"
git push origin main
```

---

## Step 2: Create CodeBuild Project

### 2.1 Navigate to CodeBuild

1. Go to AWS Console: https://console.aws.amazon.com/
2. Search for "CodeBuild" in the search bar
3. Click **"CodeBuild"**
4. Click **"Create build project"**

### 2.2 Project Configuration

**Project name:** `web-agent-executor-builder`

**Description:** `Builds Docker image with Playwright + Chromium for Lambda`

### 2.3 Source

- **Source provider:** GitHub
- Click **"Connect to GitHub"** (if not already connected)
  - Authorize AWS CodeBuild to access your GitHub account
- **Repository:** Select "Repository in my GitHub account"
- **GitHub repository:** `kat-tinyfish/starliner-axiom`
- **Source version:** `main` (or leave blank for default branch)

**IMPORTANT - Webhooks:**
- Scroll down to **"Primary source webhook events"**
- **UNCHECK** "Rebuild every time a code change is pushed to this repository"
- (We'll trigger builds manually - avoids webhook setup issues)

### 2.4 Environment

- **Environment image:** Managed image
- **Operating system:** Amazon Linux
- **Runtime(s):** Standard
- **Image:** `aws/codebuild/standard:7.0` (latest)
- **Image version:** Always use the latest image
- **Environment type:** Linux
- **Privileged:** ✅ **ENABLE** (Required for Docker builds!)
  - Check the box "Enable this flag if you want to build Docker images or want your builds to get elevated privileges"
- **Service role:** 
  - Select "New service role"
  - **Role name:** `codebuild-web-agent-executor-builder-service-role-1`

### 2.5 Buildspec

- **Build specifications:** Use a buildspec file
- **Buildspec name:** `lambda/buildspec.yml`

### 2.6 Artifacts

- **Type:** No artifacts

### 2.7 Logs

- **CloudWatch logs:** ✅ Enabled
- **Group name:** `/aws/codebuild/web-agent-executor-builder`
- **Stream name:** (leave blank)

### 2.8 Click "Create build project"

---

## Step 3: Add ECR Permissions to CodeBuild Role

CodeBuild needs permission to push to ECR.

### 3.1 Navigate to IAM

1. Go to IAM Console: https://console.aws.amazon.com/iam/
2. Click **"Roles"** in the left sidebar
3. Search for `codebuild-web-agent-executor-builder-service-role`
4. Click on the role

### 3.2 Add ECR Policy

1. Click **"Add permissions"** → **"Attach policies"**
2. Search for `AmazonEC2ContainerRegistryPowerUser`
3. Check the box next to it
4. Click **"Attach policies"**

Alternatively, create a custom inline policy:

1. Click **"Add permissions"** → **"Create inline policy"**
2. Click **"JSON"** tab
3. Paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

4. Click **"Review policy"**
5. **Name:** `ECRPushPolicy`
6. Click **"Create policy"**

---

## Step 4: Add Environment Variables

Back in CodeBuild project:

1. Go to your CodeBuild project: `web-agent-executor-builder`
2. Click **"Edit"** → **"Environment"**
3. Scroll to **"Additional configuration"**
4. Under **"Environment variables"**, add:

| Name | Value | Type |
|------|-------|------|
| `AWS_DEFAULT_REGION` | `us-east-1` | Plaintext |
| `AWS_ACCOUNT_ID` | `344735855159` | Plaintext |

5. Click **"Update environment"**

---

## Step 5: Start Build

1. Go to your CodeBuild project: `web-agent-executor-builder`
2. Click **"Start build"**
3. Leave all settings as default
4. Click **"Start build"** at the bottom

### Monitor Build

The build will take **15-25 minutes** (downloading base images, installing 238 packages, downloading Chromium).

You can watch the build logs in real-time:
- **Phase details** shows current phase (pre_build, build, post_build)
- **Build logs** shows command output

---

## Step 6: Verify ECR Push

Once the build completes (status: **Succeeded**):

1. Go to ECR Console: https://console.aws.amazon.com/ecr/
2. Click on `web-agent-executor` repository
3. You should see:
   - **Image tag:** `latest`
   - **Image tag:** `<commit-hash>`
   - **Image size:** ~1.5-2 GB
   - **Pushed:** Just now

---

## Step 7: Create/Update Lambda Function

Now that the image is in ECR, create the Lambda function:

### 7.1 Navigate to Lambda

1. Go to Lambda Console: https://console.aws.amazon.com/lambda/
2. Click **"Create function"**

### 7.2 Function Configuration

- **Function option:** Container image
- **Function name:** `web-agent-executor`
- **Container image URI:** Click **"Browse images"**
  - Select `web-agent-executor` repository
  - Select `latest` tag
  - Click **"Select image"**
- **Architecture:** x86_64

### 7.3 Permissions

- **Execution role:** Create a new role with basic Lambda permissions

### 7.4 Click "Create function"

### 7.5 Configure Function

1. Click **"Configuration"** tab
2. Click **"General configuration"** → **"Edit"**
   - **Memory:** 2048 MB
   - **Timeout:** 5 minutes (300 seconds)
   - **Ephemeral storage:** 2048 MB
3. Click **"Save"**

4. Click **"Environment variables"** → **"Edit"**
   - Add your API keys:
     - `OPENAI_API_KEY`
     - `ANTHROPIC_API_KEY`
     - `GOOGLE_API_KEY`
     - `TINYFISH_API_KEY`
5. Click **"Save"**

### 7.6 Enable Function URL

1. Click **"Configuration"** tab
2. Click **"Function URL"** → **"Create function URL"**
3. **Auth type:** NONE (for testing; use IAM for production)
4. **Configure CORS:** Yes
   - **Allow origins:** `*` (or your Streamlit app domain)
   - **Allow methods:** POST, GET
   - **Allow headers:** content-type
5. Click **"Save"**

6. **Copy the Function URL** (you'll need this for Streamlit)

---

## Step 8: Test Lambda Function

### 8.1 Test Health Check

1. In Lambda console, click **"Test"** tab
2. **Event name:** `health-check`
3. **Event JSON:**

```json
{
  "action": "health_check"
}
```

4. Click **"Test"**
5. You should see:

```json
{
  "status": "healthy",
  "playwright_available": true,
  "timestamp": "2024-11-13T..."
}
```

### 8.2 Test Agent Execution

1. Create new test event
2. **Event name:** `test-agent`
3. **Event JSON:**

```json
{
  "action": "execute_agent",
  "agent_id": "gpt4",
  "task": "Go to example.com and find the heading",
  "session_id": "test-123"
}
```

4. Click **"Test"**
5. Wait 30-60 seconds
6. You should see agent execution results with screenshots and tool calls

---

## Step 9: Connect to Streamlit

Update your `.env` file:

```bash
LAMBDA_FUNCTION_URL=https://your-function-url.lambda-url.us-east-1.on.aws/
```

Update `utils/lambda_client.py` if needed to use the function URL.

Test the integration:

```bash
cd /Users/kat.tinyfish/starliner/starliner-axiom
streamlit run app.py
```

---

## Troubleshooting

### Webhook Creation Failed: "CodeBuild is not authorized to perform: sts:AssumeRole"
**Solution 1 (Recommended):** Disable webhooks
- When creating the project, uncheck "Rebuild every time a code change is pushed"
- Trigger builds manually by clicking "Start build"

**Solution 2:** Fix the trust policy
1. Go to IAM → Roles → Find your CodeBuild service role
2. Click "Trust relationships" → "Edit trust policy"
3. Ensure it has:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```
4. Save and retry creating the CodeBuild project

### Build Fails: "Privileged flag not enabled"
- Edit CodeBuild project → Environment → Enable "Privileged" flag

### Build Fails: "Access Denied" pushing to ECR
- Check IAM role has ECR permissions (Step 3)
- Verify AWS_ACCOUNT_ID environment variable is correct

### Lambda Fails: "Task timed out"
- Increase Lambda timeout to 5 minutes (300 seconds)
- Increase memory to 2048 MB or more

### Lambda Fails: "No space left on device"
- Increase ephemeral storage to 2048 MB

### Playwright Fails: "Browser not found"
- Verify `PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright` is set
- Check build logs to ensure Chromium was installed

---

## Cost Estimate

**CodeBuild:**
- First 100 build minutes/month: FREE
- After: $0.005/minute
- This build: ~20 minutes = FREE (or $0.10)

**ECR:**
- Storage: $0.10/GB/month
- This image: ~2GB = $0.20/month
- Data transfer: FREE (within same region)

**Lambda:**
- First 1M requests/month: FREE
- First 400,000 GB-seconds: FREE
- Typical cost: $0-5/month for development

---

## Next Steps

1. ✅ Commit buildspec.yml to GitHub
2. ✅ Create CodeBuild project
3. ✅ Add ECR permissions
4. ✅ Start build (wait 15-25 min)
5. ✅ Create Lambda function with ECR image
6. ✅ Test Lambda function
7. ✅ Connect to Streamlit app
8. 🚀 Deploy Streamlit to Streamlit Cloud

---

## Success Criteria

✅ CodeBuild status: **Succeeded**  
✅ ECR has image tagged `latest` (~2GB)  
✅ Lambda function health check returns `{"status": "healthy"}`  
✅ Lambda function can execute agent tasks  
✅ Streamlit app can call Lambda function URL

You're done! 🎉

