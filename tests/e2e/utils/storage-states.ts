/**
 * Storage State Utilities
 * Helper functions for working with authenticated storage states
 */

import { Browser, BrowserContext } from '@playwright/test';

export interface StorageStateUser {
  email: string;
  filename: string;
  description: string;
}

export const STORAGE_STATE_USERS: Record<string, StorageStateUser> = {
  commissioner: {
    email: 'commish@test.local',
    filename: 'test-results/commissioner-state.json',
    description: 'Commissioner user (can create leagues)'
  },
  alice: {
    email: 'alice@test.local', 
    filename: 'test-results/alice-state.json',
    description: 'Alice user (regular participant)'
  },
  bob: {
    email: 'bob@test.local',
    filename: 'test-results/bob-state.json', 
    description: 'Bob user (regular participant)'
  }
};

/**
 * Create an authenticated browser context using a storage state
 */
export async function createAuthenticatedContext(
  browser: Browser, 
  userKey: keyof typeof STORAGE_STATE_USERS,
  baseURL?: string
): Promise<BrowserContext> {
  const user = STORAGE_STATE_USERS[userKey];
  if (!user) {
    throw new Error(`Unknown user key: ${userKey}`);
  }
  
  console.log(`🔐 Creating authenticated context for ${user.description}`);
  
  return await browser.newContext({
    storageState: user.filename,
    baseURL
  });
}

/**
 * Get the email for a storage state user
 */
export function getUserEmail(userKey: keyof typeof STORAGE_STATE_USERS): string {
  const user = STORAGE_STATE_USERS[userKey];
  if (!user) {
    throw new Error(`Unknown user key: ${userKey}`);
  }
  return user.email;
}