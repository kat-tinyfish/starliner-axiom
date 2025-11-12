"""
Google Agent Implementation - Gemini 2.0 Flash Web Agent
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
import json

from agents.base_agent import BaseAgent, AgentResult


class GoogleAgent(BaseAgent):
    """
    Web agent powered by Google's Gemini 2.0 Flash.
    
    Uses Gemini's function calling to interact with browser tools.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: str, model: str = "gemini-2.0-flash-exp"):
        super().__init__(agent_id, name, api_key)
        self.model = model
        self._is_executing = False
        self._browser_session_url = None
        self.client = None
    
    def _initialize_client(self):
        """Initialize Google Generative AI client."""
        if not self.client:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
    
    def _get_browser_tools(self) -> List:
        """Get available browser tools for Gemini's function calling."""
        import google.generativeai as genai
        
        navigate_to = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name="navigate_to",
                    description="Navigate the browser to a URL",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "url": genai.protos.Schema(type=genai.protos.Type.STRING, description="The URL to navigate to")
                        },
                        required=["url"]
                    )
                )
            ]
        )
        
        click_element = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name="click_element",
                    description="Click on a page element",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "selector": genai.protos.Schema(type=genai.protos.Type.STRING, description="CSS selector or text of element to click")
                        },
                        required=["selector"]
                    )
                )
            ]
        )
        
        type_text = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name="type_text",
                    description="Type text into an input field",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "selector": genai.protos.Schema(type=genai.protos.Type.STRING, description="CSS selector of the input field"),
                            "text": genai.protos.Schema(type=genai.protos.Type.STRING, description="Text to type")
                        },
                        required=["selector", "text"]
                    )
                )
            ]
        )
        
        extract_data = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name="extract_data",
                    description="Extract data from the current page",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "selector": genai.protos.Schema(type=genai.protos.Type.STRING, description="CSS selector to extract data from"),
                            "attribute": genai.protos.Schema(type=genai.protos.Type.STRING, description="Attribute to extract")
                        },
                        required=["selector"]
                    )
                )
            ]
        )
        
        take_screenshot = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name="take_screenshot",
                    description="Take a screenshot of the current page",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "full_page": genai.protos.Schema(type=genai.protos.Type.BOOLEAN, description="Whether to capture full page")
                        }
                    )
                )
            ]
        )
        
        return [navigate_to, click_element, type_text, extract_data, take_screenshot]
    
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
        """Execute a task using Gemini 2.0 Flash with function calling."""
        start_time = time.time()
        self._is_executing = True
        self._initialize_client()
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Agent initialized and ready", "completed")
            await asyncio.sleep(0.5)
            
            # Checkpoint 2: Planning
            self._add_checkpoint("planning", "Analyzing task with multimodal understanding", "in_progress")
            
            # Build system instruction
            system_instruction = """You are a web automation agent with multimodal capabilities. 
            You can navigate websites, interact with elements, and extract information. 
            Be efficient and systematic in your approach."""
            
            if constraints:
                if "domains" in constraints:
                    system_instruction += f"\n\nOnly visit these domains: {constraints['domains']}"
                if "schema" in constraints:
                    system_instruction += f"\n\nFormat output as: {json.dumps(constraints['schema'])}"
            
            # Start chat with tools
            chat = self.client.start_chat(enable_automatic_function_calling=False)
            
            # Send initial message
            response = await asyncio.to_thread(
                chat.send_message,
                f"{system_instruction}\n\n{prompt}",
                tools=self._get_browser_tools()
            )
            
            self._add_checkpoint("planning", "Execution plan created", "completed")
            await asyncio.sleep(0.3)
            
            # Checkpoint 3: Execution
            self._add_checkpoint("execution", "Executing browser actions", "in_progress")
            
            # Agent loop: handle function calls
            max_iterations = 10
            iteration = 0
            final_output = None
            
            while iteration < max_iterations and self._is_executing:
                iteration += 1
                
                # Check for function calls
                if response.candidates[0].content.parts:
                    function_calls = [
                        part.function_call for part in response.candidates[0].content.parts 
                        if hasattr(part, 'function_call') and part.function_call
                    ]
                    
                    if not function_calls:
                        # No more function calls, extract final text
                        final_output = response.text
                        break
                    
                    # Execute each function call
                    function_responses = []
                    
                    for function_call in function_calls:
                        tool_name = function_call.name
                        tool_params = dict(function_call.args)
                        
                        # Record tool call
                        tc = self._add_tool_call(tool_name, tool_params, "in_progress")
                        
                        # Execute the tool
                        try:
                            result = await self._execute_browser_tool(tool_name, tool_params)
                            self._update_tool_call(tc, "success", result=result)
                        except Exception as e:
                            self._update_tool_call(tc, "error", error_message=str(e))
                            result = {"status": "error", "message": str(e)}
                        
                        # Add function response
                        import google.generativeai as genai
                        function_responses.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={"result": result}
                                )
                            )
                        )
                    
                    # Send function responses and get next response
                    response = await asyncio.to_thread(
                        chat.send_message,
                        function_responses
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
