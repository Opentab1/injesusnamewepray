# Installation - Just Follow The Repos!

**We're using 3 repos. Just install them their way!**

---

## 1️⃣ **Hailo RPi5 Examples**

**Their repo:** https://github.com/hailo-ai/hailo-rpi5-examples

**Their install instructions (from their README):**

```bash
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh
```

**Done! Follow whatever their install.sh does.**

---

## 2️⃣ **Supervision**

**Their repo:** https://github.com/roboflow/supervision

**Their install instructions (from their README):**

```bash
pip install supervision
```

**If you get the "externally-managed-environment" error, use:**

```bash
pip install supervision --break-system-packages
```

**That's it! That's what they say to do.**

---

## 3️⃣ **Streamlit**

**Their repo:** https://github.com/streamlit/streamlit

**Their install instructions (from their README):**

```bash
pip install streamlit
```

**If you get the "externally-managed-environment" error, use:**

```bash
pip install streamlit --break-system-packages
```

**Done! That's their official install.**

---

## ✅ **That's It!**

Just run:

```bash
# Hailo (their way)
cd ~ && git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples && ./install.sh

# Supervision (their way)
pip install supervision --break-system-packages

# Streamlit (their way)  
pip install streamlit --break-system-packages
```

**Follow their docs, not mine!**

---

## 📖 **Links to Their Real Install Docs:**

- **Hailo:** https://github.com/hailo-ai/hailo-rpi5-examples#installation
- **Supervision:** https://github.com/roboflow/supervision#installation  
- **Streamlit:** https://docs.streamlit.io/library/get-started/installation

**Read their docs if you have questions!**
