export default [
  {
    files: ['**/*.{js,jsx}'],
    plugins: {
      'ssr-safety': require('./eslint-rules/index.js')
    },
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        process: 'readonly',
        Buffer: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        module: 'readonly',
        require: 'readonly',
        exports: 'readonly',
        global: 'readonly',
        React: 'readonly',
      },
    },
    rules: {
      // SSR Safety: Prevent module-scope browser API usage
      'ssr-safety/no-window-at-module-scope': 'error',
      
      // Custom rule to forbid magic number 3 for club slots
      'no-magic-numbers': ['warn', {
        ignore: [0, 1, 2, -1],
        ignoreArrayIndexes: true,
        enforceConst: false,
        detectObjects: false,
        ignoreDefaultValues: true
      }]
    },
  },
  {
    files: ['src/components/**/*.js', 'src/components/**/*.jsx'],
    rules: {
      // Specific rule for club slot magic numbers in UI components
      'no-magic-numbers': ['error', {
        ignore: [0, 1, 2, -1],
        ignoreArrayIndexes: true,
        enforceConst: false,
        detectObjects: false,
        ignoreDefaultValues: false, // Changed to false to catch variable assignments
      }]
    },
  },
  {
    files: ['**/*.test.js', '**/*.test.jsx', '**/__tests__/**/*', '**/__mocks__/**/*'],
    rules: {
      // Allow magic numbers in tests
      'no-magic-numbers': 'off',
      // Allow browser globals in tests  
      'ssr-safety/no-window-at-module-scope': 'off'
    },
  },
  {
    files: ['scripts/**/*.js', 'scripts/**/*.jsx', 'public/**/*.js'],
    rules: {
      // Allow browser globals in scripts and public files
      'ssr-safety/no-window-at-module-scope': 'off'
    },
  },
];