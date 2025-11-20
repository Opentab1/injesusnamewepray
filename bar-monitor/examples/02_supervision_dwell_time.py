"""
Dwell Time Example - USING SUPERVISION'S PolygonZone

Source: https://github.com/roboflow/supervision/blob/develop/examples/time_in_zone/

This is NOT custom code - this uses Supervision's built-in zone tracking!

⭐ Supervision: 18,000 stars
📖 Docs: https://supervision.roboflow.com/latest/detection/tools/polygon_zone/
"""

import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO

# For Hailo, replace YOLO with Hailo detection
# See: ~/hailo-rpi5-examples/basic_pipelines/detection_with_tracking.py

def main():
    # Load model
    model = YOLO("yolov8n.pt")
    
    # ByteTrack tracker (from Supervision)
    tracker = sv.ByteTrack()
    
    # Define zone (whole frame = bar area)
    zone_polygon = np.array([
        [0, 0],
        [640, 0],
        [640, 480],
        [0, 480]
    ])
    
    # Polygon zone for dwell time (from Supervision)
    zone = sv.PolygonZone(polygon=zone_polygon)
    
    # Annotators (from Supervision)
    box_annotator = sv.BoxAnnotator()
    zone_annotator = sv.PolygonZoneAnnotator(
        zone=zone,
        color=sv.Color.GREEN,
        thickness=2
    )
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect
        results = model(frame)[0]
        detections = sv.Detections.from_ultralytics(results)
        
        # Filter people only
        detections = detections[detections.class_id == 0]
        
        # Track (from Supervision)
        detections = tracker.update_with_detections(detections)
        
        # Trigger zone (from Supervision)
        # This tracks which objects are in the zone
        zone.trigger(detections)
        
        # Annotate (from Supervision)
        frame = box_annotator.annotate(scene=frame, detections=detections)
        frame = zone_annotator.annotate(scene=frame)
        
        # Show count
        cv2.putText(
            frame,
            f"In Zone: {zone.current_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        
        cv2.imshow("Dwell Time (Supervision Example)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
