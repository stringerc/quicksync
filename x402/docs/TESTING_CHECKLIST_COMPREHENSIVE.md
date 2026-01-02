# Comprehensive Testing Checklist
**QuickSync.app - Production Testing**

**Recommended Testing Order:** SEO (5 min) → Free First File (10 min) → Parser (10 min) → Integration (15 min)  
**Total Time: ~40 minutes**

---

## ✅ 1. SEO TESTS (5 minutes)

### 1.1 Meta Tags Verification
- [ ] **Homepage (`https://quicksync.app`)**
  - [ ] View page source, verify:
    - `<title>` contains "QuickSync - Bank Statement to CSV/QBO Converter"
    - `<meta name="description">` is present and descriptive
    - OpenGraph tags (`og:title`, `og:description`, `og:url`)
    - Twitter Card tags
    - `canonical` URL

- [ ] **Bookkeepers Page (`https://quicksync.app/bookkeepers`)**
  - [ ] View page source, verify meta tags exist
  - [ ] Title is unique and descriptive

- [ ] **Job Details Page** (any job URL)
  - [ ] View page source, verify meta tags
  - [ ] Title includes job filename or relevant info

### 1.2 Sitemap & Robots
- [ ] **Sitemap Accessibility**
  - [ ] Visit: `https://www.quicksync.app/sitemap.xml`
  - [ ] Verify: Returns valid XML (not 404)
  - [ ] Verify: Contains homepage URL
  - [ ] Verify: Contains `/bookkeepers` URL

- [ ] **Robots.txt**
  - [ ] Visit: `https://quicksync.app/robots.txt`
  - [ ] Verify: Allows all user agents
  - [ ] Verify: Sitemap URL is listed
  - [ ] Verify: API routes are disallowed

### 1.3 Google Search Console
- [ ] **Verification Status**
  - [ ] Log into Google Search Console
  - [ ] Verify: Domain shows "Ownership verified"
  - [ ] Check: No critical errors

- [ ] **Sitemap Status**
  - [ ] Navigate to: Sitemaps section
  - [ ] Verify: `https://www.quicksync.app/sitemap.xml` shows "Success"
  - [ ] Verify: URLs discovered = 2 (or more if indexed)
  - [ ] Check: Last read timestamp is recent

- [ ] **Coverage Report** (check after 24-48 hours)
  - [ ] Navigate to: Coverage section
  - [ ] Verify: No critical errors
  - [ ] Check: Pages are being discovered/indexed

---

## 🎁 2. FREE FIRST FILE TESTS (10 minutes)

### 2.1 New User Free File Flow
- [ ] **Upload as New User (No Account)**
  1. Go to: `https://quicksync.app`
  2. Upload a PDF (use a test bank statement)
  3. Wait for processing to complete
  4. Verify: Preview shows watermarked files
  5. Click: "Pay $9 to Download"
  6. Verify: **Should show "Free first file!" message**
  7. Verify: Job status changes to "paid" automatically
  8. Verify: Download buttons appear without Stripe checkout

- [ ] **Verify Free File Grant**
  - [ ] Check: Job page shows "Free first file! Your job is ready for download."
  - [ ] Verify: Download CSV button works
  - [ ] Verify: Download QBO button works
  - [ ] Verify: No payment was processed (check Stripe dashboard)

### 2.2 Returning User Paid Flow
- [ ] **Second File (Should Require Payment)**
  1. Upload a second PDF (same or different email)
  2. Wait for processing
  3. Click: "Pay $9 to Download"
  4. Verify: **Stripe Checkout opens** (not free)
  5. Complete test payment (use Stripe test card: `4242 4242 4242 4242`)
  6. Verify: Redirected back to job page
  7. Verify: Download buttons appear
  8. Verify: Files download successfully

### 2.3 Email Eligibility Check
- [ ] **Test Different Emails**
  - [ ] Use email that has never paid before → Should get free file
  - [ ] Use email that has paid before → Should require payment
  - [ ] Use same email for second file → Should require payment

---

## 📊 3. PARSER QUALITY TESTS (10 minutes)

### 3.1 Date Parsing
- [ ] **Upload PDF with various date formats**
  - [ ] Test: MM/DD/YYYY format
  - [ ] Test: M/D/YY format (2-digit year)
  - [ ] Test: Dates in 2024-2025 range
  - [ ] Verify: Dates parse correctly in CSV output
  - [ ] Verify: No dates show as "1900" or invalid years

### 3.2 Debit/Credit Logic
- [ ] **Verify Simplified Logic**
  - [ ] Upload PDF with transactions
  - [ ] Check CSV output:
    - [ ] **Negative amounts** → Should be in Debit column (positive value)
    - [ ] **Positive amounts** → Should be in Credit column
    - [ ] Verify: No amount appears in both columns
    - [ ] Verify: Example: `-3.01` → Debit: `3.01`, Credit: empty
    - [ ] Verify: Example: `11.04` → Credit: `11.04`, Debit: empty

