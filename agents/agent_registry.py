"""
Agent Registry - Manages available agents and their configurations.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_id: str
    name: str
    display_name: str
    api_provider: str  # "openai", "anthropic", "google", "custom"
    model: Optional[str] = None
    endpoint: Optional[str] = None
    description: str = ""
    codebase_url: Optional[str] = None


class AgentRegistry:
    """
    Registry of available agents for the arena.
    
    This class manages the configuration and instantiation of agents.
    """
    
    # Available agents configuration
    AGENTS = {
        "gpt4-agent": AgentConfig(
            agent_id="gpt4-agent",
            name="gpt4_web_agent",
            display_name="GPT-4 Web Agent",
            api_provider="openai",
            model="gpt-4-turbo",
            description="OpenAI's GPT-4 Turbo model with web navigation capabilities"
        ),
        "claude-agent": AgentConfig(
            agent_id="claude-agent",
            name="claude_web_agent",
            display_name="Claude 3.5 Sonnet Agent",
            api_provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            description="Anthropic's Claude 3.5 Sonnet with advanced reasoning"
        ),
        "gemini-agent": AgentConfig(
            agent_id="gemini-agent",
            name="gemini_web_agent",
            display_name="Gemini 2.0 Agent",
            api_provider="google",
            model="gemini-2.0-flash-exp",
            description="Google's Gemini 2.0 Flash with multimodal capabilities"
        ),
        "tinyfish-agent": AgentConfig(
            agent_id="tinyfish-agent",
            name="tinyfish_agent",
            display_name="TinyFish Agent",
            api_provider="custom",
            endpoint="https://api.tinyfish.ai/v1/agent",
            description="TinyFish's custom web agent with specialized capabilities",
            codebase_url="https://github.com/your-org/tinyfish-agent"
        )
    }
    
    @classmethod
    def get_agent_config(cls, agent_id: str) -> Optional[AgentConfig]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            AgentConfig if found, None otherwise
        """
        return cls.AGENTS.get(agent_id)
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, AgentConfig]:
        """Get all available agents."""
        return cls.AGENTS.copy()
    
    @classmethod
    def get_agent_list(cls) -> List[str]:
        """Get list of agent display names."""
        return [config.display_name for config in cls.AGENTS.values()]
    
    @classmethod
    def get_agent_id_by_display_name(cls, display_name: str) -> Optional[str]:
        """
        Get agent ID from display name.
        
        Args:
            display_name: Human-readable agent name
        
        Returns:
            Agent ID if found, None otherwise
        """
        for agent_id, config in cls.AGENTS.items():
            if config.display_name == display_name:
                return agent_id
        return None
    
    @classmethod
    def create_agent(cls, agent_id: str, api_key: str):
        """
        Create an agent instance.
        
        Args:
            agent_id: Unique identifier for the agent
            api_key: API key for the agent service
        
        Returns:
            Agent instance
        
        Raises:
            ValueError: If agent_id is not found
        """
        config = cls.get_agent_config(agent_id)
        if not config:
            raise ValueError(f"Agent '{agent_id}' not found in registry")
        
        # Import the appropriate agent implementation
        if config.api_provider == "openai":
            from agents.implementations.openai_agent import OpenAIAgent
            return OpenAIAgent(agent_id, config.display_name, api_key, config.model)
        elif config.api_provider == "anthropic":
            from agents.implementations.anthropic_agent import AnthropicAgent
            return AnthropicAgent(agent_id, config.display_name, api_key, config.model)
        elif config.api_provider == "google":
            from agents.implementations.google_agent import GoogleAgent
            return GoogleAgent(agent_id, config.display_name, api_key, config.model)
        elif config.api_provider == "custom":
            from agents.implementations.tinyfish.agent import TinyFishAgent
            return TinyFishAgent(agent_id, config.display_name, api_key, config.endpoint)
        else:
            raise ValueError(f"Unknown API provider: {config.api_provider}")

