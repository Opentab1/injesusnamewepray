"""
Hailo Runner - Integration with Official hailo-rpi5-examples

This module provides a clean interface to run the official Hailo examples
and extract detection results for our people counting system.

IMPORTANT: This requires hailo-rpi5-examples to be installed:
    cd ~
    git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
    cd hailo-rpi5-examples
    ./install.sh
    source setup_env.sh

APPROACH:
Instead of reimplementing the Hailo pipeline, we use their official code
and extract the detection results for our counting logic.
"""

import subprocess
import sys
import os
import logging
import threading
import queue
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class HailoRunner:
    """
    Runner for Hailo official detection pipeline.
    
    This class manages the Hailo detection process and provides
    detection results to our counting system.
    
    ARCHITECTURE:
    ┌─────────────────┐
    │  Camera Input   │
    └────────┬────────┘
             │
    ┌────────▼──────────┐
    │  Hailo Pipeline   │  ← Official hailo-rpi5-examples
    │  (detection.py)   │
    └────────┬──────────┘
             │
    ┌────────▼──────────┐
    │  HailoRunner      │  ← This class
    │  (Extract results)│
    └────────┬──────────┘
             │
    ┌────────▼──────────┐
    │  Counting Logic   │  ← Our tracking/counting code
    └───────────────────┘
    """
    
    def __init__(self, hailo_examples_path: str = None):
        """
        Initialize Hailo runner.
        
        Args:
            hailo_examples_path: Path to hailo-rpi5-examples directory
                               If None, looks in standard locations
        """
        # Find hailo-rpi5-examples
        if hailo_examples_path is None:
            hailo_examples_path = self._find_hailo_examples()
        
        self.hailo_path = Path(hailo_examples_path)
        
        if not self.hailo_path.exists():
            raise FileNotFoundError(
                f"Hailo examples not found at {self.hailo_path}\n"
                "Please install: git clone https://github.com/hailo-ai/hailo-rpi5-examples.git"
            )
        
        self.running = False
        self.detection_queue = queue.Queue(maxsize=100)
        
        logger.info(f"HailoRunner initialized with path: {self.hailo_path}")
    
    def _find_hailo_examples(self) -> str:
        """
        Try to find hailo-rpi5-examples in standard locations.
        
        Checks:
        1. ~/hailo-rpi5-examples
        2. /home/ubuntu/hailo-rpi5-examples
        3. Current directory
        """
        possible_paths = [
            Path.home() / "hailo-rpi5-examples",
            Path("/home/ubuntu/hailo-rpi5-examples"),
            Path.cwd() / "hailo-rpi5-examples",
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found hailo-rpi5-examples at: {path}")
                return str(path)
        
        # Default to home directory (will fail if not there)
        return str(Path.home() / "hailo-rpi5-examples")
    
    def check_installation(self) -> bool:
        """
        Check if Hailo software is properly installed.
        
        Returns:
            True if installation is valid
        """
        # Check if hailo-rpi5-examples exists
        if not self.hailo_path.exists():
            logger.error(f"hailo-rpi5-examples not found at {self.hailo_path}")
            return False
        
        # Check if detection.py exists
        detection_script = self.hailo_path / "basic_pipelines" / "detection.py"
        if not detection_script.exists():
            logger.error(f"detection.py not found at {detection_script}")
            return False
        
        # Check if Hailo device is accessible
        try:
            result = subprocess.run(
                ['hailortcli', 'fw-control', 'identify'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("Hailo device detected successfully")
                return True
            else:
                logger.error("Hailo device not detected")
                return False
        
        except FileNotFoundError:
            logger.error("hailortcli not found - Hailo software not installed")
            logger.error("Install with: sudo apt install hailo-all")
            return False
        
        except subprocess.TimeoutExpired:
            logger.error("Hailo device check timed out")
            return False
    
    def get_hailo_info(self) -> Dict:
        """
        Get information about Hailo device.
        
        Returns:
            Dictionary with device info
        """
        try:
            result = subprocess.run(
                ['hailortcli', 'fw-control', 'identify'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            info = {
                'installed': result.returncode == 0,
                'output': result.stdout if result.returncode == 0 else result.stderr
            }
            
            return info
        
        except Exception as e:
            return {
                'installed': False,
                'error': str(e)
            }
    
    def run_detection(self, camera_source: str = 'rpi', 
                     model: str = 'yolov6n') -> subprocess.Popen:
        """
        Start Hailo detection process.
        
        Args:
            camera_source: 'rpi', 'usb', or '/dev/videoX'
            model: Model name (yolov6n, yolov8s, etc.)
            
        Returns:
            Subprocess handle
        """
        detection_script = self.hailo_path / "basic_pipelines" / "detection.py"
        
        # Build command
        cmd = [
            'python3',
            str(detection_script),
            '--input', camera_source,
        ]
        
        # Set environment
        env = os.environ.copy()
        env['DISPLAY'] = ':0'  # For video output
        
        # Source setup_env.sh by running in bash
        setup_script = self.hailo_path / "setup_env.sh"
        if setup_script.exists():
            cmd = [
                'bash', '-c',
                f'source {setup_script} && ' + ' '.join(cmd)
            ]
        
        logger.info(f"Starting Hailo detection: {' '.join(cmd)}")
        
        # Start process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=str(self.hailo_path)
        )
        
        return process
    
    def start(self, camera_source: str = 'rpi'):
        """
        Start detection in background.
        
        Args:
            camera_source: Camera source string
        """
        if self.running:
            logger.warning("HailoRunner already running")
            return
        
        self.running = True
        self.process = self.run_detection(camera_source)
        
        # Monitor process in background thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_process,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("HailoRunner started")
    
    def _monitor_process(self):
        """Monitor the Hailo process and capture output."""
        while self.running:
            if self.process.poll() is not None:
                # Process ended
                logger.warning("Hailo process ended unexpectedly")
                self.running = False
                break
            
            time.sleep(0.1)
    
    def stop(self):
        """Stop the detection process."""
        if not self.running:
            return
        
        self.running = False
        
        if hasattr(self, 'process'):
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        logger.info("HailoRunner stopped")


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Hailo Runner Test")
    print("=" * 60)
    
    runner = HailoRunner()
    
    print("\nChecking Hailo installation...")
    if runner.check_installation():
        print("✓ Hailo installation OK")
        
        print("\nHailo Device Info:")
        info = runner.get_hailo_info()
        print(info['output'])
        
        print("\nTo run detection manually:")
        print("cd ~/hailo-rpi5-examples")
        print("source setup_env.sh")
        print("python basic_pipelines/detection.py --input rpi")
    else:
        print("✗ Hailo installation check failed")
        print("\nInstallation steps:")
        print("1. sudo apt update")
        print("2. sudo apt install hailo-all")
        print("3. cd ~ && git clone https://github.com/hailo-ai/hailo-rpi5-examples.git")
        print("4. cd hailo-rpi5-examples && ./install.sh")
