# Google Search Console Setup Guide

**Purpose:** Verify your domain ownership and submit your sitemap so Google can index your website.

**Time Required:** 10-15 minutes  
**Prerequisites:** Access to your domain's DNS settings (or ability to upload files to your website)

---

## Step 1: Access Google Search Console

1. Go to https://search.google.com/search-console
2. Sign in with your Google account (use the same account you want to manage the site with)
3. If this is your first time, click **"Start now"** or **"Add Property"**

---

## Step 2: Add Your Property

1. Click the **"Add Property"** button (top left)
2. Choose **"URL prefix"** (recommended for most sites)
3. Enter your domain: `https://quicksync.app`
4. Click **"Continue"**

---

## Step 3: Verify Domain Ownership

You'll see several verification methods. Choose the **easiest** one for you:

### Option A: DNS Verification (Recommended - Most Reliable)

**Best for:** If you have access to your domain's DNS settings

**Steps:**
1. Select **"DNS record"** from the verification methods
2. Google will show you a verification code (looks like: `google-site-verification=abc123xyz`)
3. Log in to your domain registrar (where you bought quicksync.app)
   - Common registrars: GoDaddy, Namecheap, Google Domains, Cloudflare, etc.
4. Navigate to DNS management / DNS settings
5. Add a **TXT record** with:
   - **Name/Host:** `@` (or leave blank, or use `quicksync.app`)
   - **Type:** `TXT`
   - **Value/Content:** Copy the entire verification code from Google (starts with `google-site-verification=`)
   - **TTL:** Leave default (usually 3600 or 1 hour)
6. Save the DNS record
7. Wait 5-10 minutes for DNS to propagate
8. Go back to Google Search Console and click **"Verify"**
9. If successful, you'll see "Ownership verified"

**Note:** DNS propagation can take up to 48 hours, but usually works within 5-30 minutes.

---

### Option B: HTML File Upload (Alternative)

**Best for:** If you have access to upload files to your website root

**Steps:**
1. Select **"HTML file"** from the verification methods
2. Google will provide a file to download (e.g., `google1234567890abcdef.html`)
3. Download the HTML file
4. Upload the file to your website's root directory (`/public` folder in Next.js)
   - For Vercel: Upload to `public/` folder in your repo
   - The file should be accessible at: `https://quicksync.app/google1234567890abcdef.html`
5. Commit and push to your repository (if using Git)
6. Wait for Vercel to deploy
7. Verify the file is accessible by visiting the URL in your browser
8. Go back to Google Search Console and click **"Verify"**

**Note:** This method requires a new deployment. If you use this method, you'll need to keep the file in your repo.

---

### Option C: HTML Tag (Alternative)

**Best for:** If you can modify your website's HTML head section

**Steps:**
1. Select **"HTML tag"** from the verification methods
2. Google will show you a meta tag (looks like: `<meta name="google-site-verification" content="abc123xyz" />`)
3. Add this meta tag to your `app/layout.tsx` file in the `<head>` section
4. For Next.js, add it to the `metadata` object in `app/layout.tsx`:
   ```typescript
   export const metadata: Metadata = {
     // ... existing metadata
     verification: {
       google: 'your-verification-code-here', // Add the content value here
     },
   }
   ```
5. Commit and deploy your changes
6. Go back to Google Search Console and click **"Verify"**

**Note:** We already have a placeholder for this in `app/layout.tsx` - you just need to add the code.

---

## Step 4: Submit Your Sitemap

Once verification is successful:

1. In Google Search Console, click on your property (`quicksync.app`)
2. In the left sidebar, click **"Sitemaps"** (under "Indexing")
3. In the "Add a new sitemap" field, enter: `sitemap.xml`
4. Click **"Submit"**
5. You should see: **"Success"** status with a green checkmark

**Your sitemap URL:** `https://quicksync.app/sitemap.xml`

**Note:** Google will start crawling your sitemap. It may take a few days to see results in the "Coverage" report.

---

## Step 5: Verify Everything Works

### Check Sitemap is Accessible

1. Visit: https://quicksync.app/sitemap.xml
2. You should see XML content with your URLs
3. If you see an error, check that `app/sitemap.ts` exists and is properly formatted

### Check Robots.txt

1. Visit: https://quicksync.app/robots.txt
2. You should see:
   ```
   User-agent: *
   Allow: /
   Allow: /bookkeepers
   Disallow: /api/
   Disallow: /jobs/
   Disallow: /auth/
   Sitemap: https://quicksync.app/sitemap.xml
   ```

### Test URL Inspection (Optional)

1. In Google Search Console, use the **"URL Inspection"** tool (search bar at top)
2. Enter: `https://quicksync.app`
3. Click **"Test Live URL"**
4. You should see: "URL is on Google" or "URL is not on Google" (both are fine - indexing takes time)

---

## Step 6: Monitor Your Site (Ongoing)

After setup, Google Search Console will show:

- **Performance:** Search queries, clicks, impressions, CTR
- **Coverage:** Which pages are indexed, errors, warnings
- **Enhancements:** Structured data, mobile usability, etc.
- **Links:** Internal and external links to your site

**Important:** It takes 3-7 days to see initial data, and 2-4 weeks to see meaningful search performance data.

---

## Troubleshooting

### "Verification failed"

**For DNS verification:**
- Wait 10-30 minutes for DNS to propagate
- Double-check the TXT record value (must match exactly)
- Make sure you added it to the root domain (@) not a subdomain
- Try using a DNS checker: https://dnschecker.org/

**For HTML file:**
- Make sure the file is in the `public/` folder
- Verify the file is accessible at the exact URL Google provided
- Check that Vercel has deployed the latest version
- Clear your browser cache and try again

**For HTML tag:**
- Make sure the meta tag is in the `<head>` section
- Verify the code matches exactly (copy/paste, don't type)
- Check that the page has been redeployed

### "Sitemap could not be read"

- Visit `https://quicksync.app/sitemap.xml` directly in your browser
- Check for XML syntax errors
- Make sure `app/sitemap.ts` is properly formatted
- Verify the file was deployed to Vercel

### "No URLs submitted"

- This is normal for new sites
- Google will crawl your sitemap over time
- Check back in 3-7 days
- Make sure your pages are accessible (not behind auth)

---

## Quick Checklist

- [ ] Created Google Search Console account
- [ ] Added property: `https://quicksync.app`
- [ ] Chose verification method (DNS/HTML file/HTML tag)
- [ ] Completed verification (saw "Ownership verified")
- [ ] Submitted sitemap: `sitemap.xml`
- [ ] Verified sitemap is accessible: `https://quicksync.app/sitemap.xml`
- [ ] Verified robots.txt is accessible: `https://quicksync.app/robots.txt`

---

## Next Steps

After setup:

1. **Wait 3-7 days** for initial data
2. **Check Coverage report** to see which pages are indexed
3. **Monitor Performance** to see search queries and clicks
4. **Fix any errors** that appear in the Coverage report
5. **Submit sitemap again** after major content changes (optional - Google will re-crawl automatically)

---

## Additional Resources

- Google Search Console Help: https://support.google.com/webmasters
- Sitemap Guidelines: https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview
- Verification Methods: https://support.google.com/webmasters/answer/9008080

---

**Setup Complete!** Your site is now connected to Google Search Console. Check back in a few days to see indexing progress.

