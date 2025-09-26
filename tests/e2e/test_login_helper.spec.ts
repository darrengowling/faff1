import { test, expect } from '@playwright/test';
import { loginTestOnly } from './utils/helpers';

test.describe('Test-Only Login Helper', () => {
  test('loginTestOnly helper authenticates user without UI', async ({ page }) => {
    const testEmail = 'playwright-helper-test@example.com';
    
    // Use the test-only login helper
    await loginTestOnly(page, testEmail);
    
    // Verify we're authenticated by checking protected route access
    await page.goto('/app');
    await expect(page).toHaveURL('/app');
    
    // Verify we're not redirected to login
    await page.waitForLoadState('networkidle');
    await expect(page).not.toHaveURL('/login');
    
    console.log('✅ Test-only login helper working correctly');
  });

  test('loginTestOnly sets proper authentication state', async ({ page }) => {
    const testEmail = 'playwright-auth-state-test@example.com';
    
    // Use the test-only login helper
    await loginTestOnly(page, testEmail);
    
    // Check that localStorage has been set correctly
    const token = await page.evaluate(() => localStorage.getItem('token'));
    const userStr = await page.evaluate(() => localStorage.getItem('user'));
    
    expect(token).toBeTruthy();
    expect(userStr).toBeTruthy();
    
    const user = JSON.parse(userStr);
    expect(user.email).toBe(testEmail);
    expect(user.verified).toBe(true);
    
    console.log('✅ Authentication state set correctly');
  });

  test('loginTestOnly bypasses UI authentication completely', async ({ page }) => {
    const testEmail = 'playwright-bypass-test@example.com';
    
    // We should be able to authenticate without ever visiting /login
    await loginTestOnly(page, testEmail);
    
    // Go directly to a protected route
    await page.goto('/app');
    
    // Should not be redirected to login
    await expect(page).toHaveURL('/app');
    await expect(page).not.toHaveURL('/login');
    
    console.log('✅ UI authentication bypassed successfully');
  });
});