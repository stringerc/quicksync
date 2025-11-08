# Secure Agent Deployment Guide

## 🔒 Security Features Implemented

### ✅ Authentication
- **API Key Authentication**: Required for `/metrics` endpoint
- **Bearer Token Support**: `Authorization: Bearer <key>` or `X-API-Key: <key>`
- **Constant-Time Comparison**: Prevents timing attacks

### ✅ Rate Limiting
- **Per-IP Rate Limiting**: 100 requests/minute (configurable)
- **Automatic Cleanup**: Expired entries removed every 5 minutes
- **429 Status Code**: Returns rate limit exceeded when threshold hit

### ✅ Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`

### ✅ CORS Control
- **Configurable Origins**: Whitelist allowed origins
- **Preflight Support**: OPTIONS requests handled
- **Disabled by Default**: Only enabled if explicitly configured

### ✅ Health Endpoint
- **Public Access**: `/health` endpoint doesn't require authentication
- **Read-Only**: Returns only status information
- **No Sensitive Data**: Only exposes operational state

---

## 🚀 Deployment to resonance.syncscript.app

### Prerequisites

1. **Domain DNS Setup**:
   - Point `resonance.syncscript.app` to your deployment platform
   - A record or CNAME as required by your hosting provider

2. **SSL/TLS Certificate**:
   - HTTPS is mandatory (security headers require it)
   - Use Let's Encrypt or platform-managed certificates

3. **Generate API Key**:
   ```bash
   node -e "console.log(require('crypto').randomBytes(32).toString('base64url'))"
   ```
   Save this key securely!

---

## 📦 Deployment Options

### Option 1: Railway (Recommended - Easy & Secure)

**Why Railway?**
- ✅ Automatic HTTPS
- ✅ Environment variable management
- ✅ Docker support
- ✅ Built-in monitoring
- ✅ Easy domain setup

**Steps**:

