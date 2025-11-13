"""
AWS Lambda Handler - Entry point for browser execution.

This handler receives agent execution requests and orchestrates browser automation.
Handles missing Playwright gracefully for MVP deployment.
"""

import json
import os
import sys
import asyncio
from typing import Dict, Any

# Check Playwright availability first
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Playwright not available - Lambda will work without browser automation")

# Try to import agent executor
AGENT_EXECUTOR_AVAILABLE = False
AgentExecutor = None
try:
    from agent_executor import AgentExecutor
    AGENT_EXECUTOR_AVAILABLE = True
except ImportError as e:
    print(f"AgentExecutor import failed: {e}")
    print("Lambda will respond with status only")


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
            return create_response(200, {
                "status": "healthy",
                "message": "Lambda function is running",
                "playwright_available": PLAYWRIGHT_AVAILABLE,
                "agent_executor_available": AGENT_EXECUTOR_AVAILABLE,
                "python_version": sys.version,
                "environment": "aws_lambda"
            })
        
        # Check if execution is possible
        if action == "execute":
            if not AGENT_EXECUTOR_AVAILABLE:
                return create_response(503, {
                    "status": "unavailable",
                    "error": "AgentExecutor not available",
                    "message": "Lambda configured but agent executor failed to import"
                })
            
            if not PLAYWRIGHT_AVAILABLE:
                return create_response(503, {
                    "status": "unavailable",
                    "error": "Playwright not available",
                    "message": "Add Lambda layer with Playwright for browser automation",
                    "note": "For MVP: Health check works, but browser execution requires Playwright layer"
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
            
            # Execute agent task
            executor = AgentExecutor(agent_config)
            result = asyncio.run(executor.execute(prompt, constraints))
            
            return create_response(200, {
                "status": "success",
                "result": result
            })
        
        # Unknown action
        return create_response(400, {
            "status": "error",
            "error": f"Unknown action: {action}",
            "supported_actions": ["health_check", "execute"]
        })
    
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
    
    print("\n" + "=" * 60)
    print("Health check test complete!")
    print("If Playwright is not available, that's expected for MVP.")
    print("Lambda will work for health checks and status reporting.")

