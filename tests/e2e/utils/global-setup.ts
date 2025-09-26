import { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🧪 Global E2E Test Setup Starting...');
  
  // Set test environment variables
  process.env.BID_TIMER_SECONDS = '8';
  process.env.ANTI_SNIPE_SECONDS = '3';
  process.env.NEXT_PUBLIC_SOCKET_TRANSPORTS = 'polling,websocket';
  process.env.DISABLE_ANIMATIONS = 'true';
  
  // Check if application is accessible
  const baseURL = config.projects[0].use?.baseURL || 'http://localhost:3000';
  
  try {
    const response = await fetch(baseURL);
    if (response.ok) {
      console.log(`✅ Application accessible at: ${baseURL} (Status: ${response.status})`);
    } else {
      console.error(`❌ Application not accessible: ${response.status}`);
      throw new Error(`Application not accessible at ${baseURL}`);
    }
  } catch (error) {
    console.error(`❌ Failed to connect to application at ${baseURL}:`, error);
    throw error;
  }
  
  console.log('🎉 Global setup completed successfully!');
}

export default globalSetup;