"""
Browser Tool Executor for Web Agent Arena.

This module executes browser tool calls using Playwright connected to BrowserBase.
It translates high-level tool calls (navigate, click, type) into actual browser actions.
"""

import asyncio
import base64
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


@dataclass
class ToolExecutionResult:
    """Result of executing a browser tool."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    screenshot: Optional[str] = None  # Base64 encoded
    execution_time: float = 0.0


class BrowserToolExecutor:
    """
    Executes browser tool calls using Playwright.
    
    This class maintains a browser session and executes tool calls
    like navigate, click, type, etc. It connects to BrowserBase for
    cloud browser execution.
    """
    
    def __init__(self, browserbase_session_id: Optional[str] = None,
                 browserbase_connect_url: Optional[str] = None):
        """
        Initialize the browser tool executor.
        
        Args:
            browserbase_session_id: BrowserBase session ID (if using BrowserBase)
            browserbase_connect_url: CDP connection URL for BrowserBase
        """
        self.session_id = browserbase_session_id
        self.connect_url = browserbase_connect_url
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def __aenter__(self):
        """Context manager entry - initialize browser."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser."""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize the browser connection."""
        if not self.connect_url:
            raise Exception(
                "BrowserBase connection required. "
                "Local Playwright not supported in cloud deployments. "
                "Please configure BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID."
            )
        
        self.playwright = await async_playwright().start()
        
        # Connect to BrowserBase via CDP
        self.browser = await self.playwright.chromium.connect_over_cdp(
            self.connect_url
        )
        
        # Get default context from BrowserBase
        contexts = self.browser.contexts
        if contexts:
            self.context = contexts[0]
            pages = self.context.pages
            self.page = pages[0] if pages else await self.context.new_page()
        else:
            raise Exception("No browser context available from BrowserBase")
    
    async def cleanup(self):
        """Cleanup browser resources."""
        # Note: For BrowserBase, we don't close page/context/browser
        # as they're managed by BrowserBase and closed via their API
        if self.playwright:
            await self.playwright.stop()
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute a browser tool call.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
        
        Returns:
            ToolExecutionResult with success status and data
        """
        start_time = time.time()
        
        try:
            # Route to appropriate handler
            handler = getattr(self, f"_handle_{tool_name}", None)
            if not handler:
                return ToolExecutionResult(
                    success=False,
                    error=f"Unknown tool: {tool_name}"
                )
            
            # Execute the tool
            result_data = await handler(arguments)
            
            # Capture screenshot after action
            screenshot = await self._capture_screenshot()
            
            execution_time = time.time() - start_time
            
            return ToolExecutionResult(
                success=True,
                data=result_data,
                screenshot=screenshot,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    # ========================================================================
    # TOOL HANDLERS
    # ========================================================================
    
    async def _handle_navigate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL."""
        url = args["url"]
        wait_for = args.get("wait_for")
        
        await self.page.goto(url, wait_until="networkidle", timeout=30000)
        
        if wait_for:
            await self.page.wait_for_selector(wait_for, timeout=10000)
        
        return {
            "url": self.page.url,
            "title": await self.page.title()
        }
    
    async def _handle_click(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Click an element."""
        selector = args["selector"]
        wait_after = args.get("wait_after", 500)
        
        # Handle text-based selectors
        if selector.startswith("text:"):
            text = selector[5:]
            await self.page.click(f"text={text}")
        else:
            await self.page.click(selector)
        
        # Wait after click for page to update
        await asyncio.sleep(wait_after / 1000)
        
        return {
            "clicked": selector,
            "current_url": self.page.url
        }
    
    async def _handle_type_text(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into an input field."""
        selector = args["selector"]
        text = args["text"]
        press_enter = args.get("press_enter", False)
        
        await self.page.fill(selector, text)
        
        if press_enter:
            await self.page.press(selector, "Enter")
            await asyncio.sleep(0.5)  # Wait for potential page load
        
        return {
            "typed": len(text),
            "selector": selector
        }
    
    async def _handle_extract_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from the page."""
        selector = args["selector"]
        attribute = args.get("attribute", "textContent")
        multiple = args.get("multiple", False)
        
        if multiple:
            elements = await self.page.query_selector_all(selector)
            if attribute == "textContent":
                content = [await el.text_content() for el in elements]
            else:
                content = [await el.get_attribute(attribute) for el in elements]
        else:
            element = await self.page.query_selector(selector)
            if not element:
                return {"content": None, "found": False}
            
            if attribute == "textContent":
                content = await element.text_content()
            else:
                content = await element.get_attribute(attribute)
        
        return {
            "content": content,
            "found": True,
            "count": len(content) if multiple else 1
        }
    
    async def _handle_get_page_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about the current page."""
        include_html = args.get("include_html", False)
        
        info = {
            "url": self.page.url,
            "title": await self.page.title(),
        }
        
        if include_html:
            info["html"] = await self.page.content()
        
        return info
    
    async def _handle_scroll(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll the page."""
        direction = args["direction"]
        amount = args.get("amount", 500)
        
        if direction == "down":
            await self.page.evaluate(f"window.scrollBy(0, {amount})")
        elif direction == "up":
            await self.page.evaluate(f"window.scrollBy(0, -{amount})")
        elif direction == "top":
            await self.page.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        return {"scrolled": direction}
    
    async def _handle_wait(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for time or element."""
        selector = args.get("selector")
        timeout = args.get("timeout", 3000)
        
        if selector:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {"waited_for": selector, "found": True}
        else:
            await asyncio.sleep(timeout / 1000)
            return {"waited": timeout}
    
    async def _handle_go_back(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate back in history."""
        await self.page.go_back()
        return {
            "url": self.page.url,
            "title": await self.page.title()
        }
    
    async def _handle_screenshot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot."""
        selector = args.get("selector")
        full_page = args.get("full_page", False)
        
        if selector:
            element = await self.page.query_selector(selector)
            if element:
                screenshot_bytes = await element.screenshot()
            else:
                return {"error": "Element not found"}
        else:
            screenshot_bytes = await self.page.screenshot(full_page=full_page)
        
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
        
        return {
            "screenshot": screenshot_b64,
            "size": len(screenshot_bytes)
        }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _capture_screenshot(self, full_page: bool = False) -> str:
        """Capture a screenshot of the current page."""
        try:
            screenshot_bytes = await self.page.screenshot(full_page=full_page)
            return base64.b64encode(screenshot_bytes).decode()
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            return ""
    
    async def get_page_state(self) -> Dict[str, Any]:
        """Get current page state for agent context."""
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "timestamp": time.time()
        }

