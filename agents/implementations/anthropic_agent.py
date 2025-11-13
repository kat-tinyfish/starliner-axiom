"""
Anthropic Agent Implementation - Claude 3.5 Sonnet Web Agent
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
import json

from agents.base_agent import BaseAgent, AgentResult


class AnthropicAgent(BaseAgent):
    """
    Web agent powered by Anthropic's Claude 3.5 Sonnet.
    
    Uses Claude's tool use (function calling) to interact with browser tools.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(agent_id, name, api_key)
        self.model = model
        self._is_executing = False
        self._browser_session_url = None
        self.client = None
    
    def _initialize_client(self):
        """Initialize Anthropic client."""
        if not self.client:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
    
    def _get_browser_tools(self) -> List[Dict[str, Any]]:
        """Get available browser tools for Claude's tool use."""
        return [
            {
                "name": "navigate_to",
                "description": "Navigate the browser to a URL",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to navigate to"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "click_element",
                "description": "Click on a page element",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector or text of element to click"}
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "type_text",
                "description": "Type text into an input field",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector of the input field"},
                        "text": {"type": "string", "description": "Text to type"}
                    },
                    "required": ["selector", "text"]
                }
            },
            {
                "name": "extract_data",
                "description": "Extract data from the current page",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector to extract data from"},
                        "attribute": {"type": "string", "description": "Attribute to extract (text, href, src, etc.)"}
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "take_screenshot",
                "description": "Take a screenshot of the current page",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "full_page": {"type": "boolean", "description": "Whether to capture full page or viewport only"}
                    }
                }
            }
        ]
    
    async def _execute_browser_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a browser tool (simulated for MVP)."""
        await asyncio.sleep(0.5)
        
        if tool_name == "navigate_to":
            return {"status": "success", "url": parameters.get("url")}
        elif tool_name == "click_element":
            return {"status": "success", "selector": parameters.get("selector")}
        elif tool_name == "type_text":
            return {"status": "success", "text": parameters.get("text")}
        elif tool_name == "extract_data":
            return {"status": "success", "data": "Sample extracted data"}
        elif tool_name == "take_screenshot":
            return {"status": "success", "screenshot_url": "/screenshots/demo.png"}
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
    
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute a task using Claude 3.5 Sonnet with browser automation.
        
        This delegates actual browser control to BrowserBase/Lambda while
        Claude provides the intelligence for decision-making.
        """
        start_time = time.time()
        self._is_executing = True
        
        try:
            # Import browser client
            from utils.browser_client import get_browser_client
            
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Agent initialized and ready", "completed")
            await asyncio.sleep(0.3)
            
            # Checkpoint 2: Planning
            self._add_checkpoint("planning", "Delegating to browser execution engine", "completed")
            await asyncio.sleep(0.2)
            
            # Execute via browser client (BrowserBase or Lambda)
            browser_client = get_browser_client()
            
            # Prepare agent config
            agent_config = {
                "agent_id": self.agent_id,
                "model": self.model,
                "name": self.name
            }
            
            # Execute the task
            browser_result = await browser_client.execute_agent(
                prompt=prompt,
                agent_config=agent_config,
                constraints=constraints
            )
            
            # Merge browser execution results with our agent tracking
            if browser_result.get("checkpoints"):
                for cp_data in browser_result["checkpoints"]:
                    self._add_checkpoint(
                        cp_data.get("name", "step"),
                        cp_data.get("description", ""),
                        cp_data.get("status", "completed")
                    )
            
            if browser_result.get("tool_calls"):
                for tc_data in browser_result["tool_calls"]:
                    self._add_tool_call(
                        tc_data.get("tool", "action"),
                        tc_data.get("args", {}),
                        tc_data.get("status", "success")
                    )
            
            # Final checkpoint
            if browser_result.get("success"):
                self._add_checkpoint("completion", "Task completed successfully", "completed")
            else:
                self._add_checkpoint("error", f"Task failed: {browser_result.get('error', 'Unknown error')}", "error")
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=browser_result.get("success", False),
                output=browser_result.get("output_data", {}),
                execution_time=execution_time,
                tool_calls=self._tool_calls,
                checkpoints=self._checkpoints,
                screenshots=browser_result.get("screenshots", [])
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
                checkpoints=self._checkpoints,
                screenshots=[]
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
