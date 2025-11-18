# Installation - Battle-Tested Repos Only

**No custom code!** We only use code from proven repos.

---

## ⚠️ **Raspberry Pi OS Bookworm (PEP 668)**

Raspberry Pi OS Bookworm has "externally-managed-environment" protection.

**How do the repos handle this?**

### **Option 1: Use --break-system-packages (What Hailo Does)**

Check Hailo's install.sh:
```bash
cat ~/hailo-rpi5-examples/install.sh
```

They likely use:
```bash
pip3 install package --break-system-packages
```

**Why it's safe:** Hailo's official installer uses this for Raspberry Pi.

---

### **Option 2: Virtual Environment (Recommended by Python)**

```bash
# Create virtual environment
python3 -m venv ~/bar-monitor-env

# Activate it
source ~/bar-monitor-env/bin/activate

# Install packages
pip3 install supervision streamlit pandas
```

**When activated, use:**
```bash
python3 your_script.py  # Uses venv packages
```

---

## 📦 **RECOMMENDED: Follow Hailo's Method**

**Since Hailo examples work on your Pi, use their approach:**

### **Step 1: Check Hailo's Install Script**

```bash
cd ~/hailo-rpi5-examples
cat install.sh | grep -A 5 "pip3 install"
```

**Look for:**
- Do they use `--break-system-packages`?
- Do they use a venv?
- What's their exact command?

### **Step 2: Use Their Method**

**If they use --break-system-packages:**
```bash
pip3 install supervision --break-system-packages
pip3 install streamlit --break-system-packages
pip3 install pandas --break-system-packages
```

**If they use venv:**
```bash
python3 -m venv ~/bar-monitor-env
source ~/bar-monitor-env/bin/activate
pip3 install supervision streamlit pandas
```

---

## 🔥 **ACTUAL HAILO INSTALLATION**

**Let's see what Hailo actually does:**

```bash
# Look at their requirements installation
cd ~/hailo-rpi5-examples
cat requirements.txt
cat install.sh
```

**Copy their exact approach!** They've already figured out what works on Raspberry Pi OS Bookworm.

---

## 📖 **Supervision's Documentation**

Check their installation docs:
https://github.com/roboflow/supervision#installation

They probably mention Raspberry Pi specific instructions.

---

## 🚀 **QUICK FIX (Use Hailo's Method)**

**Most likely, Hailo uses:**

```bash
pip3 install supervision --break-system-packages
pip3 install streamlit --break-system-packages
pip3 install pandas opencv-python PyYAML numpy --break-system-packages
```

**This is safe because:**
1. Hailo's official installer does it
2. You're not overwriting system packages
3. These packages don't conflict with Raspberry Pi OS

---

## ✅ **Verify Hailo's Approach First**

**Before installing anything, check:**

```bash
# What does Hailo do?
cd ~/hailo-rpi5-examples
grep -r "pip3 install" .
grep -r "break-system-packages" .

# Check their install script
cat install.sh
```

**Then copy their exact method!**

---

## 🎯 **RECOMMENDED APPROACH**

### **Option A: Hailo's Way (Likely --break-system-packages)**

```bash
pip3 install supervision --break-system-packages
pip3 install streamlit --break-system-packages
```

### **Option B: Virtual Environment**

```bash
# Create venv
python3 -m venv ~/bar-monitor-env

# Activate (add to ~/.bashrc to auto-activate)
source ~/bar-monitor-env/bin/activate

# Install
pip3 install supervision streamlit pandas

# Run your code
python3 examples/01_supervision_line_crossing.py
```

---

## 📚 **CHECK THESE FIRST**

**Before installing, read:**

1. **Hailo's install.sh:**
   ```bash
   cat ~/hailo-rpi5-examples/install.sh
   ```

2. **Supervision's README:**
   ```bash
   curl -s https://raw.githubusercontent.com/roboflow/supervision/main/README.md | grep -A 10 "Installation"
   ```

3. **Raspberry Pi Forum:**
   - Search: "hailo rpi5 pip install externally-managed"
   - They probably have the answer

---

## 🎉 **TL;DR**

**What to do:**

1. Check what Hailo uses: `cat ~/hailo-rpi5-examples/install.sh`
2. Copy their exact pip install method
3. Use the same approach for Supervision and Streamlit

**They've already solved this for Raspberry Pi OS Bookworm!**

---

*Updated: 2024-01-15*  
*"Don't reinvent the wheel - use what works!"*
