"""
Web Agent Arena - Main Streamlit Application
A live web agent comparison platform for head-to-head agent battles.
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Page configuration
st.set_page_config(
    page_title="Web Agent Arena",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh for real-time updates (every 2 seconds during active race)
if "race_active" in st.session_state and st.session_state.race_active:
    st_autorefresh(interval=2000, key="race_refresh")


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "arena"
    
    if "race_active" not in st.session_state:
        st.session_state.race_active = False
    
    if "agent_a" not in st.session_state:
        st.session_state.agent_a = None
    
    if "agent_b" not in st.session_state:
        st.session_state.agent_b = None
    
    if "current_prompt" not in st.session_state:
        st.session_state.current_prompt = ""
    
    if "race_id" not in st.session_state:
        st.session_state.race_id = None


def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Header with navigation
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🏆 Web Agent Arena")
    
    with col2:
        if st.button("Arena", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "arena" else "secondary"):
            st.session_state.current_page = "arena"
            st.rerun()
    
    with col3:
        if st.button("Dashboard", use_container_width=True,
                    type="primary" if st.session_state.current_page == "dashboard" else "secondary"):
            st.session_state.current_page = "dashboard"
            st.rerun()
    
    st.divider()
    
    # Route to appropriate page
    if st.session_state.current_page == "arena":
        show_arena_page()
    else:
        show_dashboard_page()


def show_arena_page():
    """Display the main arena page."""
    from components.arena import render_arena
    render_arena()


def show_dashboard_page():
    """Display the dashboard page."""
    from components.dashboard import render_dashboard
    render_dashboard()


if __name__ == "__main__":
    main()

