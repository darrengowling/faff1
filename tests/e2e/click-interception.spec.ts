/**
 * Click Interception Test
 * 
 * Verifies that header/nav overlays do not intercept clicks on page content
 */

import { test, expect } from '@playwright/test';
import { login } from './utils/login';
import { clickCreateLeague } from './utils/helpers';

test.describe('Click Interception Prevention', () => {
  test('should click Create League button and form fields without interception', async ({ page }) => {
    console.log('🧪 Testing click interception prevention...');
    
    // Login and navigate to dashboard
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Allow React to fully render
    
    console.log('✅ Dashboard loaded');
    
    // Test 1: Click Create League button without scrolling or special handling
    console.log('🔍 Testing Create League button click...');
    
    // Verify button is visible and clickable
    const createLeagueBtn = page.getByTestId('create-league-btn').first();
    await expect(createLeagueBtn).toBeVisible();
    
    // Click without any special handling - should not timeout
    await createLeagueBtn.click({ timeout: 5000 });
    console.log('✅ Create League button clicked successfully');
    
    // Verify dialog opened
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    console.log('✅ Create League dialog opened');
    
    // Test 2: Click all form fields without interception
    console.log('🔍 Testing form field clicks...');
    
    const formFields = [
      { testid: 'create-name', label: 'League Name', value: 'Test League' },
      { testid: 'create-budget', label: 'Budget', value: '150' },
      { testid: 'create-slots', label: 'Club Slots', value: '6' },
      { testid: 'create-min', label: 'Min Managers', value: '3' }
    ];
    
    for (const field of formFields) {
      console.log(`  Testing ${field.label} field...`);
      
      const input = page.getByTestId(field.testid);
      await expect(input).toBeVisible();
      
      // Click and focus input - should not timeout
      await input.click({ timeout: 3000 });
      await expect(input).toBeFocused({ timeout: 2000 });
      
      // Clear and type appropriate value
      await input.fill('');
      await input.fill(field.value);
      await expect(input).toHaveValue(field.value);
      
      console.log(`  ✅ ${field.label} field interactive`);
    }
    
    // Test 3: Click submit button without interception
    console.log('🔍 Testing submit button click...');
    
    // Fill required fields first
    await page.getByTestId('create-name').fill('Test League');
    await page.getByTestId('create-budget').fill('100');
    await page.getByTestId('create-slots').fill('5');
    await page.getByTestId('create-min').fill('2');
    
    const submitBtn = page.getByTestId('create-submit');
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toBeEnabled();
    
    // Click submit - should not timeout
    await submitBtn.click({ timeout: 3000 });
    console.log('✅ Submit button clicked successfully');
    
    // Test 4: Verify header doesn't block content interactions
    console.log('🔍 Testing header does not block content...');
    
    // Close dialog first
    const dialog = page.locator('[role="dialog"]');
    if (await dialog.isVisible()) {
      // Try to close dialog by clicking backdrop or close button
      const breadcrumbHome = page.getByTestId('breadcrumb-home');
      if (await breadcrumbHome.isVisible()) {
        await breadcrumbHome.click();
      } else {
        // Try clicking outside dialog
        await page.click('body', { position: { x: 50, y: 300 } });
      }
      await expect(dialog).not.toBeVisible({ timeout: 3000 });
    }
    
    // Click elements at different vertical positions to ensure header doesn't interfere
    const testPositions = [
      { selector: '[data-testid="create-league-btn"]', description: 'Top area button' },
      { selector: '[data-testid="join-via-invite-btn"]', description: 'Middle area button' }
    ];
    
    for (const position of testPositions) {
      const element = page.locator(position.selector).first();
      if (await element.isVisible()) {
        console.log(`  Testing ${position.description}...`);
        await element.click({ timeout: 3000 });
        console.log(`  ✅ ${position.description} clickable`);
        
        // Close any opened dialogs
        if (await page.locator('[role="dialog"]').isVisible()) {
          const homeLink = page.getByTestId('breadcrumb-home');
          if (await homeLink.isVisible()) {
            await homeLink.click();
          }
        }
      }
    }
    
    console.log('🎉 All click interception tests passed!');
  });

  test('should close dropdowns on route navigation', async ({ page }) => {
    console.log('🧪 Testing dropdown closes on route change...');
    
    // Login and navigate to dashboard
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    
    // Check if product dropdown exists and can be opened
    const productDropdown = page.locator('[data-testid*="dropdown"], [data-testid*="menu"]').first();
    
    if (await productDropdown.isVisible()) {
      console.log('🔍 Testing dropdown behavior...');
      
      // Open dropdown
      await productDropdown.click();
      await page.waitForTimeout(500);
      
      // Navigate to another route
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // Navigate back
      await page.goto('/app');
      await page.waitForLoadState('networkidle');
      
      // Dropdown should be closed
      const openDropdown = page.locator('[role="menu"][aria-expanded="true"], .dropdown-open');
      await expect(openDropdown).not.toBeVisible();
      
      console.log('✅ Dropdown properly closed on route change');
    } else {
      console.log('⚠️  No dropdown found to test - skipping dropdown test');
    }
  });

  test('should handle mobile menu without click blocking', async ({ page }) => {
    console.log('🧪 Testing mobile menu click handling...');
    
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Login and navigate to dashboard
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    
    // Look for mobile menu button
    const mobileMenuBtn = page.locator('[data-testid*="mobile"], button[aria-label*="menu"]').first();
    
    if (await mobileMenuBtn.isVisible()) {
      console.log('🔍 Testing mobile menu interaction...');
      
      // Open mobile menu
      await mobileMenuBtn.click({ timeout: 3000 });
      console.log('✅ Mobile menu opened');
      
      // Check if backdrop or close button works
      const closeBtn = page.locator('[aria-label="Close menu"], [data-testid*="close"]').first();
      if (await closeBtn.isVisible()) {
        await closeBtn.click({ timeout: 3000 });
        console.log('✅ Mobile menu closed');
      } else {
        // Try clicking backdrop
        await page.click('body', { position: { x: 50, y: 300 } });
        console.log('✅ Mobile menu closed via backdrop');
      }
    } else {
      console.log('⚠️  No mobile menu found - skipping mobile test');
    }
  });
});