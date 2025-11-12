"""
Dashboard Component - Leaderboard and analytics dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def render_dashboard():
    """
    Render the dashboard with leaderboard and analytics.
    """
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🏆 Leaderboard", "🔥 Top Matchups", "📈 Performance"])
    
    with tab1:
        render_leaderboard()
    
    with tab2:
        render_top_matchups()
    
    with tab3:
        render_trends()


def render_leaderboard():
    """Render the agent leaderboard."""
    st.markdown("### 🏆 Agent Rankings")
    
    # Get real data from database
    try:
        from database.operations import get_db
        db_ops = get_db()
        leaderboard = db_ops.get_leaderboard()
        
        # Convert to DataFrame
        data = {
            "Agent": [],
            "Total Races": [],
            "Wins": [],
            "Losses": [],
            "Win Rate": [],
            "Avg Time (s)": []
        }
        
        for entry in leaderboard:
            # Get agent info
            agents = entry.get('agents', {})
            if isinstance(agents, dict):
                agent_name = agents.get('display_name', 'Unknown')
            else:
                agent_name = 'Unknown'
            
            data["Agent"].append(agent_name)
            data["Total Races"].append(entry.get('total_races', 0))
            data["Wins"].append(entry.get('wins', 0))
            data["Losses"].append(entry.get('losses', 0))
            data["Win Rate"].append(entry.get('win_rate', 0.0))
            data["Avg Time (s)"].append(entry.get('avg_execution_time', 0.0) or 0.0)
        
        df = pd.DataFrame(data)
        
        if len(df) == 0:
            st.info("No race data yet. Start racing to build the leaderboard!")
            return
            
    except Exception as e:
        st.error(f"Error loading leaderboard: {str(e)}")
        # Fall back to empty data
        df = pd.DataFrame({
            "Agent": [],
            "Total Races": [],
            "Wins": [],
            "Losses": [],
            "Win Rate": [],
            "Avg Time (s)": []
        })
    
    # Add rank
    df["Rank"] = range(1, len(df) + 1)
    
    # Reorder columns
    df = df[["Rank", "Agent", "Total Races", "Wins", "Losses", "Win Rate", "Avg Time (s)"]]
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Chart
    st.markdown("### Win Rate Comparison")
    fig = px.bar(
        df,
        x="Agent",
        y="Win Rate",
        color="Win Rate",
        color_continuous_scale="RdYlGn",
        labels={"Win Rate": "Win Rate (%)"}
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_top_matchups():
    """Render top agent matchups."""
    st.markdown("### 🔥 Most Popular Matchups")
    
    # Get real data from database
    try:
        from database.operations import get_db
        db_ops = get_db()
        
        # Get races and count matchups
        races = db_ops.get_recent_races(limit=100)
        
        if not races:
            st.info("💡 No matchup data yet. Create races to see popular agent pairings!")
            return
        
        # Count matchups
        matchup_counts = {}
        for race in races:
            key = tuple(sorted([race['agent_a_id'], race['agent_b_id']]))
            if key not in matchup_counts:
                matchup_counts[key] = {
                    'agent_a_id': race['agent_a_id'],
                    'agent_b_id': race['agent_b_id'],
                    'count': 0,
                    'races': []
                }
            matchup_counts[key]['count'] += 1
            matchup_counts[key]['races'].append(race['id'])
        
        # Sort by popularity
        sorted_matchups = sorted(matchup_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        if not sorted_matchups:
            st.info("💡 No matchup data yet. Create races to see popular agent pairings!")
            return
        
        # Get agent names
        agents = db_ops.get_all_agents()
        agent_map = {agent['id']: agent['display_name'] for agent in agents}
        
        # Display top matchups
        for _, matchup_data in sorted_matchups:
            agent_a_name = agent_map.get(matchup_data['agent_a_id'], 'Unknown')
            agent_b_name = agent_map.get(matchup_data['agent_b_id'], 'Unknown')
            count = matchup_data['count']
            
            with st.expander(f"**{agent_a_name} vs {agent_b_name}** - {count} races"):
                st.write(f"This matchup has been run {count} times")
                st.write("Check the leaderboard to see overall win rates!")
                
    except Exception as e:
        st.error(f"Error loading matchups: {str(e)}")
        st.info("💡 Create some races to see matchup statistics!")


def render_trends():
    """Render performance trends and statistics."""
    st.markdown("### 📈 Performance Statistics")
    
    # Get real data from database
    try:
        from database.operations import get_db
        db_ops = get_db()
        
        # Get recent races
        races = db_ops.get_recent_races(limit=100)
        total_races = db_ops.get_race_count()
        
        # Get leaderboard
        leaderboard = db_ops.get_leaderboard()
        
        # Calculate stats
        if races:
            completed_races = [r for r in races if r.get('status') == 'completed']
            completion_rate = (len(completed_races) / len(races) * 100) if races else 0
            
            # Calculate average duration
            durations = [r.get('duration_seconds', 0) for r in completed_races if r.get('duration_seconds')]
            avg_duration = sum(durations) / len(durations) if durations else 0
        else:
            completion_rate = 0
            avg_duration = 0
        
        # Display summary statistics
        st.markdown("### 📊 Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Races", f"{total_races}")
        
        with col2:
            st.metric("Avg Duration", f"{avg_duration:.1f}s" if avg_duration > 0 else "N/A")
        
        with col3:
            st.metric("Completion Rate", f"{completion_rate:.1f}%" if total_races > 0 else "N/A")
        
        with col4:
            active_agents = sum(1 for entry in leaderboard if entry.get('total_races', 0) > 0)
            st.metric("Active Agents", f"{active_agents}/4")
        
        # Show agent activity if we have data
        if total_races > 0:
            st.markdown("### 🎯 Agent Activity")
            
            # Create activity chart
            agent_data = []
            agents = db_ops.get_all_agents()
            agent_map = {agent['id']: agent['display_name'] for agent in agents}
            
            for entry in leaderboard:
                agents_info = entry.get('agents', {})
                if isinstance(agents_info, dict):
                    agent_name = agents_info.get('display_name', 'Unknown')
                else:
                    agent_id = entry.get('agent_id')
                    agent_name = agent_map.get(agent_id, 'Unknown')
                
                agent_data.append({
                    'Agent': agent_name,
                    'Races': entry.get('total_races', 0)
                })
            
            df = pd.DataFrame(agent_data)
            
            if len(df) > 0 and df['Races'].sum() > 0:
                fig = px.bar(
                    df,
                    x='Agent',
                    y='Races',
                    title='Total Races by Agent',
                    color='Races',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 No race activity yet. Start racing to see agent activity!")
        else:
            st.info("💡 No race data yet. Create races to see performance trends!")
            
    except Exception as e:
        st.error(f"Error loading trends: {str(e)}")
        st.info("💡 Create some races to see performance statistics!")
