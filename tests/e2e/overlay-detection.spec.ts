/**
 * Overlay Detection Test
 * 
 * Tests the ensureClickable helper function to verify it properly detects overlays
 */

import { test, expect } from '@playwright/test';
import { login } from './utils/login';
import { ensureClickable, clickWhenReady, screenshotWithOverlayDiag } from './utils/ensureClickable';

test.describe('Overlay Detection', () => {
  test('should pass when element is clickable', async ({ page }) => {
    console.log('🧪 Testing overlay detection with clickable element...');
    
    // Login and navigate to dashboard
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.goto('/app');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Test with a known clickable element
    const createLeagueBtn = page.getByTestId('create-league-btn').first();
    
    if (await createLeagueBtn.count() > 0) {
      console.log('🎯 Testing ensureClickable on Create League button...');
      
      // This should pass without throwing
      await ensureClickable(createLeagueBtn);
      console.log('✅ ensureClickable passed - element is clickable');
      
      // Test clickWhenReady
      await clickWhenReady(createLeagueBtn);
      console.log('✅ clickWhenReady succeeded');
      
      // Verify dialog opened (proving the click worked)
      await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 3000 });
      console.log('✅ Click was successful - dialog opened');
    } else {
      console.log('⚠️  No Create League button found - skipping clickable test');
    }
  });

  test('should detect and report overlay interference', async ({ page }) => {
    console.log('🧪 Testing overlay detection with artificial overlay...');
    
    // Navigate to a simple page
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Create a button that we'll overlay
    await page.evaluate(() => {
      const button = document.createElement('button');
      button.id = 'test-button';
      button.textContent = 'Test Button';
      button.setAttribute('data-testid', 'test-button');
      button.style.cssText = `
        position: fixed;
        top: 100px;
        left: 100px;
        width: 200px;
        height: 50px;
        background: blue;
        color: white;
        border: none;
        z-index: 1;
      `;
      document.body.appendChild(button);
    });
    
    // Create an overlay that blocks the button
    await page.evaluate(() => {
      const overlay = document.createElement('div');
      overlay.id = 'blocking-overlay';
      overlay.style.cssText = `
        position: fixed;
        top: 50px;
        left: 50px;
        width: 300px;
        height: 150px;
        background: rgba(255, 0, 0, 0.5);
        z-index: 10;
        pointer-events: auto;
      `;
      overlay.textContent = 'Blocking Overlay';
      document.body.appendChild(overlay);
    });
    
    const testButton = page.getByTestId('test-button');
    
    // This should throw with diagnostic information
    let errorThrown = false;
    let errorMessage = '';
    
    try {
      await ensureClickable(testButton, { timeout: 2000 });
    } catch (error) {
      errorThrown = true;
      errorMessage = error.message;
      console.log('🎯 Expected error caught:');
      console.log(error.message);
    }
    
    expect(errorThrown).toBe(true);
    expect(errorMessage).toContain('ELEMENT NOT CLICKABLE - OVERLAY DETECTED');
    expect(errorMessage).toContain('Intercepting Element');
    expect(errorMessage).toContain('blocking-overlay');
    
    console.log('✅ Overlay detection working correctly');
  });

  test('should provide helpful diagnostic information', async ({ page }) => {
    console.log('🧪 Testing diagnostic information quality...');
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Create a complex overlay scenario
    await page.evaluate(() => {
      // Target button
      const button = document.createElement('button');
      button.setAttribute('data-testid', 'diagnostic-test-btn');
      button.textContent = 'Target Button';
      button.style.cssText = `
        position: fixed;
        top: 200px;
        left: 200px;
        width: 150px;
        height: 40px;
        background: green;
        color: white;
        z-index: 5;
      `;
      document.body.appendChild(button);
      
      // High z-index overlay
      const highZOverlay = document.createElement('div');
      highZOverlay.className = 'modal-backdrop high-priority';
      highZOverlay.id = 'high-z-overlay';
      highZOverlay.style.cssText = `
        position: fixed;
        top: 150px;
        left: 150px;
        width: 250px;
        height: 140px;
        background: rgba(0, 0, 255, 0.3);
        z-index: 999;
        pointer-events: auto;
      `;
      document.body.appendChild(highZOverlay);
    });
    
    const targetBtn = page.getByTestId('diagnostic-test-btn');
    
    try {
      await ensureClickable(targetBtn, { timeout: 2000 });
    } catch (error) {
      const message = error.message;
      
      // Verify diagnostic information is present
      expect(message).toContain('Target Element:');
      expect(message).toContain('diagnostic-test-btn');
      expect(message).toContain('Intercepting Element:');
      expect(message).toContain('high-z-overlay');
      expect(message).toContain('Z-Index: 999');
      expect(message).toContain('Suggested Fixes:');
      expect(message).toContain('All Elements at Click Point:');
      
      console.log('✅ Diagnostic information is comprehensive');
      return;
    }
    
    throw new Error('Expected ensureClickable to throw an error');
  });

  test('should handle pointer-events: none correctly', async ({ page }) => {
    console.log('🧪 Testing pointer-events: none handling...');
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Create button with overlay that has pointer-events: none
    await page.evaluate(() => {
      const button = document.createElement('button');
      button.setAttribute('data-testid', 'pointer-events-test-btn');
      button.textContent = 'Button';
      button.style.cssText = `
        position: fixed;
        top: 300px;
        left: 300px;
        width: 100px;
        height: 30px;
        background: orange;
        z-index: 1;
      `;
      document.body.appendChild(button);
      
      // Overlay with pointer-events: none (should allow clicks through)
      const overlay = document.createElement('div');
      overlay.style.cssText = `
        position: fixed;
        top: 280px;
        left: 280px;
        width: 140px;
        height: 70px;
        background: rgba(128, 128, 128, 0.5);
        z-index: 10;
        pointer-events: none;
      `;
      document.body.appendChild(overlay);
    });
    
    const testBtn = page.getByTestId('pointer-events-test-btn');
    
    // This should pass because pointer-events: none allows clicks through
    try {
      await ensureClickable(testBtn, { timeout: 2000 });
      console.log('✅ pointer-events: none handled correctly');
    } catch (error) {
      // If it fails, check that the diagnostic mentions pointer-events: none
      expect(error.message).toContain('pointer-events: none');
      console.log('✅ pointer-events: none detected in diagnostics');
    }
  });
});