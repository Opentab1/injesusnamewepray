# Bar Monitoring System - Project Overview

## 🎯 What This System Does

This is a complete people counting and occupancy tracking system for your bar using the Raspberry Pi 5 with Hailo AI HAT.

### Core Features Implemented:
✅ **Real-time People Detection** - Uses Hailo AI accelerator for 30+ FPS detection  
✅ **Entry/Exit Counting** - Tracks people crossing a virtual line  
✅ **Occupancy Tracking** - Maintains current count of people inside  
✅ **Data Storage** - SQLite database with historical data  
✅ **Statistics & Reports** - Peak occupancy, hourly/daily stats  

---

## 📁 Project Structure

```
bar-monitor/
│
├── README.md                    # Quick overview and features
├── SETUP_GUIDE.md              # Complete installation guide
├── PROJECT_OVERVIEW.md         # This file - explains the system
│
├── main.py                     # Main application entry point
├── test_hailo.py              # Test script to verify installation
├── requirements.txt            # Python dependencies
│
├── config/
│   └── settings.yaml          # Configuration file (EDIT THIS!)
│
├── hailo_integration/         # Hailo HAT integration code
│   ├── __init__.py           # Module initialization
│   ├── people_detector.py    # Hailo detection interface
│   ├── counting_logic.py     # Entry/exit counting logic
│   ├── occupancy_tracker.py  # Occupancy tracking & database
│   └── hailo_runner.py       # Official examples integration
│
├── sensors/                   # Other sensors (future)
│   └── (temperature, audio, lux, BLE modules)
│
├── data/                      # Data storage
│   └── occupancy.db          # SQLite database (auto-created)
│
└── logs/                      # Application logs
    └── bar-monitor.log       # Log file (auto-created)
```

---

## 🔍 How Each Component Works

### 1. **people_detector.py** - Hailo Detection Interface

**Purpose:** Interfaces with the Hailo AI HAT to get person detections.

**What it does:**
- Manages connection to Hailo accelerator
- Receives video frames from camera
- Returns detected people with bounding boxes
- Runs at 30+ FPS with minimal CPU usage

**Key Classes:**
- `Detection`: Represents one detected person
- `PeopleDetector`: Main detection interface
- `HailoSimpleDetector`: Simplified wrapper

**Example:**
```python
detector = HailoSimpleDetector(camera='rpi')
detector.start()
people = detector.get_people_count()  # Returns: 5
```

---

### 2. **counting_logic.py** - Entry/Exit Counting

**Purpose:** Counts people entering and exiting by tracking movement across a line.

**How it works:**

```
Frame 1: Person at Y=200 (above line at Y=240)
Frame 2: Person at Y=220 (still above)
Frame 3: Person at Y=250 (crossed to below) → ENTRY DETECTED! +1

Frame 4: Person at Y=270 (below line)
Frame 5: Person at Y=250 (moving up)
Frame 6: Person at Y=220 (crossed to above) → EXIT DETECTED! -1
```

**Key Classes:**
- `CentroidTracker`: Tracks people across frames using center point
- `EntryExitCounter`: Detects line crossings and counts

**Algorithm:**
1. Get person detections from Hailo
2. Calculate center point (centroid) of each person
3. Match centroids frame-to-frame (same person?)
4. Track each person's position history
5. Detect when someone crosses the counting line
6. Determine direction → entry or exit

**Example:**
```python
counter = EntryExitCounter(counting_line_y=240)
centroids = [(320, 250), (400, 180)]  # 2 people detected
entries, exits = counter.update(centroids)
occupancy = counter.get_occupancy()  # Returns: 15
```

---

### 3. **occupancy_tracker.py** - Data Storage & Statistics

**Purpose:** Manages occupancy data, stores to database, provides statistics.

**Database Schema:**

**Table: snapshots** (periodic state snapshots)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TEXT | When snapshot taken |
| current_occupancy | INTEGER | People inside at this time |
| total_entries | INTEGER | Total entries since start |
| total_exits | INTEGER | Total exits since start |
| active_tracks | INTEGER | People currently tracked |

**Table: events** (individual entry/exit events)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TEXT | When event occurred |
| event_type | TEXT | 'entry' or 'exit' |
| occupancy_after | INTEGER | Occupancy after this event |

**Table: sessions** (tracking sessions)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| start_time | TEXT | Session start |
| end_time | TEXT | Session end |
| total_entries | INTEGER | Entries in this session |
| total_exits | INTEGER | Exits in this session |
| peak_occupancy | INTEGER | Highest occupancy |

**Features:**
- Auto-saves snapshot every 60 seconds (configurable)
- Records every entry/exit event
- Provides historical data queries
- Calculates peak occupancy
- Thread-safe for real-time updates

**Example:**
```python
tracker = OccupancyTracker(db_path='data/occupancy.db')
tracker.update(stats)  # Update with latest counts

# Get current state
occupancy = tracker.get_current_occupancy()  # Returns: 15

# Get last hour of history
history = tracker.get_history(hours=1)  # Returns list of snapshots

# Get peak today
peak, time = tracker.get_peak_occupancy(hours=24)  # Returns: (28, "2024-11-18T21:30:00")
```

