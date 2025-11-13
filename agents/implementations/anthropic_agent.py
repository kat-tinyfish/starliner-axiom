"""
Anthropic Agent Implementation - Claude 3.5 Sonnet with Native Tool Use

This agent uses Claude's native tool use API to orchestrate browser automation.

Flow:
1. User provides natural language task
2. Claude thinks and decides which browser tools to use
3. Tools are executed via BrowserToolExecutor
4. Results are fed back to Claude
5. Claude continues until task is complete
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional, List
import json

from agents.base_agent import BaseAgent, AgentResult
from agents.browser_tools import get_anthropic_tools
from agents.browser_executor import BrowserToolExecutor


# System prompt for Claude web navigation
SYSTEM_PROMPT = """You are a helpful web automation assistant. Your task is to complete user requests by controlling a web browser.

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

Strategy for success:
1. Start by navigating to the target website
2. Use get_page_info to understand where you are
3. Use extract_content to read page content before deciding actions
4. Break complex tasks into simple steps
5. If something fails, try alternative approaches
6. When complete, explain what you accomplished

You're excellent at web navigation - use your tools methodically to help users!"""


class AnthropicAgent(BaseAgent):
    """
    Web agent powered by Anthropic's Claude 3.5 Sonnet with native tool use.
    
    Uses Claude to think, plan, and orchestrate browser automation via tool use.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        super().__init__(agent_id, name, api_key)
        self.model = model
        self._is_executing = False
        self.client = None
    
    def _initialize_client(self):
        """Initialize Anthropic client."""
        if not self.client:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
    
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute a task using Claude's native tool use with browser automation.
        
        Flow:
        1. User task → Claude thinks
        2. Claude chooses browser tools → Execute via Playwright
        3. Results → Back to Claude
        4. Repeat until task complete
        5. Return final result
        """
        start_time = time.time()
        self._is_executing = True
        
        # Initialize Anthropic client
        self._initialize_client()
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Initializing Claude agent", "completed")
            
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
                self._add_checkpoint("planning", "Claude analyzing task and planning approach", "completed")
                
                # Initialize conversation
                messages = [
                    {"role": "user", "content": self._build_user_prompt(prompt, constraints)}
                ]
                
                # Tool calling loop - let Claude orchestrate
                max_iterations = 15
                final_response = None
                
                for iteration in range(max_iterations):
                    print(f"\n🤖 Claude Iteration {iteration + 1}/{max_iterations}")
                    
                    # Ask Claude what to do next
                    response = await self.client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        system=SYSTEM_PROMPT,
                        messages=messages,
                        tools=get_anthropic_tools(),
                        temperature=0.7
                    )
                    
                    # Add assistant response to conversation
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    
                    # Check if Claude wants to use tools
                    tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
                    
                    if tool_use_blocks:
                        # Claude has chosen tools to execute
                        print(f"   🔧 Claude chose {len(tool_use_blocks)} tool(s)")
                        
                        # Execute each tool and collect results
                        tool_results = []
                        
                        for tool_use in tool_use_blocks:
                            tool_name = tool_use.name
                            tool_args = tool_use.input
                            tool_id = tool_use.id
                            
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
                            
                            # Prepare tool result for Claude
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": json.dumps({
                                    "success": result.success,
                                    "data": result.data,
                                    "error": result.error,
                                    "execution_time": result.execution_time
                                }, indent=2)
                            })
                            
                            print(f"   ✅ Result: {result.success}")
                            if result.error:
                                print(f"   ⚠️  Error: {result.error}")
                        
                        # Send tool results back to Claude as a user message
                        messages.append({
                            "role": "user",
                            "content": tool_results
                        })
                    
                    else:
                        # Claude says task is complete (no more tool use blocks)
                        print("   ✅ Claude says task is complete!")
                        # Extract text from content blocks
                        text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
                        final_response = '\n'.join(text_blocks)
                        break
                    
                    # Check if we should stop
                    if not self._is_executing:
                        print("   ⏸️  Execution stopped by user")
                        break
                    
                    # Check stop reason
                    if response.stop_reason == "end_turn":
                        # Claude is done without tool use
                        text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
                        final_response = '\n'.join(text_blocks)
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
            print(f"❌ Error in Anthropic agent execution: {str(e)}")
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
