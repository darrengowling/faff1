#!/bin/bash

# Core E2E Test Suite
# Essential user journey: auth → create → start auction → nominate → bid → roster/budget

set -e

echo "🧪 Running Core E2E Test Suite..."

# Core user journey tests in order
CORE_SPECS=(
    "tests/e2e/auth_ui.spec.ts"
    "tests/e2e/hooks-unit.spec.ts" 
    "tests/e2e/auction-hooks.spec.ts"
    "tests/e2e/time-control.spec.ts"
)

cd /app

PASSED=0
TOTAL=0

for spec in "${CORE_SPECS[@]}"; do
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

PASS_RATE=$((PASSED * 100 / TOTAL))

echo "📊 Core E2E Results: $PASSED/$TOTAL passed ($PASS_RATE%)"

if [ $PASS_RATE -ge 80 ]; then
    echo "✅ Core E2E suite meets minimum threshold"
    exit 0
else
    echo "❌ Core E2E suite below 80% threshold"
    exit 1
fi