# QuickSync.app - GO-LIVE Guide

This guide provides the exact steps to go live with QuickSync.app on `quicksync.app`.

## Quick Start

```bash
# 1. Fill in .env.production
cp .env.production.example .env.production
# Edit .env.production with actual values

# 2. Run go-live script
./scripts/go_live_quicksync.sh
```

The script will:
- ✅ Run preflight checks
- ✅ Deploy to Vercel
- ✅ Apply database migrations
- ✅ Run smoke tests
- ✅ Print GO/NO-GO report

## Detailed Steps

### Step 1: Prerequisites

Ensure you have:
- Node.js 18+ installed
- Vercel CLI installed: `npm install -g vercel`
- Vercel account logged in: `vercel login`
- Domain `quicksync.app` registered

### Step 2: Environment Setup

1. Copy environment template:
   ```bash
   cp .env.production.example .env.production
   ```

2. Fill in `.env.production` with actual values:
   - Database connection string
   - S3/R2 credentials
   - Stripe live keys
   - JWT secret (generate: `openssl rand -base64 32`)
   - Admin emails

   See `.env.production.example` for detailed instructions.

### Step 3: Run Go-Live Script

```bash
./scripts/go_live_quicksync.sh
```

The script will:
1. Check prerequisites
2. Validate environment variables
3. Deploy to Vercel production
4. Run database migrations
5. Execute smoke tests
6. Print GO/NO-GO report

### Step 4: Manual Configuration (After Deployment)

Complete these steps in the order listed:

#### DNS Configuration (Domain Registrar)

Add these DNS records for `quicksync.app`:

```
Type: A
Name: @ (or quicksync.app)
Value: 76.76.21.21
TTL: 3600

Type: CNAME
Name: www
Value: cname.vercel-dns.com
TTL: 3600
```

**Note:** Vercel may provide different IP addresses. Check your Vercel project's domain settings for the exact values after adding the domain.

**How to verify:**
```bash
dig quicksync.app +short
# Should return: 76.76.21.21 (or Vercel's IP)
```

#### Vercel Domain Setup

1. Go to: https://vercel.com/[your-team]/quicksync/settings/domains
2. Click "Add Domain"
3. Enter: `quicksync.app`
4. Click "Add"
5. (Optional) Add: `www.quicksync.app`

SSL certificate will be provisioned automatically (wait 5-10 minutes).

#### Stripe Webhook Configuration

1. Go to: https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. **Endpoint URL:** `https://quicksync.app/api/payment/webhook`
4. **Description:** QuickSync Payment Webhook
5. **Events to send:**
   - ✅ `checkout.session.completed`
   - ✅ `payment_intent.succeeded`
6. Click "Add endpoint"
7. Copy the **Signing secret** (starts with `whsec_...`)
8. Add to Vercel environment variables:
   - Go to: https://vercel.com/[your-team]/quicksync/settings/environment-variables
   - Add/Update: `STRIPE_WEBHOOK_SECRET` = `whsec_...`
   - Select "Production" environment
   - Save

**Verify webhook:**
- Stripe Dashboard → Webhooks → Your endpoint → "Send test webhook"
- Check Vercel function logs for successful receipt

#### Environment Variables Checklist

Ensure all these are set in Vercel (Settings → Environment Variables → Production):

```
✅ DATABASE_URL
✅ STORAGE_TYPE="s3"
✅ AWS_S3_BUCKET
✅ AWS_ACCESS_KEY_ID
✅ AWS_SECRET_ACCESS_KEY
✅ AWS_REGION
✅ AWS_S3_ENDPOINT (if using R2)
✅ STRIPE_SECRET_KEY
✅ STRIPE_PUBLISHABLE_KEY
✅ NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
✅ STRIPE_WEBHOOK_SECRET
✅ PRICE_PER_FILE=900
✅ PRICE_PACK_10=2900
✅ JWT_SECRET
✅ NEXT_PUBLIC_APP_URL="https://quicksync.app"
✅ ADMIN_EMAILS
✅ NEXT_PUBLIC_PLAUSIBLE_DOMAIN (optional)
```

## GO/NO-GO Criteria

### ✅ GO Criteria (All Must Pass)

1. **Preflight Checks**
   - [ ] All prerequisites installed (node, npm, vercel CLI)
   - [ ] Logged into Vercel
   - [ ] .env.production exists with all required variables
   - [ ] NEXT_PUBLIC_APP_URL = "https://quicksync.app"

2. **Deployment**
   - [ ] Deployment succeeds without errors
   - [ ] Vercel build completes successfully
   - [ ] All environment variables are set in Vercel

3. **Database Migration**
   - [ ] Migration runs without errors
   - [ ] All tables created (Users, Jobs, Credits)
   - [ ] Schema matches Prisma schema.prisma

