/**
 * Custom ESLint Rules for SSR Safety
 * 
 * Collection of custom rules to prevent SSR-breaking patterns
 * in React applications.
 */

const noWindowAtModuleScope = require('./no-window-at-module-scope.js');

module.exports = {
  rules: {
    'no-window-at-module-scope': noWindowAtModuleScope,
  },
};