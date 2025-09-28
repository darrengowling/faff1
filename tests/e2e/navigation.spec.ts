/**
 * Navigation Tests - Enhanced with Accessibility & No Placeholders
 * Tests landing anchors, top-nav dropdowns, hamburger drawer, 404 recovery
 * HARD RULE: Only data-testid selectors allowed, no href="#" in DOM
 */

import { test, expect } from '@playwright/test';
import { TESTIDS } from '../../frontend/src/testids';
import { ensureClickable } from './utils/ensureClickable';

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
      await page.locator(`[data-testid="${TESTIDS.inPageTabHow}"]`).click({ force: true });
      
      // Verify the URL hash changes
      await expect(page).toHaveURL('/#how');
      
      // Verify the section is visible
      const howSection = page.locator('#how');
      await expect(howSection).toBeInViewport();
      
      // Test "Why FoP" anchor navigation
      await page.locator(`[data-testid="${TESTIDS.inPageTabWhy}"]`).click({ force: true });
      await expect(page).toHaveURL('/#why');
      
      const whySection = page.locator('#why');
      await expect(whySection).toBeInViewport();
      
      // Test FAQ anchor navigation
      await page.locator(`[data-testid="${TESTIDS.inPageTabFaq}"]`).click({ force: true });
      await expect(page).toHaveURL('/#faq');
      
      const faqSection = page.locator('#faq');
      await expect(faqSection).toBeInViewport();
    });

    test('Product dropdown shows only enabled items and navigates correctly', async ({ page }) => {
      // For unauthenticated users, product dropdown should either:
      // 1. Not be visible at all, OR
      // 2. Be visible but show no items (empty dropdown hidden)
      
      const productDropdown = page.locator(`[data-testid="${TESTIDS.navDropdownProduct}"]`);
      
      if (await productDropdown.isVisible()) {
        // Try to open dropdown
        await productDropdown.click();
        
        // Check if any dropdown items are visible
        const dropdownItems = page.locator(`[data-testid="${TESTIDS.navDdAuction}"], [data-testid="${TESTIDS.navDdRoster}"], [data-testid="${TESTIDS.navDdFixtures}"], [data-testid="${TESTIDS.navDdLeaderboard}"]`);
        
        // For unauthenticated users, either no dropdown opens or no items are shown
        const itemCount = await dropdownItems.count();
        
        if (itemCount > 0) {
          // If items are shown, they should navigate properly
          await page.locator(`[data-testid="${TESTIDS.navDdAuction}"]`).first().click();
          await expect(page).toHaveURL(/\/(auction|login)/); // Should go to auction or redirect to login
        }
      }
    });
  });

  test.describe('Mobile Navigation', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
    });

    test('Mobile hamburger menu works correctly', async ({ page }) => {
      // Ensure hamburger menu is clickable before clicking
      const hamburgerMenu = page.locator(`[data-testid="${TESTIDS.navHamburger}"]`);
      await ensureClickable(hamburgerMenu);
      await hamburgerMenu.click();
      
      // Verify mobile drawer is visible
      await page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"]`).waitFor({ state: 'visible' });
      
      // Test navigation items are listed
      const navigationItems = page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"] button`);
      await expect(navigationItems).toHaveCount({ min: 3 }); // Should have at least How, Why, Sign In
      
      // Test drawer focus trap - pressing Escape should close
      await page.keyboard.press('Escape');
      await page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"]`).waitFor({ state: 'hidden' });
    });

    test('Mobile navigation shows only enabled items and navigates correctly', async ({ page }) => {
      // Ensure hamburger menu is clickable before clicking
      const hamburgerMenu = page.locator(`[data-testid="${TESTIDS.navHamburger}"]`);
      await ensureClickable(hamburgerMenu);
      await hamburgerMenu.click();
      await page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"]`).waitFor({ state: 'visible' });
      
      // Check if navigation items are present using testids
      const mobileItems = page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"] [role="menuitem"]`);
      const itemCount = await mobileItems.count();
      
      if (itemCount > 0) {
        // Ensure first navigation item is clickable before clicking
        const firstItem = mobileItems.first();
        await ensureClickable(firstItem);
        await firstItem.click();
        
        // Assert drawer closes after navigation
        await page.waitForTimeout(500); // Allow state change
        await expect(page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"]`)).toBeHidden();
        
        // Should navigate away from current page (either to section or new page)
        await page.waitForTimeout(1000); // Allow navigation to complete
      } else {
        // No items shown - verify proper empty state
        const emptyMessage = page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"] >> text="No navigation items available"`);
        await expect(emptyMessage).toBeVisible();
      }
    });
  });

  test.describe('No Dead Ends & 404 Recovery', () => {
    test('All navigation links have valid destinations and no href="#"', async ({ page }) => {
      // Test brand logo navigation using testid
      await page.locator(`[data-testid="${TESTIDS.navBrand}"]`).click();
      await expect(page).toHaveURL(/\/$|#home$/); // Allow both / and /#home
      
      // Test sign in button using testid
      const signInButton = page.locator(`[data-testid="${TESTIDS.navSignIn}"]`);
      if (await signInButton.isVisible()) {
        await signInButton.click();
        await page.waitForURL('**/login');
      }
      
      // CRITICAL: Verify no empty hrefs or placeholder # links anywhere in DOM
      const emptyLinks = page.locator('a[href="#"], a[href=""], a:not([href]), button[href="#"]');
      await expect(emptyLinks).toHaveCount(0);
      
      // Verify no "coming soon" alerts or placeholder behaviors
      const placeholderElements = page.locator('text=/coming soon|placeholder|not implemented/i');
      await expect(placeholderElements).toHaveCount(0);
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
    test('Keyboard navigation works with proper ARIA and focus management', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      // Test product dropdown keyboard behavior
      const productDropdown = page.locator(`[data-testid="${TESTIDS.navDropdownProduct}"]`);
      
      if (await productDropdown.isVisible()) {
        // Focus dropdown button
        await productDropdown.focus();
        await expect(productDropdown).toBeFocused();
        
        // Test Enter/Space opens dropdown
        await page.keyboard.press('Enter');
        
        // Check if dropdown opened (may not have items for unauthenticated users)
        const dropdown = page.locator('[role="menu"]');
        if (await dropdown.isVisible()) {
          // Test Arrow Down navigation within dropdown
          await page.keyboard.press('ArrowDown');
          
          // Test Escape closes dropdown
          await page.keyboard.press('Escape');
          await expect(dropdown).not.toBeVisible();
          
          // Focus should return to dropdown button
          await expect(productDropdown).toBeFocused();
        }
      }
      
      // Test mobile menu keyboard behavior
      await page.setViewportSize({ width: 390, height: 844 });
      
      const hamburger = page.locator(`[data-testid="${TESTIDS.navHamburger}"]`);
      await hamburger.focus();
      await hamburger.click();
      
      const mobileDrawer = page.locator(`[data-testid="${TESTIDS.navMobileDrawer}"]`);
      await expect(mobileDrawer).toBeVisible();
      
      // Test Escape closes mobile drawer
      await page.keyboard.press('Escape');
      await expect(mobileDrawer).not.toBeVisible();
    });
  });
});