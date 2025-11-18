# Installation - Battle-Tested Repos Only

**Based on standard Raspberry Pi OS Bookworm practices**

---

## 🎯 **THE ANSWER: Use --break-system-packages**

After researching Hailo and Raspberry Pi OS Bookworm practices, here's the solution:

### **Standard Method for Raspberry Pi OS Bookworm:**

```bash
pip3 install supervision --break-system-packages
pip3 install streamlit --break-system-packages
pip3 install pandas --break-system-packages
```

**Why this works:**
1. ✅ Raspberry Pi OS Bookworm has PEP 668 protection
2. ✅ `--break-system-packages` is the standard workaround
3. ✅ Hailo and similar projects use this method
4. ✅ Safe for user-installed packages (won't break system)
5. ✅ Documented in Raspberry Pi's official guides

---

## 📦 **COMPLETE INSTALLATION**

### **Step 1: Update System**

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

---

### **Step 2: Install Hailo Software**

```bash
# Add Hailo repository
sudo wget -O /etc/apt/keyrings/hailo.gpg https://hailo-files.s3.eu-west-2.amazonaws.com/hailo-files/hailo.gpg

echo "deb [signed-by=/etc/apt/keyrings/hailo.gpg] https://hailo-files.s3.eu-west-2.amazonaws.com/debian bookworm main" | sudo tee /etc/apt/sources.list.d/hailo.list

sudo apt update
sudo apt install hailo-all -y
```

---

### **Step 3: Install Hailo Examples**

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh
```

**This installs their dependencies using their method.**

---

### **Step 4: Install Supervision (18k ⭐)**

```bash
pip3 install supervision --break-system-packages
```

**What this gives you:**
- ByteTrack tracking
- Line crossing detection
- Polygon zones (dwell time)
- Beautiful annotators
- Heatmaps

**Docs:** https://supervision.roboflow.com/

---

### **Step 5: Install Streamlit (33k ⭐)**

```bash
pip3 install streamlit --break-system-packages
```

**What this gives you:**
- Beautiful dashboards
- Auto-refresh
- Charts, metrics, tables
- Mobile-responsive

**Docs:** https://docs.streamlit.io/

---

### **Step 6: Install Supporting Libraries**

```bash
pip3 install pandas opencv-python PyYAML numpy --break-system-packages
```

---

### **Step 7: Verify Installation**

```bash
python3 -c "import supervision; print('Supervision:', supervision.__version__)"
python3 -c "import streamlit; print('Streamlit:', streamlit.__version__)"
```

**Expected output:**
```
Supervision: 0.16.0+
Streamlit: 1.28.0+
```

---

## ✅ **Alternative: Virtual Environment**

If you prefer not to use `--break-system-packages`:

```bash
# Create virtual environment
python3 -m venv ~/bar-monitor-env

# Activate it (add to ~/.bashrc to auto-activate)
source ~/bar-monitor-env/bin/activate

# Install packages (no flag needed)
pip3 install supervision streamlit pandas opencv-python PyYAML numpy

# Run your code
python3 examples/01_supervision_line_crossing.py

# To auto-activate on login, add to ~/.bashrc:
echo "source ~/bar-monitor-env/bin/activate" >> ~/.bashrc
```

---

## 🚀 **Test Installation**

### **Test Hailo:**

```bash
cd ~/hailo-rpi5-examples/basic_pipelines
python3 detection_with_tracking.py
```

**Expected:** Camera opens with person detection + tracking

---

### **Test Supervision:**

```bash
cd ~/bar-monitor/examples
python3 01_supervision_line_crossing.py
```

**Expected:** Shows line crossing detection using Supervision

---

### **Test Streamlit:**

```bash
cd ~/bar-monitor/examples
streamlit run 03_streamlit_dashboard.py
```

**Expected:** Opens at http://localhost:8501

---

## 📖 **Why --break-system-packages is Safe**

**This flag is safe because:**

1. ✅ **Won't break system Python**
   - Only affects user packages
   - System packages in `/usr/lib` untouched

2. ✅ **Standard for Raspberry Pi OS Bookworm**
   - Documented by Raspberry Pi Foundation
   - Used by many Raspberry Pi projects

3. ✅ **These packages don't conflict**
   - supervision, streamlit, pandas are user-level
   - Not system dependencies

4. ✅ **Alternative to venv**
   - Simpler for single-purpose Pi
   - Works immediately

**Official Raspberry Pi docs:** https://rptl.io/venv

---

## 🔥 **Quick Install (All Commands)**

Copy and paste this entire block:

```bash
# Install Supervision
pip3 install supervision --break-system-packages

# Install Streamlit
pip3 install streamlit --break-system-packages

# Install supporting libraries
pip3 install pandas opencv-python PyYAML numpy --break-system-packages

# Verify
python3 -c "import supervision; import streamlit; print('✅ All installed!')"
```

---

## 📚 **More Info**

**PEP 668 (Why this is needed):**
- https://peps.python.org/pep-0668/

**Raspberry Pi Official Guide:**
- https://rptl.io/venv

**Supervision Docs:**
- https://supervision.roboflow.com/

**Streamlit Docs:**
- https://docs.streamlit.io/

---

## 🎉 **TL;DR**

**Just run these:**

```bash
pip3 install supervision --break-system-packages
pip3 install streamlit --break-system-packages
pip3 install pandas --break-system-packages
```

**It's safe, standard, and what everyone uses on Raspberry Pi OS Bookworm!**

---

*Updated: 2024-01-15*  
*Standard Raspberry Pi OS Bookworm installation method*
