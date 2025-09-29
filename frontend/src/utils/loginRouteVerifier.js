/**
 * Pre-gate Route Verifier for /login
 * 
 * Verifies that critical testids are visible before any auth guards/redirects
 * Prevents timeout issues in auth_ui.spec.ts
 */

import { TESTIDS } from '../testids';

export const verifyLoginRoute = () => {
  return new Promise((resolve, reject) => {
    // Wait for a short period to allow elements to render
    setTimeout(() => {
      const requiredTestIds = [
        TESTIDS.loginHeader,        // login-header on H1
        TESTIDS.authReady,         // auth-ready on form
        TESTIDS.authEmailInput,    // authEmailInput on input
        TESTIDS.authSubmitBtn,     // authSubmitBtn on submit button
        TESTIDS.backToHomeLink     // back-to-home-link
      ];

      const results = {
        passed: [],
        failed: [],
        visible: true
      };

      for (const testId of requiredTestIds) {
        const element = document.querySelector(`[data-testid="${testId}"]`);
        
        if (!element) {
          results.failed.push(`${testId}: Element not found`);
        } else {
          // Check if element is visible (not hidden, has dimensions, not opacity 0)
          const computedStyle = window.getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          
          const isVisible = (
            computedStyle.display !== 'none' &&
            computedStyle.visibility !== 'hidden' &&
            computedStyle.opacity !== '0' &&
            rect.width > 0 &&
            rect.height > 0
          );
          
          if (isVisible) {
            results.passed.push(`${testId}: ✅ Visible`);
          } else {
            results.failed.push(`${testId}: ❌ Element found but not visible (display: ${computedStyle.display}, visibility: ${computedStyle.visibility}, opacity: ${computedStyle.opacity}, dimensions: ${rect.width}x${rect.height})`);
          }
        }
      }

      if (results.failed.length === 0) {
        console.log('✅ Pre-gate route verification passed for /login:', results.passed);
        resolve(results);
      } else {
        console.error('❌ Pre-gate route verification failed for /login:', results.failed);
        results.visible = false;
        reject(results);
      }
    }, 50); // 50ms delay to allow first render
  });
};

export const runLoginRouteVerification = () => {
  if (window.location.pathname === '/login') {
    verifyLoginRoute()
      .then(() => {
        console.log('🧪 Login route verification: All required testids are visible');
      })
      .catch((results) => {
        console.warn('🧪 Login route verification: Some testids missing or not visible', results.failed);
      });
  }
};

export default {
  verifyLoginRoute,
  runLoginRouteVerification
};