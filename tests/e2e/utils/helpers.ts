/**
 * E2E Test Helpers
 * Deterministic, stable helper functions using only data-testid selectors
 */

import { Page, expect, Locator } from '@playwright/test';
import { ensureClickable, clickWhenReady } from './ensureClickable';
import { safeClick, ensureClickable as checkClickable } from './click-interceptor-detector';
import { TESTIDS } from '../../../frontend/src/testids.js';

/**
 * Authentication helpers
 */
export async function login(page: Page, email: string): Promise<void> {
  console.log(`🔐 Logging in user: ${email}`);
  
  // Navigate to login page
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  
  // Fill email and submit magic link form using test IDs
  const emailInput = page.locator(`[data-testid="${TESTIDS.authEmailInput}"]`);
  const submitBtn = page.locator(`[data-testid="${TESTIDS.authSubmitBtn}"]`);
  
  await emailInput.fill(email);
  
  // Wait for button to be enabled (my validation might be disabling it)
  await expect(submitBtn).toBeEnabled({ timeout: 5000 });
  console.log(`Submit button enabled for email: ${email}`);
  
  // Use safe click to detect any UI interception
  await safeClick(page, submitBtn);
  
  // Wait for success message to appear (indicates backend processing complete)
  await page.locator(`[data-testid="${TESTIDS.authSuccess}"]`).waitFor({ state: 'visible', timeout: 10000 });
  
  // Check if dev magic link button appears (conditional in development mode)
  const devMagicBtn = page.locator('[data-testid="dev-magic-link-btn"]');
  if (await devMagicBtn.isVisible()) {
    console.log('Dev magic link button found, using safe click...');
    await safeClick(page, devMagicBtn);
  } else {
    // In test mode, should automatically redirect - wait for it
    console.log('Waiting for automatic redirect...');
  }
  
  // Wait for successful login redirect (either manual click or automatic)
  await page.waitForURL(url => url.pathname === '/auth/verify' || url.pathname === '/dashboard', { timeout: 15000 });
  console.log(`✅ User logged in: ${email}`);
}

/**
 * Test-only login helper that bypasses UI authentication
 * Only works when ALLOW_TEST_LOGIN=true is set on the backend
 * @deprecated Use login() from utils/login.ts instead
 */
export async function loginTestOnly(page: Page, email: string): Promise<void> {
  // Delegate to the new login utility
  const { login } = await import('./login');
  await login(page, email, { mode: 'test' });
}

/**
 * League creation helpers
 */
export interface LeagueSettings {
  name: string;
  clubSlots: number;
  budgetPerManager: number;
  minManagers: number;
  maxManagers: number;
}

/**
 * Click Create League button from multiple possible entry points
 * Tries both dashboard and navigation buttons
 */
export async function clickCreateLeague(page: Page): Promise<void> {
  // Wait for page to be fully loaded and components to render
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000); // Increased wait time
  
  const btns = [
    page.getByTestId('create-league-btn'),
    page.getByTestId('nav-create-league-btn')
  ];
  
  for (const b of btns) {
    try {
      const count = await b.count();
      if (count > 0) {
        const firstBtn = b.first();
        const isVisible = await firstBtn.isVisible();
        if (isVisible) {
          console.log('🎯 Using safe click for Create League button...');
          await safeClick(page, firstBtn);
          return;
        }
      }
    } catch (e) {
      console.log(`Failed to click button: ${e.message}`);
    }
  }
  
  throw new Error('Create League CTA not found');
}

