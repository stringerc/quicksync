# Render.com Deployment - Copy/Paste Guide

## ⚡ Quick Copy/Paste Values

Use these exact values when deploying to Render.com:

---

## 📋 Service Configuration

**Name**: 
```
resonance-agent
```

**Environment**: 
```
Node
```

**Build Command**: 
```
RESONANCE_DIR=$(find . -type d -name "resonance" 2>/dev/null | head -1) && if [ -z "$RESONANCE_DIR" ]; then echo "ERROR: resonance directory not found"; ls -la; exit 1; fi && cd "$RESONANCE_DIR" && npm install && npm run build
```

**Start Command**: 
```
RESONANCE_DIR=$(find . -type d -name "resonance" 2>/dev/null | head -1) && node "$RESONANCE_DIR/dist/agent/index_secure.js"
```

**Health Check Path**: 
```
/health
```

**Note:** Render automatically sets the `PORT` environment variable. The agent now uses a single server on this port (not separate health/metrics ports).

---

## 🔑 Environment Variables (Copy Each)

Click **"Environment"** tab → **"Add Environment Variable"** for each:

### 1. RESONANCE_MODE
```
adaptive
```

### 2. RESONANCE_METRICS_PORT
```
9090
```

### 3. RESONANCE_HEALTH_PORT
```
8080
```

### 4. RESONANCE_API_KEY ⚠️ IMPORTANT
```
jAn5Wzpm4EMbt-QQJPUXHo4esCiGW3i2hYW-BQsrlWY
```

### 5. RESONANCE_RATE_LIMIT_MAX
```
100
```

### 6. RESONANCE_RATE_LIMIT_WINDOW_MS
```
60000
```

### 7. RESONANCE_ALLOWED_ORIGINS
```
https://resonance.syncscript.app
```

### 8. RESONANCE_ENABLE_CORS
```
true
```

---

## 🌐 Custom Domain

**Domain**: 
```
api.resonance.syncscript.app
```

---

## ✅ Verification Commands

After deployment, test with:

```bash
# Health (should work)
curl https://api.resonance.syncscript.app/health

# Metrics without key (should fail with 401)
curl https://api.resonance.syncscript.app/metrics

# Metrics with key (should work)
curl -H "Authorization: Bearer jAn5Wzpm4EMbt-QQJPUXHo4esCiGW3i2hYW-BQsrlWY" \
     https://api.resonance.syncscript.app/metrics
```

---

**That's it! Copy and paste these values into Render.com!** 🚀

