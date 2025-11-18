# Hailo HAT Setup Guide for Bar Monitoring System

## 📋 Table of Contents
1. [Hardware Requirements](#hardware-requirements)
2. [Initial Raspberry Pi Setup](#initial-raspberry-pi-setup)
3. [Installing Hailo Software](#installing-hailo-software)
4. [Installing This Project](#installing-this-project)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Running the System](#running-the-system)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Hardware Requirements

### Required:
- ✅ Raspberry Pi 5 (4GB or 8GB RAM recommended)
- ✅ Hailo AI HAT (Hailo-8L or Hailo-8)
- ✅ Pi Camera Module or USB Webcam
- ✅ Power supply (5V 5A for Pi 5)
- ✅ MicroSD card (32GB+ recommended)

### Optional (for complete bar monitoring):
- DHT22 Temperature/Humidity sensor
- BH1750 Lux sensor
- USB Microphone
- Bluetooth capability (built-in on Pi 5)

---

## 🚀 Initial Raspberry Pi Setup

### 1. Install Raspberry Pi OS

```bash
# Use Raspberry Pi Imager to install:
# "Raspberry Pi OS (64-bit)" - recommended
# Enable SSH and set username/password during imaging
```

### 2. First Boot Setup

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential
sudo apt install -y raspberrypi-kernel-headers

# Reboot
sudo reboot
```

### 3. Enable Camera (if using Pi Camera)

```bash
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
# Reboot when prompted
```

---

## 🎯 Installing Hailo Software

### Step 1: Install Hailo Package

This is THE most important step - this installs the Hailo AI accelerator drivers and tools.

```bash
# Install Hailo software suite
sudo apt update
sudo apt install -y hailo-all
```

**What this does:**
- Installs Hailo Runtime (HailoRT)
- Installs Hailo CLI tools
- Installs necessary drivers for the Hailo chip
- Sets up GStreamer plugins for Hailo

### Step 2: Verify Hailo Device

After installing, verify your Hailo HAT is detected:

```bash
hailortcli fw-control identify
```

**Expected output:**
```
Executing on device: 0000:01:00.0
Identifying board
Control Protocol Version: 2
Firmware Version: 4.17.0 (release,app,extended context switch buffer)
Logger Version: 0
Board Name: Hailo-8
Device Architecture: HAILO8L
...
```

If you see this, **your Hailo HAT is working!** 🎉

If you get an error:
- Check that HAT is properly seated on GPIO pins
- Try reboot: `sudo reboot`
- Check dmesg: `dmesg | grep hailo`

---

## 📦 Installing Hailo Examples (Official)

### Clone Official Examples

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
```

### Run Installation Script

```bash
./install.sh
```

**What this does:**
- Downloads pre-trained YOLO models for Hailo
- Sets up Python virtual environment
- Installs GStreamer plugins
- Configures detection pipelines
- Takes 5-10 minutes

### Test Detection Pipeline

```bash
source setup_env.sh

# Test with Pi Camera
python basic_pipelines/detection.py --input rpi

# OR test with USB camera
python basic_pipelines/detection.py --input usb
```

**You should see:**
- Live video feed with bounding boxes around detected people
- FPS counter (should be 30+ FPS)
- Very low CPU usage (Hailo does the work!)

Press `Ctrl+C` to stop.

---

## 🏗️ Installing This Project

### Clone Bar Monitor Project

```bash
cd ~
cd /workspace/bar-monitor  # Or wherever you placed this project
```

### Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### Create Data Directories

```bash
mkdir -p data logs
```

---

## ⚙️ Configuration

### 1. Edit Configuration File

Open `config/settings.yaml` and adjust settings:

```yaml
camera:
  source: 'rpi'  # Change to 'usb' if using USB camera
  
counting:
  counting_line_y: 240  # IMPORTANT: Set this to your doorway position!
  entry_direction: 'down'  # Direction entering people move in frame
```

### 2. Determine Counting Line Position

The counting line is a horizontal line in your camera view where people are counted.

**To find the right Y-coordinate:**

1. Run the test detection:
```bash
cd ~/hailo-rpi5-examples
source setup_env.sh
python basic_pipelines/detection.py --input rpi
```

2. Look at your video feed
3. Note where your doorway threshold is vertically
4. Frame is 480 pixels tall:
   - `y=0` = top of frame
   - `y=240` = middle
   - `y=480` = bottom

5. Set `counting_line_y` in config to that position

**Example:**
- If doorway is near bottom of frame: `counting_line_y: 400`
- If doorway is in middle: `counting_line_y: 240`
- If doorway is near top: `counting_line_y: 100`

### 3. Determine Entry Direction

Watch people walking through doorway:
- If entering people move **downward** in frame: `entry_direction: 'down'`
- If entering people move **upward** in frame: `entry_direction: 'up'`

---

## 🧪 Testing

### 1. Test Hailo Installation

```bash
python3 test_hailo.py
```

This checks:
- ✓ Hailo device detected
- ✓ hailo-rpi5-examples installed
- ✓ Camera available
- ✓ Python packages installed
- ✓ GStreamer working

### 2. Test Counting Logic

```bash
cd hailo_integration
python3 counting_logic.py
```

This runs a simulation of the counting logic.

### 3. Test Occupancy Tracker

```bash
cd hailo_integration
python3 occupancy_tracker.py
```

This tests the database and tracking system.

---

## 🎬 Running the System

### Start the Bar Monitor

```bash
cd /workspace/bar-monitor
python3 main.py
```

**You should see:**
```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║            BAR MONITORING SYSTEM v1.0                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Initializing components...
1. Initializing Hailo HAT...
2. Initializing Entry/Exit Counter...
3. Initializing Occupancy Tracker...
✓ All components initialized successfully

System started successfully!
Monitoring Status:
  Camera: rpi
  Model: yolov6n
  Counting Line: Y=240px
  Database: data/occupancy.db
```

### View Logs

Real-time logs:
```bash
tail -f logs/bar-monitor.log
```

### Check Database

```bash
sqlite3 data/occupancy.db

# Query current stats
SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT 10;

# Query events
SELECT * FROM events ORDER BY timestamp DESC LIMIT 20;
```

### Stop the System

Press `Ctrl+C` or:
```bash
pkill -f main.py
```

---

## 🐛 Troubleshooting

### Issue: "Hailo device not detected"

**Solution:**
```bash
# Check if HAT is properly connected
lspci | grep Hailo

# Should show something like:
# 0000:01:00.0 Co-processor: Hailo Technologies Ltd. Hailo-8 AI Processor

# If nothing shows:
sudo reboot

# After reboot, test again
hailortcli fw-control identify
```

### Issue: "Camera not found"

**Solution for Pi Camera:**
```bash
# Check camera detection
libcamera-hello --list-cameras

# Should show camera detected

# If not, enable in raspi-config
sudo raspi-config
# Interface Options → Camera → Enable
```

**Solution for USB Camera:**
```bash
# List video devices
ls -l /dev/video*

# Test device
v4l2-ctl --list-devices

# Use the correct /dev/videoX in config
```

### Issue: Low FPS / Stuttering

**Possible causes:**
1. **CPU thermal throttling**
   ```bash
   vcgencmd measure_temp
   # Should be < 80°C
   # Add heatsink/fan if too hot
   ```

2. **Power supply insufficient**
   - Use official Pi 5 power supply (5V 5A)
   - Check for undervoltage warnings: `vcgencmd get_throttled`

3. **Wrong camera resolution**
   - Use 640x480 or 1280x720
   - Higher resolutions may reduce FPS

### Issue: "hailortcli: command not found"

**Solution:**
```bash
# Hailo software not installed
sudo apt update
sudo apt install hailo-all
```

### Issue: Detection not counting correctly

**Solutions:**

1. **Adjust counting line position**
   - Edit `config/settings.yaml`
   - Change `counting_line_y` to match doorway

2. **Fix entry direction**
   - Watch people entering
   - Set `entry_direction` correctly ('up' or 'down')

3. **Adjust tracking parameters**
   ```yaml
   counting:
     max_disappeared: 30  # Increase if people disappear too quickly
     max_distance: 50     # Increase if tracking jumps between people
   ```

### Issue: Database errors

**Solution:**
```bash
# Reset database
rm data/occupancy.db

# Restart system - will recreate DB
python3 main.py
```

---

## 📊 Understanding the System

### How It Works

```
┌─────────────┐
│   Camera    │ Captures video at 30 FPS
└──────┬──────┘
       │
┌──────▼──────────┐
│  Hailo AI HAT   │ Detects people in each frame (30+ FPS)
│   (YOLO model)  │ CPU usage: < 10%
└──────┬──────────┘
       │
┌──────▼──────────┐
│ Centroid        │ Tracks each person across frames
│ Tracker         │ Assigns unique IDs
└──────┬──────────┘
       │
┌──────▼──────────┐
│ Line Crossing   │ Detects when someone crosses counting line
│ Detection       │ Determines entry vs exit
└──────┬──────────┘
       │
┌──────▼──────────┐
│ Occupancy       │ Maintains current count
│ Tracker         │ Stores to database
└─────────────────┘
```

### Key Concepts

**1. Detection (Hailo HAT)**
- Runs YOLO neural network at 30+ FPS
- Outputs bounding box for each person: (x, y, width, height)
- Confidence score: how sure the model is (0.0 to 1.0)

**2. Tracking (Centroid Tracker)**
- Follows center point of each person frame-to-frame
- Assigns unique ID to each person
- Removes IDs when person leaves frame

**3. Counting (Line Crossing)**
- Virtual horizontal line in frame
- When person crosses line:
  - Direction determines entry vs exit
  - Updates occupancy count
  - Stores event to database

**4. Storage (SQLite)**
- Snapshots: State every 60 seconds
- Events: Each entry/exit individually
- Sessions: Track when system starts/stops

---

## 📈 Next Steps

After getting people counting working:

1. **Add temperature sensor** (sensors/temperature.py)
2. **Add audio monitoring** (sensors/audio.py)
3. **Add lux sensor** (sensors/light.py)
4. **Add BLE tracking** (sensors/bluetooth.py)
5. **Build web dashboard** for real-time viewing

Each sensor module follows the same pattern:
- Initialize hardware
- Read data in loop
- Store to database
- Integrate with main.py

---

## 💡 Tips

1. **Test with detection.py first** - Make sure basic detection works before running our system
2. **Position camera carefully** - Should have clear view of doorway
3. **Good lighting helps** - Hailo works in various conditions but better with good light
4. **Start simple** - Get counting working, then add other sensors
5. **Monitor logs** - `tail -f logs/bar-monitor.log` shows what's happening

---

## 📚 Additional Resources

- [Hailo Official Documentation](https://hailo.ai/developer-zone/)
- [Hailo Community Forum](https://community.hailo.ai/)
- [hailo-rpi5-examples GitHub](https://github.com/hailo-ai/hailo-rpi5-examples)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)

---

## ❓ Need Help?

If you encounter issues:

1. Run `python3 test_hailo.py` to diagnose
2. Check logs in `logs/bar-monitor.log`
3. Verify config in `config/settings.yaml`
4. Test basic detection with official examples first

---

**Good luck with your bar monitoring system!** 🍺📊
