#!/bin/bash
# Docker-based Lambda Deployment (Alternative for full browser support)
# This uses Docker to create a Lambda-compatible image with Playwright

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Docker Lambda Deployment - Web Agent Executor              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-web-agent-executor}"
REGION="${AWS_REGION:-us-east-1}"
IMAGE_NAME="web-agent-executor"

echo "📋 This approach uses Docker to create a Lambda container image"
echo "   with full Playwright + Chromium support."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    echo "   Install: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker found"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWS credentials configured"
echo "   Account ID: $ACCOUNT_ID"
echo "   Region: $REGION"
echo ""

# Create Dockerfile
echo "📝 Creating Dockerfile..."
cat > Dockerfile << 'EOF'
FROM public.ecr.aws/lambda/python:3.12

# Install Node.js 18 (required for Playwright)
RUN dnf install -y tar gzip && \
    curl -fsSL https://nodejs.org/dist/v18.19.0/node-v18.19.0-linux-x64.tar.gz | tar -xz -C /usr/local --strip-components=1 && \
    dnf clean all

# Install system dependencies for Chromium
RUN dnf install -y \
    atk \
    cups-libs \
    gtk3 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXScrnSaver \
    libXtst \
    pango \
    alsa-lib \
    libdrm \
    mesa-libgbm \
    nss \
    xdg-utils \
    && dnf clean all

# Install VNC Server and Xvfb for browser streaming
RUN dnf install -y \
    xorg-x11-server-Xvfb \
    tigervnc-server \
    fluxbox \
    git \
    && dnf clean all

# Install noVNC for web access
RUN git clone https://github.com/novnc/noVNC.git /opt/noVNC && \
    cd /opt/noVNC && \
    git checkout v1.4.0 && \
    ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html

# Configure VNC environment variables
ENV DISPLAY=:99
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080
RUN mkdir -p ~/.vnc

# Copy function code
COPY handler.py agent_executor.py vnc_manager.py ${LAMBDA_TASK_ROOT}/

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Install Playwright
RUN pip install playwright --target "${LAMBDA_TASK_ROOT}"

# Replace Playwright's bundled Node.js with system Node.js
# This fixes GLIBC compatibility issues on Amazon Linux 2
RUN rm -f ${LAMBDA_TASK_ROOT}/playwright/driver/node && \
    ln -s /usr/local/bin/node ${LAMBDA_TASK_ROOT}/playwright/driver/node

# Install Playwright browsers (dependencies already installed via dnf)
# Set environment variables for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright \
    python -m playwright install chromium

# Set the CMD to your handler
CMD [ "handler.lambda_handler" ]
EOF

echo "✅ Dockerfile created"
echo ""

# Create ECR repository
echo "📦 Creating ECR repository..."
aws ecr create-repository \
    --repository-name $IMAGE_NAME \
    --region $REGION \
    2>/dev/null || echo "   Repository already exists"

# Get ECR login
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin \
    ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Build Docker image
echo "🏗️  Building Docker image..."
docker build --platform linux/amd64 -t $IMAGE_NAME .

# Tag image
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${IMAGE_NAME}:latest"
docker tag $IMAGE_NAME:latest $ECR_URI

# Push to ECR
echo "⬆️  Pushing to ECR..."
docker push $ECR_URI

# Create or update Lambda function
echo "🚀 Creating/updating Lambda function..."

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &> /dev/null; then
    echo "   Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --image-uri $ECR_URI \
        --region $REGION
else
    echo "   Creating new function..."
    
    # Create IAM role if needed
    ROLE_NAME="${FUNCTION_NAME}-role"
    if ! aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
        cat > trust-policy.json << 'EOFT'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOFT
        
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document file://trust-policy.json
        
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        rm trust-policy.json
        sleep 10
    fi
    
    ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$ECR_URI \
        --role $ROLE_ARN \
        --timeout 300 \
        --memory-size 2048 \
        --region $REGION
fi

# Configure function URL
echo "🌐 Configuring Function URL..."
if ! aws lambda get-function-url-config --function-name $FUNCTION_NAME --region $REGION &> /dev/null 2>&1; then
    FUNCTION_URL=$(aws lambda create-function-url-config \
        --function-name $FUNCTION_NAME \
        --auth-type NONE \
        --cors "AllowOrigins=*,AllowMethods=POST,AllowHeaders=Content-Type" \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)
    
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id FunctionURLAllowPublicAccess \
        --action lambda:InvokeFunctionUrl \
        --principal "*" \
        --function-url-auth-type NONE \
        --region $REGION > /dev/null 2>&1 || true
else
    FUNCTION_URL=$(aws lambda get-function-url-config \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)
fi

# Cleanup
rm -f Dockerfile

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Docker Lambda Deployment Complete!                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Function URL:"
echo "  $FUNCTION_URL"
echo ""
echo "Update your .env file with:"
echo "  AWS_LAMBDA_FUNCTION_URL=$FUNCTION_URL"
echo ""

