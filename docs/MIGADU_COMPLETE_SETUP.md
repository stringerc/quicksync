# Complete Migadu Email Setup for QuickSync

**Status:** ✅ Domain active since 2026-01-02  
**Domain:** quicksync.app  
**DNS Provider:** Porkbun

---

## ✅ What's Done

- ✅ Migadu account created
- ✅ Domain verified
- ✅ DNS records configured
- ✅ Domain active and ready

---

## 📋 Next Steps

### Step 1: Create Email Mailbox

1. **Go to Migadu Dashboard:**
   - Login at https://www.migadu.com
   - Navigate to your domain: `@quicksync.app`

2. **Create Mailbox:**
   - Go to "Mailboxes" section
   - Click "New Mailbox" or "Create Mailbox"
   - **Mailbox name:** `info`
   - **Full email:** `info@quicksync.app`
   - **Password:** Create a strong password (save this!)
   - Click "Create" or "Save"

3. **Note Your Credentials:**
   - Email: `info@quicksync.app`
   - Password: (the one you just created)
   - Save these - you'll need them for SMTP

---

### Step 2: Get SMTP Settings

Migadu provides these SMTP settings:

**SMTP Server (Outgoing Mail):**
- **Host:** `smtp.migadu.com`
- **Port:** `587` (STARTTLS) or `465` (SSL/TLS)
- **Security:** STARTTLS (port 587) or SSL/TLS (port 465)
- **Username:** `info@quicksync.app`
- **Password:** (the password you created)

**IMAP Server (Incoming Mail - Optional):**
- **Host:** `imap.migadu.com`
- **Port:** `993` (SSL/TLS)

---

### Step 3: Update Environment Variables in Vercel

You need to add these environment variables to your Vercel project:

```env
SMTP_HOST=smtp.migadu.com
SMTP_PORT=587
SMTP_USER=info@quicksync.app
SMTP_PASS=your-migadu-password-here
SMTP_FROM=QuickSync <info@quicksync.app>
```

**To add them in Vercel:**

1. Go to Vercel Dashboard
2. Select your `quicksync` project
3. Go to Settings → Environment Variables
4. Add each variable:

   - **Key:** `SMTP_HOST`
   - **Value:** `smtp.migadu.com`
   - **Environments:** Production, Preview, Development
   - Click "Save"

   - **Key:** `SMTP_PORT`
   - **Value:** `587`
   - **Environments:** Production, Preview, Development
   - Click "Save"

   - **Key:** `SMTP_USER`
   - **Value:** `info@quicksync.app`
   - **Environments:** Production, Preview, Development
   - Click "Save"

   - **Key:** `SMTP_PASS`
   - **Value:** (paste your Migadu password)
   - **Environments:** Production, Preview, Development
   - Click "Save"

   - **Key:** `SMTP_FROM`
   - **Value:** `QuickSync <info@quicksync.app>`
   - **Environments:** Production, Preview, Development
   - Click "Save"

---

### Step 4: Redeploy Application

After adding environment variables:

1. **Option A: Automatic Redeploy**
   - Vercel should automatically redeploy when you add environment variables
   - Check the "Deployments" tab to see if a new deployment started

2. **Option B: Manual Redeploy**
   - Go to Deployments tab
   - Find the latest deployment
   - Click "..." → "Redeploy"
   - Or push a small change to trigger a new deployment

---

### Step 5: Test Email Functionality

After deployment, test the email system:

1. **Test Welcome Email:**
   - Go to https://quicksync.app
   - Sign up with a NEW email address (magic link auth)
   - Complete authentication
   - Check if welcome email arrives

2. **Test File Ready Email:**
   - Upload a PDF file
   - Wait for processing to complete
   - Check if "File Ready" email arrives

3. **Check Email Logs:**
   - In Migadu Dashboard → "Recent Activity" or "Email Logs"
   - You should see sent emails listed there

---

## 🔍 Troubleshooting

### Emails Not Sending?

1. **Check Environment Variables:**
   - Verify all SMTP variables are set in Vercel
   - Check that values match exactly (no extra spaces)

2. **Check Migadu Dashboard:**
   - Go to "Recent Activity"
   - Look for failed sends or errors

3. **Check Vercel Logs:**
   - Go to Vercel Dashboard → Your Project → Logs
   - Look for SMTP errors

4. **Verify SMTP Credentials:**
   - Double-check username: `info@quicksync.app`
   - Verify password is correct
   - Try port 465 instead of 587 (SSL/TLS)

5. **Check Migadu Limits:**
   - Free tier: 10 MB/day sending limit
   - If you hit the limit, you'll need to wait or upgrade

---

### Common SMTP Errors

**Error: "Authentication failed"**
- Check username and password
- Verify username is full email: `info@quicksync.app`
- Check password doesn't have extra spaces

**Error: "Connection timeout"**
- Try port 465 instead of 587
- Check if firewall is blocking

**Error: "530 5.7.0 Must issue a STARTTLS command first"**
- Make sure you're using port 587 with STARTTLS
- Or use port 465 with SSL/TLS

---

## 📊 What Email Features Are Now Active?

Once configured, these emails will automatically send:

1. **Welcome Email** ✅
   - Sent when new user signs up
   - Triggered in: `app/api/auth/callback/route.ts`

2. **File Ready Email** ✅
   - Sent when PDF processing completes
   - Triggered in: `app/api/process/route.ts`

3. **Abandoned Cart Email** ✅
   - Template ready (not yet automated)
   - Would need a cron job or scheduled task

---

## ✅ Checklist

- [ ] Create `info@quicksync.app` mailbox in Migadu
- [ ] Save mailbox password securely
- [ ] Add SMTP environment variables to Vercel:
  - [ ] SMTP_HOST
  - [ ] SMTP_PORT
  - [ ] SMTP_USER
  - [ ] SMTP_PASS
  - [ ] SMTP_FROM
- [ ] Redeploy application (automatic or manual)
- [ ] Test welcome email (sign up new user)
- [ ] Test file ready email (upload and process PDF)
- [ ] Verify emails appear in Migadu activity log

---

## 🎯 After This Setup

Once emails are working:

1. ✅ Email marketing foundation is complete
2. ✅ Welcome emails will improve user onboarding
3. ✅ File ready notifications will improve user experience
4. ✅ You can expand email features (newsletters, promotions, etc.)

**Next Steps from Strategic Plan:**
- Continue with Week 3 items (content marketing, blog setup)
- Monitor email deliverability
- Track email open/click rates (if using analytics)

---

**Need help with any step? Let me know!**

