# Preview-First Flow Implementation - Changes Summary

## Overview

This document summarizes all code changes made to implement the preview-before-payment flow.

## Database Schema Changes

### Updated `Job` Model

- `userId`: Changed from `String` to `String?` (nullable) - allows anonymous jobs
- `sessionId`: New field `String?` - temporary session ID for anonymous jobs
- `previewCsvFilePath`: New field `String?` - path to watermarked CSV preview
- `previewQboFilePath`: New field `String?` - path to watermarked QBO preview
- `user` relation: Changed to optional (`User?`)

## New Files

### `lib/watermark.ts`
- `addWatermarkToPDF()`: Adds diagonal watermark to PDF buffers using pdf-lib
- `addWatermarkToCSV()`: Creates HTML preview with CSS watermark overlay for CSV data

### `app/api/preview/[id]/[format]/route.ts`
- New endpoint to serve watermarked preview files
- No authentication required (uses sessionId for anonymous jobs)
- Returns HTML (for CSV) or PDF (for QBO) previews

### `scripts/run_migration.sh`
- Helper script to run database migrations
- Checks for DATABASE_URL environment variable

## Modified Files

### `app/api/upload/route.ts`
**Changes:**
- Removed authentication requirement
- Supports anonymous uploads via `sessionId`
- Returns `sessionId` in response for anonymous jobs
- Logging includes sessionId for anonymous jobs

**Flow:**
- If user authenticated: Creates job with `userId`
- If not authenticated: Creates job with `sessionId` (userId = null)

### `app/api/process/route.ts`
**Changes:**
- Authentication now optional (supports anonymous jobs)
- Accepts `sessionId` in request body for anonymous jobs
- Generates watermarked preview files (CSV HTML + QBO PDF)
- Stores preview file paths in database
- Access control: userId OR sessionId must match

**New Behavior:**
- Generates clean files (csvFilePath, qboFilePath) as before
- Also generates preview files (previewCsvFilePath, previewQboFilePath) with watermarks

### `app/api/payment/create-checkout/route.ts`
**Changes:**
- Accepts `email` and `sessionId` in request body
- Creates/finds user by email for anonymous jobs
- Links anonymous job to user before payment
- Pre-fills email in Stripe Checkout via `customer_email`

**Flow:**
1. If job is anonymous (no userId), requires email
2. Creates/finds user by email
3. Links job to user
4. Creates Stripe Checkout with email pre-filled

### `app/api/payment/webhook/route.ts`
**Fix:**
- Added missing `purchaseType` variable declaration

## Dependencies Added

- `pdf-lib`: For PDF watermarking functionality

## Migration Steps

### 1. Run Database Migration

```bash
# Option 1: Using the script (recommended)
./scripts/run_migration.sh

# Option 2: Manual
export DATABASE_URL="your-production-database-url"
npx prisma generate
npx prisma db push
```

**What this does:**
- Makes `userId` nullable in `jobs` table
- Adds `session_id` column
- Adds `preview_csv_file_path` column
- Adds `preview_qbo_file_path` column
- Updates foreign key constraints

### 2. Install Dependencies

```bash
npm install
# pdf-lib should already be installed
```

### 3. Deploy Code Changes

```bash
git add .
git commit -m "Implement preview-first flow with watermarking"
git push
# Or: vercel --prod
```

## New User Flow

### Before (Pay-First)
1. Login with email → Magic link
2. Upload PDF
3. Pay $9
4. Process & Download

### After (Preview-First)
1. Upload PDF (no login required)
2. Processing starts automatically
3. View watermarked preview
4. Enter email + Pay $9
5. Download clean files

## Frontend Changes Needed

The frontend components need updates to:

1. **Landing Page (`app/page.tsx`)**:
   - Remove login requirement
   - Show upload form immediately
   - No authentication needed

2. **Upload Component (`components/UploadForm.tsx`)**:
   - Don't require token/auth
   - Store `sessionId` from upload response
   - Redirect to job page with sessionId

3. **Job Page (`app/jobs/[id]/page.tsx`)**:
   - Show preview iframe/embed for watermarked files
   - Show "Download Clean Version" button
   - Collect email before payment (if anonymous)
   - Pass email + sessionId to payment endpoint

## Testing Checklist

- [ ] Upload without authentication works
- [ ] Preview files are generated with watermarks
- [ ] Preview endpoint serves watermarked files
- [ ] Payment flow collects email for anonymous jobs
- [ ] Jobs are linked to users after payment
- [ ] Clean downloads work after payment
- [ ] Authenticated users still work (backward compatible)

## Rollback Plan

If issues arise:

1. **Database**: Revert schema changes (make userId required again)
2. **Code**: Revert to previous commit
3. **Note**: Anonymous jobs created before rollback will need manual cleanup

## Performance Considerations

- Watermarking adds ~100-200ms to processing time
- Preview files use additional storage space
- Consider cleanup job for old preview files (>7 days)

## Security Considerations

- Session IDs are 21 characters (nanoid) - secure enough for temporary access
- Preview files should expire after 24-48 hours (not yet implemented)
- Anonymous jobs should be cleaned up after 7 days (not yet implemented)
- Rate limiting recommended for anonymous uploads (not yet implemented)

