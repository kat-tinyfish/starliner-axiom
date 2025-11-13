"""
Browser Tool Definitions for Web Agent Arena.

This module defines a universal set of browser tools that all agents can use,
with schemas compatible with OpenAI, Anthropic, and Google function calling APIs.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class BrowserTool:
    """Represents a browser tool with unified schema."""
    name: str
    description: str
    parameters: Dict[str, Any]


# ============================================================================
# UNIVERSAL BROWSER TOOL DEFINITIONS
# ============================================================================

BROWSER_TOOLS = [
    BrowserTool(
        name="navigate",
        description="Navigate the browser to a specific URL. Use this when you need to visit a webpage.",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The complete URL to navigate to (e.g., https://example.com)"
                },
                "wait_for": {
                    "type": "string",
                    "description": "Optional CSS selector to wait for after navigation",
                    "default": None
                }
            },
            "required": ["url"]
        }
    ),
    
    BrowserTool(
        name="click",
        description="Click on an element on the page. Use this to interact with buttons, links, or clickable elements.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector or text content to identify the element (e.g., 'button.submit', 'a[href]', or 'text:Login')"
                },
                "wait_after": {
                    "type": "number",
                    "description": "Milliseconds to wait after clicking (default: 500)",
                    "default": 500
                }
            },
            "required": ["selector"]
        }
    ),
    
    BrowserTool(
        name="type_text",
        description="Type text into an input field. Use this to fill forms or enter search queries.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the input field (e.g., 'input[name=\"search\"]', '#email')"
                },
                "text": {
                    "type": "string",
                    "description": "The text to type into the field"
                },
                "press_enter": {
                    "type": "boolean",
                    "description": "Whether to press Enter after typing (default: false)",
                    "default": False
                }
            },
            "required": ["selector", "text"]
        }
    ),
    
    BrowserTool(
        name="extract_content",
        description="Extract specific content from the current page. Use this to read text, get attribute values, or scrape data.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the element(s) to extract (e.g., 'h1', '.price', 'a[href]')"
                },
                "attribute": {
                    "type": "string",
                    "description": "Optional attribute to extract (e.g., 'href', 'src'). If not provided, extracts text content.",
                    "default": "textContent"
                },
                "multiple": {
                    "type": "boolean",
                    "description": "Whether to extract from all matching elements (default: false)",
                    "default": False
                }
            },
            "required": ["selector"]
        }
    ),
    
    BrowserTool(
        name="get_page_info",
        description="Get information about the current page (title, URL, metadata). Use this to understand where you are.",
        parameters={
            "type": "object",
            "properties": {
                "include_html": {
                    "type": "boolean",
                    "description": "Whether to include page HTML (default: false)",
                    "default": False
                }
            },
            "required": []
        }
    ),
    
    BrowserTool(
        name="scroll",
        description="Scroll the page up or down. Use this to view content not currently visible.",
        parameters={
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "top", "bottom"],
                    "description": "Direction to scroll"
                },
                "amount": {
                    "type": "number",
                    "description": "Pixels to scroll (for up/down, default: 500)",
                    "default": 500
                }
            },
            "required": ["direction"]
        }
    ),
    
    BrowserTool(
        name="wait",
        description="Wait for a specified amount of time or for an element to appear. Use this when content loads dynamically.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "Optional CSS selector to wait for",
                    "default": None
                },
                "timeout": {
                    "type": "number",
                    "description": "Maximum time to wait in milliseconds (default: 3000)",
                    "default": 3000
                }
            },
            "required": []
        }
    ),
    
    BrowserTool(
        name="go_back",
        description="Navigate back to the previous page in browser history.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    
    BrowserTool(
        name="screenshot",
        description="Take a screenshot of the current page or a specific element.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "Optional CSS selector to screenshot specific element",
                    "default": None
                },
                "full_page": {
                    "type": "boolean",
                    "description": "Capture full scrollable page (default: false)",
                    "default": False
                }
            },
            "required": []
        }
    )
]


# ============================================================================
# FORMAT CONVERTERS FOR DIFFERENT LLM PROVIDERS
# ============================================================================

def get_openai_tools() -> List[Dict[str, Any]]:
    """
    Convert browser tools to OpenAI function calling format.
    
    Returns:
        List of tool definitions for OpenAI API
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        }
        for tool in BROWSER_TOOLS
    ]


def get_anthropic_tools() -> List[Dict[str, Any]]:
    """
    Convert browser tools to Anthropic tool use format.
    
    Returns:
        List of tool definitions for Anthropic API
    """
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.parameters
        }
        for tool in BROWSER_TOOLS
    ]


def get_google_tools() -> List[Dict[str, Any]]:
    """
    Convert browser tools to Google (Gemini) function calling format.
    
    Returns:
        List of tool definitions for Google API
    """
    # Google uses similar format to OpenAI but with slight differences
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
        for tool in BROWSER_TOOLS
    ]


# ============================================================================
# TOOL DESCRIPTIONS FOR SYSTEM PROMPTS
# ============================================================================

def get_tools_description() -> str:
    """
    Get a text description of all available browser tools.
    Useful for including in system prompts.
    
    Returns:
        Formatted string describing all tools
    """
    descriptions = ["Available Browser Tools:"]
    for i, tool in enumerate(BROWSER_TOOLS, 1):
        descriptions.append(f"\n{i}. {tool.name}:")
        descriptions.append(f"   {tool.description}")
        if tool.parameters.get("properties"):
            descriptions.append("   Parameters:")
            for param_name, param_info in tool.parameters["properties"].items():
                required = param_name in tool.parameters.get("required", [])
                req_str = " (required)" if required else " (optional)"
                descriptions.append(f"   - {param_name}{req_str}: {param_info.get('description', '')}")
    
    return "\n".join(descriptions)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tool_by_name(name: str) -> BrowserTool:
    """Get a tool definition by name."""
    for tool in BROWSER_TOOLS:
        if tool.name == name:
            return tool
    raise ValueError(f"Tool '{name}' not found")


def validate_tool_call(name: str, arguments: Dict[str, Any]) -> bool:
    """
    Validate that a tool call has all required parameters.
    
    Args:
        name: Tool name
        arguments: Tool arguments
    
    Returns:
        True if valid, False otherwise
    """
    try:
        tool = get_tool_by_name(name)
        required_params = tool.parameters.get("required", [])
        
        for param in required_params:
            if param not in arguments:
                return False
        
        return True
    except ValueError:
        return False

