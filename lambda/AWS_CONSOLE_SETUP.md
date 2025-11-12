# AWS Lambda Console Setup Guide

This guide walks you through creating the Web Agent Executor Lambda function using the AWS Console (web interface).

## Prerequisites

- AWS Account with appropriate permissions
- Lambda function code packaged (see below)
- API keys for agents (OpenAI, Anthropic, Google, TinyFish)

---

## Step 1: Package Your Lambda Function

First, create the deployment package on your local machine:

```bash
cd /Users/kat.tinyfish/starliner/starliner-axiom/lambda

# Create a deployment package
zip -r function.zip handler.py agent_executor.py
```

This creates `function.zip` containing your Lambda code.

---

## Step 2: Create Lambda Function via AWS Console

### Navigate to Lambda Console

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Search for "Lambda" in the search bar
3. Click on **Lambda** to open the Lambda console
4. Click **Create function** (orange button in top right)

### Function Configuration

On the "Create function" page:

#### Basic Information

1. **Choose**: Author from scratch (selected by default)

2. **Function name**: `web-agent-executor`

3. **Runtime**: Python 3.11

4. **Architecture**: x86_64

#### Permissions

5. **Execution role**: 
   - Select: **Create a new role with basic Lambda permissions**
   - Or if you have an existing role: **Use an existing role** and select it

6. Click **Create function** (orange button at bottom)

---

## Step 3: Upload Function Code

After the function is created:

1. Scroll down to the **Code source** section
2. Click **Upload from** → **.zip file**
3. Click **Upload** button
4. Select the `function.zip` file you created in Step 1
5. Click **Save**
6. Wait for the upload to complete (you'll see "Successfully updated the function")

---

## Step 4: Configure Function Settings

### Memory and Timeout

1. Click on the **Configuration** tab
2. Click **General configuration** in the left sidebar
3. Click **Edit**
4. Set **Memory**: `2048 MB` (2 GB)
5. Set **Timeout**: `5 min 0 sec` (300 seconds)
6. Click **Save**

### Environment Variables

1. Still in **Configuration** tab
2. Click **Environment variables** in the left sidebar
3. Click **Edit**
4. Click **Add environment variable** for each of these:

| Key | Value | Description |
|-----|-------|-------------|
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Your Anthropic API key |
| `GOOGLE_API_KEY` | `AI...` | Your Google API key |
| `TINYFISH_API_KEY` | `...` | Your TinyFish API key |

5. Click **Save**

---

## Step 5: Add Playwright Layer (Optional)

**Note**: For MVP, this step is optional. The function will work for testing without Playwright/browser support.

To add Playwright support:

### Option A: Use a Public Layer

1. In **Configuration** tab → **Layers**
2. Click **Add a layer**
3. Choose **Specify an ARN**
4. Enter a Playwright layer ARN (if you have one)
5. Click **Add**

### Option B: Create Your Own Layer

See `lambda/LAYER_CREATION.md` for instructions on creating a Playwright layer.

---

## Step 6: Enable Function URL (for External Access)

1. Click **Configuration** tab
2. Click **Function URL** in the left sidebar
3. Click **Create function URL**
4. **Auth type**: Select **NONE** (for public access)
   - ⚠️ **Important**: For production, use **AWS_IAM** for security
5. **Configure CORS**:
   - Check: **Configure cross-origin resource sharing (CORS)**
   - **Allow origin**: `*` (or your Streamlit domain)
   - **Allow methods**: `POST`
   - **Allow headers**: `content-type`
6. Click **Save**
7. **Copy the Function URL** - you'll need this for your Streamlit app

Example URL: `https://abc123xyz.lambda-url.us-east-1.on.aws/`

---

## Step 7: Test the Function

### Test Event Configuration

1. Click **Test** tab
2. Click **Create new event**
3. **Event name**: `health-check`
4. **Event JSON**:
```json
{
  "body": "{\"action\": \"health_check\"}"
}
```
5. Click **Save**
6. Click **Test** button
7. Check the **Execution results** - you should see:
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "{\"status\": \"healthy\", \"message\": \"Lambda function is running\", \"playwright_available\": true}"
}
```

### Test Agent Execution (Advanced)

Create another test event:

1. **Event name**: `test-execution`
2. **Event JSON**:
```json
{
  "body": "{\"action\": \"execute\", \"agent_config\": {\"agent_id\": \"gpt4-agent\", \"name\": \"GPT-4 Web Agent\", \"api_provider\": \"openai\", \"model\": \"gpt-4-turbo\"}, \"prompt\": \"Go to https://example.com and get the page title\", \"constraints\": {}}"
}
```
3. Click **Save** → **Test**

---

## Step 8: Connect to Streamlit App

### Update Your `.env` File

Add the Lambda function URL to your `.env`:

```bash
# AWS Lambda
AWS_LAMBDA_FUNCTION_URL=https://your-function-url.lambda-url.us-east-1.on.aws/
```

### Update Streamlit Configuration

If you have a `utils/lambda_client.py`, ensure it uses this URL:

```python
import os
import requests