export async function createLeague(page: Page, settings: LeagueSettings): Promise<string> {
  console.log(`🏆 Creating league: ${settings.name}`);
  
  // Open create league dialog from dashboard
  // Look for Create League button on dashboard
  const createBtn = page.locator('button').filter({ hasText: /create.*league/i }).first();
  await safeClick(page, createBtn);
  await page.locator(`[data-testid="${TESTIDS.createDialog}"]`).waitFor({ state: 'visible' });
  
  // Fill form fields
  await page.locator(`[data-testid="${TESTIDS.createNameInput}"]`).fill(settings.name);
  await page.locator(`[data-testid="${TESTIDS.createSlotsInput}"]`).fill(settings.clubSlots.toString());
  await page.locator(`[data-testid="${TESTIDS.createBudgetInput}"]`).fill(settings.budgetPerManager.toString());
  await page.locator(`[data-testid="${TESTIDS.createMinInput}"]`).fill(settings.minManagers.toString());
  await page.locator(`[data-testid="${TESTIDS.createMaxInput}"]`).fill(settings.maxManagers.toString());
  
  // Submit form using safe click
  const submitBtn = page.locator(`[data-testid="${TESTIDS.createSubmit}"]`);
  await safeClick(page, submitBtn);
  
  // Wait for dialog to close (indicates success)
  await page.locator(`[data-testid="${TESTIDS.createDialog}"]`).waitFor({ state: 'hidden', timeout: 15000 });
  
  // Wait a moment for the league list to update
  await page.waitForTimeout(2000);
  
  // Verify the league appears in the dashboard (use first occurrence to avoid strict mode violation)
  const leagueVisible = await page.locator(`text="${settings.name}"`).first().isVisible();
  if (!leagueVisible) {
    throw new Error(`League "${settings.name}" was not found in the dashboard after creation`);
  }
  
  // For now, return a placeholder ID since we don't navigate to a league-specific URL
  // In a real implementation, we'd need to extract the league ID from the API response or DOM
  const leagueId = `created-${Date.now()}`;
  
  console.log(`✅ League created: ${settings.name} (ID: ${leagueId})`);
  return leagueId;
}

/**
 * Invitation helpers
 */
export async function getInviteLinks(page: Page): Promise<string[]> {
  console.log('📧 Getting invite links...');
  
  const inviteLinks: string[] = [];
  
  // Get first invite link
  const inviteLink = await page.locator(`[data-testid="${TESTIDS.inviteLinkUrl}"]`).first().textContent();
  if (inviteLink) {
    inviteLinks.push(inviteLink.trim());
  }
  
  // Generate second invite link if needed
  if (inviteLinks.length === 1) {
    // Create additional invite by sending to test email
    await page.locator(`[data-testid="${TESTIDS.inviteEmailInput}"]`).fill('test2@example.com');
    await page.locator(`[data-testid="${TESTIDS.inviteSubmitButton}"]`).click();
    
    // Wait for new invite to appear and get the link
    await page.waitForTimeout(2000);
    const secondInvite = await page.locator(`[data-testid="${TESTIDS.inviteLinkUrl}"]`).nth(1).textContent();
    if (secondInvite) {
      inviteLinks.push(secondInvite.trim());
    }
  }
  
  console.log(`✅ Retrieved ${inviteLinks.length} invite links`);
  return inviteLinks;
}

export async function joinViaInvite(page: Page, inviteLink: string): Promise<void> {
  console.log(`🤝 Joining league via invite link...`);
  
  // Navigate to invite link
  await page.goto(inviteLink);
  await page.waitForLoadState('networkidle');
  
  // Click join button using safe click
  const joinBtn = page.locator(`[data-testid="${TESTIDS.joinLeagueButton}"]`);
  await safeClick(page, joinBtn);
  
  // Wait for success message
  await page.locator(`[data-testid="${TESTIDS.joinSuccessMessage}"]`).waitFor({ state: 'visible', timeout: 10000 });
  
  console.log('✅ Successfully joined league');
}

/**
 * Auction helpers
 */
export async function startAuction(page: Page): Promise<void> {
  console.log('🔨 Starting auction...');
  
  // Wait for start auction button to be enabled
  const startButton = page.locator(`[data-testid="${TESTIDS.startAuctionBtn}"]`);
  await expect(startButton).toBeEnabled({ timeout: 10000 });
  
  // Click start auction
  await startButton.click();
  
  // Wait for auction room to load
  await page.locator(`[data-testid="${TESTIDS.auctionRoom}"]`).waitFor({ state: 'visible', timeout: 15000 });
  
  console.log('✅ Auction started successfully');
}

export async function nominateFirstAsset(page: Page): Promise<string> {
  console.log('🎯 Nominating first asset...');
  
  // Click nominate button
  await page.locator(`[data-testid="${TESTIDS.nominateBtn}"]`).click();
  
  // Select first available asset from dropdown
  const nominateSelect = page.locator(`[data-testid="${TESTIDS.nominateSelect}"]`);
  await nominateSelect.waitFor({ state: 'visible' });
  await nominateSelect.selectOption({ index: 0 });
  
  // Submit nomination
  await page.locator(`[data-testid="${TESTIDS.nominateSubmit}"]`).click();
  
  // Wait for asset to appear in auction
  await page.locator(`[data-testid="${TESTIDS.auctionAssetName}"]`).waitFor({ state: 'visible' });
  
  const assetName = await page.locator(`[data-testid="${TESTIDS.auctionAssetName}"]`).textContent() || '';
  
  console.log(`✅ Nominated asset: ${assetName}`);
  return assetName;
}

