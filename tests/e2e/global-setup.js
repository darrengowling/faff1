// global-setup.js
async function globalSetup(config) {
  console.log('🚀 Global E2E Test Setup Starting...');
  
  // Check if application is accessible using built-in fetch
  const baseURL = config.use.baseURL;
  
  try {
    const response = await fetch(baseURL, { 
      method: 'GET',
      headers: { 'User-Agent': 'Playwright-Test' }
    });
    console.log(`✅ Application accessible at: ${baseURL} (Status: ${response.status})`);
  } catch (error) {
    console.log(`⚠️ Application check: ${error.message} (will proceed anyway)`);
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