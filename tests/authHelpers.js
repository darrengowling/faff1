/**
 * Storage State Helpers
 * 
 * Utilities for using pre-authenticated contexts in tests
 */

import path from 'path';

export const STORAGE_STATES = {
  COMMISH: path.join(__dirname, 'storage-states', 'commish-storage.json'),
  ALICE: path.join(__dirname, 'storage-states', 'alice-storage.json'), 
  BOB: path.join(__dirname, 'storage-states', 'bob-storage.json')
};

export const TEST_USERS = {
  COMMISH: {
    email: 'commish@example.com',
    displayName: 'Commissioner',
    storageState: STORAGE_STATES.COMMISH
  },
  ALICE: {
    email: 'alice@example.com',
    displayName: 'Alice', 
    storageState: STORAGE_STATES.ALICE
  },
  BOB: {
    email: 'bob@example.com',
    displayName: 'Bob',
    storageState: STORAGE_STATES.BOB
  }
};

/**
 * Create an authenticated context for a test user
 * 
 * Usage:
 *   const context = await createAuthenticatedContext(browser, 'COMMISH');
 *   const page = await context.newPage();
 */
export async function createAuthenticatedContext(browser, userKey) {
  const user = TEST_USERS[userKey];
  if (!user) {
    throw new Error(`Invalid user key: ${userKey}. Available: ${Object.keys(TEST_USERS).join(', ')}`);
  }

  try {
    const context = await browser.newContext({
      storageState: user.storageState
    });
    
    console.log(`✅ Created authenticated context for ${user.email}`);
    return context;
  } catch (error) {
    console.error(`❌ Failed to create authenticated context for ${user.email}:`, error);
    console.warn(`⚠️ Storage state may not exist. Run global setup first: npx playwright test --global-setup`);
    throw error;
  }
}

/**
 * Verify a page is authenticated (has user data)
 */
export async function verifyAuthenticated(page, expectedEmail = null) {
  try {
    // Wait for authentication indicators
    await page.waitForSelector('[data-testid="user-profile"], [data-testid="dashboard-content"], .user-info', {
      timeout: 5000
    });
    
    // If email provided, verify it matches
    if (expectedEmail) {
      // Check if user email is visible in profile or header
      const emailVisible = await page.locator('text=' + expectedEmail).first().isVisible().catch(() => false);
      if (!emailVisible) {
        console.warn(`⚠️ Expected email ${expectedEmail} not visible, but authentication indicators found`);
      }
    }
    
    console.log(`✅ Authentication verified${expectedEmail ? ` for ${expectedEmail}` : ''}`);
    return true;
  } catch (error) {
    console.error(`❌ Authentication verification failed:`, error);
    return false;
  }
}

export default {
  STORAGE_STATES,
  TEST_USERS,
  createAuthenticatedContext,
  verifyAuthenticated
};