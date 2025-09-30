/**
 * Playwright Global Setup
 * 
 * Creates three storage states (commish/alice/bob) for reliable authentication
 * Eliminates auth flake by providing pre-authenticated contexts
 */

import { chromium } from '@playwright/test';
import path from 'path';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://test-harmony.preview.emergentagent.com';
const FRONTEND_URL = process.env.FRONTEND_URL || 'https://test-harmony.preview.emergentagent.com';

// Test users with deterministic data
const TEST_USERS = [
  {
    name: 'commish',
    email: 'commish@example.com',
    displayName: 'Commissioner',
    storageFile: 'commish-storage.json'
  },
  {
    name: 'alice', 
    email: 'alice@example.com',
    displayName: 'Alice',
    storageFile: 'alice-storage.json'
  },
  {
    name: 'bob',
    email: 'bob@example.com', 
    displayName: 'Bob',
    storageFile: 'bob-storage.json'
  }
];

/**
 * Authenticate a user and save storage state
 */
async function createUserStorageState(user, browser) {
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`🧪 Creating storage state for ${user.name} (${user.email})...`);

    // Navigate to frontend to ensure proper domain context
    await page.goto(FRONTEND_URL);
    await page.waitForTimeout(1000); // Allow page to load

    // Call test-login API directly
    const response = await page.request.post(`${BACKEND_URL}/api/auth/test-login`, {
      data: {
        email: user.email
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok()) {
      const responseText = await response.text();
      throw new Error(`Test login failed for ${user.email}: ${response.status()} - ${responseText}`);
    }

    const responseData = await response.json();
    
    if (!responseData.ok) {
      throw new Error(`Test login unsuccessful for ${user.email}: ${JSON.stringify(responseData)}`);
    }

    console.log(`✅ Test login successful for ${user.email}, userId: ${responseData.userId}`);

    // Navigate to a protected page to verify authentication
    await page.goto(`${FRONTEND_URL}/app`);
    
    // Wait for auth to be verified (wait for user data or dashboard elements)
    try {
      // Wait for either dashboard content or profile element (signs of successful auth)
      await page.waitForSelector('[data-testid="dashboard-content"], [data-testid="user-profile"], .user-info', { 
        timeout: 10000 
      });
      console.log(`✅ Authentication verified for ${user.email} - protected page accessible`);
    } catch (error) {
      console.warn(`⚠️ Could not verify dashboard access for ${user.email}, but proceeding with storage save`);
    }

    // Save storage state
    const storageStatePath = path.join(__dirname, 'storage-states', user.storageFile);
    await context.storageState({ path: storageStatePath });
    
    console.log(`✅ Storage state saved for ${user.name}: ${storageStatePath}`);

  } catch (error) {
    console.error(`❌ Failed to create storage state for ${user.name}:`, error);
    throw error;
  } finally {
    await context.close();
  }
}

/**
 * Main global setup function
 */
async function globalSetup() {
  console.log('🧪 PLAYWRIGHT GLOBAL SETUP: Starting authentication setup...');
  console.log(`Frontend URL: ${FRONTEND_URL}`);
  console.log(`Backend URL: ${BACKEND_URL}`);

  const browser = await chromium.launch();

  try {
    // Ensure storage-states directory exists
    const storageDir = path.join(__dirname, 'storage-states');
    const fs = require('fs');
    if (!fs.existsSync(storageDir)) {
      fs.mkdirSync(storageDir, { recursive: true });
      console.log(`📁 Created storage-states directory: ${storageDir}`);
    }

    // Create storage states for all test users
    for (const user of TEST_USERS) {
      await createUserStorageState(user, browser);
      
      // Small delay between user creations
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    console.log('✅ PLAYWRIGHT GLOBAL SETUP: All storage states created successfully');
    
  } catch (error) {
    console.error('❌ PLAYWRIGHT GLOBAL SETUP: Failed to create storage states:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;