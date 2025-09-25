import js from '@eslint/js';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';

export default [
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
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
      },
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      // Custom rule to forbid magic number 3 for club slots
      'no-magic-numbers': ['warn', {
        ignore: [0, 1, 2, -1],
        ignoreArrayIndexes: true,
        enforceConst: false,
        detectObjects: false,
        ignoreDefaultValues: true
      }],
      ...reactHooks.configs.recommended.rules,
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
        ignoreDefaultValues: true,
      }]
    },
  },
  {
    files: ['**/*.test.js', '**/*.test.jsx', '**/__tests__/**/*', '**/__mocks__/**/*'],
    rules: {
      // Allow magic numbers in tests
      'no-magic-numbers': 'off'
    },
  },
];