"""
OpenAI Agent Implementation - GPT-4 Web Agent
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
import json

from agents.base_agent import BaseAgent, AgentResult


class OpenAIAgent(BaseAgent):
    """
    Web agent powered by OpenAI's GPT-4.
    
    Uses OpenAI's function calling to interact with browser tools.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: str, model: str = "gpt-4-turbo"):
        super().__init__(agent_id, name, api_key)
        self.model = model
        self._is_executing = False
        self._browser_session_url = None
        self.client = None
    
    def _initialize_client(self):
        """Initialize OpenAI client."""
        if not self.client:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    def _get_browser_tools(self) -> List[Dict[str, Any]]:
        """Get available browser tools for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "navigate_to",
                    "description": "Navigate the browser to a URL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "The URL to navigate to"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "click_element",
                    "description": "Click on a page element",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector or text of element to click"}
                        },
                        "required": ["selector"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "type_text",
                    "description": "Type text into an input field",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector of the input field"},
                            "text": {"type": "string", "description": "Text to type"}
                        },
                        "required": ["selector", "text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_data",
                    "description": "Extract data from the current page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector to extract data from"},
                            "attribute": {"type": "string", "description": "Attribute to extract (text, href, src, etc.)"}
                        },
                        "required": ["selector"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description": "Take a screenshot of the current page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "full_page": {"type": "boolean", "description": "Whether to capture full page or viewport only"}
                        }
                    }
                }
            }
        ]
    
    async def _execute_browser_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a browser tool.
        
        For MVP, this simulates browser actions. In production, this would
        call the AWS Lambda function to control the actual browser.
        """
        # Simulate execution delay
        await asyncio.sleep(0.5)
        
        # Simulate different tool responses
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
        Execute a task using GPT-4 with browser automation.
        
        This delegates actual browser control to BrowserBase/Lambda while
        GPT-4 provides the intelligence for decision-making.
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
        # For MVP, return a placeholder
        if self._browser_session_url:
            return self._browser_session_url
        return f"http://localhost:6080/vnc.html?agent={self.agent_id}"

