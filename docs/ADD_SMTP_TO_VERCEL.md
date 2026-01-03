# Add SMTP Settings to Vercel

**Status:** ✅ Mailbox `info@quicksync.app` created in Migadu

---

## Option 1: Use the Script (Recommended)

We've created a script that will add all SMTP variables to Vercel:

```bash
./scripts/add_smtp_to_vercel.sh
```

This script will:
- Check Vercel CLI is installed and you're logged in
- Prompt you for your Migadu mailbox password
- Add all 5 SMTP environment variables to Vercel (Production, Preview, Development)

---

## Option 2: Manual via Vercel Dashboard

If you prefer to add them manually:

1. **Go to Vercel Dashboard:**
   - Navigate to: https://vercel.com/[your-team]/quicksync/settings/environment-variables
   - (Replace `[your-team]` with your Vercel username/team)

2. **Add Each Variable:**
   - Click "Add New"
   - Fill in and repeat for each:

   | Key | Value | Environments |
   |-----|-------|--------------|
   | `SMTP_HOST` | `smtp.migadu.com` | Production, Preview, Development |
   | `SMTP_PORT` | `587` | Production, Preview, Development |
   | `SMTP_USER` | `info@quicksync.app` | Production, Preview, Development |
   | `SMTP_PASS` | `[your mailbox password]` | Production, Preview, Development |
   | `SMTP_FROM` | `QuickSync <info@quicksync.app>` | Production, Preview, Development |

---

## Option 3: Vercel CLI Commands

Run these commands one by one (you'll be prompted for values):

```bash
# SMTP_HOST
vercel env add SMTP_HOST production preview development
# When prompted, enter: smtp.migadu.com

# SMTP_PORT
vercel env add SMTP_PORT production preview development
# When prompted, enter: 587

# SMTP_USER
vercel env add SMTP_USER production preview development
# When prompted, enter: info@quicksync.app

# SMTP_PASS
vercel env add SMTP_PASS production preview development
# When prompted, enter: [your mailbox password]

# SMTP_FROM
vercel env add SMTP_FROM production preview development
# When prompted, enter: QuickSync <info@quicksync.app>
```

---

## After Adding Variables

1. **Vercel will automatically use new env vars on next deployment**
2. **Or trigger immediate redeploy:**
   ```bash
   vercel --prod
   ```

3. **Test Email Functionality:**
   - Sign up a new user at https://quicksync.app
   - Check for welcome email
   - Upload a PDF and wait for processing
   - Check for "file ready" email

---

## Verify Variables Added

To check if variables were added successfully:

```bash
vercel env ls
```

You should see all 5 SMTP variables listed.

---

**Which option would you like to use?**

