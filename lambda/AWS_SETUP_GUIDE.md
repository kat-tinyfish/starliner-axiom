# AWS Lambda Setup Guide

Complete guide for deploying the Web Agent Executor to AWS Lambda.

## 📋 Prerequisites

### 1. AWS Account
- Active AWS account
- AWS CLI installed and configured
- Appropriate IAM permissions

### 2. Local Tools
```bash
# Check AWS CLI
aws --version

# Check credentials
aws sts get-caller-identity

# If not configured:
aws configure
```

### 3. Required Permissions
Your AWS user/role needs:
- `lambda:*` (Lambda operations)
- `iam:CreateRole`, `iam:AttachRolePolicy` (for IAM role creation)
- `s3:*` (if storing screenshots in S3)

---

## 🚀 Quick Deploy (Automated)

The easiest way to deploy:

```bash
cd lambda

# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

This script will:
1. ✅ Create Playwright Lambda layer
2. ✅ Package function code
3. ✅ Create/update Lambda function
4. ✅ Configure function URL
5. ✅ Set environment variables from .env

---

## 📝 Manual Deployment

If you prefer to deploy manually or understand each step:

### Step 1: Create Playwright Layer

```bash
# Create layer directory
mkdir -p layer/python

# Install dependencies
pip install playwright playwright-aws-lambda -t layer/python/

# Create ZIP
cd layer && zip -r ../layer.zip . && cd ..

# Upload to AWS
aws lambda publish-layer-version \
  --layer-name playwright-web-agent-layer \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11 \
  --region us-east-1
```

**Note the Layer ARN** from the output - you'll need it later.

### Step 2: Package Function Code

```bash
# Create function ZIP (just the Python files)
zip -j function.zip handler.py agent_executor.py
```

### Step 3: Create IAM Role

```bash
# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name web-agent-executor-role \
  --assume-role-policy-document file://trust-policy.json

# Attach basic execution policy
aws iam attach-role-policy \
  --role-name web-agent-executor-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

**Note the Role ARN** from the output.

### Step 4: Create Lambda Function

```bash
aws lambda create-function \
  --function-name web-agent-executor \
  --runtime python3.11 \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/web-agent-executor-role \
  --layers arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:layer:playwright-web-agent-layer:1 \
  --memory-size 2048 \
  --timeout 300 \
  --region us-east-1
```

Replace:
- `YOUR_ACCOUNT_ID` with your AWS account ID
- Layer ARN with the one from Step 1
- Role ARN with the one from Step 3

### Step 5: Configure Function URL

```bash
# Create public function URL
aws lambda create-function-url-config \
  --function-name web-agent-executor \
  --auth-type NONE \
  --cors "AllowOrigins=*,AllowMethods=POST,AllowHeaders=Content-Type" \
  --region us-east-1

# Allow public access
aws lambda add-permission \
  --function-name web-agent-executor \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region us-east-1
```

**Save the Function URL** from the output!

### Step 6: Set Environment Variables

```bash
# Set API keys
aws lambda update-function-configuration \
  --function-name web-agent-executor \
  --environment "Variables={
    OPENAI_API_KEY=sk-...,
    ANTHROPIC_API_KEY=sk-ant-...,
    GOOGLE_API_KEY=...,
    TINYFISH_API_KEY=...
  }" \
  --region us-east-1
```

---

## 🧪 Testing

### Test Locally First

```bash
# Test handler
python handler.py

# Test executor
python agent_executor.py
```

### Test Lambda Function

```bash
# Make test script executable
chmod +x test_lambda.sh

# Run tests
./test_lambda.sh https://your-function-url.lambda-url.us-east-1.on.aws/
```

Or test manually:

```bash
curl -X POST https://your-function-url.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "health_check"
  }'
```

Expected response:
```json
{
  "statusCode": 200,
  "body": {
    "status": "healthy",
    "message": "Lambda function is running",
    "playwright_available": true
  }
}
```

---

## ⚙️ Configuration

### Update .env File

After deployment, update your main `.env` file:

```bash
# Add this line
AWS_LAMBDA_FUNCTION_URL=https://your-function-url.lambda-url.us-east-1.on.aws/
```

### Lambda Function Settings

Recommended settings:
- **Memory**: 2048 MB (minimum for Playwright)
- **Timeout**: 300 seconds (5 minutes)
- **Ephemeral storage**: 512 MB (default)

To update:

```bash
aws lambda update-function-configuration \
  --function-name web-agent-executor \
  --memory-size 2048 \
  --timeout 300 \
  --ephemeral-storage Size=512
```

---

