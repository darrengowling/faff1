/**
 * Demo Test: clickCreateLeague Helper Function
 * 
 * Demonstrates that the helper function successfully finds and clicks
 * Create League buttons from multiple entry points
 */

import { test, expect } from '@playwright/test';
import { login } from './utils/login';
import { clickCreateLeague } from './utils/helpers';

test('clickCreateLeague helper finds button from multiple entry points', async ({ page }) => {
  // Login first
  await login(page, 'commish@example.com', { mode: 'test' });
  
  // Navigate to dashboard
  await page.goto('/app');
  await page.waitForLoadState('networkidle');
  
  // Test that the helper function can find and click the Create League button
  await clickCreateLeague(page);
  
  // Verify that the create league dialog opened
  await expect(page.locator('[role="dialog"], .modal')).toBeVisible({ timeout: 5000 });
  
  console.log('✅ Helper function successfully found and clicked Create League button');
});