#!/bin/bash

# Verify Auth UI Test Script
# Quick verification that authentication UI elements are present and functional

set -e

echo "🔐 Verifying Authentication UI Elements..."

# Run specific auth UI test to verify elements are present
cd /app
npx playwright test tests/e2e/auth_ui.spec.ts -g "Login page renders form with all required testid elements" --reporter=line

if [ $? -eq 0 ]; then
    echo "✅ Authentication UI verification passed"
    exit 0
else
    echo "❌ Authentication UI verification failed"
    exit 1
fi