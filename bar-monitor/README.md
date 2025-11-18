# Bar Monitoring System - Raspberry Pi 5 + Hailo AI HAT

## System Overview
This system monitors your bar environment using multiple sensors:
- **People Detection & Counting** (Hailo AI HAT)
- Temperature Monitoring
- Audio: Song Detection & Decibel Levels
- Light Level (Lux) Monitoring
- BLE Device Tracking

## Hardware Requirements
- Raspberry Pi 5
- Hailo AI HAT (AI Kit)
- Pi Camera or USB Camera
- DHT22 Temperature/Humidity Sensor
- USB Microphone
- BH1750 Lux Sensor (I2C)
- Bluetooth capability (built-in Pi 5)

## Project Structure
```
bar-monitor/
├── hailo_integration/     # Hailo HAT people detection code
├── sensors/               # Other sensor modules (temp, audio, lux, BLE)
├── data/                  # Data storage (SQLite database, logs)
├── logs/                  # Application logs
├── config/                # Configuration files
└── main.py               # Main application entry point
```

## Installation Instructions

### 1. Install Hailo Software
```bash
sudo apt update
sudo apt install hailo-all
hailortcli fw-control identify
```

### 2. Clone Hailo Examples
```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh
```

### 3. Install Project Dependencies
```bash
cd /workspace/bar-monitor
pip3 install -r requirements.txt
```

### 4. Run the System
```bash
python3 main.py
```

## Features

### People Counting (Hailo HAT)
- Real-time person detection at 30+ FPS
- Entry/Exit tracking with virtual line crossing detection
- Live occupancy count
- Configurable detection zones

### Temperature Monitoring
- Real-time indoor temperature reading
- DHT22 sensor via GPIO

### Audio Analysis
- Song recognition (Shazam-like)
- Real-time decibel level monitoring
- USB microphone input

### Light Level
- Lux measurement via BH1750 I2C sensor

### BLE Tracking
- Scan for BLE devices (phones, watches)
- Track unique device count as occupancy indicator

## Configuration
Edit `config/settings.yaml` to customize:
- Camera input source
- Detection thresholds
- Entry/Exit line coordinates
- Sensor GPIO pins
- Data logging intervals
