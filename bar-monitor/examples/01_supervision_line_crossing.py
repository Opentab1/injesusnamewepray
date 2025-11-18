"""
Line Crossing Example - COPIED FROM SUPERVISION REPO

Source: https://github.com/roboflow/supervision/blob/develop/examples/count_objects_crossing_line/line_zone_count.py

This is NOT custom code - this is from Supervision's official examples!
We just adapted their example for our camera setup.

⭐ Supervision: 18,000 stars
📖 Docs: https://supervision.roboflow.com/latest/how_to/track_objects/
"""

import cv2
import supervision as sv
from ultralytics import YOLO

# For Hailo, replace YOLO with Hailo detection
# See: ~/hailo-rpi5-examples/basic_pipelines/detection_with_tracking.py

# This example is from Supervision repo - we just point it at our camera
def main():
    # Load model (Supervision supports many)
    # For Hailo, you'd use Hailo's detection instead
    model = YOLO("yolov8n.pt")
    
    # ByteTrack tracker (from Supervision)
    tracker = sv.ByteTrack()
    
    # Line zone for counting (from Supervision)
    line_zone = sv.LineZone(
        start=sv.Point(x=0, y=240),
        end=sv.Point(x=640, y=240)
    )
    
    # Annotators (from Supervision)
    box_annotator = sv.BoxAnnotator()
    line_annotator = sv.LineZoneAnnotator()
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect (use Hailo here in production)
        results = model(frame)[0]
        detections = sv.Detections.from_ultralytics(results)
        
        # Filter people only
        detections = detections[detections.class_id == 0]
        
        # Track (from Supervision)
        detections = tracker.update_with_detections(detections)
        
        # Count line crossings (from Supervision)
        line_zone.trigger(detections)
        
        # Annotate (from Supervision)
        frame = box_annotator.annotate(scene=frame, detections=detections)
        frame = line_annotator.annotate(frame=frame, line_counter=line_zone)
        
        cv2.imshow("Line Crossing (Supervision Example)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"Total crossed: {line_zone.in_count + line_zone.out_count}")


if __name__ == "__main__":
    main()
