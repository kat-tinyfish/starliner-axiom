"""
Database Connection - Handles Supabase connection and operations.
"""

import os
from typing import Optional
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseConnection:
    """Singleton class for Supabase connection management."""
    
    _instance: Optional['SupabaseConnection'] = None
    _client: Optional[Client] = None
    _engine = None
    _session_maker = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase connection."""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client and SQLAlchemy engine."""
        # Get credentials from environment
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "Supabase credentials not found. "
                "Please set SUPABASE_URL and SUPABASE_KEY in .env file"
            )
        
        # Create Supabase client
        try:
            self._client = create_client(supabase_url, supabase_key)
            print("✅ Supabase client initialized")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
        
        # Create SQLAlchemy engine for complex queries (optional)
        # Note: Requires connection string from Supabase settings
        # For now, we'll use Supabase client for all operations
    
    @property
    def client(self) -> Client:
        """Get Supabase client."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            # Try to query agents table
            response = self.client.table('agents').select('id').limit(1).execute()
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False
    
    def get_table(self, table_name: str):
        """Get table reference for queries."""
        return self.client.table(table_name)


# Singleton instance
_supabase_connection = None


def get_supabase_client() -> Client:
    """
    Get Supabase client instance.
    
    Returns:
        Supabase client
    """
    global _supabase_connection
    
    if _supabase_connection is None:
        _supabase_connection = SupabaseConnection()
    
    return _supabase_connection.client


def test_database_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        conn = SupabaseConnection()
        return conn.test_connection()
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


# For backward compatibility
def get_db_session():
    """Get database session (placeholder for SQLAlchemy if needed)."""
    # For now, we use Supabase client directly
    # This can be implemented later if complex ORM operations are needed
    return get_supabase_client()


# Alias for consistency
get_db = get_supabase_client
