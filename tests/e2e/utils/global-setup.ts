import { FullConfig, chromium } from '@playwright/test';
import { login } from './login';

async function globalSetup(config: FullConfig) {
  console.log('🧪 Global E2E Test Setup Starting...');
  
  // Set test environment variables
  process.env.BID_TIMER_SECONDS = '8';
  process.env.ANTI_SNIPE_SECONDS = '3';
  process.env.NEXT_PUBLIC_SOCKET_TRANSPORTS = 'polling,websocket';
  process.env.DISABLE_ANIMATIONS = 'true';
  
  // Pre-check: Verify TESTIDS can be imported
  console.log('🔍 Pre-check: Verifying TESTIDS import...');
  try {
    const testidsModule = await import('../../../frontend/src/testids.ts');
    const TESTIDS = testidsModule.TESTIDS || testidsModule.default;
    
    if (!TESTIDS || typeof TESTIDS !== 'object') {
      throw new Error('TESTIDS is not an object or is missing');
    }
    
    const testidCount = Object.keys(TESTIDS).length;
    
    if (testidCount === 0) {
      throw new Error('TESTIDS is empty');
    }
    
    console.log(`✅ TESTIDS imported successfully: ${testidCount} testids available`);
    
    // Log first few testids for verification
    const firstFew = Object.keys(TESTIDS).slice(0, 5);
    console.log(`   Sample testids: ${firstFew.join(', ')}...`);
    
  } catch (error) {
    console.error('❌ TESTIDS import failed:', error);
    throw new Error(`TESTIDS import failed: ${error.message}`);
  }
  
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
  
  // Create authenticated storage states for test users
  console.log('🔐 Creating authenticated storage states...');
  const testUsers = [
    { email: 'commish@example.com', filename: 'commissioner-state.json' },
    { email: 'alice@example.com', filename: 'alice-state.json' },
    { email: 'bob@example.com', filename: 'bob-state.json' }
  ];
  
  const browser = await chromium.launch();
  
  for (const user of testUsers) {
    try {
      console.log(`🔑 Authenticating ${user.email}...`);
      const context = await browser.newContext({ baseURL });
      const page = await context.newPage();
      
      // Perform test login
      await login(page, user.email, { mode: 'test' });
      
      // Verify authentication by checking for user state
      try {
        await page.goto('/app');
        await page.waitForTimeout(2000); // Give time for auth to settle
        
        // Check if we're authenticated (not redirected to login)
        const currentUrl = page.url();
        if (currentUrl.includes('/login')) {
          throw new Error(`Authentication failed for ${user.email} - redirected to login`);
        }
        
        console.log(`✅ ${user.email} authenticated successfully`);
      } catch (authError) {
        console.warn(`⚠️ Auth verification failed for ${user.email}: ${authError.message}`);
        // Continue anyway - storage state may still be useful
      }
      
      // Save storage state
      await context.storageState({ path: `test-results/${user.filename}` });
      console.log(`💾 Storage state saved: test-results/${user.filename}`);
      
      await context.close();
    } catch (error) {
      console.error(`❌ Failed to create storage state for ${user.email}:`, error);
      // Continue with other users - don't fail the entire setup
    }
  }
  
  await browser.close();
  console.log('🎉 Global setup completed successfully!');
}

export default globalSetup;