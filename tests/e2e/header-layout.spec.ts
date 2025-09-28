/**
 * Header Layout Test
 * 
 * Verifies that header layout changes are working correctly
 */

import { test, expect } from '@playwright/test';
import { login } from './utils/login';

test('should have proper header layout without content overlap', async ({ page }) => {
  console.log('🧪 Testing header layout...');
  
  // Login and navigate to dashboard
  await login(page, 'commish@example.com', { mode: 'test' });
  await page.goto('/app');
  await page.waitForLoadState('networkidle');
  
  // Take screenshot to verify layout
  await page.screenshot({ path: 'header-layout-test.png', fullPage: true });
  
  // Check that header has correct positioning
  const header = page.locator('header');
  await expect(header).toBeVisible();
  
  const headerStyles = await header.evaluate(el => {
    const styles = window.getComputedStyle(el);
    return {
      position: styles.position,
      top: styles.top,
      zIndex: styles.zIndex
    };
  });
  
  console.log('📏 Header styles:', headerStyles);
  expect(headerStyles.position).toBe('sticky');
  expect(headerStyles.top).toBe('0px');
  expect(parseInt(headerStyles.zIndex)).toBe(50);
  
  // Check that main content has proper padding
  const main = page.locator('main');
  if (await main.count() > 0) {
    const mainStyles = await main.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        paddingTop: styles.paddingTop
      };
    });
    
    console.log('📏 Main content padding:', mainStyles);
    expect(mainStyles.paddingTop).toBe('64px'); // --header-h: 4rem = 64px
  }
  
  // Check CSS custom property is defined
  const headerHeight = await page.evaluate(() => {
    return getComputedStyle(document.documentElement).getPropertyValue('--header-h');
  });
  
  console.log('📏 CSS custom property --header-h:', headerHeight);
  expect(headerHeight.trim()).toBe('4rem');
  
  // Verify scroll padding is set
  const scrollPadding = await page.evaluate(() => {
    return getComputedStyle(document.documentElement).scrollPaddingTop;
  });
  
  console.log('📏 Scroll padding top:', scrollPadding);
  expect(scrollPadding).toBe('64px');
  
  console.log('✅ Header layout verification complete');
});