#!/bin/bash
#
# Email Import Guard - CI Check
# Ensures all email validation goes through the shared shim
#

set -e

echo "🔍 Checking for direct email_validator imports outside of shim..."

# Define the allowed file (our shim)
ALLOWED_FILE="backend/utils/email_validation.py"

# Find any files with direct email_validator imports
VIOLATIONS=$(find backend -name "*.py" | grep -v "__pycache__" | xargs grep -l "from email_validator import\|import email_validator" | grep -v "$ALLOWED_FILE" || true)

if [ -n "$VIOLATIONS" ]; then
    echo "❌ CI GUARD FAILURE: Direct email_validator imports found outside of shim:"
    echo "$VIOLATIONS"
    echo ""
    echo "📋 All email validation must go through the shared shim:"
    echo "   from utils.email_validation import is_valid_email"
    echo ""
    echo "🚫 Do not use direct imports:"
    echo "   from email_validator import ..."
    echo ""
    exit 1
fi

# Check that the shim file exists and has the expected imports
if [ ! -f "$ALLOWED_FILE" ]; then
    echo "❌ CI GUARD FAILURE: Email validation shim not found at $ALLOWED_FILE"
    exit 1
fi

# Verify shim has the expected structure
if ! grep -q "from email_validator import validate_email as _validate_email, EmailNotValidError as _EmailError" "$ALLOWED_FILE"; then
    echo "❌ CI GUARD FAILURE: Email validation shim missing expected imports"
    exit 1
fi

if ! grep -q "check_deliverability=False" "$ALLOWED_FILE"; then
    echo "❌ CI GUARD FAILURE: Email validation shim must use check_deliverability=False"
    exit 1
fi

echo "✅ Email import guard passed - all validation goes through shared shim"
echo "✅ Shim correctly configured with check_deliverability=False"