# Project Structure

```
x402/
├── app/                          # Next.js App Router
│   ├── api/                      # API Routes
│   │   ├── auth/
│   │   │   ├── login/           # POST - Request magic link
│   │   │   └── callback/        # GET - Magic link callback
│   │   ├── download/
│   │   │   └── [id]/[format]/   # GET - Download CSV/QBO
│   │   ├── jobs/
│   │   │   └── [id]/            # GET - Get job status
│   │   ├── payment/
│   │   │   ├── create-checkout/ # POST - Create Stripe session
│   │   │   └── webhook/         # POST - Stripe webhook handler
│   │   ├── process/             # POST - Process PDF
│   │   └── upload/              # POST - Upload PDF
│   ├── auth/
│   │   └── callback/            # Auth callback page
│   ├── jobs/
│   │   └── [id]/                # Job detail page
│   ├── globals.css              # Global styles
│   ├── layout.tsx               # Root layout
│   └── page.tsx                 # Home page (login/upload)
├── components/                   # React components
│   ├── JobList.tsx              # Job list component
│   └── UploadForm.tsx           # PDF upload form
├── lib/                         # Utility libraries
│   ├── auth.ts                  # JWT & magic link auth
│   ├── csv-generator.ts         # CSV file generation
│   ├── db.ts                    # Prisma client
│   ├── pdf-parser.ts            # PDF parsing logic
│   ├── qbo-generator.ts         # QBO file generation
│   ├── storage.ts               # File storage (local/S3)
│   └── stripe.ts                # Stripe client
├── prisma/
│   └── schema.prisma            # Database schema
├── storage/                     # File storage (gitignored)
│   ├── uploads/                 # Uploaded PDFs
│   └── outputs/                 # Generated CSV/QBO files
├── .env.example                 # Environment variables template
├── .eslintrc.json               # ESLint config
├── ARCHITECTURE.md              # Architecture documentation
├── next.config.js               # Next.js config
├── package.json                 # Dependencies
├── postcss.config.js            # PostCSS config
├── PROJECT_STRUCTURE.md         # This file
├── README.md                    # Main README
├── SETUP.md                     # Quick setup guide
├── tailwind.config.ts           # Tailwind CSS config
└── tsconfig.json                # TypeScript config
```

## Key Files

### API Routes
- **upload/route.ts**: Handles PDF file uploads, saves to storage, creates job record
- **process/route.ts**: Processes PDF, extracts transactions, generates CSV/QBO
- **jobs/[id]/route.ts**: Returns job status and metadata
- **download/[id]/[format]/route.ts**: Serves CSV or QBO files (requires payment)
- **payment/create-checkout/route.ts**: Creates Stripe Checkout session
- **payment/webhook/route.ts**: Handles Stripe webhook events
- **auth/login/route.ts**: Sends magic link email
- **auth/callback/route.ts**: Validates magic link token, issues JWT

### Core Libraries
- **pdf-parser.ts**: PDF text extraction and transaction parsing
- **csv-generator.ts**: Generates normalized CSV output
- **qbo-generator.ts**: Generates QuickBooks QBO format
- **storage.ts**: File storage abstraction (local filesystem, S3-ready)
- **auth.ts**: JWT token generation/validation, magic link helpers
- **db.ts**: Prisma client singleton
- **stripe.ts**: Stripe SDK client

### Frontend Pages
- **page.tsx**: Home page - login form or upload interface
- **jobs/[id]/page.tsx**: Job detail page - status, payment, download
- **auth/callback/page.tsx**: Magic link callback handler

### Components
- **UploadForm.tsx**: PDF file upload form
- **JobList.tsx**: List of user's jobs (placeholder for future)

## Data Flow

1. **Upload**: User → UploadForm → /api/upload → Storage → Database
2. **Payment**: User → Job Page → /api/payment/create-checkout → Stripe → Webhook → Database
3. **Process**: User → Job Page → /api/process → PDF Parser → CSV/QBO Generator → Storage → Database
4. **Download**: User → Job Page → /api/download → Storage → User

## Environment Variables

See `.env.example` for all required variables.

