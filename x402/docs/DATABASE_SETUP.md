# Database Setup for QuickSync.app

## Recommendation: Vercel Postgres (Easiest)

For production, you need a PostgreSQL database. **Vercel Postgres is the easiest option** since everything is in one place.

## Option 1: Vercel Postgres (Recommended - 2 minutes)

### Step 1: Create Database in Vercel

1. Go to: https://vercel.com/dashboard
2. Create a new project OR use existing project named `quicksync`
3. After project is created, go to project dashboard
4. Click **"Storage"** tab (in the top menu)
5. Click **"Create Database"**
6. Select **"Postgres"**
7. Fill in:
   - **Database name**: `quicksync-db` (or any name)
   - **Region**: Choose closest to you (usually `Washington D.C.` or `Frankfurt`)
8. Click **"Create"**
9. Wait ~30 seconds for database to be created

### Step 2: Get Connection String

1. In the Storage tab, click on your database
2. Go to **".env.local"** tab
3. Copy the **`POSTGRES_URL`** value
   - It looks like: `postgres://default:password@host:5432/verceldb?sslmode=require`
4. This is your `DATABASE_URL`

### Step 3: Use in .env.production

Add to your `.env.production`:
```env
DATABASE_URL="postgres://default:password@host:5432/verceldb?sslmode=require"
# (Use the actual connection string from Vercel)
```

**That's it!** Vercel Postgres is ready to use.

---

## Option 2: External PostgreSQL (If You Prefer)

If you want to use an external database provider:

### Neon (Recommended External Option)

1. Go to: https://neon.tech
2. Sign up (free tier available)
3. Create a new project
4. Copy the connection string
5. Use as `DATABASE_URL`

### Supabase

1. Go to: https://supabase.com
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string
5. Use as `DATABASE_URL`

### Railway

1. Go to: https://railway.app
2. Create a new project
3. Add PostgreSQL database
4. Copy the connection string
5. Use as `DATABASE_URL`

**Format:** All connection strings should look like:
```
postgresql://user:password@host:port/database?sslmode=require
```

---

## After Database Setup

Once you have `DATABASE_URL`:
1. Add it to `.env.production`
2. After deployment, run: `npx prisma db push` to create tables
3. The go-live script will handle this automatically

---

## Quick Decision Guide

**Use Vercel Postgres if:**
- ✅ You want the simplest setup
- ✅ Everything in one place (Vercel)
- ✅ Free tier is sufficient for MVP

**Use External Database if:**
- ✅ You need more control
- ✅ You want to use existing database
- ✅ You need specific features

**For QuickSync.app MVP: Vercel Postgres is recommended** ⭐

