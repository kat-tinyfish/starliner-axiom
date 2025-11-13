"""
Arena Component - Main arena interface for agent battles.
"""

import streamlit as st
from typing import Optional, Tuple
import asyncio
import time
import base64
from io import BytesIO
from PIL import Image


def render_arena():
    """
    Render the main arena interface with full functionality.
    """
    # Initialize session state
    if "race_active" not in st.session_state:
        st.session_state.race_active = False
    if "race_orchestrator" not in st.session_state:
        st.session_state.race_orchestrator = None
    if "race_results" not in st.session_state:
        st.session_state.race_results = None
    if "race_db_id" not in st.session_state:
        st.session_state.race_db_id = None
    
    st.markdown("Watch two AI agents compete in real-time web navigation tasks")
    
    # Task input
    prompt, domains, json_schema = render_task_input()
    
    # Agent selection
    agent_a, agent_b = render_agent_selection()
    
    # Control buttons
    race_started = render_control_buttons(prompt, agent_a, agent_b, domains, json_schema)
    
    # Display race if active
    if st.session_state.race_active or st.session_state.race_results:
        render_race_view()
    else:
        st.info("👆 Configure your race above and click **Start Race** to begin!")
    
    # Show previous results if available
    if st.session_state.race_results:
        render_results_and_voting()


