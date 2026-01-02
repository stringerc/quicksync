# Architecture Overview

## System Architecture

```
┌─────────────┐
│   Browser   │
│  (Next.js)  │
└──────┬──────┘
       │
       ├─► Upload PDF → /api/upload
       ├─► Payment → Stripe Checkout
       ├─► Status → /api/jobs/[id]
       └─► Download → /api/download/[id]/[format]
       │
┌──────▼──────────────────────────────────────────┐
│         Next.js API Routes (Serverless)          │
├──────────────────────────────────────────────────┤
│  /api/upload       - Handle PDF upload           │
│  /api/jobs/[id]    - Get processing status       │
│  /api/process      - Trigger processing          │
│  /api/download/... - Serve CSV/QBO files         │
│  /api/payment      - Stripe webhook & checkout   │
│  /api/auth         - Magic link auth             │
└──────┬───────────────────────────────────────────┘
       │
       ├─► File Storage (local/S3)
       ├─► Database (SQLite/Postgres)
       └─► Processing Queue (in-process)
       │
┌──────▼──────────────────────────────────────────┐
│          Processing Pipeline                      │
├──────────────────────────────────────────────────┤
│  1. PDF Upload → Save to storage                  │
│  2. Extract text/tables (pdfplumber)             │
│  3. Parse transactions                            │
│  4. Normalize (dates, amounts, descriptions)     │
│  5. Generate CSV/QBO                             │
│  6. Store results                                 │
│  7. Mark as ready (or needs review)              │
└──────────────────────────────────────────────────┘
```

## Data Model

### Jobs Table
```sql
id: UUID (primary key)
user_id: UUID (foreign key to users)
file_name: string
file_path: string (storage path)
status: enum ('pending', 'processing', 'completed', 'failed', 'needs_review')
created_at: timestamp
processed_at: timestamp
payment_status: enum ('pending', 'paid', 'refunded')
stripe_payment_id: string (nullable)
metadata: JSON
  - row_count: number
  - date_range: {start, end}
  - totals: {debit, credit, balance}
  - confidence_score: number
```

### Users Table
```sql
id: UUID (primary key)
email: string (unique)
magic_link_token: string (nullable)
magic_link_expires: timestamp (nullable)
created_at: timestamp
```

### Transactions Table (optional, for preview)
```sql
id: UUID
job_id: UUID (foreign key)
date: date
description: string
debit: decimal (nullable)
credit: decimal (nullable)
balance: decimal (nullable)
row_index: number
```

## Processing Flow

1. **Upload**: User uploads PDF → saved to storage → job created with status 'pending'
2. **Payment**: User completes Stripe Checkout → webhook marks payment_status = 'paid'
3. **Processing**: Background job (API route or queue):
   - Extract PDF tables/text
   - Parse transaction rows
   - Normalize data (dates, amounts)
   - Calculate confidence scores
   - Generate CSV/QBO files
   - Update job status
4. **Download**: User requests download → verify payment → serve file

## Technology Stack

- **Frontend**: Next.js 14+ (App Router), React, Tailwind CSS
- **Backend**: Next.js API Routes (Serverless)
- **Database**: SQLite (dev) / PostgreSQL (production) with Prisma ORM
- **File Storage**: Local filesystem (dev) / AWS S3 (production)
- **PDF Processing**: pdf-parse or pdf-lib + table extraction logic
- **Payment**: Stripe Checkout + Webhooks
- **Auth**: Magic link (email tokens, no passwords)
- **Queue**: In-process queue (simple array) or BullMQ with Redis (if needed)

## Key Design Decisions

1. **Stateless Processing**: Each job is independent, can be retried
2. **Payment-First**: Block downloads until payment confirmed
3. **Confidence Scoring**: Simple heuristic (table detection quality, row parsing success rate)
4. **Minimal State**: Only store job metadata, regenerate files on-demand if needed
5. **No Premature Optimization**: Start with in-process queue, scale to Redis if needed

