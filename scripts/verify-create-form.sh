#!/bin/bash
#
# verify-create-form.sh
# CI Pre-Gate: Verify Create League form renders with all required testids
#
# Usage: ./verify-create-form.sh
# Exit 0: All create form testids found
# Exit 1: Missing testids or form not accessible

set -euo pipefail

echo "🧪 PRE-GATE: Verifying Create League form accessibility and testids..."

# Configuration
MAX_RETRIES=3
TIMEOUT=30
BASE_URL="${PLAYWRIGHT_BASE_URL:-https://pifa-stability.preview.emergentagent.com}"

# Test script that navigates to dashboard and opens create form
VERIFY_SCRIPT='
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    const baseUrl = process.env.BASE_URL || "https://pifa-stability.preview.emergentagent.com";
    console.log(`🔍 Navigating to application: ${baseUrl}`);
    await page.goto(baseUrl);
    await page.waitForLoadState("networkidle", { timeout: 30000 });
    
    // Find and click Create League button (may be in various locations)
    console.log("🎯 Finding Create League button...");
    const createButtons = [
      "button:has-text(\"Create League\")",
      "button:has-text(\"Create\")", 
      "[data-testid*=\"create-league\"]",
      "text=Create League"
    ];
    
    let createButton = null;
    for (const selector of createButtons) {
      const button = page.locator(selector).first();
      if (await button.count() > 0 && await button.isVisible()) {
        createButton = button;
        console.log(`✅ Found Create League button: ${selector}`);
        break;
      }
    }
    
    if (!createButton) {
      throw new Error("❌ Create League button not found on page");
    }
    
    // Click to open create form
    console.log("📋 Opening Create League form...");
    await createButton.click();
    await page.waitForTimeout(2000); // Allow form to render
    
    // Required testids for create form
    const requiredTestIds = [
      "create-name",
      "create-slots-input", 
      "create-budget",
      "create-min", 
      "create-submit"
    ];
    
    console.log("🔍 Verifying all required testids are present...");
    const missingTestIds = [];
    
    for (const testid of requiredTestIds) {
      const element = page.getByTestId(testid);
      const count = await element.count();
      const isVisible = count > 0 ? await element.first().isVisible() : false;
      
      if (count === 0 || !isVisible) {
        missingTestIds.push(testid);
        console.log(`❌ Missing or hidden: ${testid}`);
      } else {
        console.log(`✅ Found: ${testid}`);
      }
    }
    
    if (missingTestIds.length > 0) {
      throw new Error(`❌ Missing create form testids: ${missingTestIds.join(", ")}`);
    }
    
    // Verify form is interactive
    console.log("🔧 Testing form interactivity...");
    await page.getByTestId("create-name").fill("Test League");
    await page.getByTestId("create-submit").isEnabled();
    
    console.log("✅ All create form testids verified and form is interactive");
    
  } catch (error) {
    console.error("❌ Create form verification failed:", error.message);
    
    // Take screenshot for debugging
    await page.screenshot({ 
      path: `create-form-verification-failure-${Date.now()}.png`
    });
    
    process.exit(1);
    
  } finally {
    await browser.close();
  }
})();
'

# Run verification with retries
for attempt in $(seq 1 $MAX_RETRIES); do
  echo "🔄 Verification attempt $attempt/$MAX_RETRIES..."
  
  if timeout $TIMEOUT node -e "$VERIFY_SCRIPT" BASE_URL="$BASE_URL"; then
    echo "✅ PRE-GATE PASSED: Create League form verification successful"
    exit 0
  else
    echo "❌ Attempt $attempt failed"
    if [ $attempt -eq $MAX_RETRIES ]; then
      echo "💥 PRE-GATE FAILED: Create League form verification failed after $MAX_RETRIES attempts"
      exit 1
    fi
    sleep 2
  fi
done