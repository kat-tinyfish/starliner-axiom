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
        """Execute a task using Claude 3.5 Sonnet with tool use."""
        start_time = time.time()
        self._is_executing = True
        self._initialize_client()
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Agent initialized and ready", "completed")
            await asyncio.sleep(0.5)
            
            # Checkpoint 2: Planning
            self._add_checkpoint("planning", "Analyzing task with advanced reasoning", "in_progress")
            
            # Build system prompt
            system_prompt = """You are a web automation agent with advanced reasoning capabilities. 
            You can navigate websites, interact with elements, and extract information. 
            Think step by step about how to accomplish the task efficiently."""
            
            if constraints:
                if "domains" in constraints:
                    system_prompt += f"\n\nRestrict your navigation to: {constraints['domains']}"
                if "schema" in constraints:
                    system_prompt += f"\n\nFormat output as: {json.dumps(constraints['schema'])}"
            
            # Make initial API call
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.messages.create(
                model=self.model,
                system=system_prompt,
                max_tokens=1024,
                tools=self._get_browser_tools(),
                messages=messages
            )
            
            self._add_checkpoint("planning", "Execution plan created", "completed")
            await asyncio.sleep(0.3)
            
            # Checkpoint 3: Execution
            self._add_checkpoint("execution", "Executing browser actions", "in_progress")
            
            # Agent loop: handle tool use
            max_iterations = 10
            iteration = 0
            final_output = None
            
            while iteration < max_iterations and self._is_executing:
                iteration += 1
                
                # Check if we should stop
                if response.stop_reason == "end_turn":
                    # Extract final text
                    for block in response.content:
                        if hasattr(block, 'text'):
                            final_output = block.text
                    break
                
                # Process tool use
                if response.stop_reason == "tool_use":
                    # Execute each tool
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            tool_params = block.input
                            
                            # Record tool call
                            tc = self._add_tool_call(tool_name, tool_params, "in_progress")
                            
                            # Execute the tool
                            try:
                                result = await self._execute_browser_tool(tool_name, tool_params)
                                self._update_tool_call(tc, "success", result=result)
                            except Exception as e:
                                self._update_tool_call(tc, "error", error_message=str(e))
                                result = {"status": "error", "message": str(e)}
                            
                            # Add tool result to messages
                            messages.append({"role": "assistant", "content": response.content})
                            messages.append({
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": json.dumps(result)
                                    }
                                ]
                            })
                    
                    # Get next response
                    response = await self.client.messages.create(
                        model=self.model,
                        system=system_prompt,
                        max_tokens=1024,
                        tools=self._get_browser_tools(),
                        messages=messages
                    )
                else:
                    break
            
            self._add_checkpoint("execution", "Browser actions completed", "completed")
            await asyncio.sleep(0.3)
            
            # Checkpoint 4: Completion
            self._add_checkpoint("completion", "Task completed successfully", "completed")
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=True,
                output=final_output,
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
