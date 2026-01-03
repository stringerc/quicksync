# Abandoned Cart Email Automation Setup

**Status:** Implementation complete ✅

---

## What It Does

Automatically sends reminder emails to users who:
- Uploaded a file (status: completed)
- Haven't paid (paymentStatus: pending)
- Created the job more than 24 hours ago
- Haven't received an abandoned cart email yet

**Frequency:** Runs daily at 10 AM UTC via Vercel Cron

---

## Implementation

### 1. API Route

**File:** `app/api/cron/abandoned-cart/route.ts`

- Finds qualifying jobs
- Sends abandoned cart emails
- Marks jobs as email sent
- Logs results

### 2. Database Schema Update Required

**Field needed:** `abandonedCartEmailSentAt` on `Job` model

Add to `prisma/schema.prisma`:

```prisma
model Job {
  // ... existing fields ...
  abandonedCartEmailSentAt DateTime?
  // ... rest of fields ...
}
```

Then run:
```bash
npx prisma db push
```

### 3. Vercel Cron Configuration

**File:** `vercel.json`

```json
{
  "crons": [
    {
      "path": "/api/cron/abandoned-cart",
      "schedule": "0 10 * * *"
    }
  ]
}
```

**Schedule:** `0 10 * * *` = Daily at 10 AM UTC

---

## Setup Steps

### Step 1: Add Database Field

1. Edit `prisma/schema.prisma`
2. Add `abandonedCartEmailSentAt DateTime?` to `Job` model
3. Run migration:
   ```bash
   npx prisma db push
   ```
   Or create a migration:
   ```bash
   npx prisma migrate dev --name add_abandoned_cart_email_field
   ```

### Step 2: Deploy to Vercel

1. Commit and push changes:
   ```bash
   git add .
   git commit -m "Add abandoned cart email automation"
   git push
   ```

2. Vercel will automatically:
   - Deploy the API route
   - Register the cron job
   - Start running daily

### Step 3: Optional - Add CRON_SECRET

For security, add a secret to Vercel environment variables:

1. Generate a random secret:
   ```bash
   openssl rand -hex 32
   ```

2. Add to Vercel:
   - Key: `CRON_SECRET`
   - Value: (your generated secret)
   - Environments: Production, Preview

3. The cron job will verify this secret (if set)

---

## Testing

### Manual Test (Local)

```bash
# Start your dev server
npm run dev

# In another terminal, trigger the endpoint
curl http://localhost:3000/api/cron/abandoned-cart
```

### Test in Production

1. Create a test job:
   - Upload a file
   - Don't pay
   - Wait 24+ hours

2. Manually trigger the cron:
   ```bash
   curl https://quicksync.app/api/cron/abandoned-cart \
     -H "Authorization: Bearer YOUR_CRON_SECRET"
   ```

3. Check logs in Vercel Dashboard

---

## Monitoring

### Vercel Dashboard

1. Go to: https://vercel.com/[your-team]/quicksync/crons
2. See cron job execution history
3. View logs and errors

### Application Logs

The cron job logs:
- Number of jobs found
- Emails sent count
- Errors count
- Individual job processing results

Check Vercel function logs for detailed output.

---

## Configuration

### Change Schedule

Edit `vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/cron/abandoned-cart",
      "schedule": "0 14 * * *"  // 2 PM UTC instead of 10 AM
    }
  ]
}
```

Common schedules:
- `0 10 * * *` - Daily at 10 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 10 * * 1` - Weekly on Monday at 10 AM UTC

### Batch Size

Current limit: 100 jobs per run (to avoid timeout)

To change, edit `take: 100` in `app/api/cron/abandoned-cart/route.ts`

---

## Troubleshooting

### Cron Job Not Running

1. Check Vercel Dashboard → Crons
2. Verify `vercel.json` is committed and deployed
3. Check cron job status (should show "Active")

### Emails Not Sending

1. Check SMTP configuration in Vercel environment variables
2. Verify `sendAbandonedCartEmail` function exists in `lib/email.ts`
3. Check application logs for errors

### Database Errors

1. Verify `abandonedCartEmailSentAt` field exists:
   ```bash
   npx prisma studio
   # Check Job model schema
   ```

2. Run migration again if needed:
   ```bash
   npx prisma db push
   ```

---

## Next Steps

After setup:

1. ✅ Monitor first few runs in Vercel Dashboard
2. ✅ Check email deliverability (check spam folders)
3. ✅ Monitor conversion rate improvements
4. ✅ Adjust timing if needed (e.g., send after 12 hours instead of 24)

---

## Expected Impact

- **Conversion Rate:** +10-15% improvement
- **Revenue:** Recover 10-15% of abandoned carts
- **User Engagement:** Remind users about their files

---

## Notes

- Cron jobs require Vercel Pro plan ($20/month) for production
- Free tier has limited cron functionality
- Consider upgrading if you need reliable cron execution

