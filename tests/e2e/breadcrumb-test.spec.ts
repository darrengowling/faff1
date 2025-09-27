/**
 * Breadcrumb Navigation Test
 * 
 * Tests that the breadcrumb-home link in Create League dialog works correctly
 */

import { test, expect } from '@playwright/test';
import { login } from './utils/login';
import { clickCreateLeague } from './utils/helpers';

test('breadcrumb-home navigation in Create League dialog', async ({ page }) => {
  // Login first
  await login(page, 'commish@example.com', { mode: 'test' });
  
  // Navigate to dashboard
  await page.goto('/app');
  await page.waitForLoadState('networkidle');
  
  // Open Create League dialog
  await clickCreateLeague(page);
  
  // Verify dialog opened
  await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
  
  // Find and verify breadcrumb-home link
  const breadcrumbHome = page.getByTestId('breadcrumb-home');
  await expect(breadcrumbHome).toBeVisible();
  await expect(breadcrumbHome).toHaveText('Home');
  
  // Click breadcrumb-home to navigate back
  await breadcrumbHome.click();
  
  // Verify dialog closed and we're back on dashboard
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();
  
  console.log('✅ Breadcrumb navigation test passed');
});