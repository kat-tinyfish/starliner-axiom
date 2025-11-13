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
            # Start Xvfb (Virtual X server)
            logger.info(f"Starting Xvfb on display {self.display}")
            self.xvfb_process = subprocess.Popen([
                'Xvfb', self.display,
                '-screen', '0', '1920x1080x24',
                '-ac',  # Disable access control
                '-nolisten', 'tcp'  # Don't listen on TCP
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for Xvfb to initialize
            time.sleep(1)
            
            # Check if Xvfb started successfully
            if self.xvfb_process.poll() is not None:
                logger.error(f"Xvfb failed to start: {self.xvfb_process.stderr.read()}")
                return False
            
            # Set DISPLAY environment variable
            os.environ['DISPLAY'] = self.display
            logger.info(f"Set DISPLAY={self.display}")
            
            # Start fluxbox window manager (lightweight)
            logger.info("Starting fluxbox window manager")
            subprocess.Popen([
                'fluxbox', '-display', self.display
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.5)
            
            # Start x11vnc
            logger.info(f"Starting x11vnc on port {self.port}")
            self.vnc_process = subprocess.Popen([
                'x11vnc',
                '-display', self.display,
                '-rfbport', str(self.port),
                '-forever',  # Keep running after client disconnects
                '-shared',   # Allow multiple clients
                '-nopw',     # No password (Lambda is already secured)
                '-quiet',    # Reduce log verbosity
                '-noxdamage' # Disable XDamage (can cause issues in Xvfb)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for VNC server to initialize
            time.sleep(1)
            
            # Check if x11vnc started successfully
            if self.vnc_process.poll() is not None:
                logger.error(f"x11vnc failed to start: {self.vnc_process.stderr.read()}")
                self.stop()
                return False
            
            # Start websockify for web access
            logger.info(f"Starting websockify on port {self.novnc_port}")
            self.websockify_process = subprocess.Popen([
                'websockify',
                '--web', '/opt/noVNC',
                str(self.novnc_port),
                f'localhost:{self.port}'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for websockify to initialize
            time.sleep(1)
            
            # Check if websockify started successfully
            if self.websockify_process.poll() is not None:
                logger.error(f"websockify failed to start: {self.websockify_process.stderr.read()}")
                self.stop()
                return False
            
            self._started = True
            logger.info("✅ All VNC services started successfully")
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
            ('x11vnc', self.vnc_process),
            ('Xvfb', self.xvfb_process)
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
        for process in [self.xvfb_process, self.vnc_process, self.websockify_process]:
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