export async function bid(page: Page, amount: number): Promise<void> {
  console.log(`💰 Placing bid: ${amount}`);
  
  // Use bid input or quick bid buttons
  if (amount <= 10) {
    // Use quick bid buttons for small amounts
    const bidButton = amount === 1 ? TESTIDS.bidPlus1 : amount === 5 ? TESTIDS.bidPlus5 : TESTIDS.bidPlus10;
    await page.locator(`[data-testid="${bidButton}"]`).click();
  } else {
    // Use manual input for larger amounts
    await page.locator(`[data-testid="${TESTIDS.bidInput}"]`).fill(amount.toString());
    await page.locator(`[data-testid="${TESTIDS.bidSubmit}"]`).click();
  }
  
  // Wait for top bid to update
  await expect(page.locator(`[data-testid="${TESTIDS.auctionTopBid}"]`)).toContainText(amount.toString(), { timeout: 5000 });
  
  console.log(`✅ Bid placed: ${amount}`);
}

/**
 * Verification helpers
 */
export async function waitForSoldBadge(page: Page): Promise<void> {
  console.log('⏳ Waiting for lot to be sold...');
  
  await page.locator(`[data-testid="${TESTIDS.soldBadge}"]`).waitFor({ state: 'visible', timeout: 15000 });
  
  console.log('✅ Lot sold successfully');
}

export async function verifyRosterCount(page: Page, expectedCount: number): Promise<void> {
  console.log(`🔍 Verifying roster count: ${expectedCount}`);
  
  const rosterItems = page.locator(`[data-testid="${TESTIDS.rosterItem}"]`);
  await expect(rosterItems).toHaveCount(expectedCount, { timeout: 10000 });
  
  console.log(`✅ Roster count verified: ${expectedCount}`);
}

export async function verifyBudgetAmount(page: Page, expectedAmount: number): Promise<void> {
  console.log(`🔍 Verifying budget amount: ${expectedAmount}`);
  
  const budgetDisplay = page.locator(`[data-testid="${TESTIDS.budgetRemaining}"]`);
  await expect(budgetDisplay).toContainText(expectedAmount.toString(), { timeout: 10000 });
  
  console.log(`✅ Budget amount verified: ${expectedAmount}`);
}

/**
 * Navigation helpers
 */
export async function navigateToRoster(page: Page): Promise<void> {
  await page.locator(`[data-testid="${TESTIDS.navDropdownItemRoster}"]`).click();
  await page.waitForURL('**/clubs/**', { timeout: 10000 });
}

export async function navigateToLeaderboard(page: Page): Promise<void> {
  await page.locator(`[data-testid="${TESTIDS.navDropdownItemLeaderboard}"]`).click();
  await page.waitForURL('**/leaderboard/**', { timeout: 10000 });
}

export async function navigateToFixtures(page: Page): Promise<void> {
  await page.locator(`[data-testid="${TESTIDS.navDropdownItemFixtures}"]`).click();
  await page.waitForURL('**/fixtures/**', { timeout: 10000 });
}

/**
 * Wait for specific test conditions
 */
export async function waitForJoinedCount(page: Page, count: number): Promise<void> {
  console.log(`⏳ Waiting for ${count} members to join...`);
  
  await expect(page.locator(`[data-testid="${TESTIDS.lobbyJoinedCount}"]`))
    .toContainText(`${count}`, { timeout: 30000 });
  
  console.log(`✅ ${count} members joined`);
}

/**
 * Error handling and debugging
 */
export async function captureDebugInfo(page: Page, testName: string): Promise<void> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  
  // Screenshot
  await page.screenshot({ 
    path: `test-results/debug-${testName}-${timestamp}.png`,
    fullPage: true 
  });
  
  // Console logs
  const logs = await page.evaluate(() => {
    return (window as any).testLogs || [];
  });
  
  console.log(`📸 Debug info captured for ${testName}:`, {
    url: page.url(),
    logs: logs.slice(-10) // Last 10 logs
  });
}