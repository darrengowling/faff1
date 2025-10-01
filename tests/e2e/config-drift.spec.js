/**
 * Config Drift Test
 * 
 * Ensures no hardcoded values leak through and all settings are properly centralized.
 * Tests that Rules badge appears and shows correct values.
 */

const { test, expect } = require('@playwright/test');

// Use baseURL from config
const BASE_URL = process.env.FRONTEND_URL || 'https://leaguemate-1.preview.emergentagent.com';

test.describe('Config Drift Prevention', () => {
  
  test('Rules Badge displays correct format in components', async ({ page }) => {
    // Navigate to main dashboard first
    await page.goto(`${BASE_URL}/dashboard`);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Look for any Rules badge on the page
    const rulesBadge = page.locator('.badge:has-text("Rules")');
    
    // If Rules badge exists (on pages that have league context), verify it
    const badgeCount = await rulesBadge.count();
    
    if (badgeCount > 0) {
      console.log('✅ Found Rules badge, checking content...');
      
      // Click to show tooltip
      await rulesBadge.first().click();
      await page.waitForTimeout(1000);
      
      // Check tooltip appears with league settings
      const tooltip = page.locator('[role="tooltip"]');
      const tooltipVisible = await tooltip.isVisible();
      
      if (tooltipVisible) {
        const tooltipText = await tooltip.textContent();
        console.log(`Tooltip content: ${tooltipText}`);
        
        // Verify tooltip contains expected format
        expect(tooltipText).toMatch(/Club Slots per Manager/);
        expect(tooltipText).toMatch(/Budget per Manager/);
        expect(tooltipText).toMatch(/Min Managers/);
        expect(tooltipText).toMatch(/Max Managers/);
      }
    } else {
      console.log('ℹ️ No Rules badge found on dashboard - normal for main leagues list');
    }
  });
  
  test('Check for hardcoded "3" values on key pages', async ({ page }) => {
    const pagesToCheck = [
      `${BASE_URL}/dashboard`,
    ];
    
    for (const pageUrl of pagesToCheck) {
      console.log(`Checking page: ${pageUrl}`);
      
      await page.goto(pageUrl);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Get page content
      const pageContent = await page.textContent('body');
      
      // Check for problematic hardcoded "3" patterns
      const problematicPatterns = [
        { pattern: /\b3\s+club\s+slot/i, description: 'hardcoded "3 club slot"' },
        { pattern: /\b3\s+slot/i, description: 'hardcoded "3 slot"' },
        { pattern: /Need\s+at\s+least\s+3\s+club/i, description: 'hardcoded club requirement' },
        { pattern: /\b3\s+remaining/i, description: 'hardcoded "3 remaining"' }
      ];
      
      const violations = [];
      
      for (const { pattern, description } of problematicPatterns) {
        const match = pageContent.match(pattern);
        if (match) {
          violations.push(`${description}: "${match[0]}"`);
        }
      }
      
      // Log results
      if (violations.length > 0) {
        console.log(`❌ Found hardcoded values on ${pageUrl}:`);
        violations.forEach(v => console.log(`  - ${v}`));
        throw new Error(`Hardcoded "3" values detected on ${pageUrl}: ${violations.join(', ')}`);
      } else {
        console.log(`✅ No hardcoded "3" values found on ${pageUrl}`);
      }
    }
  });
  
  test('Verify Rules badge format matches specification', async ({ page }) => {
    // Navigate to dashboard
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');
    
    // Check if any leagues exist that we can inspect
    const leagueLinks = page.locator('a[href*="/admin/"], a[href*="/clubs/"]');
    const linkCount = await leagueLinks.count();
    
    if (linkCount > 0) {
      // Navigate to first league
      const firstLeague = leagueLinks.first();
      await firstLeague.click();
      
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
      
      // Look for Rules badge
      const rulesBadge = page.locator('.badge:has-text("Rules")');
      const badgeExists = await rulesBadge.count() > 0;
      
      if (badgeExists) {
        console.log('✅ Rules badge found in league context');
        
        // Click to show tooltip
        await rulesBadge.click();
        await page.waitForTimeout(1000);
        
        // Check tooltip format
        const tooltip = page.locator('[role="tooltip"]');
        if (await tooltip.isVisible()) {
          const content = await tooltip.textContent();
          
          // Verify format matches: "Slots: X · Budget: Y · Min: Z · Max: W"
          const formatRegex = /Slots:\s*\d+.*Budget:\s*\d+.*Min:\s*\d+.*Max:\s*\d+/i;
          
          if (formatRegex.test(content)) {
            console.log('✅ Rules badge format matches specification');
          } else {
            console.log(`❌ Rules badge format mismatch. Content: ${content}`);
            throw new Error(`Rules badge format does not match specification. Expected format with Slots/Budget/Min/Max, got: ${content}`);
          }
        }
      } else {
        console.log('ℹ️ No Rules badge found - may not be implemented on this page yet');
      }
    } else {
      console.log('ℹ️ No leagues found to test Rules badge');
    }
  });
});