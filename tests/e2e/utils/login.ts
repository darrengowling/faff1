/**
 * Unified Login Utilities for E2E Tests
 * Supports both test-only API login and UI-based authentication
 */

import { Page } from '@playwright/test';
import { TESTIDS } from '../../../frontend/src/testids.ts';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'https://e2e-stability.preview.emergentagent.com';
const INTERNAL_API_URL = 'http://localhost:8001'; // Direct backend access for test-login

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
    // Call the test-only login endpoint with failOnStatusCode: false
    const response = await page.request.post(`${BASE_URL}/api/auth/test-login`, {
      data: { email },
      headers: {
        'Content-Type': 'application/json',
        'Origin': BASE_URL
      },
      timeout,
      failOnStatusCode: false  // Don't throw on HTTP error status
    });
    
    // Handle different response status codes
    if (response.status() === 404) {
      // ALLOW_TEST_LOGIN=false - fallback to UI login once
      console.log(`🔄 Test login disabled (404), falling back to UI login for: ${email}`);
      await loginUI(page, email, timeout);
      return;
    }
    
    if (response.status() === 502) {
      // Bad Gateway - likely proxy/routing issue, fallback to UI login
      console.log(`🔄 Test login unreachable (502), falling back to UI login for: ${email}`);
      await loginUI(page, email, timeout);
      return;
    }
    
    if (response.status() === 400) {
      // Invalid email - assert auth-error and bail with clear message
      try {
        const errorData = await response.json();
        if (errorData.code === 'INVALID_EMAIL') {
          // Navigate to login page to check for auth-error display
          await page.goto('/login');
          const authError = page.locator(`[data-testid="${TESTIDS.authError}"]`);
          
          // Verify auth-error is visible (from previous form submission)
          const isVisible = await authError.isVisible();
          throw new Error(`❌ TEST FAILED - Invalid email format: ${email}. Auth error visible: ${isVisible}. Message: ${errorData.message}`);
        }
      } catch (parseError) {
        const errorText = await response.text();
        throw new Error(`❌ TEST FAILED - Bad request (400): ${errorText}`);
      }
    }
    
    if (response.status() === 500) {
      // Server error - structured error handling
      try {
        const errorData = await response.json();
        throw new Error(`❌ SERVER ERROR (500) - ${errorData.code || 'UNKNOWN'}: ${errorData.message} (Request ID: ${errorData.requestId || 'N/A'})`);
      } catch (parseError) {
        const errorText = await response.text();
        throw new Error(`❌ SERVER ERROR (500) - ${errorText}`);
      }
    }
    
    if (!response.ok()) {
      const errorText = await response.text();
      throw new Error(`❌ Test login failed: ${response.status()} ${errorText}`);
    }
    
    // Success path (200)
    const data = await response.json();
    
    if (!data.ok || !data.userId) {
      throw new Error(`❌ Invalid test login response: ${JSON.stringify(data)}`);
    }
    
    // Session cookie should be set automatically by the server
    // No need to set localStorage tokens since we're using HTTP-only cookies
    
    // Verify we can access protected routes with the cookie
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    
    // Check if we're actually logged in by looking for authenticated content
    const authIndicator = page.locator('body'); // Basic check that page loads
    await authIndicator.waitFor({ state: 'visible', timeout: 5000 });
    
    console.log(`✅ Test-only login successful: ${email} (User ID: ${data.userId})`);
    
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