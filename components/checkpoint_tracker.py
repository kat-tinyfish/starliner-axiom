"""
Checkpoint Tracker Component - Visual progress indicators for agent execution.
"""

import streamlit as st
from typing import List
from agents.base_agent import Checkpoint


def render_checkpoint_tracker(checkpoints: List[Checkpoint], agent_name: str):
    """
    Render a checkpoint progress tracker.
    
    Args:
        checkpoints: List of checkpoints from the agent
        agent_name: Name of the agent for display
    """
    if not checkpoints:
        st.progress(0.0, text="🏁 Waiting to start...")
        return
    
    # Calculate progress
    completed_checkpoints = sum(1 for cp in checkpoints if cp.status == "completed")
    total_checkpoints = len(checkpoints)
    progress = completed_checkpoints / total_checkpoints if total_checkpoints > 0 else 0.0
    
    # Render progress bar
    st.progress(progress, text=f"{completed_checkpoints}/{total_checkpoints} checkpoints completed")
    
    # Render checkpoint icons
    checkpoint_icons = {
        "initialization": "🏁",
        "navigation": "🎯",
        "interaction": "⚡",
        "data_extraction": "📊",
        "validation": "✓",
        "completion": "✅"
    }
    
    status_icons = {
        "completed": "✅",
        "in_progress": "⏳",
        "pending": "⏸️"
    }
    
    # Display checkpoints horizontally
    cols = st.columns(len(checkpoints))
    for i, checkpoint in enumerate(checkpoints):
        with cols[i]:
            icon = checkpoint_icons.get(checkpoint.name.lower(), "📍")
            status = status_icons.get(checkpoint.status, "")
            st.markdown(f"{icon}{status}")
            st.caption(checkpoint.name)


def render_checkpoint_list(checkpoints: List[Checkpoint]):
    """
    Render checkpoints as a detailed list.
    
    Args:
        checkpoints: List of checkpoints from the agent
    """
    if not checkpoints:
        st.info("No checkpoints yet...")
        return
    
    for checkpoint in checkpoints:
        status_color = {
            "completed": "green",
            "in_progress": "orange",
            "pending": "gray"
        }.get(checkpoint.status, "gray")
        
        time_str = checkpoint.timestamp.strftime("%H:%M:%S")
        
        st.markdown(
            f":{status_color}[**{checkpoint.name}**] - {checkpoint.description} ({time_str})"
        )

