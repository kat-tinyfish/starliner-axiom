"""
Quick integration test for BrowserBase + Streamlit.

Run this before starting the full Streamlit app to verify everything is connected.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_browser_client():
    """Test the browser client."""
    print("🧪 Testing Browser Client...")
    
    from utils.browser_client import get_browser_client
    
    client = get_browser_client()
    info = client.get_backend_info()
    
    print(f"✅ Backend: {info['backend']}")
    print(f"   BrowserBase available: {info['browserbase_available']}")
    print(f"   Lambda available: {info['lambda_available']}")
    print(f"   Status: {info['status']}")
    
    if info['status'] != 'ready':
        print("\n❌ No browser execution backend configured!")
        print("   Add BROWSERBASE_API_KEY + BROWSERBASE_PROJECT_ID to .env")
        return False
    
    return True


async def test_agent_execution():
    """Test a simple agent execution."""
    print("\n🤖 Testing Agent Execution...")
    
    from agents.implementations.openai_agent import OpenAIAgent
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set - skipping agent test")
        return True
    
    agent = OpenAIAgent(
        agent_id="test-agent",
        name="Test GPT-4 Agent",
        api_key=api_key,
        model="gpt-4-turbo"
    )
    
    print("   Executing simple task...")
    result = await agent.execute(
        prompt="Go to example.com",
        constraints={"domains": ["example.com"]}
    )
    
    print(f"✅ Success: {result.success}")
    print(f"   Screenshots captured: {len(result.screenshots)}")
    print(f"   Tool calls: {len(result.tool_calls)}")
    print(f"   Checkpoints: {len(result.checkpoints)}")
    print(f"   Execution time: {result.execution_time:.2f}s")
    
    if result.screenshots:
        print(f"   First screenshot: {len(result.screenshots[0].get('data', ''))} bytes")
    
    return result.success


async def test_database():
    """Test database connection."""
    print("\n💾 Testing Database Connection...")
    
    try:
        from database.operations import get_db
        db_ops = get_db()
        
        # Try to fetch agents
        agents = db_ops.get_all_agents()
        print(f"✅ Connected to database")
        print(f"   Agents in database: {len(agents)}")
        
        return True
    except Exception as e:
        print(f"⚠️  Database connection failed: {str(e)}")
        print("   App will work but won't save results")
        return False


async def main():
    """Run all tests."""
    print("="*60)
    print("🎯 Web Agent Arena - Integration Test")
    print("="*60)
    
    results = []
    
    # Test 1: Browser Client
    results.append(("Browser Client", await test_browser_client()))
    
    # Test 2: Agent Execution
    if results[0][1]:  # Only if browser client works
        try:
            results.append(("Agent Execution", await test_agent_execution()))
        except Exception as e:
            print(f"❌ Agent execution failed: {str(e)}")
            results.append(("Agent Execution", False))
    
    # Test 3: Database
    results.append(("Database", await test_database()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    all_critical_passed = results[0][1]  # Browser client is critical
    
    print("\n" + "="*60)
    if all_critical_passed:
        print("🎉 Integration test PASSED!")
        print("\nReady to run Streamlit app:")
        print("   streamlit run app.py")
    else:
        print("❌ Integration test FAILED")
        print("\nCheck your .env file:")
        print("   BROWSERBASE_API_KEY=bb_live_...")
        print("   BROWSERBASE_PROJECT_ID=proj_...")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

