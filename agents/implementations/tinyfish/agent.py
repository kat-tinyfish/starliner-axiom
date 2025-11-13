"""
TinyFish Agent Implementation - External TinyFish Web Agent API Integration

This agent connects to the external TinyFish API (http://54.67.10.91:8000) which uses
Gemini-based browser automation to execute web tasks.

Key Features:
- SSE streaming for real-time execution updates
- Native TinyFish tool execution
- Automatic checkpoint and tool call tracking
- Authentic TinyFish performance

Flow:
1. Create TinyFish session with task instruction
2. Stream SSE events and parse them
3. Extract tool calls, checkpoints, and results
4. Return structured AgentResult
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional, List
import json

from agents.base_agent import BaseAgent, AgentResult, Checkpoint, ToolCall
from utils.tinyfish_client import TinyFishAPIClient, TinyFishEvent
from datetime import datetime


class TinyFishAgent(BaseAgent):
    """
    Web agent powered by external TinyFish API with Gemini-based browser automation.
    
    Uses the production TinyFish API to execute tasks, providing authentic
    TinyFish performance for comparison in the arena.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: Optional[str] = None):
        super().__init__(agent_id, name, api_key or "")
        self._is_executing = False
        self.client = TinyFishAPIClient()
        self.session_id: Optional[str] = None
    
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute a task using TinyFish API.
        
        Args:
            prompt: Natural language task description
            constraints: Optional constraints (domains, JSON schema, etc.)
        
        Returns:
            AgentResult with execution details
        """
        start_time = time.time()
        self._is_executing = True
        
        try:
            # Checkpoint 1: Initialization
            self._add_checkpoint("initialization", "Connecting to TinyFish API", "completed")
            
            # Create session
            session_result = await self.client.create_session(
                task_instruction=prompt,
                browser_type="tetra",
                use_proxy=False
            )
            
            self.session_id = session_result["session_id"]
            
            self._add_checkpoint("session_created", f"TinyFish session {self.session_id[:8]}... created", "completed")
            
            # Checkpoint 2: Execution starting
            self._add_checkpoint("execution_start", "Starting task execution", "in_progress")
            
            # Stream SSE events and process them
            final_response = None
            event_count = 0
            
            async for event in self.client.run_sse_stream(self.session_id, prompt):
                event_count += 1
                
                # Process event
                self._process_tinyfish_event(event)
                
                # Check for final response
                if event.final_response:
                    final_response = event.final_response
                    break
                
                # Safety check
                if not self._is_executing:
                    print("🛑 TinyFish execution stopped by user")
                    await self.client.abort_session(self.session_id)
                    break
            
            # Checkpoint 3: Execution complete
            self._add_checkpoint("execution_complete", f"Processed {event_count} events", "completed")
            
            # Checkpoint 4: Completion
            self._add_checkpoint("completion", "Task completed successfully", "completed")
            
            execution_time = time.time() - start_time
            
            # Extract output data (match format of other agents)
            output_data = {
                "summary": final_response or "Task completed",
                "iterations": event_count,
                "tool_calls_count": len(self.get_tool_calls())
            }
            
            return AgentResult(
                success=True,
                output=output_data,
                error_message=None,
                execution_time=execution_time,
                checkpoints=self.get_all_checkpoints(),
                tool_calls=self.get_tool_calls(),
                screenshots=self._screenshots  # Will be empty for now
            )
        
        except Exception as e:
            error_msg = f"TinyFish execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            self._add_checkpoint("error", error_msg, "error")
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=False,
                output=None,
                error_message=error_msg,
                execution_time=execution_time,
                checkpoints=self.get_all_checkpoints(),
                tool_calls=self.get_tool_calls(),
                screenshots=self._screenshots
            )
        
        finally:
            self._is_executing = False
    
    def _process_tinyfish_event(self, event: TinyFishEvent):
        """
        Process a TinyFish event and update checkpoints/tool calls.
        
        Args:
            event: Parsed TinyFish event
        """
        # Handle different event types
        if event.content_type == 'functionCall':
            # Agent is planning/thinking
            self._add_checkpoint(
                f"thinking_{event.event_number}",
                "TinyFish analyzing task and planning next action",
                "completed"
            )
        
        elif event.content_type == 'functionResponse':
            # Tool execution completed
            if event.tool_call:
                # Add tool call to history
                self._add_tool_call(
                    tool=event.tool_call.tool_name,
                    args=event.tool_call.args,
                    status="success" if event.tool_call.result else "in_progress"
                )
                
                # Add checkpoint for tool execution
                tool_name = event.tool_call.tool_name
                self._add_checkpoint(
                    f"tool_{tool_name}_{event.event_number}",
                    f"Executed: {tool_name}",
                    "completed"
                )
                
                # Log state changes
                if event.state_delta:
                    urls = event.state_delta.get('urls_visited', [])
                    if urls:
                        print(f"   🌐 Visited: {urls[-1] if urls else 'N/A'}")
                    
                    new_elements = event.state_delta.get('new_elements', [])
                    if new_elements:
                        print(f"   📦 Found {len(new_elements)} new elements")
        
        elif event.content_type == 'text':
            # Final response received
            if event.final_response:
                print(f"   ✅ Final response: {event.final_response[:100]}...")
                self._add_checkpoint(
                    "final_response",
                    "Received final response from TinyFish",
                    "completed"
                )
    
    def stop_execution(self) -> None:
        """Stop the current execution."""
        print("🛑 Stopping TinyFish execution...")
        self._is_executing = False
        
        # Attempt to abort the session
        if self.session_id:
            asyncio.create_task(self.client.abort_session(self.session_id))
    
    def get_browser_session_url(self) -> str:
        """
        Get the URL for the browser session.
        
        Note: TinyFish API doesn't provide direct browser session URLs.
        This returns a placeholder for UI consistency.
        """
        if self.session_id:
            return f"tinyfish://{self.session_id}"
        return "tinyfish://not-started"
