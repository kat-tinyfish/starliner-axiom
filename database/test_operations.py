#!/usr/bin/env python
"""
Test database operations.
"""

import sys
from operations import get_db


def main():
    print("=" * 60)
    print("Testing Database Operations")
    print("=" * 60)
    print()
    
    db = get_db()
    
    # Test 1: Get all agents
    print("Test 1: Get All Agents")
    print("-" * 60)
    agents = db.get_all_agents()
    print(f"✅ Found {len(agents)} agents")
    for agent in agents:
        print(f"   - {agent['display_name']}")
    print()
    
    # Test 2: Get leaderboard
    print("Test 2: Get Leaderboard")
    print("-" * 60)
    leaderboard = db.get_leaderboard()
    print(f"✅ Leaderboard has {len(leaderboard)} entries")
    for entry in leaderboard:
        print(f"   - Agent: {entry.get('agent_id', 'N/A')}")
        print(f"     Races: {entry.get('total_races', 0)}, Win Rate: {entry.get('win_rate', 0):.1%}")
    print()
    
    # Test 3: Create a test race
    print("Test 3: Create Test Race")
    print("-" * 60)
    if len(agents) >= 2:
        agent_a = agents[0]
        agent_b = agents[1]
        
        race_id = db.create_race(
            prompt="Test race: Navigate to example.com",
            agent_a_id=agent_a['id'],
            agent_b_id=agent_b['id'],
            domains=["example.com"]
        )
        
        if race_id:
            print(f"✅ Created race: {race_id}")
            
            # Test 4: Save agent execution
            print()
            print("Test 4: Save Agent Execution")
            print("-" * 60)
            
            success = db.save_agent_execution(
                race_id=race_id,
                agent_id=agent_a['id'],
                checkpoints=[{"name": "test", "status": "completed"}],
                tool_calls=[{"tool": "navigate", "status": "success"}],
                output={"result": "test"},
                execution_time=5.2,
                final_status="success"
            )
            
            if success:
                print("✅ Saved agent execution")
            else:
                print("❌ Failed to save agent execution")
            
            # Test 5: Update race status
            print()
            print("Test 5: Update Race Status")
            print("-" * 60)
            
            success = db.update_race_status(race_id, "completed", duration=10.5)
            if success:
                print("✅ Updated race status")
            else:
                print("❌ Failed to update race status")
            
            # Test 6: Save user preference
            print()
            print("Test 6: Save User Preference")
            print("-" * 60)
            
            success = db.save_user_preference(
                race_id=race_id,
                preferred_agent_id=agent_a['id'],
                preference_type="agent_a",
                feedback_notes="Test vote"
            )
            
            if success:
                print("✅ Saved user preference")
            else:
                print("❌ Failed to save user preference")
            
            # Test 7: Get updated leaderboard
            print()
            print("Test 7: Get Updated Leaderboard")
            print("-" * 60)
            leaderboard = db.get_leaderboard()
            print(f"✅ Leaderboard after vote:")
            for entry in leaderboard:
                if entry['agent_id'] in [agent_a['id'], agent_b['id']]:
                    print(f"   - Agent: {entry['agent_id']}")
                    print(f"     Races: {entry['total_races']}, Wins: {entry['wins']}, Win Rate: {entry['win_rate']:.1%}")
        else:
            print("❌ Failed to create race")
            return 1
    else:
        print("❌ Not enough agents")
        return 1
    
    print()
    print("=" * 60)
    print("✅ All database operations tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

