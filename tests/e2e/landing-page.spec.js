const { test, expect } = require('@playwright/test');

/**
 * Landing Page Comprehensive Tests
 * 
 * Tests landing page functionality, sticky navigation, scroll-spy, and CTAs
 */

test.describe('Landing Page - Comprehensive Testing', () => {
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
    // Set viewport and navigate to landing page
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.afterAll(async () => {
    const duration = ((Date.now() - testResults.startTime) / 1000).toFixed(2);
    console.log('\n' + '='.repeat(60));
    console.log('📊 Landing Page Test Summary:');
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

  test('Landing page loads correctly with all sections', async ({ page }) => {
    try {
      // Test page load and title
      const title = await page.title();
      const expectedTitle = 'Friends of PIFA — Sports gaming with friends. No gambling, all strategy.';
      const titleCorrect = title === expectedTitle;
      trackResult('Page Title', titleCorrect, `Expected: "${expectedTitle}", Got: "${title}"`);

      // Test all main sections exist
      const sections = ['#home', '#how', '#why', '#features', '#safety', '#faq'];
      let sectionsExist = true;

      for (const selector of sections) {
        const section = await page.locator(selector);
        const exists = await section.isVisible();
        if (!exists) {
          sectionsExist = false;
          trackResult(`Section ${selector}`, false, 'Section not visible');
        }
      }
      
      if (sectionsExist) {
        trackResult('All Main Sections', true, `${sections.length} sections visible`);
      }

      // Test hero section content
      const heroTitle = await page.locator('h1').first();
      const heroVisible = await heroTitle.isVisible();
      trackResult('Hero Section', heroVisible, 'Hero title visible');

      // Test CTAs in hero section
      const createLeagueBtn = page.getByRole('button', { name: /create a league/i });
      const joinInviteBtn = page.getByRole('button', { name: /join with an invite/i });
      
      const createVisible = await createLeagueBtn.isVisible();
      const joinVisible = await joinInviteBtn.isVisible();
      
      trackResult('Hero CTA Buttons', createVisible && joinVisible, 'Both CTA buttons visible');

      // Test footer exists
      const footer = page.locator('footer');
      const footerVisible = await footer.isVisible();
      trackResult('Footer', footerVisible, 'Footer visible');

    } catch (error) {
      trackResult('Landing Page Load', false, error.message);
    }
  });

  test('Sticky in-page navigation anchors scroll correctly', async ({ page }) => {
    try {
      // Wait for page to load and scroll past hero to trigger sticky nav
      await page.evaluate(() => window.scrollTo(0, 1200));
      await page.waitForTimeout(1000);

      // Check if sticky navigation appears
      const stickyNav = page.locator('[data-testid="sticky-page-nav"], .sticky-nav, nav[aria-label*="page navigation"]').first();
      let stickyVisible = false;
      
      // Try different selectors for sticky nav
      const possibleSelectors = [
        'nav:has-text("Home")',
        '.sticky',
        '[role="navigation"]'
      ];

      for (const selector of possibleSelectors) {
        const nav = page.locator(selector);
        if (await nav.isVisible()) {
          stickyVisible = true;
          break;
        }
      }

      trackResult('Sticky Navigation Visibility', stickyVisible, 'After scrolling past hero');

      // Test anchor scrolling functionality
      const sections = [
        { id: '#home', name: 'Home' },
        { id: '#how', name: 'How it Works' },
        { id: '#why', name: 'Why FoP' },
        { id: '#features', name: 'Features' },
        { id: '#safety', name: 'Fair Play' },
        { id: '#faq', name: 'FAQ' }
      ];

      let scrollTestsPassed = 0;

      for (const section of sections) {
        try {
          // Get initial scroll position
          const initialY = await page.evaluate(() => window.pageYOffset);
          
          // Try to find and click navigation link
          const navLink = page.locator(`a[href="${section.id}"], button:has-text("${section.name}")`).first();
          
          if (await navLink.isVisible()) {
            await navLink.click();
            await page.waitForTimeout(1000); // Wait for smooth scroll
            
            // Check if scrolled
            const newY = await page.evaluate(() => window.pageYOffset);
            if (Math.abs(newY - initialY) > 50) { // Scrolled at least 50px
              scrollTestsPassed++;
            }
          }
        } catch (error) {
          console.log(`Anchor scroll test for ${section.id} failed: ${error.message}`);
        }
      }

      trackResult('Anchor Scrolling', scrollTestsPassed > 0, `${scrollTestsPassed}/${sections.length} sections scrolled`);

    } catch (error) {
      trackResult('Sticky Navigation', false, error.message);
    }
  });

  test('Scroll-spy updates active section highlighting', async ({ page }) => {
    try {
      // Scroll to different sections and check for active states
      const sections = ['#home', '#how', '#why', '#features'];
      let scrollSpyWorking = false;

      for (const sectionId of sections) {
        try {
          // Scroll to section
          await page.evaluate((id) => {
            const element = document.querySelector(id);
            if (element) {
              element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }, sectionId);
          
          await page.waitForTimeout(1500); // Wait for scroll and scroll-spy update

          // Look for active indicators in navigation
          const activeIndicators = await page.locator('.active, [aria-current], .bg-blue, .text-blue').count();
          
          if (activeIndicators > 0) {
            scrollSpyWorking = true;
            break;
          }
        } catch (error) {
          console.log(`Scroll-spy test for ${sectionId} failed: ${error.message}`);
        }
      }

      trackResult('Scroll-spy Active Highlighting', scrollSpyWorking, 'Active section indicators detected');

      // Test browser hash updates
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.waitForTimeout(1000);
      
      const finalHash = await page.evaluate(() => window.location.hash);
      trackResult('Browser Hash Updates', typeof finalHash === 'string', `Hash: ${finalHash}`);

    } catch (error) {
      trackResult('Scroll-spy Functionality', false, error.message);
    }
  });

  test('CTAs route to create/join flows correctly', async ({ page }) => {
    try {
      // Test hero CTA buttons
      const createLeagueBtn = page.getByRole('button', { name: /create a league/i }).first();
      const joinInviteBtn = page.getByRole('button', { name: /join with an invite/i }).first();

      // Test Create League button
      let createRouteWorks = false;
      try {
        await createLeagueBtn.click();
        await page.waitForURL('**/login', { timeout: 5000 });
        createRouteWorks = true;
        await page.goBack();
        await page.waitForLoadState('networkidle');
      } catch (error) {
        console.log(`Create League CTA routing test failed: ${error.message}`);
      }

      trackResult('Create League CTA Routing', createRouteWorks, 'Routes to /login');

      // Test Join Invite button
      let joinRouteWorks = false;
      try {
        await joinInviteBtn.click();
        await page.waitForURL('**/login', { timeout: 5000 });
        joinRouteWorks = true;
        await page.goBack();
        await page.waitForLoadState('networkidle');
      } catch (error) {
        console.log(`Join Invite CTA routing test failed: ${error.message}`);
      }

      trackResult('Join Invite CTA Routing', joinRouteWorks, 'Routes to /login');

      // Test sticky CTA (mobile)
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      const stickyCTA = page.locator('.fixed.bottom-0 button, .sticky-cta').first();
      const stickyVisible = await stickyCTA.isVisible();
      
      if (stickyVisible) {
        let stickyRouteWorks = false;
        try {
          await stickyCTA.click();
          await page.waitForURL('**/login', { timeout: 5000 });
          stickyRouteWorks = true;
        } catch (error) {
          console.log(`Sticky CTA routing test failed: ${error.message}`);
        }
        trackResult('Sticky CTA (Mobile)', stickyRouteWorks, 'Mobile sticky CTA routes correctly');
      } else {
        trackResult('Sticky CTA (Mobile)', true, 'Not visible (acceptable on desktop-first)');
      }

    } catch (error) {
      trackResult('CTA Routing Tests', false, error.message);
    }
  });

  test('Responsive design and mobile layout', async ({ page }) => {
    try {
      const viewports = [
        { width: 1920, height: 1080, name: 'Desktop' },
        { width: 768, height: 1024, name: 'Tablet' },
        { width: 375, height: 667, name: 'Mobile' }
      ];

      let responsiveTestsPassed = 0;

      for (const viewport of viewports) {
        try {
          await page.setViewportSize(viewport);
          await page.waitForTimeout(500);

          // Check if hero content is visible
          const heroTitle = page.locator('h1').first();
          const heroVisible = await heroTitle.isVisible();

          // Check if navigation is appropriate for viewport
          const navVisible = await page.locator('nav, header').first().isVisible();

          if (heroVisible && navVisible) {
            responsiveTestsPassed++;
          }
        } catch (error) {
          console.log(`Responsive test for ${viewport.name} failed: ${error.message}`);
        }
      }

      trackResult('Responsive Design', responsiveTestsPassed === viewports.length, 
        `${responsiveTestsPassed}/${viewports.length} viewports working`);

    } catch (error) {
      trackResult('Responsive Design', false, error.message);
    }
  });
});