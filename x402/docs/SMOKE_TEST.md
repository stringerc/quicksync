# Smoke Test Checklist

## Pre-Deployment Tests

### 1. Authentication Flow
- [ ] Sign in with email → Receive magic link
- [ ] Click magic link → Redirected and authenticated
- [ ] Token persists on page refresh
- [ ] Logout works

### 2. Upload Flow
- [ ] Upload PDF file
- [ ] File validates (PDF only)
- [ ] Redirects to job page
- [ ] Processing starts automatically
- [ ] Job status updates correctly

### 3. Processing & Preview
- [ ] Processing completes (status: completed or needs_review)
- [ ] Confidence score displayed
- [ ] Validation summary shows:
  - Row count
  - Date range
  - Totals (debit, credit, balance)
- [ ] Preview visible BEFORE payment option

### 4. Payment Flow (Single File)
- [ ] "Pay $9" button appears when unpaid
- [ ] Clicking button opens Stripe Checkout
- [ ] Complete payment with test card (4242 4242 4242 4242)
- [ ] Redirected back to job page
- [ ] Payment status updated to "paid"
- [ ] Download buttons appear

### 5. Credit Pack Purchase
- [ ] Navigate to purchase credits (if link exists)
- [ ] Create checkout for $29 pack
- [ ] Complete payment
- [ ] Credits added to account (10 credits)
- [ ] Credit balance visible on job page

### 6. Credit Redemption
- [ ] Upload new file (or use existing unpaid file)
- [ ] Complete processing
- [ ] "Use 1 Credit" button appears
- [ ] Click download → Credit redeemed
- [ ] Credit balance decreases by 1
- [ ] File downloads successfully

### 7. Download Flow
- [ ] Download CSV works (paid or credit)
- [ ] Download QBO works (paid or credit)
- [ ] File format is correct
- [ ] Filename is appropriate

### 8. B3: No-Pay-For-Failed Logic
- [ ] Upload file that fails parsing
- [ ] Status shows "failed"
- [ ] Payment button NOT shown
- [ ] "Request Review" button appears
- [ ] Upload file with low confidence (< 70%)
- [ ] Status shows "needs_review"
- [ ] Payment button NOT shown (blocked)
- [ ] Warning message displayed

### 9. Request Review
- [ ] Click "Request Review" button
- [ ] Review requested successfully
- [ ] Button shows "Review Requested" (disabled)

### 10. Support Token
- [ ] Support token (job ID) visible on all error states
- [ ] Copy button works
- [ ] Token copied to clipboard

## Post-Deployment Tests

### 11. Stripe Webhook
- [ ] Complete payment in test mode
- [ ] Check Stripe Dashboard → Webhooks → Recent events
- [ ] Verify `checkout.session.completed` received
- [ ] Verify payment status updated in database
- [ ] Complete credit pack purchase
- [ ] Verify credits added to user account

### 12. Storage (Production)
- [ ] Files upload to S3/R2
- [ ] Files can be downloaded from S3/R2
- [ ] File paths stored correctly in database

### 13. Analytics (If Configured)
- [ ] Plausible script loads (check browser console)
- [ ] Events tracked (upload_started, download_completed, etc.)
- [ ] Events visible in Plausible dashboard

## Error Scenarios

### 14. Edge Cases
- [ ] Upload non-PDF file → Error message
- [ ] Download without payment/credits → 402 error
- [ ] Download with insufficient credits → 402 error
- [ ] Process already-paid job → Works
- [ ] Multiple simultaneous downloads → Handles correctly

### 15. Admin View
- [ ] Access `/api/admin/jobs` with admin email
- [ ] See last 50 jobs
- [ ] Non-admin email → 403 error
- [ ] Review requested jobs visible

## Critical Path Test (End-to-End)

### Happy Path
1. Sign in
2. Upload PDF
3. Wait for processing
4. Preview results (confidence > 70%)
5. Pay $9
6. Download CSV
7. Verify file contents

### Credit Path
1. Purchase credit pack ($29)
2. Upload PDF
3. Process file
4. Use 1 credit to download
5. Verify credit balance decreased

### Failed Parse Path
1. Upload problematic PDF
2. Processing fails or low confidence
3. Verify payment blocked
4. Request review
5. Verify review requested

## Performance Checks
- [ ] Page loads in < 2 seconds
- [ ] Upload completes in < 10 seconds (for small PDFs)
- [ ] Processing completes in < 30 seconds (for typical statements)
- [ ] Download completes quickly

## Browser Compatibility
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] Mobile (iOS Safari, Chrome)

## Notes
- Use Stripe test mode for all payment tests
- Test with various PDF formats (different banks)
- Verify all console errors are expected/acceptable
- Check Vercel function logs for errors

