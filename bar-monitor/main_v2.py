#!/usr/bin/env python3
"""
Bar Monitoring System - V2 (Using Supervision Library)

VERSION 2: Using stolen/proven libraries instead of custom code!
- Hailo official examples for detection
- Supervision library (18k stars) for line crossing + dwell tracking
- Streamlit (33k stars) for dashboard

Run with: python3 main_v2.py
"""

import sys
import logging
import signal
import time
import yaml
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Supervision library - 18k stars!
import supervision as sv

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from hailo_integration.occupancy_tracker import OccupancyTracker


class BarMonitorV2:
    """
    Bar Monitoring System V2 - Using Supervision Library
    
    WHAT WE'RE STEALING:
    - Line crossing detection (Supervision)
    - Dwell time tracking (Supervision zones)
    - Object tracking (ByteTrack via Supervision)
    - Beautiful visualizations (Supervision annotators)
    
    WHAT WE'RE KEEPING:
    - Hailo HAT detection (official examples)
    - Toast POS integration (no alternative exists)
    - SQLite storage (simple, works fine)
    """
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("=" * 60)
        self.logger.info("Bar Monitoring System V2 Starting")
        self.logger.info("Using: Supervision library + Hailo HAT")
        self.logger.info("=" * 60)
        
        # Components
        self.camera = None
        self.tracker = None  # ByteTrack from Supervision
        self.line_zone = None  # Line crossing from Supervision
        self.dwell_zones = {}  # Dwell time zones from Supervision
        self.occupancy_tracker = None  # Keep our custom tracker
        
        # Annotators for visualization
        self.box_annotator = None
        self.trace_annotator = None
        self.label_annotator = None
        
        # Stats
        self.entries = 0
        self.exits = 0
        self.running = False
        
        # Dwell time tracking
        self.active_customers = {}  # track_id -> {entry_time, last_seen}
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"Error: Configuration file not found: {config_path}")
            sys.exit(1)
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_dir = Path(log_config.get('log_dir', 'logs'))
        log_file = log_config.get('log_file', 'bar-monitor-v2.log')
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
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
        """Initialize all components using Supervision library."""
        self.logger.info("Initializing components with Supervision...")
        
        try:
            # 1. Initialize ByteTrack tracker (from Supervision)
            self.logger.info("1. Initializing ByteTrack tracker...")
            self.tracker = sv.ByteTrack()
            self.logger.info("   ✓ ByteTrack initialized (better than centroid!)")
            
            # 2. Setup line crossing zone (from Supervision)
            self.logger.info("2. Setting up line crossing zone...")
            counting_config = self.config.get('counting', {})
            line_y = counting_config.get('counting_line_y', 240)
            frame_width = self.config['camera'].get('width', 640)
            
            # Create line zone (horizontal line across frame)
            line_start = sv.Point(x=0, y=line_y)
            line_end = sv.Point(x=frame_width, y=line_y)
            
            self.line_zone = sv.LineZone(
                start=line_start,
                end=line_end
            )
            self.logger.info(f"   ✓ Line zone at Y={line_y}px")
            
            # 3. Setup visualizers (from Supervision)
            self.logger.info("3. Setting up annotators...")
            self.box_annotator = sv.BoxAnnotator(thickness=2)
            self.trace_annotator = sv.TraceAnnotator(thickness=2, trace_length=30)
            self.label_annotator = sv.LabelAnnotator(text_thickness=1, text_scale=0.5)
            self.logger.info("   ✓ Annotators ready")
            
            # 4. Initialize occupancy tracker (keep custom)
            self.logger.info("4. Initializing occupancy tracker...")
            occupancy_config = self.config.get('occupancy', {})
            self.occupancy_tracker = OccupancyTracker(
                db_path=occupancy_config.get('db_path', 'data/occupancy_v2.db'),
                snapshot_interval=occupancy_config.get('snapshot_interval', 60)
            )
            self.logger.info("   ✓ Occupancy tracker initialized")
            
            # 5. Open camera
            self.logger.info("5. Opening camera...")
            camera_source = self.config['camera']['source']
            
            if camera_source == 'rpi':
                # For Raspberry Pi camera, use libcamera
                self.logger.info("   Using Raspberry Pi camera (libcamera)")
                # Note: In production, use Hailo's GStreamer pipeline
                # For now, use OpenCV as fallback
                self.camera = cv2.VideoCapture(0)
            elif camera_source == 'usb':
                self.camera = cv2.VideoCapture(0)
            else:
                self.camera = cv2.VideoCapture(camera_source)
            
            if not self.camera.isOpened():
                self.logger.error("   ✗ Failed to open camera!")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['camera']['width'])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['camera']['height'])
            self.camera.set(cv2.CAP_PROP_FPS, self.config['camera']['fps'])
            
            self.logger.info("   ✓ Camera opened successfully")
            
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
        self.logger.info("System V2 started successfully!")
        self.logger.info("Using: Supervision library for tracking + zones")
        self.logger.info("=" * 60)
        self.logger.info("")
        self.logger.info("Press 'q' to quit")
        self.logger.info("=" * 60)
        
        self.running = True
        self._main_loop()
    
    def _detect_people(self, frame: np.ndarray) -> sv.Detections:
        """
        Detect people in frame.
        
        NOTE: In production, this should use Hailo HAT!
        For now, using a placeholder that you'll replace with Hailo detection.
        
        Returns:
            Supervision Detections object
        """
        # PLACEHOLDER: Replace this with Hailo detection pipeline
        # 
        # In production, you would:
        # 1. Run frame through Hailo GStreamer pipeline
        # 2. Get YOLO detections (bounding boxes + confidences + classes)
        # 3. Filter for person class (class_id=0)
        # 4. Convert to sv.Detections format
        
        # For demo purposes, return empty detections
        # (You'll see line zone but no actual detections until Hailo integrated)
        
        return sv.Detections.empty()
    
    def _main_loop(self):
        """
        Main monitoring loop using Supervision library.
        
        STOLEN CODE IN ACTION:
        1. ByteTrack for tracking (better than centroid)
        2. LineZone for counting (better than custom logic)
        3. Beautiful annotators (better than cv2.rectangle)
        """
        last_stats_time = time.time()
        stats_interval = 10
        frame_count = 0
        
        self.logger.info("Entering main monitoring loop...")
        self.logger.info("IMPORTANT: Hailo detection is placeholder - integrate with hailo-rpi5-examples!")
        
        while self.running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.warning("Failed to read frame")
                    continue
                
                frame_count += 1
                
                # 1. DETECT PEOPLE (using Hailo in production)
                detections = self._detect_people(frame)
                
                # 2. TRACK OBJECTS (using ByteTrack from Supervision)
                detections = self.tracker.update_with_detections(detections)
                
                # 3. LINE CROSSING (using LineZone from Supervision)
                crossed_in, crossed_out = self.line_zone.trigger(detections)
                
                # Update counters
                self.entries += crossed_in.sum()
                self.exits += crossed_out.sum()
                
                # 4. DWELL TIME TRACKING
                current_time = datetime.now()
                
                # Update active customers
                if detections.tracker_id is not None:
                    for track_id in detections.tracker_id:
                        if track_id not in self.active_customers:
                            # New customer
                            self.active_customers[track_id] = {
                                'entry_time': current_time,
                                'last_seen': current_time
                            }
                            self.logger.info(f"New customer: Track #{track_id}")
                        else:
                            # Update last seen
                            self.active_customers[track_id]['last_seen'] = current_time
                
                # Remove customers not seen for 30 seconds (exited)
                timeout_seconds = 30
                to_remove = []
                for track_id, data in self.active_customers.items():
                    if (current_time - data['last_seen']).total_seconds() > timeout_seconds:
                        # Customer exited
                        dwell_time = (data['last_seen'] - data['entry_time']).total_seconds() / 60.0
                        self.logger.info(f"Customer exited: Track #{track_id}, "
                                       f"Dwell time: {dwell_time:.1f} minutes")
                        to_remove.append(track_id)
                
                for track_id in to_remove:
                    del self.active_customers[track_id]
                
                # 5. VISUALIZE (using Supervision annotators)
                annotated_frame = frame.copy()
                
                # Draw line zone
                cv2.line(
                    annotated_frame,
                    (int(self.line_zone.vector.start.x), int(self.line_zone.vector.start.y)),
                    (int(self.line_zone.vector.end.x), int(self.line_zone.vector.end.y)),
                    (0, 255, 0), 2
                )
                
                # Draw detections (boxes, traces, labels)
                if len(detections) > 0:
                    annotated_frame = self.box_annotator.annotate(
                        scene=annotated_frame,
                        detections=detections
                    )
                    
                    annotated_frame = self.trace_annotator.annotate(
                        scene=annotated_frame,
                        detections=detections
                    )
                    
                    # Labels with track IDs
                    labels = [f"#{tracker_id}" for tracker_id in detections.tracker_id]
                    annotated_frame = self.label_annotator.annotate(
                        scene=annotated_frame,
                        detections=detections,
                        labels=labels
                    )
                
                # Add stats overlay
                current_occupancy = len(self.active_customers)
                cv2.putText(annotated_frame, f"Occupancy: {current_occupancy}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Entries: {self.entries}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Exits: {self.exits}", 
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Show frame
                cv2.imshow('Bar Monitor V2 (Supervision)', annotated_frame)
                
                # 6. UPDATE DATABASE
                self.occupancy_tracker.update({
                    'current_occupancy': current_occupancy,
                    'total_entries': self.entries,
                    'total_exits': self.exits,
                    'active_tracks': len(self.active_customers)
                })
                
                # 7. LOG STATS
                if time.time() - last_stats_time >= stats_interval:
                    self.logger.info("═" * 60)
                    self.logger.info(f"Status [{datetime.now().strftime('%H:%M:%S')}]")
                    self.logger.info(f"  Occupancy: {current_occupancy}")
                    self.logger.info(f"  Entries: {self.entries}")
                    self.logger.info(f"  Exits: {self.exits}")
                    self.logger.info(f"  Active Tracks: {len(self.active_customers)}")
                    
                    # Show dwell times
                    if self.active_customers:
                        self.logger.info("  Current Customers:")
                        for track_id, data in list(self.active_customers.items())[:5]:
                            dwell = (current_time - data['entry_time']).total_seconds() / 60.0
                            self.logger.info(f"    Track #{track_id}: {dwell:.1f} min")
                    
                    self.logger.info("═" * 60)
                    last_stats_time = time.time()
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            except KeyboardInterrupt:
                raise
            
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(1)
    
    def stop(self):
        """Stop the monitoring system."""
        if not self.running:
            return
        
        self.logger.info("Stopping system V2...")
        self.running = False
        
        if self.camera:
            self.camera.release()
        
        if self.occupancy_tracker:
            self.occupancy_tracker.stop()
        
        cv2.destroyAllWindows()
        
        self.logger.info("System stopped successfully")


def main():
    """Main entry point."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         BAR MONITORING SYSTEM V2 (Supervision)            ║
║                                                           ║
║  🔥 USING STOLEN CODE FROM:                               ║
║    • Supervision library (18k ⭐)                         ║
║    • ByteTrack tracking                                   ║
║    • LineZone for counting                                ║
║    • Beautiful annotators                                 ║
║                                                           ║
║  Features:                                                ║
║    • Real-time people detection                           ║
║    • Line crossing detection                              ║
║    • Dwell time tracking                                  ║
║    • Entry/Exit counting                                  ║
║                                                           ║
║  NOTE: Hailo detection is placeholder!                    ║
║        Integrate with hailo-rpi5-examples for real AI     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    system = BarMonitorV2()
    
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
