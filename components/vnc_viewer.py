"""
VNC Viewer Component - Embeds noVNC iframe for browser streaming.
"""

import streamlit as st
import streamlit.components.v1 as components


def render_vnc_viewer(vnc_url: str, width: int = 800, height: int = 600):
    """
    Render a VNC viewer iframe.
    
    Args:
        vnc_url: URL to the noVNC web client
        width: Width of the iframe in pixels
        height: Height of the iframe in pixels
    """
    # Use Streamlit's iframe component
    # TODO: Test with actual VNC server
    components.iframe(vnc_url, width=width, height=height, scrolling=False)


def render_vnc_with_controls(vnc_url: str, agent_name: str):
    """
    Render VNC viewer with additional controls.
    
    Args:
        vnc_url: URL to the noVNC web client
        agent_name: Name of the agent for display
    """
    st.markdown(f"**{agent_name} Browser Session**")
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh", key=f"refresh_{agent_name}"):
            st.rerun()
    with col2:
        if st.button("📸 Screenshot", key=f"screenshot_{agent_name}"):
            st.info("Screenshot saved!")
    with col3:
        fullscreen = st.checkbox("Fullscreen", key=f"fullscreen_{agent_name}")
    
    # Render VNC viewer
    height = 800 if fullscreen else 600
    render_vnc_viewer(vnc_url, height=height)

