"""
BrowserBase API Client for Web Agent Arena.

This client replaces the Lambda/Playwright setup with BrowserBase's managed
browser infrastructure, which handles all the complexity of running browsers
in the cloud.

API Docs: https://docs.browserbase.com/
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
import time
import base64

try:
    import aiohttp
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "aiohttp"])
    import aiohttp


class BrowserBaseClient:
    """Client for BrowserBase API."""
    
    def __init__(self, api_key: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initialize BrowserBase client.
        
        Args:
            api_key: BrowserBase API key (defaults to BROWSERBASE_API_KEY env var)
            project_id: BrowserBase project ID (defaults to BROWSERBASE_PROJECT_ID env var)
        """
        self.api_key = api_key or os.getenv("BROWSERBASE_API_KEY")
        self.project_id = project_id or os.getenv("BROWSERBASE_PROJECT_ID")
        
        if not self.api_key:
            raise ValueError("BROWSERBASE_API_KEY is required")
        if not self.project_id:
            raise ValueError("BROWSERBASE_PROJECT_ID is required")
        
        self.base_url = "https://www.browserbase.com/v1"
        self.headers = {
            "x-bb-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_session(self, proxies: bool = False) -> Dict[str, Any]:
        """
        Create a new browser session.
        
        Args:
            proxies: Whether to use proxies (requires paid tier)
        
        Returns:
            Dict with session info including session_id and ws_url
        """
        async with aiohttp.ClientSession() as session:
            payload = {
                "projectId": self.project_id,
                "browserSettings": {
                    "viewport": {
                        "width": 1280,
                        "height": 720
                    }
                }
            }
            
            if proxies:
                payload["proxies"] = True
            
            async with session.post(
                f"{self.base_url}/sessions",
                headers=self.headers,
                json=payload
            ) as resp:
                if resp.status != 201:
                    text = await resp.text()
                    raise Exception(f"Failed to create session: {resp.status} - {text}")
                
                return await resp.json()
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session info."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/sessions/{session_id}",
                headers=self.headers
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Failed to get session: {resp.status} - {text}")
                
                return await resp.json()
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a browser session."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/sessions/{session_id}/end",
                headers=self.headers
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Failed to end session: {resp.status} - {text}")
                
                return await resp.json()
    
    async def get_screenshot(self, session_id: str, fullPage: bool = False) -> bytes:
        """
        Get a screenshot of the current page.
        
        Args:
            session_id: Session ID
            fullPage: Whether to capture the full scrollable page
        
        Returns:
            PNG image as bytes
        """
        async with aiohttp.ClientSession() as session:
            params = {"fullPage": "true" if fullPage else "false"}
            
            async with session.get(
                f"{self.base_url}/sessions/{session_id}/screenshot",
                headers=self.headers,
                params=params
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Failed to get screenshot: {resp.status} - {text}")
                
                return await resp.read()
    
    async def get_debug_connection_url(self, session_id: str) -> str:
        """
        Get Chrome DevTools Protocol debug URL.
        This can be used to connect Playwright/Puppeteer to the remote browser.
        
        Returns:
            WebSocket URL for CDP connection
        """
        session_info = await self.get_session(session_id)
        return session_info.get("debuggerUrl", "")
    
    async def execute_agent_task(
        self,
        prompt: str,
        agent_config: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
        screenshot_interval: float = 2.0
    ) -> Dict[str, Any]:
        """
        Execute a web agent task using BrowserBase.
        
        This replaces the Lambda agent_executor.py functionality.
        
        Args:
            prompt: Natural language task description
            agent_config: Agent configuration (model, API keys, etc.)
            constraints: Optional constraints (domains, etc.)
            screenshot_interval: Seconds between screenshot captures
        
        Returns:
            Dict with execution results, screenshots, tool calls, checkpoints
        """
        start_time = time.time()
        screenshots = []
        tool_calls = []
        checkpoints = []
        
        session_id = None
        
        try:
            # Create browser session
            checkpoints.append({
                "name": "initialization",
                "description": "Creating BrowserBase session",
                "timestamp": time.time(),
                "status": "completed"
            })
            
            session_data = await self.create_session()
            session_id = session_data["id"]
            
            # BrowserBase returns connectUrl directly in the creation response
            debug_url = session_data.get("connectUrl")
            
            if not debug_url:
                print(f"⚠️ Session creation response: {session_data.keys()}")
                raise Exception(f"No CDP connection URL in session creation. Available fields: {list(session_data.keys())}")
            
            checkpoints.append({
                "name": "browser_ready",
                "description": "Browser session created successfully",
                "timestamp": time.time(),
                "status": "completed"
            })
            
            print(f"🔗 Connecting to remote browser via CDP: {debug_url[:60]}...")
            
            # Connect Playwright to BrowserBase remote browser
            try:
                from playwright.async_api import async_playwright
                
                async with async_playwright() as p:
                    # Connect to the remote browser
                    browser = await p.chromium.connect_over_cdp(debug_url)
                    
                    # Get the default context (BrowserBase creates one for us)
                    contexts = browser.contexts
                    if not contexts:
                        raise Exception("No browser contexts available")
                    
                    context = contexts[0]
                    pages = context.pages
                    
                    # Get or create a page
                    if pages:
                        page = pages[0]
                    else:
                        page = await context.new_page()
                    
                    print(f"✅ Connected to remote browser successfully")
                    
                    checkpoints.append({
                        "name": "planning",
                        "description": "Analyzing task and planning execution",
                        "timestamp": time.time(),
                        "status": "completed"
                    })
                    
                    tool_calls.append({
                        "timestamp": time.time(),
                        "tool": "navigate",
                        "args": {"url": prompt},
                        "status": "starting"
                    })
                    
                    # Start screenshot capture in background
                    screenshot_task = asyncio.create_task(
                        self._capture_screenshots_loop(
                            session_id,
                            screenshots,
                            interval=screenshot_interval,
                            start_time=start_time
                        )
                    )
                    
                    # Navigate to the URL (extract from prompt or constraints)
                    target_url = self._extract_url(prompt, constraints or {})
                    
                    if target_url:
                        print(f"🌐 Navigating to: {target_url}")
                        await page.goto(target_url, wait_until="networkidle", timeout=30000)
                        
                        tool_calls[-1]["status"] = "success"
                        tool_calls[-1]["result"] = f"Navigated to {target_url}"
                        
                        checkpoints.append({
                            "name": "navigation_complete",
                            "description": f"Successfully loaded {target_url}",
                            "timestamp": time.time(),
                            "status": "completed"
                        })
                        
                        # Get page info
                        title = await page.title()
                        url = page.url
                        
                        tool_calls.append({
                            "timestamp": time.time(),
                            "tool": "extract_info",
                            "args": {},
                            "status": "success",
                            "result": {"title": title, "url": url}
                        })
                    else:
                        print(f"⚠️ No URL found in prompt, staying on blank page")
                    
                    # Wait a bit for screenshots to capture
                    await asyncio.sleep(3)
                    
            except Exception as e:
                print(f"❌ Playwright connection failed: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            
            # Stop screenshot capture
            screenshot_task.cancel()
            try:
                await screenshot_task
            except asyncio.CancelledError:
                pass
            
            checkpoints.append({
                "name": "completion",
                "description": "Task completed successfully",
                "timestamp": time.time(),
                "status": "completed"
            })
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "session_id": session_id,
                "output_data": {"result": "Task execution simulated (MVP)"},
                "tool_calls": tool_calls,
                "checkpoints": checkpoints,
                "execution_time": execution_time,
                "screenshots": screenshots
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            checkpoints.append({
                "name": "error",
                "description": f"Execution failed: {str(e)}",
                "timestamp": time.time(),
                "status": "completed"
            })
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "tool_calls": tool_calls,
                "checkpoints": checkpoints,
                "execution_time": execution_time,
                "screenshots": screenshots
            }
        
        finally:
            # Clean up session
            if session_id:
                try:
                    await self.end_session(session_id)
                except Exception as e:
                    print(f"Warning: Failed to end session {session_id}: {e}")
    
    def _extract_url(self, prompt: str, constraints: Dict[str, Any]) -> Optional[str]:
        """Extract URL from prompt or constraints."""
        import re
        
        # Check constraints first
        if "domains" in constraints and constraints["domains"]:
            domain = constraints["domains"][0]
            if not domain.startswith("http"):
                domain = f"https://{domain}"
            return domain
        
        # Look for URLs in prompt
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, prompt)
        if urls:
            return urls[0]
        
        # Look for domain names
        domain_pattern = r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, prompt)
        if domains:
            return f"https://{domains[0]}"
        
        return None
    
    async def _capture_screenshots_loop(
        self,
        session_id: str,
        screenshots: List[Dict[str, Any]],
        interval: float,
        start_time: float
    ):
        """Capture screenshots periodically."""
        try:
            while True:
                await asyncio.sleep(interval)
                
                try:
                    screenshot_bytes = await self.get_screenshot(session_id)
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    screenshots.append({
                        "index": len(screenshots),
                        "elapsed": time.time() - start_time,
                        "timestamp": time.time(),
                        "data": screenshot_b64
                    })
                    
                    print(f"📸 Captured screenshot {len(screenshots)} at {time.time() - start_time:.1f}s")
                    
                except Exception as e:
                    print(f"Warning: Failed to capture screenshot: {e}")
                    
        except asyncio.CancelledError:
            print(f"Screenshot capture stopped. Total screenshots: {len(screenshots)}")
            raise


# CLI for testing
if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    async def test():
        client = BrowserBaseClient()
        
        print("🧪 Testing BrowserBase integration...")
        
        result = await client.execute_agent_task(
            prompt="Go to example.com",
            agent_config={"agent_id": "test", "model": "gpt-4"},
            constraints={"domains": ["example.com"]}
        )
        
        print(f"\n✅ Success: {result['success']}")
        if not result['success']:
            print(f"❌ Error: {result.get('error', 'Unknown')}")
            print(f"   Type: {result.get('error_type', 'Unknown')}")
        print(f"📸 Screenshots: {len(result['screenshots'])}")
        print(f"⏱️  Execution time: {result['execution_time']:.2f}s")
        print(f"🚩 Checkpoints: {len(result['checkpoints'])}")
        print(f"🔧 Tool calls: {len(result['tool_calls'])}")
    
    asyncio.run(test())

