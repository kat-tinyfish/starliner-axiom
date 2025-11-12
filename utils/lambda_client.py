"""
AWS Lambda Client - Handles communication with Lambda functions.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
import streamlit as st


class LambdaClient:
    """
    Client for invoking AWS Lambda functions.
    
    Handles:
    - Function invocation
    - Response parsing
    - Error handling
    """
    
    def __init__(self):
        """Initialize Lambda client with credentials from environment."""
        try:
            self.function_url = st.secrets["aws"]["lambda_function_url"]
            self.region = st.secrets["aws"]["region"]
        except (KeyError, FileNotFoundError):
            self.function_url = os.getenv("AWS_LAMBDA_FUNCTION_URL")
            self.region = os.getenv("AWS_REGION", "us-east-1")
        
        if not self.function_url:
            raise ValueError(
                "AWS Lambda function URL not found. "
                "Please set AWS_LAMBDA_FUNCTION_URL in .env or secrets.toml"
            )
    
    def invoke_agent_execution(
        self,
        agent_config: Dict[str, Any],
        prompt: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke Lambda function to execute an agent task.
        
        Args:
            agent_config: Agent configuration
            prompt: Task prompt
            constraints: Optional task constraints
        
        Returns:
            Response from Lambda function
        
        Raises:
            Exception: If invocation fails
        """
        payload = {
            "agent_config": agent_config,
            "prompt": prompt,
            "constraints": constraints or {}
        }
        
        try:
            response = requests.post(
                self.function_url,
                json=payload,
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lambda invocation failed: {str(e)}")
    
    def get_vnc_url(self, session_id: str) -> Optional[str]:
        """
        Get VNC URL for a browser session.
        
        Args:
            session_id: Browser session ID
        
        Returns:
            VNC URL or None if not available
        
        TODO: Implement actual VNC URL retrieval
        """
        # Placeholder
        return f"http://localhost:6080/vnc.html?session={session_id}"
    
    def stop_execution(self, session_id: str) -> bool:
        """
        Stop an ongoing execution.
        
        Args:
            session_id: Browser session ID
        
        Returns:
            True if successful, False otherwise
        
        TODO: Implement execution termination
        """
        # Placeholder
        return True

