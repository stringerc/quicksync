# ✅ Next Steps: Complete Deployment

## 🎉 Current Status

- ✅ Repository connected to `syncscriptE`
- ✅ Build successful in Render
- ✅ Service should be starting/running

---

## 🔍 Step 1: Verify Render Service

### Check Render Dashboard:
1. Go to https://dashboard.render.com
2. Click on your service: `resonance-agent`
3. Check status indicator:
   - 🟢 **"Live"** = Service is running (proceed to Step 2)
   - 🟡 **"Starting"** = Wait 1-2 minutes, then check again
   - 🔴 **"Failed"** = Check "Logs" tab for errors

### If Service is "Live":
Run the verification script:
```bash
cd /Users/Apple/Downloads/Resonance
./deploy/scripts/verify-render-deployment.sh
```

Or test manually:
```bash
# Health endpoint (public)
curl https://api.resonance.syncscript.app/health

# Metrics endpoint (requires API key)
curl -H "Authorization: Bearer jAn5Wzpm4EMbt-QQJPUXHo4esCiGW3i2hYW-BQsrlWY" \
     https://api.resonance.syncscript.app/metrics
```

---

## 🔧 Step 2: Update Vercel Environment Variables

Once endpoints are working, update Vercel:

### Option A: Via Vercel Dashboard (Recommended)
1. Go to https://vercel.com/dashboard
2. Select your project (`resonance-calculus-platform` or similar)
3. Go to **Settings** → **Environment Variables**
4. Add these variables (for **Production** environment):
   ```
   RESONANCE_AGENT_URL=https://api.resonance.syncscript.app
   RESONANCE_METRICS_URL=https://api.resonance.syncscript.app/metrics
   RESONANCE_API_KEY=jAn5Wzpm4EMbt-QQJPUXHo4esCiGW3i2hYW-BQsrlWY
   ```
   **Note:** Both endpoints are on the same domain now (single server). Use `/health` for health checks and `/metrics` for metrics.
5. Click **Save**
6. Go to **Deployments** tab
7. Click **⋯** (three dots) on latest deployment → **Redeploy**

### Option B: Via Vercel CLI
```bash
cd "/Users/Apple/New Math Discovery Documentation/webapp"

vercel env add RESONANCE_AGENT_URL production
# Enter: https://api.resonance.syncscript.app

vercel env add RESONANCE_METRICS_URL production
# Enter: https://api.resonance.syncscript.app/metrics

vercel env add RESONANCE_API_KEY production
# Enter: jAn5Wzpm4EMbt-QQJPUXHo4esCiGW3i2hYW-BQsrlWY

vercel --prod
```

---

## ✅ Step 3: Verify Frontend Integration

After Vercel redeploys:

1. **Visit Dashboard:**
   - https://resonance.syncscript.app (or your Vercel URL)

2. **Check Metrics:**
   - Open browser DevTools → Network tab
   - Look for `/api/metrics` request
   - Should return real data (not mock data)

3. **Verify No Errors:**
   - Check browser console for errors
   - Metrics should update every 5 seconds
   - R(t) values should be dynamic (not stuck at 0.5)

---

## 🚨 Troubleshooting

### Service Won't Start in Render?
- Check "Logs" tab in Render dashboard
- Verify Start Command: `RESONANCE_DIR=$(find . -type d -name "resonance" 2>/dev/null | head -1) && node "$RESONANCE_DIR/dist/agent/index_secure.js"`
- Verify environment variables are set:
  - `RESONANCE_API_KEY` (required for secure agent)
  - `RESONANCE_MODE` (optional, defaults to 'shadow')
  - `RESONANCE_METRICS_PORT` (optional, defaults to 9090)
  - `RESONANCE_HEALTH_PORT` (optional, defaults to 8080)

### Health Endpoint Returns 502/503?
- Service might still be starting (wait 2-3 minutes)
- Check Render logs for errors
- Verify custom domain is configured correctly

### Metrics Endpoint Returns 401/403?
- ✅ This is correct! It means authentication is working
- Use the API key in the Authorization header
- Check that `RESONANCE_API_KEY` is set in Render environment variables

### Dashboard Shows "Mock Data"?
- Verify Vercel environment variables are set correctly
- Check Vercel deployment logs for errors
- Ensure API key is correct in Vercel
- Try redeploying Vercel app after setting variables

### DNS Not Working?
- Custom domain (`api.resonance.syncscript.app`) can take up to 48 hours to propagate
- Use Render's auto-generated URL temporarily:
  - `https://resonance-agent-xxxx.onrender.com/health`
- Update Vercel env vars with Render URL until DNS propagates

---

## 📋 Deployment Checklist

- [ ] Render service status is "Live"
- [ ] Health endpoint responds with JSON
- [ ] Metrics endpoint requires API key (returns 401/403 without key)
- [ ] Metrics endpoint returns Prometheus format with API key
- [ ] Vercel environment variables updated
- [ ] Vercel app redeployed
- [ ] Dashboard shows real metrics (not mock data)
- [ ] Metrics update every 5 seconds
- [ ] No console errors in browser

---

## 🎯 What We've Accomplished

✅ **Backend (Render):**
- Repository connected to correct repo (`syncscriptE`)
- Build commands working
- Service deployed with secure agent
- API key authentication enabled
- Health and metrics endpoints exposed

✅ **Frontend (Vercel):**
- Next.js app deployed
- Metrics API route configured
- Dashboard pages ready
- Environment variables ready to connect

✅ **Integration:**
- API route supports API key authentication
- Handles production vs. local environments
- Graceful fallback to mock data if agent unavailable

---

## 🚀 Once Everything Works

You'll have a fully functional production deployment:
- **Frontend:** `resonance.syncscript.app` (Vercel)
- **Backend:** `api.resonance.syncscript.app` (Render)
- **Security:** API key protected endpoints
- **Monitoring:** Real-time metrics dashboard
- **Canary Mode:** Running in adaptive mode for gradual rollout

---

**Let me know the status of Step 1 (Render service) and we'll continue!** 🚀
