# Pricing Model

## Overview

The service uses a pay-per-file model with optional credit packs for bulk usage.

## Pricing Tiers

### Single File: $9
- One-time payment per file conversion
- Includes both CSV and QBO formats
- Preview results before payment
- Best for occasional users

### Pack of 10: $29 (Save $61)
- Purchase 10 credits upfront
- Credits can be used anytime
- Each download costs 1 credit
- Best for regular users or businesses

## Payment & Credits System

### How Credits Work

1. **Purchase**: User buys a pack of 10 credits for $29
2. **Storage**: Credits are stored in the user's account (Credits table)
3. **Redemption**: When downloading a file, user can choose:
   - Pay $9 (single file payment)
   - Use 1 credit (if available)
4. **Atomic Operation**: Credit redemption is atomic (database transaction) to prevent race conditions

### Unified Download Rule

A file is downloadable if **either**:
- Job has `paidAt` timestamp (direct payment via Stripe)
- User has >= 1 credit available (credits will be redeemed on download)

**Never trust the client** - All checks happen server-side in the download endpoint.

### Credit Redemption Flow

1. User clicks download button
2. Frontend calls `/api/download/[id]/[format]`
3. Server checks:
   - Is job paid? → Allow download
   - Does user have credits? → Redeem 1 credit atomically, then allow download
   - Neither? → Return 402 Payment Required
4. On successful credit redemption:
   - Credit balance decremented (atomic)
   - Job marked with `creditRedeemedAt` timestamp
   - File served

## Implementation Details

### Database Schema

```prisma
model Credit {
  id          String   @id @default(uuid())
  userId      String   @unique
  balance     Int      @default(0)
  source      String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

### API Endpoints

- `POST /api/payment/purchase-credits` - Create Stripe checkout for credit pack
- `GET /api/user/credits` - Get user's credit balance
- `GET /api/download/[id]/[format]` - Download file (checks payment OR credits)

### Stripe Integration

- **Single File**: Uses existing `/api/payment/create-checkout` endpoint
- **Credit Pack**: Uses `/api/payment/purchase-credits` endpoint
- **Webhook**: Handles both purchase types via `checkout.session.completed` event
  - Checks `metadata.purchaseType` field
  - If `credit_pack`, adds credits to user account
  - If `job`, marks job as paid

## Environment Variables

```env
PRICE_PER_FILE=900        # $9.00 in cents
PRICE_PACK_10=2900        # $29.00 in cents
NEXT_PUBLIC_PRICE_PER_FILE=900
```

## Future Enhancements

- Subscription plans (monthly credits)
- Larger packs (50, 100 credits)
- Credit expiration (optional)
- Promo codes for free credits

