# Conversion Flow Audit

## Current User Flow

1. **Landing Page** (`/`) → Login form (email input)
2. **Email → Magic Link** → Click link → Redirected to `/` (authenticated)
3. **Authenticated Home** → Upload form + Job list (placeholder)
4. **Upload PDF** → Redirect to `/jobs/[id]`
5. **Job Page** → Shows status, payment button ($2.99), processing, download
6. **Payment** → Stripe Checkout → Redirect back to job page
7. **Process** → Auto-triggered after payment or manual
8. **Download** → CSV/QBO download buttons

## Friction Points Identified

### 🔴 CRITICAL: Top 3 Friction Points

1. **Payment Before Preview** (HIGHEST FRICTION)
   - User must pay $2.99 BEFORE seeing if the parse worked
   - No confidence score preview before payment
   - If parse fails, user paid for nothing
   - **Impact**: High abandonment, refund requests
   - **Location**: Job page forces payment before processing

2. **No Clear Value Proposition on Landing**
   - Generic "PDF to CSV Converter" title
   - No clear benefit statement
   - No "what you get" section
   - No pricing visible
   - **Impact**: Users don't understand value before signing up
   - **Location**: Landing page is just a login form

3. **Unclear Process / No "How It Works"**
   - No explanation of the 3-step process
   - User doesn't know what happens after upload
   - Payment requirement not explained upfront
   - **Impact**: User confusion, drop-off
   - **Location**: Missing from landing page

### ⚠️ MEDIUM Priority Friction Points

4. **No Pricing Visibility**
   - Price only visible on job page ($2.99)
   - No pricing tiers or options
   - No "pack" discounts mentioned
   - **Impact**: Price shock, abandonment

5. **Failed Parses Still Require Payment**
   - If confidence < 70, job marked "needs_review"
   - But payment button still shown
   - No clear "don't pay if uncertain" messaging
   - **Impact**: Users pay for unusable outputs

6. **No FAQ / Trust Signals**
   - No data security/privacy info
   - No refund policy
   - No supported formats list
   - **Impact**: Lack of trust, abandonment

## Recommended Solutions (Phase B)

1. ✅ **Preview Before Payment** (B3)
   - Process file immediately after upload (or on payment)
   - Show confidence score and summary BEFORE payment
   - Block payment if confidence too low or failed
   - Show "Request Review" instead of payment button

2. ✅ **Conversion-Focused Landing Page** (B1)
   - Clear headline: "Turn bank/credit card PDFs into clean QuickBooks-ready files"
   - "What you get" bullets
   - Pricing section
   - FAQ section
   - "How it works" 3-step visual

3. ✅ **Credits System** (B2)
   - Add "Pack of 10" option ($29)
   - Allow credit redemption for downloads
   - Better pricing visibility

4. ✅ **Trust Signals** (B1)
   - Data handling note
   - Security/privacy FAQ
   - Refund policy
   - Supported formats

## Metrics to Track (Phase C)

- upload_started
- upload_completed  
- job_ready (confidence score shown)
- checkout_started
- paid_confirmed
- download_completed
- parse_failed
- credit_pack_purchased

