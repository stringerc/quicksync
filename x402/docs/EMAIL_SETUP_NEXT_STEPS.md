# Email Setup - Next Steps

**Current Status:** ✅ Migadu domain active, need to create mailbox and configure SMTP

---

## Step 1: Create info@quicksync.app Mailbox (REQUIRED)

You currently only have `postmaster@quicksync.app`. You need to create `info@quicksync.app`:

1. **Go to Migadu Dashboard:**
   - Login at https://www.migadu.com
   - Navigate to your domain: `@quicksync.app`

2. **Create New Mailbox:**
   - Click "Mailboxes" in the left menu
   - Click "New Mailbox" or "Create Mailbox" button
   - Fill in:
     - **Mailbox name:** `info` (this creates `info@quicksync.app`)
     - **Password:** Create a strong password (SAVE THIS - you'll need it for SMTP)
     - Click "Create" or "Save"

3. **Verify Mailbox Created:**
   - You should now see both:
     - `postmaster@quicksync.app` (already exists)
     - `info@quicksync.app` (newly created)

---

## Step 2: Add SMTP Settings to Vercel

After creating the mailbox, you need to add these environment variables to Vercel:

### Environment Variables Needed:

```
SMTP_HOST=smtp.migadu.com
SMTP_PORT=587
SMTP_USER=info@quicksync.app
SMTP_PASS=<your-mailbox-password>
SMTP_FROM=QuickSync <info@quicksync.app>
```

### How to Add to Vercel:

1. **Go to Vercel Dashboard:**
   - Navigate to: https://vercel.com/[your-team]/quicksync/settings/environment-variables
   - (Replace `[your-team]` with your Vercel username/team)

2. **Add Each Variable:**
   - Click "Add New"
   - **Key:** `SMTP_HOST`
   - **Value:** `smtp.migadu.com`
   - **Environments:** Select "Production", "Preview", "Development"
   - Click "Save"

   - Click "Add New"
   - **Key:** `SMTP_PORT`
   - **Value:** `587`
   - **Environments:** Select all
   - Click "Save"

   - Click "Add New"
   - **Key:** `SMTP_USER`
   - **Value:** `info@quicksync.app`
   - **Environments:** Select all
   - Click "Save"

   - Click "Add New"
   - **Key:** `SMTP_PASS`
   - **Value:** `<paste your mailbox password here>`
   - **Environments:** Select all
   - Click "Save"

   - Click "Add New"
   - **Key:** `SMTP_FROM`
   - **Value:** `QuickSync <info@quicksync.app>`
   - **Environments:** Select all
   - Click "Save"

3. **Redeploy (Optional):**
   - Vercel will automatically use new env vars on next deployment
   - Or trigger a redeploy: Go to Deployments → Latest → "Redeploy"

---

## Step 3: Test Email Functionality

After adding SMTP settings and redeploying:

1. **Test Welcome Email:**
   - Go to https://quicksync.app
   - Sign up with a NEW email address (magic link auth)
   - Complete authentication
   - Check inbox for welcome email

2. **Test File Ready Email:**
   - Upload a PDF file
   - Wait for processing to complete
   - Check inbox for "Your file is ready" email

3. **Check Migadu Dashboard:**
   - Go to "Recent Activity" in Migadu
   - You should see sent emails listed

---

## What's Next? (Strategic Plan)

After email setup is complete, here's what comes next according to the strategic plan:

### Week 3-4: Content Marketing & SEO (Current Phase)

1. **Blog Setup** (1-2 days)
   - Create `/blog` or `/guides` section
   - Set up blog structure in Next.js
   - Add blog post templates

2. **First Blog Post** (4-6 hours or $100-200)
   - Write: "How to Convert Bank Statements to CSV for QuickBooks"
   - Target keywords: "bank statement to CSV converter", "PDF to QuickBooks converter"
   - Optimize for SEO (meta tags, internal links)

3. **Content Marketing Foundation** (Ongoing)
   - Goal: 4-6 blog posts in Month 1
   - Focus on solving problems, not selling
   - SEO-focused content

### Month 1 Goals:
- ✅ Get first 10-20 customers (free first file + organic)
- ✅ Gather customer feedback
- ✅ Monitor metrics (conversion, refunds, satisfaction)
- ✅ Validate product-market fit

### Month 2 Goals (Only if validated):
- Content marketing expansion (4-6 more blog posts)
- Referral program (if you have happy customers)
- Small paid ads test ($200-500/month)

---

## Summary Checklist

- [ ] Create `info@quicksync.app` mailbox in Migadu
- [ ] Save mailbox password
- [ ] Add SMTP environment variables to Vercel:
  - [ ] SMTP_HOST
  - [ ] SMTP_PORT
  - [ ] SMTP_USER
  - [ ] SMTP_PASS
  - [ ] SMTP_FROM
- [ ] Redeploy application (if needed)
- [ ] Test welcome email
- [ ] Test file ready email
- [ ] Verify emails in Migadu activity log

**Once complete → Move to Week 3 items (Content Marketing & SEO)**

---

**Need help?** Let me know once you've created the mailbox and I can help you add the SMTP settings to Vercel!

