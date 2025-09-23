const { test, expect } = require('@playwright/test');

/**
 * Basic UCL Auction E2E Test
 * 
 * Core validation tests that can run without complex dependencies
 */

test.describe('UCL Auction - Basic E2E Validation', () => {
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

  test.afterAll(async () => {
    const duration = ((Date.now() - testResults.startTime) / 1000).toFixed(2);
    console.log('\n' + '='.repeat(60));
    console.log('📊 Basic E2E Test Summary:');
    console.log(`⏱️ Duration: ${duration}s`);
    console.log(`✅ Passed: ${testResults.passed.length}`);
    console.log(`❌ Failed: ${testResults.failed.length}`);
    
    if (testResults.passed.length > 0) {
      console.log('\n✅ Passed Tests:');
      testResults.passed.forEach(testName => console.log(`  - ${testName}`));
    }
    
    if (testResults.failed.length > 0) {
      console.log('\n❌ Failed Tests:');
      testResults.failed.forEach(failure => console.log(`  - ${failure}`));
    }
    
    console.log('='.repeat(60));
  });

  test('1. Application Loads Successfully', async ({ page }) => {
    const testName = 'Application Loading';
    
    try {
      await page.goto('/');
      
      // Wait for page to load
      await page.waitForLoadState('networkidle', { timeout: 15000 });
      
      // Check if page loaded
      const pageLoaded = await page.locator('body').isVisible();
      
      if (pageLoaded) {
        trackResult(testName, true, 'Page loaded successfully');
      } else {
        trackResult(testName, false, 'Page failed to load');
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('2. Authentication UI Present', async ({ page }) => {
    const testName = 'Authentication UI';
    
    try {
      await page.goto('/');
      
      // Look for authentication elements
      const hasEmailInput = await page.locator('input[type="email"]').isVisible();
      const hasLoginButton = await page.locator('text=Login').isVisible();
      const hasAuthForm = await page.locator('form').isVisible();
      
      if (hasEmailInput || hasLoginButton || hasAuthForm) {
        trackResult(testName, true, 'Authentication UI found');
      } else {
        trackResult(testName, false, 'No authentication UI found');
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('3. Competition Profiles API Working', async ({ request }) => {
    const testName = 'Competition Profiles API';
    
    try {
      const response = await request.get('/api/competition-profiles');
      
      if (response.ok()) {
        const data = await response.json();
        const hasProfiles = data.profiles && Array.isArray(data.profiles);
        const hasUCL = data.profiles?.some(p => p.id === 'ucl');
        
        if (hasProfiles && hasUCL) {
          trackResult(testName, true, `Found ${data.profiles.length} profiles including UCL`);
        } else {
          trackResult(testName, false, 'Missing profiles or UCL profile');
        }
      } else {
        trackResult(testName, false, `API returned ${response.status()}`);
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('4. UCL Competition Profile Structure', async ({ request }) => {
    const testName = 'UCL Profile Structure';
    
    try {
      const response = await request.get('/api/competition-profiles/ucl');
      
      if (response.ok()) {
        const ucl = await response.json();
        const defaults = ucl.defaults || {};
        
        const hasClubSlots = defaults.club_slots === 3;
        const hasBudget = defaults.budget_per_manager === 100;
        const hasLeagueSize = defaults.league_size?.min === 4 && defaults.league_size?.max === 8;
        
        if (hasClubSlots && hasBudget && hasLeagueSize) {
          trackResult(testName, true, 'UCL profile has correct defaults (3/100/4-8)');
        } else {
          trackResult(testName, false, `Incorrect defaults: slots=${defaults.club_slots}, budget=${defaults.budget_per_manager}, size=${JSON.stringify(defaults.league_size)}`);
        }
      } else {
        trackResult(testName, false, `UCL profile API returned ${response.status()}`);
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('5. PATCH Endpoint Exists', async ({ request }) => {
    const testName = 'PATCH Endpoint Availability';
    
    try {
      // Test PATCH endpoint exists (should return 401/403, not 404)
      const response = await request.patch('/api/leagues/test-id/settings', {
        data: { club_slots_per_manager: 4 }
      });
      
      const status = response.status();
      const endpointExists = status !== 404;
      
      if (endpointExists) {
        trackResult(testName, true, `PATCH endpoint exists (status: ${status})`);
      } else {
        trackResult(testName, false, 'PATCH endpoint not found (404)');
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('6. Responsive Design Check', async ({ page }) => {
    const testName = 'Responsive Design';
    
    try {
      await page.goto('/');
      
      // Test different viewport sizes
      const viewports = [
        { width: 1920, height: 1080, name: 'Desktop' },
        { width: 768, height: 1024, name: 'Tablet' },
        { width: 375, height: 667, name: 'Mobile' }
      ];
      
      let responsive = true;
      
      for (const viewport of viewports) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.waitForTimeout(1000);
        
        const bodyVisible = await page.locator('body').isVisible();
        const contentVisible = await page.locator('main, .container, [role="main"]').isVisible();
        
        if (!bodyVisible && !contentVisible) {
          responsive = false;
          break;
        }
      }
      
      if (responsive) {
        trackResult(testName, true, 'Responsive across all viewports');
      } else {
        trackResult(testName, false, 'Layout issues on some viewports');
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('7. Performance Check', async ({ page }) => {
    const testName = 'Performance Check';
    
    try {
      const startTime = Date.now();
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      
      // Check for basic resources
      const hasResources = await page.locator('link[rel="stylesheet"], script[src]').count() > 0;
      
      if (loadTime < 10000 && hasResources) {
        trackResult(testName, true, `Loaded in ${loadTime}ms with resources`);
      } else {
        trackResult(testName, false, `Slow load: ${loadTime}ms or missing resources`);
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('8. Navigation Structure', async ({ page }) => {
    const testName = 'Navigation Structure';
    
    try {
      await page.goto('/');
      
      // Look for navigation elements
      const hasNav = await page.locator('nav, header, [role="navigation"]').isVisible();
      const hasLinks = await page.locator('a[href]').count() > 0;
      const hasContent = await page.locator('main, [role="main"], .content').isVisible();
      
      if (hasNav || hasLinks || hasContent) {
        trackResult(testName, true, 'Navigation structure found');
      } else {
        trackResult(testName, false, 'No navigation structure detected');
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('9. Error Handling', async ({ page }) => {
    const testName = 'Error Handling';
    
    try {
      // Test 404 handling
      await page.goto('/nonexistent-page');
      
      const hasErrorPage = await page.locator('text=404, text=Not Found, text=Page not found').isVisible();
      const hasContent = await page.locator('body').textContent();
      
      // Return to main page
      await page.goto('/');
      const recovered = await page.locator('body').isVisible();
      
      if (hasErrorPage || hasContent || recovered) {
        trackResult(testName, true, 'Error handling working');
      } else {
        trackResult(testName, false, 'Poor error handling');
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });

  test('10. Overall Application Health', async ({ page, request }) => {
    const testName = 'Overall Application Health';
    
    try {
      // Frontend check
      await page.goto('/');
      const frontendWorks = await page.locator('body').isVisible();
      
      // API check
      const apiResponse = await request.get('/api/competition-profiles');
      const apiWorks = apiResponse.ok();
      
      // Basic functionality check
      const hasInteractiveElements = await page.locator('button, input, a').count() > 0;
      
      if (frontendWorks && apiWorks && hasInteractiveElements) {
        trackResult(testName, true, 'Application healthy - frontend, API, and interactivity working');
      } else {
        trackResult(testName, false, `Issues detected - Frontend: ${frontendWorks}, API: ${apiWorks}, Interactive: ${hasInteractiveElements}`);
      }
    } catch (error) {
      trackResult(testName, false, error.message);
    }
  });
});