LAMBDA_URL = os.getenv("AWS_LAMBDA_FUNCTION_URL")

def invoke_lambda(action, payload):
    response = requests.post(
        LAMBDA_URL,
        json={
            "action": action,
            **payload
        }
    )
    return response.json()
```

---

## Step 9: Monitor and Debug

### CloudWatch Logs

1. In Lambda console, click **Monitor** tab
2. Click **View CloudWatch logs**
3. Click on the latest log stream to see execution logs
4. Look for `print()` statements from your code

### Common Issues

#### Issue: "Task timed out after 3.00 seconds"
**Solution**: Increase timeout in Configuration → General configuration

#### Issue: "Unable to import module 'handler'"
**Solution**: Make sure your .zip file has `handler.py` at the root level (not in a subdirectory)

#### Issue: "No module named 'playwright'"
**Solution**: You need to add a Lambda layer with Playwright (see Step 5)

#### Issue: Environment variables not found
**Solution**: Check Configuration → Environment variables and ensure all keys are set correctly

---

## Step 10: Production Considerations

### Security

1. **Use IAM authentication** for Function URL instead of NONE
2. **Encrypt environment variables** using KMS
3. **Use VPC** if accessing private resources
4. **Set up API Gateway** for better rate limiting and security

### Performance

1. **Adjust memory** based on actual usage (monitor CloudWatch)
2. **Enable Provisioned Concurrency** for consistent performance
3. **Set up Reserved Concurrency** to control costs

### Monitoring

1. **Set up CloudWatch Alarms** for:
   - Error rate
   - Duration
   - Throttles
2. **Enable X-Ray tracing** for detailed performance insights

---

## Architecture Overview

```
┌─────────────────┐
│  Streamlit App  │
│   (Local/Cloud) │
└────────┬────────┘
         │
         │ HTTPS POST
         │
         ▼
┌─────────────────────────┐
│  Lambda Function URL    │
│  (Public Endpoint)      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  web-agent-executor     │
│  - handler.py           │
│  - agent_executor.py    │
│  - Env Variables        │
│  - Playwright (Layer)   │
└────────┬────────────────┘
         │
         ├──────► OpenAI API
         ├──────► Anthropic API
         ├──────► Google API
         └──────► TinyFish API
```

---

## Quick Reference: Key Settings

| Setting | Value |
|---------|-------|
| Function Name | `web-agent-executor` |
| Runtime | Python 3.11 |
| Memory | 2048 MB |
| Timeout | 300 seconds |
| Handler | `handler.lambda_handler` |
| Architecture | x86_64 |

---

## Next Steps

1. ✅ Lambda function created and tested
2. ✅ Function URL obtained
3. ➡️ Update Streamlit app to use Lambda URL
4. ➡️ Test end-to-end agent execution
5. ➡️ Deploy Streamlit to Streamlit Cloud

---

## Support

If you encounter issues:
- Check CloudWatch logs for detailed error messages
- Verify all environment variables are set correctly
- Ensure your AWS account has sufficient permissions
- Review the function's IAM role and attached policies

For more advanced setup (Docker, VNC streaming), see:
- `lambda/README.md` - Complete Lambda documentation
- `lambda/deploy.sh` - Automated deployment script
- `lambda/AWS_SETUP_GUIDE.md` - Advanced AWS configurations

