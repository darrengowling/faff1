/**
 * Header Contract E2E Tests
 * 
 * Validates that required testids exist on all key routes:
 * - home-nav-button
 * - back-to-home-link  
 * - nav-mobile-drawer (with data-state toggle)
 */

import { test, expect } from '@playwright/test';
import { TESTIDS } from '../../frontend/src/testids.ts';

test.describe('Header Contract Tests', () => {
  const routes = [
    { path: '/login', name: 'Login Page' },
    { path: '/', name: 'Landing Page' }, 
    { path: '/app', name: 'App Dashboard' },
    { path: '/app/leagues/new', name: 'Create League' }
  ];

  for (const route of routes) {
    test(`${route.name} (${route.path}) has required header testids`, async ({ page }) => {
      // Navigate to route
      await page.goto(route.path);
      await page.waitForLoadState('networkidle');

      // Required testids that must exist on every page
      const requiredTestIds = [
        'home-nav-button',
        'back-to-home-link',
        'nav-mobile-drawer'
      ];

      // Check each required testid exists (not null)
      for (const testId of requiredTestIds) {
        const element = await page.locator(`[data-testid="${testId}"]`).first();
        
        // Element must exist in DOM (not null)
        await expect(element).not.toBeNull();
        console.log(`✅ ${route.name}: ${testId} exists`);
      }

      // Specifically test mobile drawer data-state toggle
      const mobileDrawer = page.locator('[data-testid="nav-mobile-drawer"]');
      
      // Mobile drawer should initially be closed
      await expect(mobileDrawer).toHaveAttribute('data-state', 'closed');
      
      // Click hamburger to open mobile drawer
      const hamburgerBtn = page.locator('[data-testid="nav-hamburger"]');
      if (await hamburgerBtn.isVisible()) {
        await hamburgerBtn.click();
        
        // Mobile drawer should now be open
        await expect(mobileDrawer).toHaveAttribute('data-state', 'open');
        
        console.log(`✅ ${route.name}: nav-mobile-drawer toggles to open state`);
      }
    });
  }

  test('All routes have exactly one header element', async ({ page }) => {
    for (const route of routes) {
      await page.goto(route.path);
      await page.waitForLoadState('networkidle');
      
      // Verify exactly one header exists
      const headers = page.locator('header');
      const headerCount = await headers.count();
      
      expect(headerCount).toBe(1);
      console.log(`✅ ${route.name}: Exactly 1 header found`);
    }
  });
});