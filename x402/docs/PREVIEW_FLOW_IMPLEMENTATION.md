# Preview-Before-Payment Flow Implementation Plan

## Overview

This document outlines the implementation plan for changing QuickSync from a "pay-first" to a "preview-first" conversion flow.

## Current Flow (Pay-First)

1. User must login/authenticate
2. Upload PDF
3. Process (optional preview)
4. Pay $9
5. Download files

**Problems:**
- High friction (auth required before seeing value)
- Payment before seeing if parse works
- Lower conversion rates

## New Flow (Preview-First)

1. **Upload** (NO authentication required)
   - User uploads PDF directly
   - Create anonymous job (temporary ID)
   - Process immediately

2. **Preview** (Watermarked)
   - Show preview with watermark overlay
   - Display: Row count, date range, totals, confidence score
   - Preview is readable but clearly marked as "PREVIEW"

3. **Download Clean Version**
   - Button: "Download Clean Files - $9"
   - Prompts for email (creates account if needed)
   - Stripe Checkout
   - After payment: Download clean files

## Benefits

- **Lower friction**: No login required to try
- **Higher conversion**: Users see value before paying
- **Better UX**: Natural flow (try → see value → decide)
- **Industry standard**: Matches best practices (Canva, Figma, etc.)

## Technical Implementation

### Phase 1: Remove Auth from Upload

1. Modify `/api/upload`:
   - Remove `getCurrentUser` requirement
   - Create anonymous job (generate temp UUID or use session)
   - Store in Job table with `userId` as NULL or temp ID

2. Modify `/api/process`:
   - Accept job ID without auth
   - Process and generate files
   - Create watermarked preview versions

### Phase 2: Watermarking

1. Install `pdf-lib`:
   ```bash
   npm install pdf-lib
   ```

2. Create watermark utility (`lib/watermark.ts`):
   - Function: `addWatermark(pdfBuffer, text, opacity)`
   - Diagonal watermark across pages
   - Text: "PREVIEW - quicksync.app"
   - Opacity: 30-40%

3. For CSV preview:
   - Generate HTML table with watermark overlay (CSS)
   - Or generate PDF from CSV with watermark

### Phase 3: Preview Endpoint

1. Create `/api/preview/[id]/[format]`:
   - Returns watermarked version
   - No auth required
   - Public access (but temporary/expiring URLs)

2. Update job page:
   - Show preview iframe/embed
   - "Download Clean Version" button

### Phase 4: Payment on Download

1. Modify `/api/payment/create-checkout`:
   - Accept email in request
   - Create/find user by email
   - Link job to user
   - Create checkout session

2. Modify `/api/download`:
   - After payment, serve clean files
   - Link job to user account

### Phase 5: Email Collection

1. Update job page:
   - Add email input before payment
   - Or collect in Stripe Checkout metadata

2. User association:
   - When payment succeeds, link job to user
   - Send magic link to email

## Database Changes

### Option A: Anonymous Jobs (Recommended)

Add to `Job` model:
```prisma
userId String? @map("user_id")  // Make nullable
sessionId String? @map("session_id")  // Temporary session
```

### Option B: Temporary User IDs

Use a special "anonymous" user or session-based IDs.

## Security Considerations

1. **Preview URLs**: Use expiring tokens (24-48 hours)
2. **Job cleanup**: Delete anonymous jobs after 7 days
3. **Rate limiting**: Prevent abuse of anonymous uploads
4. **File size limits**: Enforce on upload

## Migration Strategy

1. Make `userId` nullable in schema
2. Add `sessionId` field
3. Run migration
4. Deploy code changes incrementally
5. Test thoroughly before full rollout

## Watermark Implementation Details

### PDF Watermarking (pdf-lib)

```typescript
import { PDFDocument, rgb } from 'pdf-lib'

async function addWatermark(pdfBuffer: Buffer, text: string): Promise<Buffer> {
  const pdfDoc = await PDFDocument.load(pdfBuffer)
  const pages = pdfDoc.getPages()
  
  for (const page of pages) {
    const { width, height } = page.getSize()
    
    // Diagonal watermark
    page.drawText(text, {
      x: width / 4,
      y: height / 2,
      size: 48,
      color: rgb(0.7, 0.7, 0.7),
      opacity: 0.3,
      rotate: { angleInRadians: -0.785 }, // -45 degrees
    })
  }
  
  return Buffer.from(await pdfDoc.save())
}
```

### CSV Preview (HTML with CSS overlay)

```html
<div style="position: relative;">
  <table><!-- CSV data --></table>
  <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; opacity: 0.3;">
    <div style="transform: rotate(-45deg); font-size: 48px; color: gray;">
      PREVIEW - quicksync.app
    </div>
  </div>
</div>
```

## Testing Checklist

- [ ] Upload without auth works
- [ ] Preview shows watermark clearly
- [ ] Watermark cannot be easily removed
- [ ] Payment flow collects email
- [ ] Clean download works after payment
- [ ] Job links to user after payment
- [ ] Anonymous jobs cleaned up after expiry
- [ ] Rate limiting works

## Rollout Plan

1. **Week 1**: Implement watermarking (keep current flow)
2. **Week 2**: Add preview endpoint
3. **Week 3**: Remove auth from upload (test thoroughly)
4. **Week 4**: Full rollout

## Metrics to Track

- Upload conversion rate (visitors → uploads)
- Preview → Payment conversion rate
- Time to payment (faster = better)
- Refund rate (should decrease)
- Support tickets (should decrease)

