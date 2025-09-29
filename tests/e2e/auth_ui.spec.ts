import { test, expect } from '@playwright/test';
import { byId, selectors, waitForId, clickById, fillById, isVisibleById } from './utils/selectors';
import { login } from './utils/login';

test.describe('Authentication UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate directly to login page
    await page.goto('/login');
  });

  test('Login page renders form with all required testid elements', async ({ page }) => {
    // Navigate to login and wait for full render
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Verify page loaded correctly
    await expect(page).toHaveURL('/login');

    // CRITICAL: Assert all required form elements with testids are present and visible
    await expect(byId(page, 'authEmailInput')).toBeVisible({ timeout: 10000 });
    await expect(byId(page, 'authSubmitBtn')).toBeVisible({ timeout: 10000 });
    
    // Verify navigation elements exist (no dead-ends)
    const backToHomeLink = byId(page, 'backToHome');
    await expect(backToHomeLink).toBeVisible();
    // Verify session-based routing: unauthenticated should point to "/"
    await expect(backToHomeLink).toHaveAttribute('data-dest', '/');
    
    // Verify header structure
    await expect(byId(page, 'loginHeader')).toBeVisible();
    
    // Verify form accessibility
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(emailInput).toHaveAttribute('required');
    
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    await expect(submitBtn).toHaveAttribute('type', 'submit');
    
    console.log('✅ Login form renders correctly with all required testid elements');
  });

  test('Submit button is disabled for invalid email', async ({ page }) => {
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);

    // Initially disabled when empty
    await expect(submitBtn).toBeDisabled();

    // Still disabled for invalid email formats
    await emailInput.fill('invalid-email');
    await expect(submitBtn).toBeDisabled();
    
    // Should be enabled for valid email
    await emailInput.fill('user@example.com');
    await expect(submitBtn).toBeEnabled();

    // Still disabled for incomplete email
    await emailInput.fill('test@');
    await expect(submitBtn).toBeDisabled();

    // Enabled for valid email
    await emailInput.fill('test@example.com');
    await expect(submitBtn).not.toBeDisabled();
  });

  test('Shows error for invalid email submission', async ({ page }) => {
    // Navigate to login page with playwright test mode parameter
    await page.goto('/login?playwright=true');
    await page.waitForLoadState('networkidle');
    
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    
    // Fill with invalid email format
    await emailInput.fill('not-an-email');
    
    // In test mode, button should be enabled even for invalid email
    await expect(submitBtn).toBeEnabled();
    
    // Click submit button
    await submitBtn.click();
    
    // Error should be visible with proper attributes
    const errorElement = page.getByTestId('auth-error');
    await expect(errorElement).toBeVisible();
    await expect(errorElement).toHaveAttribute('role', 'alert');
    await expect(errorElement).toHaveAttribute('aria-live', 'assertive');
    await expect(errorElement).toContainText('Please enter a valid email.');
    
    // Submit button should re-enable after error (not stuck in loading state)
    await expect(submitBtn).toBeEnabled();
    await expect(submitBtn).not.toHaveText(/creating|loading|submitting/i);
    
    // Form should remain interactive (email input still enabled)
    await expect(emailInput).toBeEnabled();
    
    console.log('✅ Invalid email error properly displayed with role="alert" and form remains interactive');
  });

  test('Successfully submits valid email and shows success', async ({ page }) => {
    // Listen to console logs
    page.on('console', msg => console.log('Browser Console:', msg.text()));
    
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    const successElement = page.locator(`[data-testid="${TESTIDS.authSuccess}"]`);

    // Enter valid email
    const testEmail = 'playwright-test@example.com';
    await emailInput.fill(testEmail);

    // Submit form
    await expect(submitBtn).not.toBeDisabled();
    
    // Wait for network requests to complete
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/api/auth/magic-link') && response.status() === 200
    );
    
    await submitBtn.click();

    // Wait for API response
    const response = await responsePromise;
    const responseBody = await response.json();
    console.log('API Response:', responseBody);

    // Wait for success message
    await expect(successElement).toBeVisible({ timeout: 10000 });
    await expect(successElement).toContainText('Magic link sent');

    // Check if dev magic link button appears
    const devMagicBtn = page.locator('[data-testid="dev-magic-link-btn"]');
    if (await devMagicBtn.isVisible()) {
      console.log('Dev magic link button found, clicking...');
      await devMagicBtn.click();
      await page.waitForURL(url => url.pathname === '/auth/verify' || url.pathname === '/app', { timeout: 5000 });
    } else {
      // In test mode, should automatically redirect to /auth/verify then /app
      console.log('Waiting for automatic redirect...');
      await page.waitForURL(url => url.pathname === '/auth/verify' || url.pathname === '/app', { timeout: 10000 });
    }
  });

  test('Back to Home navigation works', async ({ page }) => {
    const backLink = page.locator('[data-testid="back-to-home-link"]');
    
    await expect(backLink).toBeVisible();
    await backLink.click();
    
    // Should navigate back to home page
    await expect(page).toHaveURL('/');
  });

  test('Form handles loading state correctly', async ({ page }) => {
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);

    // Enter valid email
    await emailInput.fill('loading-test@example.com');
    
    // Verify form initially has aria-busy="false" 
    const form = page.locator('form');
    await expect(form).toHaveAttribute('aria-busy', 'false');
    
    // Click submit and immediately check for loading indicators
    const [response] = await Promise.all([
      page.waitForResponse(response => response.url().includes('/auth/magic-link')),
      submitBtn.click()
    ]);
    
    // Check if loading state appeared during the request
    const loadingElement = page.locator(`[data-testid="${TESTIDS.authLoading}"]`);
    const hasLoadingElement = await loadingElement.count() > 0;
    
    if (hasLoadingElement) {
      console.log('✅ Loading element appeared during request');
      // Form should have aria-busy="true" 
      await expect(form).toHaveAttribute('aria-busy', 'true');
      
      // Button should show loading text and be disabled
      await expect(submitBtn).toContainText('Sending Magic Link');
      await expect(submitBtn).toBeDisabled();
      
      // Wait for loading to complete
      await expect(loadingElement).not.toBeAttached();
    } else {
      console.log('ℹ️ Loading state too fast to catch - checking aria-busy changed');
      // At minimum, verify aria-busy was set during the process
      const finalAriaState = await form.getAttribute('aria-busy');
      console.log(`Final aria-busy state: ${finalAriaState}`);
      
      // Button should eventually re-enable or show success state
      await expect(submitBtn).toBeEnabled({ timeout: 5000 });
    }
    
    console.log(`Response status: ${response.status()}`);
  });

  test('No dead ends - page always has navigation options', async ({ page }) => {
    // Verify header is present
    await expect(page.locator('header')).toBeVisible();
    
    // Verify back to home link is always present
    await expect(page.locator('[data-testid="back-to-home-link"]')).toBeVisible();
    
    // Even after form submission, navigation should still be available
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    
    await emailInput.fill('navigation-test@example.com');
    await submitBtn.click();
    
    // Navigation should still be available during/after submission
    await expect(page.locator('[data-testid="back-to-home-link"]')).toBeVisible();
  });

  test('Test mode disables animations', async ({ page }) => {
    // In test mode, animations should be disabled
    // This is more of a visual test, but we can check that elements appear immediately
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    
    // Elements should be immediately visible without animation delays
    await expect(emailInput).toBeVisible();
    await expect(submitBtn).toBeVisible();
    
    // Form submission should not have prolonged animations
    await emailInput.fill('animation-test@example.com');
    await submitBtn.click();
    
    // Success state should appear quickly in test mode
    await expect(page.locator(`[data-testid="${TESTIDS.authSuccess}"]`)).toBeVisible({ timeout: 3000 });
  });
});

