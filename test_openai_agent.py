#!/usr/bin/env python3
"""
Test script for OpenAI agent with native function calling.

This demonstrates the flow:
User task → GPT-4 thinks → GPT-4 chooses tools → Execute → Repeat → Result
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_openai_agent():
    """Test OpenAI agent with a simple task."""
    print("="*70)
    print("🧪 Testing OpenAI Agent with Native Function Calling")
    print("="*70)
    
    # Import agent
    from agents.implementations.openai_agent import OpenAIAgent
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Add it to your .env file")
        return
    
    # Create agent
    agent = OpenAIAgent(
        agent_id="test-gpt4",
        name="GPT-4 Test Agent",
        api_key=api_key
    )
    
    print(f"\n✅ Agent created: {agent.name}")
    print(f"   Model: {agent.model}")
    
    # Test task
    task = "Go to example.com and tell me the page title"
    
    print(f"\n📋 Task: {task}")
    print("\n" + "="*70)
    print("Starting execution...")
    print("="*70 + "\n")
    
    # Execute
    result = await agent.execute(
        prompt=task,
        constraints={"domains": ["example.com"]}
    )
    
    # Display results
    print("\n" + "="*70)
    print("📊 EXECUTION RESULTS")
    print("="*70)
    print(f"\n✅ Success: {result.success}")
    print(f"⏱️  Execution time: {result.execution_time:.2f}s")
    print(f"🔧 Tool calls made: {len(result.tool_calls)}")
    print(f"🚩 Checkpoints: {len(result.checkpoints)}")
    print(f"📸 Screenshots: {len(result.screenshots)}")
    
    if result.success:
        print(f"\n📝 Output:")
        import json
        print(json.dumps(result.output, indent=2))
    else:
        print(f"\n❌ Error: {result.error_message}")
    
    print("\n" + "="*70)
    print("🔍 DETAILED BREAKDOWN")
    print("="*70)
    
    print("\n🚩 Checkpoints:")
    for i, cp in enumerate(result.checkpoints, 1):
        status_emoji = {"completed": "✅", "error": "❌", "in_progress": "⏳"}.get(cp.status, "⚪")
        print(f"  {i}. {status_emoji} {cp.name}: {cp.description}")
    
    print("\n🔧 Tool Calls:")
    for i, tc in enumerate(result.tool_calls, 1):
        status_emoji = "✅" if tc.status == "success" else "❌"
        print(f"  {i}. {status_emoji} {tc.tool}")
        if tc.args:
            print(f"      Args: {tc.args}")
    
    print("\n" + "="*70)
    print("✨ Test complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_openai_agent())