---

### 4. **hailo_runner.py** - Official Examples Integration

**Purpose:** Integrates with the official hailo-rpi5-examples code.

**Why this approach?**
Instead of reimplementing Hailo's detection pipeline (complex!), we:
1. Use their official, tested, optimized code
2. Extract detection results
3. Feed to our counting logic

**What it does:**
- Finds hailo-rpi5-examples installation
- Checks Hailo device status
- Can launch detection pipeline
- Provides clean Python interface

**Example:**
```python
runner = HailoRunner()

# Check installation
if runner.check_installation():
    print("✓ Hailo ready")

# Get device info
info = runner.get_hailo_info()
print(info['output'])  # Shows Hailo chip info
```

---

### 5. **main.py** - Main Application

**Purpose:** Ties everything together and runs the system.

**Flow:**
```
1. Load configuration from settings.yaml
2. Initialize logging
3. Initialize Hailo runner
4. Initialize counter
5. Initialize tracker
6. Start detection loop:
   │
   ├─→ Get detections from Hailo
   ├─→ Update counter (get entries/exits)
   ├─→ Update tracker (store to DB)
   ├─→ Log statistics every 10 seconds
   └─→ Repeat at 30 FPS
7. On Ctrl+C: gracefully shutdown
```

**Run it:**
```bash
python3 main.py
```

**Output:**
```
╔═══════════════════════════════════════════════════════════╗
║            BAR MONITORING SYSTEM v1.0                     ║
╚═══════════════════════════════════════════════════════════╝

Initializing components...
✓ All components initialized successfully

Current Status [21:30:45]
  Occupancy: 15 people
  Total Entries: 87
  Total Exits: 72
  Active Tracks: 3
  Peak Today: 28 people
```

---

## ⚙️ Configuration (settings.yaml)

### Critical Settings You MUST Configure:

#### 1. Camera Source
```yaml
camera:
  source: 'rpi'  # Options: 'rpi', 'usb', '/dev/video0'
```

#### 2. Counting Line Position
**Most important setting!**

```yaml
counting:
  counting_line_y: 240  # Y-coordinate in pixels
```

How to find the right value:
1. Run detection: `python basic_pipelines/detection.py --input rpi`
2. Look at doorway in video feed
3. Frame is 480 pixels tall (0=top, 240=middle, 480=bottom)
4. Set line to doorway threshold position

#### 3. Entry Direction
```yaml
counting:
  entry_direction: 'down'  # or 'up'
```

- `'down'`: Entering people move downward in frame
- `'up'`: Entering people move upward in frame

Watch your video feed to determine this.

---

## 🚀 Quick Start

### Installation
```bash
# 1. Install Hailo software
sudo apt install hailo-all

# 2. Verify device
hailortcli fw-control identify

# 3. Clone official examples
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh

# 4. Install project dependencies
cd /workspace/bar-monitor
pip3 install -r requirements.txt
```

### Testing
```bash
# Test Hailo installation
python3 test_hailo.py

# Test basic detection
cd ~/hailo-rpi5-examples
source setup_env.sh
python basic_pipelines/detection.py --input rpi
```

### Configuration
```bash
# Edit settings
nano config/settings.yaml

# Key settings:
# - counting_line_y: Set to doorway position
# - entry_direction: 'up' or 'down'
# - camera source: 'rpi' or 'usb'
```

### Run
```bash
python3 main.py
```

---

## 📊 Data Analysis

### Query Database Directly

```bash
sqlite3 data/occupancy.db
```

**Get current occupancy:**
```sql
SELECT current_occupancy, timestamp 
FROM snapshots 
ORDER BY timestamp DESC 
LIMIT 1;
```

**Get hourly entry counts:**
```sql
SELECT 
    strftime('%H:00', timestamp) as hour,
    COUNT(*) as entries
FROM events 
WHERE event_type = 'entry'
    AND timestamp >= datetime('now', '-24 hours')
GROUP BY hour
ORDER BY hour;
```

**Get peak occupancy today:**
```sql
SELECT 
    MAX(current_occupancy) as peak,
    timestamp
FROM snapshots
WHERE DATE(timestamp) = DATE('now');
```

**Get average occupancy by hour:**
```sql
SELECT 
    strftime('%H:00', timestamp) as hour,
    AVG(current_occupancy) as avg_occupancy
FROM snapshots
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY hour
ORDER BY hour;
```

---

## 🎓 Understanding the Technology

### What is the Hailo HAT?

The Hailo AI HAT is a **neural processing unit (NPU)** that:
- Contains dedicated AI processor chip
- Runs deep learning models at 26 TOPS (Hailo-8) or 13 TOPS (Hailo-8L)
- Offloads AI computation from CPU
- Enables real-time person detection at 30+ FPS

**Without Hailo:**
- CPU does detection: 2-5 FPS, 90% CPU usage
- Slow, unreliable counting
- Can't run other sensors simultaneously

