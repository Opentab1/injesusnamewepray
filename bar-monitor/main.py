#!/usr/bin/env python3
"""
Bar Monitoring System - Main Application

This is the main entry point that integrates all components:
- Hailo HAT people detection
- Entry/exit counting
- Occupancy tracking
- Data storage

Run with: python3 main.py
"""

import sys
import logging
import signal
import time
import yaml
from pathlib import Path
from datetime import datetime

# Add hailo_integration to path
sys.path.insert(0, str(Path(__file__).parent))

from hailo_integration.hailo_runner import HailoRunner
from hailo_integration.counting_logic import EntryExitCounter
from hailo_integration.occupancy_tracker import OccupancyTracker


class BarMonitorSystem:
    """
    Main system orchestrator.
    
    This ties together all components and manages the main loop.
    """
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """
        Initialize the monitoring system.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("Bar Monitoring System Starting")
        self.logger.info("=" * 60)
        
        # Initialize components
        self.hailo_runner = None
        self.counter = None
        self.tracker = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            print(f"Error: Configuration file not found: {config_path}")
            sys.exit(1)
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_dir = Path(log_config.get('log_dir', 'logs'))
        log_file = log_config.get('log_file', 'bar-monitor.log')
        
        # Create log directory
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {sig}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if successful
        """
        self.logger.info("Initializing components...")
        
        try:
            # 1. Initialize Hailo Runner
            self.logger.info("1. Initializing Hailo HAT...")
            self.hailo_runner = HailoRunner()
            
            if not self.hailo_runner.check_installation():
                self.logger.error("Hailo installation check failed!")
                return False
            
            hailo_info = self.hailo_runner.get_hailo_info()
            self.logger.info(f"Hailo Device: {hailo_info.get('output', 'Unknown')}")
            
            # 2. Initialize Entry/Exit Counter
            self.logger.info("2. Initializing Entry/Exit Counter...")
            counting_config = self.config.get('counting', {})
            self.counter = EntryExitCounter(
                counting_line_y=counting_config.get('counting_line_y', 240),
                frame_height=self.config['camera'].get('height', 480),
                entry_direction=counting_config.get('entry_direction', 'down')
            )
            
            # 3. Initialize Occupancy Tracker
            self.logger.info("3. Initializing Occupancy Tracker...")
            occupancy_config = self.config.get('occupancy', {})
            self.tracker = OccupancyTracker(
                db_path=occupancy_config.get('db_path', 'data/occupancy.db'),
                snapshot_interval=occupancy_config.get('snapshot_interval', 60)
            )
            
            self.logger.info("✓ All components initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            return False
    
    def start(self):
        """Start the monitoring system."""
        if not self.initialize():
            self.logger.error("Failed to initialize system. Exiting.")
            sys.exit(1)
        
        self.logger.info("=" * 60)
        self.logger.info("System started successfully!")
        self.logger.info("=" * 60)
        self.logger.info("")
        self.logger.info("Monitoring Status:")
        self.logger.info(f"  Camera: {self.config['camera']['source']}")
        self.logger.info(f"  Model: {self.config['detection']['model']}")
        self.logger.info(f"  Counting Line: Y={self.config['counting']['counting_line_y']}px")
        self.logger.info(f"  Database: {self.config['occupancy']['db_path']}")
        self.logger.info("")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info("=" * 60)
        
        self.running = True
        
        # Start Hailo detection
        camera_source = self.config['camera']['source']
        self.hailo_runner.start(camera_source=camera_source)
        
        # Main monitoring loop
        self._main_loop()
    
    def _main_loop(self):
        """
        Main monitoring loop.
        
        This runs continuously and:
        1. Gets detections from Hailo
        2. Updates counting logic
        3. Updates occupancy tracker
        4. Logs statistics
        """
        last_stats_time = time.time()
        stats_interval = 10  # Log stats every 10 seconds
        
        self.logger.info("Entering main monitoring loop...")
        
        while self.running:
            try:
                # In a full implementation, we would:
                # 1. Get detections from Hailo pipeline
                # 2. Extract person centroids
                # 3. Update counter
                # 4. Update tracker
                
                # For now, we'll show the structure
                # (Real implementation needs Hailo pipeline integration)
                
                # Simulated detection data for demonstration
                # detections = self.hailo_runner.get_detections()
                # centroids = [(d.center) for d in detections]
                # entries, exits = self.counter.update(centroids)
                # stats = self.counter.get_stats()
                # self.tracker.update(stats)
                
                # Log statistics periodically
                if time.time() - last_stats_time >= stats_interval:
                    stats = self.tracker.get_statistics()
                    
                    self.logger.info("─" * 60)
                    self.logger.info(f"Current Status [{datetime.now().strftime('%H:%M:%S')}]")
                    self.logger.info(f"  Occupancy: {stats['current_occupancy']} people")
                    self.logger.info(f"  Total Entries: {stats['total_entries']}")
                    self.logger.info(f"  Total Exits: {stats['total_exits']}")
                    self.logger.info(f"  Active Tracks: {stats['active_tracks']}")
                    
                    # Peak occupancy
                    peak, peak_time = self.tracker.get_peak_occupancy(hours=24)
                    self.logger.info(f"  Peak Today: {peak} people")
                    
                    self.logger.info("─" * 60)
                    
                    last_stats_time = time.time()
                
                # Sleep briefly to avoid CPU overload
                time.sleep(0.1)
            
            except KeyboardInterrupt:
                raise  # Let signal handler deal with it
            
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(1)
    
    def stop(self):
        """Stop the monitoring system."""
        if not self.running:
            return
        
        self.logger.info("Stopping system...")
        self.running = False
        
        # Stop components in reverse order
        if self.hailo_runner:
            self.logger.info("Stopping Hailo runner...")
            self.hailo_runner.stop()
        
        if self.tracker:
            self.logger.info("Stopping occupancy tracker...")
            self.tracker.stop()
        
        self.logger.info("System stopped successfully")


def main():
    """Main entry point."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║            BAR MONITORING SYSTEM v1.0                     ║
║                                                           ║
║  Features:                                                ║
║    • Real-time people detection (Hailo AI HAT)            ║
║    • Entry/Exit counting                                  ║
║    • Occupancy tracking                                   ║
║    • Historical data storage                              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi 5' not in model:
                print("⚠ Warning: Not running on Raspberry Pi 5")
    except FileNotFoundError:
        print("⚠ Warning: Could not detect Raspberry Pi hardware")
    
    # Create and start system
    system = BarMonitorSystem()
    
    try:
        system.start()
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
        system.stop()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
