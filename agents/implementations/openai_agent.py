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
        Execute a task using GPT-4 with function calling.
        """
        start_time = time.time()
        self._is_executing = True
        self._initialize_client()
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Agent initialized and ready", "completed")
            await asyncio.sleep(0.5)
            
            # Checkpoint 2: Planning
            self._add_checkpoint("planning", "Analyzing task and creating execution plan", "in_progress")
            
            # Build system prompt
            system_prompt = """You are a web automation agent. You can navigate websites, click elements, 
            fill forms, and extract data. Break down the user's task into steps and use the available 
            tools to accomplish it. Think step by step."""
            
            if constraints:
                if "domains" in constraints:
                    system_prompt += f"\n\nYou must only visit these domains: {constraints['domains']}"
                if "schema" in constraints:
                    system_prompt += f"\n\nReturn data in this format: {json.dumps(constraints['schema'])}"
            
            # Make initial API call
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._get_browser_tools(),
                tool_choice="auto",
                max_tokens=1000
            )
            
            self._add_checkpoint("planning", "Execution plan created", "completed")
            await asyncio.sleep(0.3)
            
            # Checkpoint 3: Execution
            self._add_checkpoint("execution", "Executing browser actions", "in_progress")
            
            # Handle tool calls
            message = response.choices[0].message
            final_output = None
            
            # Agent loop: handle tool calls
            max_iterations = 10
            iteration = 0
            
            while message.tool_calls and iteration < max_iterations and self._is_executing:
                iteration += 1
                
                # Execute each tool call
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_params = json.loads(tool_call.function.arguments)
                    
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
                    messages.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                        ]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Get next response
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self._get_browser_tools(),
                    tool_choice="auto",
                    max_tokens=1000
                )
                
                message = response.choices[0].message
            
            # Get final output
            if message.content:
                final_output = message.content
            
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
        # For MVP, return a placeholder
        if self._browser_session_url:
            return self._browser_session_url
        return f"http://localhost:6080/vnc.html?agent={self.agent_id}"

