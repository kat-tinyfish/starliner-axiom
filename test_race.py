#!/usr/bin/env python
"""
Test script to verify race functionality without API keys.

This script tests the basic race flow with mock agents.
"""

import asyncio
import sys
from datetime import datetime


async def test_race_orchestrator():
    """Test the race orchestrator with mock data."""
    print("=" * 60)
    print("Testing Race Orchestrator")
    print("=" * 60)
    print()
    
    # Test 1: Import modules
    print("1. Importing modules...")
    try:
        from utils.race_orchestrator import RaceOrchestrator
        from agents.agent_registry import AgentRegistry
        from agents.base_agent import AgentResult, ToolCall, Checkpoint
        print("✅ All modules imported successfully")
    except Exception as e:
        print(f"❌ Failed to import modules: {e}")
        return False
    
    print()
    
    # Test 2: Check agent registry
    print("2. Checking agent registry...")
    try:
        agents = AgentRegistry.get_all_agents()
        print(f"✅ Found {len(agents)} agents:")
        for agent_id, config in agents.items():
            print(f"   - {config.display_name} ({config.api_provider})")
    except Exception as e:
        print(f"❌ Failed to get agents: {e}")
        return False
    
    print()
    
    # Test 3: Create race orchestrator
    print("3. Creating race orchestrator...")
    try:
        orchestrator = RaceOrchestrator()
        print("✅ Race orchestrator created")
    except Exception as e:
        print(f"❌ Failed to create orchestrator: {e}")
        return False
    
    print()
    
    # Test 4: Initialize race (will fail without API keys, but tests the flow)
    print("4. Testing race initialization (may fail without API keys)...")
    try:
        # Use mock API keys for testing
        import os
        os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key"
        
        race_id = orchestrator.initialize_race(
            "GPT-4 Web Agent",
            "Claude 3.5 Sonnet Agent",
            "Search for the latest AI news",
            {"domains": ["example.com"]}
        )
        print(f"✅ Race initialized with ID: {race_id[:16]}...")
        
        # Check agent status
        status = orchestrator.get_agent_status()
        print(f"   - Agent A: {status['agent_a']['name']}")
        print(f"   - Agent B: {status['agent_b']['name']}")
        print(f"   - Race active: {status['race_active']}")
        
    except Exception as e:
        print(f"⚠️  Race initialization test: {e}")
        print("   (This is expected if API keys are not configured)")
    
    print()
    
    # Test 5: Test base agent structure
    print("5. Testing base agent structure...")
    try:
        # Create a mock tool call
        tool_call = ToolCall(
            timestamp=datetime.now(),
            tool_name="navigate_to",
            parameters={"url": "https://example.com"},
            status="success"
        )
        
        # Create a mock checkpoint
        checkpoint = Checkpoint(
            name="initialization",
            timestamp=datetime.now(),
            status="completed",
            description="Agent initialized"
        )
        
        # Create a mock result
        result = AgentResult(
            success=True,
            output="Test output",
            execution_time=5.2,
            tool_calls=[tool_call],
            checkpoints=[checkpoint]
        )
        
        print("✅ Agent structures working:")
        print(f"   - ToolCall: {tool_call.tool_name} ({tool_call.status})")
        print(f"   - Checkpoint: {checkpoint.name} ({checkpoint.status})")
        print(f"   - Result: success={result.success}, time={result.execution_time}s")
        
    except Exception as e:
        print(f"❌ Failed to create agent structures: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ All basic tests passed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Add your API keys to .env file")
    print("2. Run: streamlit run app.py")
    print("3. Test with real agents in the UI")
    print()
    
    return True


async def test_agent_implementations():
    """Test that all agent implementations can be imported."""
    print("=" * 60)
    print("Testing Agent Implementations")
    print("=" * 60)
    print()
    
    agents = [
        ("OpenAI", "agents.implementations.openai_agent", "OpenAIAgent"),
        ("Anthropic", "agents.implementations.anthropic_agent", "AnthropicAgent"),
        ("Google", "agents.implementations.google_agent", "GoogleAgent"),
        ("TinyFish", "agents.implementations.tinyfish.agent", "TinyFishAgent"),
    ]
    
    all_passed = True
    
    for name, module_path, class_name in agents:
        try:
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            print(f"✅ {name} agent imported successfully")
        except Exception as e:
            print(f"❌ {name} agent failed: {e}")
            all_passed = False
    
    print()
    
    if all_passed:
        print("✅ All agent implementations can be imported!")
    else:
        print("❌ Some agent implementations failed")
    
    print()
    return all_passed


def test_streamlit_components():
    """Test that Streamlit components can be imported."""
    print("=" * 60)
    print("Testing Streamlit Components")
    print("=" * 60)
    print()
    
    components = [
        ("Arena", "components.arena"),
        ("Dashboard", "components.dashboard"),
    ]
    
    all_passed = True
    
    for name, module_path in components:
        try:
            module = __import__(module_path, fromlist=[f"render_{name.lower()}"])
            print(f"✅ {name} component imported successfully")
        except Exception as e:
            print(f"❌ {name} component failed: {e}")
            all_passed = False
    
    print()
    
    if all_passed:
        print("✅ All Streamlit components can be imported!")
    else:
        print("❌ Some Streamlit components failed")
    
    print()
    return all_passed


async def main():
    """Run all tests."""
    print("\n")
    print("🧪 Web Agent Arena - Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Race orchestrator
    results.append(await test_race_orchestrator())
    
    # Test 2: Agent implementations
    results.append(await test_agent_implementations())
    
    # Test 3: Streamlit components
    results.append(test_streamlit_components())
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nRun the app with: streamlit run app.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

