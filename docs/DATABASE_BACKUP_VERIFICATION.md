# Database Backup Verification Guide

**Purpose:** Verify database backups are enabled to prevent data loss  
**Time Required:** 5 minutes  
**Database Provider:** Render.com

---

## 📋 Quick Check Steps

### Step 1: Login to Render.com

1. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com/
   - Login with your account

2. **Navigate to Database:**
   - Find your PostgreSQL database: `quicksync-db`
   - Click on it

---

### Step 2: Check Backup Settings

1. **Look for "Backups" Section:**
   - In the database dashboard
   - Should show backup status

2. **Check Backup Status:**

   **If Using Free Tier:**
   - ⚠️ Free tier databases do NOT have automatic backups
   - You'll see: "Upgrade for backups" or similar
   - **Recommendation:** Consider upgrading to paid tier ($20/month) for backups
   - **OR:** Set up manual backup strategy (see below)

   **If Using Paid Tier:**
   - ✅ Automatic backups should be enabled by default
   - Should show: "Backups: Enabled" or "Last backup: [timestamp]"
   - Backup frequency: Daily (usually)
   - Retention: 7 days (usually, depends on plan)

---

### Step 3: Verify Backup Configuration

**If Backups Are Enabled:**

1. **Check Backup Frequency:**
   - Should be daily (automatic)
   - Usually runs during low-traffic hours

2. **Check Retention Period:**
   - Free/Starter: 7 days (typical)
   - Pro: 30 days (typical)
   - Check your plan details

3. **View Backup History:**
   - Look for "Backups" tab or section
   - Should show list of recent backups
   - Each backup has timestamp and size

---

## ⚠️ If Backups Are NOT Enabled (Free Tier)

### Option 1: Upgrade to Paid Tier (Recommended)

**Cost:** ~$20/month for Starter PostgreSQL

**Benefits:**
- ✅ Automatic daily backups
- ✅ 7-day retention
- ✅ One-click restore
- ✅ Better performance
- ✅ More storage

**Steps:**
1. In Render dashboard → Database
2. Click "Upgrade" or "Change Plan"
3. Select Starter plan ($20/month)
4. Backups will be enabled automatically

---

### Option 2: Manual Backup Strategy (Free Tier)

If you want to stay on free tier, set up manual backups:

#### Option A: Render CLI (Recommended)

1. **Install Render CLI:**
   ```bash
   npm install -g render-cli
   ```

2. **Login:**
   ```bash
   render login
   ```

3. **Create Backup Script:**
   ```bash
   # scripts/backup-database.sh
   #!/bin/bash
   # Run this daily via cron or scheduled task
   
   BACKUP_FILE="backup-$(date +%Y%m%d-%H%M%S).sql"
   DATABASE_URL="your-database-url"
   
   pg_dump $DATABASE_URL > $BACKUP_FILE
   # Upload to S3 or storage service
   ```

#### Option B: pg_dump via Cron Job

1. **Set up cron job** (local machine or VPS)
2. **Run daily:** `pg_dump $DATABASE_URL > backup.sql`
3. **Upload to cloud storage** (S3, Google Drive, etc.)

#### Option C: GitHub Actions (Free)

1. **Create GitHub Action** that runs daily
2. **Dumps database** using pg_dump
3. **Commits backup** to private repo (or uploads to S3)

---

## ✅ Verification Checklist

- [ ] Logged into Render.com dashboard
- [ ] Navigated to `quicksync-db` database
- [ ] Checked backup status
- [ ] If enabled: Verified backup frequency and retention
- [ ] If disabled: Decided on backup strategy (upgrade or manual)

---

## 📊 Recommended Setup

**For Production (Recommended):**

- ✅ **Database Plan:** Starter ($20/month) or higher
- ✅ **Automatic Backups:** Enabled (daily)
- ✅ **Retention:** 7+ days
- ✅ **Restore:** One-click restore available

**Why Paid Tier:**
- Data loss prevention is critical
- $20/month is reasonable for production
- Automatic backups = peace of mind
- One-click restore = fast recovery

---

## 🔄 Backup Testing (If Enabled)

1. **Verify Backups Are Working:**
   - Check backup history
   - Should see daily backups with recent timestamps
   - Backup sizes should be reasonable (not 0 bytes)

2. **Test Restore (Optional - Advanced):**
   - Render.com allows restoring from backup
   - **Warning:** This will replace current database
   - Only test on a separate database instance
   - Don't test on production!

---

## 🚨 Data Loss Prevention

**Best Practices:**

1. ✅ **Enable Automatic Backups** (paid tier)
2. ✅ **Monitor Backup Status** (check weekly)
3. ✅ **Verify Backup Integrity** (check sizes)
4. ✅ **Test Restore Process** (on test database)
5. ✅ **Keep Multiple Backups** (7+ days retention)

---

## 📈 Cost Comparison

**Free Tier:**
- Cost: $0/month
- Backups: ❌ None
- Risk: High (data loss possible)

**Starter Tier:**
- Cost: $20/month
- Backups: ✅ Daily automatic
- Risk: Low (data protected)

**Recommendation:** For production, Starter tier ($20/month) is worth it for automatic backups alone.

---

## 🎯 Next Steps

1. ✅ Check Render.com dashboard
2. ✅ Verify backup status
3. ✅ If disabled: Decide on strategy (upgrade or manual)
4. ✅ If enabled: Verify backups are running

---

## 📚 Resources

- Render.com Dashboard: https://dashboard.render.com/
- Render.com Documentation: https://render.com/docs
- PostgreSQL Backup/Restore: https://render.com/docs/databases#backups-and-restores

---

**Status:** Ready to verify - Just check Render.com dashboard!

