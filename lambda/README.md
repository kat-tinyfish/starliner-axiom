# AWS Lambda Functions

This directory contains AWS Lambda functions for browser execution.

## Overview

The Lambda functions handle:
- Browser instance creation with Playwright
- Agent task execution
- Tool call streaming
- Screenshot capture
- VNC server management (for EC2 deployment)

## Structure

```
lambda/
├── requirements.txt    # Lambda-specific dependencies
├── handler.py         # Lambda entry point
└── agent_executor.py  # Browser execution logic
```

## Deployment

### Option 1: AWS Lambda (Serverless)

1. **Create Lambda Layer for Playwright**:
```bash
# Build layer
mkdir -p layer/python
pip install playwright -t layer/python/
cd layer && zip -r ../layer.zip . && cd ..

# Upload to AWS Lambda as a layer
aws lambda publish-layer-version \
  --layer-name playwright-layer \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

2. **Deploy Lambda Function**:
```bash
# Package function code
zip -r function.zip handler.py agent_executor.py

# Create/update function
aws lambda create-function \
  --function-name web-agent-executor \
  --runtime python3.11 \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --memory-size 2048 \
  --timeout 300 \
  --layers arn:aws:lambda:REGION:ACCOUNT:layer:playwright-layer:VERSION
```

3. **Enable Function URL**:
```bash
aws lambda create-function-url-config \
  --function-name web-agent-executor \
  --auth-type NONE \
  --cors '{"AllowOrigins": ["*"], "AllowMethods": ["POST"]}'
```

### Option 2: EC2 with VNC (for real-time streaming)

For better VNC streaming support, deploy on EC2:

1. Launch EC2 instance (t3.medium or larger)
2. Install dependencies:
```bash
sudo apt update
sudo apt install -y python3.11 xvfb x11vnc novnc
pip3 install playwright
playwright install chromium
```

3. Start VNC server:
```bash
# Start Xvfb
Xvfb :99 -screen 0 1280x720x24 &
export DISPLAY=:99

# Start x11vnc
x11vnc -display :99 -forever -nopw -quiet &

# Start noVNC websocket
/usr/share/novnc/utils/novnc_proxy --vnc localhost:5900
```

4. Deploy application code and run as a service

## Configuration

Set environment variables in Lambda or EC2:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
TINYFISH_API_KEY=...
```

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run handler locally
python handler.py
```

## TODO

- [ ] Implement handler.py with Lambda entry point
- [ ] Implement agent_executor.py with Playwright logic
- [ ] Add VNC server management for EC2
- [ ] Add screenshot capture and upload to Supabase Storage
- [ ] Add tool call streaming via WebSocket
- [ ] Add error handling and retry logic
- [ ] Add logging and monitoring

