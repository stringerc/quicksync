# Sentry Error Monitoring Setup

**Purpose:** Automatic error tracking and alerting for QuickSync  
**Time Required:** 15 minutes  
**Status:** ✅ Code integration complete - Need to add DSN

---

## ✅ What's Already Done

1. ✅ Sentry package installed (`@sentry/nextjs`)
2. ✅ Configuration files created:
   - `sentry.client.config.ts` - Client-side error tracking
   - `sentry.server.config.ts` - Server-side error tracking
   - `sentry.edge.config.ts` - Edge runtime error tracking

---

## 📋 Setup Steps (You Need to Do)

### Step 1: Create Sentry Account & Project

1. **Sign up for Sentry:**
   - Go to: https://sentry.io/signup/
   - Create a free account (free tier includes 5,000 errors/month)

2. **Create a New Project:**
   - Click "Create Project"
   - Select "Next.js"
   - Project name: "quicksync" or "QuickSync"
   - Click "Create Project"

3. **Get Your DSN:**
   - After creating the project, you'll see your DSN (Data Source Name)
   - It looks like: `https://xxxxx@xxxxx.ingest.sentry.io/xxxxx`
   - Copy this DSN (you'll need it in Step 2)

---

### Step 2: Add DSN to Vercel Environment Variables

1. **Go to Vercel Dashboard:**
   - Navigate to: https://vercel.com/[your-team]/quicksync/settings/environment-variables

2. **Add Environment Variables:**

   **For Server-Side:**
   - **Key:** `SENTRY_DSN`
   - **Value:** `https://xxxxx@xxxxx.ingest.sentry.io/xxxxx` (your DSN from Step 1)
   - **Environments:** Production, Preview, Development
   - Click "Save"

   **For Client-Side (optional but recommended):**
   - **Key:** `NEXT_PUBLIC_SENTRY_DSN`
   - **Value:** Same DSN as above
   - **Environments:** Production, Preview, Development
   - Click "Save"

---

### Step 3: Update Next.js Configuration

The Sentry wizard should have updated `next.config.js`, but if it didn't, you may need to run:

```bash
npx @sentry/wizard@latest -i nextjs
```

This will automatically update your Next.js config to integrate Sentry.

---

### Step 4: Redeploy

After adding the DSN:

```bash
git add .
git commit -m "Add Sentry error monitoring"
git push
```

Or trigger a redeploy in Vercel dashboard.

---

### Step 5: Test Error Tracking

1. **Trigger a test error:**
   - Go to Sentry Dashboard → Settings → Projects → Your Project → Client Keys (DSN)
   - Click "Test Error" button
   - Or: Visit a non-existent page to trigger a 404 (will be logged)

2. **Verify in Sentry:**
   - Go to Sentry Dashboard → Issues
   - You should see the test error appear within seconds

---

## 🔔 Setting Up Alerts

1. **Go to Sentry Dashboard:**
   - Navigate to: Alerts → Create Alert Rule

2. **Create Alert Rule:**
   - **Name:** "Critical Errors - QuickSync"
   - **Conditions:**
     - When an issue is created
     - Or: When events exceed X per minute
   - **Actions:**
     - Send email notification
     - Add your email address

3. **Recommended Alerts:**
   - **Critical Errors:** Any error in production
   - **High Volume:** More than 10 errors in 5 minutes
   - **Payment Errors:** Errors containing "stripe" or "payment"

---

## 📊 What Gets Tracked

Sentry will automatically track:

- ✅ **Unhandled exceptions** in API routes
- ✅ **Unhandled promise rejections**
- ✅ **React component errors** (if using client-side)
- ✅ **Server errors** (500 errors, etc.)
- ✅ **API route errors**

**Not tracked (by design):**
- ❌ Development errors (only production)
- ❌ Network errors (user connection issues)

---

## 🔍 Viewing Errors

1. **Go to Sentry Dashboard:**
   - https://sentry.io/organizations/[your-org]/issues/

2. **Error Details:**
   - Stack traces
   - Request data
   - User context
   - Browser/device info
   - Timestamp and frequency

---

## 📧 Email Notifications

Sentry will automatically send email notifications when:

- New errors occur
- Error frequency spikes
- Based on your alert rules

---

## ⚙️ Configuration

The Sentry configuration is in:

- `sentry.client.config.ts` - Client-side (browser)
- `sentry.server.config.ts` - Server-side (API routes)
- `sentry.edge.config.ts` - Edge runtime (middleware)

**Current Settings:**
- ✅ Only enabled in production
- ✅ 100% error sampling (captures all errors)
- ✅ Filtered to exclude development errors
- ✅ Filtered to exclude network errors (browser only)

---

## 🎯 Next Steps After Setup

1. ✅ Add DSN to Vercel environment variables
2. ✅ Redeploy application
3. ✅ Test error tracking
4. ✅ Set up email alerts
5. ✅ Monitor for the first few errors to ensure it's working

---

## 📚 Resources

- Sentry Next.js Docs: https://docs.sentry.io/platforms/javascript/guides/nextjs/
- Sentry Dashboard: https://sentry.io/
- Free Tier Limits: 5,000 errors/month (plenty for most apps)

---

**Status:** Code integration complete - Just add DSN and deploy!

