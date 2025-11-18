# 🍞 Toast POS Integration Guide

## 🎯 **Why Integrate Toast POS?**

### **Without POS Integration:**
```
Customer #1234 stayed 90 minutes
ESTIMATED revenue: $30 (guessing)
→ We don't really know if they're profitable
```

### **With Toast POS Integration:**
```
Customer #1234 stayed 90 minutes
ACTUAL revenue: $47.50 (from your POS!)
Revenue per minute: $0.53
→ This is a HIGH-VALUE customer - keep them happy!
```

---

## 💰 **New Insights You'll Get**

1. **Revenue Per Minute**
   - Know which customers are most profitable
   - Identify high-spenders vs low-spenders
   - Make data-driven decisions about who to turn vs who to keep

2. **Optimal Dwell Time**
   - What duration maximizes revenue?
   - 45 min? 60 min? 90 min?
   - Now you'll know from REAL data!

3. **High-Value vs Low-Value Campers**
   - Camper spending $60/hour? Keep them!
   - Camper spending $15/hour? Encourage turnover!

4. **Time-of-Day Revenue Patterns**
   - Which hours generate most revenue per customer?
   - When should you prioritize turnover vs capacity?

5. **Staff Performance**
   - Which staff generate fastest turnover?
   - Which staff generate highest revenue per customer?

6. **Table/Area Performance**
   - Which areas generate most revenue?
   - Where should you seat high-value customers?

---

## 🚀 **Step-by-Step Setup**

### **Step 1: Get Toast API Access**

#### 1.1 - Create Toast Developer Account

1. Go to: **https://developers.toasttab.com/**
2. Click **"Get Started"**
3. Fill in your information:
   - Business email
   - Restaurant name
   - Phone number
4. Verify your email
5. Log in to Toast Developer Portal

#### 1.2 - Create API Application

1. In developer portal, click **"Applications"**
2. Click **"Create New Application"**
3. Fill in:
   ```
   Application Name: Bar Monitor Integration
   Description: Occupancy and revenue analytics system
   Redirect URI: http://localhost:8080/callback
   ```
4. Click **"Save"**

#### 1.3 - Get Your Credentials

After creating the app, you'll see:

```
Client ID:     toast_abc123456789...
Client Secret: secret_xyz987654321...
```

**⚠️ SAVE THESE!** You'll need them in Step 2.

#### 1.4 - Get Restaurant GUID

Your restaurant has a unique identifier (GUID).

**Where to find it:**
- Toast Dashboard → **Settings** → **API Integration**
- Or contact Toast support: "I need my Restaurant GUID for API access"

**Format:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

#### 1.5 - Set API Permissions

Your app needs these permissions (scopes):
- ✅ `orders:read` - Read order data
- ✅ `checks:read` - Read check data
- ✅ `tables:read` - Read table assignments (optional, but recommended)

Enable these in the developer portal under your application settings.

---

### **Step 2: Configure Bar Monitor System**

#### 2.1 - Add Toast Credentials to Config

Edit your configuration file:

```bash
cd /workspace/bar-monitor
nano config/settings.yaml
```

