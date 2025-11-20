# How to Use Hailo Examples (NOT Custom Code!)

**Source:** https://github.com/hailo-ai/hailo-rpi5-examples  
**Stars:** 500+  
**Maintained by:** Hailo AI (official)

---

## 📖 **DO NOT WRITE CUSTOM HAILO CODE!**

Hailo provides official, optimized examples. **USE THEIRS!**

---

## 🚀 **Installation**

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh
```

This installs:
- Pre-trained models (YOLOv6n, YOLOv8, etc.)
- GStreamer pipelines
- Python dependencies
- Example scripts

---

## 🎯 **Examples to Use**

### **1. Basic Detection**

```bash
cd ~/hailo-rpi5-examples/basic_pipelines
python3 detection.py
```

**What it does:**
- Opens camera
- Detects people (and other objects)
- Shows bounding boxes
- Real-time at 30+ FPS

**USE THIS CODE!** Don't rewrite it.

---

### **2. Detection with Tracking**

```bash
cd ~/hailo-rpi5-examples/basic_pipelines
python3 detection_with_tracking.py
```

**What it does:**
- Opens camera
- Detects people
- **Tracks them with ByteTrack** (built-in!)
- Shows track IDs
- Real-time at 30+ FPS

**THIS IS THE ONE TO USE!** It already has tracking built-in.

---

### **3. Pose Estimation**

```bash
cd ~/hailo-rpi5-examples/basic_pipelines
python3 pose_estimation.py
```

**What it does:**
- Detects people
- Estimates their pose (skeleton)
- Could be used for counting people sitting vs standing

---

## 🔗 **How to Connect to Supervision**

**DON'T REWRITE HAILO CODE!** Instead, add Supervision to their examples:

### **Step 1: Start with their code**

```bash
cp ~/hailo-rpi5-examples/basic_pipelines/detection_with_tracking.py my_bar_monitor.py
```

### **Step 2: Add Supervision line crossing**

In their detection callback, add:

```python
import supervision as sv

# Create line zone (once at start)
line_zone = sv.LineZone(
    start=sv.Point(x=0, y=240),
    end=sv.Point(x=640, y=240)
)

# In their detection loop, add:
detections = sv.Detections(
    xyxy=hailo_boxes,
    confidence=hailo_confidences,
    class_id=hailo_class_ids,
    tracker_id=hailo_tracker_ids  # They already have ByteTrack!
)

# Count crossings
line_zone.trigger(detections)

print(f"In: {line_zone.in_count}, Out: {line_zone.out_count}")
```

### **Step 3: Done!**

Now you have:
- ✅ Hailo detection (30+ FPS)
- ✅ ByteTrack tracking (from Hailo)
- ✅ Line crossing (from Supervision)
- ✅ All battle-tested code!

---

## 📚 **Their Documentation**

- **Main repo:** https://github.com/hailo-ai/hailo-rpi5-examples
- **Documentation:** https://hailo.ai/developer-zone/documentation/
- **Forum:** https://community.hailo.ai/

---

## 💡 **Key Principle**

**USE THEIR CODE, DON'T REWRITE IT!**

Hailo spent years optimizing their code. It's:
- ✅ Faster than custom code
- ✅ More stable
- ✅ Better maintained
- ✅ Well-documented
- ✅ Updated regularly

**Just add Supervision on top for line crossing/zones!**

---

## 🎯 **Final Architecture**

```
Hailo Examples (detection + tracking)
         ↓
   Convert to sv.Detections
         ↓
Supervision (line crossing + zones)
         ↓
      SQLite (storage)
         ↓
  Streamlit (dashboard)
```

**All code from battle-tested repos!** 🔥
