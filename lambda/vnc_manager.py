"""
VNC Manager - Manages VNC server lifecycle in AWS Lambda.

This module handles:
- Starting/stopping Xvfb (virtual display)
- Starting/stopping x11vnc (VNC server)
- Starting/stopping websockify (WebSocket bridge)
- Managing VNC session lifecycle
"""

import subprocess
import os
import signal
import time
from typing import Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VNCManager:
    """Manages VNC server lifecycle in Lambda."""
    
    def __init__(self, display: str = ":99", port: int = 5900, novnc_port: int = 6080):
        """
        Initialize VNC Manager.
        
        Args:
            display: X display number (e.g., ":99")
            port: VNC server port (default: 5900)
            novnc_port: noVNC/websockify port (default: 6080)
        """
        self.display = display
        self.port = port
        self.novnc_port = novnc_port
        self.xvfb_process = None
        self.vnc_process = None
        self.websockify_process = None
        self._started = False
    
    def start(self) -> bool:
        """
        Start Xvfb, VNC server, and websockify.
        
        Returns:
            True if all services started successfully, False otherwise
        """
        if self._started:
            logger.info("VNC services already running")
            return True
        
        try:
            # Start Xvnc (TigerVNC) - acts as both virtual X server AND VNC server
            logger.info(f"Starting TigerVNC (Xvnc) on display {self.display}, port {self.port}")
            self.vnc_process = subprocess.Popen([
                'Xvnc', self.display,
                '-rfbport', str(self.port),
                '-SecurityTypes', 'None',  # No password (Lambda is already secured)
                '-AlwaysShared',  # Allow multiple clients
                '-desktop', 'WebAgentArena',
                '-geometry', '1920x1080',
                '-depth', '24',
                '-ac'  # Disable access control
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for Xvnc to initialize
            time.sleep(2)
            
            # Check if Xvnc started successfully (process should still be running)
            if self.vnc_process.poll() is not None:
                # Process died - this is a real failure
                stderr_output = self.vnc_process.stderr.read().decode('utf-8', errors='ignore')
                logger.error(f"Xvnc process died during startup: {stderr_output}")
                self.stop()
                return False
            
            # Xvnc is running (may have warnings in stderr, but that's OK)
            logger.info("Xvnc process is running successfully")
            
            # Set DISPLAY environment variable
            os.environ['DISPLAY'] = self.display
            logger.info(f"Set DISPLAY={self.display}")
            
            # Start websockify for web access (run as Python module)
            logger.info(f"Starting websockify on port {self.novnc_port}")
            self.websockify_process = subprocess.Popen([
                'python3', '-m', 'websockify',
                '--web', '/opt/noVNC',
                str(self.novnc_port),
                f'localhost:{self.port}'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for websockify to initialize
            time.sleep(1)
            
            # Check if websockify started successfully (process should still be running)
            if self.websockify_process.poll() is not None:
                # Process died - this is a real failure
                stderr_output = self.websockify_process.stderr.read().decode('utf-8', errors='ignore')
                logger.error(f"websockify process died during startup: {stderr_output}")
                self.stop()
                return False
            
            # websockify is running
            logger.info("websockify process is running successfully")
            
            self._started = True
            logger.info("✅ All VNC services started successfully (TigerVNC + websockify)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start VNC: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop all VNC-related processes."""
        logger.info("Stopping VNC services")
        
        for process_name, process in [
            ('websockify', self.websockify_process),
            ('Xvnc', self.vnc_process)
        ]:
            if process:
                try:
                    logger.info(f"Stopping {process_name}")
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"{process_name} didn't stop gracefully, killing")
                    process.kill()
                except Exception as e:
                    logger.error(f"Error stopping {process_name}: {e}")
        
        self._started = False
        logger.info("✅ All VNC services stopped")
    
    def get_websocket_url(self, base_url: str) -> str:
        """
        Return WebSocket URL for noVNC client.
        
        Args:
            base_url: Base Lambda function URL
        
        Returns:
            Full WebSocket URL for VNC connection
        """
        # Convert https:// to wss:// for WebSocket
        if base_url.startswith('https://'):
            ws_url = base_url.replace('https://', 'wss://')
        elif base_url.startswith('http://'):
            ws_url = base_url.replace('http://', 'ws://')
        else:
            ws_url = f"wss://{base_url}"
        
        # Add websockify endpoint
        return f"{ws_url}/websockify"
    
    def is_running(self) -> bool:
        """Check if VNC services are running."""
        if not self._started:
            return False
        
        # Check if all processes are still running
        for process in [self.vnc_process, self.websockify_process]:
            if process and process.poll() is not None:
                logger.warning("One or more VNC processes died")
                self._started = False
                return False
        
        return True
    
    def __del__(self):
        """Cleanup on object destruction."""
        if self._started:
            self.stop()


# Global VNC manager instance (persists across Lambda invocations)
_global_vnc_manager: Optional[VNCManager] = None


def get_vnc_manager() -> VNCManager:
    """
    Get or create global VNC manager instance.
    
    Returns:
        VNCManager instance
    """
    global _global_vnc_manager
    
    if _global_vnc_manager is None:
        _global_vnc_manager = VNCManager()
    
    return _global_vnc_manager


def ensure_vnc_running() -> bool:
    """
    Ensure VNC services are running.
    
    Returns:
        True if VNC is running, False if failed to start
    """
    manager = get_vnc_manager()
    
    if manager.is_running():
        return True
    
    return manager.start()


if __name__ == "__main__":
    # Test VNC manager locally
    print("Testing VNC Manager...")
    print("=" * 60)
    
    manager = VNCManager()
    
    print("\n1. Starting VNC services...")
    if manager.start():
        print("✅ VNC services started successfully")
        print(f"   Display: {manager.display}")
        print(f"   VNC Port: {manager.port}")
        print(f"   noVNC Port: {manager.novnc_port}")
        print(f"\n🌐 Access noVNC at: http://localhost:{manager.novnc_port}/vnc.html")
        print("   Press Ctrl+C to stop...")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n2. Stopping VNC services...")
            manager.stop()
            print("✅ VNC services stopped")
    else:
        print("❌ Failed to start VNC services")

