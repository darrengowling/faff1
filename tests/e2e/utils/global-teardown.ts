import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Global E2E Test Teardown Starting...');
  
  // Clean up test data if needed
  // Add any cleanup operations here
  
  console.log('🎉 Global teardown completed!');
}

export default globalTeardown;