### 3.3 Description Quality
- [ ] **Tab Character Handling**
  - [ ] Upload PDF with descriptions containing tabs
  - [ ] Verify: Descriptions appear in single cell (not split)
  - [ ] Verify: No extra columns created
  - [ ] Verify: Example: "PURCHASE 1112 CURSOR AI POWERED IDE CURSOR.COM NY" stays in one cell

- [ ] **Special Characters**
  - [ ] Test: Descriptions with quotes, commas, ampersands
  - [ ] Verify: CSV properly escapes quotes (double quotes)
  - [ ] Verify: No CSV formatting errors

### 3.4 Balance Calculation
- [ ] **Balance Propagation**
  - [ ] Upload PDF with transactions
  - [ ] Check: First transaction has balance
  - [ ] Verify: Subsequent transactions calculate balance correctly
  - [ ] Formula check: `balance = prevBalance + credit - debit`
  - [ ] Verify: Final balance matches PDF ending balance

### 3.5 Validation Rules
- [ ] **Duplicate Detection**
  - [ ] Upload PDF (if you have one with duplicates)
  - [ ] Check: Validation issues list shows duplicate warnings (if any)
  - [ ] Verify: Duplicates are removed from output

- [ ] **Date Monotonicity**
  - [ ] Check: Transactions are in chronological order
  - [ ] Verify: No dates appear out of order (unless PDF itself has errors)

- [ ] **Balance Verification**
  - [ ] Check: Balance calculations are consistent
  - [ ] Verify: Validation issues list shows balance discrepancies (if any)

### 3.6 Confidence Score
- [ ] **Score Display**
  - [ ] Verify: Confidence score shows on job page (0-100%)
  - [ ] Verify: Score is reasonable (usually 70-100% for good PDFs)
  - [ ] Verify: Low scores (<70%) show warning message

- [ ] **Score Accuracy**
  - [ ] Test with clean PDF → Should be high (85-100%)
  - [ ] Test with messy PDF → Should be lower (50-80%)
  - [ ] Verify: Score reflects parsing quality

---

## 🔗 4. INTEGRATION TESTS (15 minutes)

### 4.1 Upload Flow
- [ ] **Anonymous Upload**
  1. Go to homepage (not logged in)
  2. Upload PDF file
  3. Verify: Redirected to job page immediately
  4. Verify: No login required
  5. Verify: Processing starts automatically

- [ ] **Processing Status**
  - [ ] Verify: Job shows "Processing..." status
  - [ ] Verify: Auto-refreshes every 3 seconds
  - [ ] Verify: Status changes to "completed" when done
  - [ ] Verify: Processing takes < 30 seconds for typical PDF

### 4.2 Preview Flow
- [ ] **Watermarked Previews**
  - [ ] After processing, verify: "Preview Your Results" section appears
  - [ ] Click: "Preview CSV" button
  - [ ] Verify: Opens in new tab/window
  - [ ] Verify: HTML table displays with watermark overlay
  - [ ] Verify: Watermark text "PREVIEW - quicksync.app" is visible
  - [ ] Verify: Data is readable but clearly marked as preview
  - [ ] Click: "Preview QBO" button
  - [ ] Verify: Opens PDF with watermark
  - [ ] Verify: Watermark is visible but doesn't block content

- [ ] **Sample Rows Display** (NEW FEATURE)
  - [ ] After processing, verify: "Sample Output" table appears on job page
  - [ ] Verify: Shows first 5 rows (header + 4 transactions)
  - [ ] Verify: Table is readable and formatted correctly
  - [ ] Verify: Columns match: Date, Description, Debit, Credit, Balance
  - [ ] Verify: Sample rows match actual CSV content

### 4.3 Payment Flow
- [ ] **Stripe Checkout (Returning User)**
  1. Upload file (as returning user)
  2. Click: "Pay $9 to Download"
  3. Verify: Email input appears (if not logged in)
  4. Enter email and click payment button
  5. Verify: Redirected to Stripe Checkout
  6. Verify: Amount shows $9.00
  7. Verify: Product description is correct
  8. Use test card: `4242 4242 4242 4242`
  9. Complete payment
  10. Verify: Redirected back to job page with `?payment=success`
  11. Verify: Download buttons appear

- [ ] **Payment Status**
  - [ ] Verify: Job page shows "Payment: paid"
  - [ ] Verify: No "Pay $9" button (already paid)
  - [ ] Verify: Can download multiple times (no re-payment required)

### 4.4 Download Flow
- [ ] **CSV Download**
  - [ ] Click: "Download CSV" button
  - [ ] Verify: File downloads (not redirects to error)
  - [ ] Verify: Filename is reasonable (includes .csv extension)
  - [ ] Open in Excel/Google Sheets
  - [ ] Verify: Columns: Date, Description, Debit, Credit, Balance
  - [ ] Verify: Data matches preview
  - [ ] Verify: No formatting errors (extra columns, broken rows)