**With Hailo:**
- Hailo chip does detection: 30+ FPS, <10% CPU usage
- Fast, accurate counting
- CPU free for other sensors

### What is YOLO?

YOLO (You Only Look Once) is an object detection algorithm:
- Input: Image frame
- Output: Bounding boxes around detected objects
- Speed: Very fast (real-time capable)

We use pre-trained YOLO models on the Hailo:
- **yolov6n**: Fastest, good accuracy (recommended)
- **yolov8s**: Balanced speed/accuracy
- **yolov8m**: Most accurate, slower

### How Tracking Works

**Centroid Tracking Algorithm:**

```python
Frame 1: Detect person at (100, 200) → Assign ID: 1
Frame 2: Detect person at (105, 210) → Match to ID: 1 (close distance)
Frame 3: Detect person at (110, 220) → Match to ID: 1
Frame 4: No detection → Mark ID: 1 as disappeared
Frame 5: Still no detection → Remove ID: 1 after timeout
```

**Matching Logic:**
- Calculate distance between new detection and existing tracks
- Match to closest track if distance < threshold (50 pixels)
- If no close match, create new track ID
- If track disappears for >30 frames (1 second), remove it

---

## 🔮 Future Enhancements

### Phase 2: Additional Sensors

**Temperature Monitoring:**
```python
# sensors/temperature.py
from Adafruit_DHT import read_retry
temp, humidity = read_retry(DHT22, GPIO_PIN)
```

**Audio - Song Detection:**
```python
# sensors/audio.py
from dejavu import Dejavu
song = dejavu.recognize_from_microphone()
```

**Audio - Decibel Level:**
```python
# sensors/audio.py
import pyaudio
# Calculate RMS → convert to dB
db_level = 20 * log10(rms / reference)
```

**Light Level:**
```python
# sensors/light.py
from smbus2 import SMBus
lux = read_bh1750_sensor()
```

**BLE Tracking:**
```python
# sensors/bluetooth.py
import bluetooth
devices = bluetooth.discover_devices()
unique_count = len(set(devices))
```

### Phase 3: Web Dashboard

Create a real-time web interface:
- Live occupancy count
- Historical graphs
- Current song playing
- Temperature, noise level, light level
- Entry/exit timeline

Technologies:
- Flask/FastAPI backend
- React/Vue.js frontend
- Chart.js for graphs
- WebSocket for real-time updates

---

## 🐛 Common Issues & Solutions

### Issue: No people detected

**Solutions:**
1. Check camera is working: `libcamera-hello`
2. Verify Hailo device: `hailortcli fw-control identify`
3. Lower confidence threshold in config: `confidence_threshold: 0.3`
4. Check lighting - add more light if dim

### Issue: Wrong entry/exit counts

**Solutions:**
1. Adjust counting line position
2. Fix entry direction ('up' vs 'down')
3. Increase tracking parameters:
   ```yaml
   max_disappeared: 50
   max_distance: 75
   ```

### Issue: Database locked

**Solution:**
```bash
# Stop all instances
pkill -f main.py

# Check for locks
fuser data/occupancy.db

# Restart
python3 main.py
```

---

## 📚 Code Examples

### Get Current Occupancy
```python
from hailo_integration import OccupancyTracker

tracker = OccupancyTracker()
occupancy = tracker.get_current_occupancy()
print(f"Current occupancy: {occupancy}")
```

### Get Last Hour Stats
```python
history = tracker.get_history(hours=1)
for snapshot in history:
    print(f"{snapshot['timestamp']}: {snapshot['current_occupancy']} people")
```

### Get All Entry Events Today
```python
from datetime import datetime
events = tracker.get_events(hours=24)
entries = [e for e in events if e['event_type'] == 'entry']
print(f"Entries today: {len(entries)}")
```

### Custom Detection Loop
```python
from hailo_integration import HailoSimpleDetector, EntryExitCounter

detector = HailoSimpleDetector(camera='rpi')
counter = EntryExitCounter(counting_line_y=240)

detector.start()

while True:
    detections = detector.get_detections()
    centroids = [d.center for d in detections]
    entries, exits = counter.update(centroids)
    
    if entries > 0:
        print(f"{entries} people entered!")
    if exits > 0:
        print(f"{exits} people exited!")
    
    time.sleep(0.033)  # 30 FPS
```

---

## 📞 Support

For issues with:
- **This project**: Check logs, run test_hailo.py, review configuration
- **Hailo HAT**: [Hailo Community Forum](https://community.hailo.ai/)
- **Raspberry Pi**: [Raspberry Pi Forums](https://forums.raspberrypi.com/)

---

## 🎉 Success Checklist

- [ ] Hailo HAT properly installed and detected
- [ ] Camera working and detecting people
- [ ] Counting line configured correctly
- [ ] Entry direction set properly
- [ ] System running and counting accurately
- [ ] Database storing data
- [ ] Logs showing regular updates

---

**You're all set! Your bar monitoring system is ready to track occupancy.** 🍺📊
