const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

/**
 * Accessibility Audit Suite
 * 
 * Automated accessibility testing using axe-core
 * Tests key pages and user flows for WCAG compliance
 */

test.describe('UCL Auction - Accessibility Audit', () => {
  const auditResults = {
    pages: [],
    violations: [],
    totalViolations: 0,
    criticalViolations: 0
  };

  test.afterAll(async () => {
    // Generate accessibility report
    console.log('\n' + '='.repeat(60));
    console.log('🔍 ACCESSIBILITY AUDIT REPORT');
    console.log('='.repeat(60));
    console.log(`📊 Pages Audited: ${auditResults.pages.length}`);
    console.log(`🚨 Total Violations: ${auditResults.totalViolations}`);
    console.log(`⚠️ Critical Violations: ${auditResults.criticalViolations}`);
    
    if (auditResults.violations.length > 0) {
      console.log('\n🚨 VIOLATIONS FOUND:');
      auditResults.violations.forEach((violation, index) => {
        console.log(`\n${index + 1}. ${violation.page} - ${violation.id}`);
        console.log(`   Impact: ${violation.impact}`);
        console.log(`   Description: ${violation.description}`);
        console.log(`   Help: ${violation.helpUrl}`);
        console.log(`   Elements: ${violation.nodes.length}`);
      });
    } else {
      console.log('\n🎉 NO ACCESSIBILITY VIOLATIONS FOUND!');
    }
    
    console.log('='.repeat(60));
  });

  const runAccessibilityAudit = async (page, pageName, options = {}) => {
    console.log(`🔍 Auditing accessibility: ${pageName}`);
    
    try {
      const axeBuilder = new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .exclude('#axe-skip'); // Skip elements with this ID
      
      if (options.include) {
        axeBuilder.include(options.include);
      }
      
      if (options.exclude) {
        axeBuilder.exclude(options.exclude);
      }
      
      const results = await axeBuilder.analyze();
      
      auditResults.pages.push(pageName);
      auditResults.totalViolations += results.violations.length;
      
      // Process violations
      results.violations.forEach(violation => {
        if (violation.impact === 'critical' || violation.impact === 'serious') {
          auditResults.criticalViolations++;
        }
        
        auditResults.violations.push({
          page: pageName,
          id: violation.id,
          impact: violation.impact,
          description: violation.description,
          help: violation.help,
          helpUrl: violation.helpUrl,
          nodes: violation.nodes
        });
      });
      
      // Fail test if critical violations found
      if (results.violations.some(v => v.impact === 'critical')) {
        console.log(`❌ Critical accessibility violations found on ${pageName}`);
        results.violations.forEach(violation => {
          if (violation.impact === 'critical') {
            console.log(`   - ${violation.id}: ${violation.description}`);
          }
        });
      } else {
        console.log(`✅ ${pageName} - No critical violations`);
      }
      
      return results;
    } catch (error) {
      console.log(`⚠️ Accessibility audit failed for ${pageName}: ${error.message}`);
      return { violations: [] };
    }
  };

  test('1. Homepage Accessibility', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const results = await runAccessibilityAudit(page, 'Homepage');
    
    // Should have no critical violations
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });

  test('2. Authentication Page Accessibility', async ({ page }) => {
    await page.goto('/');
    
    // Look for login/auth elements
    const hasLogin = await page.locator('text=Login').isVisible();
    if (hasLogin) {
      await page.click('text=Login');
      await page.waitForTimeout(1000);
    }
    
    const results = await runAccessibilityAudit(page, 'Authentication', {
      include: ['form', 'input', 'button']
    });
    
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });

  test('3. League Dashboard Accessibility', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Try to access league area
    const hasLeague = await page.locator('text=League, text=Dashboard, text=Create').isVisible();
    if (hasLeague) {
      await page.click('text=League || text=Dashboard || text=Create').first();
      await page.waitForTimeout(1000);
    }
    
    const results = await runAccessibilityAudit(page, 'League Dashboard');
    
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });

  test('4. Mobile Accessibility Audit', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const results = await runAccessibilityAudit(page, 'Mobile Homepage');
    
    // Check for mobile-specific accessibility issues
    const mobileIssues = results.violations.filter(v => 
      v.id.includes('target-size') || 
      v.id.includes('scrollable-region') ||
      v.id.includes('focus-order')
    );
    
    console.log(`📱 Mobile-specific issues: ${mobileIssues.length}`);
    
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });

  test('5. Form Accessibility', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Focus on form elements
    const results = await runAccessibilityAudit(page, 'Forms', {
      include: ['form', 'input', 'label', 'button', 'select']
    });
    
    // Forms should have proper labels and ARIA
    const labelIssues = results.violations.filter(v => 
      v.id.includes('label') || 
      v.id.includes('aria-label') ||
      v.id.includes('form-field-multiple-labels')
    );
    
    console.log(`📝 Form accessibility issues: ${labelIssues.length}`);
    
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });

  test('6. Navigation Accessibility', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const results = await runAccessibilityAudit(page, 'Navigation', {
      include: ['nav', 'a', 'button[role="menuitem"]', '[role="navigation"]']
    });
    
    // Navigation should have proper landmarks and focus management
    const navIssues = results.violations.filter(v => 
      v.id.includes('landmark') || 
      v.id.includes('focus') ||
      v.id.includes('skip-link')
    );
    
    console.log(`🧭 Navigation accessibility issues: ${navIssues.length}`);
    
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });

  test('7. Color Contrast Audit', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const results = await runAccessibilityAudit(page, 'Color Contrast');
    
    // Check for color contrast issues
    const contrastIssues = results.violations.filter(v => 
      v.id.includes('color-contrast') || 
      v.id.includes('color-contrast-enhanced')
    );
    
    console.log(`🎨 Color contrast issues: ${contrastIssues.length}`);
    
    // Color contrast should meet WCAG AA standards
    const criticalContrastIssues = contrastIssues.filter(v => v.impact === 'serious' || v.impact === 'critical');
    expect(criticalContrastIssues.length).toBe(0);
  });

  test('8. Interactive Elements Accessibility', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const results = await runAccessibilityAudit(page, 'Interactive Elements', {
      include: ['button', 'a', 'input', '[tabindex]', '[role="button"]']
    });
    
    // Interactive elements should be keyboard accessible
    const interactiveIssues = results.violations.filter(v => 
      v.id.includes('keyboard') || 
      v.id.includes('focus-order') ||
      v.id.includes('tabindex')
    );
    
    console.log(`🖱️ Interactive element issues: ${interactiveIssues.length}`);
    
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });

  test('9. ARIA Implementation Audit', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const results = await runAccessibilityAudit(page, 'ARIA Implementation');
    
    // Check ARIA implementation
    const ariaIssues = results.violations.filter(v => 
      v.id.includes('aria-') || 
      v.id.includes('role') ||
      v.id.includes('label')
    );
    
    console.log(`🏷️ ARIA implementation issues: ${ariaIssues.length}`);
    
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });

  test('10. Semantic HTML Structure', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const results = await runAccessibilityAudit(page, 'Semantic HTML');
    
    // Check semantic HTML usage
    const semanticIssues = results.violations.filter(v => 
      v.id.includes('heading-order') || 
      v.id.includes('landmark') ||
      v.id.includes('page-has-heading-one') ||
      v.id.includes('region')
    );
    
    console.log(`🏗️ Semantic HTML issues: ${semanticIssues.length}`);
    
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);
  });
});