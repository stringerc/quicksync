# Phase B & C - Conversion & Growth - COMPLETE ✅

## Summary

Phases B and C focused on maximizing conversion and reducing purchase friction. All critical conversion blockers have been addressed.

## Phase B: Conversion Page + Simple Pricing ✅

### B0: Conversion Audit ✅
- Created `/docs/CONVERSION_AUDIT.md` identifying top 3 friction points
- Documented current user flow and pain points

### B1: Landing Page Rebuilt ✅
- **New conversion-focused landing page** with:
  - Clear headline: "Turn bank/credit card PDFs into clean QuickBooks-ready files"
  - Subheadline emphasizing time saved
  - Upload component above the fold
  - "What you get" section (CSV+QBO, validation, pay-only-when-ready)
  - "How it works" 3-step visual
  - Supported documents section (honest, narrow scope)
  - Pricing section ($9 single, $29 pack of 10)
  - FAQ section (security, accuracy, refunds, formats)
  - Data handling note (private, auto-delete, no sale)

### B2: Pricing Implementation ✅
- **Credits system implemented**:
  - Credits table in Prisma schema
  - Credit purchase endpoint (`/api/payment/purchase-credits`)
  - Credit redemption (atomic transaction)
  - Unified download rule: paid OR credits
  - Credit balance API endpoint

- **Stripe integration**:
  - Single file: $9 (updated from $2.99)
  - Pack of 10: $29
  - Webhook handles both purchase types
  - Metadata distinguishes purchase types

- **UI updates**:
  - Job page shows credit balance
  - "Use 1 Credit" button when credits available
  - "Pay $9" button when no credits
  - Credit balance displayed prominently

### B3: Refund/Failure Handling ✅
- **No-pay-for-failed logic**:
  - Payment blocked if status = "failed"
  - Payment blocked if confidence < 70% or status = "needs_review"
  - Warning message: "Don't pay yet"
  - "Request Review" button instead of payment

- **Request Review endpoint**:
  - `POST /api/jobs/[id]/request-review`
  - Sets `reviewRequestedAt` timestamp
  - Admin can see review requests

- **Auto-processing on upload**:
  - Files process automatically after upload
  - Users see preview BEFORE payment
  - Payment only required for download

## Phase C: Growth Plumbing ✅

### C1: Tracking (Plausible) ✅
- Analytics utility created (`lib/analytics.ts`)
- Plausible script added to layout (env-gated)
- Events tracked:
  - upload_started
  - upload_completed
  - job_ready
  - checkout_started
  - paid_confirmed
  - credit_pack_purchased
  - download_completed
  - parse_failed
- Privacy-safe: No-ops if domain not configured

### C2: Bookkeepers Landing Page ✅
- New `/bookkeepers` page
- Tailored copy for bookkeepers/firms
- "If it needs review, don't pay" messaging
- Same upload component
- "Firm pack coming soon" mention (honest)

### C3: Growth Kit ✅
- Created `/growth` folder with:
  - `linkedin_dm.md` (3 variants)
  - `email_outreach.md` (3 variants)
  - `facebook_groups_post.md` (3 variants)
  - `reddit_post.md` (2 variants)
- All templates:
  - Outcome-based
  - Short, no fluff
  - Include "free first file" offer
  - Privacy/security disclaimer

## Documentation Updates ✅

- `docs/CONVERSION_AUDIT.md` - Conversion flow analysis
- `docs/PRICING.md` - Complete pricing model documentation
- `docs/SMOKE_TEST.md` - Comprehensive test checklist
- `DEPLOYMENT.md` - Updated with new env vars
- `.env.example` - Updated with pricing and analytics vars

## Database Migration Required

Run migration to add new tables/fields:

```bash
npx prisma db push
```

New schema:
- `Credit` table (userId, balance, source, timestamps)
- `Job.creditRedeemedAt` field
- `Job.reviewRequestedAt` field

## Files Created/Modified

### New Files
- `lib/credits.ts` - Credit management utilities
- `lib/analytics.ts` - Plausible tracking utility
- `app/api/payment/purchase-credits/route.ts` - Credit pack checkout
- `app/api/user/credits/route.ts` - Credit balance endpoint
- `app/api/jobs/[id]/request-review/route.ts` - Review request endpoint
- `app/bookkeepers/page.tsx` - Bookkeepers landing page
- `docs/CONVERSION_AUDIT.md` - Conversion analysis
- `docs/PRICING.md` - Pricing documentation
- `docs/SMOKE_TEST.md` - Test checklist
- `growth/*.md` - Outbound templates

### Modified Files
- `app/page.tsx` - Complete landing page rebuild
- `app/jobs/[id]/page.tsx` - Credits UI, B3 logic, analytics
- `components/UploadForm.tsx` - Auto-process, analytics
- `app/api/payment/webhook/route.ts` - Credit pack handling
- `app/api/payment/create-checkout/route.ts` - Updated price
- `app/api/download/[id]/[format]/route.ts` - Credit redemption
- `app/api/process/route.ts` - Removed payment requirement
- `app/api/jobs/[id]/route.ts` - Credit balance in response
- `app/layout.tsx` - Plausible script
- `lib/stripe.ts` - Updated prices
- `prisma/schema.prisma` - Credits table, new Job fields

## Environment Variables Added

```env
# Pricing
PRICE_PER_FILE=900
PRICE_PACK_10=2900

# Analytics (optional)
NEXT_PUBLIC_PLAUSIBLE_DOMAIN="your-domain.com"
```

## Key Changes Summary

### Conversion Improvements
1. ✅ Preview before payment (auto-process on upload)
2. ✅ Clear value proposition on landing page
3. ✅ Pricing visible upfront
4. ✅ No payment for failed/low-confidence parses
5. ✅ Credits system for bulk usage
6. ✅ Trust signals (FAQ, data handling)

### User Experience
- Landing page clearly explains value
- 3-step process visual
- Pricing tiers visible
- Credit balance always shown
- Support token on all error states

### Payment Flow
- Upload → Auto-process → Preview → Pay → Download
- Credits can be used instead of payment
- Payment blocked for failed/uncertain parses

## Testing Checklist

See `docs/SMOKE_TEST.md` for complete testing guide.

Critical tests:
- [ ] Upload → Auto-process → Preview
- [ ] Payment flow ($9 single file)
- [ ] Credit pack purchase ($29)
- [ ] Credit redemption
- [ ] Payment blocked for failed/low-confidence
- [ ] Request review functionality

## Next Steps

1. Run database migration: `npx prisma db push`
2. Update environment variables
3. Configure Plausible (optional)
4. Test end-to-end flows
5. Deploy to production
6. Use growth kit templates for outreach

## Known Limitations

- Credit pack purchase link not yet added to UI (can be added to landing page or user dashboard)
- Firm pack (bulk) not implemented yet
- Subscription plans deferred
- Analytics requires Plausible domain setup

