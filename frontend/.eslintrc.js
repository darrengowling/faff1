module.exports = {
  extends: ['react-app', 'react-app/jest'],
  rules: {
    // Custom rule to forbid magic number 3 for club slots
    'no-magic-numbers': ['warn', {
      ignore: [0, 1, 2, -1],
      ignoreArrayIndexes: true,
      enforceConst: false,
      detectObjects: false,
      ignoreDefaultValues: true
    }]
  },
  overrides: [
    {
      files: ['src/components/**/*.js', 'src/components/**/*.jsx'],
      rules: {
        // Specific rule for club slot magic numbers in UI components
        'no-magic-numbers': ['error', {
          ignore: [0, 1, 2, -1],
          ignoreArrayIndexes: true,
          enforceConst: false,
          detectObjects: false,
          ignoreDefaultValues: true,
          // Custom message for violations
          message: 'Magic number detected. Use useLeagueSettings hook for club slots instead of hardcoded values.'
        }]
      }
    },
    {
      files: ['**/*.test.js', '**/*.test.jsx', '**/__tests__/**/*', '**/__mocks__/**/*'],
      rules: {
        // Allow magic numbers in tests
        'no-magic-numbers': 'off'
      }
    }
  ]
};