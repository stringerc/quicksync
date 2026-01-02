# UptimeRobot Health Check Monitoring Setup

**Purpose:** Monitor site uptime and get alerts when the site is down  
**Time Required:** 10 minutes  
**Cost:** Free (50 monitors on free plan)

---

## 📋 Setup Steps

### Step 1: Sign Up for UptimeRobot

1. **Go to UptimeRobot:**
   - Visit: https://uptimerobot.com/
   - Click "Sign Up" (top right)

2. **Create Account:**
   - Enter email address
   - Create password
   - Verify email (check your inbox)

3. **Login:**
   - Go to: https://uptimerobot.com/dashboard

---

### Step 2: Add Monitor

1. **Click "Add New Monitor":**
   - Button at top of dashboard

2. **Monitor Configuration:**
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** `QuickSync - Production`
   - **URL (or IP):** `https://quicksync.app/api/health`
   - **Monitoring Interval:** 5 minutes (free plan minimum)
   - **Alert Contacts:** Select your email (or add it first)

3. **Advanced Settings (Optional):**
   - **Alert When Down For:** 1 interval (5 minutes)
   - **Alert When Up Again:** Yes
   - **Ignore SSL Certificate Errors:** No (leave unchecked)

4. **Click "Create Monitor"**

---

### Step 3: Verify Monitor

1. **Check Monitor Status:**
   - Should show "Up" with green status
   - Last checked timestamp should be recent

2. **Test Alert (Optional):**
   - You can temporarily stop your Vercel deployment
   - Wait 5-10 minutes
   - Should receive email alert
   - Restart deployment
   - Should receive "back up" email

---

### Step 4: Add Additional Monitors (Optional)

You can add more monitors for:

1. **Homepage:**
   - URL: `https://quicksync.app`
   - Type: HTTP(s)

2. **Blog:**
   - URL: `https://quicksync.app/blog`
   - Type: HTTP(s)

3. **API Health (already done):**
   - URL: `https://quicksync.app/api/health`
   - Type: HTTP(s)

**Note:** Free plan includes 50 monitors, so you have plenty of room.

---

## 🔔 Alert Configuration

### Email Alerts (Default)

- ✅ Automatically enabled when you add monitor
- ✅ Alerts sent to your registered email
- ✅ Alerts for: Site down, Site back up

### SMS Alerts (Optional - Requires Credits)

1. **Go to:** My Settings → Alert Contacts
2. **Add SMS Contact:**
   - Click "Add New Alert Contact"
   - Select "SMS"
   - Enter phone number
   - Verify (will receive code)

3. **Assign to Monitor:**
   - Edit monitor
   - Select SMS contact in "Alert Contacts"

**Note:** SMS requires credits (purchased), but email is free.

---

## 📊 Monitoring Dashboard

**What You'll See:**

- ✅ **Status:** Up/Down (with color coding)
- ✅ **Uptime:** Percentage (99.9%, etc.)
- ✅ **Response Time:** Average response time
- ✅ **Last Checked:** Timestamp of last check
- ✅ **History:** Chart showing uptime over time

---

## 🎯 Health Check Endpoint

**Endpoint:** `https://quicksync.app/api/health`

**Response:**
```json
{
  "ok": true,
  "timestamp": "2025-01-02T12:00:00.000Z",
  "version": "abc123",
  "environment": "production"
}
```

**Status Codes:**
- `200` = Site is up and healthy
- `500` = Site has an error (will trigger alert)

---

## 📧 What Alerts You'll Get

1. **Site Down Alert:**
   - When health endpoint returns non-200 status
   - Or when endpoint is unreachable
   - Sent after 5 minutes of downtime

2. **Site Back Up Alert:**
   - When site recovers after being down
   - Confirms site is operational again

---

## ⚙️ Recommended Settings

**For Production:**
- ✅ **Monitoring Interval:** 5 minutes (minimum on free plan)
- ✅ **Alert Threshold:** 1 interval (get notified quickly)
- ✅ **Alert Contacts:** Your primary email
- ✅ **SSL Verification:** Enabled (default)

---

## 🔍 Troubleshooting

### Monitor Shows "Down" But Site Is Up

1. **Check Health Endpoint:**
   - Visit: `https://quicksync.app/api/health` in browser
   - Should return `{"ok": true}` with 200 status

2. **Check SSL Certificate:**
   - UptimeRobot verifies SSL certificates
   - If certificate is invalid, monitor will show down
   - Verify SSL in browser (should show valid)

3. **Check Response Time:**
   - If health endpoint is slow (>30 seconds), may timeout
   - Check Vercel function logs for performance issues

### Not Receiving Alerts

1. **Check Email Spam Folder:**
   - UptimeRobot emails sometimes go to spam
   - Add `noreply@uptimerobot.com` to contacts

2. **Verify Alert Contacts:**
   - Go to: My Settings → Alert Contacts
   - Ensure email is verified and selected for monitor

3. **Check Alert Threshold:**
   - Monitor settings → Alert When Down For
   - Ensure it's set to 1 interval (5 minutes)

---

## 📈 Free Plan Limits

- ✅ **50 monitors** (plenty for QuickSync)
- ✅ **5-minute check interval** (minimum)
- ✅ **Email alerts** (unlimited)
- ✅ **Basic status pages** (optional)
- ⚠️ **SMS alerts:** Requires credits (paid)

**For QuickSync:** Free plan is more than sufficient.

---

## 🎯 Next Steps

1. ✅ Sign up for UptimeRobot
2. ✅ Add monitor for `/api/health` endpoint
3. ✅ Verify monitor shows "Up"
4. ✅ Test alert (optional - stop deployment briefly)
5. ✅ Set up additional monitors (optional)

---

## 📚 Resources

- UptimeRobot Dashboard: https://uptimerobot.com/dashboard
- Documentation: https://uptimerobot.com/api/
- Support: https://uptimerobot.com/support/

---

**Status:** Ready to set up - Just follow the steps above!

