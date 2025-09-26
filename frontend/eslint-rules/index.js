/**
 * Custom ESLint Rules for SSR Safety
 * 
 * Collection of custom rules to prevent SSR-breaking patterns
 * in React applications.
 */

import noWindowAtModuleScope from './no-window-at-module-scope.js';

export default {
  rules: {
    'no-window-at-module-scope': noWindowAtModuleScope,
  },
};