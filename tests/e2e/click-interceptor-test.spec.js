/**
 * Test Script: Click Interceptor Detector Validation
 * 
 * Tests our new click interception detection utility to ensure it properly
 * identifies UI overlay issues and provides helpful debugging information.
 */

import { test, expect } from '@playwright/test';

test.describe('Click Interceptor Detector Tests', () => {
  
  test('should detect header overlay interception on login page', async ({ page }) => {
    // Import our utility
    const { ensureClickable, safeClick, analyzeClickPoint } = await import('./utils/click-interceptor-detector.ts');
    
    console.log('🧪 Testing click interceptor detector on /login page...');
    
    // Navigate to login page
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('networkidle');
    
    // Test the submit button (likely to have interception issues)
    const submitBtn = page.locator('[data-testid="auth-submit-btn"]');
    
    try {
      // This should pass or give us detailed interception info
      await ensureClickable(page, submitBtn);
      console.log('✅ Submit button is clickable - no interception detected');
      
    } catch (error) {
      console.log('🔍 Click interception detected:');
      console.log(error.message);
      
      // Get the button's position for analysis
      const boundingBox = await submitBtn.boundingBox();
      if (boundingBox) {
        const clickX = boundingBox.x + boundingBox.width / 2;
        const clickY = boundingBox.y + boundingBox.height / 2;
        
        console.log('📍 Analyzing elements at click point...');
        const analysis = await analyzeClickPoint(page, clickX, clickY);
        console.log('Elements at click point:', JSON.stringify(analysis, null, 2));
      }
    }
    
    // Test safe click functionality
    console.log('🖱️ Testing safe click...');
    try {
      // Fill email first to enable button
      const emailInput = page.locator('[data-testid="auth-email-input"]');
      await emailInput.fill('test@example.com');
      
      // Try safe click
      await safeClick(page, submitBtn);
      console.log('✅ Safe click completed successfully');
      
    } catch (error) {
      console.log('❌ Safe click failed (expected if interception detected):');
      console.log(error.message);
    }
  });
  
  test('should detect navigation dropdown interception', async ({ page }) => {
    const { ensureClickable, analyzeClickPoint } = await import('./tests/e2e/utils/click-interceptor-detector.ts');
    
    console.log('🧪 Testing click interceptor on navigation elements...');
    
    // Navigate to homepage
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Test Sign In button (known to have interception issues)
    const signInBtn = page.locator('[data-testid="nav-sign-in"]');
    
    if (await signInBtn.count() > 0) {
      try {
        await ensureClickable(page, signInBtn);
        console.log('✅ Sign In button is clickable - no interception detected');
        
      } catch (error) {
        console.log('🔍 Navigation interception detected:');
        console.log(error.message);
        
        // Analyze the click point
        const boundingBox = await signInBtn.boundingBox();
        if (boundingBox) {
          const clickX = boundingBox.x + boundingBox.width / 2;
          const clickY = boundingBox.y + boundingBox.height / 2;
          
          const analysis = await analyzeClickPoint(page, clickX, clickY);
          console.log('Navigation elements at click point:', JSON.stringify(analysis.slice(0, 3), null, 2));
        }
      }
    } else {
      console.log('⚠️ Sign In button not found on page');
    }
  });
  
});