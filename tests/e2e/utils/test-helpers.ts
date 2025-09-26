/**
 * Test Helpers for Production Readiness Regression
 * Enforces deterministic testing with data-testid only selectors
 */

import { Page, expect } from '@playwright/test';
import { TESTIDS } from '../../../frontend/src/testids';

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * Enforce data-testid only selectors - no heuristics allowed
   */
  static validateSelector(selector: string) {
    if (!selector.startsWith('[data-testid=') && !selector.includes('data-testid')) {
      throw new Error(`❌ INVALID SELECTOR: "${selector}" - Only data-testid selectors allowed`);
    }
  }

  /**
   * Safe click with data-testid validation
   */
  async clickByTestId(testId: keyof typeof TESTIDS) {
    const selector = `[data-testid="${TESTIDS[testId]}"]`;
    TestHelpers.validateSelector(selector);
    
    await expect(this.page.locator(selector)).toBeVisible();
    await this.page.click(selector);
  }

  /**
   * Safe fill with data-testid validation
   */
  async fillByTestId(testId: keyof typeof TESTIDS, value: string) {
    const selector = `[data-testid="${TESTIDS[testId]}"]`;
    TestHelpers.validateSelector(selector);
    
    await expect(this.page.locator(selector)).toBeVisible();
    await this.page.fill(selector, value);
  }

  /**
   * Wait for element with specific text - deterministic
   */
  async waitForTestIdWithText(testId: keyof typeof TESTIDS, text: string) {
    const selector = `[data-testid="${TESTIDS[testId]}"]`;
    TestHelpers.validateSelector(selector);
    
    await expect(this.page.locator(selector)).toHaveText(text);
  }

  /**
   * Assert element count - no guessing
   */
  async assertTestIdCount(testId: keyof typeof TESTIDS, count: number) {
    const selector = `[data-testid="${TESTIDS[testId]}"]`;
    TestHelpers.validateSelector(selector);
    
    await expect(this.page.locator(selector)).toHaveCount(count);
  }

  /**
   * Console error monitoring
   */
  setupConsoleErrorTracking() {
    const errors: string[] = [];
    
    this.page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    this.page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    return () => {
      if (errors.length > 0) {
        throw new Error(`❌ Console errors detected: ${errors.join(', ')}`);
      }
    };
  }

  /**
   * Network error monitoring
   */
  setupNetworkErrorTracking() {
    const networkErrors: string[] = [];
    
    this.page.on('response', (response) => {
      const status = response.status();
      if (status >= 400 && status < 600) {
        // Allow expected errors (like 401 for unauthenticated requests)
        const url = response.url();
        if (!url.includes('/auth/me') || status !== 401) {
          networkErrors.push(`${status} ${response.url()}`);
        }
      }
    });

    return () => {
      if (networkErrors.length > 0) {
        throw new Error(`❌ Unexpected network errors: ${networkErrors.join(', ')}`);
      }
    };
  }

  /**
   * Auth helper for test users
   */
  async loginTestUser(email: string) {
    await this.fillByTestId('emailInput', email);
    await this.clickByTestId('magicLinkSubmit');
    
    // Wait for magic link response
    await expect(this.page.locator(`[data-testid="${TESTIDS.loginNowButton}"]`)).toBeVisible({ timeout: 15000 });
    await this.clickByTestId('loginNowButton');
    
    // Wait for dashboard redirect
    await this.page.waitForURL('**/dashboard', { timeout: 15000 });
  }
}

/**
 * Rules badge checker for config drift detection
 */
export async function checkRulesBadge(page: Page, expectedMin: number, expectedSlots: number) {
  // Look for rules badge or settings display
  const rulesBadge = page.locator('[data-testid*="rules"], [data-testid*="settings"], .rules-badge');
  
  if (await rulesBadge.count() > 0) {
    const text = await rulesBadge.textContent();
    
    if (text?.includes(expectedMin.toString()) && text?.includes(expectedSlots.toString())) {
      return true;
    }
    
    throw new Error(`❌ Config drift detected: Expected min=${expectedMin}, slots=${expectedSlots}, found: ${text}`);
  }
  
  return false; // No rules badge found - not necessarily an error
}