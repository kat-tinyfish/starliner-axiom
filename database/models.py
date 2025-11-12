"""
Database Models - SQLAlchemy ORM models for the database schema.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class Agent(Base):
    """Agent table - stores agent metadata."""
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    version = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    executions = relationship("AgentExecution", back_populates="agent")
    preferences = relationship("UserPreference", back_populates="preferred_agent")


class Race(Base):
    """Race table - stores race execution details."""
    __tablename__ = "races"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt = Column(Text, nullable=False)
    prompt_domains = Column(JSONB)  # JSON array of domain hints
    prompt_schema = Column(JSONB)  # JSON schema for output
    agent_a_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    agent_b_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    status = Column(
        Enum("running", "completed", "stopped", "error", name="race_status"),
        default="running"
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    executions = relationship("AgentExecution", back_populates="race")
    preferences = relationship("UserPreference", back_populates="race")


class AgentExecution(Base):
    """Agent execution table - stores individual agent performance in a race."""
    __tablename__ = "agent_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    race_id = Column(UUID(as_uuid=True), ForeignKey("races.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    checkpoints = Column(JSONB)  # JSON array of checkpoint timestamps
    output = Column(JSONB)  # JSON output from agent
    error_message = Column(Text)
    execution_time = Column(Float)
    final_status = Column(
        Enum("success", "failure", "stopped", name="execution_status"),
        nullable=False
    )
    
    # Relationships
    race = relationship("Race", back_populates="executions")
    agent = relationship("Agent", back_populates="executions")


class UserPreference(Base):
    """User preference table - stores user votes for agents."""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    race_id = Column(UUID(as_uuid=True), ForeignKey("races.id"), nullable=False)
    preferred_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    preference_type = Column(
        Enum("agent_a", "agent_b", name="preference_type"),
        nullable=False
    )
    feedback_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    race = relationship("Race", back_populates="preferences")
    preferred_agent = relationship("Agent", back_populates="preferences")


class LeaderboardCache(Base):
    """Leaderboard cache table - stores aggregated statistics for performance."""
    __tablename__ = "leaderboard_cache"
    
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), primary_key=True)
    total_races = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    avg_execution_time = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

