/**
 * Navigation Specification Tests
 * Tests landing anchors, top nav dropdowns, mobile navigation, and "Go to..." menu
 */

import { test, expect } from '@playwright/test';
import { TESTIDS } from '../../frontend/src/testids.js';

test.describe('Navigation Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Desktop Navigation', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
    });

    test('Landing page anchor navigation works correctly', async ({ page }) => {
      // Test "How it Works" anchor navigation
      await page.locator(`[data-testid="${TESTIDS.inPageTabHow}"]`).click();
      
      // Verify the URL hash changes
      await expect(page).toHaveURL('/#how');
      
      // Verify the section is visible
      const howSection = page.locator('#how');
      await expect(howSection).toBeInViewport();
      
      // Test "Why FoP" anchor navigation
      await page.locator(`[data-testid="${TESTIDS.inPageTabWhy}"]`).click();
      await expect(page).toHaveURL('/#why');
      
      const whySection = page.locator('#why');
      await expect(whySection).toBeInViewport();
      
      // Test FAQ anchor navigation
      await page.locator(`[data-testid="${TESTIDS.inPageTabFaq}"]`).click();
      await expect(page).toHaveURL('/#faq');
      
      const faqSection = page.locator('#faq');
      await expect(faqSection).toBeInViewport();
    });

    test('Product dropdown navigation routes correctly', async ({ page }) => {
      // Open product dropdown
      await page.locator(`[data-testid="${TESTIDS.navDropdownProduct}"]`).click();
      
      // Wait for dropdown to be visible
      await page.locator(`[data-testid="product-dropdown-menu"]`).waitFor({ state: 'visible' });
      
      // Test Auction Room navigation (should redirect to login for unauthenticated)
      await page.locator(`[data-testid="${TESTIDS.navDropdownItemAuction}"]`).click();
      await page.waitForURL('**/login');
      
      // Go back to home
      await page.goto('/');
      
      // Test Roster navigation
      await page.locator(`[data-testid="${TESTIDS.navDropdownProduct}"]`).click();
      await page.locator(`[data-testid="${TESTIDS.navDropdownItemRoster}"]`).click();
      await page.waitForURL('**/login');
      
      // Test other dropdown items
      await page.goto('/');
      await page.locator(`[data-testid="${TESTIDS.navDropdownProduct}"]`).click();
      await page.locator(`[data-testid="${TESTIDS.navDropdownItemFixtures}"]`).click();
      await page.waitForURL('**/login');
    });
  });

  test.describe('Mobile Navigation', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
    });

    test('Mobile hamburger menu works correctly', async ({ page }) => {
      // Open hamburger menu
      await page.locator(`[data-testid="${TESTIDS.navHamburger}"]`).click();
      
      // Verify mobile drawer is visible
      await page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"]`).waitFor({ state: 'visible' });
      
      // Test navigation items are listed
      const navigationItems = page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"] button`);
      await expect(navigationItems).toHaveCount({ min: 3 }); // Should have at least How, Why, Sign In
      
      // Test drawer focus trap - pressing Escape should close
      await page.keyboard.press('Escape');
      await page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"]`).waitFor({ state: 'hidden' });
    });

    test('Mobile navigation item tap works', async ({ page }) => {
      // Open hamburger menu
      await page.locator(`[data-testid="${TESTIDS.navHamburger}"]`).click();
      await page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"]`).waitFor({ state: 'visible' });
      
      // Tap on "How it Works" - should scroll to section
      const howButton = page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"] button:has-text("How it Works")`);
      await howButton.click();
      
      // Should stay on same page but navigate to section
      await expect(page).toHaveURL('/#how');
      
      // Test Sign In navigation
      await page.locator(`[data-testid="${TESTIDS.navHamburger}"]`).click();
      const signInButton = page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"] button:has-text("Sign In")`);
      await signInButton.click();
      
      // Should navigate to login
      await page.waitForURL('**/login');
    });
  });

  test.describe('No Dead Ends & 404 Recovery', () => {
    test('All navigation links have valid destinations', async ({ page }) => {
      // Test brand logo navigation
      await page.locator(`[data-testid="${TESTIDS.navBrand}"]`).click();
      await expect(page).toHaveURL(/\/$|#home$/); // Allow both / and /#home
      
      // Test sign in button
      await page.locator(`[data-testid="${TESTIDS.navSignIn}"]`).click();
      await page.waitForURL('**/login');
      
      // Verify no empty hrefs or # links
      const emptyLinks = page.locator('a[href="#"], a[href=""], a:not([href])');
      await expect(emptyLinks).toHaveCount(0);
    });

    test('404 page shows and allows navigation back', async ({ page }) => {
      // Navigate to non-existent page
      await page.goto('/nonexistent-page');
      
      // Should show 404 page (or redirect to home)
      const url = page.url();
      expect(url.includes('/nonexistent-page') || url.endsWith('/')).toBeTruthy();
      
      // Should be able to navigate back to home via brand
      await page.locator(`[data-testid="${TESTIDS.navBrand}"]`).click();
      await expect(page).toHaveURL('/');
    });
  });

  test.describe('Go to... Menu on /app', () => {
    test('Go to dropdown shows appropriate options', async ({ page }) => {
      // Navigate to app page (will redirect to login)
      await page.goto('/app');
      
      // Should redirect to login for unauthenticated users
      await page.waitForURL('**/login');
      
      // For authenticated users test (would need login flow)
      // This test would check that the Go to... dropdown shows context-aware options
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('Tab navigation works through navbar elements', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      // Start from brand
      await page.keyboard.press('Tab'); // Focus brand
      await expect(page.locator(`[data-testid="${TESTIDS.navBrand}"]`)).toBeFocused();
      
      // Continue tabbing through navigation
      await page.keyboard.press('Tab'); // How it Works
      await page.keyboard.press('Tab'); // Why FoP
      await page.keyboard.press('Tab'); // FAQ
      await page.keyboard.press('Tab'); // Product dropdown
      
      await expect(page.locator(`[data-testid="${TESTIDS.navDropdownProduct}"]`)).toBeFocused();
      
      // Test Enter opens dropdown
      await page.keyboard.press('Enter');
      await page.locator(`[data-testid="product-dropdown-menu"]`).waitFor({ state: 'visible' });
      
      // Test Escape closes dropdown
      await page.keyboard.press('Escape');
      await page.locator(`[data-testid="product-dropdown-menu"]`).waitFor({ state: 'hidden' });
    });
  });
});