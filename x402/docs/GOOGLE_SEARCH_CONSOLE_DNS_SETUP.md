# Google Search Console DNS Verification - Quick Guide

**Your TXT Record Value:**
```
google-site-verification=ZkNSSolZpXgzWJoYfiad6lBFy-NwOdB8UK7j5f7G2ng
```

## How to Add TXT Record (By Provider)

### Option 1: Vercel DNS (If using Vercel for DNS)

1. Go to: https://vercel.com/dashboard
2. Click on your project (quicksync)
3. Go to **Settings** → **Domains**
4. Click on **quicksync.app**
5. Click **"DNS Records"** or **"DNS Management"**
6. Click **"Add Record"** or **"New Record"**
7. Fill in:
   - **Type:** `TXT`
   - **Name/Host:** `@` (or leave blank, or `quicksync.app`)
   - **Value:** `google-site-verification=ZkNSSolZpXgzWJoYfiad6lBFy-NwOdB8UK7j5f7G2ng`
   - **TTL:** Leave default (usually 3600 or Auto)
8. Click **Save** or **Add**
9. Wait 5-10 minutes for DNS propagation
10. Go back to Google Search Console and click **"Verify"**

---

### Option 2: GoDaddy

1. Go to: https://www.godaddy.com
2. Sign in to your account
3. Click **"My Products"** or **"Domains"**
4. Find **quicksync.app** and click **"DNS"** or **"Manage DNS"**
5. Scroll down to **"Records"** section
6. Click **"Add"** button
7. Fill in:
   - **Type:** `TXT`
   - **Name:** `@` (or leave blank)
   - **Value:** `google-site-verification=ZkNSSolZpXgzWJoYfiad6lBFy-NwOdB8UK7j5f7G2ng`
   - **TTL:** Leave default (usually 1 hour or 3600)
8. Click **"Save"**
9. Wait 5-10 minutes
10. Go back to Google Search Console and click **"Verify"**

---

### Option 3: Namecheap

1. Go to: https://www.namecheap.com
2. Sign in to your account
3. Go to **"Domain List"**
4. Click **"Manage"** next to **quicksync.app**
5. Go to **"Advanced DNS"** tab
6. In **"Host Records"** section, click **"Add New Record"**
7. Fill in:
   - **Type:** `TXT Record`
   - **Host:** `@` (or leave blank)
   - **Value:** `google-site-verification=ZkNSSolZpXgzWJoYfiad6lBFy-NwOdB8UK7j5f7G2ng`
   - **TTL:** Leave default (usually Automatic or 3600)
8. Click the checkmark to save
9. Wait 5-10 minutes
10. Go back to Google Search Console and click **"Verify"**

---

### Option 4: Cloudflare

1. Go to: https://dash.cloudflare.com
2. Sign in to your account
3. Select your domain: **quicksync.app**
4. Go to **"DNS"** → **"Records"**
5. Click **"Add record"**
6. Fill in:
   - **Type:** `TXT`
   - **Name:** `@` (or leave blank, or `quicksync.app`)
   - **Content:** `google-site-verification=ZkNSSolZpXgzWJoYfiad6lBFy-NwOdB8UK7j5f7G2ng`
   - **TTL:** Leave default (Auto)
7. Click **"Save"**
8. Wait 5-10 minutes (Cloudflare is usually faster)
9. Go back to Google Search Console and click **"Verify"**

---

### Option 5: Google Domains / Squarespace Domains

1. Go to: https://domains.google.com (or your provider)
2. Sign in
3. Click on **quicksync.app**
4. Go to **"DNS"** section
5. Scroll to **"Custom records"** or **"DNS records"**
6. Click **"Add"** or **"Create new record"**
7. Fill in:
   - **Type:** `TXT`
   - **Host name:** `@` (or leave blank)
   - **Text data:** `google-site-verification=ZkNSSolZpXgzWJoYfiad6lBFy-NwOdB8UK7j5f7G2ng`
   - **TTL:** Leave default
8. Click **"Save"**
9. Wait 5-10 minutes
10. Go back to Google Search Console and click **"Verify"**

---

## Quick Checklist

- [ ] Found your DNS provider (Vercel/GoDaddy/Namecheap/Cloudflare/etc.)
- [ ] Added TXT record with the exact value shown above
- [ ] Record name is `@` or blank (for root domain)
- [ ] Saved the record
- [ ] Waited 5-10 minutes for DNS propagation
- [ ] Went back to Google Search Console
- [ ] Clicked **"Verify"** button

---

## Troubleshooting

### "Verification failed" or "Record not found"

**Solutions:**
1. **Wait longer** - DNS can take up to 48 hours (but usually 5-30 minutes)
2. **Check the record value** - Must match exactly (copy/paste, don't type)
3. **Verify record name** - Should be `@` or blank for root domain
4. **Check DNS propagation** - Use: https://dnschecker.org/#TXT/quicksync.app
   - Enter: `quicksync.app`
   - Select: `TXT`
   - Click Search
   - Wait for it to show your TXT record globally

### Can't find DNS settings

**Where to look:**
- Vercel: Settings → Domains → quicksync.app → DNS
- GoDaddy: My Products → Domains → quicksync.app → DNS
- Namecheap: Domain List → Manage → Advanced DNS
- Cloudflare: Dashboard → Select domain → DNS → Records

### Still not working after 24 hours

**Try alternative method:**
1. In Google Search Console, click **"Can't verify via Domain name provider?"**
2. Select **"Use a URL prefix property instead"**
3. Use the HTML file or HTML tag method instead (see main guide)

---

## What Happens After Verification

Once verified successfully:
1. You'll see "Ownership verified" ✅
2. You'll be taken to your Search Console dashboard
3. You can then submit your sitemap: `sitemap.xml`
4. Start monitoring your site's search performance

---

**Next Step After Verification:**
Submit your sitemap at: `https://quicksync.app/sitemap.xml`

See `docs/GOOGLE_SEARCH_CONSOLE_SETUP.md` for complete instructions.

