"""
Test TinyFish Agent Integration

Tests the complete TinyFish agent implementation with a simple task.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.implementations.tinyfish.agent import TinyFishAgent


async def test_simple_task():
    """Test TinyFish agent with a simple task."""
    print("="*80)
    print("🐟 Testing TinyFish Agent Integration")
    print("="*80)
    print()
    
    # Create agent
    agent = TinyFishAgent(
        agent_id="test-tinyfish",
        name="Test TinyFish Agent"
    )
    
    # Define task
    task = "Go to example.com and extract the main heading text"
    
    print(f"📋 Task: {task}")
    print()
    
    # Execute task
    print("🚀 Starting execution...")
    print()
    
    result = await agent.execute(task)
    
    # Display results
    print()
    print("="*80)
    print("📊 Execution Results")
    print("="*80)
    print()
    
    print(f"✅ Success: {result.success}")
    print(f"⏱️  Execution Time: {result.execution_time:.2f}s")
    print(f"📦 Output: {result.output}")
    print()
    
    print(f"🚩 Checkpoints ({len(result.checkpoints)}):")
    for i, checkpoint in enumerate(result.checkpoints, 1):
        status_emoji = {"completed": "✅", "in_progress": "⏳", "error": "❌"}.get(
            checkpoint.status, "⚪"
        )
        print(f"   {i}. {status_emoji} {checkpoint.name}: {checkpoint.description}")
    print()
    
    print(f"🔧 Tool Calls ({len(result.tool_calls)}):")
    for i, tool_call in enumerate(result.tool_calls, 1):
        status_emoji = {"success": "✅", "in_progress": "⏳", "error": "❌"}.get(
            tool_call.status, "⚪"
        )
        print(f"   {i}. {status_emoji} {tool_call.tool_name}({list(tool_call.parameters.keys())})")
    print()
    
    if result.error_message:
        print(f"❌ Error: {result.error_message}")
    
    print("="*80)
    
    return result.success


if __name__ == "__main__":
    success = asyncio.run(test_simple_task())
    sys.exit(0 if success else 1)

