# Deploy QuickSync.app to Vercel - Step-by-Step Guide

This guide walks through deploying QuickSync.app to production on `quicksync.app` using Vercel.

## Prerequisites

- Node.js 18+ installed
- Vercel account (free tier works)
- Stripe account (live mode)
- S3 bucket (AWS S3) OR Cloudflare R2 bucket
- Domain: quicksync.app (configured in your domain registrar)

## Quick Start

```bash
# 1. Install Vercel CLI (if not installed)
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Run deployment script
./scripts/deploy_vercel_quicksync.sh
```

The script will:
- Check prerequisites
- Link/create Vercel project
- Set environment variables
- Build the project
- Deploy to production

## Detailed Setup

### Step 1: Database Setup

#### Option A: Vercel Postgres (Recommended)

1. In Vercel Dashboard → Go to your project → Storage tab
2. Click "Create Database" → Select "Postgres"
3. Choose a name (e.g., "quicksync-db")
4. Copy the connection string
5. Use as `DATABASE_URL` in `.env.production`

#### Option B: External PostgreSQL

Use any PostgreSQL provider:
- **Neon**: https://neon.tech (free tier available)
- **Supabase**: https://supabase.com (free tier)
- **Railway**: https://railway.app
- **AWS RDS**: For enterprise setups

Connection string format:
```
postgresql://user:password@host:port/database?sslmode=require
```

**After deployment, run migration:**
```bash
# Option 1: Using Vercel CLI (recommended)
vercel env pull .env.vercel
npx prisma db push

# Option 2: Using Vercel exec (if available)
vercel exec 'npx prisma db push'

# Option 3: Direct connection (if DB allows)
# Set DATABASE_URL in your local .env and run:
npx prisma db push
```

### Step 2: Storage Setup (S3 or Cloudflare R2)

#### Option A: AWS S3

1. **Create S3 Bucket:**
   - AWS Console → S3 → Create bucket
   - Name: `quicksync-app` (or your choice)
   - Region: `us-east-1` (or your preference)
   - Block all public access: **Yes** (keep files private)

2. **Create IAM User & Access Keys:**
   - IAM Console → Users → Create user
   - Username: `quicksync-s3-user`
   - Permissions: Attach policy `AmazonS3FullAccess` (or create custom policy with only PutObject, GetObject, DeleteObject)
   - Create Access Key → Copy Access Key ID and Secret Access Key

3. **Environment Variables:**
   ```env
   STORAGE_TYPE="s3"
   AWS_REGION="us-east-1"
   AWS_S3_BUCKET="quicksync-app"
   AWS_ACCESS_KEY_ID="AKIA..."
   AWS_SECRET_ACCESS_KEY="..."
   # Leave AWS_S3_ENDPOINT empty for AWS S3
   ```

#### Option B: Cloudflare R2

1. **Create R2 Bucket:**
   - Cloudflare Dashboard → R2 → Create bucket
   - Name: `quicksync-app`

2. **Create API Token:**
   - R2 → Manage R2 API Tokens → Create API token
   - Permissions: Object Read & Write
   - Copy Access Key ID and Secret Access Key
   - Copy Account ID (from R2 overview page)

3. **Get Endpoint URL:**
   - Format: `https://<account-id>.r2.cloudflarestorage.com`
   - Example: `https://abc123def456.r2.cloudflarestorage.com`

4. **Environment Variables:**
   ```env
   STORAGE_TYPE="s3"
   AWS_REGION="auto"
   AWS_S3_BUCKET="quicksync-app"
   AWS_ACCESS_KEY_ID="your-r2-access-key"
   AWS_SECRET_ACCESS_KEY="your-r2-secret-key"
   AWS_S3_ENDPOINT="https://<account-id>.r2.cloudflarestorage.com"
   ```

**Bucket Policy (Optional but Recommended):**
For AWS S3, you can restrict access by IP if needed. For R2, tokens provide sufficient security.

### Step 3: Stripe Setup

1. **Get API Keys:**
   - Stripe Dashboard → Developers → API keys
   - Copy **Live** keys:
     - Publishable key: `pk_live_...`
     - Secret key: `sk_live_...`

2. **Set Environment Variables:**
   ```env
   STRIPE_SECRET_KEY="sk_live_..."
   STRIPE_PUBLISHABLE_KEY="pk_live_..."
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_live_..."
   ```

