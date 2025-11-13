"""
OpenAI Agent Implementation - GPT-4 Web Agent with Native Function Calling

This agent uses OpenAI's native function calling API to orchestrate browser automation.

Flow:
1. User provides natural language task
2. GPT-4 thinks and decides which browser tools to use
3. Tools are executed via BrowserToolExecutor
4. Results are fed back to GPT-4
5. GPT-4 continues until task is complete
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional, List
import json

from agents.base_agent import BaseAgent, AgentResult
from agents.browser_tools import get_openai_tools
from agents.browser_executor import BrowserToolExecutor


# System prompt for GPT-4 web navigation
SYSTEM_PROMPT = """You are a web navigation agent. Your task is to complete user requests by controlling a web browser.

You have access to these browser tools:
- navigate: Go to a URL
- click: Click an element (use CSS selectors or text:)
- type_text: Type into input fields
- extract_content: Read text or attributes from elements
- get_page_info: Get current page title/URL
- scroll: Scroll the page
- wait: Wait for elements or time
- go_back: Navigate back
- screenshot: Capture the page

Important guidelines:
1. Always start by navigating to the target URL
2. Use get_page_info to understand where you are
3. Use extract_content to read page content before making decisions
4. Be methodical - one step at a time
5. If you encounter errors, try alternative approaches
6. When task is complete, summarize what you did

Think step-by-step and use tools strategically to accomplish the goal."""


class OpenAIAgent(BaseAgent):
    """
    Web agent powered by OpenAI's GPT-4 with native function calling.
    
    Uses GPT-4 to think, plan, and orchestrate browser automation via tool calls.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: str, model: str = "gpt-4-turbo"):
        super().__init__(agent_id, name, api_key)
        self.model = model
        self._is_executing = False
        self.client = None
    
    def _initialize_client(self):
        """Initialize OpenAI client."""
        if not self.client:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute a task using GPT-4's native function calling with browser automation.
        
        Flow:
        1. User task → GPT-4 thinks
        2. GPT-4 chooses browser tools → Execute via Playwright
        3. Results → Back to GPT-4
        4. Repeat until task complete
        5. Return final result
        """
        start_time = time.time()
        self._is_executing = True
        
        # Initialize OpenAI client
        self._initialize_client()
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Initializing GPT-4 agent", "completed")
            
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
                self._add_checkpoint("planning", "GPT-4 analyzing task and planning approach", "completed")
                
                # Initialize conversation with system prompt
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": self._build_user_prompt(prompt, constraints)}
                ]
                
                # Tool calling loop - let GPT-4 orchestrate
                max_iterations = 15
                final_response = None
                
                for iteration in range(max_iterations):
                    print(f"\n🤖 GPT-4 Iteration {iteration + 1}/{max_iterations}")
                    
                    # Ask GPT-4 what to do next
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=get_openai_tools(),
                        tool_choice="auto",
                        temperature=0.7
                    )
                    
                    assistant_message = response.choices[0].message
                    messages.append(assistant_message)
                    
                    # Check if GPT-4 wants to use tools
                    if assistant_message.tool_calls:
                        # GPT-4 has chosen tools to execute
                        print(f"   🔧 GPT-4 chose {len(assistant_message.tool_calls)} tool(s)")
                        
                        # Execute each tool call
                        for tool_call in assistant_message.tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)
                            
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
                            
                            # Add tool result back to conversation
                            tool_result_message = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({
                                    "success": result.success,
                                    "data": result.data,
                                    "error": result.error,
                                    "execution_time": result.execution_time
                                }, indent=2)
                            }
                            messages.append(tool_result_message)
                            
                            print(f"   ✅ Result: {result.success}")
                            if result.error:
                                print(f"   ⚠️  Error: {result.error}")
                    
                    else:
                        # GPT-4 says task is complete (no more tool calls)
                        print("   ✅ GPT-4 says task is complete!")
                        final_response = assistant_message.content
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
            print(f"❌ Error in OpenAI agent execution: {str(e)}")
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

