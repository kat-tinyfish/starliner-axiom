"""
Tool Call Panel Component - Displays agent tool calls in real-time.
"""

import streamlit as st
from typing import List
from agents.base_agent import ToolCall


def render_tool_call_panel(tool_calls: List[ToolCall], agent_name: str):
    """
    Render a tool call panel showing agent actions.
    
    Args:
        tool_calls: List of tool calls from the agent
        agent_name: Name of the agent for display
    """
    st.markdown(f"**Tool Calls - {agent_name}**")
    
    if not tool_calls:
        st.text("No tool calls yet...")
        return
    
    # Create a scrollable container
    with st.container():
        for tool_call in tool_calls[-10:]:  # Show last 10 calls
            status_icon = {
                "in_progress": "⏳",
                "success": "✅",
                "error": "❌"
            }.get(tool_call.status, "❓")
            
            # Format timestamp
            time_str = tool_call.timestamp.strftime("%H:%M:%S")
            
            # Display tool call
            col1, col2 = st.columns([1, 4])
            with col1:
                st.text(f"{status_icon} {time_str}")
            with col2:
                st.text(f"{tool_call.tool_name}")
                
                # Show parameters in expander
                if tool_call.parameters:
                    with st.expander("Details", expanded=False):
                        st.json(tool_call.parameters)
                
                if tool_call.error_message:
                    st.error(tool_call.error_message)


def render_tool_call_sidebar(tool_calls: List[ToolCall], key: str):
    """
    Render tool calls in a sidebar-style layout.
    
    Args:
        tool_calls: List of tool calls from the agent
        key: Unique key for the component
    """
    # TODO: Implement sidebar-style tool call display
    # This will be integrated into the main arena layout
    pass

