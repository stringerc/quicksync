# Deployment Guide

## Vercel Deployment

### Prerequisites

1. Vercel account (free tier works)
2. GitHub repository with your code
3. Stripe account (test mode for development)
4. PostgreSQL database (Vercel Postgres or external)
5. S3-compatible storage (AWS S3 or Cloudflare R2)

### Step 1: Deploy to Vercel

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com) and import your repository
3. Vercel will auto-detect Next.js settings

### Step 2: Environment Variables

Add these environment variables in Vercel Dashboard → Settings → Environment Variables:

#### Required

```env
# Database (PostgreSQL)
DATABASE_URL="postgresql://user:password@host:5432/dbname"
# Or use Vercel Postgres and copy the connection string

# Storage (S3-compatible)
STORAGE_TYPE="s3"
AWS_ACCESS_KEY_ID="your-access-key"
AWS_SECRET_ACCESS_KEY="your-secret-key"
AWS_REGION="us-east-1"
AWS_S3_BUCKET="your-bucket-name"

# For Cloudflare R2:
# AWS_S3_ENDPOINT="https://<account-id>.r2.cloudflarestorage.com"
# AWS_REGION="auto"
# AWS_S3_BUCKET="your-bucket-name"

# Stripe
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_PUBLISHABLE_KEY="pk_live_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_..."

# Auth
JWT_SECRET="generate-a-random-secret-here"
NEXT_PUBLIC_APP_URL="https://your-app.vercel.app"

# Pricing
PRICE_PER_FILE=900
PRICE_PACK_10=2900
NEXT_PUBLIC_PRICE_PER_FILE=900

# Admin (comma-separated)
ADMIN_EMAILS="your-email@example.com"

# Analytics (optional)
NEXT_PUBLIC_PLAUSIBLE_DOMAIN="your-domain.com"
```

#### Optional (for email magic links)

```env
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASS="your-app-password"
```

### Step 3: Database Setup

#### Option A: Vercel Postgres (Recommended)

1. In Vercel Dashboard, go to Storage tab
2. Create a Postgres database
3. Copy the `POSTGRES_URL` connection string
4. Use it as `DATABASE_URL` (may need to adjust format)

#### Option B: External PostgreSQL

Use any PostgreSQL provider (Railway, Supabase, Neon, etc.) and provide the connection string.

#### Run Migrations

After deployment, run Prisma migrations:

```bash
# In your local terminal (or use Vercel CLI)
npx prisma migrate deploy
# Or push the schema
npx prisma db push
```

### Step 4: S3 Storage Setup

#### Option A: AWS S3

1. Create an S3 bucket in AWS Console
2. Create an IAM user with S3 permissions
3. Get access key ID and secret access key
4. Set environment variables as shown above

#### Option B: Cloudflare R2 (Recommended - Cheaper)

1. Create R2 bucket in Cloudflare Dashboard
2. Create API token with R2 permissions
3. Get Account ID from dashboard
4. Set environment variables:
   - `AWS_S3_ENDPOINT="https://<account-id>.r2.cloudflarestorage.com"`
   - `AWS_REGION="auto"`
   - Use R2 API token credentials as `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

### Step 5: Stripe Webhook Setup

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://your-app.vercel.app/api/payment/webhook`
4. Select events to listen to:
   - `checkout.session.completed` (handles both single file and credit pack purchases)
   - `payment_intent.succeeded` (backup verification)
5. Copy the webhook signing secret → set as `STRIPE_WEBHOOK_SECRET`

**Important**: Use the webhook secret from the exact endpoint you created (test vs live mode have different secrets).

### Step 6: Deploy and Verify

1. Push a commit or trigger a deployment
2. Visit your app URL
3. Test the flow:
   - Sign up with email
   - Upload a test PDF
   - Complete payment (use Stripe test card: `4242 4242 4242 4242`)
   - Verify processing and download works

### Step 7: Production Checklist

- [ ] Database migrations applied
- [ ] S3 bucket accessible and configured
- [ ] Stripe webhook endpoint responding (check Stripe Dashboard → Webhooks → Recent events)
- [ ] Test payment flow end-to-end
- [ ] Admin email configured
- [ ] JWT_SECRET is a strong random value
- [ ] All environment variables set correctly
- [ ] Error logging working (check Vercel logs)

## Troubleshooting

### Files Not Uploading

- Check S3 credentials and bucket permissions
- Verify `STORAGE_TYPE="s3"` is set
- Check Vercel function logs for errors

### Payments Not Processing

- Verify Stripe webhook endpoint is accessible
- Check webhook secret matches Stripe dashboard
- Review Stripe Dashboard → Webhooks → Recent events for errors
- Check database for payment status updates

### Database Errors

- Verify `DATABASE_URL` format is correct
- Ensure migrations have run
- Check database connection limits

### Admin View Not Working

- Verify `ADMIN_EMAILS` includes your email
- Check email matches exactly (case-sensitive)
- Review API logs for 403 errors

## Security Notes

1. **Never commit `.env` files** - Use Vercel environment variables
2. **Use strong JWT_SECRET** - Generate with: `openssl rand -base64 32`
3. **Rotate secrets regularly** - Especially after team member changes
4. **Monitor webhook logs** - Check for failed payments or suspicious activity
5. **S3 bucket permissions** - Use private buckets, don't enable public access

## Monitoring

- Check Vercel Dashboard → Functions for API route logs
- Monitor Stripe Dashboard for payment issues
- Review database for failed jobs
- Use admin view (`/api/admin/jobs`) to inspect recent jobs

## Scaling Considerations

- S3 storage scales automatically
- Vercel serverless functions scale automatically
- Database: Consider connection pooling for high traffic
- Consider adding a job queue (Redis + BullMQ) if processing times increase

