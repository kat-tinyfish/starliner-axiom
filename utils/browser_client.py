"""
Unified Browser Execution Client for Web Agent Arena.

This module provides a unified interface for executing agents via:
- BrowserBase (recommended, free tier available)
- AWS Lambda (if configured)

The client automatically selects the best available option based on
environment variables.
"""

import os
import asyncio
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add lambda directory to path for imports
lambda_dir = Path(__file__).parent.parent / "lambda"
sys.path.insert(0, str(lambda_dir))


class BrowserExecutionClient:
    """Unified client for browser-based agent execution."""
    
    def __init__(self):
        """Initialize the client based on available configuration."""
        self.browserbase_available = bool(
            os.getenv("BROWSERBASE_API_KEY") and os.getenv("BROWSERBASE_PROJECT_ID")
        )
        self.lambda_available = bool(os.getenv("LAMBDA_FUNCTION_URL") or os.getenv("AWS_LAMBDA_FUNCTION_URL"))
        
        # Prefer BrowserBase (more reliable, free tier available)
        if self.browserbase_available:
            self.backend = "browserbase"
            print("🌐 Using BrowserBase for browser execution")
        elif self.lambda_available:
            self.backend = "lambda"
            print("⚡ Using AWS Lambda for browser execution")
        else:
            self.backend = None
            print("⚠️ No browser execution backend configured")
    
    async def execute_agent(
        self,
        prompt: str,
        agent_config: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an agent task.
        
        Args:
            prompt: Natural language task description
            agent_config: Agent configuration (model, API keys, etc.)
            constraints: Optional constraints (domains, JSON schema, etc.)
        
        Returns:
            Dict with execution results including:
            - success: bool
            - screenshots: List[Dict] (with base64 data)
            - tool_calls: List[Dict]
            - checkpoints: List[Dict]
            - execution_time: float
            - error: str (if failed)
        """
        if not self.backend:
            return {
                "success": False,
                "error": "No browser execution backend configured. Add BROWSERBASE_API_KEY or LAMBDA_FUNCTION_URL to .env",
                "error_type": "ConfigurationError",
                "screenshots": [],
                "tool_calls": [],
                "checkpoints": [],
                "execution_time": 0
            }
        
        if self.backend == "browserbase":
            return await self._execute_browserbase(prompt, agent_config, constraints)
        else:
            return await self._execute_lambda(prompt, agent_config, constraints)
    
    async def _execute_browserbase(
        self,
        prompt: str,
        agent_config: Dict[str, Any],
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute via BrowserBase."""
        try:
            from browserbase_client import BrowserBaseClient
            
            client = BrowserBaseClient()
            result = await client.execute_agent_task(
                prompt=prompt,
                agent_config=agent_config,
                constraints=constraints,
                screenshot_interval=2.0
            )
            
            return result
            
        except Exception as e:
            print(f"❌ BrowserBase execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "screenshots": [],
                "tool_calls": [],
                "checkpoints": [],
                "execution_time": 0
            }
    
    async def _execute_lambda(
        self,
        prompt: str,
        agent_config: Dict[str, Any],
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute via AWS Lambda."""
        try:
            from utils.lambda_client import invoke_agent_execution
            
            result = await invoke_agent_execution(
                prompt=prompt,
                agent_config=agent_config,
                constraints=constraints
            )
            
            return result
            
        except Exception as e:
            print(f"❌ Lambda execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "screenshots": [],
                "tool_calls": [],
                "checkpoints": [],
                "execution_time": 0
            }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the configured backend."""
        return {
            "backend": self.backend,
            "browserbase_available": self.browserbase_available,
            "lambda_available": self.lambda_available,
            "status": "ready" if self.backend else "not_configured"
        }


# Singleton instance
_client = None

def get_browser_client() -> BrowserExecutionClient:
    """Get the singleton browser execution client."""
    global _client
    if _client is None:
        _client = BrowserExecutionClient()
    return _client


# For backward compatibility
async def execute_agent(
    prompt: str,
    agent_config: Dict[str, Any],
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute an agent task (convenience function)."""
    client = get_browser_client()
    return await client.execute_agent(prompt, agent_config, constraints)

