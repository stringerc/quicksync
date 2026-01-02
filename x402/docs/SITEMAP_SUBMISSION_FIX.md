# Fix: "Invalid sitemap address" Error

## ✅ Good News
Your sitemap IS working! It's accessible and valid XML.

**Working URLs:**
- ✅ https://www.quicksync.app/sitemap.xml (returns 200 OK)
- ✅ https://quicksync.app/sitemap.xml (redirects to www)

---

## 🔧 The Fix

When submitting in Google Search Console, you need to use the **FULL URL**, not just the filename.

### ❌ Wrong:
```
sitemap.xml
```

### ✅ Correct (use ONE of these):

**Option 1: Use the www version (recommended)**
```
https://www.quicksync.app/sitemap.xml
```

**Option 2: Use non-www (it will redirect, but works)**
```
https://quicksync.app/sitemap.xml
```

---

## 📋 Step-by-Step Fix

1. **Go to Google Search Console**
   - Navigate to: https://search.google.com/search-console

2. **Select your property** (whichever domain you verified - www or non-www)

3. **Go to Sitemaps**
   - Click **"Sitemaps"** in the left sidebar

4. **Submit with FULL URL**
   - In the **"Add a new sitemap"** field, enter the FULL URL:
     - `https://www.quicksync.app/sitemap.xml` 
     - OR `https://quicksync.app/sitemap.xml`
   - **Don't just type:** `sitemap.xml`

5. **Click "Submit"**

6. **You should see:** ✅ **"Success"** status

---

## 🤔 Which Domain Should You Use?

Use the **exact domain you verified** in Google Search Console:

- **If you verified `quicksync.app`** (non-www) → Use: `https://quicksync.app/sitemap.xml`
- **If you verified `www.quicksync.app`** (www) → Use: `https://www.quicksync.app/sitemap.xml`

**How to check which one you verified:**
- Look at the top of Google Search Console - it shows your property name/URL
- That's the one you should use for the sitemap URL

---

## ✅ Verify It's Working

After submission, you should see:

1. **Status:** "Success"
2. **URLs discovered:** Should show 2 URLs (homepage + /bookkeepers)
3. **Last read:** Should show a recent timestamp

---

## 🐛 Still Getting Errors?

If you still get "Invalid sitemap address" after using the full URL:

1. **Check the domain matches your verified property:**
   - Make sure you're using the exact same domain (www vs non-www) that you verified

2. **Try both versions:**
   - Try: `https://www.quicksync.app/sitemap.xml`
   - If that fails, try: `https://quicksync.app/sitemap.xml`

3. **Wait a few minutes:**
   - Sometimes Google needs a moment to recognize new sitemaps

4. **Verify the sitemap is accessible:**
   - Open the URL in your browser
   - You should see XML content (not an error page)

---

## 📊 Current Sitemap Status

Your sitemap contains:
- ✅ Homepage: `https://quicksync.app`
- ✅ Bookkeepers page: `https://quicksync.app/bookkeepers`
- ✅ Valid XML format
- ✅ Proper encoding (UTF-8)
- ✅ Correct sitemap schema

**Everything is configured correctly!** Just make sure to use the full URL when submitting. 🎉