3. **Create Webhook Endpoint:**
   - Stripe Dashboard → Developers → Webhooks
   - Click "Add endpoint"
   - Endpoint URL: `https://quicksync.app/api/payment/webhook`
   - Description: "QuickSync Payment Webhook"
   - Events to send:
     - `checkout.session.completed`
     - `payment_intent.succeeded`
   - Click "Add endpoint"
   - Copy the **Signing secret** (starts with `whsec_...`)
   - Set as `STRIPE_WEBHOOK_SECRET`

4. **Pricing Configuration:**
   No Stripe Products/Prices needed - we use `price_data` in checkout sessions.
   Environment variables:
   ```env
   PRICE_PER_FILE=900    # $9.00 in cents
   PRICE_PACK_10=2900    # $29.00 in cents
   ```

### Step 4: Domain & DNS Setup

1. **Add Domain in Vercel:**
   - Vercel Dashboard → Your Project → Settings → Domains
   - Add domain: `quicksync.app`
   - Add domain: `www.quicksync.app` (optional)

2. **DNS Records (At Your Domain Registrar):**

   For **apex domain** (`quicksync.app`):
   ```
   Type: A
   Name: @ (or quicksync.app)
   Value: 76.76.21.21
   TTL: 3600
   ```

   OR (if your registrar supports it):
   ```
   Type: CNAME
   Name: @ (or quicksync.app)
   Value: cname.vercel-dns.com
   TTL: 3600
   ```

   For **www subdomain** (`www.quicksync.app`):
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   TTL: 3600
   ```

   **Note:** Vercel will show you the exact values after you add the domain. Check the Vercel dashboard for the current DNS values.

3. **SSL Certificate:**
   - Vercel automatically provisions SSL certificates
   - Wait 5-10 minutes after DNS propagation
   - Certificate will be active automatically

### Step 5: Environment Variables Summary

Create `.env.production` from `.env.production.example` and fill in:

```env
# Database
DATABASE_URL="postgresql://..."

# Storage
STORAGE_TYPE="s3"
AWS_REGION="us-east-1"  # or "auto" for R2
AWS_S3_BUCKET="quicksync-app"
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
AWS_S3_ENDPOINT=""  # Only for R2: "https://<account-id>.r2.cloudflarestorage.com"

# Stripe
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_PUBLISHABLE_KEY="pk_live_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_..."

# Pricing
PRICE_PER_FILE=900
PRICE_PACK_10=2900

# Auth
JWT_SECRET="generate-with: openssl rand -base64 32"

# App
NEXT_PUBLIC_APP_URL="https://quicksync.app"

# Admin
ADMIN_EMAILS="your-email@example.com"

# Analytics (optional)
NEXT_PUBLIC_PLAUSIBLE_DOMAIN="quicksync.app"  # or leave empty
```

### Step 6: Database Migration

After deployment, run the database migration:

```bash
# Option 1: Using Vercel CLI (recommended)
vercel env pull .env.vercel
npx prisma db push

# Option 2: Direct connection (if your DB allows external connections)
# Set DATABASE_URL in local .env to production DB
npx prisma db push
```

This creates:
- `Credit` table
- `Job.creditRedeemedAt` field
- `Job.reviewRequestedAt` field
- All other required tables

### Step 7: Deployment

```bash
# Run the deployment script
./scripts/deploy_vercel_quicksync.sh
```

Or manually:
```bash
# Link project (first time only)
vercel link

# Set env vars (if not using script)
vercel env add DATABASE_URL production
# ... repeat for each var ...

