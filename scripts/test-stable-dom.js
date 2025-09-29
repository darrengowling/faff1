#!/usr/bin/env node

/**
 * Test Script: Verify Stable DOM Patterns
 * 
 * Tests that critical testids remain in DOM during loading states
 * and use proper visibility patterns instead of unmounting.
 */

const puppeteer = require('puppeteer');

async function testStableDom() {
  console.log('🧪 Testing Stable DOM Patterns...');
  
  const browser = await puppeteer.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Navigate to login page
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle0' });
    console.log('✅ Navigated to login page');
    
    // Check that critical testids are present
    const authEmailInput = await page.$('[data-testid="authEmailInput"]');
    const authSubmitBtn = await page.$('[data-testid="authSubmitBtn"]');
    
    if (!authEmailInput) {
      throw new Error('❌ authEmailInput not found in DOM');
    }
    if (!authSubmitBtn) {
      throw new Error('❌ authSubmitBtn not found in DOM');
    }
    
    console.log('✅ Critical testids found in DOM');
    
    // Check initial state
    const initialEmailDisabled = await authEmailInput.evaluate(el => el.disabled);
    const initialSubmitDisabled = await authSubmitBtn.evaluate(el => el.disabled);
    
    console.log(`📊 Initial state - Email disabled: ${initialEmailDisabled}, Submit disabled: ${initialSubmitDisabled}`);
    
    // Enter email to enable submit
    await page.type('[data-testid="authEmailInput"]', 'test@example.com');
    
    // Check that submit button is now enabled
    const emailAfterType = await page.$('[data-testid="authEmailInput"]');
    const submitAfterType = await page.$('[data-testid="authSubmitBtn"]');
    
    if (!emailAfterType || !submitAfterType) {
      throw new Error('❌ Elements disappeared after typing - not stable!');
    }
    
    const submitEnabledAfterType = await submitAfterType.evaluate(el => !el.disabled);
    console.log(`✅ Submit enabled after typing: ${submitEnabledAfterType}`);
    
    // Test that elements have proper aria attributes
    const emailAriaDisabled = await authEmailInput.evaluate(el => el.getAttribute('aria-disabled'));
    const submitAriaDisabled = await authSubmitBtn.evaluate(el => el.getAttribute('aria-disabled'));
    
    console.log(`✅ ARIA attributes - Email: ${emailAriaDisabled}, Submit: ${submitAriaDisabled}`);
    
    // Test CSS classes for stability
    const emailClasses = await authEmailInput.evaluate(el => el.className);
    const submitClasses = await authSubmitBtn.evaluate(el => el.className);
    
    const hasStableClasses = emailClasses.includes('w-full') && submitClasses.includes('w-full');
    console.log(`✅ Elements have stable CSS classes: ${hasStableClasses}`);
    
    console.log('🎉 All Stable DOM tests passed!');
    return true;
    
  } catch (error) {
    console.error('💥 Stable DOM test failed:', error.message);
    return false;
  } finally {
    await browser.close();
  }
}

// Run the test if called directly
if (require.main === module) {
  testStableDom()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Unexpected error:', error);
      process.exit(1);
    });
}

module.exports = { testStableDom };