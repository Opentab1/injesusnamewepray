# Supervision - Installation & Usage

**Repo:** https://github.com/roboflow/supervision  
**Stars:** 18,000+  
**License:** MIT

---

## 📦 **Install:**

```bash
pip install supervision --break-system-packages
```

**That's it!** You don't copy their code - you install it as a library.

---

## 📖 **Their Official Docs:**

- **Main docs:** https://supervision.roboflow.com/
- **GitHub:** https://github.com/roboflow/supervision
- **Examples:** https://github.com/roboflow/supervision/tree/develop/examples

---

## 🎯 **What You Use From Supervision:**

### **1. Line Crossing (Entry/Exit Counting)**

```python
import supervision as sv

# Create line
line_zone = sv.LineZone(
    start=sv.Point(x=0, y=240),
    end=sv.Point(x=640, y=240)
)

# Count crossings
line_zone.trigger(detections)

print(f"In: {line_zone.in_count}, Out: {line_zone.out_count}")
```

**Docs:** https://supervision.roboflow.com/latest/detection/tools/line_zone/

---

### **2. Dwell Time (Polygon Zones)**

```python
import supervision as sv
import numpy as np

# Define zone
zone = sv.PolygonZone(
    polygon=np.array([[0,0], [640,0], [640,480], [0,480]])
)

# Track people in zone
zone.trigger(detections)

print(f"People in zone: {zone.current_count}")
```

**Docs:** https://supervision.roboflow.com/latest/detection/tools/polygon_zone/

---

### **3. Tracking**

```python
import supervision as sv

# ByteTrack tracker
tracker = sv.ByteTrack()

# Track detections
detections = tracker.update_with_detections(detections)
```

**Docs:** https://supervision.roboflow.com/latest/trackers/

---

### **4. Annotations (Pretty Visualizations)**

```python
import supervision as sv

# Create annotators
box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()
trace_annotator = sv.TraceAnnotator()

# Annotate frame
frame = box_annotator.annotate(scene=frame, detections=detections)
frame = label_annotator.annotate(scene=frame, detections=detections)
```

**Docs:** https://supervision.roboflow.com/latest/detection/annotators/

---

## 📚 **Learn More:**

**Browse their examples:**
```bash
git clone https://github.com/roboflow/supervision.git
cd supervision/examples
ls
```

**Their examples include:**
- Line crossing counting
- Zone time tracking  
- Object tracking
- Heatmaps
- And more!

---

## ✅ **You DON'T Copy Their Code:**

- ❌ Don't copy their repo
- ❌ Don't copy their library files
- ✅ Just install: `pip install supervision`
- ✅ Then import: `import supervision as sv`
- ✅ Use their functions in YOUR code

---

## 🎯 **Summary:**

```bash
# Install it
pip install supervision --break-system-packages

# Use it in your code
import supervision as sv
```

**That's how libraries work! Install, don't copy!**
