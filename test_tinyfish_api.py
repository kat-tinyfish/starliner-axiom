"""
Test script to explore TinyFish API endpoints.
"""
import httpx
import uuid
import json

TINYFISH_API = "http://54.67.10.91:8000"
USER_ID = "test-arena-user"

async def test_api():
    session_id = str(uuid.uuid4())
    
    print(f"🧪 Testing TinyFish API at {TINYFISH_API}")
    print(f"Session ID: {session_id}\n")
    
    # Test 1: Create session
    print("1️⃣ Testing session creation...")
    url = f"{TINYFISH_API}/apps/eva_agent/users/{USER_ID}/sessions/{session_id}"
    payload = {
        "task_instruction": "Go to example.com and tell me the page title",
        "browser_type": "tetra",
        "use_proxy": False
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, json=payload)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            print()
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return
    
    # Test 2: Run SSE stream
    print("2️⃣ Testing SSE stream...")
    url = f"{TINYFISH_API}/run_sse"
    payload = {
        "app_name": "eva_agent",
        "user_id": USER_ID,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": "Go to example.com"}]
        }
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            async with client.stream("POST", url, json=payload) as response:
                print(f"   Status: {response.status_code}")
                
                event_count = 0
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str:
                            event = json.loads(data_str)
                            event_count += 1
                            print(f"   Event {event_count}: {list(event.keys())}")
                            
                            if event_count >= 5:  # Just show first 5
                                print(f"   ... (stopping after 5 events)")
                                break
        except Exception as e:
            print(f"   ❌ Error: {e}\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_api())
