# PDF to CSV/QBO Converter MVP

A production-ready MVP for converting financial PDF documents (bank statements, credit card statements, payout reports) into clean CSV or QBO files for QuickBooks import.

## Features

- ✅ PDF upload and processing
- ✅ Transaction extraction with date/amount normalization
- ✅ CSV and QBO file generation
- ✅ Stripe payment integration (pay-per-file)
- ✅ Email + magic link authentication (no passwords)
- ✅ Processing status tracking
- ✅ Confidence scoring and validation summary
- ✅ Multi-page PDF support

## Tech Stack

- **Frontend**: Next.js 14 (App Router), React, Tailwind CSS
- **Backend**: Next.js API Routes (Serverless)
- **Database**: SQLite (dev) / PostgreSQL (production) with Prisma
- **File Storage**: Local filesystem (dev) / S3 (production-ready)
- **PDF Processing**: pdf-parse
- **Payment**: Stripe Checkout
- **Auth**: Magic link (JWT tokens)

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Stripe account (for payments)
- SMTP server (optional, for email magic links - Gmail works)

### Installation

1. **Clone and install dependencies:**

```bash
npm install
```

2. **Set up environment variables:**

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL` - SQLite (default: `file:./dev.db`) or PostgreSQL connection string
- `STRIPE_SECRET_KEY` - From Stripe dashboard
- `STRIPE_PUBLISHABLE_KEY` - From Stripe dashboard  
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Same as above
- `STRIPE_WEBHOOK_SECRET` - From Stripe webhook settings
- `JWT_SECRET` - Random secret for JWT signing
- `NEXT_PUBLIC_APP_URL` - Your app URL (http://localhost:3000 for dev)

Optional (for email):
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`

3. **Set up database:**

```bash
npx prisma generate
npx prisma db push
```

4. **Create storage directory:**

```bash
mkdir -p storage/uploads storage/outputs
```

5. **Run development server:**

```bash
npm run dev
```

Visit http://localhost:3000

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture and data model.

### Key Components

- **Upload Flow**: User uploads PDF → File saved → Job created with `pending` status
- **Payment Flow**: User pays via Stripe Checkout → Webhook updates payment status → Processing can begin
- **Processing Flow**: Extract PDF text → Parse transactions → Normalize data → Generate CSV/QBO → Update job status
- **Download Flow**: User requests download → Verify payment → Serve file

## API Routes

- `POST /api/upload` - Upload PDF file
- `GET /api/jobs/[id]` - Get job status
- `POST /api/process` - Trigger processing (requires payment)
- `GET /api/download/[id]/[format]` - Download CSV or QBO file
- `POST /api/payment/create-checkout` - Create Stripe checkout session
- `POST /api/payment/webhook` - Stripe webhook handler
- `POST /api/auth/login` - Request magic link
- `GET /api/auth/callback` - Magic link callback

## User Flow

1. **Sign In**: Enter email → Receive magic link → Click link → Authenticated
2. **Upload**: Select PDF file → Upload → Redirected to job page
3. **Pay**: Click "Pay to Process" → Stripe Checkout → Complete payment
4. **Process**: (Auto-triggered after payment) → Processing begins → Status updates
5. **Download**: View validation summary → Download CSV or QBO

## PDF Parsing

The PDF parser uses `pdf-parse` to extract text, then applies heuristics to identify:
- Transaction dates (multiple format support)
- Debit/credit amounts
- Descriptions
- Balances

**Note**: This is a simplified parser for MVP. For production, consider:
- More robust table extraction (pdfplumber equivalent for Node.js)
- OCR fallback for scanned PDFs (Tesseract.js or external API)
- Machine learning models for better accuracy
- Bank-specific parsers

## Configuration

### Pricing

Set `PRICE_PER_FILE` in `.env` (default: 299 = $2.99). Price is in cents.

### Storage

- **Local** (default): Files stored in `./storage` directory
- **S3**: Set `STORAGE_TYPE=s3` and configure AWS credentials (not fully implemented yet)

### Database

- **Development**: SQLite (no setup needed)
- **Production**: PostgreSQL (recommended for Vercel/Railway/etc.)

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Add environment variables
4. Set up Stripe webhook:
   - URL: `https://your-app.vercel.app/api/payment/webhook`
   - Events: `checkout.session.completed`
5. Deploy!

**Important**: 
- Use PostgreSQL database (Vercel Postgres or external)
- Set up S3 or use Vercel Blob storage for file storage
- Update `NEXT_PUBLIC_APP_URL` to production URL

### Other Platforms

Works on any platform supporting Next.js:
- Railway
- Render
- Fly.io
- AWS/Google Cloud/Azure

## Limitations & Future Improvements

This MVP prioritizes speed to revenue over perfection. Known limitations:

1. **PDF Parsing**: Basic text extraction - may need improvement for complex layouts
2. **Table Detection**: Simple heuristics - could use ML models
3. **OCR**: Not implemented - add Tesseract.js or external API for scanned PDFs
4. **Queue**: In-process processing - consider Redis queue for scale
5. **Storage**: Local filesystem only - S3 integration partial
6. **Error Handling**: Basic - add retries, better error messages
7. **Validation**: Minimal - add more data validation rules

### Recommended Next Steps

- [ ] Add OCR support for scanned PDFs
- [ ] Improve table extraction accuracy
- [ ] Add Redis queue for async processing
- [ ] Implement S3 storage
- [ ] Add batch processing
- [ ] Create API access for developers
- [ ] Add subscription plans
- [ ] Build admin dashboard
- [ ] Add more file format support (Excel, etc.)

## Testing

For testing, you can:

1. Use Stripe test mode (test card: `4242 4242 4242 4242`)
2. Magic links appear in console in dev mode
3. Test with sample bank statement PDFs

## License

MIT

## Support

For issues or questions, please open a GitHub issue.

