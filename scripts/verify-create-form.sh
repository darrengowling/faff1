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

# Set environment for Node.js script
export BASE_URL

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
    
    // Check if we need authentication first
    console.log("🔐 Checking authentication status...");
    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);
    
    // If we are on login page, do a quick test authentication
    if (currentUrl.includes("/login") || currentUrl === process.env.BASE_URL + "/") {
      console.log("🔑 Performing test authentication...");
      await page.goto(process.env.BASE_URL + "/login?playwright=true");
      await page.fill("[data-testid=\"auth-email-input\"]", "test@example.com");
      await page.click("[data-testid=\"auth-submit-btn\"]");
      await page.waitForTimeout(2000);
      
      // Look for dev magic link button
      const devButton = page.locator("[data-testid=\"dev-magic-link-btn\"]");
      if (await devButton.count() > 0) {
        await devButton.click();
        await page.waitForTimeout(3000);
      }
    }
    
    // Navigate to app dashboard if not already there
    console.log("📍 Navigating to dashboard...");
    await page.goto(process.env.BASE_URL + "/app");
    await page.waitForLoadState("networkidle", { timeout: 10000 });
    
    // Find and click Create League button (may be in various locations)
    console.log("🎯 Finding Create League button...");
    const createButtons = [
      "[data-testid=\"create-league-btn\"]",
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
      // Take debug screenshot
      await page.screenshot({ path: `debug-no-create-button-${Date.now()}.png` });
      console.log("🔍 Available buttons on page:");
      const allButtons = await page.locator("button").all();
      for (const button of allButtons.slice(0, 5)) {
        const text = await button.textContent();
        console.log(`  - Button: "${text}"`);
      }
      throw new Error("❌ Create League button not found on page");
    }
    
    // Click to open create form
    console.log("📋 Opening Create League form...");
    await createButton.click();
    await page.waitForTimeout(3000); // Allow form to render
    
    // Detect which form type (Dialog vs Wizard) by checking for specific testids
    console.log("🔍 Detecting form type...");
    const dialogForm = await page.getByTestId("create-league-dialog").count() > 0;
    const wizardForm = await page.getByTestId("create-name").count() > 0;
    
    console.log(\`Debug: dialogForm=\${dialogForm}, wizardForm=\${wizardForm}\`);
    console.log("Available testids on page:");
    const allTestids = await page.locator("[data-testid]").all();
    for (const element of allTestids.slice(0, 10)) {
      const testid = await element.getAttribute("data-testid");
      console.log(\`  - \${testid}\`);
    }
    
    let requiredTestIds = [];
    let formType = "";
    
    if (dialogForm) {
      formType = "Dialog";
      requiredTestIds = [
        "create-name",
        "create-slots-input", 
        "create-budget",
        "create-min", 
        "create-submit"
      ];
    } else if (wizardForm) {
      formType = "Wizard";
      requiredTestIds = [
        "create-name",
        "create-slots", 
        "create-budget",
        "create-min", 
        "create-submit"
      ];
    } else {
      throw new Error("❌ Neither Dialog nor Wizard create form detected");
    }
    
    console.log(`🎯 Detected ${formType} form, verifying testids...`);
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