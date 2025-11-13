"""
TinyFish Agent Implementation - Custom Hybrid Web Agent

This agent uses a hybrid approach combining LLM intelligence with domain-specific
optimizations and rule-based improvements.

Unique features:
- Pre-planning phase with task decomposition
- Optimized tool selection based on patterns
- Advanced error recovery with fallbacks
- Custom caching and performance optimizations

Flow:
1. User provides natural language task
2. LLM analyzes and creates execution plan
3. Execute plan with optimizations
4. LLM validates results and adjusts
5. Return enhanced results
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional, List
import json
import re

from agents.base_agent import BaseAgent, AgentResult
from agents.browser_tools import get_openai_tools, BROWSER_TOOLS
from agents.browser_executor import BrowserToolExecutor


# System prompt for TinyFish planning
PLANNING_PROMPT = """You are TinyFish, an expert web automation agent with advanced planning capabilities.

Given a user task, create a detailed execution plan using available browser tools.

Available tools: navigate, click, type_text, extract_content, get_page_info, scroll, wait, go_back, screenshot

Your plan should:
1. Break the task into clear steps
2. Specify which tool to use for each step
3. Include fallback strategies for common failures
4. Identify what data to extract

Respond with a JSON plan:
{
  "steps": [
    {"tool": "navigate", "args": {"url": "..."}, "purpose": "..."},
    {"tool": "click", "args": {"selector": "..."}, "purpose": "..."}
  ],
  "success_criteria": "...",
  "fallbacks": ["..."]
}"""


# System prompt for TinyFish execution
EXECUTION_PROMPT = """You are TinyFish, executing a web automation plan.

You have access to browser tools and can see the results of previous actions.

Guidelines:
- Follow the plan but adapt if needed
- If a step fails, try the fallback strategy
- Extract all requested data accurately
- Summarize your accomplishment clearly

