const { test, expect } = require('@playwright/test');

/**
 * Persona-Based Usability Testing Suite
 * 
 * Tests UCL Auction usability with 3 personas:
 * - Commissioner Casey (desktop, mouse + keyboard)
 * - Manager Morgan (mobile, one-hand use) 
 * - Manager Riley (desktop, keyboard-only + screen reader)
 */

test.describe('UCL Auction - Persona Usability Tests', () => {
  const usabilityResults = {
    personas: {
      casey: { tasks: [], issues: [], successes: [] },
      morgan: { tasks: [], issues: [], successes: [] },
      riley: { tasks: [], issues: [], successes: [] }
    },
    heuristics: {},
    screenshots: [],
    recommendations: []
  };

  // Heuristics evaluation framework
  const evaluateHeuristic = async (page, heuristic, persona, expected = true) => {
    const key = `${persona}_${heuristic.replace(/\s+/g, '_').toLowerCase()}`;
    
    try {
      const result = await heuristic.evaluation(page);
      usabilityResults.heuristics[key] = {
        persona,
        heuristic: heuristic.name,
        passed: result.passed,
        notes: result.notes,
        expected
      };
      
      console.log(`${result.passed ? '✅' : '❌'} ${persona}: ${heuristic.name} - ${result.notes}`);
      return result.passed;
    } catch (error) {
      usabilityResults.heuristics[key] = {
        persona,
        heuristic: heuristic.name,
        passed: false,
        notes: `Error: ${error.message}`,
        expected
      };
      console.log(`❌ ${persona}: ${heuristic.name} - Error: ${error.message}`);
      return false;
    }
  };

  const takeUsabilityScreenshot = async (page, persona, scenario, description) => {
    const timestamp = Date.now();
    const filename = `usability-${persona}-${scenario}-${timestamp}.png`;
    const path = `test-results/screenshots/${filename}`;
    
    await page.screenshot({ 
      path,
      fullPage: false,
      quality: 90
    });
    
    usabilityResults.screenshots.push({
      persona,
      scenario,
      description,
      filename,
      path
    });
    
    console.log(`📸 Screenshot: ${description} (${filename})`);
  };

  test.afterAll(async () => {
    // Generate usability report
    console.log('\n' + '='.repeat(60));
    console.log('👥 USABILITY TESTING REPORT');
    console.log('='.repeat(60));
    
    Object.entries(usabilityResults.personas).forEach(([persona, data]) => {
      console.log(`\n🎭 ${persona.toUpperCase()}:`);
      console.log(`   Tasks: ${data.tasks.length}`);
      console.log(`   Issues: ${data.issues.length}`);
      console.log(`   Successes: ${data.successes.length}`);
    });
    
    console.log(`\n📊 HEURISTICS EVALUATION:`);
    const heuristicsPassed = Object.values(usabilityResults.heuristics).filter(h => h.passed).length;
    const heuristicsTotal = Object.values(usabilityResults.heuristics).length;
    console.log(`   Passed: ${heuristicsPassed}/${heuristicsTotal}`);
    
    console.log(`\n📸 SCREENSHOTS: ${usabilityResults.screenshots.length}`);
    
    console.log('='.repeat(60));
  });

  // Persona 1: Commissioner Casey (Desktop, Mouse + Keyboard)
  test('Casey: League Creation and Management Flow', async ({ page }) => {
    const persona = 'casey';
    console.log('🎭 Testing Casey (Commissioner, Desktop)...');
    
    try {
      // Task 1: Navigate to homepage
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await takeUsabilityScreenshot(page, persona, 'homepage', 'Initial homepage view');
      
      usabilityResults.personas[persona].tasks.push('Navigate to homepage');
      usabilityResults.personas[persona].successes.push('Homepage loaded successfully');
      
      // Task 2: Look for league creation
      const hasCreateLeague = await page.locator('text=Create League || text=Create || text=New League').isVisible();
      const hasLogin = await page.locator('text=Login || input[type="email"]').isVisible();
      
      if (hasLogin) {
        await takeUsabilityScreenshot(page, persona, 'auth', 'Authentication required');
        usabilityResults.personas[persona].tasks.push('Authentication flow required');
        
        // Check auth usability
        const emailInput = page.locator('input[type="email"]');
        const hasEmailLabel = await emailInput.getAttribute('aria-label') || await emailInput.getAttribute('placeholder');
        
        if (hasEmailLabel) {
          usabilityResults.personas[persona].successes.push('Email input has proper labeling');
        } else {
          usabilityResults.personas[persona].issues.push('Email input lacks clear labeling');
        }
      }
      
      if (hasCreateLeague) {
        await page.click('text=Create League || text=Create || text=New League');
        await takeUsabilityScreenshot(page, persona, 'create-league', 'League creation form');
        usabilityResults.personas[persona].successes.push('League creation accessible');
      } else {
        usabilityResults.personas[persona].issues.push('League creation not immediately visible');
      }
      
      // Task 3: Evaluate mental model clarity
      const hasHelp = await page.locator('text=Help || text=How to || text=Guide || [aria-label*="help"]').isVisible();
      const hasTooltips = await page.locator('[title], [data-tooltip], .tooltip').count();
      
      if (hasHelp || hasTooltips > 0) {
        usabilityResults.personas[persona].successes.push('Help/guidance elements present');
      } else {
        usabilityResults.personas[persona].issues.push('Limited help or guidance visible');
      }
      
      // Task 4: Check for system status visibility
      const statusElements = await page.locator('[data-testid*="status"], .status, .badge, .indicator').count();
      if (statusElements > 0) {
        usabilityResults.personas[persona].successes.push('System status indicators present');
      } else {
        usabilityResults.personas[persona].issues.push('Limited system status visibility');
      }
      
      console.log(`✅ Casey's tasks completed: ${usabilityResults.personas[persona].tasks.length}`);
      
    } catch (error) {
      usabilityResults.personas[persona].issues.push(`Task failed: ${error.message}`);
      console.log(`❌ Casey's task failed: ${error.message}`);
    }
  });

  // Persona 2: Manager Morgan (Mobile, One-hand use)
  test('Morgan: Mobile Auction Experience', async ({ page, context }) => {
    const persona = 'morgan';
    console.log('🎭 Testing Morgan (Manager, Mobile)...');
    
    try {
      // Set mobile context
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await takeUsabilityScreenshot(page, persona, 'mobile-homepage', 'Mobile homepage view');
      
      usabilityResults.personas[persona].tasks.push('Mobile navigation');
      
      // Task 1: Mobile navigation usability
      const hasHamburgerMenu = await page.locator('[aria-label*="menu"], .hamburger, .menu-toggle').isVisible();
      const hasBottomNav = await page.locator('nav[style*="bottom"], .bottom-nav, .tab-bar').isVisible();
      
      if (hasHamburgerMenu || hasBottomNav) {
        usabilityResults.personas[persona].successes.push('Mobile navigation pattern found');
      } else {
        usabilityResults.personas[persona].issues.push('No clear mobile navigation pattern');
      }
      
      // Task 2: Touch target size evaluation
      const buttons = await page.locator('button, a, input[type="submit"]').all();
      let smallTargets = 0;
      
      for (const button of buttons) {
        try {
          const box = await button.boundingBox();
          if (box && (box.width < 44 || box.height < 44)) {
            smallTargets++;
          }
        } catch (e) {
          // Skip elements that can't be measured
        }
      }
      
      if (smallTargets === 0) {
        usabilityResults.personas[persona].successes.push('All touch targets meet 44px minimum');
      } else {
        usabilityResults.personas[persona].issues.push(`${smallTargets} touch targets below 44px minimum`);
      }
      
      // Task 3: Horizontal scroll check
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.viewportSize().width;
      
      if (bodyWidth <= viewportWidth + 10) { // 10px tolerance
        usabilityResults.personas[persona].successes.push('No horizontal scroll detected');
      } else {
        usabilityResults.personas[persona].issues.push('Horizontal scroll detected - may cause mobile usability issues');
      }
      
      // Task 4: Thumb zone accessibility
      const primaryActions = await page.locator('button[type="submit"], .primary-button, .cta-button').all();
      let thumbZoneActions = 0;
      
      for (const action of primaryActions) {
        try {
          const box = await action.boundingBox();
          if (box && box.y > 300) { // Rough thumb zone (bottom 2/3 of mobile screen)
            thumbZoneActions++;
          }
        } catch (e) {
          // Skip elements that can't be measured
        }
      }
      
      if (thumbZoneActions > 0) {
        usabilityResults.personas[persona].successes.push('Primary actions in thumb-reach zone');
      } else {
        usabilityResults.personas[persona].issues.push('Primary actions may be difficult to reach with thumb');
      }
      
      await takeUsabilityScreenshot(page, persona, 'mobile-interaction', 'Mobile interaction elements');
      
      console.log(`✅ Morgan's mobile tasks completed: ${usabilityResults.personas[persona].tasks.length}`);
      
    } catch (error) {
      usabilityResults.personas[persona].issues.push(`Mobile task failed: ${error.message}`);
      console.log(`❌ Morgan's task failed: ${error.message}`);
    }
  });

  // Persona 3: Manager Riley (Desktop, Keyboard-only + Screen Reader)
  test('Riley: Keyboard Navigation and Screen Reader Experience', async ({ page }) => {
    const persona = 'riley';
    console.log('🎭 Testing Riley (Manager, Keyboard + Screen Reader)...');
    
    try {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await takeUsabilityScreenshot(page, persona, 'keyboard-start', 'Initial state for keyboard navigation');
      
      usabilityResults.personas[persona].tasks.push('Keyboard navigation assessment');
      
      // Task 1: Keyboard navigation flow
      let focusableElements = [];
      let tabIndex = 0;
      
      // Simulate Tab navigation
      try {
        for (let i = 0; i < 10; i++) {
          await page.keyboard.press('Tab');
          
          const focusedElement = await page.locator(':focus').first();
          if (await focusedElement.isVisible()) {
            const tagName = await focusedElement.evaluate(el => el.tagName);
            const role = await focusedElement.getAttribute('role') || '';
            const ariaLabel = await focusedElement.getAttribute('aria-label') || '';
            
            focusableElements.push({
              index: i,
              tagName,
              role,
              ariaLabel,
              hasVisibleFocus: true
            });
            tabIndex++;
          }
          
          await page.waitForTimeout(100);
        }
      } catch (error) {
        usabilityResults.personas[riley].issues.push(`Keyboard navigation error: ${error.message}`);
      }
      
      if (focusableElements.length > 0) {
        usabilityResults.personas[persona].successes.push(`${focusableElements.length} keyboard-accessible elements found`);
      } else {
        usabilityResults.personas[persona].issues.push('No keyboard-accessible elements detected');
      }
      
      // Task 2: Focus visibility check
      await page.keyboard.press('Tab');
      const focusedElement = await page.locator(':focus').first();
      
      try {
        const focusStyles = await focusedElement.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            outline: computed.outline,
            outlineWidth: computed.outlineWidth,
            boxShadow: computed.boxShadow,
            border: computed.border
          };
        });
        
        const hasVisibleFocus = focusStyles.outline !== 'none' || 
                               focusStyles.outlineWidth !== '0px' ||
                               focusStyles.boxShadow !== 'none' ||
                               focusStyles.border.includes('solid');
        
        if (hasVisibleFocus) {
          usabilityResults.personas[persona].successes.push('Visible focus indicators present');
        } else {
          usabilityResults.personas[persona].issues.push('Focus indicators may not be visible enough');
        }
      } catch (error) {
        usabilityResults.personas[persona].issues.push('Could not evaluate focus visibility');
      }
      
      // Task 3: ARIA labels and landmarks
      const ariaLabels = await page.locator('[aria-label], [aria-labelledby], [aria-describedby]').count();
      const landmarks = await page.locator('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], main, nav, header, footer').count();
      
      if (ariaLabels > 0) {
        usabilityResults.personas[persona].successes.push(`${ariaLabels} ARIA-labeled elements found`);
      } else {
        usabilityResults.personas[persona].issues.push('Limited ARIA labeling detected');
      }
      
      if (landmarks > 0) {
        usabilityResults.personas[persona].successes.push(`${landmarks} page landmarks found`);
      } else {
        usabilityResults.personas[persona].issues.push('Page landmarks missing - navigation may be difficult');
      }
      
      // Task 4: Form accessibility
      const formInputs = await page.locator('input, select, textarea').all();
      let properlyLabeledInputs = 0;
      
      for (const input of formInputs) {
        try {
          const hasLabel = await input.getAttribute('aria-label') || 
                           await input.getAttribute('aria-labelledby') ||
                           await page.locator(`label[for="${await input.getAttribute('id')}"]`).count() > 0;
          
          if (hasLabel) {
            properlyLabeledInputs++;
          }
        } catch (e) {
          // Skip elements that can't be checked
        }
      }
      
      if (formInputs.length > 0) {
        const labelPercentage = Math.round((properlyLabeledInputs / formInputs.length) * 100);
        if (labelPercentage >= 90) {
          usabilityResults.personas[persona].successes.push(`${labelPercentage}% of form inputs properly labeled`);
        } else {
          usabilityResults.personas[persona].issues.push(`Only ${labelPercentage}% of form inputs properly labeled`);
        }
      }
      
      await takeUsabilityScreenshot(page, persona, 'keyboard-focus', 'Keyboard focus state');
      
      console.log(`✅ Riley's keyboard tasks completed: ${usabilityResults.personas[persona].tasks.length}`);
      
    } catch (error) {
      usabilityResults.personas[persona].issues.push(`Keyboard task failed: ${error.message}`);
      console.log(`❌ Riley's task failed: ${error.message}`);
    }
  });

  // Heuristics Evaluation Tests
  test('Heuristics: Clear Mental Model', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const heuristic = {
      name: 'Clear Mental Model',
      evaluation: async (page) => {
        const hasScoring = await page.locator('text=points, text=score, text=win, text=draw, text=goal').isVisible();
        const hasTooltips = await page.locator('[title*="point"], [title*="score"], .tooltip').count();
        const hasExamples = await page.locator('text=example, text="2-2", text="3 points"').isVisible();
        
        const clarity = hasScoring || hasTooltips > 0 || hasExamples;
        
        return {
          passed: clarity,
          notes: clarity ? 'Scoring/points system explained' : 'Scoring system unclear - needs examples like "2-2 draw = 3 points"'
        };
      }
    };
    
    await evaluateHeuristic(page, heuristic, 'general');
  });

  test('Heuristics: System Status Visibility', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const heuristic = {
      name: 'System Status Visibility',
      evaluation: async (page) => {
        const statusElements = await page.locator('.timer, .budget, .status, [data-testid*="timer"], [data-testid*="budget"]').count();
        const liveRegions = await page.locator('[aria-live], [role="status"], [role="alert"]').count();
        
        const visibility = statusElements > 0 || liveRegions > 0;
        
        return {
          passed: visibility,
          notes: visibility ? 'Status indicators present' : 'Missing live status updates for timer, budget, bids'
        };
      }
    };
    
    await evaluateHeuristic(page, heuristic, 'general');
  });

  test('Heuristics: Error Prevention and Messages', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const heuristic = {
      name: 'Error Prevention',
      evaluation: async (page) => {
        const errorMessages = await page.locator('.error, .warning, [role="alert"], [aria-describedby]').count();
        const disabledStates = await page.locator('button[disabled], input[disabled]').count();
        const helpText = await page.locator('.help-text, .hint, small').count();
        
        const prevention = errorMessages > 0 || disabledStates > 0 || helpText > 0;
        
        return {
          passed: prevention,
          notes: prevention ? 'Error prevention elements found' : 'Need better error prevention and helpful messages'
        };
      }
    };
    
    await evaluateHeuristic(page, heuristic, 'general');
  });

  test('Heuristics: Mobile Ergonomics', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const heuristic = {
      name: 'Mobile Ergonomics',
      evaluation: async (page) => {
        const hasHorizontalScroll = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
        const primaryButtons = await page.locator('button[type="submit"], .primary-btn, .cta').count();
        const stickyElements = await page.locator('[style*="sticky"], [style*="fixed"], .sticky, .fixed').count();
        
        const ergonomics = !hasHorizontalScroll && primaryButtons > 0 && stickyElements > 0;
        
        return {
          passed: ergonomics,
          notes: ergonomics ? 'Mobile ergonomics good' : 'Check thumb zone, horizontal scroll, sticky timer'
        };
      }
    };
    
    await evaluateHeuristic(page, heuristic, 'mobile');
  });

  test('Heuristics: Learnability', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const heuristic = {
      name: 'Learnability',
      evaluation: async (page) => {
        const disabledButtons = await page.locator('button[disabled]').count();
        const tooltips = await page.locator('[title], [data-tooltip], .tooltip').count();
        const helpText = await page.locator('.help, .hint, .guide').count();
        
        const learnable = disabledButtons > 0 && (tooltips > 0 || helpText > 0);
        
        return {
          passed: learnable,
          notes: learnable ? 'Disabled states with explanations' : 'Disabled buttons should explain requirements (e.g., "Need 4+ managers")'
        };
      }
    };
    
    await evaluateHeuristic(page, heuristic, 'general');
  });
});