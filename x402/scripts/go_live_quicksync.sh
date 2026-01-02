#!/bin/bash

# Go-Live Script for QuickSync.app
# Runs preflight checks, deploys, migrates DB, and executes smoke tests

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROD_URL="https://quicksync.app"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 QuickSync.app GO-LIVE SEQUENCE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Preflight Checks
echo -e "${BLUE}📋 PREFLIGHT CHECKS${NC}"
echo "────────────────────────────────────────────────────────────"

# Check required commands
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
  echo -e "\n${RED}❌ Prerequisites missing${NC}"
  exit 1
fi

# Check Vercel auth
if ! vercel whoami &> /dev/null; then
  echo -e "${RED}✗${NC} Not logged into Vercel"
  echo "Run: vercel login"
  exit 1
fi
VERCEL_USER=$(vercel whoami 2>/dev/null)
echo -e "${GREEN}✓${NC} Logged in as: $VERCEL_USER"

# Check .env.production exists
if [ ! -f ".env.production" ]; then
  echo -e "${YELLOW}⚠${NC} .env.production not found"
  if [ -f ".env.production.example" ]; then
    echo "Creating from template..."
    cp .env.production.example .env.production
    echo -e "${YELLOW}⚠${NC} Please fill in .env.production with actual values"
    exit 1
  else
    echo -e "${RED}❌${NC} .env.production.example not found"
    exit 1
  fi
fi
echo -e "${GREEN}✓${NC} .env.production exists"

# Check required env vars in .env.production
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
  "JWT_SECRET"
  "NEXT_PUBLIC_APP_URL"
  "ADMIN_EMAILS"
)
# STRIPE_WEBHOOK_SECRET is optional for initial deployment (added after webhook creation)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    MISSING_VARS+=("$var")
  fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
  echo -e "${RED}✗${NC} Missing required variables in .env.production:"
  for var in "${MISSING_VARS[@]}"; do
    echo "   - $var"
  done
  exit 1
fi
echo -e "${GREEN}✓${NC} All required environment variables present"

# Check NEXT_PUBLIC_APP_URL matches expected
if [ "$NEXT_PUBLIC_APP_URL" != "$PROD_URL" ]; then
  echo -e "${YELLOW}⚠${NC} NEXT_PUBLIC_APP_URL is '$NEXT_PUBLIC_APP_URL', expected '$PROD_URL'"
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

echo ""
echo -e "${BLUE}📦 DEPLOYMENT${NC}"
echo "────────────────────────────────────────────────────────────"

# Ask for confirmation
echo "This will deploy to production: $PROD_URL"
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Deployment cancelled"
  exit 1
fi

# Run deployment script
if [ -f "scripts/deploy_vercel_quicksync.sh" ]; then
  echo "Running deployment script..."
  ./scripts/deploy_vercel_quicksync.sh || {
    echo -e "\n${RED}❌ Deployment failed${NC}"
    exit 1
  }
else
  echo -e "${YELLOW}⚠${NC} Deployment script not found, running manual deploy..."
  vercel --prod || {
    echo -e "\n${RED}❌ Deployment failed${NC}"
    exit 1
  }
fi

echo ""
echo -e "${BLUE}🗄️  DATABASE MIGRATION${NC}"
echo "────────────────────────────────────────────────────────────"

echo "Applying database migrations..."
vercel env pull .env.vercel 2>/dev/null || {
  echo -e "${YELLOW}⚠${NC} Could not pull env vars, using local .env.production"
}

# Use DATABASE_URL from .env.production or .env.vercel
if [ -f ".env.vercel" ]; then
  source .env.vercel 2>/dev/null || true
fi

if [ -z "$DATABASE_URL" ]; then
  source .env.production 2>/dev/null || true
fi

if [ -z "$DATABASE_URL" ]; then
  echo -e "${RED}❌${NC} DATABASE_URL not found"
  exit 1
fi

# Run migration
echo "Running: npx prisma db push"
npx prisma db push || {
  echo -e "\n${RED}❌ Database migration failed${NC}"
  exit 1
}
echo -e "${GREEN}✓${NC} Database migration complete"

echo ""
echo -e "${BLUE}🧪 SMOKE TESTS${NC}"
echo "────────────────────────────────────────────────────────────"

# Wait a few seconds for deployment to propagate
echo "Waiting 10 seconds for deployment to propagate..."
sleep 10

# Run smoke tests
if [ -f "scripts/smoke_test_prod.js" ]; then
  echo "Running smoke tests against $PROD_URL..."
  PROD_URL="$PROD_URL" node scripts/smoke_test_prod.js
  TEST_EXIT_CODE=$?
else
  echo -e "${YELLOW}⚠${NC} Smoke test script not found"
  TEST_EXIT_CODE=0
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 GO/NO-GO REPORT${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ GO${NC} - All checks passed"
  echo ""
  echo "Production URL: $PROD_URL"
  echo ""
  echo "Next steps:"
  echo "1. Verify DNS is configured (see docs/GO_LIVE.md)"
  echo "2. Configure Stripe webhook (see docs/GO_LIVE.md)"
  echo "3. Test end-to-end flow manually"
  echo "4. Monitor Vercel logs for errors"
  exit 0
else
  echo -e "${RED}❌ NO-GO${NC} - Smoke tests failed"
  echo ""
  echo "Please review failures above and fix before going live."
  echo ""
  echo "To redeploy previous version:"
  echo "  vercel rollback"
  exit 1
fi

