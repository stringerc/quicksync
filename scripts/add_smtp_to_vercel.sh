#!/bin/bash

# Add SMTP environment variables to Vercel
# Usage: ./scripts/add_smtp_to_vercel.sh

set -e

echo "📧 Adding SMTP Environment Variables to Vercel"
echo "================================================"
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
  echo "❌ Vercel CLI not found"
  echo "Please install: npm install -g vercel"
  exit 1
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
  echo "❌ Not logged into Vercel"
  echo "Please run: vercel login"
  exit 1
fi

echo "✓ Vercel CLI ready"
echo ""

# Prompt for password
read -sp "Enter your Migadu mailbox password for info@quicksync.app: " SMTP_PASS
echo ""

if [ -z "$SMTP_PASS" ]; then
  echo "❌ Password is required"
  exit 1
fi

echo ""
echo "Adding environment variables to Vercel..."
echo ""

# Add SMTP_HOST
echo "Adding SMTP_HOST..."
echo "smtp.migadu.com" | vercel env add SMTP_HOST production preview development

# Add SMTP_PORT
echo "Adding SMTP_PORT..."
echo "587" | vercel env add SMTP_PORT production preview development

# Add SMTP_USER
echo "Adding SMTP_USER..."
echo "info@quicksync.app" | vercel env add SMTP_USER production preview development

# Add SMTP_PASS
echo "Adding SMTP_PASS..."
echo "$SMTP_PASS" | vercel env add SMTP_PASS production preview development

# Add SMTP_FROM
echo "Adding SMTP_FROM..."
echo "QuickSync <info@quicksync.app>" | vercel env add SMTP_FROM production preview development

echo ""
echo "✅ All SMTP environment variables added successfully!"
echo ""
echo "Next steps:"
echo "1. Vercel will automatically use these on the next deployment"
echo "2. To redeploy immediately: vercel --prod"
echo "3. Test email functionality by signing up a new user"

