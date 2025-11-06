# Resonance.syncscript.app - Comprehensive Technical Guide

## 🎯 Executive Summary

**Resonance.syncscript.app** is a **Next.js-based web platform** that provides:
1. **User authentication & license management** (SaaS subscription platform)
2. **Real-time monitoring dashboard** for Resonance runtime optimization
3. **Stripe integration** for subscription billing
4. **Admin dashboard** for viewing metrics, licenses, and system status

This is the **web frontend and backend** that customers use to:
- Sign up and manage their accounts
- Purchase Resonance licenses (Starter, Pro, Enterprise)
- View real-time performance metrics from their Resonance agents
- Monitor system health and coherence metrics (R(t), spectral entropy, latency)

---

## 🏗️ Architecture Overview

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    resonance.syncscript.app                     │
│                     (Vercel - Next.js)                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Frontend (React/Next.js App Router)                     │  │
│  │  - Landing pages, pricing, auth                          │  │
│  │  - Dashboard (canary monitoring)                         │  │
│  │  - User account management                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Routes (Next.js API Routes)                         │  │
│  │  - /api/auth/* (NextAuth.js)                             │  │
│  │  - /api/checkout/* (Stripe)                              │  │
│  │  - /api/webhooks/stripe (Stripe webhooks)                │  │
│  │  - /api/metrics (Proxy to Resonance Agent)               │  │
│  │  - /api/dashboard/license (License lookup)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│         ┌──────────────────┴──────────────────┐               │
│         ▼                                      ▼               │
│  ┌──────────────┐                    ┌──────────────────┐     │
│  │  PostgreSQL  │                    │  Resonance Agent │     │
│  │  (Supabase)  │                    │  (Render.com)    │     │
│  │              │                    │                  │     │
│  │  - Users     │                    │  - /health       │     │
│  │  - Licenses  │                    │  - /metrics      │     │
│  │  - Payments  │                    │  - Runtime opt   │     │
│  │  - Sessions  │                    │                  │     │
│  └──────────────┘                    └──────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

### Directory Layout

```
webapp/
├── app/                          # Next.js App Router (Pages & API Routes)
│   ├── page.tsx                  # Landing page (/)
│   ├── layout.tsx                # Root layout with providers
│   ├── globals.css               # Global styles (Tailwind)
│   ├── api/                      # API Routes
│   │   ├── auth/
│   │   │   ├── [...nextauth]/route.ts  # NextAuth handler
│   │   │   ├── register/route.ts       # User registration
│   │   │   └── forgot-password/route.ts # Password reset
│   │   ├── checkout/create/route.ts    # Stripe checkout
│   │   ├── dashboard/license/route.ts  # License API
│   │   ├── metrics/route.ts            # Metrics proxy (agent → dashboard)
│   │   ├── webhooks/stripe/route.ts    # Stripe webhooks
│   │   └── stripe/check-coupon/route.ts # Coupon validation
│   ├── auth/                     # Auth pages
│   │   ├── signin/page.tsx
│   │   ├── signup/page.tsx
│   │   └── forgot-password/page.tsx
│   ├── dashboard/                # User dashboard
│   │   ├── page.tsx              # Main dashboard
│   │   ├── canary/page.tsx       # Canary monitoring dashboard
│   │   └── DashboardClient.tsx   # Client-side status component
│   ├── pricing/                  # Pricing page
│   ├── resonance/pricing/        # Resonance-specific pricing
│   ├── syncscript/pricing/       # Syncscript-specific pricing
│   ├── contact/page.tsx
│   ├── privacy/page.tsx
│   └── terms/page.tsx
├── lib/                          # Shared libraries
│   ├── auth/
│   │   ├── config.ts             # NextAuth configuration
│   │   ├── password.ts           # Password hashing/validation
│   │   ├── rate-limit.ts         # Rate limiting (Upstash Redis)
│   │   └── mfa.ts                # Multi-factor authentication
│   ├── db.ts                     # Prisma client singleton
│   └── stripe/
│       ├── config.ts             # Stripe client initialization
│       ├── checkout.ts           # Checkout session creation
│       └── webhooks.ts           # Webhook event handlers
├── components/                   # React components
│   └── CheckoutButton.tsx        # Stripe checkout buttons
├── prisma/
│   └── schema.prisma             # Database schema (Prisma ORM)
├── public/                       # Static assets
├── middleware.ts                 # Edge middleware (security headers, CSP)
├── next.config.js                # Next.js configuration
├── package.json                  # Dependencies
├── tailwind.config.js            # Tailwind CSS configuration
└── tsconfig.json                 # TypeScript configuration
```

---

## 🔑 Key Technologies

### Frontend
- **Next.js 14.2** (App Router)
- **React 18.3**
- **TypeScript 5.3**
- **Tailwind CSS 3.4** (Styling)
- **NextAuth.js 4.24** (Authentication)

### Backend
- **Next.js API Routes** (Serverless functions)
- **Prisma ORM 5.14** (Database ORM)
- **PostgreSQL** (Supabase - Production database)

### Third-Party Services
- **Stripe** (Payment processing, subscriptions)
- **Upstash Redis** (Rate limiting - optional)
- **Supabase** (PostgreSQL database)
- **Vercel** (Hosting & deployment)

### Security
- **bcryptjs** (Password hashing)
- **@zxcvbn-ts** (Password strength validation)
- **JWT** (Session tokens via NextAuth)
- **CSP Headers** (Content Security Policy)
- **Rate Limiting** (Upstash Redis)

---

## 🗄️ Database Schema

### Core Models

#### User
```typescript
{
  id: string (UUID)
  email: string (unique)
  passwordHash: string (bcrypt)
  name: string?
  emailVerified: DateTime?
  mfaEnabled: boolean
  mfaSecret: string?
  createdAt: DateTime
  updatedAt: DateTime
  deletedAt: DateTime?
  
  // Relations
  sessions: Session[]
  licenses: License[]
  payments: Payment[]
  metrics: UserMetric[]
}
```

#### License
```typescript
{
  id: string (UUID)
  userId: string
  productType: "RESONANCE" | "SYNCSCRIPT"
  resonanceType: "STARTER" | "PRO" | "ENTERPRISE"?
  syncscriptType: "FREE" | "PRO" | "TEAM" | "ENTERPRISE"?
  type: "BASIC" | "PRO" | "ENTERPRISE"? (legacy)
  status: "ACTIVE" | "EXPIRED" | "CANCELLED" | "TRIAL"
  
  // Stripe Integration
  stripeCustomerId: string? (unique)
  stripeSubscriptionId: string? (unique)
  stripePriceId: string?
  stripeProductId: string?
  
  // Dates
  currentPeriodStart: DateTime?
  currentPeriodEnd: DateTime?
  trialEndsAt: DateTime?
  cancelledAt: DateTime?
  
  createdAt: DateTime
  updatedAt: DateTime
}
```

#### Payment
```typescript
{
  id: string (UUID)
  userId: string
  licenseId: string?
  amount: number (cents)
  currency: string ("usd")
  status: string ("succeeded" | "failed" | "pending")
  
  // Stripe
  stripePaymentIntentId: string? (unique)
  stripeInvoiceId: string? (unique)
  stripeChargeId: string?
  
  createdAt: DateTime
  updatedAt: DateTime
}
```

#### Session (NextAuth)
```typescript
{
  id: string (UUID)
  sessionToken: string (unique)
  userId: string
  expires: DateTime
}
```

#### UserMetric
```typescript
{
  id: string (UUID)
  userId: string
  data: Json (flexible structure)
  timestamp: DateTime
}
```

---

## 🔐 Authentication Flow

### NextAuth.js Configuration

**Provider**: Credentials (Email/Password)
**Session Strategy**: JWT (15-minute lifetime)
**Storage**: Database (Prisma adapter)

### Registration Flow

1. **User submits** `/api/auth/register`
2. **Rate limiting** (3 registrations/hour per IP)
3. **Password validation** (zxcvbn score ≥ 3, min 12 chars)
4. **Email uniqueness** check
5. **Password hashing** (bcrypt, 10 rounds)
6. **User creation** in database
7. **Response**: User object (no password)

### Login Flow

1. **User submits** credentials to NextAuth
2. **Account lockout** check (5 failed attempts = 15 min lockout)
3. **User lookup** by email
4. **Password verification** (bcrypt)
5. **MFA check** (if enabled)
6. **Session creation** (JWT token)
7. **Response**: Session cookie

### Password Reset Flow

1. **User requests** reset at `/auth/forgot-password`
2. **Rate limiting** (3 requests/hour per email)
3. **Email sent** (TODO: Implement email sending)
4. **Reset token** generated (TODO: Implement token storage)
5. **User clicks** reset link
6. **Password updated**

---

## 💳 Stripe Integration

### Products & Pricing

#### Resonance Products
- **Starter**: $29/month (Launch pricing, normally $49)
- **Pro**: $99/month (Launch pricing, normally $149)
- **Enterprise**: Custom pricing

#### Syncscript Products
- **Free**: Free tier
- **Pro**: $49/month
- **Team**: $99/month
- **Enterprise**: Custom pricing

### Checkout Flow

1. **User clicks** "Subscribe" button
2. **Frontend calls** `/api/checkout/create`
3. **Backend creates** Stripe Checkout Session
4. **Metadata added** (userId, licenseType, product)
5. **User redirected** to Stripe hosted checkout
6. **Payment processed** by Stripe
7. **Webhook received** at `/api/webhooks/stripe`
8. **License created** in database

### Webhook Events Handled

#### `checkout.session.completed`
- Extracts `userId` and `licenseType` from metadata
- Creates or updates License record
- Sets status to `ACTIVE`
- Links Stripe customer/subscription IDs

#### `invoice.payment_succeeded`
- Fallback license creation (if checkout didn't create it)
- Updates license period dates
- Creates Payment record
- Handles recurring payments

#### `invoice.payment_failed`
- Marks license as `EXPIRED`
- Notifies user (TODO: Email notification)

#### `customer.subscription.deleted`
- Marks license as `CANCELLED`
- Sets `cancelledAt` timestamp

#### `customer.subscription.updated`
- Updates license period dates
- Updates status based on subscription status

### Webhook Security

- **Signature verification** using `STRIPE_WEBHOOK_SECRET`
- **Idempotency** via `WebhookEvent` table
- **Event deduplication** prevents double-processing

---

## 📊 Metrics & Monitoring Integration

### Metrics Flow

```
Resonance Agent (Render.com)
    │
    │ HTTP GET /health
    │ HTTP GET /metrics (protected)
    │
    ▼
Next.js API Route: /api/metrics
    │
    │ Fetches from agent
    │ Parses Prometheus metrics
    │ Returns JSON
    │
    ▼
Dashboard Client (React)
    │
    │ Polls every 5 seconds
    │ Updates state
    │
    ▼
Real-time UI Updates
```

### Metrics Proxy (`/api/metrics`)

**Purpose**: Proxy between frontend and Resonance agent

**Flow**:
1. **Determines environment** (production vs development)
2. **Gets agent URLs** from environment variables:
   - `RESONANCE_AGENT_URL` (health endpoint)
   - `RESONANCE_METRICS_URL` (metrics endpoint)
3. **Adds API key** if `RESONANCE_API_KEY` is set
4. **Fetches health** endpoint (public)
5. **Fetches metrics** endpoint (protected, Prometheus format)
6. **Parses Prometheus** metrics:
   - `resonance_R` → Global coherence R(t)
   - `resonance_K` → Coupling strength K(t)
   - `resonance_spectral_entropy` → Spectral entropy
   - `resonance_mode` → Controller mode
   - `resonance_p99_latency_ms` → P99 latency (if available)
7. **Returns JSON** with all metrics

**Fallback Behavior**:
- If agent not accessible → Returns mock data
- If agent URL not configured → Returns mock data with error message
- Always returns 200 (so UI can display status)

### Dashboard Components

#### Main Dashboard (`/dashboard`)
- **License status** card
- **Quick stats** (Agent status, Features, Data retention)
- **Payment history**
- **Recent metrics**
- **Quick actions** (View Monitoring, Manage Subscription)

#### Canary Dashboard (`/dashboard/canary`)
- **Real-time R(t) graph** with historical data
- **Time interval selector** (Real-time, Hourly, Daily, Monthly, Quarterly, Yearly)
- **Supporting metrics** (Latency P99, Spectral Entropy, Controller Mode)
- **AI Insights** panel
- **System Information** panel (Agent status, environment, URLs, data points)
- **Canary validation progress** bar

---

## 🔌 API Endpoints

### Authentication

#### `POST /api/auth/register`
**Purpose**: User registration

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe" (optional)
}
```

**Response**:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "createdAt": "2025-01-01T00:00:00Z"
  }
}
```

**Security**:
- Rate limiting: 3 registrations/hour per IP
- Password validation: zxcvbn score ≥ 3, min 12 chars
- Email uniqueness check

#### `GET /api/auth/register`
**Purpose**: Diagnostic endpoint (for debugging)

**Response**: Database connection status, environment variables, etc.

### Checkout

#### `POST /api/checkout/create`
**Purpose**: Create Stripe checkout session

**Request**:
```json
{
  "licenseType": "pro",
  "product": "resonance" (optional, defaults to "resonance")
}
```

**Response**:
```json
{
  "sessionId": "cs_test_...",
  "url": "https://checkout.stripe.com/..."
}
```

**Security**:
- Requires authentication (NextAuth session)
- Stripe handles payment processing (PCI-DSS compliant)

### Metrics

#### `GET /api/metrics`
**Purpose**: Proxy to Resonance agent metrics

**Response**:
```json
{
  "R": 0.52,
  "K": 0.3,
  "spectralEntropy": 0.45,
  "mode": "adaptive",
  "modeValue": 2,
  "p99Latency": 230,
  "p50Latency": 120,
  "latencyImprovement": 12,
  "timestamp": "2025-01-01T00:00:00Z",
  "agentUrl": "https://...",
  "agentConnected": true,
  "environment": "production",
  "error": null (if error occurred)
}
```

**Security**:
- Public endpoint (no auth required)
- Returns mock data if agent not accessible
- Agent metrics endpoint protected by API key

### Dashboard

#### `GET /api/dashboard/license`
**Purpose**: Get user's license information

**Response**:
```json
{
  "license": {
    "id": "uuid",
    "type": "PRO",
    "status": "ACTIVE",
    "currentPeriodEnd": "2025-12-06T00:00:00Z",
    ...
  },
  "allLicenses": [...],
  "userId": "uuid",
  "email": "user@example.com"
}
```

**Security**:
- Requires authentication (NextAuth session)
- Returns 401 if not authenticated

### Stripe Webhooks

#### `POST /api/webhooks/stripe`
**Purpose**: Handle Stripe webhook events

**Events Handled**:
- `checkout.session.completed`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `customer.subscription.deleted`
- `customer.subscription.updated`

**Security**:
- Signature verification using `STRIPE_WEBHOOK_SECRET`
- Idempotency via database (WebhookEvent table)

---

## 🔐 Security Features

### Authentication & Authorization

1. **NextAuth.js**:
   - JWT-based sessions (15-minute lifetime)
   - Database-backed session storage
   - Secure password hashing (bcrypt)

2. **Password Security**:
   - Minimum 12 characters
   - zxcvbn strength validation (score ≥ 3)
   - bcrypt hashing (10 rounds)

3. **Account Protection**:
   - Rate limiting (registration, login, password reset)
   - Account lockout after 5 failed attempts (15 min cooldown)
   - MFA support (TOTP, backup codes)

### API Security

1. **Rate Limiting**:
   - Upstash Redis (optional, graceful degradation)
   - Registration: 3/hour per IP
   - Login: 5/15 minutes per IP
   - Password reset: 3/hour per email

2. **CORS**:
   - Configured in middleware
   - Restricted to trusted origins

3. **CSP (Content Security Policy)**:
   - Strict script-src (allows Stripe, vercel.live)
   - Frame-src (Stripe, vercel.live)
   - Connect-src (Stripe API, vercel.live)

### Data Security

1. **Database**:
   - Connection pooling (Supabase)
   - SSL required
   - Password hashing (never stored plaintext)

2. **Environment Variables**:
   - Sensitive data in Vercel environment variables
   - Never committed to git
   - Separate values for Production/Preview/Development

3. **API Keys**:
   - Stripe keys (secret + publishable)
   - Resonance agent API key
   - Database connection strings

---

## 🚀 Deployment Architecture

### Production Deployment

#### Frontend (Vercel)
- **Platform**: Vercel (Next.js optimized)
- **URL**: `https://resonance.syncscript.app`
- **Build**: `npm run build` (includes Prisma generate)
- **Runtime**: Node.js (serverless functions)
- **Edge Runtime**: Middleware (security headers)

#### Database (Supabase)
- **Provider**: Supabase (PostgreSQL)
- **Connection**: Connection pooler (port 6543) recommended
- **SSL**: Required
- **Migrations**: Prisma migrations

#### Resonance Agent (Render.com)
- **Platform**: Render.com (Web Service)
- **URL**: `https://syncscript-backend-1.onrender.com`
- **Endpoints**:
  - `/health` (public)
  - `/metrics` (protected, requires API key)
- **Port**: Uses Render's `PORT` environment variable

### Environment Variables

#### Vercel (Frontend)

**Required**:
- `DATABASE_URL` - PostgreSQL connection string (Supabase)
- `NEXTAUTH_SECRET` - JWT signing secret
- `NEXTAUTH_URL` - Frontend URL (`https://resonance.syncscript.app`)
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret
- `STRIPE_RESONANCE_STARTER` - Stripe Price ID (Starter)
- `STRIPE_RESONANCE_PRO` - Stripe Price ID (Pro)
- `STRIPE_RESONANCE_ENTERPRISE` - Stripe Price ID (Enterprise)

**Optional**:
- `RESONANCE_AGENT_URL` - Agent health endpoint URL
- `RESONANCE_METRICS_URL` - Agent metrics endpoint URL
- `RESONANCE_API_KEY` - API key for agent authentication
- `UPSTASH_REDIS_REST_URL` - Redis URL (for rate limiting)
- `UPSTASH_REDIS_REST_TOKEN` - Redis token (for rate limiting)

**Stripe Price IDs**:
- `STRIPE_SYNCSCRIPT_PRO` - Syncscript Pro price ID
- `STRIPE_SYNCSCRIPT_TEAM` - Syncscript Team price ID
- `STRIPE_SYNCSCRIPT_ENTERPRISE` - Syncscript Enterprise price ID

#### Render.com (Agent)

**Required**:
- `PORT` - Port to bind to (Render sets this automatically)
- `RESONANCE_API_KEY` - API key for metrics endpoint protection
- `RESONANCE_MODE` - Mode: `observe`, `shadow`, `adaptive`, `active`

**Optional**:
- `RESONANCE_CONFIG_FILE` - Path to config file
- `RESONANCE_METRICS_PORT` - Metrics endpoint port
- `RESONANCE_HEALTH_PORT` - Health endpoint port

---

## 🔄 Data Flow

### User Registration → License Activation

```
1. User registers
   ↓
2. Account created in database
   ↓
3. User clicks "Subscribe" on pricing page
   ↓
4. Stripe Checkout Session created
   ↓
5. User completes payment on Stripe
   ↓
6. Stripe webhook: checkout.session.completed
   ↓
7. License created in database (status: ACTIVE)
   ↓
8. User redirected to dashboard
   ↓
9. Dashboard shows license status
```

### Metrics Collection → Dashboard Display

```
1. Resonance Agent running (Render.com)
   - Collects metrics every second
   - Exposes /health and /metrics endpoints
   ↓
2. Dashboard polls /api/metrics every 5 seconds
   ↓
3. /api/metrics fetches from agent
   - GET /health (public)
   - GET /metrics (protected, with API key)
   ↓
4. Prometheus metrics parsed
   - resonance_R → R(t)
   - resonance_K → K(t)
   - resonance_spectral_entropy → Entropy
   - resonance_mode → Mode
   ↓
5. JSON response sent to frontend
   ↓
6. React state updated
   ↓
7. UI re-renders with new metrics
   - Graph updates
   - Metrics cards update
   - System info updates
```

---

## 🎨 Frontend Architecture

### Page Structure

#### Landing Page (`/`)
- Hero section
- Features overview
- Pricing teaser
- Call-to-action

#### Authentication Pages
- `/auth/signin` - Login form
- `/auth/signup` - Registration form
- `/auth/forgot-password` - Password reset request

#### Dashboard Pages
- `/dashboard` - Main dashboard (license status, quick stats)
- `/dashboard/canary` - Canary monitoring (real-time metrics, graphs)

#### Pricing Pages
- `/pricing` - General pricing (redirects to Resonance pricing)
- `/resonance/pricing` - Resonance-specific pricing
- `/syncscript/pricing` - Syncscript-specific pricing

#### Legal Pages
- `/privacy` - Privacy policy
- `/terms` - Terms of service
- `/contact` - Contact form

### Component Architecture

#### Client Components
- `DashboardClient.tsx` - Agent status indicator (client-side polling)
- `CheckoutButton.tsx` - Stripe checkout button
- Dashboard pages use `'use client'` for interactivity

#### Server Components
- Most pages are server components (default in App Router)
- Fetch data directly from database (Prisma)
- No client-side JavaScript needed

### State Management

- **React Hooks**: `useState`, `useEffect` for local state
- **NextAuth Session**: Server-side session management
- **No Redux/Zustand**: Keeping it simple with React state

### Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Responsive Design**: Mobile-first approach
- **Design System**: Custom colors via `tailwind.config.js`

---

## 🔧 Key Files & Their Purposes

### Configuration Files

#### `next.config.js`
- Next.js configuration
- React strict mode enabled
- Server actions body size limit: 2MB

#### `tailwind.config.js`
- Tailwind CSS configuration
- Custom color palette (primary colors)
- Responsive breakpoints

#### `tsconfig.json`
- TypeScript configuration
- Path aliases (`@/` → root directory)
- Strict type checking

#### `middleware.ts`
- Edge middleware (runs on every request)
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- CSP configuration for Stripe and Vercel Live

### Core Library Files

#### `lib/db.ts`
- Prisma client singleton
- Prevents multiple Prisma client instances
- Used throughout app for database access

#### `lib/auth/config.ts`
- NextAuth configuration
- Credentials provider setup
- Session callbacks
- JWT configuration

#### `lib/stripe/config.ts`
- Stripe client initialization
- Price ID retrieval functions
- Graceful handling when Stripe not configured

#### `lib/stripe/checkout.ts`
- Checkout session creation
- Supports both Resonance and Syncscript products
- Metadata handling for webhooks

#### `lib/stripe/webhooks.ts`
- Webhook signature verification
- Event handlers (checkout, invoice, subscription)
- License creation/updates
- Payment recording

---

## 🔌 Integration Points

### How to Integrate Resonance Agent

#### 1. Set Up Agent

Deploy Resonance agent to Render.com (or any public URL):
- Health endpoint: `/health` (public)
- Metrics endpoint: `/metrics` (protected)

#### 2. Configure Environment Variables

In Vercel, add:
- `RESONANCE_AGENT_URL` = `https://your-agent-url.com/health`
- `RESONANCE_METRICS_URL` = `https://your-agent-url.com/metrics`
- `RESONANCE_API_KEY` = Your API key (for metrics endpoint)

#### 3. Dashboard Will Auto-Connect

The `/api/metrics` endpoint will:
- Fetch from your agent automatically
- Parse Prometheus metrics
- Return JSON to frontend
- Show "Agent Connected" status

### How to Add New Features

#### Adding a New Page

1. Create file: `app/your-page/page.tsx`
2. Export default component
3. Access at: `https://resonance.syncscript.app/your-page`

#### Adding a New API Route

1. Create file: `app/api/your-endpoint/route.ts`
2. Export `GET`, `POST`, etc. functions
3. Access at: `https://resonance.syncscript.app/api/your-endpoint`

#### Adding a New Database Model

1. Update `prisma/schema.prisma`
2. Run: `npx prisma migrate dev --name your_migration`
3. Use in code: `prisma.yourModel.create(...)`

---

## 📦 Dependencies Breakdown

### Core Dependencies

```json
{
  "next": "^14.2.0",              // Next.js framework
  "react": "^18.3.0",             // React library
  "react-dom": "^18.3.0",         // React DOM
  "typescript": "^5.3.3",         // TypeScript
  "@prisma/client": "^5.14.0",    // Database ORM client
  "prisma": "^5.14.0",            // Database ORM CLI
  "next-auth": "^4.24.5",         // Authentication
  "@next-auth/prisma-adapter": "^1.0.7", // NextAuth + Prisma
  "stripe": "^14.21.0",           // Stripe payments
  "bcryptjs": "^2.4.3",           // Password hashing
  "zod": "^3.22.4",               // Schema validation
  "@zxcvbn-ts/core": "^2.0.1",    // Password strength
  "@upstash/ratelimit": "^1.1.0", // Rate limiting
  "@upstash/redis": "^1.34.0",    // Redis client
  "tailwindcss": "^3.4.1"         // CSS framework
}
```

### Development Dependencies

```json
{
  "@types/node": "^20.11.0",
  "@types/react": "^18.2.0",
  "@types/react-dom": "^18.2.0",
  "eslint": "^8.56.0",
  "eslint-config-next": "^14.2.0",
  "autoprefixer": "^10.4.17",
  "postcss": "^8.4.35"
}
```

---

## 🎯 Current Features

### ✅ Implemented

1. **User Authentication**
   - Registration with email/password
   - Login with NextAuth
   - Password reset (UI ready, email sending TODO)
   - MFA support (code ready, UI TODO)
   - Account lockout protection

2. **License Management**
   - Stripe subscription integration
   - License creation via webhooks
   - License status tracking
   - Payment history

3. **Dashboard**
   - Main dashboard with license info
   - Canary monitoring dashboard
   - Real-time metrics display
   - Historical R(t) graph
   - Time interval selector
   - System information panel
   - AI insights panel

4. **Pricing Pages**
   - Resonance pricing
   - Syncscript pricing
   - Promotional pricing support
   - Stripe checkout integration

5. **Security**
   - Rate limiting
   - Password strength validation
   - CSP headers
   - Secure session management
   - API key authentication for agent

### 🚧 TODO / Future Enhancements

1. **Email Notifications**
   - Password reset emails
   - Payment failure notifications
   - Subscription renewal reminders

2. **Admin Dashboard**
   - User management
   - License analytics
   - System health monitoring

3. **Advanced Features**
   - License usage tracking
   - API key management
   - Webhook configuration
   - Custom dashboards

4. **Integration Features**
   - OAuth providers (Google, GitHub)
   - SSO for Enterprise
   - API access for programmatic license management

---

## 🚀 Deployment Guide

### Prerequisites

1. **Vercel Account** (for frontend hosting)
2. **Supabase Account** (for database)
3. **Stripe Account** (for payments)
4. **Render.com Account** (for Resonance agent - optional)
5. **GitHub Repository** (for code)

### Deployment Steps

#### 1. Database Setup

```bash
# Create Supabase project
# Get connection string
# Update DATABASE_URL in Vercel

# Run migrations
npx prisma migrate deploy
```

#### 2. Stripe Setup

1. Create products in Stripe Dashboard
2. Create prices for each product
3. Copy Price IDs
4. Add to Vercel environment variables:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_RESONANCE_STARTER`
   - `STRIPE_RESONANCE_PRO`
   - `STRIPE_RESONANCE_ENTERPRISE`

#### 3. Vercel Deployment

1. Connect GitHub repository
2. Configure environment variables
3. Deploy automatically on push

#### 4. Custom Domain

1. Add domain in Vercel
2. Update DNS (CNAME to Vercel)
3. SSL automatically provisioned

---

## 🔍 How Metrics Flow

### Agent → Dashboard Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Resonance Agent (Render.com)                               │
│  - Collects metrics continuously                            │
│  - Exposes Prometheus metrics at /metrics                   │
│  - Exposes health at /health                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP GET
                       │ (with API key for /metrics)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Next.js API Route: /api/metrics                            │
│  - Fetches from agent                                       │
│  - Parses Prometheus format                                 │
│  - Returns JSON                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ fetch() every 5 seconds
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  React Dashboard Component                                  │
│  - Updates state with new metrics                           │
│  - Re-renders graph, cards, etc.                            │
│  - Stores history for graph                                 │
└─────────────────────────────────────────────────────────────┘
```

### Prometheus Metrics Format

The agent exposes metrics in Prometheus format:

```
resonance_R 0.52
resonance_K 0.3
resonance_spectral_entropy 0.45
resonance_mode{value="adaptive"} 2
resonance_p99_latency_ms 230
resonance_p50_latency_ms 120
```

These are parsed by `/api/metrics` and converted to JSON.

---

## 🎨 UI/UX Patterns

### Design System

- **Primary Color**: Blue (`primary-600`, `primary-700`)
- **Success**: Green
- **Warning**: Yellow
- **Error**: Red
- **Gray Scale**: For text and backgrounds

### Component Patterns

#### Cards
- White background
- Border: `border-gray-200`
- Shadow: `shadow-sm`
- Padding: `p-6`
- Rounded: `rounded-lg`

#### Buttons
- Primary: `bg-primary-600 text-white`
- Hover: `hover:bg-primary-700`
- Disabled: `disabled:opacity-50`

#### Forms
- Inputs: `border border-gray-300 rounded-md`
- Focus: `focus:ring-2 focus:ring-primary-500`
- Labels: `text-sm font-medium text-gray-700`

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] User registration
- [ ] User login
- [ ] Password reset
- [ ] License purchase (Stripe checkout)
- [ ] Webhook processing
- [ ] Dashboard display
- [ ] Metrics fetching
- [ ] License status display
- [ ] Payment history
- [ ] Agent connection status

### API Testing

```bash
# Test registration
curl -X POST https://resonance.syncscript.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepass123"}'

# Test metrics (public)
curl https://resonance.syncscript.app/api/metrics

# Test license (requires auth cookie)
curl https://resonance.syncscript.app/api/dashboard/license \
  -H "Cookie: next-auth.session-token=..."
```

---

## 📚 Extension Guide

### Adding a New Product

1. **Update Prisma Schema**:
   - Add new product type enum
   - Add new license type enum

2. **Update Stripe Config**:
   - Add price ID environment variable
   - Add price ID retrieval function

3. **Update Checkout**:
   - Add checkout session creation function
   - Update webhook handlers

4. **Update UI**:
   - Add pricing page
   - Add checkout button

### Adding a New Dashboard View

1. **Create Page**: `app/dashboard/your-view/page.tsx`
2. **Add Navigation**: Link from main dashboard
3. **Fetch Data**: Use Prisma or API routes
4. **Display Metrics**: Use existing components or create new ones

### Adding a New API Endpoint

1. **Create Route**: `app/api/your-endpoint/route.ts`
2. **Export Handler**: `export async function GET/POST(req: NextRequest)`
3. **Handle Auth**: Check session if needed
4. **Return Response**: `NextResponse.json(...)`

---

## 🔐 Security Best Practices

### Already Implemented

- ✅ Password hashing (bcrypt)
- ✅ Password strength validation
- ✅ Rate limiting
- ✅ Account lockout
- ✅ CSP headers
- ✅ Secure session management
- ✅ API key authentication
- ✅ Webhook signature verification

### Recommended Additions

- [ ] Email verification
- [ ] 2FA enforcement for Enterprise
- [ ] API rate limiting per user
- [ ] Audit logging
- [ ] IP whitelisting for admin
- [ ] Session timeout warnings
- [ ] Password expiration (Enterprise)

---

## 📊 Monitoring & Observability

### Current Monitoring

1. **Vercel Analytics**: Built-in (if enabled)
2. **Error Tracking**: Console logs (consider Sentry)
3. **Database Monitoring**: Supabase dashboard
4. **Stripe Dashboard**: Payment monitoring

### Recommended Additions

- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (Vercel Analytics)
- [ ] Uptime monitoring (UptimeRobot, etc.)
- [ ] Log aggregation (Logtail, etc.)

---

## 🎯 Business Logic

### License Tiers

#### Resonance Starter
- Price: $29/month (Launch), $49/month (Standard)
- Features: Basic monitoring, Core metrics

#### Resonance Pro
- Price: $99/month (Launch), $149/month (Standard)
- Features: Advanced analytics, Spectral panel, PLV map, Explainability, Policy editor

#### Resonance Enterprise
- Price: Custom
- Features: Everything in Pro + Fleet policy, SSO, Custom adapters, On-premise, SLA

### Subscription Flow

1. **Trial Period**: 14 days (if enabled)
2. **Payment**: Stripe subscription (monthly)
3. **Renewal**: Automatic (Stripe handles)
4. **Cancellation**: Via Stripe or dashboard (TODO)
5. **Downgrade/Upgrade**: Via Stripe or dashboard (TODO)

---

## 🔗 Integration with Resonance Agent

### How They Work Together

1. **Agent** (Render.com):
   - Runs on customer's infrastructure (or Render)
   - Monitors application performance
   - Applies runtime optimizations
   - Exposes metrics via Prometheus

2. **Webapp** (Vercel):
   - Provides user interface
   - Manages licenses and subscriptions
   - Fetches metrics from agent
   - Displays dashboards and insights

3. **Connection**:
   - Webapp → Agent: HTTP requests (public health, protected metrics)
   - Agent → Webapp: Metrics exposed via HTTP
   - No direct agent → webapp push (polling model)

### Agent Configuration

The agent is configured via environment variables:
- `RESONANCE_MODE`: `observe`, `shadow`, `adaptive`, `active`
- `RESONANCE_API_KEY`: For protecting metrics endpoint
- `RESONANCE_METRICS_PORT`: Port for metrics (default: 9090)
- `RESONANCE_HEALTH_PORT`: Port for health (default: 8080)

---

## 🚨 Common Issues & Solutions

### Issue: "Agent not accessible"

**Cause**: Agent URL not configured or agent not running

**Solution**:
1. Check `RESONANCE_AGENT_URL` in Vercel
2. Verify agent is running on Render.com
3. Check agent health endpoint is public

### Issue: "Metrics showing N/A"

**Cause**: Agent not exposing latency metrics, or metrics endpoint not accessible

**Solution**:
1. Check agent is exposing Prometheus metrics
2. Verify `RESONANCE_METRICS_URL` is correct
3. Verify `RESONANCE_API_KEY` is set and correct
4. Check agent logs for errors

### Issue: "License not created after payment"

**Cause**: Webhook not processed or metadata missing

**Solution**:
1. Check Stripe webhook logs
2. Verify webhook secret is correct
3. Check webhook endpoint is accessible
4. Verify metadata is set in checkout session

### Issue: "Database connection error"

**Cause**: Wrong connection string or database paused

**Solution**:
1. Verify `DATABASE_URL` in Vercel
2. Check Supabase database is active (not paused)
3. Verify connection string format
4. Check network access (Supabase IP restrictions)

---

## 🎓 Learning Resources

### Next.js Documentation
- [Next.js App Router](https://nextjs.org/docs/app)
- [API Routes](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)
- [Server Components](https://nextjs.org/docs/app/building-your-application/rendering/server-components)

### Prisma Documentation
- [Prisma Client](https://www.prisma.io/docs/concepts/components/prisma-client)
- [Migrations](https://www.prisma.io/docs/concepts/components/prisma-migrate)

### NextAuth.js Documentation
- [NextAuth.js](https://next-auth.js.org/)
- [Configuration](https://next-auth.js.org/configuration/options)

### Stripe Documentation
- [Checkout Sessions](https://stripe.com/docs/api/checkout/sessions)
- [Webhooks](https://stripe.com/docs/webhooks)

---

## 📝 Next Steps for Development

### Immediate Enhancements

1. **Email System**
   - Set up Resend or SendGrid
   - Implement password reset emails
   - Payment failure notifications

2. **Admin Dashboard**
   - User management
   - License analytics
   - System health overview

3. **Advanced Features**
   - License usage tracking
   - API key management
   - Custom dashboards

### Long-Term Roadmap

1. **Enterprise Features**
   - SSO integration
   - On-premise deployment
   - Custom integrations

2. **Analytics**
   - Usage analytics
   - Revenue analytics
   - Customer insights

3. **Developer Experience**
   - API documentation
   - SDK improvements
   - Integration guides

---

## 🎉 Summary

**Resonance.syncscript.app** is a complete SaaS platform built with:

- **Next.js 14** (App Router) for the frontend and API
- **PostgreSQL** (Supabase) for data storage
- **Stripe** for payment processing
- **NextAuth.js** for authentication
- **Prisma** for database access

It provides:
- ✅ User authentication and management
- ✅ License/subscription management
- ✅ Real-time metrics dashboard
- ✅ Stripe payment integration
- ✅ Security best practices

**Ready to extend and customize for your needs!**

---

**Last Updated**: January 2025  
**Version**: 1.0.1  
**Status**: Production Ready ✅

