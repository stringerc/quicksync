# Storage Setup: AWS S3 vs Cloudflare R2

## Quick Comparison

| Feature | AWS S3 | Cloudflare R2 |
|---------|--------|---------------|
| **Setup Time** | ~10 minutes | ~5 minutes |
| **Ease of Use** | Moderate | Very Easy |
| **Cost** | Pay per GB + egress fees | Pay per GB, **NO egress fees** |
| **Free Tier** | 5GB storage, limited requests | 10GB storage, 1M Class A requests |
| **Interface** | AWS Console (complex) | Cloudflare Dashboard (simple) |
| **Documentation** | Extensive | Good |
| **Best For** | Already have AWS account | Starting fresh, want simplicity |

## Recommendation: **Cloudflare R2** ⭐

**Why R2 is better for QuickSync.app:**
1. ✅ **Simpler setup** - fewer steps, cleaner interface
2. ✅ **No egress fees** - you won't pay for downloads (users download files frequently)
3. ✅ **Better free tier** - more generous limits
4. ✅ **Easier to manage** - simpler dashboard
5. ✅ **Same API** - uses S3-compatible API, so switching later is easy

**Choose AWS S3 if:**
- You already have an AWS account set up
- You're comfortable with AWS console
- You want the most standard solution
- Your organization requires AWS

---

## AWS S3 Setup (10 minutes)

### Step 1: Create S3 Bucket

1. Go to: https://console.aws.amazon.com/s3/
2. Make sure you're logged in to AWS
3. Click **"Create bucket"** button (orange button, top right)

4. Fill in the form:
   - **Bucket name**: `quicksync-app` (must be globally unique)
     - If taken, try: `quicksync-app-[yourname]` or `quicksync-prod`
   - **AWS Region**: Select `US East (N. Virginia) us-east-1` (or closest to you)
   - **Object Ownership**: Leave default (ACLs disabled)
   - **Block Public Access settings**: ✅ **KEEP ALL CHECKED** (private bucket)
   - **Bucket Versioning**: Disabled (unless you want it)
   - **Default encryption**: Enabled (recommended)
   - **Advanced settings**: Leave defaults

5. Click **"Create bucket"** at the bottom

### Step 2: Create IAM User for Access

1. Go to: https://console.aws.amazon.com/iam/
2. In the left sidebar, click **"Users"**
3. Click **"Create user"** button

4. **Step 1 - Specify user details:**
   - **User name**: `quicksync-s3-user`
   - **Provide user access to the AWS Management Console**: ❌ Leave unchecked
   - ✅ **Select "Provide user access to the AWS Management Console"**
   - Actually, UNCHECK this - we want programmatic access only
   - Click **"Next"**

5. **Step 2 - Set permissions:**
   - Select **"Attach policies directly"**
   - In search box, type: `AmazonS3FullAccess`
   - ✅ Check the box next to **"AmazonS3FullAccess"**
   - Click **"Next"**

6. **Step 3 - Review and create:**
   - Review the settings
   - Click **"Create user"**

7. **Step 4 - Save credentials:**
   - You'll see a success page
   - **IMPORTANT**: Click **"Create access key"** button
   - Select **"Application running outside AWS"**
   - Click **"Next"**
   - Add description (optional): `QuickSync S3 Access`
   - Click **"Create access key"**
   - **CRITICAL**: Copy BOTH values immediately:
     - **Access key ID** (starts with `AKIA...`)
     - **Secret access key** (click "Show" to reveal, long random string)
   - Click **"Done"**

⚠️ **Save these credentials securely** - you can't view the secret key again!

### Step 3: Use in .env.production

Add these to your `.env.production`:

```env
STORAGE_TYPE="s3"
AWS_REGION="us-east-1"
AWS_S3_BUCKET="quicksync-app"
AWS_ACCESS_KEY_ID="AKIA..."  # Your Access Key ID
AWS_SECRET_ACCESS_KEY="..."  # Your Secret Access Key
# Leave AWS_S3_ENDPOINT empty for AWS S3
```

