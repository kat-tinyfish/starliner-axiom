"""
TinyFish API Client - Wrapper for external TinyFish Web Agent API.

This client handles communication with the TinyFish API including:
- Session creation
- SSE streaming
- Event parsing
- Tool call extraction
"""

import asyncio
import os
import uuid
import json
import time
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx
from dataclasses import dataclass


@dataclass
class TinyFishToolCall:
    """Represents a tool call from TinyFish."""
    tool_name: str
    args: Dict[str, Any]
    timestamp: float
    url_before: str
    result: Optional[Dict[str, Any]] = None


@dataclass
class TinyFishEvent:
    """Represents a parsed TinyFish SSE event."""
    event_number: int
    author: str
    finish_reason: Optional[str]
    content_type: str  # "functionCall", "functionResponse", "text"
    tool_call: Optional[TinyFishToolCall] = None
    state_delta: Optional[Dict[str, Any]] = None
    final_response: Optional[str] = None
    token_count: int = 0


class TinyFishAPIClient:
    """
    Client for interacting with TinyFish Web Agent API.
    
    Based on the EVB backend implementation but adapted for the arena.
    """
    
    def __init__(self):
        """Initialize the TinyFish API client."""
        self.base_url = os.getenv("TINYFISH_API_URL", "http://54.67.10.91:8000")
        self.user_id = os.getenv("TINYFISH_USER_ID", "arena-user")
        self.timeout = int(os.getenv("TINYFISH_API_TIMEOUT", "30"))
        self.sse_timeout = int(os.getenv("TINYFISH_SSE_TIMEOUT", "300"))  # 5 minutes
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    async def create_session(
        self,
        task_instruction: str,
        session_id: Optional[str] = None,
        browser_type: str = "tetra",
        use_proxy: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new TinyFish session.
        
        Args:
            task_instruction: Natural language task for the agent
            session_id: Optional session ID (generated if not provided)
            browser_type: Browser type ("tetra" or "anchor")
            use_proxy: Whether to use proxy
        
        Returns:
            Dict with session details including session_id
        
        Raises:
            Exception: If session creation fails
        """
        if session_id is None:
            session_id = self._generate_session_id()
        
        url = f"{self.base_url}/apps/eva_agent/users/{self.user_id}/sessions/{session_id}"
        payload = {
            "task_instruction": task_instruction,
            "browser_type": browser_type,
            "use_proxy": use_proxy
        }
        
        print(f"🐟 Creating TinyFish session: {session_id}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code not in [200, 201]:
                raise Exception(
                    f"Failed to create TinyFish session: {response.status_code} - {response.text[:200]}"
                )
            
            return {
                "session_id": session_id,
                "status": "created",
                "response": response.json()
            }
    
    async def run_sse_stream(
        self,
        session_id: str,
        goal: str
    ) -> AsyncGenerator[TinyFishEvent, None]:
        """
        Execute session and stream parsed events.
        
        Args:
            session_id: Session ID to execute
            goal: The goal/task for the agent
        
        Yields:
            TinyFishEvent objects
        
        Raises:
            Exception: If stream fails
        """
        url = f"{self.base_url}/run_sse"
        payload = {
            "app_name": "eva_agent",
            "user_id": self.user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": goal}]
            }
        }
        
        print(f"🐟 Starting TinyFish SSE stream for session: {session_id}")
        
        async with httpx.AsyncClient(timeout=self.sse_timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to start TinyFish SSE stream: {response.status_code}"
                    )
                
                event_count = 0
                async for line in response.aiter_lines():
                    line = line.strip()
                    
                    if not line or not line.startswith("data:"):
                        continue
                    
                    data_str = line[5:].strip()
                    if not data_str:
                        continue
                    
                    try:
                        raw_event = json.loads(data_str)
                        event_count += 1
                        
                        # Parse event
                        parsed_event = self._parse_event(raw_event, event_count)
                        
                        if parsed_event:
                            yield parsed_event
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Failed to parse TinyFish SSE event: {e}")
                        continue
        
        print(f"🐟 TinyFish stream completed: {event_count} events")
    
    def _parse_event(self, raw_event: Dict[str, Any], event_number: int) -> Optional[TinyFishEvent]:
        """
        Parse a raw TinyFish SSE event into a structured TinyFishEvent.
        
        Args:
            raw_event: Raw event dict from SSE stream
            event_number: Event sequence number
        
        Returns:
            Parsed TinyFishEvent or None if unparseable
        """
        author = raw_event.get('author', 'unknown')
        finish_reason = raw_event.get('finishReason')
        
        # Extract content
        content = raw_event.get('content', {})
        parts = content.get('parts', [])
        
        if not parts:
            return None
        
        first_part = parts[0]
        
        # Determine content type
        if 'functionCall' in first_part:
            content_type = 'functionCall'
        elif 'functionResponse' in first_part:
            content_type = 'functionResponse'
        elif 'text' in first_part:
            content_type = 'text'
        else:
            content_type = 'unknown'
        
        # Extract actions/state
        actions = raw_event.get('actions', {})
        state_delta = actions.get('stateDelta', {})
        
        # Extract tool call from state delta
        tool_call = None
        if content_type == 'functionResponse':
            tool_call_history = state_delta.get('tool_call_history', [])
            if tool_call_history:
                # Get latest tool call
                latest_call = tool_call_history[-1]
                tool_call = TinyFishToolCall(
                    tool_name=latest_call.get('tool_call', 'unknown'),
                    args=latest_call.get('args', {}),
                    timestamp=latest_call.get('ts', time.time()),
                    url_before=latest_call.get('url_before_tool_call', ''),
                    result=latest_call.get('result')
                )
        
        # Extract final response
        final_response = None
        if content_type == 'text':
            final_response_raw = state_delta.get('final_response')
            if final_response_raw:
                try:
                    # Parse JSON string
                    final_response_json = json.loads(final_response_raw)
                    final_response = final_response_json.get('raw', '')
                except:
                    final_response = final_response_raw
        
        # Extract token count
        usage = raw_event.get('usageMetadata', {})
        token_count = usage.get('totalTokenCount', 0)
        
        return TinyFishEvent(
            event_number=event_number,
            author=author,
            finish_reason=finish_reason,
            content_type=content_type,
            tool_call=tool_call,
            state_delta=state_delta,
            final_response=final_response,
            token_count=token_count
        )
    
    async def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve session history from TinyFish API.
        
        Args:
            session_id: Session ID to retrieve
        
        Returns:
            Session history dict
        
        Raises:
            Exception: If retrieval fails
        """
        url = f"{self.base_url}/apps/eva_agent/users/{self.user_id}/sessions/{session_id}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                raise Exception(
                    f"Failed to get TinyFish session history: {response.status_code}"
                )
            
            return response.json()
    
    async def abort_session(self, session_id: str) -> Dict[str, Any]:
        """
        Abort a running TinyFish session.
        
        Args:
            session_id: Session ID to abort
        
        Returns:
            Abort confirmation
        
        Raises:
            Exception: If abort fails
        """
        url = f"{self.base_url}/run"
        payload = {
            "app_name": "eva_agent",
            "user_id": self.user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": "tf_stop_agent"}]
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                raise Exception(
                    f"Failed to abort TinyFish session: {response.status_code}"
                )
            
            return {
                "session_id": session_id,
                "status": "abort_requested"
            }

