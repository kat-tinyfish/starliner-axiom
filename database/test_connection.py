#!/usr/bin/env python
"""
Test database connection to Supabase.
"""

import sys
from connection import get_supabase_client, test_database_connection


def main():
    print("=" * 60)
    print("Testing Supabase Database Connection")
    print("=" * 60)
    print()
    
    # Test 1: Connection
    print("Test 1: Database Connection")
    print("-" * 60)
    
    if test_database_connection():
        print("✅ Successfully connected to Supabase!")
    else:
        print("❌ Failed to connect to Supabase")
        print("   Check your .env file for SUPABASE_URL and SUPABASE_KEY")
        return 1
    
    print()
    
    # Test 2: Query agents table
    print("Test 2: Query Agents Table")
    print("-" * 60)
    
    try:
        client = get_supabase_client()
        response = client.table('agents').select('*').execute()
        
        if response.data:
            print(f"✅ Found {len(response.data)} agents:")
            for agent in response.data:
                print(f"   - {agent['display_name']} ({agent['name']})")
        else:
            print("⚠️  No agents found. Run the SQL setup script.")
            return 1
    except Exception as e:
        print(f"❌ Error querying agents: {str(e)}")
        return 1
    
    print()
    
    # Test 3: Check all tables exist
    print("Test 3: Verify All Tables")
    print("-" * 60)
    
    tables = {
        'agents': 'id',
        'races': 'id',
        'agent_executions': 'id',
        'user_preferences': 'id',
        'leaderboard_cache': 'agent_id'  # This table uses agent_id as PK
    }
    all_exist = True
    
    for table, pk_column in tables.items():
        try:
            response = client.table(table).select(pk_column).limit(1).execute()
            print(f"   ✅ {table}")
        except Exception as e:
            print(f"   ❌ {table} - {str(e)}")
            all_exist = False
    
    print()
    
    if all_exist:
        print("=" * 60)
        print("✅ All tests passed! Database is ready.")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("❌ Some tests failed. Check your database setup.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

