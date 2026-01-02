# Quick Setup Guide

## 1. Install Dependencies

```bash
npm install
```

## 2. Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Minimum Required Variables:

```env
DATABASE_URL="file:./dev.db"
JWT_SECRET="change-me-to-random-string"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_PUBLISHABLE_KEY="pk_test_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
```

**Getting Stripe Keys:**
1. Sign up at https://stripe.com
2. Get test keys from https://dashboard.stripe.com/test/apikeys
3. For webhook secret:
   - Go to https://dashboard.stripe.com/test/webhooks
   - Add endpoint: `http://localhost:3000/api/payment/webhook` (use ngrok for local testing)
   - Copy the webhook signing secret

## 3. Initialize Database

```bash
npx prisma generate
npx prisma db push
```

## 4. Create Storage Directories

```bash
mkdir -p storage/uploads storage/outputs
```

## 5. Run Development Server

```bash
npm run dev
```

Visit http://localhost:3000

## Testing the Flow

1. **Sign In**: Enter your email → Check console for magic link (dev mode) → Click link
2. **Upload**: Select a PDF file → Click upload
3. **Payment**: Click "Pay to Process" → Use test card `4242 4242 4242 4242`
4. **Process**: After payment, processing starts automatically
5. **Download**: Once complete, download CSV or QBO

## Email Setup (Optional)

For production email magic links, configure SMTP:

```env
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASS="your-app-password"
```

For Gmail, use an App Password (not your regular password).

## Troubleshooting

**Database errors**: Run `npx prisma db push` again

**Storage errors**: Make sure `storage/` directory exists and is writable

**Stripe errors**: Verify your API keys are correct and in test mode

**PDF parsing issues**: The parser uses basic heuristics. Complex PDFs may need manual review.