- [ ] **QBO Download**
  - [ ] Click: "Download QBO" button
  - [ ] Verify: File downloads
  - [ ] Verify: Filename includes .qbo extension
  - [ ] Verify: File can be opened in QuickBooks (if you have it)
  - [ ] Verify: Transaction data appears correctly

### 4.5 Error Handling
- [ ] **Failed Processing**
  - [ ] Upload invalid/corrupted PDF (if possible)
  - [ ] Verify: Job status shows "failed"
  - [ ] Verify: Error message is user-friendly
  - [ ] Verify: Support token is visible
  - [ ] Verify: Payment button is NOT shown for failed jobs

- [ ] **Low Confidence**
  - [ ] Upload PDF that parses poorly (if available)
  - [ ] Verify: Confidence score is low (<70%)
  - [ ] Verify: Warning message appears
  - [ ] Verify: Payment is blocked or discouraged
  - [ ] Verify: "Request Review" button appears (if logged in)

- [ ] **Missing File**
  - [ ] Try to access non-existent job: `/jobs/invalid-id`
  - [ ] Verify: Shows 404 or friendly error message

### 4.6 Authentication Flow
- [ ] **Magic Link Login**
  1. Click: "Send Magic Link" on homepage
  2. Enter email address
  3. Verify: Success message appears
  4. Check email (inbox/spam)
  5. Click magic link
  6. Verify: Redirected to job list or homepage
  7. Verify: Shows logged-in state

- [ ] **Job List (Logged In)**
  - [ ] After login, verify: Can see past jobs
  - [ ] Verify: Jobs show status and payment status
  - [ ] Verify: Can click to view job details

### 4.7 Credits System (Optional - if implemented)
- [ ] **Purchase Credit Pack**
  - [ ] Navigate to credit purchase page
  - [ ] Click: "Buy Pack of 10 for $29"
  - [ ] Complete Stripe checkout
  - [ ] Verify: Credits are added to account
  - [ ] Verify: Credit balance shows on job page

- [ ] **Use Credits for Download**
  - [ ] Upload file
  - [ ] Verify: "Use 1 Credit to Download" button appears
  - [ ] Click button
  - [ ] Verify: Download works without payment
  - [ ] Verify: Credit balance decreases by 1

---

## 🚨 5. CRITICAL PATH TEST (Full User Journey)

- [ ] **Complete Flow: New User → Free File → Second File → Payment**
  1. **New User (Free File)**
     - [ ] Visit homepage (not logged in)
     - [ ] Upload PDF
     - [ ] See preview with watermark
     - [ ] See sample rows table
     - [ ] Click "Pay $9" → Get free file
     - [ ] Download CSV and QBO successfully

  2. **Second File (Payment Required)**
     - [ ] Upload second PDF (same or different email)
     - [ ] See preview
     - [ ] Click "Pay $9" → Stripe Checkout opens
     - [ ] Complete payment
     - [ ] Download files successfully

  3. **Verification**
     - [ ] Check Stripe dashboard: Only 1 payment recorded (for second file)
     - [ ] Verify: First file was free (no Stripe payment)
     - [ ] Verify: Both files downloaded correctly
     - [ ] Verify: CSV and QBO files are valid

---

## 📝 TESTING NOTES

### Test Data
- Use real bank statement PDFs (anonymized if needed)
- Test with various formats (Chase, BofA, Citi, etc.)
- Test with different date ranges and transaction counts

### Expected Results
- **Processing Time**: < 30 seconds for typical PDF
- **Success Rate**: > 90% for standard bank statement PDFs
- **CSV Quality**: All dates, amounts, descriptions parse correctly
- **Free First File**: Works for new emails, requires payment for returning users

### Issues to Watch For
- ❌ Processing fails unexpectedly
- ❌ Debit/credit values in wrong columns
- ❌ Dates parsing as 1900 or invalid years
- ❌ Descriptions split across multiple columns (tab issue)
- ❌ Free first file not working (charges payment)
- ❌ Payment succeeds but download doesn't work
- ❌ Preview files not loading
- ❌ Sample rows table not showing

---

## ✅ SIGN-OFF

**Tester:** _________________  
**Date:** _________________  
**Environment:** Production (quicksync.app)  
**Overall Status:** ☐ PASS  ☐ FAIL  ☐ NEEDS WORK

**Critical Issues Found:** _________________  
**Minor Issues Found:** _________________  
**Notes:** _________________

---

**Next Steps:**
- If all tests pass → Proceed with remaining strategic plan implementation
- If critical issues found → Fix before proceeding
- If minor issues found → Document and fix in next iteration

