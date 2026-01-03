#!/bin/bash

# Commands to add SMTP settings to Vercel
# Run these commands one by one and enter the values when prompted

echo "📧 Adding SMTP Environment Variables to Vercel"
echo "================================================"
echo ""
echo "You'll be prompted to enter values for each variable."
echo "For SMTP_PASS, enter your Migadu mailbox password."
echo ""
echo "Press Enter to start..."
read

# SMTP_HOST
echo ""
echo "1/5 Adding SMTP_HOST..."
vercel env add SMTP_HOST production
vercel env add SMTP_HOST preview  
vercel env add SMTP_HOST development

# SMTP_PORT
echo ""
echo "2/5 Adding SMTP_PORT..."
vercel env add SMTP_PORT production
vercel env add SMTP_PORT preview
vercel env add SMTP_PORT development

# SMTP_USER
echo ""
echo "3/5 Adding SMTP_USER..."
vercel env add SMTP_USER production
vercel env add SMTP_USER preview
vercel env add SMTP_USER development

# SMTP_PASS
echo ""
echo "4/5 Adding SMTP_PASS..."
echo "⚠️  When prompted, enter your Migadu mailbox password"
vercel env add SMTP_PASS production
vercel env add SMTP_PASS preview
vercel env add SMTP_PASS development

# SMTP_FROM
echo ""
echo "5/5 Adding SMTP_FROM..."
vercel env add SMTP_FROM production
vercel env add SMTP_FROM preview
vercel env add SMTP_FROM development

echo ""
echo "✅ Done! All variables added."
echo ""
echo "Values you should have entered:"
echo "  SMTP_HOST: smtp.migadu.com"
echo "  SMTP_PORT: 587"
echo "  SMTP_USER: info@quicksync.app"
echo "  SMTP_PASS: [your Migadu password]"
echo "  SMTP_FROM: QuickSync <info@quicksync.app>"

