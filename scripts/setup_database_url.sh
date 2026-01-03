#!/bin/bash

# Helper script to set DATABASE_URL and run migration
# You need to get the password from Supabase Dashboard

echo "🔧 Database Migration Setup"
echo ""
echo "Your Supabase project: quicksync-db"
echo "Project ref: mdykctkqzpyoyqaxywvb"
echo "Database host: db.mdykctkqzpyoyqaxywvb.supabase.co"
echo ""
echo "To get your database password:"
echo "1. Go to: https://supabase.com/dashboard/project/mdykctkqzpyoyqaxywvb"
echo "2. Click: Settings → Database"
echo "3. Under 'Database password', click 'Reset database password' or copy existing"
echo ""
read -p "Enter your database password: " -s DB_PASSWORD
echo ""

if [ -z "$DB_PASSWORD" ]; then
  echo "❌ Password is required"
  exit 1
fi

# Construct connection string (use port 5432 for direct connection, not pooler)
export DATABASE_URL="postgresql://postgres.mdykctkqzpyoyqaxywvb:${DB_PASSWORD}@db.mdykctkqzpyoyqaxywvb.supabase.co:5432/postgres?sslmode=require"

echo ""
echo "✅ DATABASE_URL set"
echo ""
echo "Running Prisma migration..."
echo ""

npx prisma generate
npx prisma db push

echo ""
echo "✅ Migration complete!"

