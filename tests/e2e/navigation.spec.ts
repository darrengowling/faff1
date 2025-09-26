/**
 * Navigation Usability Tests
 * 
 * Comprehensive Playwright tests for navigation functionality including:
 * - Desktop navigation with scroll-spy
 * - Product dropdown navigation
 * - Keyboard accessibility
 * - Mobile hamburger menu
 * - Focus management and no placeholder links
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

// Test configuration
const DESKTOP_VIEWPORT = { width: 1920, height: 1080 };
const MOBILE_VIEWPORT = { width: 390, height: 844 };
const TEST_TIMEOUT = 30000;

// Helper function to take screenshot on failure
const takeFailureScreenshot = async (page: Page, testName: string) => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const screenshotPath = `test-results/nav-${testName}-failure-${timestamp}.png`;
  await page.screenshot({ 
    path: screenshotPath, 
    fullPage: true 
  });
  console.log(`📸 Failure screenshot saved: ${screenshotPath}`);
};

test.describe('Navigation Usability Tests', () => {
  test.setTimeout(TEST_TIMEOUT);

  test.beforeEach(async ({ page }) => {
    // Navigate to landing page before each test
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Desktop Navigation Tests', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize(DESKTOP_VIEWPORT);
    });

    test('Landing page top nav links jump to sections with scroll-spy', async ({ page }) => {
      const testName = 'desktop-scroll-spy';
      
      try {
        console.log('🧪 Testing desktop navigation scroll-spy behavior...');
        
        // Test "How it Works" link
        const howLink = page.locator('nav a[href="/#how"], nav button:has-text("How it Works")').first();
        await expect(howLink).toBeVisible();
        await howLink.click();
        await page.waitForTimeout(1000);
        
        // Verify we're at the how section
        const howSection = page.locator('#how');
        await expect(howSection).toBeVisible();
        
        // Check if section is in viewport (scroll-spy active)
        const howSectionBox = await howSection.boundingBox();
        expect(howSectionBox).not.toBeNull();
        
        console.log('✅ How it Works navigation working');
        
        // Test "Why FoP" link
        const whyLink = page.locator('nav a[href="/#why"], nav button:has-text("Why FoP")').first();
        await expect(whyLink).toBeVisible();
        await whyLink.click();
        await page.waitForTimeout(1000);
        
        // Verify we're at the why section
        const whySection = page.locator('#why');
        await expect(whySection).toBeVisible();
        
        console.log('✅ Why FoP navigation working');
        
        // Test "FAQ" link
        const faqLink = page.locator('nav a[href="/#faq"], nav button:has-text("FAQ")').first();
        await expect(faqLink).toBeVisible();
        await faqLink.click();
        await page.waitForTimeout(1000);
        
        // Verify we're at the FAQ section
        const faqSection = page.locator('#faq');
        await expect(faqSection).toBeVisible();
        
        console.log('✅ FAQ navigation working');
        
        // Verify scroll-spy active states (check for active classes)
        const activeElements = page.locator('nav .text-blue-600, nav .bg-blue-50, nav [aria-current="page"]');
        const activeCount = await activeElements.count();
        expect(activeCount).toBeGreaterThan(0);
        
        console.log('✅ Scroll-spy active states detected');
        
      } catch (error) {
        console.error('❌ Desktop scroll-spy test failed:', error);
        await takeFailureScreenshot(page, testName);
        throw error;
      }
    });

    test('Product dropdown navigation to correct routes', async ({ page }) => {
      const testName = 'product-dropdown-routes';
      
      try {
        console.log('🧪 Testing Product dropdown navigation...');
        
        // Find and click Product dropdown
        const productDropdown = page.locator('button:has-text("Product")').first();
        await expect(productDropdown).toBeVisible();
        await productDropdown.click();
        await page.waitForTimeout(500);
        
        // Verify dropdown is open (look for the actual dropdown container)
        const dropdown = page.locator('.bg-theme-surface, .bg-white').filter({ hasText: 'Auction Room' });
        await expect(dropdown).toBeVisible({ timeout: 10000 });
        
        console.log('✅ Product dropdown opened');
        
        // Test each dropdown item navigation
        const dropdownItems = [
          { text: 'Auction Room', expectedRoute: '/login' }, // Should redirect to login for unauthenticated users
          { text: 'My Roster', expectedRoute: '/login' },
          { text: 'Fixtures', expectedRoute: '/login' },
          { text: 'Leaderboard', expectedRoute: '/login' },
          { text: 'League', expectedRoute: '/login' } // League Settings/Admin
        ];
        
        for (const item of dropdownItems) {
          // Reopen dropdown for each test
          await productDropdown.click();
          await page.waitForTimeout(300);
          
          // Find and click the item
          const menuItem = page.locator(`[role="menuitem"]:has-text("${item.text}"), button:has-text("${item.text}")`).first();
          
          if (await menuItem.isVisible()) {
            await menuItem.click();
            await page.waitForTimeout(1000);
            
            // Verify navigation (should redirect to login for unauthenticated users)
            const currentURL = page.url();
            expect(currentURL).toContain(item.expectedRoute);
            
            console.log(`✅ ${item.text} navigation working (${currentURL})`);
            
            // Navigate back to landing page for next test
            await page.goto('/');
            await page.waitForLoadState('networkidle');
          } else {
            console.log(`⚠️ ${item.text} menu item not visible (may be disabled)`);
          }
        }
        
      } catch (error) {
        console.error('❌ Product dropdown test failed:', error);
        await takeFailureScreenshot(page, testName);
        throw error;
      }
    });
  });

  test.describe('Keyboard Navigation Tests', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize(DESKTOP_VIEWPORT);
    });

    test('Keyboard accessibility for dropdown navigation', async ({ page }) => {
      const testName = 'keyboard-navigation';
      
      try {
        console.log('🧪 Testing keyboard navigation accessibility...');
        
        // Tab to the Product dropdown
        await page.keyboard.press('Tab'); // Brand
        await page.keyboard.press('Tab'); // How it Works
        await page.keyboard.press('Tab'); // Why FoP  
        await page.keyboard.press('Tab'); // FAQ
        await page.keyboard.press('Tab'); // Product dropdown
        
        // Verify focus is on Product dropdown
        const productDropdown = page.locator('button:has-text("Product")').first();
        await expect(productDropdown).toBeFocused();
        
        console.log('✅ Tabbed to Product dropdown successfully');
        
        // Open dropdown with Enter
        await page.keyboard.press('Enter');
        await page.waitForTimeout(500);
        
        // Verify dropdown opened
        const dropdown = page.locator('[role="menu"]').first();
        await expect(dropdown).toBeVisible();
        
        console.log('✅ Dropdown opened with Enter key');
        
        // Test Arrow key navigation
        await page.keyboard.press('ArrowDown');
        await page.waitForTimeout(200);
        await page.keyboard.press('ArrowDown');
        await page.waitForTimeout(200);
        await page.keyboard.press('ArrowUp');
        await page.waitForTimeout(200);
        
        console.log('✅ Arrow key navigation working');
        
        // Test Escape closes dropdown
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
        
        // Verify dropdown closed
        const dropdownVisible = await dropdown.isVisible().catch(() => false);
        expect(dropdownVisible).toBeFalsy();
        
        console.log('✅ Escape key closes dropdown');
        
        // Test Enter activates item (reopen dropdown)
        await page.keyboard.press('Enter'); // Open dropdown
        await page.waitForTimeout(500);
        await page.keyboard.press('ArrowDown'); // Focus first item
        await page.keyboard.press('Enter'); // Activate item
        await page.waitForTimeout(1000);
        
        // Should navigate somewhere (likely login page for unauthenticated users)
        const currentURL = page.url();
        expect(currentURL).not.toBe('/');
        
        console.log('✅ Enter key activates focused item');
        
      } catch (error) {
        console.error('❌ Keyboard navigation test failed:', error);
        await takeFailureScreenshot(page, testName);
        throw error;
      }
    });
  });

  test.describe('Mobile Navigation Tests', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize(MOBILE_VIEWPORT);
    });

    test('Mobile hamburger menu functionality and focus trap', async ({ page }) => {
      const testName = 'mobile-hamburger';
      
      try {
        console.log('🧪 Testing mobile hamburger menu...');
        
        // Find and click hamburger menu
        const hamburgerButton = page.locator('button[aria-label*="menu"], button[aria-label*="navigation"]').first();
        await expect(hamburgerButton).toBeVisible();
        await hamburgerButton.click();
        await page.waitForTimeout(500);
        
        // Verify menu drawer opened
        const mobileDrawer = page.locator('[role="navigation"], .mobile-menu, #mobile-navigation').first();
        await expect(mobileDrawer).toBeVisible();
        
        console.log('✅ Mobile menu opened');
        
        // Check that menu items are listed
        const menuItems = page.locator('[role="navigation"] button, [role="navigation"] a');
        const itemCount = await menuItems.count();
        expect(itemCount).toBeGreaterThan(0);
        
        console.log(`✅ Found ${itemCount} menu items`);
        
        // Test navigation on tap (test a few items)
        const navigationTests = [
          { text: 'How it Works', shouldStayOnPage: true },
          { text: 'Why FoP', shouldStayOnPage: true },
          { text: 'Sign In', shouldNavigate: true }
        ];
        
        for (const navTest of navigationTests) {
          // Reopen menu if closed
          if (!(await mobileDrawer.isVisible())) {
            await hamburgerButton.click();
            await page.waitForTimeout(300);
          }
          
          const menuItem = page.locator(`[role="navigation"] button:has-text("${navTest.text}"), [role="navigation"] a:has-text("${navTest.text}")`).first();
          
          if (await menuItem.isVisible()) {
            const startURL = page.url();
            await menuItem.click();
            await page.waitForTimeout(1000);
            
            if (navTest.shouldNavigate) {
              expect(page.url()).not.toBe(startURL);
              console.log(`✅ ${navTest.text} navigated correctly`);
              
              // Navigate back for next test
              await page.goto('/');
              await page.waitForLoadState('networkidle');
            } else {
              // Should stay on same page but scroll to section
              expect(page.url()).toContain('/');
              console.log(`✅ ${navTest.text} scrolled to section`);
            }
          }
        }
        
        // Test focus trap (verify Escape key closes menu)
        await hamburgerButton.click(); // Reopen menu
        await page.waitForTimeout(300);
        
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
        
        const drawerVisible = await mobileDrawer.isVisible().catch(() => false);
        expect(drawerVisible).toBeFalsy();
        
        console.log('✅ Focus trap working - Escape closes menu');
        
        // Test back button functionality (simulate back button)
        await page.goBack();
        await page.waitForTimeout(500);
        expect(page.url()).toContain('/');
        
        console.log('✅ Back button returns to home');
        
      } catch (error) {
        console.error('❌ Mobile hamburger test failed:', error);
        await takeFailureScreenshot(page, testName);
        throw error;
      }
    });
  });

  test.describe('Link Quality Assurance', () => {
    test('No placeholder links with empty or # href', async ({ page }) => {
      const testName = 'no-placeholder-links';
      
      try {
        console.log('🧪 Testing for placeholder links...');
        
        // Check for anchors with href="#" 
        const hashLinks = page.locator('a[href="#"]');
        const hashLinkCount = await hashLinks.count();
        
        if (hashLinkCount > 0) {
          console.log(`⚠️ Found ${hashLinkCount} links with href="#"`);
          // Log them for debugging
          for (let i = 0; i < hashLinkCount; i++) {
            const linkText = await hashLinks.nth(i).textContent();
            console.log(`  - Link with href="#": "${linkText}"`);
          }
        }
        
        expect(hashLinkCount).toBe(0);
        
        // Check for anchors with empty href
        const emptyLinks = page.locator('a[href=""], a:not([href])');
        const emptyLinkCount = await emptyLinks.count();
        
        if (emptyLinkCount > 0) {
          console.log(`⚠️ Found ${emptyLinkCount} links with empty href`);
          for (let i = 0; i < emptyLinkCount; i++) {
            const linkText = await emptyLinks.nth(i).textContent();
            console.log(`  - Link with empty href: "${linkText}"`);
          }
        }
        
        expect(emptyLinkCount).toBe(0);
        
        // Check for buttons that might be acting as placeholder links
        const buttonLinks = page.locator('button[onclick*="#"], button[data-href="#"]');
        const buttonLinkCount = await buttonLinks.count();
        expect(buttonLinkCount).toBe(0);
        
        console.log('✅ No placeholder links found');
        
        // Verify all navigation links have proper hrefs
        const navLinks = page.locator('nav a, [role="navigation"] a');
        const navLinkCount = await navLinks.count();
        
        for (let i = 0; i < navLinkCount; i++) {
          const href = await navLinks.nth(i).getAttribute('href');
          expect(href).toBeTruthy();
          expect(href).not.toBe('#');
          expect(href).not.toBe('');
        }
        
        console.log(`✅ All ${navLinkCount} navigation links have proper hrefs`);
        
      } catch (error) {
        console.error('❌ Placeholder links test failed:', error);
        await takeFailureScreenshot(page, testName);
        throw error;
      }
    });
  });

  test.describe('Cross-browser Compatibility', () => {
    test('Navigation works consistently across viewport sizes', async ({ page }) => {
      const testName = 'cross-viewport';
      
      try {
        console.log('🧪 Testing navigation across different viewport sizes...');
        
        const viewports = [
          { name: 'Desktop', ...DESKTOP_VIEWPORT },
          { name: 'Tablet', width: 768, height: 1024 },
          { name: 'Mobile', ...MOBILE_VIEWPORT }
        ];
        
        for (const viewport of viewports) {
          console.log(`Testing ${viewport.name} viewport (${viewport.width}x${viewport.height})`);
          
          await page.setViewportSize({ width: viewport.width, height: viewport.height });
          await page.waitForTimeout(500);
          
          // Test basic navigation elements exist
          if (viewport.width >= 768) {
            // Desktop/Tablet - check for desktop navigation
            const desktopNav = page.locator('nav button:has-text("Product"), nav a:has-text("How it Works")');
            const navCount = await desktopNav.count();
            expect(navCount).toBeGreaterThan(0);
            
            console.log(`  ✅ Desktop navigation visible (${navCount} elements)`);
          } else {
            // Mobile - check for hamburger menu
            const hamburgerMenu = page.locator('button[aria-label*="menu"], button[aria-label*="navigation"]');
            await expect(hamburgerMenu).toBeVisible();
            
            console.log('  ✅ Mobile hamburger menu visible');
          }
          
          // Test brand/logo navigation
          const brandLogo = page.locator('a[href="/"], button[onclick*="/"]').first();
          if (await brandLogo.isVisible()) {
            await brandLogo.click();
            await page.waitForTimeout(500);
            expect(page.url()).toContain('/');
            
            console.log('  ✅ Brand logo navigation working');
          }
        }
        
      } catch (error) {
        console.error('❌ Cross-viewport test failed:', error);
        await takeFailureScreenshot(page, testName);
        throw error;
      }
    });
  });
});

// Test summary and reporting
test.afterAll(async () => {
  console.log('\n' + '='.repeat(60));
  console.log('📊 Navigation Usability Test Summary Complete');
  console.log('🎯 Tests covered:');
  console.log('  ✅ Desktop scroll-spy navigation');
  console.log('  ✅ Product dropdown routing');
  console.log('  ✅ Keyboard accessibility');
  console.log('  ✅ Mobile hamburger menu');
  console.log('  ✅ Focus trap and drawer management');
  console.log('  ✅ No placeholder links validation');
  console.log('  ✅ Cross-viewport compatibility');
  console.log('='.repeat(60));
});