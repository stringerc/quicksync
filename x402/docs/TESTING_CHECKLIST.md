# Testing Checklist - Week 1 Implementation

**Date:** January 2025  
**Purpose:** Test all Week 1 features before deploying to production

---

## Pre-Testing Setup

- [ ] Local environment is running (`npm run dev`)
- [ ] Database is set up and accessible
- [ ] Environment variables are configured
- [ ] Can access the site at http://localhost:3000

---

## 1. SEO Foundation Testing

### 1.1 Meta Tags

- [ ] Visit homepage: http://localhost:3000
- [ ] Right-click → "View Page Source" (or Cmd+U / Ctrl+U)
- [ ] Check that `<title>` tag includes "QuickSync - Bank Statement to CSV/QBO Converter"
- [ ] Check that `<meta name="description">` tag exists with proper description
- [ ] Check that OpenGraph tags are present (`<meta property="og:...">`)
- [ ] Check that Twitter Card tags are present (`<meta name="twitter:...">`)

**Expected Result:** All meta tags should be present and properly formatted.

---

### 1.2 Sitemap

- [ ] Visit: http://localhost:3000/sitemap.xml
- [ ] Should see XML content (not error page)
- [ ] XML should contain:
  - URL: `http://localhost:3000` (or your domain)
  - URL: `http://localhost:3000/bookkeepers`
  - Proper XML structure

**Expected Result:** Valid XML sitemap with at least 2 URLs.

---

### 1.3 Robots.txt

- [ ] Visit: http://localhost:3000/robots.txt
- [ ] Should see:
  ```
  User-agent: *
  Allow: /
  Allow: /bookkeepers
  Disallow: /api/
  Disallow: /jobs/
  Disallow: /auth/
  Sitemap: https://quicksync.app/sitemap.xml
  ```

**Expected Result:** robots.txt file with proper directives.

---

### 1.4 Structured Data

- [ ] Visit homepage: http://localhost:3000
- [ ] Right-click → "View Page Source"
- [ ] Search for `application/ld+json`
- [ ] Should find JSON-LD structured data blocks
- [ ] Should include Organization schema
- [ ] Should include SoftwareApplication schema

**Expected Result:** Structured data present in page source.

---

## 2. Free First File Feature Testing

### 2.1 First File (New User) - Should Be FREE

