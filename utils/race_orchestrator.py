"""
Race Orchestrator - Manages head-to-head agent battles.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

from agents.base_agent import BaseAgent, AgentResult
from agents.agent_registry import AgentRegistry


class RaceOrchestrator:
    """
    Orchestrates head-to-head races between two agents.
    
    Handles:
    - Concurrent agent execution
    - Race timing
    - State management
    - Results collection
    """
    
    def __init__(self):
        self.race_id: Optional[str] = None
        self.agent_a: Optional[BaseAgent] = None
        self.agent_b: Optional[BaseAgent] = None
        self.prompt: str = ""
        self.constraints: Dict[str, Any] = {}
        self.race_active: bool = False
        self.start_time: Optional[float] = None
        self.result_a: Optional[AgentResult] = None
        self.result_b: Optional[AgentResult] = None
    
    def initialize_race(
        self,
        agent_a_name: str,
        agent_b_name: str,
        prompt: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Initialize a new race.
        
        Args:
            agent_a_name: Display name of agent A
            agent_b_name: Display name of agent B
            prompt: Task prompt
            constraints: Optional task constraints
        
        Returns:
            Race ID
        """
        from dotenv import load_dotenv
        import os
        
        # Load environment variables
        load_dotenv()
        
        # Generate race ID
        self.race_id = str(uuid.uuid4())
        self.prompt = prompt
        self.constraints = constraints or {}
        
        # Get agent IDs from display names
        agent_a_id = AgentRegistry.get_agent_id_by_display_name(agent_a_name)
        agent_b_id = AgentRegistry.get_agent_id_by_display_name(agent_b_name)
        
        if not agent_a_id or not agent_b_id:
            raise ValueError(f"Invalid agent names: {agent_a_name}, {agent_b_name}")
        
        # Get API keys from environment
        agent_a_config = AgentRegistry.get_agent_config(agent_a_id)
        agent_b_config = AgentRegistry.get_agent_config(agent_b_id)
        
        api_key_a = os.getenv(agent_a_config.api_provider.upper() + "_API_KEY", "")
        api_key_b = os.getenv(agent_b_config.api_provider.upper() + "_API_KEY", "")
        
        # Create agent instances
        self.agent_a = AgentRegistry.create_agent(agent_a_id, api_key_a)
        self.agent_b = AgentRegistry.create_agent(agent_b_id, api_key_b)
        
        return self.race_id
    
    async def start_race(self) -> Tuple[AgentResult, AgentResult, float]:
        """
        Start the race and run both agents concurrently.
        
        Returns:
            Tuple of (result_a, result_b, duration)
        """
        if not self.agent_a or not self.agent_b:
            raise RuntimeError("Race not initialized. Call initialize_race() first.")
        
        self.race_active = True
        self.start_time = time.time()
        
        # Run both agents concurrently
        results = await asyncio.gather(
            self.agent_a.execute(self.prompt, self.constraints),
            self.agent_b.execute(self.prompt, self.constraints),
            return_exceptions=True
        )
        
        duration = time.time() - self.start_time
        self.race_active = False
        
        # Handle results (including exceptions)
        self.result_a = results[0] if not isinstance(results[0], Exception) else AgentResult(
            success=False,
            output=None,
            error_message=str(results[0])
        )
        
        self.result_b = results[1] if not isinstance(results[1], Exception) else AgentResult(
            success=False,
            output=None,
            error_message=str(results[1])
        )
        
        return self.result_a, self.result_b, duration
    
    def stop_race(self):
        """Stop the ongoing race."""
        self.race_active = False
        if self.agent_a:
            self.agent_a.stop_execution()
        if self.agent_b:
            self.agent_b.stop_execution()
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since race start."""
        if not self.start_time:
            return 0.0
        return time.time() - self.start_time
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get current status of both agents.
        
        Returns:
            Dictionary with agent statuses, checkpoints, and tool calls
        """
        status = {
            "race_id": self.race_id,
            "race_active": self.race_active,
            "elapsed_time": self.get_elapsed_time(),
            "agent_a": {
                "name": self.agent_a.name if self.agent_a else None,
                "checkpoints": self.agent_a.get_all_checkpoints() if self.agent_a else [],
                "tool_calls": self.agent_a.get_tool_calls() if self.agent_a else [],
                "current_checkpoint": self.agent_a.get_current_checkpoint() if self.agent_a else None,
                "screenshots": self.result_a.screenshots if self.result_a and hasattr(self.result_a, 'screenshots') and self.result_a.screenshots else [],
            },
            "agent_b": {
                "name": self.agent_b.name if self.agent_b else None,
                "checkpoints": self.agent_b.get_all_checkpoints() if self.agent_b else [],
                "tool_calls": self.agent_b.get_tool_calls() if self.agent_b else [],
                "current_checkpoint": self.agent_b.get_current_checkpoint() if self.agent_b else None,
                "screenshots": self.result_b.screenshots if self.result_b and hasattr(self.result_b, 'screenshots') and self.result_b.screenshots else [],
            }
        }
        return status
    
    def get_results(self) -> Optional[Tuple[AgentResult, AgentResult]]:
        """
        Get race results.
        
        Returns:
            Tuple of (result_a, result_b) or None if race not complete
        """
        if self.result_a and self.result_b:
            return self.result_a, self.result_b
        return None
    
    def is_race_finished(self) -> bool:
        """Check if race has finished."""
        return not self.race_active and self.result_a is not None and self.result_b is not None
    
    def get_race_results(self) -> Optional[Tuple[AgentResult, AgentResult, float]]:
        """Get complete race results including duration."""
        if self.is_race_finished():
            duration = 0.0
            if self.start_time:
                duration = (self.result_a.execution_time + self.result_b.execution_time) / 2
            return self.result_a, self.result_b, duration
        return None

