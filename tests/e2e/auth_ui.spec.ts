import { test, expect } from '@playwright/test';
import { TESTIDS } from '../../frontend/src/testids.js';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'https://friends-pifa.preview.emergentagent.com';

test.describe('Authentication UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate directly to login page
    await page.goto('/login');
  });

  test('Login page loads with all required elements', async ({ page }) => {
    // Verify page loads correctly
    await expect(page).toHaveURL('/login');
    await expect(page).toHaveTitle(/Friends of PIFA/);

    // Verify all required elements are present using data-testids only
    await expect(page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`)).toBeVisible();
    await expect(page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`)).toBeVisible();
    
    // Verify error and success containers exist (but may not be visible initially)
    await expect(page.locator(`[data-testid="${TESTIDS.authError}"]`)).not.toBeVisible();
    await expect(page.locator(`[data-testid="${TESTIDS.authSuccess}"]`)).not.toBeVisible();

    // Verify back to home link exists
    await expect(page.locator('[data-testid="back-to-home-link"]')).toBeVisible();
  });

  test('Submit button is disabled for invalid email', async ({ page }) => {
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);

    // Initially disabled when empty
    await expect(submitBtn).toBeDisabled();

    // Still disabled for invalid email
    await emailInput.fill('invalid-email');
    await expect(submitBtn).toBeDisabled();

    // Still disabled for incomplete email
    await emailInput.fill('test@');
    await expect(submitBtn).toBeDisabled();

    // Enabled for valid email
    await emailInput.fill('test@example.com');
    await expect(submitBtn).not.toBeDisabled();
  });

  test('Shows error for invalid email submission', async ({ page }) => {
    const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
    const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
    const errorElement = page.locator(`[data-testid="${TESTIDS.authError}"]`);

    // Try to submit with empty email
    await emailInput.fill('');
    await emailInput.blur(); // Trigger validation
    
    // Enter invalid email and try to submit
    await emailInput.fill('invalid-email');
    await submitBtn.click({ force: true }); // Force click even if disabled
    
    // Error should be visible
    await expect(errorElement).toBeVisible();
    await expect(errorElement).toContainText('valid email address');
  });

  test('Successfully submits valid email and shows success', async ({ page }) => {
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
    await responsePromise;

    // Wait for success message
    await expect(successElement).toBeVisible({ timeout: 10000 });
    await expect(successElement).toContainText('Magic link sent');

    // In test mode, should automatically redirect to /auth/verify then /app
    // Wait for navigation to happen
    await page.waitForURL(url => url.pathname === '/auth/verify' || url.pathname === '/app', { timeout: 10000 });
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
    
    // Click submit and verify loading state
    await submitBtn.click();
    
    // Button should show loading text and be disabled
    await expect(submitBtn).toContainText('Sending Magic Link');
    await expect(submitBtn).toBeDisabled();
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
  test('Complete auth flow from login to app', async ({ page }) => {
    // Start at login page
    await page.goto('/login');
    
    // Fill and submit form using only data-testids
    await page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`).fill('integration-test@example.com');
    await page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`).click();
    
    // Wait for success and automatic redirect in test mode
    await expect(page.locator(`[data-testid="${TESTIDS.authSuccess}"]`)).toBeVisible();
    await expect(page).toHaveURL('/app', { timeout: 5000 });
    
    // Verify we landed on the app page successfully
    // (The app page should handle the authentication token verification)
    await expect(page).toHaveURL(/\/app/);
  });
});