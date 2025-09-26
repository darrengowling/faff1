/**
 * Custom ESLint Rules for SSR Safety
 * 
 * Collection of custom rules to prevent SSR-breaking patterns
 * in React applications.
 */

module.exports = {
  rules: {
    'no-window-at-module-scope': require('./no-window-at-module-scope'),
  },
};