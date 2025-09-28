import { test, expect } from '@playwright/test';
import { TESTIDS } from '../../frontend/src/testids.ts';

test('PRE-GATE: Auth UI elements validation', async ({ page }) => {
  console.log('🔐 PRE-GATE 2: Checking auth UI elements on /login...');
  
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  
  // Assert presence of required auth elements - FAIL FAST if missing
  const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
  const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
  
  try {
    await expect(emailInput).toBeVisible({ timeout: 10000 });
    await expect(submitBtn).toBeVisible({ timeout: 10000 });
    
    console.log('✅ PRE-GATE 2 PASSED: Auth UI elements found (authEmailInput + authSubmitBtn)');
  } catch (error) {
    console.error('❌ PRE-GATE 2 FAILED: Required auth elements missing');
    await page.screenshot({ path: 'auth-gate-failure.png', quality: 20 });
    throw new Error('PRE-GATE FAILURE: Authentication UI elements not found - cannot proceed with regression suite');
  }
});