#!/bin/bash

# CI SSR Safety Check Script
# Runs ESLint with SSR safety rules and fails CI on violations

set -e

echo "🔍 Running SSR Safety Check..."
echo "Checking for module-scope browser API usage..."

cd /app/frontend

# Run the SSR safety lint check
if npm run lint:ssr-safety; then
    echo "✅ SSR Safety Check PASSED - No module-scope browser API usage found"
    exit 0
else
    echo "❌ SSR Safety Check FAILED - Module-scope browser API usage detected"
    echo ""
    echo "💡 Fix suggestions:"
    echo "  - Move window, document, or navigator usage inside React components"
    echo "  - Use useEffect hooks for browser API access"
    echo "  - Use safeBrowser utilities for SSR-compatible access"
    echo ""
    exit 1
fi