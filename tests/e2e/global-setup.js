// global-setup.js
async function globalSetup(config) {
  console.log('🚀 Global E2E Test Setup Starting...');
  
  // Check if application is accessible
  const axios = require('axios');
  const baseURL = config.use.baseURL;
  
  try {
    const response = await axios.get(baseURL, { timeout: 10000 });
    console.log(`✅ Application accessible at: ${baseURL}`);
  } catch (error) {
    console.error(`❌ Application not accessible at: ${baseURL}`);
    console.error('Error:', error.message);
    process.exit(1);
  }
  
  // Create screenshots directory
  const fs = require('fs');
  const path = require('path');
  
  const screenshotsDir = path.join(__dirname, '../../test-results/screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }
  
  console.log('🎉 Global setup completed successfully!');
}

module.exports = globalSetup;