---

## Cloudflare R2 Setup (5 minutes) ⭐ RECOMMENDED

### Step 1: Access Cloudflare Dashboard

1. Go to: https://dash.cloudflare.com
2. Log in (or create a free account)
3. Select your account

### Step 2: Enable R2 (First Time Only)

1. In the left sidebar, click **"R2"** (under "Workers & Pages")
2. If you see "Get started", click it
3. You may need to add a payment method (but R2 has a generous free tier)

### Step 3: Create Bucket

1. Click **"Create bucket"** button
2. **Bucket name**: `quicksync-app`
3. Click **"Create bucket"**

That's it! Bucket is created.

### Step 4: Create API Token

1. In R2 dashboard, click **"Manage R2 API Tokens"** (usually at the top)
2. Click **"Create API token"** button
3. Fill in:
   - **Token name**: `quicksync-r2-token`
   - **Permissions**: Select **"Object Read & Write"**
   - **TTL**: Leave default (no expiration)
4. Click **"Create API token"**
5. **IMPORTANT**: Copy BOTH values immediately (you can only see the secret once):
   - **Access Key ID** (looks like: `a1b2c3d4e5f6g7h8i9j0`)
   - **Secret Access Key** (long random string)

⚠️ **Save these credentials securely** - you can't view the secret key again!

### Step 5: Get Account ID

The Account ID is in the R2 endpoint URL. Here's how to find it:

1. Look at the URL when viewing your R2 bucket - it should be:
   `https://dash.cloudflare.com/<account-id>/r2/...`
2. OR in R2 dashboard, look for any API endpoint examples
3. OR go to any bucket settings - the Account ID is usually shown
4. The format is: `abc123def456` (alphanumeric string)

**Alternative method:**
- In R2 dashboard, if you see any API endpoint URLs, they'll be:
  `https://<account-id>.r2.cloudflarestorage.com`
- Extract the `<account-id>` part

### Step 6: Use in .env.production

Add these to your `.env.production`:

```env
STORAGE_TYPE="s3"
AWS_REGION="auto"
AWS_S3_BUCKET="quicksync-app"
AWS_ACCESS_KEY_ID="..."  # Your R2 Access Key ID
AWS_SECRET_ACCESS_KEY="..."  # Your R2 Secret Access Key
AWS_S3_ENDPOINT="https://<your-account-id>.r2.cloudflarestorage.com"
# Replace <your-account-id> with your actual Account ID from Step 5
```

**Example:**
If your Account ID is `abc123def456`, the endpoint would be:
```env
AWS_S3_ENDPOINT="https://abc123def456.r2.cloudflarestorage.com"
```

---

## Cost Comparison (Rough Estimates)

### AWS S3 (us-east-1)
- Storage: $0.023 per GB/month
- PUT requests: $0.005 per 1,000
- GET requests: $0.0004 per 1,000
- **Data transfer OUT**: $0.09 per GB (this adds up!)
- **First 1GB transfer free per month**

### Cloudflare R2
- Storage: $0.015 per GB/month (cheaper!)
- Class A operations (PUT): $4.50 per million
- Class B operations (GET): $0.36 per million
- **Data transfer OUT**: **FREE** (no egress fees!) ⭐

**For QuickSync.app (users download files):**
- R2 is significantly cheaper due to **no egress fees**
- If users download 100GB/month, AWS would charge ~$9, R2 charges $0

---

## Final Recommendation

**Use Cloudflare R2** because:
1. ✅ Faster setup (5 min vs 10 min)
2. ✅ No egress fees (users download frequently)
3. ✅ Simpler interface
4. ✅ Better free tier
5. ✅ Same API - easy to switch later if needed

---

## Next Steps After Choosing

Once you've set up your storage (S3 or R2), you'll have:
- Access Key ID
- Secret Access Key
- Bucket name
- (For R2) Account ID and Endpoint URL

Then I can help you:
1. Create your complete `.env.production` file
2. Set up the database (Vercel Postgres or external)
3. Run the deployment

