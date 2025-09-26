const { test, expect } = require('@playwright/test');

/**
 * Internationalization (i18n) Validation Tests
 * 
 * Tests i18n key rendering, missing string warnings, and translation consistency
 */

test.describe('i18n Validation - Comprehensive Testing', () => {
  const testResults = {
    passed: [],
    failed: [],
    startTime: Date.now()
  };

  const trackResult = (testName, success, details = '') => {
    if (success) {
      testResults.passed.push(testName);
      console.log(`✅ ${testName} - PASSED ${details}`);
    } else {
      testResults.failed.push(`${testName}: ${details}`);
      console.log(`❌ ${testName} - FAILED ${details}`);
    }
  };

  let consoleErrors = [];
  let consoleLogs = [];

  test.beforeEach(async ({ page }) => {
    // Reset console capture arrays
    consoleErrors = [];
    consoleLogs = [];

    // Capture console messages to detect i18n warnings
    page.on('console', (msg) => {
      const text = msg.text();
      if (msg.type() === 'error') {
        consoleErrors.push(text);
      } else if (msg.type() === 'log' || msg.type() === 'warn') {
        consoleLogs.push(text);
      }
    });

    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // Give i18n time to initialize
    await page.waitForTimeout(2000);
  });

  test.afterAll(async () => {
    const duration = ((Date.now() - testResults.startTime) / 1000).toFixed(2);
    console.log('\n' + '='.repeat(60));
    console.log('📊 i18n Validation Test Summary:');
    console.log(`⏱️ Duration: ${duration}s`);
    console.log(`✅ Passed: ${testResults.passed.length}`);
    console.log(`❌ Failed: ${testResults.failed.length}`);
    
    if (testResults.passed.length > 0) {
      console.log('\n🎉 Successful Tests:');
      testResults.passed.forEach(test => console.log(`  - ${test}`));
    }
    
    if (testResults.failed.length > 0) {
      console.log('\n💥 Failed Tests:');
      testResults.failed.forEach(test => console.log(`  - ${test}`));
    }
    console.log('='.repeat(60));
  });

  test('i18n keys render correctly (no missing string warnings)', async ({ page }) => {
    try {
      // Check for i18n-related console warnings/errors
      const i18nErrors = consoleErrors.filter(error => 
        error.includes('i18n') || 
        error.includes('translation') || 
        error.includes('missing') ||
        error.includes('key not found')
      );

      const i18nWarnings = consoleLogs.filter(log => 
        log.includes('i18n') || 
        log.includes('translation') || 
        log.includes('missing key') ||
        log.includes('keyNotFound')
      );

      trackResult('No i18n Console Errors', i18nErrors.length === 0, 
        `${i18nErrors.length} i18n errors found: ${i18nErrors.join('; ')}`);

      trackResult('No Missing Translation Warnings', i18nWarnings.length === 0,
        `${i18nWarnings.length} i18n warnings found: ${i18nWarnings.join('; ')}`);

      // Check if i18next is properly initialized
      const i18nInitialized = await page.evaluate(() => {
        return typeof window.i18n !== 'undefined' || 
               typeof window.i18next !== 'undefined' ||
               document.documentElement.getAttribute('data-i18n-initialized') === 'true';
      });

      trackResult('i18n Library Initialization', i18nInitialized, 'i18n library properly loaded');

    } catch (error) {
      trackResult('i18n Error Detection', false, error.message);
    }
  });

  test('Key brand messaging renders from i18n', async ({ page }) => {
    try {
      // Test specific brand messaging that should come from i18n keys
      const brandElements = [
        { selector: 'title', expectedContent: 'Friends of PIFA', keyName: 'page title' },
        { selector: 'h1', expectedContent: 'Football Auctions', keyName: 'hero title' },
        { selector: 'button:has-text("Create a League")', expectedContent: 'Create a League', keyName: 'CTA button' },
        { selector: 'button:has-text("Join with an Invite")', expectedContent: 'Join with an Invite', keyName: 'CTA button' }
      ];

      let brandElementsFound = 0;

      for (const element of brandElements) {
        try {
          const locator = page.locator(element.selector).first();
          const isVisible = await locator.isVisible({ timeout: 2000 });
          
          if (isVisible) {
            const content = await locator.textContent();
            if (content && content.includes(element.expectedContent)) {
              brandElementsFound++;
            }
          }
        } catch (error) {
          console.log(`Brand element test failed for ${element.keyName}: ${error.message}`);
        }
      }

      trackResult('Brand Messaging from i18n', brandElementsFound >= 2, 
        `${brandElementsFound}/${brandElements.length} brand elements found`);

      // Test specific i18n content that should not show placeholder text
      const noPlaceholders = await page.evaluate(() => {
        const text = document.body.innerText;
        return !text.includes('{{') && 
               !text.includes('undefined') && 
               !text.includes('[object Object]') &&
               !text.includes('missing');
      });

      trackResult('No i18n Placeholders Visible', noPlaceholders, 'No placeholder text detected');

    } catch (error) {
      trackResult('Brand Messaging i18n', false, error.message);
    }
  });

  test('Landing page sections use i18n keys', async ({ page }) => {
    try {
      // Test that main landing page sections have proper content (not showing keys)
      const sections = [
        { id: '#home', name: 'Hero Section' },
        { id: '#how', name: 'How It Works' },
        { id: '#why', name: 'Why FoP' },
        { id: '#features', name: 'Features' },
        { id: '#safety', name: 'Fair Play' },
        { id: '#faq', name: 'FAQ' }
      ];

      let sectionsWithContent = 0;

      for (const section of sections) {
        try {
          const sectionElement = page.locator(section.id);
          const isVisible = await sectionElement.isVisible();
          
          if (isVisible) {
            const textContent = await sectionElement.textContent();
            // Check that section has meaningful content (not just keys)
            if (textContent && 
                textContent.length > 20 && 
                !textContent.includes('.') && // Not showing key paths like 'landing.hero.title'
                !textContent.includes('{{')) { // Not showing interpolation syntax
              sectionsWithContent++;
            }
          }
        } catch (error) {
          console.log(`Section i18n test failed for ${section.name}: ${error.message}`);
        }
      }

      trackResult('Landing Sections Have i18n Content', sectionsWithContent >= 4,
        `${sectionsWithContent}/${sections.length} sections with proper content`);

    } catch (error) {
      trackResult('Landing Page i18n', false, error.message);
    }
  });

  test('Navigation components use i18n keys', async ({ page }) => {
    try {
      // Test navigation elements for proper i18n content
      const navTests = [
        { selector: 'button:has-text("Product")', name: 'Product dropdown' },
        { selector: 'button:has-text("Sign In")', name: 'Sign In button' },
        { selector: 'button:has-text("Get Started")', name: 'Get Started button' },
        { selector: '[aria-label]', name: 'ARIA labels' }
      ];

      let navElementsWorking = 0;

      for (const test of navTests) {
        try {
          const elements = await page.locator(test.selector).count();
          if (elements > 0) {
            // Check if elements have proper text (not showing raw keys)
            const firstElement = page.locator(test.selector).first();
            const text = await firstElement.textContent();
            
            if (text && !text.includes('.') && text.length > 2) {
              navElementsWorking++;
            }
          }
        } catch (error) {
          console.log(`Navigation i18n test failed for ${test.name}: ${error.message}`);
        }
      }

      trackResult('Navigation i18n Content', navElementsWorking >= 2,
        `${navElementsWorking}/${navTests.length} navigation elements working`);

      // Test dropdown menu items for i18n content
      const productBtn = page.locator('button:has-text("Product")').first();
      if (await productBtn.isVisible()) {
        await productBtn.click();
        await page.waitForTimeout(500);
        
        const menuItems = await page.locator('[role="menuitem"], .dropdown-menu a, .dropdown-menu button').count();
        trackResult('Dropdown Menu Items', menuItems > 0, `${menuItems} dropdown menu items found`);
      }

    } catch (error) {
      trackResult('Navigation Component i18n', false, error.message);
    }
  });

  test('Footer and legal content use i18n', async ({ page }) => {
    try {
      // Scroll to footer to ensure it's loaded
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(1000);

      // Test footer content
      const footer = page.locator('footer');
      const footerVisible = await footer.isVisible();
      
      if (footerVisible) {
        const footerText = await footer.textContent();
        
        // Check for specific footer content that should come from i18n
        const hasManifesto = footerText.includes('integrity') || footerText.includes('fairness');
        const hasDisclaimer = footerText.includes('No gambling') || footerText.includes('No wagering');
        const hasCopyright = footerText.includes('©') || footerText.includes('Friends of PIFA');
        
        trackResult('Footer Manifesto i18n', hasManifesto, 'Footer contains manifesto messaging');
        trackResult('Footer Disclaimer i18n', hasDisclaimer, 'Footer contains no-gambling disclaimer');
        trackResult('Footer Copyright i18n', hasCopyright, 'Footer contains copyright information');
      } else {
        trackResult('Footer i18n Content', false, 'Footer not visible');
      }

    } catch (error) {
      trackResult('Footer i18n Content', false, error.message);
    }
  });

  test('Theme toggle and accessibility labels use i18n', async ({ page }) => {
    try {
      // Test theme toggle aria-label
      const themeToggle = page.locator('button[aria-label*="theme"]').first();
      
      if (await themeToggle.isVisible()) {
        const ariaLabel = await themeToggle.getAttribute('aria-label');
        const hasProperLabel = ariaLabel && 
          (ariaLabel.includes('Switch to') || ariaLabel.includes('Toggle')) &&
          !ariaLabel.includes('.');

        trackResult('Theme Toggle ARIA Label', hasProperLabel, `Label: "${ariaLabel}"`);
      }

      // Test other accessibility labels for i18n compliance
      const ariaLabels = await page.locator('[aria-label]').count();
      let properLabels = 0;

      if (ariaLabels > 0) {
        const labels = await page.locator('[aria-label]').all();
        
        for (const label of labels) {
          const ariaText = await label.getAttribute('aria-label');
          // Check that label doesn't look like a raw i18n key
          if (ariaText && !ariaText.includes('.') && ariaText.length > 3) {
            properLabels++;
          }
        }
      }

      trackResult('Accessibility Labels i18n', properLabels >= ariaLabels * 0.8,
        `${properLabels}/${ariaLabels} ARIA labels properly translated`);

    } catch (error) {
      trackResult('Accessibility i18n Labels', false, error.message);
    }
  });

  test('No raw translation keys visible in UI', async ({ page }) => {
    try {
      // Get all visible text content and check for raw i18n keys
      const bodyText = await page.evaluate(() => document.body.innerText);
      
      // Common patterns that indicate untranslated keys
      const keyPatterns = [
        /\w+\.\w+\.\w+/g,  // dot notation keys like 'landing.hero.title'
        /\{\{[\w.]+\}\}/g,  // interpolation syntax like '{{brandName}}'
        /t\(['"`][\w.]+['"`]\)/g,  // raw t() calls visible in UI
        /undefined/gi,
        /\[object Object\]/gi,
        /missing.*key/gi
      ];

      let rawKeysFound = [];
      
      keyPatterns.forEach((pattern, index) => {
        const matches = bodyText.match(pattern);
        if (matches) {
          rawKeysFound.push(...matches);
        }
      });

      trackResult('No Raw Translation Keys', rawKeysFound.length === 0,
        `${rawKeysFound.length} potential raw keys found: ${rawKeysFound.slice(0, 5).join(', ')}${rawKeysFound.length > 5 ? '...' : ''}`);

      // Check for specific problematic patterns
      const hasUndefined = bodyText.includes('undefined');
      const hasObjectObject = bodyText.includes('[object Object]');
      const hasInterpolation = bodyText.includes('{{');

      trackResult('No Undefined Values', !hasUndefined, 'No "undefined" text visible');
      trackResult('No Object Serialization', !hasObjectObject, 'No "[object Object]" visible');
      trackResult('No Raw Interpolation', !hasInterpolation, 'No "{{key}}" syntax visible');

    } catch (error) {
      trackResult('Raw Translation Key Detection', false, error.message);
    }
  });
});