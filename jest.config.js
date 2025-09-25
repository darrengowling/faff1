module.exports = {
  testEnvironment: 'node',
  testMatch: [
    '**/tests/unit/**/*.test.js',
    '**/tests/unit/**/*.spec.js'
  ],
  setupFilesAfterEnv: ['<rootDir>/tests/unit/setup.js'],
  globals: {
    'describe': true,
    'test': true,
    'expect': true,
    'beforeEach': true,
    'afterEach': true,
    'beforeAll': true,
    'afterAll': true,
    'jest': true
  }
};