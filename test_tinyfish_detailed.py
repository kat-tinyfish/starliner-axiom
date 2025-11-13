"""
Detailed TinyFish API test to see event structure.
"""
import httpx
import uuid
import json
import asyncio

TINYFISH_API = "http://54.67.10.91:8000"
USER_ID = "test-arena-user"

async def test_detailed():
    session_id = str(uuid.uuid4())
    
    print(f"🔍 Detailed TinyFish API Test")
    print(f"Session ID: {session_id}\n")
    
    # Create session
    url = f"{TINYFISH_API}/apps/eva_agent/users/{USER_ID}/sessions/{session_id}"
    payload = {
        "task_instruction": "Go to example.com and extract the main heading text",
        "browser_type": "tetra",
        "use_proxy": False
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload)
        print(f"✅ Session created: {response.status_code}\n")
    
    # Run SSE stream with detailed logging
    url = f"{TINYFISH_API}/run_sse"
    payload = {
        "app_name": "eva_agent",
        "user_id": USER_ID,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": "Go to example.com and extract the main heading"}]
        }
    }
    
    print("📡 SSE Stream Events:\n" + "="*80)
    
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload) as response:
            event_count = 0
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str:
                        event = json.loads(data_str)
                        event_count += 1
                        
                        print(f"\n📦 Event {event_count}:")
                        print(f"   Author: {event.get('author', 'N/A')}")
                        print(f"   Finish Reason: {event.get('finishReason', 'N/A')}")
                        
                        # Content
                        content = event.get('content', {})
                        if isinstance(content, dict):
                            text = content.get('text', '')
                            if text:
                                print(f"   Content Text: {text[:100]}...")
                            parts = content.get('parts', [])
                            if parts:
                                print(f"   Content Parts: {len(parts)} parts")
                                for i, part in enumerate(parts[:2]):  # First 2 parts
                                    print(f"      Part {i+1}: {list(part.keys())}")
                        elif content:
                            print(f"   Content: {str(content)[:100]}")
                        
                        # Actions
                        actions = event.get('actions')
                        if actions:
                            if isinstance(actions, list):
                                print(f"   Actions: {len(actions)} actions")
                                for i, action in enumerate(actions[:3]):  # First 3 actions
                                    print(f"      Action {i+1}: {action.get('type', 'unknown')}")
                                    if 'args' in action:
                                        print(f"         Args: {list(action['args'].keys())}")
                            else:
                                print(f"   Actions (non-list): {type(actions).__name__}")
                                print(f"      {str(actions)[:200]}")
                        
                        # Usage
                        usage = event.get('usageMetadata', {})
                        if usage:
                            print(f"   Tokens: {usage.get('totalTokenCount', 0)}")
                        
                        if event_count >= 10:  # Show first 10 events
                            print(f"\n   ... (showing first 10 events)")
                            break
    
    print("\n" + "="*80)
    print(f"✅ Total events processed: {event_count}")

if __name__ == "__main__":
    asyncio.run(test_detailed())
