#!/bin/bash
# Test script for AWS Lambda function

set -e

echo "🧪 Testing AWS Lambda Function"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if FUNCTION_URL is provided
if [ -z "$1" ]; then
    # Try to get from .env file
    if [ -f "../.env" ]; then
        FUNCTION_URL=$(grep AWS_LAMBDA_FUNCTION_URL ../.env | cut -d '=' -f2)
    fi
    
    if [ -z "$FUNCTION_URL" ]; then
        echo "❌ Function URL not provided"
        echo ""
        echo "Usage: ./test_lambda.sh <FUNCTION_URL>"
        echo "   or set AWS_LAMBDA_FUNCTION_URL in .env file"
        exit 1
    fi
else
    FUNCTION_URL=$1
fi

echo "Function URL: $FUNCTION_URL"
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "────────────────────────────────────────────────────────────────"

RESPONSE=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{
        "action": "health_check"
    }')

echo "$RESPONSE" | python3 -m json.tool
echo ""

# Test 2: Simple Navigation
echo "Test 2: Simple Navigation Task"
echo "────────────────────────────────────────────────────────────────"

RESPONSE=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{
        "action": "execute",
        "agent_config": {
            "agent_id": "test-agent",
            "name": "Test Agent"
        },
        "prompt": "Go to example.com and get the page title",
        "constraints": {}
    }')

echo "$RESPONSE" | python3 -m json.tool
echo ""

echo "✅ Tests complete!"