# Deploy
vercel --prod
```

## Production Smoke Tests

After deployment, test these URLs and flows:

### 1. Basic Site Access
- [ ] https://quicksync.app loads
- [ ] https://www.quicksync.app redirects (if configured)
- [ ] SSL certificate is valid (green lock icon)

### 2. Authentication Flow
- [ ] Go to https://quicksync.app
- [ ] Enter email → Click "Send Magic Link"
- [ ] Check email for magic link
- [ ] Click link → Redirected and authenticated
- [ ] Can see upload form

### 3. Upload & Process Flow
- [ ] Upload a PDF file
- [ ] Redirected to job page
- [ ] File processes automatically
- [ ] See confidence score and validation summary
- [ ] Preview data before payment

### 4. Payment Flow (Single File)
- [ ] On job page, click "Pay $9 to Download"
- [ ] Stripe Checkout opens
- [ ] Use test card: `4242 4242 4242 4242`
- [ ] Complete payment
- [ ] Redirected back to job page
- [ ] Payment status shows "paid"
- [ ] Download buttons appear

### 5. Download Flow
- [ ] Click "Download CSV" → File downloads
- [ ] Click "Download QBO" → File downloads
- [ ] Files are correct format

### 6. Credit Pack Purchase
- [ ] Call API or use UI (when implemented):
  ```bash
  curl -X POST https://quicksync.app/api/payment/purchase-credits \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json"
  ```
- [ ] Complete payment ($29)
- [ ] Check credits added to account
- [ ] Use credit to download file

### 7. Credit Redemption
- [ ] Upload new file
- [ ] Process completes
- [ ] See "Use 1 Credit" button
- [ ] Click download → Credit redeemed
- [ ] Credit balance decreases

### 8. Failed Parse Path
- [ ] Upload problematic PDF
- [ ] Processing fails or low confidence
- [ ] Payment button NOT shown
- [ ] "Request Review" button appears
- [ ] Support token visible

### 9. Webhook Verification
- [ ] Make a test payment
- [ ] Stripe Dashboard → Developers → Webhooks → Your endpoint
- [ ] Check "Recent events" tab
- [ ] Verify `checkout.session.completed` event received
- [ ] Verify payment status updated in database

### 10. Admin Endpoint
- [ ] Call: `GET https://quicksync.app/api/admin/jobs`
- [ ] With Authorization header (admin email's JWT token)
- [ ] Returns list of jobs
- [ ] Non-admin returns 403

### 11. Storage Verification
- [ ] Upload file → Check S3/R2 bucket
- [ ] File appears in bucket
- [ ] Download file → Verifies file retrieval works

## Troubleshooting

### Build Fails
- Check Node.js version (need 18+)
- Run `npm install` locally
- Check for TypeScript errors: `npm run lint`

### Database Connection Fails
- Verify `DATABASE_URL` format is correct
- Check if database allows connections from Vercel IPs
- For Vercel Postgres: Check connection string format

### Storage Upload Fails
- Verify S3/R2 credentials are correct
- Check bucket name matches `AWS_S3_BUCKET`
- For R2: Verify endpoint URL includes account ID
- Check IAM permissions (S3) or token permissions (R2)

### Webhook Not Working
- Verify webhook URL is correct: `https://quicksync.app/api/payment/webhook`
- Check `STRIPE_WEBHOOK_SECRET` matches Stripe dashboard
- Test with Stripe CLI: `stripe listen --forward-to https://quicksync.app/api/payment/webhook`
- Check Vercel function logs for errors

### Domain Not Resolving
- Wait 24-48 hours for DNS propagation
- Check DNS records match Vercel's requirements
- Verify domain is added in Vercel dashboard
- Use `dig quicksync.app` to check DNS

### Payment Not Processing
- Verify Stripe keys are **live** mode (not test)
- Check webhook is receiving events
- Check database has `paidAt` timestamp set
- Verify `NEXT_PUBLIC_APP_URL` is correct

## Manual Checklist

After running the deployment script, complete these manual steps:

### DNS (At Domain Registrar)
- [ ] Add A record: `@` → `76.76.21.21` (check Vercel for current IP)
- [ ] Add CNAME: `www` → `cname.vercel-dns.com`
- [ ] Wait for DNS propagation (check with `dig quicksync.app`)

### Vercel Dashboard
- [ ] Project created: `quicksync`
- [ ] Domain added: `quicksync.app`
- [ ] Domain added: `www.quicksync.app` (optional)
- [ ] SSL certificate active (automatic, wait 5-10 min)

### Stripe Dashboard
- [ ] Webhook endpoint created: `https://quicksync.app/api/payment/webhook`
- [ ] Events selected: `checkout.session.completed`, `payment_intent.succeeded`
- [ ] Signing secret copied: `whsec_...`
- [ ] Added to `.env.production` as `STRIPE_WEBHOOK_SECRET`

### Database
- [ ] Database created (Vercel Postgres or external)
- [ ] Connection string copied to `DATABASE_URL`
- [ ] Migration run: `npx prisma db push`

### Storage
- [ ] S3 bucket created OR R2 bucket created
- [ ] Access keys created and added to `.env.production`
- [ ] Bucket name set as `AWS_S3_BUCKET`
- [ ] Test upload works (use smoke test)

## Support

If deployment fails:
1. Check Vercel build logs
2. Check Vercel function logs
3. Verify all environment variables are set
4. Test locally with production env vars
5. Check database/storage connectivity

For issues with specific services:
- **Vercel**: https://vercel.com/docs
- **Stripe**: https://stripe.com/docs
- **S3**: https://docs.aws.amazon.com/s3
- **R2**: https://developers.cloudflare.com/r2

