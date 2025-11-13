"""
Google Agent Implementation - Gemini 2.0 Flash with Native Function Calling

This agent uses Google's Gemini native function calling API to orchestrate browser automation.

Flow:
1. User provides natural language task
2. Gemini thinks and decides which browser tools to use
3. Tools are executed via BrowserToolExecutor
4. Results are fed back to Gemini
5. Gemini continues until task is complete
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional, List
import json

from agents.base_agent import BaseAgent, AgentResult
from agents.browser_tools import get_google_tools, BROWSER_TOOLS
from agents.browser_executor import BrowserToolExecutor


# System instruction for Gemini web navigation
SYSTEM_INSTRUCTION = """You are a web navigation agent. Your task is to complete user requests by controlling a web browser.

You have access to browser tools for navigation, clicking, typing, extracting data, and more.

Guidelines:
1. Always start by navigating to the target website
2. Use get_page_info to understand where you are
3. Extract content before making decisions
4. Break complex tasks into simple steps
5. Try alternative approaches if something fails
6. Summarize your accomplishment when done

Be methodical and strategic in using your tools to complete tasks successfully."""


class GoogleAgent(BaseAgent):
    """
    Web agent powered by Google's Gemini 2.0 Flash with native function calling.
    
    Uses Gemini to think, plan, and orchestrate browser automation via function calls.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: str, model: str = "gemini-2.0-flash-exp"):
        super().__init__(agent_id, name, api_key)
        self.model = model
        self._is_executing = False
        self.model_instance = None
    
    def _initialize_client(self):
        """Initialize Google Generative AI client."""
        if not self.model_instance:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # Convert our universal tools to Gemini format
            tool_declarations = []
            for tool in BROWSER_TOOLS:
                tool_declarations.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                })
            
            # Create model with tools
            self.model_instance = genai.GenerativeModel(
                model_name=self.model,
                tools=tool_declarations,
                system_instruction=SYSTEM_INSTRUCTION
            )
    
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute a task using Gemini's native function calling with browser automation.
        
        Flow:
        1. User task → Gemini thinks
        2. Gemini chooses browser tools → Execute via Playwright
        3. Results → Back to Gemini
        4. Repeat until task complete
        5. Return final result
        """
        start_time = time.time()
        self._is_executing = True
        
        # Initialize Gemini client
        self._initialize_client()
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Initializing Gemini agent", "completed")
            
            # Get BrowserBase connection
            browserbase_session = await self._create_browserbase_session()
            
            # Checkpoint 2: Browser Ready
            self._add_checkpoint("browser_ready", "Browser session created", "completed")
            
            # Initialize browser executor with BrowserBase
            async with BrowserToolExecutor(
                browserbase_session_id=browserbase_session["id"],
                browserbase_connect_url=browserbase_session["connect_url"]
            ) as executor:
                
                # Checkpoint 3: Planning
                self._add_checkpoint("planning", "Gemini analyzing task and planning approach", "completed")
                
                # Start chat session
                chat = self.model_instance.start_chat(enable_automatic_function_calling=False)
                
                # Send initial prompt
                user_prompt = self._build_user_prompt(prompt, constraints)
                
                # Tool calling loop - let Gemini orchestrate
                max_iterations = 15
                final_response = None
                current_prompt = user_prompt
                
                for iteration in range(max_iterations):
                    print(f"\n🤖 Gemini Iteration {iteration + 1}/{max_iterations}")
                    
                    # Ask Gemini what to do next
                    response = await asyncio.to_thread(
                        chat.send_message,
                        current_prompt
                    )
                    
                    # Check if Gemini wants to use functions
                    if response.candidates[0].content.parts:
                        function_calls = [
                            part.function_call
                            for part in response.candidates[0].content.parts
                            if hasattr(part, 'function_call') and part.function_call
                        ]
                        
                        if function_calls:
                            # Gemini has chosen tools to execute
                            print(f"   🔧 Gemini chose {len(function_calls)} tool(s)")
                            
                            # Execute each function call and collect results
                            function_responses = []
                            
                            for function_call in function_calls:
                                tool_name = function_call.name
                                tool_args = dict(function_call.args)
                                
                                print(f"   ⚙️  Executing: {tool_name}({json.dumps(tool_args, indent=2)})")
                                
                                # Execute the tool via browser executor
                                result = await executor.execute_tool(tool_name, tool_args)
                                
                                # Track tool call
                                self._add_tool_call(
                                    tool=tool_name,
                                    args=tool_args,
                                    status="success" if result.success else "error"
                                )
                                
                                # Track screenshot
                                if result.screenshot:
                                    self._screenshots.append({
                                        "index": len(self._screenshots),
                                        "timestamp": time.time(),
                                        "elapsed": time.time() - start_time,
                                        "data": result.screenshot
                                    })
                                
                                # Prepare function response for Gemini
                                import google.generativeai as genai
                                function_responses.append(
                                    genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=tool_name,
                                            response={
                                                "success": result.success,
                                                "data": result.data,
                                                "error": result.error,
                                                "execution_time": result.execution_time
                                            }
                                        )
                                    )
                                )
                                
                                print(f"   ✅ Result: {result.success}")
                                if result.error:
                                    print(f"   ⚠️  Error: {result.error}")
                            
                            # Send function results back to Gemini
                            import google.generativeai as genai
                            current_prompt = genai.protos.Content(parts=function_responses)
                        
                        else:
                            # Gemini provided text response (task complete)
                            print("   ✅ Gemini says task is complete!")
                            text_parts = [
                                part.text
                                for part in response.candidates[0].content.parts
                                if hasattr(part, 'text')
                            ]
                            final_response = '\n'.join(text_parts)
                            break
                    
                    else:
                        # No content parts, task complete
                        print("   ✅ Gemini finished")
                        final_response = "Task completed"
                        break
                    
                    # Check if we should stop
                    if not self._is_executing:
                        print("   ⏸️  Execution stopped by user")
                        break
                
                # Checkpoint 4: Completion
                if final_response:
                    self._add_checkpoint("completion", "Task completed successfully", "completed")
                else:
                    self._add_checkpoint("completion", "Reached maximum iterations", "completed")
                
                # Extract final output
                output_data = {
                    "summary": final_response or "Task execution completed",
                    "iterations": iteration + 1,
                    "tool_calls_count": len(self._tool_calls)
                }
                
                execution_time = time.time() - start_time
                
                return AgentResult(
                    success=True,
                    output=output_data,
                    execution_time=execution_time,
                    tool_calls=self._tool_calls,
                    checkpoints=self._checkpoints,
                    screenshots=self._screenshots
                )
        
        except Exception as e:
            print(f"❌ Error in Google agent execution: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self._add_checkpoint("error", f"Execution failed: {str(e)}", "error")
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=False,
                output=None,
                error_message=str(e),
                execution_time=execution_time,
                tool_calls=self._tool_calls,
                checkpoints=self._checkpoints,
                screenshots=self._screenshots
            )
        finally:
            self._is_executing = False
    
    def _build_user_prompt(self, prompt: str, constraints: Optional[Dict[str, Any]]) -> str:
        """Build the user prompt with task and constraints."""
        user_prompt = f"Task: {prompt}\n"
        
        if constraints:
            if constraints.get("domains"):
                user_prompt += f"\nDomain hints: {', '.join(constraints['domains'])}"
            if constraints.get("json_schema"):
                user_prompt += f"\nExpected output format: {json.dumps(constraints['json_schema'])}"
        
        return user_prompt
    
    async def _create_browserbase_session(self) -> Dict[str, Any]:
        """Create a BrowserBase session for browser control."""
        try:
            # Import BrowserBase client
            import sys
            from pathlib import Path
            lambda_dir = Path(__file__).parent.parent.parent / "lambda"
            sys.path.insert(0, str(lambda_dir))
            
            from browserbase_client import BrowserBaseClient
            
            client = BrowserBaseClient()
            session = await client.create_session()
            
            return {
                "id": session["id"],
                "connect_url": session.get("connectUrl")
            }
        
        except Exception as e:
            print(f"⚠️  Failed to create BrowserBase session: {e}")
            # Return mock session for testing without BrowserBase
            return {
                "id": "mock-session",
                "connect_url": None
            }
    
    def stop_execution(self) -> None:
        """Stop the current execution."""
        self._is_executing = False
