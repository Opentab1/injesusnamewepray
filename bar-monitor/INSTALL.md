# Installation - Battle-Tested Repos Only

**No custom code!** We only use code from proven repos.

---

## 📦 **Step 1: Install Hailo (Official)**

```bash
# Add Hailo repository
sudo wget -O /etc/apt/keyrings/hailo.gpg https://hailo-files.s3.eu-west-2.amazonaws.com/hailo-files/hailo.gpg
echo "deb [signed-by=/etc/apt/keyrings/hailo.gpg] https://hailo-files.s3.eu-west-2.amazonaws.com/debian bookworm main" | sudo tee /etc/apt/sources.list.d/hailo.list
sudo apt update && sudo apt install hailo-all -y
```

---

## 📦 **Step 2: Install Hailo Examples (Official)**

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh
```

**This is their official code! Use it!**

---

## 📦 **Step 3: Install Supervision (18k ⭐)**

```bash
pip3 install supervision
```

**Documentation:** https://supervision.roboflow.com/

---

## 📦 **Step 4: Install Streamlit (33k ⭐)**

```bash
pip3 install streamlit
```

**Documentation:** https://docs.streamlit.io/

---

## 📦 **Step 5: Install Supporting Libraries**

```bash
pip3 install pandas opencv-python PyYAML numpy
```

---

## 🚀 **Step 6: Test Hailo**

```bash
cd ~/hailo-rpi5-examples/basic_pipelines
python3 detection_with_tracking.py
```

**Expected:** Camera opens, people detected with track IDs

**This is the code to use!** Don't rewrite it.

---

## 🚀 **Step 7: Test Supervision**

```bash
cd ~/bar-monitor/examples
python3 01_supervision_line_crossing.py
```

**This shows how to add line crossing to Hailo's detection.**

---

## 🚀 **Step 8: Test Streamlit**

```bash
cd ~/bar-monitor/examples
streamlit run 03_streamlit_dashboard.py
```

**Opens at:** http://localhost:8501

---

## ✅ **You're Done!**

You now have:
- ✅ Hailo detection (official code)
- ✅ Supervision tracking & counting (18k stars)
- ✅ Streamlit dashboard (33k stars)

**All battle-tested code! No custom code!**

---

## 🔗 **Next Steps**

1. Copy Hailo's `detection_with_tracking.py`
2. Add Supervision line crossing (see examples)
3. Store data in SQLite (standard Python library)
4. Build Streamlit dashboard (see examples)

**Use code from the repos! Don't reinvent!**
