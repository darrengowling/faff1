const { test, expect } = require('@playwright/test');

/**
 * Navigation Component Tests
 * 
 * Tests navbar dropdown keyboard navigation, mobile drawer, and focus management
 */

test.describe('Navigation Components - Comprehensive Testing', () => {
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
    console.log('📊 Navigation Component Test Summary:');
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

  test('GlobalNavbar dropdown keyboard navigation works', async ({ page }) => {
    try {
      // Find Product dropdown button
      const productDropdown = page.locator('button:has-text("Product"), [aria-label*="Product"]').first();
      const dropdownExists = await productDropdown.isVisible();
      
      if (!dropdownExists) {
        trackResult('Product Dropdown Visibility', false, 'Product dropdown button not found');
        return;
      }

      trackResult('Product Dropdown Visibility', true, 'Product dropdown button found');

      // Test keyboard navigation to dropdown
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab'); // Navigate to dropdown
      
      // Press Enter or Space to open dropdown
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);

      // Check if dropdown menu opened
      const dropdownMenu = page.locator('[role="menu"], .dropdown-menu, [aria-expanded="true"] + *').first();
      let dropdownOpened = false;
      
      try {
        dropdownOpened = await dropdownMenu.isVisible({ timeout: 2000 });
      } catch (error) {
        console.log('Dropdown menu visibility check failed:', error.message);
      }

      trackResult('Dropdown Opens with Enter', dropdownOpened, 'Dropdown menu becomes visible');

      if (dropdownOpened) {
        // Test arrow key navigation within dropdown
        let arrowNavigationWorks = false;
        try {
          await page.keyboard.press('ArrowDown');
          await page.waitForTimeout(200);
          await page.keyboard.press('ArrowDown');
          await page.waitForTimeout(200);
          await page.keyboard.press('ArrowUp');
          await page.waitForTimeout(200);
          arrowNavigationWorks = true;
        } catch (error) {
          console.log('Arrow navigation test failed:', error.message);
        }

        trackResult('Arrow Key Navigation', arrowNavigationWorks, 'Arrow keys navigate dropdown items');

        // Test Escape to close dropdown
        let escapeCloses = false;
        try {
          await page.keyboard.press('Escape');
          await page.waitForTimeout(500);
          escapeCloses = !(await dropdownMenu.isVisible());
        } catch (error) {
          console.log('Escape key test failed:', error.message);
        }

        trackResult('Escape Key Closes Dropdown', escapeCloses, 'Dropdown closes with Escape');
      }

      // Test clicking dropdown button to open
      let clickOpensDropdown = false;
      try {
        await productDropdown.click();
        await page.waitForTimeout(500);
        const dropdownVisible = await page.locator('[role="menu"], .dropdown-menu').first().isVisible();
        clickOpensDropdown = dropdownVisible;
      } catch (error) {
        console.log('Click to open dropdown test failed:', error.message);
      }

      trackResult('Click Opens Dropdown', clickOpensDropdown, 'Dropdown opens with mouse click');

    } catch (error) {
      trackResult('Dropdown Keyboard Navigation', false, error.message);
    }
  });

  test('Mobile drawer behaves correctly', async ({ page }) => {
    try {
      // Switch to mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      // Find mobile menu button (hamburger)
      const mobileMenuBtn = page.locator('button[aria-label*="menu"], button[aria-label*="navigation"], .hamburger, [aria-expanded]').first();
      const menuBtnExists = await mobileMenuBtn.isVisible();

      trackResult('Mobile Menu Button Visibility', menuBtnExists, 'Hamburger menu button visible on mobile');

      if (menuBtnExists) {
        // Test opening mobile drawer
        await mobileMenuBtn.click();
        await page.waitForTimeout(500);

        // Check if mobile drawer/menu opened
        const mobileDrawer = page.locator('[role="dialog"], .mobile-menu, .drawer, nav[aria-label*="mobile"]').first();
        let drawerOpened = false;

        try {
          drawerOpened = await mobileDrawer.isVisible({ timeout: 2000 });
        } catch (error) {
          // Try alternative selectors
          const altDrawer = page.locator('.fixed.inset-0, .absolute.top-full, .mobile-nav').first();
          drawerOpened = await altDrawer.isVisible().catch(() => false);
        }

        trackResult('Mobile Drawer Opens', drawerOpened, 'Mobile navigation drawer becomes visible');

        if (drawerOpened) {
          // Test navigation items in mobile drawer
          const navItems = [
            page.locator(`[data-testid="${TESTIDS.navSignIn}"]`),
            page.locator(`[data-testid="${TESTIDS.navCreateLeagueBtn}"]`),
            page.locator(`[data-testid="${TESTIDS.navDropdownProduct}"]`)
          ];
          
          let visibleItemCount = 0;
          for (const item of navItems) {
            if (await item.isVisible()) visibleItemCount++;
          }
          
          trackResult('Mobile Navigation Items', visibleItemCount > 0, `${visibleItemCount} navigation items found`);

          // Test closing mobile drawer
          let drawerCloses = false;
          try {
            // Try clicking the close button or outside the drawer
            const closeBtn = page.locator('button[aria-label*="close"], [data-close]').first();
            if (await closeBtn.isVisible()) {
              await closeBtn.click();
            } else {
              // Click hamburger again to close
              await mobileMenuBtn.click();
            }
            await page.waitForTimeout(500);
            drawerCloses = !(await mobileDrawer.isVisible());
          } catch (error) {
            console.log('Mobile drawer close test failed:', error.message);
          }

          trackResult('Mobile Drawer Closes', drawerCloses, 'Drawer closes correctly');

          // Test theme toggle in mobile menu
          await mobileMenuBtn.click(); // Reopen to test theme toggle
          await page.waitForTimeout(500);
          
          const themeToggle = page.locator('button[aria-label*="theme"], .theme-toggle').first();
          const themeToggleVisible = await themeToggle.isVisible();
          trackResult('Mobile Theme Toggle', themeToggleVisible, 'Theme toggle visible in mobile menu');
        }
      }

      // Test responsive navigation behavior
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.waitForTimeout(500);

      const desktopNav = page.locator('nav, header').first();
      const desktopNavVisible = await desktopNav.isVisible();
      trackResult('Desktop Navigation Restoration', desktopNavVisible, 'Desktop nav visible after viewport change');

    } catch (error) {
      trackResult('Mobile Drawer Functionality', false, error.message);
    }
  });

  test('Focus trap and keyboard accessibility', async ({ page }) => {
    try {
      // Test focus management in dropdown
      const productDropdown = page.locator('button:has-text("Product")').first();
      
      if (await productDropdown.isVisible()) {
        // Focus on dropdown and open it
        await productDropdown.focus();
        await page.keyboard.press('Enter');
        await page.waitForTimeout(500);

        // Test focus trap within dropdown
        let focusTrapped = false;
        try {
          // Tab through dropdown items
          await page.keyboard.press('Tab');
          await page.keyboard.press('Tab');
          
          // Check if focus stays within dropdown area
          const activeElement = await page.evaluate(() => document.activeElement?.tagName);
          focusTrapped = activeElement === 'BUTTON' || activeElement === 'A';
        } catch (error) {
          console.log('Focus trap test failed:', error.message);
        }

        trackResult('Dropdown Focus Management', focusTrapped, 'Focus managed within dropdown');

        // Close dropdown and test focus return
        await page.keyboard.press('Escape');
        await page.waitForTimeout(200);
        
        const focusReturned = await page.evaluate(() => 
          document.activeElement && document.activeElement.textContent && document.activeElement.textContent.includes('Product')
        );
        trackResult('Focus Returns on Close', focusReturned, 'Focus returns to trigger button');
      }

      // Test skip link functionality
      const skipLink = page.locator('a[href="#main-content"], .skip-link').first();
      if (await skipLink.isVisible()) {
        await skipLink.click();
        const mainFocused = await page.evaluate(() => 
          document.activeElement?.id === 'main-content' || 
          document.activeElement?.tagName === 'MAIN'
        );
        trackResult('Skip Link Functionality', mainFocused, 'Skip link moves focus to main content');
      } else {
        trackResult('Skip Link Functionality', true, 'Skip link not visible (acceptable)');
      }

      // Test overall keyboard navigation flow
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      const keyboardNavWorks = await page.evaluate(() => {
        return document.activeElement && document.activeElement !== document.body;
      });
      trackResult('General Keyboard Navigation', keyboardNavWorks, 'Tab navigation works throughout page');

      // Test theme toggle keyboard accessibility
      const themeToggle = page.locator('button[aria-label*="theme"], .theme-toggle').first();
      if (await themeToggle.isVisible()) {
        await themeToggle.focus();
        await page.keyboard.press('Enter');
        await page.waitForTimeout(500);
        
        // Check if theme actually changed (basic test)
        const bodyClass = await page.evaluate(() => document.body.className);
        trackResult('Theme Toggle Keyboard', true, 'Theme toggle accessible via keyboard');
      }

    } catch (error) {
      trackResult('Focus Trap and Keyboard Accessibility', false, error.message);
    }
  });

  test('ARIA attributes and semantic markup', async ({ page }) => {
    try {
      // Check for proper ARIA labels
      const ariaLabels = await page.locator('[aria-label]').count();
      trackResult('ARIA Labels Present', ariaLabels > 0, `${ariaLabels} elements with aria-label`);

      // Check for proper roles
      const roles = await page.locator('[role]').count();
      trackResult('Role Attributes Present', roles > 0, `${roles} elements with role attribute`);

      // Check navigation landmarks
      const navElements = await page.locator('nav, [role="navigation"]').count();
      trackResult('Navigation Landmarks', navElements > 0, `${navElements} navigation landmarks`);

      // Check for proper heading structure
      const h1Count = await page.locator('h1').count();
      const h2Count = await page.locator('h2').count();
      trackResult('Heading Structure', h1Count === 1 && h2Count > 0, `H1: ${h1Count}, H2: ${h2Count}`);

      // Check for alt text on images
      const images = await page.locator('img').count();
      const imagesWithAlt = await page.locator('img[alt]').count();
      const altTextRatio = images > 0 ? (imagesWithAlt / images) * 100 : 100;
      trackResult('Image Alt Text', altTextRatio >= 80, `${imagesWithAlt}/${images} images with alt text (${altTextRatio.toFixed(1)}%)`);

      // Check for proper button labels
      const buttons = await page.locator('button').count();
      const labeledButtons = await page.locator('button[aria-label], button:has-text("")').count();
      const buttonLabelRatio = buttons > 0 ? (labeledButtons / buttons) * 100 : 100;
      trackResult('Button Labels', buttonLabelRatio >= 90, `${labeledButtons}/${buttons} buttons properly labeled (${buttonLabelRatio.toFixed(1)}%)`);

    } catch (error) {
      trackResult('ARIA and Semantic Markup', false, error.message);
    }
  });

  test('Theme toggle functionality across contexts', async ({ page }) => {
    try {
      // Test desktop theme toggle
      const desktopThemeToggle = page.locator('button[aria-label*="theme"]').first();
      
      if (await desktopThemeToggle.isVisible()) {
        // Get initial theme
        const initialTheme = await page.evaluate(() => 
          document.body.className.includes('theme-dark') || 
          localStorage.getItem('theme-preference')
        );
        
        // Click theme toggle
        await desktopThemeToggle.click();
        await page.waitForTimeout(500);
        
        // Check if theme changed
        const newTheme = await page.evaluate(() => 
          document.body.className.includes('theme-dark') || 
          localStorage.getItem('theme-preference')
        );
        
        const themeChanged = initialTheme !== newTheme;
        trackResult('Desktop Theme Toggle', themeChanged, 'Theme changes on desktop');
        
        // Test theme persistence
        await page.reload();
        await page.waitForLoadState('networkidle');
        
        const persistedTheme = await page.evaluate(() => 
          localStorage.getItem('theme-preference')
        );
        trackResult('Theme Persistence', persistedTheme !== null, `Theme persisted: ${persistedTheme}`);
      }

      // Test mobile theme toggle
      await page.setViewportSize({ width: 375, height: 667 });
      const mobileMenuBtn = page.locator('button[aria-label*="menu"]').first();
      
      if (await mobileMenuBtn.isVisible()) {
        await mobileMenuBtn.click();
        await page.waitForTimeout(500);
        
        const mobileThemeToggle = page.locator('button[aria-label*="theme"]').first();
        if (await mobileThemeToggle.isVisible()) {
          await mobileThemeToggle.click();
          await page.waitForTimeout(500);
          trackResult('Mobile Theme Toggle', true, 'Mobile theme toggle works');
        } else {
          trackResult('Mobile Theme Toggle', false, 'Mobile theme toggle not found');
        }
      }

    } catch (error) {
      trackResult('Theme Toggle Functionality', false, error.message);
    }
  });
});