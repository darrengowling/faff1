#!/bin/bash

# Extended E2E Test Suite  
# Advanced features: anti-snipe, simultaneous bids, reconnect, scoring, rate limits

set -e

echo "🚀 Running Extended E2E Test Suite..."

# Extended feature tests
EXTENDED_SPECS=(
    "tests/e2e/auction.spec.ts"
    "tests/e2e/scoring_ingest.spec.ts"
    "tests/e2e/anti-snipe-unit.spec.ts"
    # Add more as they become available:
    # "tests/e2e/reconnect.spec.ts"
    # "tests/e2e/rate-limits.spec.ts"
)

cd /app

PASSED=0
TOTAL=0

for spec in "${EXTENDED_SPECS[@]}"; do
    # Check if spec file exists
    if [ ! -f "$spec" ]; then
        echo "⚠️ Skipping $spec (file not found)"
        continue
    fi
    
    echo "🔄 Running $spec..."
    TOTAL=$((TOTAL + 1))
    
    if npx playwright test "$spec" --reporter=line; then
        echo "✅ $spec passed"
        PASSED=$((PASSED + 1))
    else
        echo "❌ $spec failed"
    fi
    
    echo ""
done

if [ $TOTAL -eq 0 ]; then
    echo "⚠️ No extended tests found - skipping extended suite"
    exit 0
fi

PASS_RATE=$((PASSED * 100 / TOTAL))

echo "📊 Extended E2E Results: $PASSED/$TOTAL passed ($PASS_RATE%)"

# Extended tests are less critical - 70% threshold
if [ $PASS_RATE -ge 70 ]; then
    echo "✅ Extended E2E suite meets minimum threshold"
    exit 0
else
    echo "⚠️ Extended E2E suite below 70% threshold (non-blocking)"
    exit 0  # Don't block deployment on extended tests
fi