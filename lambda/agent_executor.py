"""
Agent Executor - Handles browser automation for agents using Playwright.

This module provides browser automation capabilities for web agents,
including navigation, interaction, and data extraction.
"""

import asyncio
import time
import os
import base64
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
import json


class AgentExecutor:
    """
    Executes agent tasks using Playwright for browser automation.
    
    This class manages the browser lifecycle and provides tools for web interaction.
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """
        Initialize executor with agent configuration.
        
        Args:
            agent_config: Agent configuration dictionary containing:
                - agent_id: Agent identifier
                - model: Model name (e.g., "gpt-4-turbo")
                - api_key: API key for the agent
                - name: Human-readable name
        """
        self.agent_config = agent_config
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.tool_calls: List[Dict[str, Any]] = []
        self.checkpoints: List[Dict[str, Any]] = []
        self.screenshots: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self._screenshot_task: Optional[asyncio.Task] = None
        self._should_capture = True
    
    async def execute(self, prompt: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task with browser automation.
        
        Args:
            prompt: Task prompt/description
            constraints: Task constraints (domains, schema, etc.)
        
        Returns:
            Execution results including:
                - success: Whether execution succeeded
                - output: Final output/result
                - tool_calls: List of tool calls made
                - checkpoints: List of checkpoints reached
                - execution_time: Total execution time
                - screenshots: List of screenshot URLs (if captured)
        """
        self.start_time = time.time()
        
        try:
            # Add initial checkpoint
            self._add_checkpoint("initialization", "Starting browser and initializing agent")
            
            async with async_playwright() as p:
                # Always use headless mode for screenshot polling
                # VNC mode is disabled - we use periodic screenshots instead
                print("🎬 Launching browser in headless mode (screenshot polling enabled)")
                
                self.browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-first-run',
                        '--no-zygote',
                        '--single-process',
                        '--disable-extensions'
                    ]
                )
                
                # Create browser context with reasonable defaults
                context = await self.browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                self.page = await context.new_page()
                
                self._add_checkpoint("browser_ready", "Browser initialized successfully")
                
                # Start screenshot capture in background
                self._screenshot_task = asyncio.create_task(self._capture_screenshots_loop(interval=2.0))
                print("📸 Screenshot capture task started")
                
                try:
                    # Execute the actual task
                    result = await self._execute_task(prompt, constraints)
                finally:
                    # Stop screenshot capture
                    self._should_capture = False
                    if self._screenshot_task:
                        try:
                            await asyncio.wait_for(self._screenshot_task, timeout=5.0)
                        except asyncio.TimeoutError:
                            self._screenshot_task.cancel()
                        print("📸 Screenshot capture task stopped")
                
                # Cleanup
                await self.browser.close()
                
                self._add_checkpoint("completion", "Task execution completed")
                
                execution_time = time.time() - self.start_time
                
                return {
                    "success": True,
                    "output": result.get("output"),
                    "tool_calls": self.tool_calls,
                    "checkpoints": self.checkpoints,
                    "execution_time": execution_time,
                    "screenshots": self.screenshots  # Include captured screenshots
                }
        
        except Exception as e:
            # Stop screenshot capture on error
            self._should_capture = False
            if self._screenshot_task:
                try:
                    self._screenshot_task.cancel()
                except:
                    pass
            
            execution_time = time.time() - self.start_time if self.start_time else 0
            self._add_checkpoint("error", f"Execution failed: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "tool_calls": self.tool_calls,
                "checkpoints": self.checkpoints,
                "execution_time": execution_time,
                "screenshots": self.screenshots  # Include screenshots even on error
            }
    
    async def _execute_task(self, prompt: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the actual task logic.
        
        For MVP, this demonstrates basic browser automation.
        In production, this would integrate with agent APIs (GPT-4, Claude, etc.)
        to make intelligent decisions.
        """
        self._add_checkpoint("planning", "Analyzing task and planning execution")
        
        # Simple example: Navigate to a URL if one is in the prompt or constraints
        output_data = []
        screenshots = []
        
        # Extract URL from prompt or constraints
        target_url = self._extract_url(prompt, constraints)
        
        if target_url:
            # Navigate to URL
            result = await self._tool_navigate(target_url)
            output_data.append(f"Navigated to {target_url}")
            
            # Wait for page load
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Extract page title
            title_result = await self._tool_get_title()
            if title_result.get("success"):
                output_data.append(f"Page title: {title_result['title']}")
            
            # Take screenshot
            screenshot = await self._tool_screenshot()
            if screenshot.get("success"):
                screenshots.append(screenshot["path"])
            
            # Extract main content if requested
            if "extract" in prompt.lower() or "content" in prompt.lower():
                content_result = await self._tool_get_content()
                if content_result.get("success"):
                    output_data.append(f"Content extracted: {content_result['content'][:200]}...")
        else:
            output_data.append("No URL found in prompt. Please provide a URL to navigate to.")
        
        return {
            "output": "\n".join(output_data),
            "screenshots": screenshots
        }
    
    def _extract_url(self, prompt: str, constraints: Dict[str, Any]) -> Optional[str]:
        """Extract URL from prompt or constraints."""
        import re
        
        # Try to find URL in prompt
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, prompt)
        
        if urls:
            return urls[0]
        
        # Check for domain in constraints
        domains = constraints.get("domains", [])
        if domains:
            domain = domains[0]
            if not domain.startswith("http"):
                domain = f"https://{domain}"
            return domain
        
        # Common domain mentions
        if "example.com" in prompt.lower():
            return "https://example.com"
        
        return None
    
    async def _tool_navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        tool_call = {
            "tool": "navigate",
            "parameters": {"url": url},
            "timestamp": time.time()
        }
        
        try:
            await self.page.goto(url, wait_until='domcontentloaded', timeout=15000)
            tool_call["status"] = "success"
            tool_call["result"] = f"Successfully navigated to {url}"
            self.tool_calls.append(tool_call)
            return {"success": True, "url": url}
        except PlaywrightTimeout:
            tool_call["status"] = "error"
            tool_call["error"] = "Navigation timeout"
            self.tool_calls.append(tool_call)
            return {"success": False, "error": "Navigation timeout"}
        except Exception as e:
            tool_call["status"] = "error"
            tool_call["error"] = str(e)
            self.tool_calls.append(tool_call)
            return {"success": False, "error": str(e)}
    
    async def _tool_get_title(self) -> Dict[str, Any]:
        """Get page title."""
        tool_call = {
            "tool": "get_title",
            "parameters": {},
            "timestamp": time.time()
        }
        
        try:
            title = await self.page.title()
            tool_call["status"] = "success"
            tool_call["result"] = title
            self.tool_calls.append(tool_call)
            return {"success": True, "title": title}
        except Exception as e:
            tool_call["status"] = "error"
            tool_call["error"] = str(e)
            self.tool_calls.append(tool_call)
            return {"success": False, "error": str(e)}
    
    async def _tool_get_content(self) -> Dict[str, Any]:
        """Extract page content."""
        tool_call = {
            "tool": "get_content",
            "parameters": {},
            "timestamp": time.time()
        }
        
        try:
            content = await self.page.evaluate("""
                () => {
                    const body = document.body;
                    return body ? body.innerText : '';
                }
            """)
            tool_call["status"] = "success"
            tool_call["result"] = f"Extracted {len(content)} characters"
            self.tool_calls.append(tool_call)
            return {"success": True, "content": content}
        except Exception as e:
            tool_call["status"] = "error"
            tool_call["error"] = str(e)
            self.tool_calls.append(tool_call)
            return {"success": False, "error": str(e)}
    
    async def _tool_screenshot(self, full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot."""
        tool_call = {
            "tool": "screenshot",
            "parameters": {"full_page": full_page},
            "timestamp": time.time()
        }
        
        try:
            # In Lambda, you'd save to /tmp and upload to S3
            screenshot_path = f"/tmp/screenshot_{int(time.time())}.png"
            await self.page.screenshot(path=screenshot_path, full_page=full_page)
            
            tool_call["status"] = "success"
            tool_call["result"] = screenshot_path
            self.tool_calls.append(tool_call)
            return {"success": True, "path": screenshot_path}
        except Exception as e:
            tool_call["status"] = "error"
            tool_call["error"] = str(e)
            self.tool_calls.append(tool_call)
            return {"success": False, "error": str(e)}
    
    async def _capture_screenshots_loop(self, interval: float = 2.0):
        """
        Background task to capture screenshots periodically.
        
        Args:
            interval: Time between screenshots in seconds (default: 2.0)
        """
        print(f"📸 Starting screenshot capture loop (interval: {interval}s)")
        screenshot_count = 0
        
        while self._should_capture and self.page:
            try:
                # Capture screenshot as bytes
                screenshot_bytes = await self.page.screenshot()
                
                # Convert to base64 for JSON transport
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                # Store with metadata
                self.screenshots.append({
                    'timestamp': time.time(),
                    'elapsed': time.time() - self.start_time if self.start_time else 0,
                    'data': screenshot_b64,
                    'format': 'png',
                    'index': screenshot_count
                })
                
                screenshot_count += 1
                
                # Wait before next capture
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"Screenshot capture error: {e}")
                # Continue on error - don't break the loop
                await asyncio.sleep(interval)
        
        print(f"📸 Screenshot capture loop ended. Captured {screenshot_count} screenshots")
    
    async def _tool_click(self, selector: str) -> Dict[str, Any]:
        """Click an element."""
        tool_call = {
            "tool": "click",
            "parameters": {"selector": selector},
            "timestamp": time.time()
        }
        
        try:
            await self.page.click(selector, timeout=5000)
            tool_call["status"] = "success"
            tool_call["result"] = f"Clicked {selector}"
            self.tool_calls.append(tool_call)
            return {"success": True}
        except Exception as e:
            tool_call["status"] = "error"
            tool_call["error"] = str(e)
            self.tool_calls.append(tool_call)
            return {"success": False, "error": str(e)}
    
    async def _tool_type(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into an input."""
        tool_call = {
            "tool": "type",
            "parameters": {"selector": selector, "text": text},
            "timestamp": time.time()
        }
        
        try:
            await self.page.fill(selector, text, timeout=5000)
            tool_call["status"] = "success"
            tool_call["result"] = f"Typed into {selector}"
            self.tool_calls.append(tool_call)
            return {"success": True}
        except Exception as e:
            tool_call["status"] = "error"
            tool_call["error"] = str(e)
            self.tool_calls.append(tool_call)
            return {"success": False, "error": str(e)}
    
    def _add_checkpoint(self, name: str, description: str):
        """Add a checkpoint to track progress."""
        self.checkpoints.append({
            "name": name,
            "description": description,
            "timestamp": time.time(),
            "status": "completed"
        })


# For local testing
if __name__ == "__main__":
    print("Testing AgentExecutor locally...")
    print("=" * 60)
    
    async def test():
        executor = AgentExecutor({
            "agent_id": "test-agent",
            "name": "Test Agent"
        })
        
        result = await executor.execute(
            prompt="Go to example.com and get the page title",
            constraints={}
        )
        
        print("\nExecution Result:")
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(test())
