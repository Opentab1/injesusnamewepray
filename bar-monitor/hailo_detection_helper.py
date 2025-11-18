#!/usr/bin/env python3
"""
Hailo Detection Helper - Integrate with Official Examples

This file shows HOW to integrate Hailo's official detection code
with our Supervision-based tracking system.

WHAT TO STEAL FROM HAILO:
- hailo-rpi5-examples/basic_pipelines/detection_with_tracking.py
- Has ByteTrack already built-in
- Has GStreamer pipeline optimized for Hailo
- Has person detection

HOW TO INTEGRATE:
1. Copy detection pipeline from Hailo examples
2. Convert output to sv.Detections format
3. Pass to our main_v2.py system
"""

import numpy as np
import supervision as sv
from typing import List, Tuple


def convert_hailo_to_supervision(hailo_detections: List[dict]) -> sv.Detections:
    """
    Convert Hailo detection format to Supervision Detections.
    
    Hailo detections format (from their examples):
    [
        {
            'bbox': [x1, y1, x2, y2],
            'confidence': 0.95,
            'class_id': 0,  # 0 = person in COCO
            'class_name': 'person'
        },
        ...
    ]
    
    Args:
        hailo_detections: List of detection dicts from Hailo
        
    Returns:
        sv.Detections object for Supervision library
    """
    if not hailo_detections:
        return sv.Detections.empty()
    
    # Extract components
    xyxy = np.array([d['bbox'] for d in hailo_detections])
    confidence = np.array([d['confidence'] for d in hailo_detections])
    class_id = np.array([d['class_id'] for d in hailo_detections])
    
    # Create Supervision Detections
    detections = sv.Detections(
        xyxy=xyxy,
        confidence=confidence,
        class_id=class_id
    )
    
    return detections


def filter_person_class(detections: sv.Detections) -> sv.Detections:
    """
    Filter detections to only include people (class_id=0 in COCO).
    
    Args:
        detections: All detections
        
    Returns:
        Filtered detections (only people)
    """
    if len(detections) == 0:
        return detections
    
    # COCO class 0 = person
    person_mask = detections.class_id == 0
    return detections[person_mask]


# ============================================================================
# EXAMPLE: How to integrate with Hailo's official examples
# ============================================================================

"""
STEP 1: Copy Hailo's detection pipeline

From: ~/hailo-rpi5-examples/basic_pipelines/detection_with_tracking.py

Their code has:
- GStreamer pipeline with Hailo inference
- ByteTrack tracking built-in
- Person detection with YOLOv6n/v8

STEP 2: Use their GStreamer pipeline

# From Hailo examples
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Their pipeline (simplified)
pipeline_string = '''
    v4l2src device=/dev/video0 ! 
    video/x-raw,width=640,height=480 ! 
    hailonet hef-path=yolov6n.hef ! 
    hailotracker tracking-method=byte-track ! 
    hailooverlay ! 
    autovideosink
'''

STEP 3: Extract detections from their pipeline

# Add a callback to get detection results
def on_detection(element, detections):
    # Convert to Supervision format
    sv_detections = convert_hailo_to_supervision(detections)
    
    # Now use with our Supervision-based system
    sv_detections = tracker.update_with_detections(sv_detections)
    line_zone.trigger(sv_detections)
    # etc...

STEP 4: Run both together

# Their Hailo pipeline runs in GStreamer
# We intercept detections and pass to Supervision
# Best of both worlds: Hailo speed + Supervision features!
"""


# ============================================================================
# INTEGRATION TEMPLATE
# ============================================================================

class HailoSupervisionBridge:
    """
    Bridge between Hailo's official examples and Supervision library.
    
    This combines:
    - Hailo HAT detection (fast AI inference)
    - Supervision tracking & zones (18k stars, battle-tested)
    
    USAGE:
        bridge = HailoSupervisionBridge()
        bridge.start()
    """
    
    def __init__(self):
        """Initialize bridge."""
        # Supervision components
        self.tracker = sv.ByteTrack()
        self.line_zone = None  # Set up in initialize()
        
        # Hailo components (to be filled)
        self.hailo_pipeline = None  # From hailo-rpi5-examples
    
    def on_hailo_detection(self, detections):
        """
        Callback when Hailo detects objects.
        
        This is called by Hailo's GStreamer pipeline.
        We convert to Supervision format and process.
        """
        # Convert Hailo → Supervision
        sv_detections = convert_hailo_to_supervision(detections)
        
        # Filter to people only
        sv_detections = filter_person_class(sv_detections)
        
        # Track with ByteTrack
        sv_detections = self.tracker.update_with_detections(sv_detections)
        
        # Check line crossing
        if self.line_zone:
            crossed_in, crossed_out = self.line_zone.trigger(sv_detections)
            print(f"In: {crossed_in.sum()}, Out: {crossed_out.sum()}")
        
        return sv_detections
    
    def start(self):
        """Start the integrated system."""
        print("TODO: Integrate with hailo-rpi5-examples")
        print("See: ~/hailo-rpi5-examples/basic_pipelines/detection_with_tracking.py")


# ============================================================================
# INSTRUCTIONS FOR USER
# ============================================================================

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          HAILO + SUPERVISION INTEGRATION GUIDE            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

📖 HOW TO INTEGRATE:
════════════════════════════════════════════════════════════

STEP 1: Find Hailo's official detection code
  → cd ~/hailo-rpi5-examples/basic_pipelines
  → Look at: detection_with_tracking.py

STEP 2: Copy their GStreamer pipeline
  → They have ByteTrack built-in
  → They have person detection
  → They have Hailo-optimized inference

STEP 3: Add callback for detections
  → When their pipeline detects people
  → Convert to Supervision format
  → Use: convert_hailo_to_supervision()

STEP 4: Pass to our Supervision system
  → Use Supervision for line crossing
  → Use Supervision for dwell zones
  → Use Supervision for visualizations

EXAMPLE CODE:
════════════════════════════════════════════════════════════

# In Hailo's pipeline callback:
def on_detection(element, hailo_detections):
    # Convert to Supervision
    sv_detections = convert_hailo_to_supervision(hailo_detections)
    
    # Track with ByteTrack
    sv_detections = tracker.update_with_detections(sv_detections)
    
    # Line crossing
    crossed_in, crossed_out = line_zone.trigger(sv_detections)
    
    # Done! Now you have:
    # ✓ Hailo speed (30+ FPS)
    # ✓ Supervision features (line crossing, zones, viz)

FILES TO REFERENCE:
════════════════════════════════════════════════════════════

1. ~/hailo-rpi5-examples/basic_pipelines/detection_with_tracking.py
   → Hailo's official detection code

2. /workspace/bar-monitor/main_v2.py
   → Our Supervision-based tracking system

3. This file (hailo_detection_helper.py)
   → Helper functions to convert Hailo → Supervision

NEXT STEPS:
════════════════════════════════════════════════════════════

1. Study Hailo's detection_with_tracking.py
2. Copy their GStreamer pipeline
3. Add on_detection callback
4. Use convert_hailo_to_supervision() to bridge
5. Pass to our main_v2.py system

RESULT:
════════════════════════════════════════════════════════════

Best of both worlds:
  ✓ Hailo HAT speed (30+ FPS)
  ✓ Supervision features (18k stars, battle-tested)
  ✓ Less code (using proven libraries)
  ✓ Better tracking (ByteTrack > centroid)
  ✓ Line crossing (Supervision > custom)
  ✓ Beautiful visualizations (Supervision annotators)

════════════════════════════════════════════════════════════
    """)
