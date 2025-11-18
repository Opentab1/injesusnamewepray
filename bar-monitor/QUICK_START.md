# ⚡ Quick Start Guide - Get Running in 10 Minutes

## 🎯 Goal
Get your Hailo HAT people counting system up and running FAST.

---

## ✅ Pre-Flight Checklist

Before starting, make sure you have:
- [x] Raspberry Pi 5
- [x] Hailo AI HAT physically installed on GPIO pins
- [x] Pi Camera or USB webcam connected
- [x] Fresh Raspberry Pi OS installed
- [x] Internet connection

---

## 🚀 Installation (5 minutes)

### Step 1: Install Hailo Software

```bash
sudo apt update
sudo apt install -y hailo-all
```

**Verify it worked:**
```bash
hailortcli fw-control identify
```

Should show: `Board Name: Hailo-8` or `Hailo-8L`

---

### Step 2: Install Official Examples

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh
```

This takes ~5 minutes. Be patient!

---

### Step 3: Test Basic Detection

```bash
source setup_env.sh
python basic_pipelines/detection.py --input rpi
```

**You should see:**
- Live video feed
- Bounding boxes around people
- FPS counter showing 30+ FPS

Press `Ctrl+C` to stop.

**✅ If this works, your Hailo HAT is ready!**

---

### Step 4: Install Bar Monitor System

```bash
cd /workspace/bar-monitor
pip3 install -r requirements.txt
```

---

## ⚙️ Configuration (2 minutes)

Edit the config file:

```bash
nano config/settings.yaml
```

**CRITICAL: Set these 3 values:**

```yaml
camera:
  source: 'rpi'  # or 'usb' if using USB camera

counting:
  counting_line_y: 240  # Y-position of doorway (see below)
  entry_direction: 'down'  # or 'up' (see below)
```

### How to Find `counting_line_y`:

1. Look at your detection video from Step 3
2. Note where your doorway is vertically in the frame
3. Frame is 480 pixels tall:
   - Top of frame: y = 0
   - Middle: y = 240
   - Bottom: y = 480
4. Set `counting_line_y` to doorway position

**Examples:**
- Doorway in middle: `counting_line_y: 240`
- Doorway near bottom: `counting_line_y: 400`
- Doorway near top: `counting_line_y: 100`

### How to Find `entry_direction`:

Watch someone walk into the frame:
- If they move **downward** when entering: `entry_direction: 'down'`
- If they move **upward** when entering: `entry_direction: 'up'`

---

## 🧪 Testing (1 minute)

Run the test script:

```bash
python3 test_hailo.py
```

**Expected output:**
```
✓ Hailo Device ................ PASS
✓ Hailo Examples .............. PASS
✓ Camera ...................... PASS
✓ Python Packages ............. PASS
✓ GStreamer ................... PASS

All tests passed!
```

If any test fails, see `SETUP_GUIDE.md` for troubleshooting.

---

## 🎬 Run the System (30 seconds)

Start the bar monitor:

```bash
python3 main.py
```

**You should see:**

```
╔═══════════════════════════════════════════════════════════╗
║            BAR MONITORING SYSTEM v1.0                     ║
╚═══════════════════════════════════════════════════════════╝

Initializing components...
1. Initializing Hailo HAT... ✓
2. Initializing Entry/Exit Counter... ✓
3. Initializing Occupancy Tracker... ✓

System started successfully!

Monitoring Status:
  Camera: rpi
  Model: yolov6n
  Counting Line: Y=240px
  Database: data/occupancy.db

Press Ctrl+C to stop
──────────────────────────────────────────────────────────

Current Status [21:30:45]
  Occupancy: 0 people
  Total Entries: 0
  Total Exits: 0
  Active Tracks: 0
  Peak Today: 0 people
```

**🎉 IT'S WORKING!**

---

## 🧪 Test Counting

Walk through the doorway:

1. **Walk into view** (entering)
   - Watch the occupancy count increase
   - Log shows: "Entry detected"

2. **Walk out of view** (exiting)
   - Watch the occupancy count decrease
   - Log shows: "Exit detected"

---

## 📊 View Your Data

### Check Logs

```bash
tail -f logs/bar-monitor.log
```

### Query Database

```bash
sqlite3 data/occupancy.db

# Get current occupancy
SELECT current_occupancy FROM snapshots ORDER BY timestamp DESC LIMIT 1;

# Get today's entries
SELECT COUNT(*) FROM events WHERE event_type='entry' AND DATE(timestamp)=DATE('now');

# Exit database
.quit
```

---

## 🐛 Troubleshooting

### Problem: "Hailo device not detected"

```bash
# Reboot and retry
sudo reboot
# After reboot:
hailortcli fw-control identify
```

### Problem: "Camera not found"

**For Pi Camera:**
```bash
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

**For USB Camera:**
```bash
ls /dev/video*
# Use the device shown in config: source: '/dev/video0'
```

### Problem: "No people detected"

1. Check camera angle - should see doorway clearly
2. Add more lighting
3. Lower confidence in config: `confidence_threshold: 0.3`

### Problem: "Wrong counts"

1. Adjust `counting_line_y` - should be AT doorway threshold
2. Fix `entry_direction` - watch which way people move
3. Test with slow, deliberate walks first

---

## 📞 Get Help

1. **Read the docs:**
   - `SETUP_GUIDE.md` - Full installation guide
   - `PROJECT_OVERVIEW.md` - How everything works
   - `WHAT_I_BUILT.md` - Complete explanation

2. **Run diagnostics:**
   ```bash
   python3 test_hailo.py
   ```

3. **Check logs:**
   ```bash
   cat logs/bar-monitor.log
   ```

---

## 🎯 Success Checklist

- [ ] Hailo device detected
- [ ] Camera working
- [ ] Detection showing 30+ FPS
- [ ] `test_hailo.py` passes
- [ ] Config file edited
- [ ] `main.py` running
- [ ] Walking through doorway changes count
- [ ] Database file created
- [ ] Logs updating

---

## 🚀 What's Next?

Once counting works reliably:

1. **Add more sensors:**
   - Temperature (DHT22)
   - Audio/song detection
   - Decibel meter
   - Light sensor (BH1750)
   - BLE tracking

2. **Build dashboard:**
   - Web interface
   - Real-time graphs
   - Historical data

3. **Optimize:**
   - Fine-tune counting line
   - Adjust tracking parameters
   - Test different models

---

## 💡 Pro Tips

1. **Test with official examples first** - Makes sure Hailo works
2. **Configure counting line carefully** - Most common issue
3. **Start with good lighting** - Easier detection
4. **Walk slowly through doorway** - Better tracking
5. **Monitor logs** - See what's happening

---

## 📋 Command Cheat Sheet

```bash
# Test Hailo
hailortcli fw-control identify

# Test detection
cd ~/hailo-rpi5-examples
source setup_env.sh
python basic_pipelines/detection.py --input rpi

# Run bar monitor
cd /workspace/bar-monitor
python3 main.py

# Test installation
python3 test_hailo.py

# View logs
tail -f logs/bar-monitor.log

# Query database
sqlite3 data/occupancy.db
```

---

**That's it! You should now have a working people counting system.** 🎉

If you followed all steps and it's working, congratulations! You have professional-grade occupancy tracking running on your Raspberry Pi.

**Questions?** Read `SETUP_GUIDE.md` or `WHAT_I_BUILT.md` for more details.
