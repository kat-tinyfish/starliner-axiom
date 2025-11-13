"""
AWS Lambda Handler - Entry point for browser execution.

This handler receives agent execution requests and orchestrates browser automation.
"""

import json
import os
import asyncio
from typing import Dict, Any
from agent_executor import AgentExecutor
from vnc_manager import ensure_vnc_running, get_vnc_manager


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function for agent execution.
    
    Expected event structure:
    {
        "body": {
            "action": "execute" | "health_check",
            "agent_config": {
                "agent_id": "gpt4-agent",
                "model": "gpt-4-turbo",
                "api_key": "sk-..."
            },
            "prompt": "Task description",
            "constraints": {
                "domains": ["example.com"],
                "schema": {...}
            }
        }
    }
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        Response with execution results
    """
    try:
        # Parse event body
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)
        
        action = body.get("action", "execute")
        
        # Health check endpoint
        if action == "health_check":
            # VNC disabled for screenshot polling
            return create_response(200, {
                "status": "healthy",
                "message": "Lambda function is running (screenshot polling mode)",
                "playwright_available": check_playwright_available(),
                "screenshot_polling_enabled": True
            })
        
        # Validate required fields
        agent_config = body.get("agent_config", {})
        prompt = body.get("prompt", "")
        
        if not agent_config:
            return create_response(400, {
                "status": "error",
                "error": "agent_config is required"
            })
        
        if not prompt:
            return create_response(400, {
                "status": "error",
                "error": "prompt is required"
            })
        
        # Get API keys from environment if not provided
        agent_id = agent_config.get("agent_id", "")
        if not agent_config.get("api_key"):
            api_key = get_api_key_for_agent(agent_id)
            if api_key:
                agent_config["api_key"] = api_key
        
        constraints = body.get("constraints", {})
        enable_vnc = body.get("enable_vnc", False)  # VNC disabled by default (using screenshot polling)
        
        # Start VNC if explicitly requested (experimental)
        vnc_url = None
        if enable_vnc:
            print("⚠️ VNC mode requested (experimental - screenshots recommended)")
            if ensure_vnc_running():
                # Get Lambda Function URL from environment
                lambda_url = os.environ.get('AWS_LAMBDA_FUNCTION_URL', os.environ.get('LAMBDA_FUNCTION_URL', 'http://localhost:6080'))
                vnc_manager = get_vnc_manager()
                vnc_url = vnc_manager.get_websocket_url(lambda_url)
            else:
                print("Warning: Failed to start VNC, continuing with screenshot polling")
        
        # Execute agent task
        executor = AgentExecutor(agent_config)
        result = asyncio.run(executor.execute(prompt, constraints))
        
        # Build response
        response_body = {
            "status": "success",
            "result": result
        }
        
        # Add VNC URL if available
        if vnc_url:
            response_body["vnc_url"] = vnc_url
            response_body["session_id"] = context.aws_request_id if context else "local-test"
        
        return create_response(200, response_body)
    
    except json.JSONDecodeError as e:
        return create_response(400, {
            "status": "error",
            "error": f"Invalid JSON: {str(e)}"
        })
    
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return create_response(500, {
            "status": "error",
            "error": str(e),
            "type": type(e).__name__
        })


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a properly formatted Lambda response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body)
    }


def check_playwright_available() -> bool:
    """Check if Playwright is available."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


def get_api_key_for_agent(agent_id: str) -> str:
    """Get API key from environment variables based on agent ID."""
    key_map = {
        "gpt4-agent": "OPENAI_API_KEY",
        "claude-agent": "ANTHROPIC_API_KEY",
        "gemini-agent": "GOOGLE_API_KEY",
        "tinyfish-agent": "TINYFISH_API_KEY"
    }
    
    env_var = key_map.get(agent_id, "")
    return os.environ.get(env_var, "")


# For local testing
if __name__ == "__main__":
    print("Testing Lambda handler locally...")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    health_event = {
        "body": json.dumps({
            "action": "health_check"
        })
    }
    
    result = lambda_handler(health_event, None)
    print(f"Status: {result['statusCode']}")
    print(f"Body: {json.dumps(json.loads(result['body']), indent=2)}")
    
    # Test 2: Agent execution (with mock API key)
    print("\n2. Testing agent execution...")
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
    
    test_event = {
        "body": json.dumps({
            "action": "execute",
            "agent_config": {
                "agent_id": "gpt4-agent",
                "model": "gpt-4-turbo",
                "name": "GPT-4 Web Agent"
            },
            "prompt": "Go to example.com and get the page title",
            "constraints": {
                "domains": ["example.com"]
            }
        })
    }
    
    result = lambda_handler(test_event, None)
    print(f"Status: {result['statusCode']}")
    print(f"Body: {json.dumps(json.loads(result['body']), indent=2)}")