1. **Create Railway Project**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Create project
   railway init
   ```

2. **Configure Environment Variables**:
   ```bash
   railway variables set RESONANCE_API_KEY=<your-generated-key>
   railway variables set RESONANCE_MODE=adaptive
   railway variables set RESONANCE_METRICS_PORT=9090
   railway variables set RESONANCE_HEALTH_PORT=8080
   railway variables set RESONANCE_RATE_LIMIT_MAX=100
   railway variables set RESONANCE_ALLOWED_ORIGINS=https://webapp-2kjkxxrpk-christopher-stringers-projects.vercel.app
   ```

3. **Deploy**:
   ```bash
   railway up
   ```

4. **Add Custom Domain**:
   - Railway Dashboard → Settings → Domains
   - Add: `resonance.syncscript.app`
   - Follow DNS instructions

---

### Option 2: Fly.io (Great for Global Distribution)

**Why Fly.io?**
- ✅ Global edge deployment
- ✅ Automatic HTTPS
- ✅ Built-in DDoS protection
- ✅ Easy scaling

**Steps**:

1. **Create `fly.toml`**:
   ```toml
   app = "resonance-agent"
   primary_region = "iad"

   [build]
     dockerfile = "deploy/docker/Dockerfile"

   [[services]]
     internal_port = 8080
     protocol = "tcp"

     [[services.ports]]
       handlers = ["http"]
       port = 80

     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443

   [[services]]
     internal_port = 9090
     protocol = "tcp"

   [env]
     RESONANCE_MODE = "adaptive"
     RESONANCE_METRICS_PORT = "9090"
     RESONANCE_HEALTH_PORT = "8080"
   ```

2. **Deploy**:
   ```bash
   fly launch
   fly secrets set RESONANCE_API_KEY=<your-generated-key>
   fly domains add resonance.syncscript.app
   ```

---

### Option 3: Render (Simple & Secure)

**Why Render?**
- ✅ Zero-config deployments
- ✅ Automatic HTTPS
- ✅ Free SSL certificates
- ✅ Easy environment variables

**Steps**:

1. **Connect Repository**:
   - Go to https://render.com
   - New → Web Service
   - Connect GitHub repo

2. **Configure**:
   - **Build Command**: `cd resonance && npm install && npm run build`
   - **Start Command**: `node resonance/dist/agent/index_secure.js`
   - **Environment Variables**:
     - `RESONANCE_API_KEY`: <your-generated-key>
     - `RESONANCE_MODE`: `adaptive`
     - `RESONANCE_METRICS_PORT`: `9090`
     - `RESONANCE_HEALTH_PORT`: `8080`

3. **Add Custom Domain**:
   - Settings → Custom Domain
   - Add: `resonance.syncscript.app`
   - Follow DNS instructions

---

## 🔐 Security Checklist

Before going live:

- [ ] **API Key Generated**: Use strong random key (32+ bytes)
- [ ] **HTTPS Enabled**: All traffic must be encrypted
- [ ] **Rate Limiting Configured**: Set appropriate limits
- [ ] **CORS Restricted**: Only allow trusted origins
- [ ] **Environment Variables Secured**: Never commit keys to git
- [ ] **Monitoring Enabled**: Set up alerts for suspicious activity
- [ ] **Health Endpoint Tested**: Verify `/health` works publicly
- [ ] **Metrics Endpoint Protected**: Test that `/metrics` requires auth

---

## 💻 Desktop Distribution (macOS / Windows / Linux)

Need to install the Resonance Agent directly on customer machines? A packaging pipeline is now available:

1. From `resonance/`, run `npm run build:agent-binaries` – this compiles TypeScript and uses [`pkg`](https://github.com/vercel/pkg) to produce self‑contained executables in `resonance/dist-binaries/`:
   - `resonance-agent-macos-x64`
   - `resonance-agent-linux-x64`
   - `resonance-agent-windows-x64.exe`
   - `manifest.json` (metadata for release automation).
2. GitHub Actions workflow `.github/workflows/build-agent-binaries.yml` can be triggered manually or by tagging `agent-v*` to generate the same artifacts in CI.
3. Next steps before customer distribution:
   - **Code-sign** the binaries (Authenticode for Windows, Apple notarization for macOS).
   - Wrap them in installers (`.msi/.exe`, `.pkg`, `.deb/.rpm`) with auto-start services.
   - Provide CLI onboarding (`resonance-agent register --license <TOKEN>`) that stores customer credentials securely per OS.
   - See `docs/desktop-agent/SIGNING_AND_INSTALLERS.md` and `docs/desktop-agent/AUTO_UPDATE.md` for detailed workflows.

This approach matches how observability agents (Datadog, New Relic) ship native endpoints: a signed binary communicates over TLS to the hosted Resonance service.

---

## 🧪 Testing Security

### Test API Key Authentication:
```bash
# Should fail (no key)
curl https://resonance.syncscript.app/metrics

# Should fail (wrong key)
curl -H "Authorization: Bearer wrong-key" https://resonance.syncscript.app/metrics

# Should succeed (correct key)
curl -H "Authorization: Bearer YOUR_API_KEY" https://resonance.syncscript.app/metrics
```

### Test Rate Limiting:
```bash
# Make 101 requests quickly
for i in {1..101}; do
  curl -H "Authorization: Bearer YOUR_API_KEY" https://resonance.syncscript.app/metrics
done
# 101st request should return 429
```

### Test Health Endpoint:
```bash
# Should work without auth
curl https://resonance.syncscript.app/health
```

---

## 📊 Update Vercel Dashboard

After deployment, update Vercel environment variables:

```bash
cd "/Users/Apple/New Math Discovery Documentation/webapp"
vercel env add RESONANCE_AGENT_URL production
# Enter: https://resonance.syncscript.app/health

vercel env add RESONANCE_METRICS_URL production
# Enter: https://resonance.syncscript.app/metrics

vercel env add RESONANCE_API_KEY production
# Enter: <your-generated-api-key>

# Redeploy
vercel --prod
```

---

## 🚨 Security Monitoring

Set up alerts for:
- **High request volume**: Potential DDoS
- **Failed auth attempts**: Brute force attack
- **Rate limit hits**: Abuse detection
- **Health check failures**: Service issues

---

## ✅ Production Ready!

Once deployed:
1. ✅ Agent accessible at `https://resonance.syncscript.app`
2. ✅ Metrics API protected with API key
3. ✅ Health endpoint public
4. ✅ All security headers enabled
5. ✅ Rate limiting active
6. ✅ HTTPS enforced

**Your agent is secure and production-ready!** 🔒

