#!/bin/bash

# Script to add Sentry DSN to Vercel environment variables
# Usage: ./scripts/add_sentry_dsn_to_vercel.sh

set -e

SENTRY_DSN="https://60f78090eb56baab93e466a1c170aa18@o4510642039685120.ingest.us.sentry.io/4510642041651200"

echo "🔧 Adding Sentry DSN to Vercel"
echo "================================================"
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
  echo "❌ Vercel CLI not found. Install it with: npm install -g vercel"
  exit 1
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
  echo "❌ Not logged in to Vercel. Run: vercel login"
  exit 1
fi

echo "📝 Adding SENTRY_DSN to Production..."
vercel env add SENTRY_DSN production <<< "$SENTRY_DSN" || echo "⚠️  Failed to add to Production (may already exist)"

echo ""
echo "📝 Adding SENTRY_DSN to Preview..."
vercel env add SENTRY_DSN preview <<< "$SENTRY_DSN" || echo "⚠️  Failed to add to Preview (may already exist)"

echo ""
echo "📝 Adding NEXT_PUBLIC_SENTRY_DSN to Production..."
vercel env add NEXT_PUBLIC_SENTRY_DSN production <<< "$SENTRY_DSN" || echo "⚠️  Failed to add to Production (may already exist)"

echo ""
echo "📝 Adding NEXT_PUBLIC_SENTRY_DSN to Preview..."
vercel env add NEXT_PUBLIC_SENTRY_DSN preview <<< "$SENTRY_DSN" || echo "⚠️  Failed to add to Preview (may already exist)"

echo ""
echo "✅ Done!"
echo ""
echo "⚠️  Note: If you see errors above, the variables may already exist."
echo "   You can verify in Vercel dashboard: https://vercel.com/[your-team]/quicksync/settings/environment-variables"
echo ""
echo "🚀 Next step: Redeploy your application"
echo "   Run: vercel --prod"
echo "   Or: git push (if auto-deploy is enabled)"