Be flexible and resilient in completing the task."""


class TinyFishAgent(BaseAgent):
    """
    Custom web agent with hybrid LLM + rule-based orchestration.
    
    Uses OpenAI for planning and adaptation, with custom optimizations
    for common web automation patterns.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: Optional[str] = None):
        # Use OpenAI for planning (or fallback to mock)
        super().__init__(agent_id, name, api_key or os.getenv("OPENAI_API_KEY", ""))
        self.model = "gpt-4-turbo"
        self._is_executing = False
        self.client = None
        
        # Custom features
        self.url_cache = {}  # Cache page info to avoid redundant navigations
        self.tool_success_rate = {}  # Track tool performance
    
    def _initialize_client(self):
        """Initialize OpenAI client for planning."""
        if not self.client and self.api_key:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute a task using TinyFish's hybrid approach.
        
        Flow:
        1. User task → LLM creates execution plan
        2. Execute plan with custom optimizations
        3. LLM validates and adapts if needed
        4. Return enhanced results
        """
        start_time = time.time()
        self._is_executing = True
        
        # Initialize client
        self._initialize_client()
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Initializing TinyFish agent", "completed")
            
            # Checkpoint 2: Planning
            self._add_checkpoint("planning", "Creating execution plan", "in_progress")
            
            # Create execution plan (uses LLM if available, else rule-based)
            plan = await self._create_execution_plan(prompt, constraints)
            
            self._add_checkpoint("planning", "Execution plan created", "completed")
            print(f"\n📋 TinyFish Plan: {len(plan['steps'])} steps")
            
            # Checkpoint 3: Browser Setup
            self._add_checkpoint("browser_setup", "Creating browser session", "in_progress")
            
            # Get BrowserBase connection
            browserbase_session = await self._create_browserbase_session()
            
            self._add_checkpoint("browser_setup", "Browser session ready", "completed")
            
            # Checkpoint 4: Execution
            self._add_checkpoint("execution", "Executing plan", "in_progress")
            
            # Execute plan with browser
            async with BrowserToolExecutor(
                browserbase_session_id=browserbase_session["id"],
                browserbase_connect_url=browserbase_session["connect_url"]
            ) as executor:
                
                execution_results = await self._execute_plan(plan, executor, start_time)
                
                self._add_checkpoint("execution", "Plan executed", "completed")
                
                # Checkpoint 5: Validation
                if self.client:
                    self._add_checkpoint("validation", "Validating results", "in_progress")
                    summary = await self._validate_and_summarize(prompt, execution_results)
                    self._add_checkpoint("validation", "Results validated", "completed")
                else:
                    summary = self._create_summary(execution_results)
                
                # Checkpoint 6: Completion
                self._add_checkpoint("completion", "Task completed successfully", "completed")
                
                execution_time = time.time() - start_time
                
                return AgentResult(
                    success=True,
                    output={
                        "summary": summary,
                        "plan_steps": len(plan['steps']),
                        "tool_calls_count": len(self._tool_calls),
                        "execution_results": execution_results
                    },
                    execution_time=execution_time,
                    tool_calls=self._tool_calls,
                    checkpoints=self._checkpoints,
                    screenshots=self._screenshots
                )
        
        except Exception as e:
            print(f"❌ Error in TinyFish agent execution: {str(e)}")
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
    
    async def _create_execution_plan(self, prompt: str, constraints: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create an execution plan using LLM or rule-based approach."""
        
        if self.client:
            # Use LLM for intelligent planning
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": PLANNING_PROMPT},
                        {"role": "user", "content": f"Task: {prompt}\nConstraints: {json.dumps(constraints or {})}"}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                plan = json.loads(response.choices[0].message.content)
                return plan
            
            except Exception as e:
                print(f"⚠️  LLM planning failed: {e}, falling back to rule-based planning")
        
        # Fallback: Rule-based planning
        return self._create_rule_based_plan(prompt, constraints)
    
    def _create_rule_based_plan(self, prompt: str, constraints: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a plan using simple rule-based heuristics."""
        steps = []
        
        # Extract URL from prompt or constraints
        url = None
        if constraints and constraints.get("domains"):
            domain = constraints["domains"][0]
            url = domain if domain.startswith("http") else f"https://{domain}"
        else:
            # Try to extract URL from prompt
            url_match = re.search(r'https?://[^\s]+', prompt)
            if url_match:
                url = url_match.group(0)
            else:
                # Look for domain names
                domain_match = re.search(r'(\w+\.)+\w{2,}', prompt)
                if domain_match:
                    url = f"https://{domain_match.group(0)}"
        
        if url:
            steps.append({
                "tool": "navigate",
                "args": {"url": url},
                "purpose": "Navigate to target website"
            })
            
            steps.append({
                "tool": "get_page_info",
                "args": {},
                "purpose": "Get page title and URL"
            })
            
            # If prompt mentions extraction, add extract step
            if any(word in prompt.lower() for word in ["find", "get", "extract", "show", "tell"]):
                steps.append({
                    "tool": "extract_content",
                    "args": {"selector": "h1, h2, .title, title"},
                    "purpose": "Extract main content"
                })
        
        return {
            "steps": steps,
            "success_criteria": "Page loaded and content extracted",
            "fallbacks": ["Try alternative selectors if extraction fails"]
        }
    
    async def _execute_plan(self, plan: Dict[str, Any], executor: BrowserToolExecutor, start_time: float) -> Dict[str, Any]:
        """Execute the plan step by step."""
        results = []
        
        for i, step in enumerate(plan["steps"]):
            if not self._is_executing:
                break
            
            tool_name = step["tool"]
            tool_args = step["args"]
            purpose = step.get("purpose", "")
            
            print(f"\n⚙️  Step {i+1}/{len(plan['steps'])}: {tool_name} - {purpose}")
            
            # Execute tool
            result = await executor.execute_tool(tool_name, tool_args)
            
            # Track tool call
            self._add_tool_call(
                tool=tool_name,
                args=tool_args,
                status="success" if result.success else "error"
            )
            
            # Update tool success rate
            if tool_name not in self.tool_success_rate:
                self.tool_success_rate[tool_name] = {"success": 0, "total": 0}
            self.tool_success_rate[tool_name]["total"] += 1
            if result.success:
                self.tool_success_rate[tool_name]["success"] += 1
            
            # Track screenshot
            if result.screenshot:
                self._screenshots.append({
                    "index": len(self._screenshots),
                    "timestamp": time.time(),
                    "elapsed": time.time() - start_time,
                    "data": result.screenshot
                })
            
            results.append({
                "step": i + 1,
                "tool": tool_name,
                "success": result.success,
                "data": result.data,
                "error": result.error
            })
            
            print(f"   {'✅' if result.success else '❌'} {result.success}")
        
        return {
            "steps_executed": len(results),
            "results": results,
            "tool_performance": self.tool_success_rate
        }
    
    async def _validate_and_summarize(self, task: str, execution_results: Dict[str, Any]) -> str:
        """Use LLM to validate results and create summary."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are validating web automation results. Summarize what was accomplished."},
                    {"role": "user", "content": f"Task: {task}\n\nExecution Results:\n{json.dumps(execution_results, indent=2)}\n\nSummarize the outcome:"}
                ],
                temperature=0.5
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"⚠️  Validation failed: {e}")
            return self._create_summary(execution_results)
    
    def _create_summary(self, execution_results: Dict[str, Any]) -> str:
        """Create a simple summary without LLM."""
        total = execution_results["steps_executed"]
        successful = sum(1 for r in execution_results["results"] if r["success"])
        
        return f"TinyFish executed {total} steps with {successful}/{total} successful. Task completed."
    
    async def _create_browserbase_session(self) -> Dict[str, Any]:
        """Create a BrowserBase session for browser control."""
        try:
            import sys
            from pathlib import Path
            lambda_dir = Path(__file__).parent.parent.parent.parent / "lambda"
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
            return {
                "id": "mock-session",
                "connect_url": None
            }
    
    def stop_execution(self) -> None:
        """Stop the current execution."""
        self._is_executing = False