def render_task_input() -> Tuple[str, Optional[str], Optional[str]]:
    """
    Render task input section.
    
    Returns:
        Tuple of (prompt, domains, json_schema)
    """
    with st.expander("📝 Task Input", expanded=True):
        prompt = st.text_area(
            "Enter your task in natural language:",
            placeholder="Example: Go to Amazon and find the top 3 bestselling science fiction books",
            height=100,
            key="task_input"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            domains = st.text_input(
                "Domain hints (optional):",
                placeholder="amazon.com, example.com"
            )
        with col2:
            json_schema = st.text_input(
                "JSON output schema (optional):",
                placeholder='{"title": "string", "price": "number"}'
            )
    
    return prompt, domains, json_schema


def render_agent_selection() -> Tuple[str, str]:
    """
    Render agent selection dropdowns.
    
    Returns:
        Tuple of (agent_a_name, agent_b_name)
    """
    from agents.agent_registry import AgentRegistry
    
    agent_list = AgentRegistry.get_agent_list()
    
    st.markdown("### 🤖 Select Agents")
    col1, col2 = st.columns(2)
    
    with col1:
        agent_a = st.selectbox(
            "Agent A:",
            agent_list,
            key="agent_a_select"
        )
    
    with col2:
        # Default to second agent for Agent B
        default_b = agent_list[1] if len(agent_list) > 1 else agent_list[0]
        agent_b = st.selectbox(
            "Agent B:",
            agent_list,
            index=agent_list.index(default_b),
            key="agent_b_select"
        )
    
    return agent_a, agent_b


def render_control_buttons(prompt: str, agent_a: str, agent_b: str, 
                           domains: Optional[str], json_schema: Optional[str]) -> bool:
    """
    Render control buttons for the race.
    
    Returns:
        True if race was started, False otherwise
    """
    st.markdown("### 🎬 Controls")
    
    # Validate inputs
    can_start = bool(prompt and agent_a and agent_b)
    
    col1, col2, col3, col4 = st.columns(4)
    
    race_started = False
    
    with col1:
        if st.button("▶️ Start Race", width="stretch", type="primary", disabled=not can_start):
            if can_start:
                # Initialize race orchestrator
                from utils.race_orchestrator import RaceOrchestrator
                orchestrator = RaceOrchestrator()
                
                # Parse constraints
                constraints = {}
                if domains:
                    constraints["domains"] = [d.strip() for d in domains.split(",")]
                if json_schema:
                    import json
                    try:
                        constraints["schema"] = json.loads(json_schema)
                    except:
                        st.error("Invalid JSON schema")
                        return False
                
                # Initialize race
                try:
                    race_id = orchestrator.initialize_race(agent_a, agent_b, prompt, constraints)
                    st.session_state.race_orchestrator = orchestrator
                    st.session_state.race_active = True
                    st.session_state.race_start_time = time.time()
                    st.session_state.race_results = None
                    race_started = True
                    
                    # Save race to database
                    try:
                        from database.operations import get_db
                        db = get_db()
                        
                        # Get agent IDs from database
                        agent_a_data = db.get_agent_by_display_name(agent_a)
                        agent_b_data = db.get_agent_by_display_name(agent_b)
                        
                        if agent_a_data and agent_b_data:
                            db_race_id = db.create_race(
                                prompt=prompt,
                                agent_a_id=agent_a_data['id'],
                                agent_b_id=agent_b_data['id'],
                                domains=constraints.get("domains"),
                                schema=constraints.get("schema")
                            )
                            st.session_state.race_db_id = db_race_id
                            st.success(f"Race saved to database!")
                        else:
                            st.warning("Could not save race to database")
                    except Exception as db_error:
                        st.warning(f"Database save failed: {str(db_error)}")
                    
                    st.success(f"Race initialized! ID: {race_id[:8]}")
                except Exception as e:
                    st.error(f"Failed to start race: {str(e)}")
                    return False
    
    with col2:
        if st.button("⏹️ Stop", width="stretch", disabled=not st.session_state.race_active):
            if st.session_state.race_orchestrator:
                st.session_state.race_orchestrator.stop_race()
            st.session_state.race_active = False
            st.info("Race stopped")
    
    with col3:
        if st.button("🔄 Reset", width="stretch"):
            st.session_state.race_active = False
            st.session_state.race_orchestrator = None
            st.session_state.race_results = None
            st.session_state.race_start_time = None
            st.rerun()
    
    with col4:
        # Display timer
        if st.session_state.race_active and hasattr(st.session_state, 'race_start_time'):
            elapsed = time.time() - st.session_state.race_start_time
            st.metric("⏱️ Timer", f"{elapsed:.1f}s")
        else:
            st.metric("⏱️ Timer", "0.0s")
    
    return race_started


def render_race_view():
    """
    Render the live race view with agent browsers and tool calls.
    """
    if not st.session_state.race_orchestrator:
        return
    
    orchestrator = st.session_state.race_orchestrator
    
    st.markdown("---")
    st.markdown("## 🏁 Race in Progress")
    
    # Start the race if it hasn't been started yet
    if st.session_state.race_active and not hasattr(st.session_state, 'race_executing'):
        st.session_state.race_executing = True
        
        # Show a spinner while executing
        with st.spinner("🏁 Race executing... This may take 10-30 seconds"):
            # Run the race asynchronously with timeout
            try:
                async def run_with_timeout():
                    return await asyncio.wait_for(
                        orchestrator.start_race(),
                        timeout=60.0  # 60 second timeout
                    )
                
                result_a, result_b, duration = asyncio.run(run_with_timeout())
                
                # Store results
                st.session_state.race_results = (result_a, result_b, duration)
                st.session_state.race_active = False
                st.session_state.race_executing = False
                
                st.success(f"✅ Race completed in {duration:.1f}s!")
                
                # Save executions to database
                if st.session_state.race_db_id:
                    try:
                        from database.operations import get_db
                        db_ops = get_db()
                        
                        agent_a_data = db_ops.get_agent_by_display_name(orchestrator.agent_a.name)
                        agent_b_data = db_ops.get_agent_by_display_name(orchestrator.agent_b.name)
                        
                        if agent_a_data:
                            db_ops.save_agent_execution(
                                race_id=st.session_state.race_db_id,
                                agent_id=agent_a_data['id'],
                                checkpoints=[{"name": cp.name, "status": cp.status, "timestamp": cp.timestamp.isoformat()} for cp in result_a.checkpoints],
                                tool_calls=[{"tool": tc.tool_name, "status": tc.status, "timestamp": tc.timestamp.isoformat()} for tc in result_a.tool_calls],
                                output=result_a.output,
                                error_message=result_a.error_message,
                                execution_time=result_a.execution_time,
                                final_status="success" if result_a.success else "error"
                            )
                        
                        if agent_b_data:
                            db_ops.save_agent_execution(
                                race_id=st.session_state.race_db_id,
                                agent_id=agent_b_data['id'],
                                checkpoints=[{"name": cp.name, "status": cp.status, "timestamp": cp.timestamp.isoformat()} for cp in result_b.checkpoints],
                                tool_calls=[{"tool": tc.tool_name, "status": tc.status, "timestamp": tc.timestamp.isoformat()} for tc in result_b.tool_calls],
                                output=result_b.output,
                                error_message=result_b.error_message,
                                execution_time=result_b.execution_time,
                                final_status="success" if result_b.success else "error"
                            )
                        
                        db_ops.update_race_status(st.session_state.race_db_id, "completed", duration=duration)
                    except Exception as e:
                        st.warning(f"Failed to save race results to database: {str(e)}")
                
                st.rerun()
                
            except asyncio.TimeoutError:
                st.error("⏰ Race timed out after 60 seconds. This may indicate:")
                st.error("• BrowserBase session is slow or stuck")
                st.error("• Network connectivity issues")
                st.error("• Complex task taking too long")
                st.info("💡 Try: Click Reset and start a new race with a simpler task")
                st.session_state.race_active = False
                st.session_state.race_executing = False
                return
                
            except Exception as e:
                st.error(f"❌ Race execution failed: {str(e)}")
                st.error(f"Error type: {type(e).__name__}")
                with st.expander("🐛 Debug Info"):
                    import traceback
                    st.code(traceback.format_exc())
                st.session_state.race_active = False
                st.session_state.race_executing = False
                return
    
    # Get agent status
    status = orchestrator.get_agent_status()
    
    # Create two columns for agents
    col_a, col_b = st.columns(2)
    
    with col_a:
        render_agent_panel("Agent A", status["agent_a"], orchestrator.agent_a)
    
    with col_b:
        render_agent_panel("Agent B", status["agent_b"], orchestrator.agent_b)
    
    # Show voting interface immediately when race starts
    if st.session_state.race_active:
        st.markdown("---")
        render_voting_interface()
    
    # Auto-refresh while race is active
    if st.session_state.race_active:
        time.sleep(0.5)
        st.rerun()


def render_agent_panel(title: str, agent_status: dict, agent):
    """Render a panel for a single agent with Tool Calls (left) | Browser (right) layout."""
    st.markdown(f"### {title}: {agent_status['name']}")
    
    # Two-column layout: Tool Calls | Browser Session
    col_tools, col_browser = st.columns([1, 2])
    
    with col_tools:
        st.markdown("**🔧 Tool Calls**")
        st.markdown("---")
        
        tool_calls = agent_status["tool_calls"]
        if tool_calls:
            # Show last 10 tool calls
            for tc in tool_calls[-10:]:
                status_icon = {"success": "✅", "in_progress": "⏳", "error": "❌"}
                st.markdown(f"{status_icon.get(tc.status, '•')} `{tc.tool_name}`")
                # Show compact parameters
                if tc.parameters:
                    param_str = ", ".join([f"{k}: {v}" for k, v in list(tc.parameters.items())[:2]])
                    if len(param_str) > 30:
                        param_str = param_str[:30] + "..."
                    st.caption(param_str)
        else:
            st.info("Waiting for agent to start...")
    
    with col_browser:
        st.markdown("**🖥️ Browser Session**")
        st.markdown("---")
        
        # Display latest screenshot
        result = agent.result if agent and hasattr(agent, 'result') else None
        screenshots = result.screenshots if result and hasattr(result, 'screenshots') else []
        
        if screenshots:
            # Get latest screenshot
            latest_screenshot = screenshots[-1]
            
            try:
                screenshot_bytes = base64.b64decode(latest_screenshot['data'])
                screenshot_image = Image.open(BytesIO(screenshot_bytes))
                
                # Display screenshot
                st.image(screenshot_image, use_container_width=True)
                
                # Show metadata
                elapsed = latest_screenshot.get('elapsed', 0)
                index = latest_screenshot.get('index', 0)
                st.caption(f"Screenshot {index + 1} • {elapsed:.1f}s elapsed")
            except Exception as e:
                st.error(f"Failed to load screenshot: {str(e)}")
        else:
            # Placeholder for browser session
            st.info("📸 Browser screenshots will appear here when race starts")
            st.caption("Updates every 2 seconds")
        
        # Progress indicator below browser
        st.markdown("**Progress:**")
        if agent_status["current_checkpoint"]:
            cp = agent_status["current_checkpoint"]
            status_icon = {"completed": "✅", "in_progress": "⏳", "pending": "⏸️", "error": "❌"}
            st.info(f"{status_icon.get(cp.status, '•')} {cp.name}: {cp.description}")
        
        # Checkpoint progress bar
        checkpoints = agent_status["checkpoints"]
        if checkpoints:
            completed = sum(1 for cp in checkpoints if cp.status == "completed")
            progress = completed / len(checkpoints) if checkpoints else 0
            checkpoint_emojis = " → ".join([
                "✅" if cp.status == "completed" else
                "⏳" if cp.status == "in_progress" else
                "⏸️" if cp.status == "pending" else "❌"
                for cp in checkpoints[:4]  # Show first 4
            ])
            st.progress(progress, text=checkpoint_emojis)


def render_voting_interface():
    """
    Render the voting interface (shown during and after race).
    """
    if not st.session_state.race_orchestrator:
        return
    
    orchestrator = st.session_state.race_orchestrator
    
    st.markdown("### 🗳️ Which agent is performing better?")
    st.caption("You can vote anytime during or after the race")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("👈 Agent A", width="stretch", type="primary", key="vote_a"):
            # Save vote to database
            if st.session_state.get('race_db_id'):
                try:
                    from database.operations import get_db
                    db_ops = get_db()
                    
                    # Get agent A ID
                    if orchestrator.agent_a:
                        agent_data = db_ops.get_agent_by_display_name(orchestrator.agent_a.name)
                        if agent_data:
                            db_ops.save_user_preference(
                                race_id=st.session_state.race_db_id,
                                preferred_agent_id=agent_data['id'],
                                preference_type="agent_a"
                            )
                            
                            # Update race status if results are available
                            if st.session_state.race_results:
                                _, _, duration = st.session_state.race_results
                                db_ops.update_race_status(st.session_state.race_db_id, "completed", 
                                                    duration=duration if duration else None)
                            
                            st.success("✅ Vote recorded for Agent A!")
                            st.balloons()
                        else:
                            st.success("✅ Vote recorded for Agent A!")
                except Exception as e:
                    st.warning(f"Vote saved locally: {str(e)}")
            else:
                st.success("✅ Vote recorded for Agent A!")
    
    with col2:
        st.write("")  # Spacer
    
    with col3:
        if st.button("Agent B 👉", width="stretch", type="primary", key="vote_b"):
            # Save vote to database
            if st.session_state.get('race_db_id'):
                try:
                    from database.operations import get_db
                    db_ops = get_db()
                    
                    # Get agent B ID
                    if orchestrator.agent_b:
                        agent_data = db_ops.get_agent_by_display_name(orchestrator.agent_b.name)
                        if agent_data:
                            db_ops.save_user_preference(
                                race_id=st.session_state.race_db_id,
                                preferred_agent_id=agent_data['id'],
                                preference_type="agent_b"
                            )
                            
                            # Update race status if results are available
                            if st.session_state.race_results:
                                _, _, duration = st.session_state.race_results
                                db_ops.update_race_status(st.session_state.race_db_id, "completed", 
                                                    duration=duration if duration else None)
                            
                            st.success("✅ Vote recorded for Agent B!")
                            st.balloons()
                        else:
                            st.success("✅ Vote recorded for Agent B!")
                except Exception as e:
                    st.warning(f"Vote saved locally: {str(e)}")
            else:
                st.success("✅ Vote recorded for Agent B!")


def render_results_and_voting():
    """
    Render race results (outputs section after race completes).
    """
    if not st.session_state.race_results:
        return
    
    st.markdown("---")
    st.markdown("## 📊 Outputs")
    
    result_a, result_b, duration = st.session_state.race_results
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### Agent A Output")
        
        # Execution metrics
        col_time, col_status = st.columns(2)
        with col_time:
            st.metric("Time", f"{result_a.execution_time:.2f}s")
        with col_status:
            st.metric("Status", "✅" if result_a.success else "❌")
        
        # Output display
        if result_a.output:
            # Try to display as JSON first, fall back to text
            try:
                if isinstance(result_a.output, str):
                    st.code(result_a.output, language="text")
                else:
                    st.json(result_a.output)
            except:
                st.code(str(result_a.output), language="text")
        elif result_a.error_message:
            st.error(f"Error: {result_a.error_message}")
        else:
            st.code("No output", language=None)
    
    with col_b:
        st.markdown("### Agent B Output")
        
        # Execution metrics
        col_time, col_status = st.columns(2)
        with col_time:
            st.metric("Time", f"{result_b.execution_time:.2f}s")
        with col_status:
            st.metric("Status", "✅" if result_b.success else "❌")
        
        # Output display
        if result_b.output:
            # Try to display as JSON first, fall back to text
            try:
                if isinstance(result_b.output, str):
                    st.code(result_b.output, language="text")
                else:
                    st.json(result_b.output)
            except:
                st.code(str(result_b.output), language="text")
        elif result_b.error_message:
            st.error(f"Error: {result_b.error_message}")
        else:
            st.code("No output", language=None)
    
    # Voting is now shown during the race, but repeat it here for convenience
    st.markdown("---")
    render_voting_interface()

