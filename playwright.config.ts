import { defineConfig, devices } from '@playwright/test';

/**
 * Deterministic Playwright Configuration
 * Zero retries, stable selectors only, comprehensive artifacts on failure
 */
export default defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Parallel execution
  fullyParallel: false, // Disable for deterministic database state
  forbidOnly: !!process.env.CI,
  
  // Zero retries - tests must be stable
  retries: 0,
  
  // Workers
  workers: process.env.CI ? 2 : 1,
  
  // Reporter configuration
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }]
  ],
  
  // Global test configuration
  use: {
    // Base URL from environment
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'https://leaguemate-1.preview.emergentagent.com',
    
    // Browser context
    headless: true, // Always run headless in container
    
    // Timeouts
    actionTimeout: 10000,
    navigationTimeout: 30000,
    
    // Artifacts on failure
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // Disable animations for stable tests
    reducedMotion: 'reduce',
    
    // Locale
    locale: 'en-US',
    timezoneId: 'America/New_York',
  },
  
  // Test timeout
  timeout: 60000,
  
  // Expect timeout
  expect: {
    timeout: 6000, // 6s unified expect timeout
  },
  
  // Global setup and teardown
  globalSetup: require.resolve('./tests/e2e/utils/global-setup.ts'),
  globalTeardown: require.resolve('./tests/e2e/utils/global-teardown.ts'),
  
  // Projects for different browsers (only Chromium for container environment)
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    }
  ],
  
  // Output directory
  outputDir: 'test-results/',
  
  // Web server configuration (if needed)
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});