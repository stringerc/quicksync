#!/bin/bash

# Deploy script for QuickSync.app to Vercel
# Usage: ./scripts/deploy_vercel_quicksync.sh

set -e

echo "🚀 QuickSync.app Vercel Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

check_command() {
  if command -v "$1" &> /dev/null; then
    echo -e "${GREEN}✓${NC} $1 installed"
    return 0
  else
    echo -e "${RED}✗${NC} $1 not found"
    return 1
  fi
}

PREREQS_OK=true

check_command "node" || PREREQS_OK=false
check_command "npm" || PREREQS_OK=false
check_command "vercel" || PREREQS_OK=false

if [ "$PREREQS_OK" = false ]; then
  echo ""
  echo -e "${RED}❌ Prerequisites missing${NC}"
  echo ""
  echo "Please install:"
  echo "  - Node.js: https://nodejs.org/"
  echo "  - npm: Comes with Node.js"
  echo "  - Vercel CLI: npm install -g vercel"
  exit 1
fi

echo ""
echo "🔐 Checking Vercel authentication..."

# Check if logged in
if ! vercel whoami &> /dev/null; then
  echo -e "${YELLOW}⚠${NC} Not logged into Vercel"
  echo "Please run: vercel login"
  exit 1
fi

VERCEL_USER=$(vercel whoami 2>/dev/null)
echo -e "${GREEN}✓${NC} Logged in as: $VERCEL_USER"
echo ""

# Check for .env.production
if [ ! -f ".env.production" ]; then
  echo -e "${YELLOW}⚠${NC} .env.production not found"
  echo "Creating from template..."
  if [ -f ".env.production.example" ]; then
    cp .env.production.example .env.production
    echo -e "${YELLOW}⚠${NC} Please fill in .env.production with actual values"
    echo "See .env.production.example for documentation"
    exit 1
  else
    echo -e "${RED}❌${NC} .env.production.example not found"
    exit 1
  fi
fi

# Verify required env vars are set
echo "🔍 Checking environment variables..."

source .env.production 2>/dev/null || true

REQUIRED_VARS=(
  "DATABASE_URL"
  "STORAGE_TYPE"
  "AWS_S3_BUCKET"
  "AWS_ACCESS_KEY_ID"
  "AWS_SECRET_ACCESS_KEY"
  "STRIPE_SECRET_KEY"
  "STRIPE_PUBLISHABLE_KEY"
  "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY"
  "STRIPE_WEBHOOK_SECRET"
  "JWT_SECRET"
  "NEXT_PUBLIC_APP_URL"
  "ADMIN_EMAILS"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    MISSING_VARS+=("$var")
  fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
  echo -e "${RED}❌ Missing required environment variables:${NC}"
  for var in "${MISSING_VARS[@]}"; do
    echo "  - $var"
  done
  echo ""
  echo "Please fill in .env.production"
  exit 1
fi

echo -e "${GREEN}✓${NC} All required environment variables present"
echo ""

# Check if project is linked
if [ ! -f ".vercel/project.json" ]; then
  echo "🔗 Linking Vercel project..."
  echo "If you haven't created a project yet, you'll be prompted to create one."
  echo "Project name should be: quicksync"
  echo ""
  vercel link
else
  echo -e "${GREEN}✓${NC} Project already linked"
  PROJECT_ID=$(cat .vercel/project.json | grep -o '"projectId":"[^"]*' | cut -d'"' -f4)
  echo "  Project ID: $PROJECT_ID"
fi

echo ""

# Environment variables guide
echo "🔧 Environment Variables Setup"
echo -e "${YELLOW}⚠${NC} Environment variables must be set in Vercel Dashboard"
echo ""
echo "Option 1: Vercel Dashboard (Recommended)"
echo "  → Go to: https://vercel.com/[your-team]/quicksync/settings/environment-variables"
echo "  → Add each variable from .env.production"
echo ""
echo "Option 2: Vercel CLI (Interactive)"
echo "  Run: vercel env add <KEY> production"
echo "  (You'll be prompted to paste the value)"
echo ""
echo "Required variables:"
for var in "${REQUIRED_VARS[@]}"; do
  echo "  - $var"
done
echo ""
read -p "Have you set environment variables in Vercel? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo ""
  echo "Please set environment variables first."
  echo "See docs/DEPLOY_QUICKSYNC.md for detailed instructions"
  exit 1
fi
echo ""

# Generate Prisma client
echo "🔨 Generating Prisma client..."
npm run db:generate

echo ""

# Build locally to check for errors
echo "🔨 Building project..."
if npm run build; then
  echo -e "${GREEN}✓${NC} Build successful"
else
  echo -e "${RED}❌ Build failed${NC}"
  exit 1
fi

echo ""

# Deploy to production
echo "🚀 Deploying to production..."
echo "This will deploy to: https://quicksync.app"
echo ""

vercel --prod

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Set up DNS records (see docs/DEPLOY_QUICKSYNC.md)"
echo "2. Configure Stripe webhook (see docs/DEPLOY_QUICKSYNC.md)"
echo "3. Run database migration: vercel exec 'npx prisma db push'"
echo "   OR use Vercel CLI: vercel env pull .env.vercel && npx prisma db push"
echo "4. Run smoke tests (see docs/DEPLOY_QUICKSYNC.md)"
echo ""

