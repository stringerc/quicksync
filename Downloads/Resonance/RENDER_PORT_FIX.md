# ✅ Render Port Configuration Fix

## 🐛 Issue

The agent was timing out on Render because it was using **two separate servers** on different ports (8080 and 9090). Render requires services to:
1. Bind to the **`PORT`** environment variable (automatically set by Render)
2. Serve all endpoints from a **single server** on that port
3. Respond to health checks on that port

---

## ✅ Fix Applied

### Changed:
- ❌ **Before:** Two separate servers (health on 8080, metrics on 9090)
- ✅ **After:** Single server on Render's `PORT` environment variable

### Key Changes:
1. **Unified Server:**
   - Single `http.createServer()` handles all routes
   - Uses `process.env.PORT` (Render's requirement)
   - Falls back to `RESONANCE_HEALTH_PORT` or `8080` for local dev

2. **Endpoints:**
   - `/health` - Public health check (no auth required)
   - `/metrics` - Protected metrics (requires API key)
   - `/` - Root endpoint for Render health checks

3. **Binding:**
   - Server listens on `0.0.0.0` (required for Render)
   - Uses Render's `PORT` environment variable

---

## 📋 Render Configuration

### Environment Variables Required:
```
RESONANCE_API_KEY=jAn5Wzpm4EMbt-QQJPUXHo4esCiGW3i2hYW-BQsrlWY
RESONANCE_MODE=adaptive
```

### Not Required (but optional):
```
RESONANCE_HEALTH_PORT  # Not used in production (Render sets PORT)
RESONANCE_METRICS_PORT # Not used (single server now)
```

### Health Check Path:
```
/health
```

---

## 🚀 Next Steps

1. **Commit and Push:**
   ```bash
   git add resonance/agent/index_secure.ts
   git commit -m "Fix: Use single server on Render PORT"
   git push
   ```

2. **Render Will Auto-Deploy:**
   - Render will detect the new commit
   - Build will succeed (already verified)
   - Service should start successfully on Render's PORT

3. **Verify Deployment:**
   - Check Render logs for: "Resonance Agent started"
   - Test: `curl https://api.resonance.syncscript.app/health`
   - Should return JSON with status "healthy"

---

## 🔍 Verification

Once deployed, you should see in Render logs:
```
Resonance Agent started
Mode: adaptive
Port: 10000  (or whatever Render assigns)
Health: http://0.0.0.0:10000/health
Metrics: http://0.0.0.0:10000/metrics
Security: API key authentication enabled for /metrics
```

---

## ✅ Benefits

1. **Render Compatible:** Uses Render's PORT requirement
2. **Simpler Architecture:** Single server is easier to manage
3. **Better Security:** Unified security middleware
4. **Local Dev Still Works:** Falls back to port 8080 locally

---

**The fix is complete! Commit and push to trigger a new Render deployment.** 🚀
