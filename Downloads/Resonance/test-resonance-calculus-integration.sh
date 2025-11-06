#!/bin/bash

# Resonance Calculus Integration Test Suite
# Tests all new features: metrics exposure, API parsing, dashboard components

set -e

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧪 Resonance Calculus Integration Test Suite"
echo "=============================================="
echo "Working directory: $(pwd)"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test function
test_check() {
    local test_name="$1"
    local command="$2"
    
    echo -n "Testing: $test_name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# Test 1: Check if Resonance Calculus metrics are exposed in agent
echo "📊 Phase 1: Agent Metrics Exposure"
echo "-----------------------------------"

test_check "Resonance Bridge returns GPD parameters" \
    "grep -q 'gpd' resonance/resonance-core/resonance_bridge.ts && grep -q 'xi: number' resonance/resonance-core/resonance_bridge.ts"

test_check "Resonance Bridge returns tail quantiles" \
    "grep -q 'tailQuantiles' resonance/resonance-core/resonance_bridge.ts && grep -q 'q99: number' resonance/resonance-core/resonance_bridge.ts"

test_check "Agent exposes coherence_score metric" \
    "grep -q 'resonance_coherence_score' resonance/agent/index.ts"

test_check "Agent exposes tail_health_score metric" \
    "grep -q 'resonance_tail_health_score' resonance/agent/index.ts"

test_check "Agent exposes timing_score metric" \
    "grep -q 'resonance_timing_score' resonance/agent/index.ts"

test_check "Agent exposes lambda_res metric" \
    "grep -q 'resonance_lambda_res' resonance/agent/index.ts"

test_check "Agent exposes GPD parameters" \
    "grep -q 'resonance_gpd_xi' resonance/agent/index.ts"

test_check "Agent exposes tail quantiles" \
    "grep -q 'resonance_tail_q99' resonance/agent/index.ts"

echo ""

# Test 2: Check API route parsing
echo "🔌 Phase 2: API Metrics Parsing"
echo "--------------------------------"

# Try multiple possible webapp paths
WEBAPP_PATH=""
if [ -d "../../New Math Discovery Documentation/webapp" ]; then
    WEBAPP_PATH="../../New Math Discovery Documentation/webapp"
elif [ -d "../New Math Discovery Documentation/webapp" ]; then
    WEBAPP_PATH="../New Math Discovery Documentation/webapp"
elif [ -d "webapp" ]; then
    WEBAPP_PATH="webapp"
fi

if [ -n "$WEBAPP_PATH" ] && [ -d "$WEBAPP_PATH" ]; then
    echo "Found webapp at: $WEBAPP_PATH"
    API_ROUTE="$WEBAPP_PATH/app/api/metrics/route.ts"
    test_check "API route parses coherence_score" \
        "grep -q 'coherenceScoreMatch' \"$API_ROUTE\""
    
    test_check "API route parses tail_health_score" \
        "grep -q 'tailHealthScoreMatch' \"$API_ROUTE\""
    
    test_check "API route parses timing_score" \
        "grep -q 'timingScoreMatch' \"$API_ROUTE\""
    
    test_check "API route parses lambda_res" \
        "grep -q 'lambdaResMatch' \"$API_ROUTE\""
    
    test_check "API route parses GPD parameters" \
        "grep -q 'gpdXiMatch' \"$API_ROUTE\""
    
    test_check "API route parses tail quantiles" \
        "grep -q 'tailQ99Match' \"$API_ROUTE\""
    
    test_check "API route includes Resonance Calculus in response" \
        "grep -q 'coherenceScore:' \"$API_ROUTE\""
    
    test_check "API route maintains backward compatibility (null handling)" \
        "grep -q 'coherenceScore: metricsData' \"$API_ROUTE\""
else
    echo -e "${YELLOW}⚠ Webapp directory not found, skipping API tests${NC}"
fi

echo ""

# Test 3: Check Dashboard Components
echo "🎨 Phase 3: Dashboard Components"
echo "----------------------------------"

if [ -n "$WEBAPP_PATH" ] && [ -d "$WEBAPP_PATH" ]; then
    CANARY_PAGE="$WEBAPP_PATH/app/dashboard/canary/page.tsx"
    CALCULUS_PAGE="$WEBAPP_PATH/app/dashboard/resonance-calculus/page.tsx"
    DASHBOARD_PAGE="$WEBAPP_PATH/app/dashboard/page.tsx"
    
    test_check "Canary dashboard has Resonance Components panel" \
        "grep -q 'Resonance Components' \"$CANARY_PAGE\""
    
    test_check "Canary dashboard has Tail Health Details section" \
        "grep -q 'Tail Health Analysis' \"$CANARY_PAGE\""
    
    test_check "Canary dashboard has enhanced band visualization" \
        "grep -q 'LOW' \"$CANARY_PAGE\" && grep -q 'OPTIMAL BAND' \"$CANARY_PAGE\""
    
    test_check "Canary dashboard Metrics interface includes Resonance Calculus fields" \
        "grep -q 'coherenceScore' \"$CANARY_PAGE\""
    
    test_check "Resonance Calculus page exists" \
        "[ -f \"$CALCULUS_PAGE\" ]"
    
    test_check "Resonance Calculus page has component breakdown" \
        "grep -q 'Component Breakdown' \"$CALCULUS_PAGE\""
    
    test_check "Resonance Calculus page has tail health analysis" \
        "grep -q 'Tail Health Analysis' \"$CALCULUS_PAGE\""
    
    test_check "Resonance Calculus page has max-plus timing analysis" \
        "grep -q 'Max-Plus Timing Analysis' \"$CALCULUS_PAGE\""
    
    test_check "Navigation links added to dashboard" \
        "grep -q 'resonance-calculus' \"$DASHBOARD_PAGE\""
else
    echo -e "${YELLOW}⚠ Webapp directory not found, skipping dashboard tests${NC}"
fi

echo ""

# Test 4: TypeScript Compilation
echo "🔧 Phase 4: TypeScript Compilation"
echo "-----------------------------------"

if [ -d "resonance" ]; then
    echo -n "Testing: Resonance agent TypeScript compilation... "
    if cd resonance && npm run build > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        cd ..
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        cd ..
    fi
fi

echo ""

# Test 5: Backward Compatibility
echo "🔄 Phase 5: Backward Compatibility"
echo "-----------------------------------"

if [ -n "$WEBAPP_PATH" ] && [ -d "$WEBAPP_PATH" ]; then
    test_check "API route handles missing Resonance Calculus gracefully" \
        "grep -q 'coherenceScore: metricsData' \"$API_ROUTE\""
    
    test_check "Dashboard handles null Resonance Calculus metrics" \
        "grep -q 'coherenceScore !== null' \"$CANARY_PAGE\""
    
    test_check "Dashboard shows info message when Calculus unavailable" \
        "grep -q 'Resonance Calculus Metrics Not Available' \"$CALCULUS_PAGE\""
fi

echo ""

# Summary
echo "=============================================="
echo "📊 Test Summary"
echo "=============================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review the output above.${NC}"
    exit 1
fi

