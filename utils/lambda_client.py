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
            agent_config: Agent configuration (must include agent_id, model, name)
            prompt: Task prompt
            constraints: Optional task constraints (domains, schema)
        
        Returns:
            Response from Lambda function with format:
            {
                "status": "success" | "error",
                "result": {...} | "error": "..."
            }
        
        Raises:
            Exception: If invocation fails
        """
        # Lambda handler expects this structure
        payload = {
            "body": {
                "action": "execute",
                "agent_config": agent_config,
                "prompt": prompt,
                "constraints": constraints or {}
            }
        }
        
        try:
            response = requests.post(
                self.function_url,
                json=payload,
                timeout=300,  # 5 minute timeout
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Parse the response body if it's a string (Lambda function URL format)
            if isinstance(result.get('body'), str):
                result['body'] = json.loads(result['body'])
            
            # Return the body content
            return result.get('body', result)
            
        except requests.exceptions.Timeout:
            raise Exception("Lambda execution timed out (>5 minutes)")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lambda invocation failed: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if Lambda function is healthy and ready.
        
        Returns:
            Health check response with status and playwright availability
        """
        payload = {
            "body": {
                "action": "health_check"
            }
        }
        
        try:
            response = requests.post(
                self.function_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Parse the response body if it's a string
            if isinstance(result.get('body'), str):
                result['body'] = json.loads(result['body'])
            
            return result.get('body', result)
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Health check failed: {str(e)}"
            }
    
    def get_vnc_url(self, session_id: str) -> Optional[str]:
        """
        Get VNC URL for a browser session.
        
        Args:
            session_id: Browser session ID
        
        Returns:
            VNC URL or None if not available
        
        Note: For now, returns a placeholder. In production, this would:
        - Return a real VNC WebSocket URL from Lambda
        - Or return screenshot polling URL
        - Or return browserbase.com viewer URL
        """
        # Placeholder - will be replaced with actual Lambda VNC streaming
        return f"https://placeholder-vnc.example.com?session={session_id}"
    
    def stop_execution(self, session_id: str) -> bool:
        """
        Stop an ongoing execution.
        
        Args:
            session_id: Browser session ID
        
        Returns:
            True if successful, False otherwise
        
        TODO: Implement execution termination endpoint in Lambda
        """
        # Placeholder - would call Lambda stop endpoint
        return True

