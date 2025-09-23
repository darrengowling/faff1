// global-teardown.js
async function globalTeardown(config) {
  console.log('🧹 Global E2E Test Teardown Starting...');
  
  // Any global cleanup can go here
  // Test-specific cleanup should be in individual tests
  
  console.log('🎉 Global teardown completed!');
}

module.exports = globalTeardown;