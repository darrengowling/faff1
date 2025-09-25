/**
 * Config Drift Test
 * 
 * Ensures no hardcoded values leak through and all settings are properly centralized.
 * Creates a league with specific settings and validates they appear correctly
 * across all screens without any hardcoded "3" values.
 */

const { test, expect } = require('@playwright/test');

test.describe('Config Drift Prevention', () => {
  let leagueId;
  let userId;
  
  test.beforeAll(async ({ browser }) => {
    // Create a new user and league with specific settings for testing
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Navigate to the application
    await page.goto('/');
    
    // Sign up / Login (assuming magic link flow)
    await page.fill('input[name="email"]', `configtest-${Date.now()}@example.com`);
    await page.click('button:has-text("Send Magic Link")');
    
    // Mock magic link success (in development mode)
    await page.evaluate(() => {
      // Simulate successful magic link auth
      const token = 'test-token-config-drift';
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify({
        id: `user-config-drift-${Date.now()}`,
        email: `configtest-${Date.now()}@example.com`,
        verified: true
      }));
      window.location.reload();
    });
    
    await page.waitForURL('/dashboard');
    
    // Create league with specific settings: clubSlots=5, min=2, max=8
    await page.click('button:has-text("Create League")');
    
    // Fill league form
    await page.fill('input[name="name"]', 'Config Drift Test League');
    
    // Select UCL profile (which should have our updated defaults)
    const profileSelector = await page.locator('select#profile');
    await profileSelector.selectOption('ucl');
    
    // Verify the form shows the correct default values
    const clubSlotsInput = await page.locator('input[name="settings.club_slots_per_manager"]');
    const clubSlotsValue = await clubSlotsInput.inputValue();
    expect(parseInt(clubSlotsValue)).toBe(5);
    
    const minManagersInput = await page.locator('input[name="settings.league_size.min"]');
    const minValue = await minManagersInput.inputValue();
    expect(parseInt(minValue)).toBe(2);
    
    // Submit league creation
    await page.click('button:has-text("Create League")');
    
    // Wait for success and extract league ID
    await page.waitForSelector('.toast', { timeout: 10000 });
    
    // Navigate to the created league (should be in URL or visible in dashboard)
    await page.waitForTimeout(2000);
    
    // Extract league info for use in tests
    const currentURL = page.url();
    const leagueMatch = currentURL.match(/\/admin\/([^\/]+)/);
    if (leagueMatch) {
      leagueId = leagueMatch[1];
    }
    
    await context.close();
  });
  
  test('Rules Badge shows correct values in Lobby (Admin Dashboard)', async ({ page }) => {
    // Navigate to admin dashboard (lobby)
    await page.goto(`/admin/${leagueId}`);
    
    // Wait for league data to load
    await page.waitForSelector('[data-testid="rules-badge"], .badge:has-text("Rules")', { timeout: 10000 });
    
    // Check Rules badge exists and has correct values
    const rulesBadge = await page.locator('.badge:has-text("Rules")');
    await expect(rulesBadge).toBeVisible();
    
    // Click on rules badge to see tooltip
    await rulesBadge.click();
    
    // Check tooltip contains correct values
    const tooltip = await page.locator('[role="tooltip"]');
    await expect(tooltip).toContainText('Club Slots per Manager: 5');
    await expect(tooltip).toContainText('Min Managers: 2');
    
    // Fail if any hardcoded "3" appears on the page
    const pageContent = await page.textContent('body');
    const hardcodedThreePattern = /\b3\s+slot|\b3\s+club|slot.*\b3\b|club.*\b3\b/i;
    
    if (hardcodedThreePattern.test(pageContent)) {
      throw new Error(`Found hardcoded "3" reference in page content: ${pageContent.match(hardcodedThreePattern)?.[0]}`);
    }
  });
  
  test('Rules Badge shows correct values in Auction Room', async ({ page }) => {
    // First, we need to start an auction to access the auction room
    // Navigate to admin dashboard
    await page.goto(`/admin/${leagueId}`);
    
    // Add a second member to meet minimum requirement
    await page.click('button:has-text("Invite Members")');
    
    // Mock adding a member (in real test, this would be done properly)
    await page.evaluate(() => {
      // Simulate member joining (mock for test)
      window.dispatchEvent(new CustomEvent('member-joined', { 
        detail: { memberCount: 2 } 
      }));
    });
    
    await page.waitForTimeout(1000);
    
    // Try to start auction (should be enabled with 2 members, min=2)
    const startButton = await page.locator('button:has-text("Start Auction")');
    
    if (await startButton.isEnabled()) {
      await startButton.click();
      
      // Wait for auction to start and navigate to auction room
      await page.waitForTimeout(2000);
      
      // Navigate to auction room
      const auctionUrl = page.url().replace('/admin/', '/auction/');
      await page.goto(auctionUrl);
      
      // Wait for auction room to load
      await page.waitForSelector('[data-testid="rules-badge"], .badge:has-text("Rules")', { timeout: 10000 });
      
      // Check Rules badge exists
      const rulesBadge = await page.locator('.badge:has-text("Rules")');
      await expect(rulesBadge).toBeVisible();
      
      // Click to see tooltip with values
      await rulesBadge.click();
      await page.waitForTimeout(500);
      
      const tooltip = await page.locator('[role="tooltip"]');
      await expect(tooltip).toContainText('Club Slots per Manager: 5');
      await expect(tooltip).toContainText('Min Managers: 2');
      
      // Check for hardcoded "3" values
      const pageContent = await page.textContent('body');
      const hardcodedThreePattern = /\b3\s+slot|\b3\s+club|slot.*\b3\b|club.*\b3\b/i;
      
      if (hardcodedThreePattern.test(pageContent)) {
        throw new Error(`Found hardcoded "3" reference in auction room: ${pageContent.match(hardcodedThreePattern)?.[0]}`);
      }
    }
  });
  
  test('Roster page shows correct slot counts', async ({ page }) => {
    // Navigate to roster/clubs page
    await page.goto(`/clubs/${leagueId}`);
    
    // Wait for roster data to load
    await page.waitForSelector('[data-testid="slots-available"], .text-2xl', { timeout: 10000 });
    
    // Check "slots remaining" shows 5 (before any wins)
    const slotsAvailableElement = await page.locator('.text-2xl:has-text("5"), [data-testid="slots-available"]:has-text("5")').first();
    await expect(slotsAvailableElement).toBeVisible();
    
    // Check club count display shows "0 / 5 Clubs" 
    const clubCountBadge = await page.locator('.badge:has-text("/ 5 Clubs"), .badge:has-text("0 / 5")');
    await expect(clubCountBadge).toBeVisible();
    
    // Verify "Slots Available" section shows 5
    const slotsSection = await page.locator('text="Slots Available"').locator('..').locator('.text-2xl');
    await expect(slotsSection).toHaveText('5');
    
    // Fail if any hardcoded "3" appears
    const pageContent = await page.textContent('body');
    const hardcodedThreePattern = /\b3\s+slot|\b3\s+club|slot.*\b3\b|club.*\b3\b/i;
    
    if (hardcodedThreePattern.test(pageContent)) {
      throw new Error(`Found hardcoded "3" reference in roster page: ${pageContent.match(hardcodedThreePattern)?.[0]}`);
    }
  });
  
  test('Badge tooltip displays all settings correctly', async ({ page }) => {
    // Navigate to admin dashboard
    await page.goto(`/admin/${leagueId}`);
    
    // Wait for rules badge
    await page.waitForSelector('.badge:has-text("Rules")', { timeout: 10000 });
    
    // Click rules badge to show tooltip
    const rulesBadge = await page.locator('.badge:has-text("Rules")');
    await rulesBadge.click();
    
    // Wait for tooltip to appear
    await page.waitForSelector('[role="tooltip"]', { timeout: 5000 });
    
    const tooltip = await page.locator('[role="tooltip"]');
    
    // Verify all expected values are present
    await expect(tooltip).toContainText('Club Slots per Manager: 5');
    await expect(tooltip).toContainText('Budget per Manager: $100M');
    await expect(tooltip).toContainText('Min Managers: 2');
    await expect(tooltip).toContainText('Max Managers: 8');
    
    // Verify the compact format matches expected pattern
    // "Slots: 5 · Budget: 100 · Min: 2 · Max: 8"
    const compactRules = await page.locator('text=/Slots:\\s*5.*Budget:\\s*100.*Min:\\s*2.*Max:\\s*8/');
    if (await compactRules.count() > 0) {
      await expect(compactRules).toBeVisible();
    }
  });
  
  test('No hardcoded 3 values anywhere on key pages', async ({ page }) => {
    const pagesToCheck = [
      `/admin/${leagueId}`,      // Admin Dashboard (Lobby)
      `/clubs/${leagueId}`,      // Roster page
    ];
    
    for (const pageUrl of pagesToCheck) {
      await page.goto(pageUrl);
      
      // Wait for page to fully load
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Get all text content from the page
      const pageContent = await page.textContent('body');
      
      // Check for hardcoded "3" in contexts that should use dynamic values
      const problematicPatterns = [
        /\b3\s+club\s+slot/i,
        /\b3\s+slot/i,
        /slot.*\b3\b/i,
        /\b3\s+club/i,
        /club.*\b3\b/i,
        /\b3\s+remaining/i,
        /remaining.*\b3\b/i,
        /\b3\s+available/i,
        /available.*\b3\b/i
      ];
      
      for (const pattern of problematicPatterns) {
        const match = pageContent.match(pattern);
        if (match) {
          throw new Error(`Found hardcoded "3" on ${pageUrl}: "${match[0]}" - should use dynamic league settings`);
        }
      }
    }
  });
});

// Utility to check for hardcoded values
async function checkForHardcodedValues(page, context = '') {
  const content = await page.textContent('body');
  
  // Patterns that indicate hardcoded values that should be dynamic
  const patterns = [
    { pattern: /\b3\s+club\s+slot/i, description: 'hardcoded club slots' },
    { pattern: /\b4\s+manager/i, description: 'hardcoded minimum managers' },
    { pattern: /need\s+4\s+to\s+start/i, description: 'hardcoded start requirement' }
  ];
  
  const violations = [];
  
  for (const { pattern, description } of patterns) {
    const match = content.match(pattern);
    if (match) {
      violations.push(`${description}: "${match[0]}"`);
    }
  }
  
  if (violations.length > 0) {
    throw new Error(`Hardcoded values detected ${context}: ${violations.join(', ')}`);
  }
}