## 🔄 Updating the Function

When you make changes to `handler.py` or `agent_executor.py`:

```bash
# Re-package
zip -j function.zip handler.py agent_executor.py

# Update
aws lambda update-function-code \
  --function-name web-agent-executor \
  --zip-file fileb://function.zip
```

Or use the deployment script:

```bash
./deploy.sh  # Automatically updates if function exists
```

---

## 💰 Cost Estimates

### Lambda Pricing (us-east-1)
- **Compute**: $0.0000166667 per GB-second
- **Requests**: $0.20 per 1M requests
- **Free tier**: 400,000 GB-seconds/month, 1M requests/month

### Example Costs

**With 2GB memory, 30s average execution:**
- Per execution: ~$0.001
- 1,000 races/month: ~$1.00
- 10,000 races/month: ~$10.00

**Note:** Most usage will likely fall within the free tier for development/testing.

---

## 🔒 Security Best Practices

### 1. Restrict Function URL (Production)

Instead of public access:

```bash
# Use IAM authentication
aws lambda update-function-url-config \
  --function-name web-agent-executor \
  --auth-type AWS_IAM
```

Then use Cognito or API Gateway for authentication.

### 2. Environment Variables

Don't hardcode API keys in code. Always use environment variables or AWS Secrets Manager:

```bash
# Store in Secrets Manager
aws secretsmanager create-secret \
  --name web-agent-api-keys \
  --secret-string '{
    "OPENAI_API_KEY": "sk-...",
    "ANTHROPIC_API_KEY": "sk-ant-..."
  }'

# Update Lambda to use Secrets Manager
# (requires code changes in handler.py)
```

### 3. VPC Configuration

For additional security, run Lambda in a VPC:

```bash
aws lambda update-function-configuration \
  --function-name web-agent-executor \
  --vpc-config SubnetIds=subnet-xxx,subnet-yyy,SecurityGroupIds=sg-xxx
```

---

## 📊 Monitoring

### CloudWatch Logs

View logs:

```bash
# Get log streams
aws logs describe-log-streams \
  --log-group-name /aws/lambda/web-agent-executor \
  --order-by LastEventTime \
  --descending

# Tail logs
aws logs tail /aws/lambda/web-agent-executor --follow
```

### Metrics

Key metrics to monitor:
- **Invocations**: Number of executions
- **Duration**: Execution time
- **Errors**: Failed executions
- **Throttles**: Rate limit hits

View in CloudWatch Console:
https://console.aws.amazon.com/cloudwatch/

---

## 🐛 Troubleshooting

### Issue: "Playwright not found"

**Solution**: Make sure the Playwright layer is attached:

```bash
aws lambda update-function-configuration \
  --function-name web-agent-executor \
  --layers arn:aws:lambda:REGION:ACCOUNT:layer:playwright-web-agent-layer:VERSION
```

### Issue: "Task timed out after 3.00 seconds"

**Solution**: Increase timeout:

```bash
aws lambda update-function-configuration \
  --function-name web-agent-executor \
  --timeout 300
```

### Issue: "Memory limit exceeded"

**Solution**: Increase memory:

```bash
aws lambda update-function-configuration \
  --function-name web-agent-executor \
  --memory-size 3008  # or higher
```

### Issue: "CORS errors"

**Solution**: Update CORS configuration:

```bash
aws lambda update-function-url-config \
  --function-name web-agent-executor \
  --cors "AllowOrigins=*,AllowMethods=POST,OPTIONS,AllowHeaders=Content-Type,Authorization"
```

---

## 🔄 Alternative: EC2 Deployment

For better VNC streaming support, consider EC2:

### Advantages
- Real VNC server for live streaming
- No 15-minute Lambda timeout
- Persistent browser sessions
- Better for long-running tasks

### Disadvantages
- Always running (higher cost)
- Manual scaling
- More maintenance

See `README.md` for EC2 deployment instructions.

---

## 📚 Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Playwright Documentation](https://playwright.dev/)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [AWS CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lambda/index.html)

---

## ✅ Deployment Checklist

- [ ] AWS CLI installed and configured
- [ ] Created Playwright Lambda layer
- [ ] Packaged function code
- [ ] Created IAM role with appropriate permissions
- [ ] Deployed Lambda function
- [ ] Configured function URL
- [ ] Set environment variables (API keys)
- [ ] Tested function with health check
- [ ] Tested function with sample execution
- [ ] Updated .env with Lambda URL
- [ ] Configured monitoring/logging
- [ ] Set up budget alerts (optional)

---

**Need help?** Check the troubleshooting section or file an issue in the repository.

