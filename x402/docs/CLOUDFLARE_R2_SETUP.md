# Cloudflare R2 Setup - Visual Guide

## Step-by-Step Instructions

### Step 1: Access Cloudflare Dashboard
1. Go to: https://dash.cloudflare.com
2. Log in with your Cloudflare account
3. Select your account (or create one if needed - it's free)

### Step 2: Create R2 Bucket
1. In the left sidebar, click **"R2"** (or "Workers & Pages" → "R2")
2. If you see "Get started" or "Create bucket", click it
3. Click **"Create bucket"** button
4. Enter bucket name: `quicksync-app` (or any name you prefer)
5. Click **"Create bucket"**

### Step 3: Create API Token
1. In R2 dashboard, click **"Manage R2 API Tokens"** (usually at top or in settings)
2. Click **"Create API token"** button
3. Fill in:
   - **Token name**: `quicksync-r2-token` (or any name)
   - **Permissions**: Select **"Object Read & Write"**
4. Click **"Create API token"**
5. **IMPORTANT**: Copy BOTH values immediately (you can only see the secret once):
   - **Access Key ID** (starts with something like: `a1b2c3d4e5f6...`)
   - **Secret Access Key** (long random string)

### Step 4: Get Your Account ID
1. Look at the R2 dashboard URL - it might be: `https://dash.cloudflare.com/.../r2/...`
2. OR click on your bucket name
3. OR go to any R2 API endpoint URL shown
4. Find your **Account ID** (usually in the format: `abc123def456` or shown in the endpoint URL)
5. The endpoint URL format is: `https://<account-id>.r2.cloudflarestorage.com`

### Step 5: Use These Values in .env.production

Once you have:
- Access Key ID
- Secret Access Key  
- Account ID

I'll help you create the complete .env.production file.

## Quick Checklist

- [ ] Created R2 bucket: `quicksync-app`
- [ ] Created API token with "Object Read & Write" permissions
- [ ] Copied Access Key ID
- [ ] Copied Secret Access Key
- [ ] Found Account ID (from URL or dashboard)

## If You Get Stuck

**Can't find R2?**
- Make sure you're logged into Cloudflare
- R2 might be under "Workers & Pages" → "R2" in some accounts
- Or search for "R2" in the Cloudflare dashboard

**Can't find API Tokens?**
- Look for "Manage R2 API Tokens" in the R2 section
- Or "API Tokens" in R2 settings
- Sometimes it's in a dropdown menu or gear icon

**Can't find Account ID?**
- Check the URL when viewing your bucket: `https://dash.cloudflare.com/<account-id>/r2/...`
- Or look at the R2 API endpoint examples in the dashboard
- Or contact Cloudflare support

