"""
Base Agent Class - Abstract interface for all web agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ToolCall:
    """Represents a single tool call made by an agent."""
    timestamp: datetime
    tool_name: str
    parameters: Dict[str, Any]
    status: str  # "in_progress", "success", "error"
    result: Optional[Any] = None
    error_message: Optional[str] = None


@dataclass
class Checkpoint:
    """Represents a checkpoint in agent execution."""
    name: str
    timestamp: datetime
    status: str  # "completed", "in_progress", "pending"
    description: str


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    output: Any
    error_message: Optional[str] = None
    execution_time: float = 0.0
    tool_calls: List[ToolCall] = None
    checkpoints: List[Checkpoint] = None
    screenshots: List[Dict[str, Any]] = None  # List of screenshot dicts with base64 data
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []
        if self.checkpoints is None:
            self.checkpoints = []
        if self.screenshots is None:
            self.screenshots = []


class BaseAgent(ABC):
    """
    Abstract base class for all web agents.
    
    Each agent implementation must inherit from this class and implement
    the abstract methods.
    """
    
    def __init__(self, agent_id: str, name: str, api_key: str):
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name
            api_key: API key for the agent service
        """
        self.agent_id = agent_id
        self.name = name
        self.api_key = api_key
        self._current_checkpoint = None
        self._tool_calls = []
        self._checkpoints = []
        self._screenshots = []  # Track screenshots during execution
    
    @abstractmethod
    async def execute(self, prompt: str, constraints: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute a task based on the given prompt.
        
        Args:
            prompt: Natural language description of the task
            constraints: Optional constraints (domains, JSON schema, etc.)
        
        Returns:
            AgentResult with execution details
        """
        pass
    
    @abstractmethod
    def stop_execution(self) -> None:
        """Stop the current execution."""
        pass
    
    def get_browser_session_url(self) -> str:
        """
        Get the URL for the browser session (deprecated - using screenshot polling now).
        
        Returns:
            Placeholder URL (VNC streaming has been replaced with screenshot polling)
        """
        return f"#agent-{self.agent_id}"  # Placeholder - not used with screenshot polling
    
    def get_current_checkpoint(self) -> Optional[Checkpoint]:
        """Get the current checkpoint."""
        return self._current_checkpoint
    
    def get_all_checkpoints(self) -> List[Checkpoint]:
        """Get all checkpoints recorded so far."""
        return self._checkpoints.copy()
    
    def get_tool_calls(self) -> List[ToolCall]:
        """Get all tool calls recorded so far."""
        return self._tool_calls.copy()
    
    def _add_checkpoint(self, name: str, description: str, status: str = "completed"):
        """Add a checkpoint to the execution history."""
        checkpoint = Checkpoint(
            name=name,
            timestamp=datetime.now(),
            status=status,
            description=description
        )
        self._checkpoints.append(checkpoint)
        self._current_checkpoint = checkpoint
    
    def _add_tool_call(self, tool: str = None, args: Dict[str, Any] = None, 
                       status: str = "in_progress", 
                       tool_name: str = None, parameters: Dict[str, Any] = None) -> ToolCall:
        """
        Add a tool call to the execution history.
        
        Supports both naming conventions:
        - tool, args (new agents)
        - tool_name, parameters (legacy)
        """
        # Support both parameter names
        final_tool_name = tool or tool_name or "unknown"
        final_parameters = args if args is not None else (parameters or {})
        
        tool_call = ToolCall(
            timestamp=datetime.now(),
            tool_name=final_tool_name,
            parameters=final_parameters,
            status=status
        )
        self._tool_calls.append(tool_call)
        return tool_call
    
    def _update_tool_call(self, tool_call: ToolCall, status: str, 
                          result: Any = None, error_message: str = None):
        """Update a tool call with results."""
        tool_call.status = status
        tool_call.result = result
        tool_call.error_message = error_message

