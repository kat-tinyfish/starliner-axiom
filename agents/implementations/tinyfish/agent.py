"""
TinyFish Agent Implementation - Custom Web Agent
"""

import asyncio
import time
from typing import Dict, Any, Optional
import json

from agents.base_agent import BaseAgent, AgentResult


class TinyFishAgent(BaseAgent):
    """
    Custom TinyFish web agent with specialized capabilities.
    
    This is a custom agent that can be extended with domain-specific logic.
    For MVP, uses a simple API-based approach similar to other agents.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: str, endpoint: Optional[str] = None):
        super().__init__(agent_id, name, api_key)
        self.endpoint = endpoint or "https://api.tinyfish.ai/v1/agent"
        self._is_executing = False
        self._browser_session_url = None
    
    async def _make_api_call(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make API call to TinyFish agent endpoint.
        
        For MVP, this is a placeholder. In production, this would call the actual TinyFish API.
        """
        import aiohttp
        
        # Simulate API call delay
        await asyncio.sleep(1.0)
        
        # For MVP, return a mock response
        # In production, this would be:
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(
        #         self.endpoint,
        #         headers={"Authorization": f"Bearer {self.api_key}"},
        #         json={"prompt": prompt, "constraints": constraints}
        #     ) as response:
        #         return await response.json()
        
        return {
            "success": True,
            "actions": [
                {"type": "navigate", "url": "https://example.com"},
                {"type": "click", "selector": "#search-button"},
                {"type": "type", "selector": "#input-field", "text": "search query"},
                {"type": "extract", "selector": ".results", "data": "Sample data"}
            ],
            "output": "TinyFish agent completed the task successfully."
        }
    
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Execute a task using the TinyFish agent."""
        start_time = time.time()
        self._is_executing = True
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "TinyFish agent initialized", "completed")
            await asyncio.sleep(0.5)
            
            # Checkpoint 2: Planning
            self._add_checkpoint("planning", "Creating specialized execution plan", "in_progress")
            
            # Make API call to TinyFish agent
            api_response = await self._make_api_call(prompt, constraints)
            
            self._add_checkpoint("planning", "Execution plan created", "completed")
            await asyncio.sleep(0.3)
            
            # Checkpoint 3: Execution
            self._add_checkpoint("execution", "Executing specialized actions", "in_progress")
            
            # Execute actions from API response
            if api_response.get("actions"):
                for action in api_response["actions"]:
                    if not self._is_executing:
                        break
                    
                    action_type = action.get("type", "unknown")
                    
                    # Record tool call
                    tc = self._add_tool_call(action_type, action, "in_progress")
                    
                    # Simulate execution
                    await asyncio.sleep(0.5)
                    
                    # Update tool call status
                    self._update_tool_call(tc, "success", result={"status": "completed"})
            
            self._add_checkpoint("execution", "Actions completed", "completed")
            await asyncio.sleep(0.3)
            
            # Checkpoint 4: Completion
            self._add_checkpoint("completion", "Task completed successfully", "completed")
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=api_response.get("success", True),
                output=api_response.get("output"),
                execution_time=execution_time,
                tool_calls=self._tool_calls,
                checkpoints=self._checkpoints
            )
        
        except Exception as e:
            self._add_checkpoint("error", f"Execution failed: {str(e)}", "error")
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=False,
                output=None,
                error_message=str(e),
                execution_time=execution_time,
                tool_calls=self._tool_calls,
                checkpoints=self._checkpoints
            )
        finally:
            self._is_executing = False
    
    def stop_execution(self) -> None:
        """Stop the current execution."""
        self._is_executing = False
    
    def get_browser_session_url(self) -> str:
        """Get the VNC stream URL for the browser session."""
        if self._browser_session_url:
            return self._browser_session_url
        return f"http://localhost:6080/vnc.html?agent={self.agent_id}"
