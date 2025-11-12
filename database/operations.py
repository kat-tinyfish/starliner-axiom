"""
Database Operations - CRUD operations for Web Agent Arena.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from database.connection import get_db as get_supabase_client


class DatabaseOperations:
    """Database operations for race management."""
    
    def __init__(self):
        """Initialize database operations."""
        self.client = get_supabase_client()
    
    # ========================================================================
    # AGENTS
    # ========================================================================
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """
        Get all agents from database.
        
        Returns:
            List of agent dictionaries
        """
        try:
            response = self.client.table('agents').select('*').execute()
            return response.data
        except Exception as e:
            print(f"Error fetching agents: {str(e)}")
            return []
    
    def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get agent by name.
        
        Args:
            name: Agent name (e.g., 'gpt4_web_agent')
        
        Returns:
            Agent dictionary or None
        """
        try:
            response = self.client.table('agents')\
                .select('*')\
                .eq('name', name)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching agent: {str(e)}")
            return None
    
    def get_agent_by_display_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        """
        Get agent by display name.
        
        Args:
            display_name: Agent display name (e.g., 'GPT-4 Web Agent')
        
        Returns:
            Agent dictionary or None
        """
        try:
            response = self.client.table('agents')\
                .select('*')\
                .eq('display_name', display_name)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching agent: {str(e)}")
            return None
    
    # ========================================================================
    # RACES
    # ========================================================================
    
    def create_race(self, prompt: str, agent_a_id: str, agent_b_id: str,
                    domains: Optional[List[str]] = None,
                    schema: Optional[Dict] = None) -> Optional[str]:
        """
        Create a new race.
        
        Args:
            prompt: Task prompt
            agent_a_id: UUID of agent A
            agent_b_id: UUID of agent B
            domains: Optional list of allowed domains
            schema: Optional JSON schema for output
        
        Returns:
            Race ID or None if failed
        """
        try:
            race_data = {
                'prompt': prompt,
                'agent_a_id': agent_a_id,
                'agent_b_id': agent_b_id,
                'started_at': datetime.now().isoformat(),
                'status': 'running'
            }
            
            if domains:
                race_data['prompt_domains'] = domains
            if schema:
                race_data['prompt_schema'] = schema
            
            response = self.client.table('races').insert(race_data).execute()
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            print(f"Error creating race: {str(e)}")
            return None
    
    def update_race_status(self, race_id: str, status: str,
                          duration: Optional[float] = None) -> bool:
        """
        Update race status and completion time.
        
        Args:
            race_id: Race UUID
            status: New status ('completed', 'stopped', 'error')
            duration: Optional duration in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                'status': status,
                'completed_at': datetime.now().isoformat()
            }
            
            if duration is not None:
                update_data['duration_seconds'] = duration
            
            self.client.table('races')\
                .update(update_data)\
                .eq('id', race_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Error updating race: {str(e)}")
            return False
    
    def get_race(self, race_id: str) -> Optional[Dict[str, Any]]:
        """
        Get race by ID.
        
        Args:
            race_id: Race UUID
        
        Returns:
            Race dictionary or None
        """
        try:
            response = self.client.table('races')\
                .select('*')\
                .eq('id', race_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching race: {str(e)}")
            return None
    
    def get_recent_races(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent races.
        
        Args:
            limit: Maximum number of races to return
        
        Returns:
            List of race dictionaries
        """
        try:
            response = self.client.table('races')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching recent races: {str(e)}")
            return []
    
    # ========================================================================
    # AGENT EXECUTIONS
    # ========================================================================
    
    def save_agent_execution(self, race_id: str, agent_id: str,
                            checkpoints: List[Dict], tool_calls: List[Dict],
                            output: Any, execution_time: float,
                            final_status: str,
                            error_message: Optional[str] = None) -> bool:
        """
        Save agent execution results.
        
        Args:
            race_id: Race UUID
            agent_id: Agent UUID
            checkpoints: List of checkpoint dictionaries
            tool_calls: List of tool call dictionaries
            output: Agent output
            execution_time: Execution time in seconds
            final_status: 'success', 'error', 'timeout', or 'stopped'
            error_message: Optional error message
        
        Returns:
            True if successful, False otherwise
        """
        try:
            execution_data = {
                'race_id': race_id,
                'agent_id': agent_id,
                'checkpoints': json.dumps(checkpoints),
                'tool_calls': json.dumps(tool_calls),
                'output': json.dumps(output) if output else None,
                'execution_time': execution_time,
                'final_status': final_status,
                'error_message': error_message
            }
            
            self.client.table('agent_executions').insert(execution_data).execute()
            return True
        except Exception as e:
            print(f"Error saving agent execution: {str(e)}")
            return False
    
    def get_race_executions(self, race_id: str) -> List[Dict[str, Any]]:
        """
        Get all agent executions for a race.
        
        Args:
            race_id: Race UUID
        
        Returns:
            List of execution dictionaries
        """
        try:
            response = self.client.table('agent_executions')\
                .select('*')\
                .eq('race_id', race_id)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching race executions: {str(e)}")
            return []
    
    # ========================================================================
    # USER PREFERENCES (VOTING)
    # ========================================================================
    
    def save_user_preference(self, race_id: str, preferred_agent_id: str,
                            preference_type: str,
                            feedback_notes: Optional[str] = None) -> bool:
        """
        Save user's agent preference (vote).
        
        Args:
            race_id: Race UUID
            preferred_agent_id: UUID of preferred agent
            preference_type: 'agent_a' or 'agent_b'
            feedback_notes: Optional user feedback
        
        Returns:
            True if successful, False otherwise
        """
        try:
            preference_data = {
                'race_id': race_id,
                'preferred_agent_id': preferred_agent_id,
                'preference_type': preference_type,
                'feedback_notes': feedback_notes
            }
            
            self.client.table('user_preferences').insert(preference_data).execute()
            return True
        except Exception as e:
            print(f"Error saving user preference: {str(e)}")
            return False
    
    # ========================================================================
    # LEADERBOARD
    # ========================================================================
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """
        Get leaderboard data for all agents.
        
        Returns:
            List of leaderboard entries sorted by win rate
        """
        try:
            response = self.client.table('leaderboard_cache')\
                .select('*, agents(name, display_name)')\
                .order('win_rate', desc=True)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching leaderboard: {str(e)}")
            return []
    
    def get_agent_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific agent.
        
        Args:
            agent_id: Agent UUID
        
        Returns:
            Statistics dictionary or None
        """
        try:
            response = self.client.table('leaderboard_cache')\
                .select('*')\
                .eq('agent_id', agent_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching agent stats: {str(e)}")
            return None
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_top_matchups(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get most popular agent matchups.
        
        Args:
            limit: Number of matchups to return
        
        Returns:
            List of matchup statistics
        """
        try:
            # This requires a more complex query - implement with RPC or Python aggregation
            response = self.client.table('races')\
                .select('agent_a_id, agent_b_id, agents!agent_a_id(display_name), agents!agent_b_id(display_name)')\
                .execute()
            
            # Aggregate in Python for simplicity
            matchups = {}
            for race in response.data:
                key = tuple(sorted([race['agent_a_id'], race['agent_b_id']]))
                if key not in matchups:
                    matchups[key] = {
                        'agent_a_id': race['agent_a_id'],
                        'agent_b_id': race['agent_b_id'],
                        'count': 0
                    }
                matchups[key]['count'] += 1
            
            # Sort by count and return top N
            sorted_matchups = sorted(matchups.values(), key=lambda x: x['count'], reverse=True)
            return sorted_matchups[:limit]
        except Exception as e:
            print(f"Error fetching top matchups: {str(e)}")
            return []
    
    def get_race_count(self) -> int:
        """Get total number of races."""
        try:
            response = self.client.table('races').select('id', count='exact').execute()
            return response.count
        except Exception as e:
            print(f"Error fetching race count: {str(e)}")
            return 0


# Singleton instance
_db_operations = None


def get_db() -> DatabaseOperations:
    """
    Get database operations instance.
    
    Returns:
        DatabaseOperations instance
    """
    global _db_operations
    if _db_operations is None:
        _db_operations = DatabaseOperations()
    return _db_operations

