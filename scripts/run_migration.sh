#!/bin/bash

# Database Migration Script for QuickSync
# This script runs Prisma migrations to create/update database tables

set -e

echo "🔄 Running database migration..."
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
  echo "❌ DATABASE_URL environment variable is not set"
  echo ""
  echo "Please set it with one of these methods:"
  echo ""
  echo "Option 1: From Vercel (recommended)"
  echo "  vercel env pull .env.production"
  echo "  source .env.production"
  echo "  ./scripts/run_migration.sh"
  echo ""
  echo "Option 2: Direct export"
  echo "  export DATABASE_URL='postgresql://user:password@host:port/db'"
  echo "  ./scripts/run_migration.sh"
  echo ""
  echo "Option 3: Inline"
  echo "  DATABASE_URL='postgresql://...' ./scripts/run_migration.sh"
  exit 1
fi

echo "✓ DATABASE_URL is set"
echo ""

# Generate Prisma client
echo "🔨 Generating Prisma client..."
npx prisma generate

echo ""

# Push schema to database
echo "📊 Pushing schema to database..."
npx prisma db push

echo ""
echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Test the auth endpoint: curl -X POST https://quicksync.app/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\"}'"
echo "2. Deploy the code changes: git push (or vercel --prod)"

