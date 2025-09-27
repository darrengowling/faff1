/**
 * Debug Test: Create League Button Detection
 * 
 * Diagnostic test to understand why clickCreateLeague helper fails in E2E context
 */

import { test, expect } from '@playwright/test';
import { login } from './utils/login';

test('Debug Create League button detection', async ({ page }) => {
  console.log('🔍 Starting Create League button diagnostic...');
  
  // Login first
  await login(page, 'commish@example.com', { mode: 'test' });
  
  // Navigate to dashboard
  await page.goto('/app');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000); // Allow React to fully render
  
  console.log('✅ Dashboard loaded and authenticated');
  
  // Check all buttons on the page
  const allButtons = page.locator('button');
  const buttonCount = await allButtons.count();
  console.log(`🔍 Total buttons on page: ${buttonCount}`);
  
  // Check specifically for create-league-btn testid
  const createLeagueBtns = page.getByTestId('create-league-btn');
  const createLeagueCount = await createLeagueBtns.count();
  console.log(`🔍 Buttons with 'create-league-btn' testid: ${createLeagueCount}`);
  
  // Check specifically for nav-create-league-btn testid
  const navCreateLeagueBtns = page.getByTestId('nav-create-league-btn');
  const navCreateLeagueCount = await navCreateLeagueBtns.count();
  console.log(`🔍 Buttons with 'nav-create-league-btn' testid: ${navCreateLeagueCount}`); 
  
  // Check all elements with data-testid containing 'create'
  const createElements = page.locator('[data-testid*="create"]');
  const createElementCount = await createElements.count();
  console.log(`🔍 Elements with 'create' in testid: ${createElementCount}`);
  
  for (let i = 0; i < Math.min(createElementCount, 10); i++) {
    const element = createElements.nth(i);
    const testid = await element.getAttribute('data-testid');
    const tagName = await element.evaluate('el => el.tagName');
    const isVisible = await element.isVisible();
    const textContent = await element.textContent();
    console.log(`  ${i+1}. ${tagName} [data-testid="${testid}"] visible=${isVisible} text="${textContent?.trim()}"`);
  }
  
  // Check buttons containing "Create" or "League" text
  const createTextButtons = page.locator('button:has-text("Create"), button:has-text("League")');
  const createTextCount = await createTextButtons.count();
  console.log(`🔍 Buttons with 'Create' or 'League' text: ${createTextCount}`);
  
  for (let i = 0; i < Math.min(createTextCount, 5); i++) {
    const button = createTextButtons.nth(i);
    const testid = await button.getAttribute('data-testid');
    const isVisible = await button.isVisible();
    const textContent = await button.textContent();
    console.log(`  ${i+1}. Button testid="${testid}" visible=${isVisible} text="${textContent?.trim()}"`);
  }
  
  // Check if there are any loading states that might be blocking
  const loadingElements = page.locator('[data-loading="true"], .animate-spin, .loading');
  const loadingCount = await loadingElements.count();
  console.log(`⏳ Loading indicators found: ${loadingCount}`);
  
  // Take a screenshot for visual debugging
  await page.screenshot({ path: 'debug-create-league-dashboard.png', fullPage: false });
  console.log('📸 Screenshot saved as debug-create-league-dashboard.png');
  
  // Verify at least one Create League button exists
  const hasAnyCreateButton = createLeagueCount > 0 || navCreateLeagueCount > 0;
  expect(hasAnyCreateButton).toBe(true);
  
  if (hasAnyCreateButton) {
    console.log('✅ Create League buttons found - helper should work');
  } else {
    console.log('❌ No Create League buttons found - this explains the helper failure');
  }
});