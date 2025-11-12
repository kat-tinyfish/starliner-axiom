#!/bin/bash
# AWS Lambda Deployment Script for Web Agent Executor
# This script packages and deploys the Lambda function with Playwright

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  AWS Lambda Deployment - Web Agent Executor                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-web-agent-executor}"
REGION="${AWS_REGION:-us-east-1}"
RUNTIME="python3.11"
MEMORY_SIZE=2048
TIMEOUT=300

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    echo "   Install: https://aws.amazon.com/cli/"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI found${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "   Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS credentials configured${NC}"
echo "   Account ID: $ACCOUNT_ID"
echo "   Region: $REGION"
echo ""

# Step 1: Create Playwright Lambda Layer
echo "📦 Step 1: Creating Playwright Lambda Layer..."
echo "────────────────────────────────────────────────────────────────"

if [ -d "layer" ]; then
    echo "   Cleaning up old layer directory..."
    rm -rf layer
fi

mkdir -p layer/python

echo "   Installing Playwright and dependencies..."
pip install playwright -t layer/python/ --quiet

echo ""
echo -e "${YELLOW}⚠️  Note: Chromium browser not included in layer (size limitations)${NC}"
echo "   For browser automation, consider:"
echo "   1. Using Docker-based Lambda (recommended for production)"
echo "   2. Using a pre-built Playwright layer from AWS Serverless Repo"
echo "   3. For MVP: Handler will work but browser tests will be limited"
echo ""

echo "   Creating layer ZIP file..."
cd layer && zip -r ../layer.zip . -q && cd ..

echo "   Publishing layer to AWS Lambda..."
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name playwright-web-agent-layer \
    --description "Playwright for web agent execution" \
    --zip-file fileb://layer.zip \
    --compatible-runtimes $RUNTIME \
    --region $REGION \
    --query 'Version' \
    --output text)

LAYER_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:layer:playwright-web-agent-layer:${LAYER_VERSION}"

echo -e "${GREEN}✅ Layer published${NC}"
echo "   Layer ARN: $LAYER_ARN"
echo ""

# Step 2: Package Lambda Function
echo "📦 Step 2: Packaging Lambda Function..."
echo "────────────────────────────────────────────────────────────────"

if [ -f "function.zip" ]; then
    rm function.zip
fi

echo "   Zipping function code..."
zip -j function.zip handler.py agent_executor.py -q

echo -e "${GREEN}✅ Function packaged${NC}"
echo ""

# Step 3: Create or Update Lambda Function
echo "🚀 Step 3: Deploying Lambda Function..."
echo "────────────────────────────────────────────────────────────────"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &> /dev/null; then
    echo "   Function exists. Updating..."
    
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION \
        --query 'FunctionArn' \
        --output text
    
    echo "   Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --layers $LAYER_ARN \
        --memory-size $MEMORY_SIZE \
        --timeout $TIMEOUT \
        --region $REGION \
        --query 'FunctionArn' \
        --output text > /dev/null
    
    echo -e "${GREEN}✅ Function updated${NC}"
else
    echo "   Function doesn't exist. Creating..."
    
    # Create IAM role if it doesn't exist
    ROLE_NAME="${FUNCTION_NAME}-role"
    
    if ! aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
        echo "   Creating IAM role..."
        
        cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
        
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document file://trust-policy.json \
            --region $REGION > /dev/null
        
        # Attach basic execution policy
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        rm trust-policy.json
        
        echo "   Waiting for role to be ready..."
        sleep 10
    fi
    
    ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --handler handler.lambda_handler \
        --zip-file fileb://function.zip \
        --role $ROLE_ARN \
        --layers $LAYER_ARN \
        --memory-size $MEMORY_SIZE \
        --timeout $TIMEOUT \
        --region $REGION \
        --query 'FunctionArn' \
        --output text
    
    echo -e "${GREEN}✅ Function created${NC}"
fi

echo ""

# Step 4: Configure Function URL
echo "🌐 Step 4: Configuring Function URL..."
echo "────────────────────────────────────────────────────────────────"

# Check if function URL exists
if aws lambda get-function-url-config --function-name $FUNCTION_NAME --region $REGION &> /dev/null 2>&1; then
    echo "   Function URL already configured"
    FUNCTION_URL=$(aws lambda get-function-url-config \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)
else
    echo "   Creating function URL..."
    FUNCTION_URL=$(aws lambda create-function-url-config \
        --function-name $FUNCTION_NAME \
        --auth-type NONE \
        --cors "AllowOrigins=*,AllowMethods=POST,AllowHeaders=Content-Type" \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)
    
    # Add resource-based policy to allow public access
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id FunctionURLAllowPublicAccess \
        --action lambda:InvokeFunctionUrl \
        --principal "*" \
        --function-url-auth-type NONE \
        --region $REGION > /dev/null 2>&1 || true
fi

echo -e "${GREEN}✅ Function URL configured${NC}"
echo "   URL: $FUNCTION_URL"
echo ""

# Step 5: Set Environment Variables
echo "⚙️  Step 5: Setting Environment Variables..."
echo "────────────────────────────────────────────────────────────────"

# Read API keys from .env file if it exists
if [ -f "../.env" ]; then
    echo "   Reading API keys from .env file..."
    
    # Source the .env file
    export $(grep -v '^#' ../.env | xargs)
    
    ENV_VARS="Variables={"
    [ ! -z "$OPENAI_API_KEY" ] && ENV_VARS="${ENV_VARS}OPENAI_API_KEY=${OPENAI_API_KEY},"
    [ ! -z "$ANTHROPIC_API_KEY" ] && ENV_VARS="${ENV_VARS}ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},"
    [ ! -z "$GOOGLE_API_KEY" ] && ENV_VARS="${ENV_VARS}GOOGLE_API_KEY=${GOOGLE_API_KEY},"
    [ ! -z "$TINYFISH_API_KEY" ] && ENV_VARS="${ENV_VARS}TINYFISH_API_KEY=${TINYFISH_API_KEY},"
    ENV_VARS="${ENV_VARS%,}}"
    
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment "$ENV_VARS" \
        --region $REGION > /dev/null
    
    echo -e "${GREEN}✅ Environment variables set${NC}"
else
    echo -e "${YELLOW}⚠️  No .env file found. You'll need to set API keys manually.${NC}"
fi

echo ""

# Cleanup
echo "🧹 Cleaning up..."
rm -rf layer layer.zip function.zip

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Deployment Complete!                                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Function Details:"
echo "─────────────────────────────────────────────────────────────────"
echo "  Name:    $FUNCTION_NAME"
echo "  Region:  $REGION"
echo "  Runtime: $RUNTIME"
echo "  Memory:  ${MEMORY_SIZE}MB"
echo "  Timeout: ${TIMEOUT}s"
echo ""
echo "Function URL:"
echo "─────────────────────────────────────────────────────────────────"
echo "  $FUNCTION_URL"
echo ""
echo "Update your .env file with:"
echo "  AWS_LAMBDA_FUNCTION_URL=$FUNCTION_URL"
echo ""
echo "Test the function:"
echo "  ./test_lambda.sh"
echo ""

