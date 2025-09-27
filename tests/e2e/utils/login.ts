/**
 * Unified Login Utilities for E2E Tests
 * Supports both test-only API login and UI-based authentication
 */

import { Page } from '@playwright/test';
import { TESTIDS } from '../../../frontend/src/testids.js';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'https://pifa-friends-1.preview.emergentagent.com';

export interface LoginOptions {
  mode?: 'test' | 'ui';
  timeout?: number;
}

/**
 * Unified login function that supports both test-only and UI modes
 * @param page - Playwright page instance
 * @param email - User email to login with
 * @param options - Login configuration options
 */
export async function login(page: Page, email: string, options: LoginOptions = {}): Promise<void> {
  const { mode = 'test', timeout = 15000 } = options;
  
  console.log(`🔐 Logging in user: ${email} (mode: ${mode})`);
  
  if (mode === 'test') {
    await loginTestOnlyInternal(page, email, timeout);
  } else {
    await loginUI(page, email, timeout);
  }
}

/**
 * Test-only login that bypasses UI authentication
 * Only works when ALLOW_TEST_LOGIN=true is set on the backend
 */
async function loginTestOnlyInternal(page: Page, email: string, timeout: number): Promise<void> {
  console.log(`🧪 Test-only login for user: ${email}`);
  
  try {
    // Call the test-only login endpoint
    const response = await page.request.post(`${BASE_URL}/api/auth/test-login`, {
      data: { email },
      timeout
    });
    
    if (!response.ok()) {
      const errorText = await response.text();
      throw new Error(`Test login failed: ${response.status()} ${errorText}`);
    }
    
    const data = await response.json();
    
    // Set the authentication token in localStorage for the browser session
    await page.goto('/'); // Navigate to any page first to set localStorage
    await page.evaluate(({ token, email }) => {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify({
        email: email,
        display_name: email.split('@')[0],
        verified: true
      }));
    }, { token: data.access_token, email });
    
    // Verify we can access protected routes
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    
    console.log(`✅ Test-only login successful: ${email}`);
  } catch (error) {
    console.error(`❌ Test login failed for ${email}:`, error);
    throw error;
  }
}

/**
 * UI-based login using only data-testid selectors
 * Uses the /login page and magic-link authentication flow
 */
async function loginUI(page: Page, email: string, timeout: number): Promise<void> {
  console.log(`🖱️  UI login for user: ${email}`);
  
  try {
    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Fill email using data-testid selector
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    await emailInput.waitFor({ state: 'visible', timeout });
    await emailInput.fill(email);
    
    // Submit form using data-testid selector
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    await submitBtn.waitFor({ state: 'visible', timeout });
    
    // Wait for network response
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/api/auth/magic-link') && response.status() === 200,
      { timeout }
    );
    
    await submitBtn.click();
    
    // Wait for API response
    await responsePromise;
    
    // Wait for success message
    const successElement = page.locator(`[data-testid="${TESTIDS.authSuccess}"]`);
    await successElement.waitFor({ state: 'visible', timeout });
    
    // Check if dev magic link button appears and click it
    const devMagicBtn = page.locator('[data-testid="dev-magic-link-btn"]');
    await devMagicBtn.waitFor({ state: 'visible', timeout: 5000 });
    await devMagicBtn.click();
    
    // Wait for navigation to /auth/verify or /app
    await page.waitForURL(url => url.pathname === '/auth/verify' || url.pathname === '/app', { timeout });
    
    console.log(`✅ UI login successful: ${email}`);
  } catch (error) {
    // Take screenshot for debugging
    await page.screenshot({ path: `ui-login-debug-${email.replace('@', '-at-')}.png` });
    console.error(`❌ UI login failed for ${email}:`, error);
    throw error;
  }
}

/**
 * Legacy helper for backward compatibility
 * @deprecated Use login() with mode option instead
 */
export async function loginTestOnly(page: Page, email: string): Promise<void> {
  await login(page, email, { mode: 'test' });
}

/**
 * Legacy helper for backward compatibility  
 * @deprecated Use login() with mode option instead
 */
export async function loginUser(page: Page, email: string): Promise<void> {
  await login(page, email, { mode: 'ui' });
}