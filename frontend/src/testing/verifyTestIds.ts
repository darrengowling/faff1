/**
 * DOM TestID Verifier
 * 
 * Verifies that required testids are present and visible per route.
 * Used for runtime validation of critical UI elements for E2E testing.
 */

import { CRITICAL_ROUTE_TESTIDS } from './critical-routes.ts';

export interface TestIdVerificationResult {
  present: string[];
  missing: string[];
  hidden: string[];
  route: string;
  timestamp: string;
}

/**
 * Check if an element is visible to the user
 * Updated to handle stable DOM patterns where critical elements are kept mounted
 * but hidden via visibility:hidden + aria-hidden="true"
 */
function isElementVisible(element: Element): boolean {
  if (!element) return false;
  
  // Check if element is in the DOM
  if (!document.body.contains(element)) return false;
  
  // Check for explicit hidden attribute
  if (element.hasAttribute('hidden')) return false;
  
  // Check for aria-hidden="true" - these should not count as present
  if (element.getAttribute('aria-hidden') === 'true') return false;
  
  // Check for visually-hidden class (our stable hiding method)
  if (element.classList.contains('visually-hidden')) return false;
  
  const style = window.getComputedStyle(element);
  
  // Check basic visibility properties
  if (style.display === 'none' || 
      style.visibility === 'hidden' || 
      style.opacity === '0') {
    return false;
  }
  
  // Check if element has dimensions
  const rect = element.getBoundingClientRect();
  if (rect.width === 0 && rect.height === 0) {
    return false;
  }
  
  // Element is present and visible
  return true;
}

/**
 * Check if an element is present but intentionally hidden (not counted as "present")
 * This includes elements that are kept in DOM for stability but are not user-visible
 */
function isElementStablyHidden(element: Element): boolean {
  if (!element) return false;
  
  // Check for aria-hidden="true" (stable hiding pattern)
  if (element.getAttribute('aria-hidden') === 'true') return true;
  
  // Check for visually-hidden class (our stable hiding method)
  if (element.classList.contains('visually-hidden')) return true;
  
  // Check for visibility:hidden with stable positioning
  const style = window.getComputedStyle(element);
  if (style.visibility === 'hidden' && 
      (style.position === 'relative' || style.position === 'absolute')) {
    return true;
  }
  
  return false;
}

/**
 * Verify testids for the current route
 */
export function verifyTestIds(route?: string): TestIdVerificationResult {
  const currentRoute = route || window.location.pathname;
  const requiredTestIds = CRITICAL_ROUTE_TESTIDS[currentRoute] || [];
  
  const result: TestIdVerificationResult = {
    present: [],
    missing: [],
    hidden: [],
    route: currentRoute,
    timestamp: new Date().toISOString()
  };
  
  for (const testId of requiredTestIds) {
    const element = document.querySelector(`[data-testid="${testId}"]`);
    
    if (!element) {
      result.missing.push(testId);
    } else if (isElementStablyHidden(element)) {
      // Element is intentionally hidden using stable DOM patterns
      result.hidden.push(testId);
    } else if (!isElementVisible(element)) {
      // Element is present but not visible (traditional hiding)
      result.hidden.push(testId);
    } else {
      result.present.push(testId);
    }
  }
  
  return result;
}

/**
 * Log warnings for missing/hidden testids in development
 */
export function logTestIdIssues(result: TestIdVerificationResult): void {
  if (process.env.NODE_ENV !== 'development') return;
  
  const { route, missing, hidden } = result;
  
  if (missing.length > 0) {
    console.warn(
      `🚨 TestID Verification: Missing testids on route ${route}:`,
      missing.map(id => `data-testid="${id}"`).join(', ')
    );
  }
  
  if (hidden.length > 0) {
    console.warn(
      `⚠️  TestID Verification: Hidden testids on route ${route}:`,
      hidden.map(id => `data-testid="${id}"`).join(', ')
    );
  }
  
  if (missing.length === 0 && hidden.length === 0) {
    console.log(`✅ TestID Verification: All testids present and visible on route ${route}`);
  }
}

/**
 * Verify testids and log issues automatically
 */
export function verifyAndLogTestIds(route?: string): TestIdVerificationResult {
  const result = verifyTestIds(route);
  logTestIdIssues(result);
  return result;
}

/**
 * Set up automatic verification on route changes (React Router)
 */
export function setupRouteVerification(): void {
  if (process.env.NODE_ENV !== 'development') return;
  
  // Initial verification
  setTimeout(() => {
    verifyAndLogTestIds();
  }, 1000);
  
  // Listen for route changes (React Router uses popstate and custom events)
  window.addEventListener('popstate', () => {
    setTimeout(() => {
      verifyAndLogTestIds();
    }, 500);
  });
  
  // Listen for programmatic navigation
  const originalPushState = history.pushState;
  const originalReplaceState = history.replaceState;
  
  history.pushState = function(...args) {
    originalPushState.apply(this, args);
    setTimeout(() => {
      verifyAndLogTestIds();
    }, 500);
  };
  
  history.replaceState = function(...args) {
    originalReplaceState.apply(this, args);
    setTimeout(() => {
      verifyAndLogTestIds();
    }, 500);
  };
}

/**
 * Manual verification trigger for testing
 */
export function manualVerifyTestIds(route?: string): void {
  const result = verifyAndLogTestIds(route);
  
  // Also log a detailed summary
  console.group(`🔍 TestID Verification Results for ${result.route}`);
  console.log(`✅ Present (${result.present.length}):`, result.present);
  if (result.missing.length > 0) {
    console.log(`❌ Missing (${result.missing.length}):`, result.missing);
  }
  if (result.hidden.length > 0) {
    console.log(`👁️ Hidden (${result.hidden.length}):`, result.hidden);
  }
  console.log(`📊 Coverage: ${result.present.length}/${result.present.length + result.missing.length + result.hidden.length} visible`);
  console.groupEnd();
}

// Export for window access in development
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  (window as any).verifyTestIds = manualVerifyTestIds;
  (window as any).testIdVerification = {
    verify: verifyTestIds,
    verifyAndLog: verifyAndLogTestIds,
    manual: manualVerifyTestIds,
    setup: setupRouteVerification
  };
}