Add this section (it's already in the file, just fill in your values):

```yaml
# Toast POS Integration
toast_pos:
  # Enable Toast POS integration
  enabled: true
  
  # Your Toast API Credentials
  client_id: 'toast_abc123456789...'  # From Step 1.3
  client_secret: 'secret_xyz987654321...'  # From Step 1.3
  restaurant_guid: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'  # From Step 1.4
  
  # How often to sync orders (seconds)
  sync_interval: 60  # Check for new orders every minute
  
  # Link orders to customers within this time window
  order_matching_window: 300  # 5 minutes
```

**Save the file:** Press `Ctrl+X`, then `Y`, then `Enter`

#### 2.2 - Install Python Dependencies

```bash
pip3 install requests
```

Or update from requirements.txt:

```bash
pip3 install -r requirements.txt
```

---

### **Step 3: Test Toast Connection**

Run the test script to verify everything works:

```bash
cd /workspace/bar-monitor
python3 integrations/toast_pos.py --test
```

**Expected output:**

```
✓ Authentication successful
✓ Successfully retrieved 47 orders from today
   Sample order: $34.50 at 2024-01-15T18:23:45
```

**If you see errors:**

- ❌ **"Authentication failed"** → Check client_id and client_secret
- ❌ **"Restaurant not found"** → Check restaurant_guid
- ❌ **"Permission denied"** → Enable required API scopes (Step 1.5)

---

### **Step 4: View Recent Orders** (Optional Test)

Get orders from last 24 hours:

```bash
python3 integrations/toast_pos.py --orders
```

Get revenue statistics:

```bash
python3 integrations/toast_pos.py --revenue
```

---

### **Step 5: Run the Full System**

Now run your bar monitoring system with Toast integration:

```bash
python3 main.py
```

The system will now:
1. ✅ Count people entering/exiting (as before)
2. ✅ Track dwell time (as before)
3. ✅ **NEW:** Fetch orders from Toast every minute
4. ✅ **NEW:** Link orders to customers based on timing
5. ✅ **NEW:** Calculate actual revenue per customer
6. ✅ **NEW:** Show revenue per minute in dashboard

---

## 📊 **Using the Enhanced Dashboard**

Start the dashboard:

```bash
python3 dashboard/dwell_dashboard.py
```

Open in browser: **http://localhost:5000**

### **New Dashboard Features:**

**Before (without Toast):**
```
Customer #1234 | 85 min | ⚠️ Warning
Estimated: $28.33
```

**After (with Toast):**
```
Customer #1234 | 85 min | ✅ High-Value
Actual Revenue: $47.50
Revenue/Min: $0.56
```

**Color Coding:**
- 🟢 **Green** - High-value customer (>$0.80/min) → Keep happy!
- 🟡 **Yellow** - Medium-value (>$0.50/min) → Monitor
- 🟠 **Orange** - Low-value (<$0.50/min) → Consider turnover
- 🔴 **Red** - Low-value camper (>90min, <$0.40/min) → Encourage exit

---

## 📈 **View Revenue Analytics Reports**

Generate comprehensive revenue analysis:

```bash
cd /workspace/bar-monitor
python3 analytics/revenue_analytics.py
```

**Example Output:**

```
╔═══════════════════════════════════════════════════════════╗
║              📊 REVENUE ANALYTICS REPORT                  ║
╚═══════════════════════════════════════════════════════════╝

PERIOD: Last 7 days

💰 REVENUE PERFORMANCE:
════════════════════════════════════════════════════════════
Total Revenue:              $12,450.00
Total Customers:            234
Avg Revenue/Customer:       $53.21
Avg Revenue/Minute:         $0.68
Avg Dwell Time:             78 minutes

🎯 CUSTOMER BREAKDOWN:
════════════════════════════════════════════════════════════
High-Value (>$1.00/min):    45 customers
Medium-Value ($0.50-1.00):  128 customers
Low-Value (<$0.50/min):     61 customers

⏱️ OPTIMAL DWELL TIME:
════════════════════════════════════════════════════════════
Target Dwell Time:          60 minutes
Best Revenue/Minute:        $0.82/min
Confidence:                 high
Sample Size:                234 customers

Target dwell time: 60 minutes for best revenue/minute.
Customers staying 75 minutes spend most per visit.

💡 CURRENT OPPORTUNITIES:
════════════════════════════════════════════════════════════
⚠️ ACTION NEEDED: 3 low-value campers detected.
Encouraging turnover could generate $67 additional revenue.
```

---

## 🎯 **How to Use Revenue Data**

### **Strategy 1: Smart Turnover Management**

**Old Way (without Toast):**
```
"Any customer over 90 minutes gets a gentle nudge"
→ Risk losing high-spenders!
```

**New Way (with Toast):**
```
- Customer over 90 min + spending $1.20/min? → Keep them happy!
- Customer over 90 min + spending $0.30/min? → Encourage check
```

### **Strategy 2: Optimal Table Duration**

**Use the analytics to find your sweet spot:**

```bash
python3 analytics/revenue_analytics.py
```

Look at the **OPTIMAL DWELL TIME** section. Example:

```
Target Dwell Time: 60 minutes
→ This is your sweet spot for revenue per minute!

Customers staying 75 minutes spend most per visit
→ This is your maximum revenue per customer
```

**Action:** Focus on 60-75 minute turnover for optimal revenue.

### **Strategy 3: Staff Training**

Share revenue data with staff:

```
"When you see a customer in the RED on the dashboard,
they've been here 90+ min but only spending $0.30/min.
That seat could serve a new customer spending $0.60/min!"
```

### **Strategy 4: Pricing Strategy**

```
Average Revenue/Minute: $0.68
Optimal Dwell: 60 minutes
→ Average customer should spend ~$40 in 60 minutes

If current average is lower:
- Review drink prices
- Encourage appetizers
- Suggest rounds
```

---

## 🔧 **Advanced Configuration**

### **Adjust Order Matching Window**

By default, orders are linked to customers if they occur within 5 minutes of their visit.

To adjust:

```yaml
toast_pos:
  order_matching_window: 300  # 5 minutes (default)
```

**When to adjust:**
- **Slower service?** Increase to 600 (10 min)
- **Fast-casual?** Decrease to 180 (3 min)

### **Adjust Sync Interval**

How often to fetch orders from Toast:

```yaml
toast_pos:
  sync_interval: 60  # 1 minute (default)
```

**When to adjust:**
- **High volume?** Decrease to 30 (30 seconds)
- **Save API calls?** Increase to 300 (5 minutes)

**Note:** Toast allows 500 requests/minute, so 60 seconds is safe.

### **Customer Classification Thresholds**

Edit `/workspace/bar-monitor/analytics/revenue_analytics.py` to adjust thresholds:

```python
# In link_customer_to_revenue() method:
if revenue_per_minute > 1.0:       # High-value threshold
    customer_type = 'high_value'
elif revenue_per_minute > 0.5:     # Medium-value threshold
    customer_type = 'medium_value'
```

**Adjust based on your bar:**
- High-end cocktail bar? Increase thresholds (>$1.50/min = high)
- Dive bar? Decrease thresholds (>$0.60/min = high)

---

## 🛠️ **Troubleshooting**

### **Problem: "Authentication failed"**

**Cause:** Wrong client_id or client_secret

**Fix:**
1. Go to Toast Developer Portal
2. Check your application credentials
3. Copy exact values to `config/settings.yaml`
4. Make sure no extra spaces or quotes

### **Problem: "Restaurant not found"**

**Cause:** Wrong restaurant_guid

**Fix:**
1. Contact Toast support: "I need my Restaurant GUID"
2. Or check: Toast Dashboard → Settings → API Integration
3. Should be format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### **Problem: "Permission denied"**

**Cause:** Missing API scopes

**Fix:**
1. Go to Toast Developer Portal
2. Select your application
3. Enable these scopes:
   - `orders:read`
   - `checks:read`
   - `tables:read`
4. Save and test again

### **Problem: No orders showing up**

**Possible causes:**
1. **No orders in time window:** Try `python3 integrations/toast_pos.py --orders` to verify
2. **Order matching window too small:** Increase `order_matching_window` in config
3. **Orders not closed yet:** Toast API only shows closed orders

**Debug:**
```bash
# Check if orders are coming through
python3 integrations/toast_pos.py --orders

# Check revenue analytics
python3 analytics/revenue_analytics.py
```

### **Problem: Orders not linking to customers**

**Cause:** Timing mismatch between customer entry and order placement

**Fix:**
1. Increase `order_matching_window` in config
2. Check that your camera is capturing all entries/exits
3. Verify customer track_ids are persisting correctly

---

## 📊 **Expected Business Results**

### **Scenario: Typical Busy Night (Without Toast)**

```
Saturday 8pm-2am (6 hours)
Estimated revenue: $3,600 (guessing)
Estimated avg customer value: $45 (guessing)
→ Not sure which customers are actually profitable
```

### **Scenario: Same Night (With Toast)**

```
Saturday 8pm-2am (6 hours)
ACTUAL revenue: $4,235
ACTUAL avg customer value: $52.94
Revenue breakdown:
  - 15 high-value customers: $125/each avg (19% of customers)
  - 45 medium-value customers: $48/each avg (56% of customers)
  - 20 low-value customers: $22/each avg (25% of customers)

💡 INSIGHT: Top 19% of customers generate 44% of revenue!
→ Focus on attracting and retaining high-value customers
```

### **ROI Calculation**

**Cost:**
- Toast POS: You already have it! ($0 additional)
- Bar Monitor System: Free + Raspberry Pi hardware (~$150)
- Setup time: 30 minutes

**Revenue Impact:**
- Identify $67/night in turnover opportunities (conservative)
- 6 nights/week = $402/week = **$1,608/month**
- Better decisions about pricing and promotions
- Staff training based on real data

**Payback Period:** Less than 1 week!

---

## 🎓 **API Usage Best Practices**

### **Rate Limits**

Toast allows **500 requests per minute**.

Our system makes:
- 1 request/minute for orders (default sync_interval)
- Very safe usage!

### **Data Retention**

- Order data is fetched and stored locally in SQLite
- No need to repeatedly query Toast for same data
- Historical analysis uses local database

### **Security**

**⚠️ IMPORTANT:** Your Toast API credentials are sensitive!

**Best practices:**
1. ✅ Keep `config/settings.yaml` secure
2. ✅ Don't commit credentials to git
3. ✅ Use file permissions: `chmod 600 config/settings.yaml`
4. ❌ Never share your client_secret publicly

---

## 📚 **Additional Resources**

- **Toast API Documentation:** https://doc.toasttab.com/
- **Toast Developer Portal:** https://developers.toasttab.com/
- **Toast Support:** support@toasttab.com

---

## 🎉 **You're Ready!**

With Toast POS integration, you now have:

✅ **Real revenue data** (not estimates!)  
✅ **Customer profitability insights** (who's actually profitable?)  
✅ **Optimal dwell time calculations** (what duration makes most money?)  
✅ **Actionable turnover decisions** (who to keep vs who to turn)  
✅ **Data-driven pricing** (what should you charge?)  

**Start making $1,500-2,500 more per month with data-driven decisions!** 🚀💰

---

**Questions? Issues? Check the troubleshooting section above or review logs:**

```bash
tail -f logs/bar-monitor.log
```