1. **Upload Test:**
   - [ ] Go to homepage: http://localhost:3000
   - [ ] Use a **new email address** (one you've never used before)
   - [ ] Upload a PDF file
   - [ ] Wait for processing to complete

2. **Payment Test:**
   - [ ] Click "Pay to Download" or "Pay $9 to Download"
   - [ ] Enter email if prompted
   - [ ] **Expected:** Should see success message: "🎉 Free first file! Your job is ready for download."
   - [ ] **Should NOT redirect to Stripe checkout**
   - [ ] Payment status should change to "paid"

3. **Download Test:**
   - [ ] Download buttons should appear
   - [ ] Click "Download CSV" - should download file
   - [ ] Click "Download QBO" - should download file

**Expected Result:** First file is free, no Stripe checkout, files download successfully.

---

### 2.2 Second File (Same User) - Should Require Payment

1. **Upload Second File:**
   - [ ] Use the **same email** from test 2.1
   - [ ] Upload another PDF file
   - [ ] Wait for processing to complete

2. **Payment Test:**
   - [ ] Click "Pay to Download"
   - [ ] **Expected:** Should redirect to Stripe checkout (test mode)
   - [ ] **Should NOT show free file message**

**Expected Result:** Second file requires payment via Stripe checkout.

---

### 2.3 Landing Page Messaging

- [ ] Visit homepage: http://localhost:3000
- [ ] Look for: "🎉 Try your first file free - no credit card required!"
- [ ] Message should be visible above the upload form

**Expected Result:** Free first file messaging is visible on landing page.

---

## 3. Parser Validation Testing

### 3.1 Duplicate Removal

1. **Upload Test File:**
   - [ ] Upload a PDF with known duplicate transactions
   - [ ] Wait for processing

2. **Check CSV Output:**
   - [ ] Download the CSV file
   - [ ] Open in Excel/Google Sheets
   - [ ] Check for duplicate rows (same date, description, amount)
   - [ ] **Expected:** No duplicate rows should appear

**Expected Result:** Duplicates are removed from CSV output.

---

### 3.2 Balance Verification

1. **Upload Test File:**
   - [ ] Upload a PDF with balance information
   - [ ] Wait for processing

2. **Check Balance Column:**
   - [ ] Download the CSV file
   - [ ] Check the Balance column
   - [ ] Verify balances are sequential and make sense
   - [ ] Calculate: previous balance + credit - debit = current balance
   - [ ] **Expected:** Balances should be consistent

**Expected Result:** Balance calculations are correct and sequential.

---

### 3.3 Date Monotonicity

1. **Upload Test File:**
   - [ ] Upload a PDF with transaction dates
   - [ ] Wait for processing

2. **Check Date Column:**
   - [ ] Download the CSV file
   - [ ] Check the Date column
   - [ ] Verify dates are roughly sequential (some variation is OK)
   - [ ] **Expected:** Dates should progress forward (not jump backwards significantly)

**Expected Result:** Dates are properly ordered and make sense.

---

### 3.4 Confidence Score

- [ ] Upload various PDF files
- [ ] Check confidence scores shown on job page
- [ ] **Expected:** Scores should be 0-100 range
- [ ] Files with more transactions should have higher scores
- [ ] Files with issues (duplicates, balance problems) should have lower scores

**Expected Result:** Confidence scores are meaningful and accurate.

---

## 4. Integration Testing

### 4.1 End-to-End Flow (New User)

- [ ] User visits homepage
- [ ] Sees "Free first file" messaging
- [ ] Uploads PDF (no login required)
- [ ] Sees processing status
- [ ] Sees preview (watermarked)
- [ ] Clicks "Pay to Download"
- [ ] Enters email
- [ ] Gets free file (no payment)
- [ ] Downloads CSV
- [ ] Downloads QBO
- [ ] **Expected:** Everything works smoothly

---

### 4.2 End-to-End Flow (Returning User)

- [ ] User who has already used free file
- [ ] Uploads new PDF
- [ ] Sees processing status
- [ ] Clicks "Pay to Download"
- [ ] Redirects to Stripe checkout (or shows payment required)
- [ ] **Expected:** Payment is required (not free)

---

## 5. Error Handling Testing

### 5.1 Invalid PDF

- [ ] Try uploading a non-PDF file
- [ ] **Expected:** Should show error message

### 5.2 Processing Errors

- [ ] Upload a corrupted PDF
- [ ] **Expected:** Should show error state, not crash

### 5.3 Payment Errors

- [ ] Test free first file with invalid email
- [ ] **Expected:** Should show appropriate error message

---

## 6. Performance Testing

- [ ] Homepage loads quickly (< 2 seconds)
- [ ] Upload completes in reasonable time
- [ ] Processing doesn't timeout
- [ ] Downloads work smoothly

---

## 7. Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Edge
- [ ] Safari
- [ ] Firefox

**Expected:** Should work in all modern browsers.

---

## Production Deployment Checklist

Before deploying to production:

- [ ] All tests above pass locally
- [ ] Environment variables are set in Vercel
- [ ] Database is accessible from production
- [ ] Stripe keys are in production mode (if ready)
- [ ] Build succeeds: `npm run build`
- [ ] No console errors in browser
- [ ] Sitemap accessible: https://quicksync.app/sitemap.xml
- [ ] Robots.txt accessible: https://quicksync.app/robots.txt

---

## Issues Found

Document any issues you encounter:

1. **Issue:** [Description]
   - **Steps to reproduce:** [Steps]
   - **Expected:** [Expected behavior]
   - **Actual:** [Actual behavior]
   - **Severity:** [High/Medium/Low]

---

## Test Results Summary

- [ ] All SEO tests pass
- [ ] Free first file works correctly
- [ ] Parser validation improvements work
- [ ] Integration tests pass
- [ ] Error handling works
- [ ] Performance is acceptable
- [ ] Ready for production deployment

---

**Testing Complete!** ✅

If all tests pass, you're ready to deploy to production and set up Google Search Console.