4. **Smoke Tests (Automated)**
   - [ ] Health endpoint: `GET /api/health` returns 200
   - [ ] Landing page: `GET /` returns 200
   - [ ] Bookkeepers page: `GET /bookkeepers` returns 200
   - [ ] Admin endpoint: `GET /api/admin/jobs` returns 401 (auth required)
   - [ ] Webhook endpoint: `POST /api/payment/webhook` (unsigned) returns 400
   - [ ] Upload endpoint: `POST /api/upload` returns 401 (auth required)
   - [ ] Jobs endpoint: `GET /api/jobs/[id]` returns 401/404 (auth required)
   - [ ] Download endpoint: `GET /api/download/[id]/[format]` returns 401/404 (auth required)

5. **Manual Verification (Post-Deployment)**
   - [ ] DNS records configured correctly
   - [ ] Domain resolves: `dig quicksync.app`
   - [ ] SSL certificate active (green lock icon)
   - [ ] Stripe webhook endpoint configured
   - [ ] Stripe webhook test event received successfully

### ❌ NO-GO Criteria (Any One Fails = NO-GO)

- Deployment fails
- Database migration fails
- Any automated smoke test fails
- DNS not configured after 24 hours
- SSL certificate not provisioned after 30 minutes
- Stripe webhook returns errors in test

## Manual Smoke Tests (Post-Go-Live)

After automated tests pass, perform these manual tests:

### 1. Authentication Flow
- [ ] Visit https://quicksync.app
- [ ] Enter email → Click "Send Magic Link"
- [ ] Receive email with magic link
- [ ] Click link → Redirected and authenticated
- [ ] Can see upload form

### 2. Upload & Process Flow
- [ ] Upload a PDF file
- [ ] Redirected to job page
- [ ] File processes automatically
- [ ] See confidence score and validation summary
- [ ] Preview data before payment

### 3. Payment Flow (Single File)
- [ ] Click "Pay $9 to Download"
- [ ] Stripe Checkout opens
- [ ] Complete payment with test card: `4242 4242 4242 4242`
- [ ] Redirected back to job page
- [ ] Payment status shows "paid"
- [ ] Download buttons appear

### 4. Download Flow
- [ ] Click "Download CSV" → File downloads correctly
- [ ] Click "Download QBO" → File downloads correctly
- [ ] Files are correct format

### 5. Webhook Verification
- [ ] Make a test payment
- [ ] Stripe Dashboard → Webhooks → Your endpoint → "Recent events"
- [ ] Verify `checkout.session.completed` event received
- [ ] Check Vercel logs: No errors
- [ ] Verify payment status updated in database

### 6. Admin Endpoint
- [ ] Get JWT token for admin email
- [ ] Call: `GET https://quicksync.app/api/admin/jobs`
- [ ] With Authorization header
- [ ] Returns list of jobs
- [ ] Non-admin returns 403

## Rollback Procedure

If you need to rollback to a previous deployment:

### Option 1: Vercel Dashboard
1. Go to: https://vercel.com/[your-team]/quicksync/deployments
2. Find the previous successful deployment
3. Click "..." menu → "Promote to Production"

### Option 2: Vercel CLI
```bash
# List recent deployments
vercel ls

# Rollback to previous deployment
vercel rollback

# Or promote specific deployment
vercel promote [deployment-url]
```

### Option 3: Git-based Rollback
```bash
# Checkout previous commit
git checkout <previous-commit-hash>

# Redeploy
vercel --prod
```

## Troubleshooting

### Deployment Fails
- Check Vercel build logs
- Verify all environment variables are set
- Check for TypeScript/build errors locally: `npm run build`

### Database Migration Fails
- Verify DATABASE_URL is correct
- Check database allows connections from Vercel IPs
- Try connecting directly: `psql $DATABASE_URL`

### Smoke Tests Fail
- Check if deployment is fully propagated (wait 2-3 minutes)
- Verify DNS is resolving correctly
- Check Vercel function logs for errors
- Test endpoints manually with curl

### Stripe Webhook Not Working
- Verify webhook URL is correct: `https://quicksync.app/api/payment/webhook`
- Check STRIPE_WEBHOOK_SECRET matches Stripe dashboard
- Test with Stripe CLI: `stripe listen --forward-to https://quicksync.app/api/payment/webhook`
- Check Vercel function logs

### DNS Not Resolving
- Wait 24-48 hours for propagation
- Verify DNS records match exactly
- Use `dig quicksync.app` to check
- Check domain registrar's DNS settings

## Support

For issues:
1. Check Vercel build/deployment logs
2. Check Vercel function logs (Runtime Logs)
3. Verify all environment variables
4. Test locally with production env vars
5. Review error messages in browser console (for frontend issues)

## Next Steps After Go-Live

1. Monitor Vercel logs for errors
2. Set up error tracking (Sentry, etc.)
3. Monitor Stripe webhook events
4. Track conversion metrics
5. Set up uptime monitoring
6. Configure alerts for critical failures

