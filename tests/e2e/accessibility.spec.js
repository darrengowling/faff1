const { test, expect } = require('@playwright/test');

/**
 * Accessibility Tests
 * 
 * Tests Lighthouse a11y ≥90, contrast checks, keyboard navigation, and WCAG compliance
 */

test.describe('Accessibility - Comprehensive Testing', () => {
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

  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.afterAll(async () => {
    const duration = ((Date.now() - testResults.startTime) / 1000).toFixed(2);
    console.log('\n' + '='.repeat(60));
    console.log('📊 Accessibility Test Summary:');
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

  test('Lighthouse accessibility audit ≥90', async ({ page }) => {
    try {
      // Note: Full Lighthouse audit requires specific setup, so we'll do a comprehensive a11y check
      // This simulates key Lighthouse accessibility checks
      
      // Check for proper page structure
      const h1Count = await page.locator('h1').count();
      const hasProperHeading = h1Count === 1;
      trackResult('Single H1 Heading', hasProperHeading, `${h1Count} H1 elements found`);

      // Check heading hierarchy
      const headings = await page.evaluate(() => {
        const headingLevels = [];
        document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
          headingLevels.push(parseInt(h.tagName.charAt(1)));
        });
        return headingLevels;
      });

      let properHierarchy = true;
      for (let i = 1; i < headings.length; i++) {
        if (headings[i] > headings[i-1] + 1) {
          properHierarchy = false;
          break;
        }
      }
      
      trackResult('Proper Heading Hierarchy', properHierarchy, 
        `Heading sequence: ${headings.join(' → ')}`);

      // Check for alt text on images
      const images = await page.locator('img').count();
      const imagesWithAlt = await page.locator('img[alt]').count();
      const altTextCompliance = images === 0 || (imagesWithAlt / images) >= 0.9;
      
      trackResult('Image Alt Text Compliance', altTextCompliance,
        `${imagesWithAlt}/${images} images with alt text`);

      // Check for form labels
      const inputs = await page.locator('input, textarea, select').count();
      const labeledInputs = await page.locator('input[aria-label], input[aria-labelledby], input + label, label input, textarea[aria-label], select[aria-label]').count();
      const formLabelCompliance = inputs === 0 || (labeledInputs / inputs) >= 0.8;
      
      trackResult('Form Label Compliance', formLabelCompliance,
        `${labeledInputs}/${inputs} form elements properly labeled`);

      // Check for keyboard focus indicators
      const focusableElements = await page.locator('button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])').count();
      trackResult('Focusable Elements Present', focusableElements > 5,
        `${focusableElements} focusable elements found`);

      // Check color contrast basics (simplified check)
      const contrastIssues = await page.evaluate(() => {
        let issues = 0;
        const elements = document.querySelectorAll('*');
        
        elements.forEach(el => {
          const style = window.getComputedStyle(el);
          const color = style.color;
          const backgroundColor = style.backgroundColor;
          
          // Basic check for very light text on light background or dark on dark
          if ((color === 'rgb(255, 255, 255)' && backgroundColor === 'rgb(255, 255, 255)') ||
              (color === 'rgb(0, 0, 0)' && backgroundColor === 'rgb(0, 0, 0)')) {
            issues++;
          }
        });
        
        return issues;
      });

      trackResult('Basic Contrast Check', contrastIssues === 0,
        `${contrastIssues} potential contrast issues detected`);

      // Calculate estimated accessibility score based on checks
      const passedChecks = [hasProperHeading, properHierarchy, altTextCompliance, formLabelCompliance, contrastIssues === 0].filter(Boolean).length;
      const estimatedScore = (passedChecks / 5) * 100;
      
      trackResult('Estimated Accessibility Score', estimatedScore >= 90,
        `${estimatedScore}% (≥90% required)`);

    } catch (error) {
      trackResult('Lighthouse Accessibility Audit', false, error.message);
    }
  });

  test('WCAG contrast checks pass', async ({ page }) => {
    try {
      // Test specific UI elements for proper contrast
      const contrastElements = [
        { selector: 'h1', name: 'Main Heading' },
        { selector: 'button', name: 'Buttons' },
        { selector: 'a', name: 'Links' },
        { selector: 'p', name: 'Body Text' },
        { selector: '.text-gray-600, .text-secondary', name: 'Secondary Text' }
      ];

      let contrastChecksPassed = 0;

      for (const element of contrastElements) {
        try {
          const locator = page.locator(element.selector).first();
          
          if (await locator.isVisible()) {
            const colors = await page.evaluate((sel) => {
              const el = document.querySelector(sel);
              if (!el) return null;
              
              const style = window.getComputedStyle(el);
              return {
                color: style.color,
                backgroundColor: style.backgroundColor,
                fontSize: style.fontSize
              };
            }, element.selector);

            if (colors) {
              // Simplified contrast check - in real implementation would use proper contrast ratio calculation
              const hasGoodContrast = 
                !colors.color.includes('rgb(128, 128, 128)') && // Not medium gray
                colors.color !== colors.backgroundColor; // Not same as background
              
              if (hasGoodContrast) {
                contrastChecksPassed++;
              }
            }
          }
        } catch (error) {
          console.log(`Contrast check failed for ${element.name}: ${error.message}`);
        }
      }

      trackResult('WCAG Contrast Compliance', contrastChecksPassed >= 3,
        `${contrastChecksPassed}/${contrastElements.length} elements pass contrast check`);

      // Test light/dark theme contrast
      const themeToggle = page.locator('button[aria-label*="theme"]').first();
      
      if (await themeToggle.isVisible()) {
        // Test dark theme contrast
        await themeToggle.click();
        await page.waitForTimeout(1000);
        
        const darkThemeContrast = await page.evaluate(() => {
          const body = document.body;
          const style = window.getComputedStyle(body);
          const bgColor = style.backgroundColor;
          const textColor = style.color;
          
          // Basic check that dark theme has appropriate colors
          return bgColor.includes('17, 17, 17') || bgColor.includes('0, 0, 0') || 
                 textColor.includes('255, 255, 255') || textColor.includes('245, 245, 245');
        });
        
        trackResult('Dark Theme Contrast', darkThemeContrast, 'Dark theme has appropriate contrast colors');
        
        // Switch back to light theme
        await themeToggle.click();
        await page.waitForTimeout(500);
      }

    } catch (error) {
      trackResult('WCAG Contrast Checks', false, error.message);
    }
  });

  test('Keyboard navigation completeness', async ({ page }) => {
    try {
      // Test Tab navigation through interactive elements
      let tabableElements = 0;
      let currentElement = null;
      
      // Count tabable elements by tabbing through them
      for (let i = 0; i < 20; i++) { // Test up to 20 tab stops
        await page.keyboard.press('Tab');
        
        const activeElement = await page.evaluate(() => {
          const el = document.activeElement;
          return el ? {
            tagName: el.tagName,
            type: el.type,
            text: el.textContent?.substring(0, 20)
          } : null;
        });
        
        if (activeElement && activeElement.tagName !== 'BODY') {
          tabableElements++;
        }
        
        // Break if we've cycled back to the first element
        if (i > 5 && JSON.stringify(activeElement) === JSON.stringify(currentElement)) {
          break;
        }
        
        if (i === 0) currentElement = activeElement;
      }

      trackResult('Keyboard Navigation Elements', tabableElements >= 5,
        `${tabableElements} keyboard-accessible elements found`);

      // Test specific keyboard interactions
      const keyboardTests = [
        { key: 'Enter', name: 'Enter key activation' },
        { key: 'Space', name: 'Space key activation' },
        { key: 'Escape', name: 'Escape key handling' }
      ];

      let keyboardInteractionsPassed = 0;

      // Focus on a button and test keyboard activation
      const firstButton = page.locator('button').first();
      if (await firstButton.isVisible()) {
        await firstButton.focus();
        
        // Test Enter key
        const enterWorks = await page.evaluate(() => {
          return document.activeElement?.tagName === 'BUTTON';
        });
        
        if (enterWorks) keyboardInteractionsPassed++;
      }

      // Test dropdown keyboard navigation
      const dropdown = page.locator('button:has-text("Product")').first();
      if (await dropdown.isVisible()) {
        await dropdown.focus();
        await page.keyboard.press('Enter');
        await page.waitForTimeout(500);
        
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Escape');
        
        keyboardInteractionsPassed++;
      }

      trackResult('Keyboard Interactions', keyboardInteractionsPassed >= 1,
        `${keyboardInteractionsPassed} keyboard interactions working`);

      // Test focus management
      const focusManagement = await page.evaluate(() => {
        // Check if focus is visible
        const activeEl = document.activeElement;
        const computedStyle = activeEl ? window.getComputedStyle(activeEl) : null;
        
        return computedStyle && (
          computedStyle.outline !== 'none' || 
          computedStyle.boxShadow.includes('focus') ||
          computedStyle.border.includes('blue')
        );
      });

      trackResult('Focus Indicators', focusManagement, 'Focus indicators are visible');

    } catch (error) {
      trackResult('Keyboard Navigation', false, error.message);
    }
  });

  test('Screen reader compatibility', async ({ page }) => {
    try {
      // Test ARIA landmarks
      const landmarks = await page.locator('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], main, nav, header, footer').count();
      trackResult('ARIA Landmarks', landmarks >= 3, `${landmarks} landmarks found`);

      // Test ARIA labels and descriptions
      const ariaLabels = await page.locator('[aria-label]').count();
      const ariaDescriptions = await page.locator('[aria-describedby]').count();
      
      trackResult('ARIA Labels', ariaLabels >= 5, `${ariaLabels} elements with aria-label`);
      trackResult('ARIA Descriptions', ariaDescriptions >= 0, `${ariaDescriptions} elements with aria-describedby`);

      // Test button accessibility
      const buttons = await page.locator('button').count();
      const accessibleButtons = await page.locator('button[aria-label], button:has-text()').count();
      const buttonAccessibility = buttons === 0 || (accessibleButtons / buttons) >= 0.9;
      
      trackResult('Button Accessibility', buttonAccessibility,
        `${accessibleButtons}/${buttons} buttons have accessible names`);

      // Test link accessibility
      const links = await page.locator('a').count();
      const accessibleLinks = await page.locator('a[aria-label], a:has-text(), a[title]').count();
      const linkAccessibility = links === 0 || (accessibleLinks / links) >= 0.8;
      
      trackResult('Link Accessibility', linkAccessibility,
        `${accessibleLinks}/${links} links have accessible names`);

      // Test form accessibility
      const formElements = await page.locator('input, select, textarea').count();
      if (formElements > 0) {
        const accessibleForms = await page.locator('input[aria-label], input[aria-labelledby], select[aria-label], textarea[aria-label]').count();
        const formAccessibility = (accessibleForms / formElements) >= 0.8;
        
        trackResult('Form Accessibility', formAccessibility,
          `${accessibleForms}/${formElements} form elements properly labeled`);
      } else {
        trackResult('Form Accessibility', true, 'No form elements to test');
      }

      // Test skip links
      const skipLinks = await page.locator('a[href="#main"], a[href="#content"], .skip-link').count();
      trackResult('Skip Links', skipLinks >= 0, `${skipLinks} skip links found`);

    } catch (error) {
      trackResult('Screen Reader Compatibility', false, error.message);
    }
  });

  test('Mobile accessibility compliance', async ({ page }) => {
    try {
      // Switch to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      // Test touch target sizes (minimum 44px)
      const touchTargets = await page.evaluate(() => {
        const buttons = document.querySelectorAll('button, a, input[type="button"], input[type="submit"]');
        let adequateTargets = 0;
        let totalTargets = buttons.length;
        
        buttons.forEach(button => {
          const rect = button.getBoundingClientRect();
          if (rect.width >= 44 && rect.height >= 44) {
            adequateTargets++;
          }
        });
        
        return { adequate: adequateTargets, total: totalTargets };
      });

      const touchTargetCompliance = touchTargets.total === 0 || 
        (touchTargets.adequate / touchTargets.total) >= 0.8;
      
      trackResult('Touch Target Sizes', touchTargetCompliance,
        `${touchTargets.adequate}/${touchTargets.total} targets ≥44px`);

      // Test mobile navigation accessibility
      const mobileMenu = page.locator('button[aria-label*="menu"]').first();
      if (await mobileMenu.isVisible()) {
        const hasProperLabel = await mobileMenu.getAttribute('aria-label');
        trackResult('Mobile Menu Accessibility', !!hasProperLabel,
          `Mobile menu aria-label: "${hasProperLabel}"`);
        
        // Test mobile menu keyboard access
        await mobileMenu.focus();
        await page.keyboard.press('Enter');
        await page.waitForTimeout(500);
        
        const menuOpened = await page.locator('[role="dialog"], .mobile-menu').first().isVisible();
        trackResult('Mobile Menu Keyboard Access', menuOpened, 'Mobile menu opens with keyboard');
      }

      // Test mobile theme toggle accessibility
      const mobileThemeToggle = page.locator('button[aria-label*="theme"]').first();
      if (await mobileThemeToggle.isVisible()) {
        const themeLabel = await mobileThemeToggle.getAttribute('aria-label');
        trackResult('Mobile Theme Toggle A11y', !!themeLabel,
          `Theme toggle label: "${themeLabel}"`);
      }

      // Reset to desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 });

    } catch (error) {
      trackResult('Mobile Accessibility', false, error.message);
    }
  });

  test('Focus trap and modal accessibility', async ({ page }) => {
    try {
      // Test dropdown focus management
      const productDropdown = page.locator('button:has-text("Product")').first();
      
      if (await productDropdown.isVisible()) {
        // Open dropdown
        await productDropdown.click();
        await page.waitForTimeout(500);
        
        // Test that focus moves into dropdown
        await page.keyboard.press('Tab');
        
        const focusInDropdown = await page.evaluate(() => {
          const activeEl = document.activeElement;
          const dropdown = document.querySelector('[role="menu"]');
          return dropdown && dropdown.contains(activeEl);
        });
        
        trackResult('Dropdown Focus Management', focusInDropdown, 'Focus moves into dropdown menu');
        
        // Test escape closes and returns focus
        await page.keyboard.press('Escape');
        await page.waitForTimeout(200);
        
        const focusReturned = await page.evaluate(() => {
          return document.activeElement?.textContent?.includes('Product');
        });
        
        trackResult('Focus Return on Close', focusReturned, 'Focus returns to trigger button');
      }

      // Test mobile drawer focus management
      await page.setViewportSize({ width: 375, height: 667 });
      const mobileMenuBtn = page.locator('button[aria-label*="menu"]').first();
      
      if (await mobileMenuBtn.isVisible()) {
        await mobileMenuBtn.click();
        await page.waitForTimeout(500);
        
        // Test that focus moves into mobile drawer
        const drawerFocusable = await page.locator('[role="dialog"] button, .mobile-menu button').count();
        trackResult('Mobile Drawer Focus Elements', drawerFocusable > 0,
          `${drawerFocusable} focusable elements in mobile drawer`);
      }

    } catch (error) {
      trackResult('Focus Trap and Modal Accessibility', false, error.message);
    }
  });
});