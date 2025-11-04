#!/bin/bash

# Verify Render Deployment
# Tests health and metrics endpoints

set -e

API_KEY="${RESONANCE_API_KEY:-jAn5Wzpm4EMbt-QQJPUXHo4esCiGW3i2hYW-BQsrlWY}"
AGENT_URL="${RESONANCE_AGENT_URL:-https://api.resonance.syncscript.app}"
HEALTH_URL="${AGENT_URL}/health"
METRICS_URL="${AGENT_URL}/metrics"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Verifying Render Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Health Endpoint (Public)
echo "1️⃣  Testing Health Endpoint (Public)..."
echo "   URL: $HEALTH_URL"
echo ""

if curl -s -f "$HEALTH_URL" > /tmp/health_response.json 2>/dev/null; then
    echo "   ✅ Health endpoint is accessible!"
    echo "   Response:"
    cat /tmp/health_response.json | python3 -m json.tool 2>/dev/null || cat /tmp/health_response.json
    echo ""
else
    echo "   ❌ Health endpoint failed or not accessible"
    echo "   Status: Service may still be starting, check Render dashboard"
    echo ""
    exit 1
fi

# Test 2: Metrics Endpoint (Protected - with API key)
echo "2️⃣  Testing Metrics Endpoint (Protected - with API key)..."
echo "   URL: $METRICS_URL"
echo ""

if curl -s -f -H "Authorization: Bearer $API_KEY" "$METRICS_URL" > /tmp/metrics_response.txt 2>/dev/null; then
    echo "   ✅ Metrics endpoint is accessible with API key!"
    echo "   Response preview (first 20 lines):"
    head -n 20 /tmp/metrics_response.txt
    echo ""
    
    # Check for key metrics
    if grep -q "resonance_R" /tmp/metrics_response.txt; then
        echo "   ✅ Found resonance_R metric"
    fi
    if grep -q "resonance_K" /tmp/metrics_response.txt; then
        echo "   ✅ Found resonance_K metric"
    fi
    if grep -q "resonance_spectral_entropy" /tmp/metrics_response.txt; then
        echo "   ✅ Found resonance_spectral_entropy metric"
    fi
    echo ""
else
    echo "   ❌ Metrics endpoint failed with API key"
    echo "   This might indicate:"
    echo "   - API key is incorrect"
    echo "   - Service is not fully started"
    echo "   - Check Render logs for errors"
    echo ""
    exit 1
fi

# Test 3: Metrics Endpoint (Protected - without API key - should fail)
echo "3️⃣  Testing Metrics Endpoint (Without API key - should fail)..."
echo "   URL: $METRICS_URL"
echo ""

if curl -s -w "\nHTTP Status: %{http_code}\n" "$METRICS_URL" > /tmp/metrics_no_auth.txt 2>&1; then
    HTTP_CODE=$(grep "HTTP Status:" /tmp/metrics_no_auth.txt | awk '{print $3}')
    if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
        echo "   ✅ Metrics endpoint correctly rejects requests without API key"
        echo "   HTTP Status: $HTTP_CODE (Expected)"
    else
        echo "   ⚠️  Metrics endpoint returned unexpected status: $HTTP_CODE"
        echo "   Expected: 401 or 403"
        echo "   Response:"
        cat /tmp/metrics_no_auth.txt
    fi
    echo ""
else
    echo "   ⚠️  Could not test unauthorized access"
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment Verification Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Update Vercel Environment Variables:"
echo "   RESONANCE_AGENT_URL=$HEALTH_URL"
echo "   RESONANCE_METRICS_URL=$METRICS_URL"
echo "   RESONANCE_API_KEY=$API_KEY"
echo ""
echo "2. Redeploy Vercel app to pick up new environment variables"
echo ""
echo "3. Test dashboard at: https://resonance.syncscript.app"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Cleanup
rm -f /tmp/health_response.json /tmp/metrics_response.txt /tmp/metrics_no_auth.txt
