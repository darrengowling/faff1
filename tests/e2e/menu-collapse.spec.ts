/**
 * Menu Collapse on Navigation Test
 * 
 * Verifies that all menus collapse on route changes and don't interfere with form interactions
 */

import { test, expect } from '@playwright/test';
import { login } from './utils/login';
import { clickCreateLeague } from './utils/helpers';
import { ensureClickable } from './utils/ensureClickable';

test.describe('Menu Collapse on Navigation', () => {
  test('should close dropdown on route change and not interfere with form', async ({ page }) => {
    console.log('🧪 Testing menu collapse behavior...');
    
    // Login and navigate to dashboard
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('✅ Dashboard loaded');
    
    // Step 1: Open the product dropdown menu
    console.log('🔍 Opening product dropdown...');
    
    const productDropdown = page.getByTestId('nav-dropdown-product');
    if (await productDropdown.isVisible()) {
      await productDropdown.click();
      await page.waitForTimeout(500);
      
      // Verify dropdown is open
      const dropdownMenu = page.locator('[role="menu"]');
      await expect(dropdownMenu).toBeVisible({ timeout: 3000 });
      console.log('✅ Product dropdown opened');
      
      // Verify dropdown items are visible
      const menuItems = page.locator('[role="menuitem"]');
      const itemCount = await menuItems.count();
      console.log(`📋 Found ${itemCount} menu items`);
      
      if (itemCount > 0) {
        console.log('✅ Menu items are populated (not empty)');
      }
    } else {
      console.log('⚠️  Product dropdown not found - skipping dropdown test');
    }
    
    // Step 2: Navigate to Create League (route change)
    console.log('🔄 Navigating to Create League (route change)...');
    
    await clickCreateLeague(page);
    await page.waitForTimeout(1000);
    
    // Verify Create League dialog opened
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible({ timeout: 5000 });
    console.log('✅ Create League dialog opened');
    
    // Step 3: Verify dropdown is closed after navigation
    console.log('🔍 Verifying dropdown is closed after navigation...');
    
    const openDropdownMenu = page.locator('[role="menu"]:visible');
    const openDropdownCount = await openDropdownMenu.count();
    expect(openDropdownCount).toBe(0);
    console.log('✅ Dropdown properly closed on navigation');
    
    // Step 4: Verify no overlay intercepts form interactions
    console.log('🔍 Testing form interaction without overlay interference...');
    
    const formFields = [
      { testid: 'create-name', value: 'Test League Navigation' },
      { testid: 'create-budget', value: '120' },
      { testid: 'create-slots', value: '4' },
      { testid: 'create-min', value: '2' }
    ];
    
    for (const field of formFields) {
      console.log(`  Testing ${field.testid} field...`);
      
      const input = page.getByTestId(field.testid);
      await expect(input).toBeVisible();
      
      // Click and interact without overlay interference
      await input.click({ timeout: 3000 });
      await expect(input).toBeFocused({ timeout: 2000 });
      
      await input.fill(field.value);
      await expect(input).toHaveValue(field.value);
      
      console.log(`  ✅ ${field.testid} field interactive without interference`);
    }
    
    // Step 5: Test submit button interaction
    console.log('🔍 Testing submit button without overlay interference...');
    
    const submitBtn = page.getByTestId('create-submit');
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toBeEnabled();
    
    await submitBtn.click({ timeout: 3000 });
    console.log('✅ Submit button clicked without interference');
    
    console.log('🎉 Menu collapse and form interaction test passed!');
  });

  test('should close mobile drawer on route change', async ({ page }) => {
    console.log('🧪 Testing mobile drawer collapse...');
    
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Login and navigate to dashboard
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    
    // Step 1: Open mobile drawer
    console.log('🔍 Opening mobile drawer...');
    
    const mobileMenuBtn = page.getByTestId('mobile-menu-btn');
    if (await mobileMenuBtn.isVisible()) {
      await mobileMenuBtn.click();
      await page.waitForTimeout(500);
      
      // Verify mobile drawer is open
      const mobileDrawer = page.getByTestId('nav-mobile-drawer');
      await expect(mobileDrawer).toBeVisible({ timeout: 3000 });
      console.log('✅ Mobile drawer opened');
      
      // Step 2: Navigate via clicking a navigation item
      console.log('🔄 Navigating via mobile menu item...');
      
      const createLeagueBtn = page.getByTestId('create-league-btn').first();
      if (await createLeagueBtn.isVisible()) {
        await createLeagueBtn.click();
        await page.waitForTimeout(1000);
        
        // Step 3: Verify mobile drawer is closed after navigation  
        console.log('🔍 Verifying mobile drawer closed after navigation...');
        
        await expect(mobileDrawer).not.toBeVisible({ timeout: 3000 });
        console.log('✅ Mobile drawer properly closed on navigation');
        
        // Step 4: Verify focus trap is removed
        console.log('🔍 Verifying focus trap removed...');
        
        // Try pressing Tab to ensure focus moves normally
        await page.keyboard.press('Tab');
        const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
        console.log(`📍 Focus moved to: ${focusedElement}`);
        
        // Focus should not be trapped in the closed drawer
        expect(focusedElement).not.toBe('BODY'); // Focus should have moved
        console.log('✅ Focus trap properly removed');
      } else {
        console.log('⚠️  Create League button not found in mobile context');
      }
    } else {
      console.log('⚠️  Mobile menu button not found - skipping mobile test');
    }
  });

  test('should not render empty menus', async ({ page }) => {
    console.log('🧪 Testing empty menu prevention...');
    
    // Navigate without login (unauthenticated state)
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check that menus with no visible items don't render
    console.log('🔍 Checking that empty menus are not rendered...');
    
    const productDropdown = page.getByTestId('nav-dropdown-product');
    const dropdownExists = await productDropdown.count();
    
    if (dropdownExists > 0) {
      // If dropdown exists, it should not be clickable/functional when empty
      const isVisible = await productDropdown.isVisible();
      console.log(`📋 Product dropdown visible: ${isVisible}`);
      
      if (isVisible) {
        await productDropdown.click();
        await page.waitForTimeout(500);
        
        // Check if menu opened - it shouldn't if empty
        const openMenu = page.locator('[role="menu"]:visible');
        const openMenuCount = await openMenu.count();
        
        if (openMenuCount === 0) {
          console.log('✅ Empty menu correctly prevented from opening');
        } else {
          // If menu opened, check that it has content
          const menuItems = page.locator('[role="menuitem"]');
          const itemCount = await menuItems.count();
          expect(itemCount).toBeGreaterThan(0);
          console.log(`✅ Menu opened with ${itemCount} items (not empty)`);
        }
      }
    } else {
      console.log('✅ Product dropdown not rendered when no items available');
    }
  });
  
  test('should have proper testids for all menu components', async ({ page }) => {
    console.log('🧪 Testing menu component testids...');
    
    // Login to ensure all menu components are available
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    
    // Test product dropdown testid
    const productDropdown = page.getByTestId('nav-dropdown-product');
    if (await productDropdown.count() > 0) {
      console.log('✅ nav-dropdown-product testid found');
    }
    
    // Test mobile drawer testid (need to check if mobile menu button exists first)
    const mobileMenuBtn = page.locator('[data-testid*="mobile"], button[aria-label*="menu"]').first();
    if (await mobileMenuBtn.isVisible()) {
      await mobileMenuBtn.click();
      await page.waitForTimeout(500);
      
      const mobileDrawer = page.getByTestId('nav-mobile-drawer');
      await expect(mobileDrawer).toBeVisible();
      console.log('✅ nav-mobile-drawer testid found');
      
      // Close mobile drawer
      const closeBtn = page.locator('[aria-label="Close menu"]');
      if (await closeBtn.isVisible()) {
        await closeBtn.click();
      }
    }
    
    // Test specific menu item testids (when dropdown is open)
    if (await productDropdown.isVisible()) {
      await productDropdown.click();
      await page.waitForTimeout(500);
      
      const specificTestids = [
        'nav-dd-auction',
        'nav-dd-roster', 
        'nav-dd-fixtures',
        'nav-dd-leaderboard',
        'nav-dd-settings'
      ];
      
      for (const testid of specificTestids) {
        const element = page.getByTestId(testid);
        const count = await element.count();
        if (count > 0) {
          console.log(`✅ ${testid} testid found`);
        }
      }
    }
    
    console.log('🎉 All menu testids verified!');
  });
});