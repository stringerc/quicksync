# Stripe Webhook Setup for QuickSync.app

## Important: Do This AFTER Deployment

You need to set up the webhook **after** your site is deployed to `quicksync.app` so the endpoint URL exists.

## Step-by-Step Instructions

### Step 1: Access Stripe Dashboard

1. Go to: https://dashboard.stripe.com/webhooks
2. Make sure you're in **Live mode** (toggle in top right should say "Live mode")
3. Click **"Add endpoint"** button (or "Create endpoint" in newer interface)

### Step 2: Configure Endpoint

Fill in these **exact values**:

1. **Endpoint URL:**
   ```
   https://quicksync.app/api/payment/webhook
   ```
   ⚠️ Make sure it's `quicksync.app` (not resonance.syncscript.app or any other domain)

2. **Description** (optional but recommended):
   ```
   QuickSync Payment Webhook
   ```

3. **API version** (optional):
   - Leave as default, or select `2023-10-16` if available
   - Our code works with the default version

### Step 3: Select Events

Click **"Select events"** or "Add events" button.

You need to select these **2 events**:

1. ✅ **`checkout.session.completed`**
   - This fires when a customer completes a Stripe Checkout payment
   - Used for single file payments ($9)

2. ✅ **`payment_intent.succeeded`**
   - This fires when a payment succeeds
   - Used as a backup/secondary confirmation

**How to find them:**
- Look for "Checkout" section → Select `checkout.session.completed`
- Look for "Payment" section → Select `payment_intent.succeeded`
- You can also search/filter by typing the event name

**DO NOT select:**
- ❌ `charge.succeeded` (different event, not used)
- ❌ `charge.failed` (different event, not used)
- ❌ Other events (unless you specifically need them)

### Step 4: Create Endpoint

1. Review your settings:
   - URL: `https://quicksync.app/api/payment/webhook`
   - Events: `checkout.session.completed`, `payment_intent.succeeded`
2. Click **"Add endpoint"** (or "Create endpoint")

### Step 5: Copy Signing Secret

After creating the endpoint:

1. Click on the endpoint you just created (it should appear in the list)
2. Look for **"Signing secret"** section
3. Click **"Reveal"** or **"Show"** to reveal the secret
4. Copy the entire secret (it starts with `whsec_...`)
   - Example: `whsec_vh1l4NgrhoVBv4NgNg1h00Xamk8wY473`
5. **Keep this secret safe** - you'll add it to Vercel next

### Step 6: Add Signing Secret to Vercel

1. Go to: https://vercel.com/[your-team]/quicksync/settings/environment-variables
   (Replace `[your-team]` with your Vercel team/username)

2. Find the variable: `STRIPE_WEBHOOK_SECRET`
   - If it exists, click to edit it
   - If it doesn't exist, click **"Add New"**

3. Fill in:
   - **Key**: `STRIPE_WEBHOOK_SECRET`
   - **Value**: Paste the signing secret (whsec_...)
   - **Environment**: Select **"Production"** (and optionally "Preview" if you want)
   
4. Click **"Save"**

### Step 7: Redeploy (If Needed)

If you already deployed and are just adding the webhook secret:
- You can trigger a redeploy, OR
- Vercel will automatically use the new env var on next deployment

To trigger immediate redeploy:
```bash
vercel --prod
```

## Testing the Webhook

### Option 1: Send Test Webhook (Recommended)

1. In Stripe Dashboard → Webhooks → Your endpoint
2. Click **"Send test webhook"** (or "Send test event")
3. Select event: `checkout.session.completed`
4. Click **"Send test webhook"**
5. Check the response - should show:
   - Status: 200 (Success)
   - Response time: < 1 second

### Option 2: Make a Test Payment

1. Visit: https://quicksync.app
2. Upload a PDF file
3. Complete a test payment (use test card: `4242 4242 4242 4242`)
4. In Stripe Dashboard → Webhooks → Your endpoint → "Recent events"
5. You should see a `checkout.session.completed` event
6. Click on it to see:
   - Status: 200 (success)
   - Response: `{"received": true}`

### Option 3: Check Vercel Logs

1. Go to: https://vercel.com/[your-team]/quicksync/functions
2. Click on `api/payment/webhook`
3. Check "Runtime Logs"
4. You should see successful webhook processing (no errors)

## Troubleshooting

### Webhook Returns 400 or 401

**Problem**: Invalid signature
**Solution**: 
- Verify `STRIPE_WEBHOOK_SECRET` in Vercel matches Stripe dashboard
- Make sure you copied the entire secret (including `whsec_` prefix)
- Check you're using the secret from **Live mode** (not Test mode)

### Webhook Returns 404

**Problem**: Endpoint doesn't exist
**Solution**:
- Verify URL is exactly: `https://quicksync.app/api/payment/webhook`
- Make sure the site is deployed
- Check DNS is resolving correctly

### Webhook Returns 500

**Problem**: Server error
**Solution**:
- Check Vercel function logs for errors
- Verify database connection
- Verify all environment variables are set
- Check that Prisma schema is migrated

### Events Not Being Received

**Problem**: Events selected incorrectly
**Solution**:
- Verify events are selected: `checkout.session.completed`, `payment_intent.succeeded`
- Make sure you're in **Live mode** (not Test mode)
- Check the webhook is **enabled** (status shows "Enabled")

### Payment Succeeds But Status Not Updated

**Problem**: Webhook not processing correctly
**Solution**:
- Check Vercel logs for webhook handler errors
- Verify `STRIPE_WEBHOOK_SECRET` is correct
- Test webhook manually using "Send test webhook"
- Verify database connection is working

## Quick Checklist

- [ ] Site deployed to https://quicksync.app
- [ ] In Stripe Dashboard, switched to **Live mode**
- [ ] Created webhook endpoint
- [ ] URL set to: `https://quicksync.app/api/payment/webhook`
- [ ] Events selected: `checkout.session.completed`, `payment_intent.succeeded`
- [ ] Copied signing secret (whsec_...)
- [ ] Added `STRIPE_WEBHOOK_SECRET` to Vercel environment variables
- [ ] Selected "Production" environment in Vercel
- [ ] Sent test webhook and verified 200 response
- [ ] Checked Vercel logs - no errors

## Important Notes

1. **Live vs Test Mode**: Make sure you create the webhook in **Live mode** (toggle in top right of Stripe dashboard)

2. **URL Must Match Exactly**: The URL must be exactly `https://quicksync.app/api/payment/webhook` - no trailing slashes, no typos

3. **Secret is Sensitive**: Never commit the webhook secret to git. It's only in Vercel environment variables.

4. **HTTPS Required**: Stripe webhooks require HTTPS. Vercel automatically provides SSL certificates.

5. **Timeout**: Webhooks should respond within 30 seconds. Our handler responds quickly, so this shouldn't be an issue.