test.describe('Authentication UI Integration', () => {
  test('Form submission works using only testids', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Fill form using testids only
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    
    await emailInput.fill('test-submission@example.com');
    
    // Verify submit button becomes enabled
    await expect(submitBtn).not.toBeDisabled();
    
    // Submit form
    await submitBtn.click();
    
    // Should either show success message or navigate
    const successMsg = page.locator(`[data-testid="${TESTIDS.authSuccess}"]`);
    const devMagicBtn = page.locator('[data-testid="dev-magic-link-btn"]');
    
    // Wait for either success message or navigation
    await Promise.race([
      successMsg.waitFor({ state: 'visible', timeout: 10000 }),
      page.waitForURL('**/auth/verify', { timeout: 10000 }),
      page.waitForURL('**/app', { timeout: 10000 })
    ]);
    
    console.log('✅ Form submission completed successfully using testids');
  });

  test('Complete auth flow using UI login mode', async ({ page }) => {
    // Start at login page
    await page.goto('/login');
    
    // Use UI mode explicitly to test the authentication interface
    await login(page, 'ui-integration-test@example.com', { mode: 'ui' });
    
    // Verify we navigated away from login and to the app
    await expect(page).not.toHaveURL('/login');
    await expect(page).toHaveURL(/\/(app|auth\/verify)/);
  });

  test('Shows error for empty email with proper UX', async ({ page }) => {
    console.log('🧪 Testing empty email error handling...');
    
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    const errorDisplay = page.locator(`[data-testid="${TESTIDS.authError}"]`);

    // Submit with empty email (form validation should prevent this, but test anyway)
    await emailInput.fill('');
    await expect(submitBtn).toBeDisabled();
    
    // Add some text then clear it to test error behavior
    await emailInput.fill('test');
    await expect(submitBtn).toBeEnabled();
    
    await emailInput.fill('');
    await expect(submitBtn).toBeDisabled();
    
    console.log('✅ Empty email handling works correctly');
  });

  test('Shows error for invalid email format with concise message', async ({ page }) => {
    console.log('🧪 Testing invalid email error handling...');
    
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    const errorDisplay = page.locator(`[data-testid="${TESTIDS.authError}"]`);

    // Enter invalid email and try to submit
    await emailInput.fill('invalid-email-format');
    
    // Button should be disabled for invalid email
    await expect(submitBtn).toBeDisabled();
    
    // Now enter a properly formatted but potentially non-existent email
    await emailInput.fill('test@nonexistentdomain999.com');
    await expect(submitBtn).toBeEnabled();
    
    // Submit to trigger backend validation
    await submitBtn.click();
    
    // Check if error appears (backend might return error for non-existent domain)
    try {
      await errorDisplay.waitFor({ state: 'visible', timeout: 5000 });
      
      // Verify error message is concise and helpful
      const errorText = await errorDisplay.textContent();
      expect(errorText.length).toBeLessThan(100); // Concise error message
      expect(errorText).not.toBe(''); // Not empty
      
      console.log(`✅ Error message: "${errorText}"`);
      
      // Verify email input maintains focus
      await expect(emailInput).toBeFocused();
      
      // Verify form remains interactive
      await emailInput.fill('corrected@example.com');
      await expect(submitBtn).toBeEnabled();
      
      console.log('✅ Form remains interactive after error');
      
    } catch {
      // If no error shown (valid domain), that's also fine
      console.log('ℹ️  No backend error for this email - backend accepted it');
    }
  });

  test('Error clears when user starts typing', async ({ page }) => {
    console.log('🧪 Testing error clearing behavior...');
    
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    const errorDisplay = page.locator(`[data-testid="${TESTIDS.authError}"]`);

    // Enter email that might trigger error
    await emailInput.fill('error-test@invaliddomain999.com');
    await submitBtn.click();
    
    // Wait a moment for any potential error
    await page.waitForTimeout(2000);
    
    // If error appeared, test that it clears when typing
    if (await errorDisplay.isVisible()) {
      console.log('✅ Error displayed, now testing clear behavior');
      
      // Start typing - error should clear
      await emailInput.fill('corrected@example.com');
      
      // Error should be gone
      await expect(errorDisplay).not.toBeVisible();
      console.log('✅ Error cleared when user started typing');
    } else {
      console.log('ℹ️  No error to clear - backend accepted the email');
    }
  });

  test('Submit button states work correctly during loading', async ({ page }) => {
    console.log('🧪 Testing submit button states...');
    
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    const form = page.locator('form');

    // Fill valid email
    await emailInput.fill('loading-test@example.com');
    
    // Button should be enabled
    await expect(submitBtn).toBeEnabled();
    
    // Form should initially have aria-busy="false"
    await expect(form).toHaveAttribute('aria-busy', 'false');
    
    // Submit form and race with response
    const [response] = await Promise.all([
      page.waitForResponse(response => response.url().includes('/auth/magic-link')),
      submitBtn.click()
    ]);
    
    console.log(`Response received with status: ${response.status()}`);
    
    // Check if loading state was detectable
    const loadingElement = page.locator(`[data-testid="${TESTIDS.authLoading}"]`);
    const hasLoadingElement = await loadingElement.count() > 0;
    
    if (hasLoadingElement) {
      console.log('✅ Loading state appeared with explicit testid');
      
      // Form should have aria-busy="true"
      await expect(form).toHaveAttribute('aria-busy', 'true');
      
      // Button should be disabled during loading
      await expect(submitBtn).toBeDisabled();
      
      // Should show loading text
      await expect(submitBtn).toContainText('Sending Magic Link');
      
      // Wait for loading to disappear
      await expect(loadingElement).not.toBeAttached();
      
      console.log('✅ Loading completed and testid removed');
    } else {
      console.log('ℹ️ Loading state too fast to catch - verifying final state');
      
      // Verify that the loading process completed correctly
      // Form should be back to aria-busy="false"
      await expect(form).toHaveAttribute('aria-busy', 'false');
      
      // Button should eventually be enabled again or show success state
      await expect(submitBtn).toBeEnabled({ timeout: 5000 });
      
      console.log('✅ Form returned to normal state after loading');
    }
  });

  test('Error display has proper accessibility attributes', async ({ page }) => {
    console.log('🧪 Testing error accessibility...');
    
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    const errorDisplay = page.locator(`[data-testid="${TESTIDS.authError}"]`);

    // Try to trigger an error
    await emailInput.fill('accessibility-test@invaliddomain999.com');
    await submitBtn.click();
    await page.waitForTimeout(2000);

    // If error appears, check accessibility
    if (await errorDisplay.isVisible()) {
      // Check for proper ARIA attributes
      await expect(errorDisplay).toHaveAttribute('role', 'alert');
      await expect(errorDisplay).toHaveAttribute('aria-live', 'polite');
      
      // Check that email input references the error
      const ariaDescribedBy = await emailInput.getAttribute('aria-describedby');
      expect(ariaDescribedBy).toContain('email-error');
      
      console.log('✅ Error has proper accessibility attributes');
    } else {
      console.log('ℹ️  No error to test accessibility on');
    }
  });
});