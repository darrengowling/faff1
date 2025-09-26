/**
 * E2E Test Helpers
 * Deterministic, stable helper functions using only data-testid selectors
 */

import { Page, expect, Locator } from '@playwright/test';
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
  await page.locator(`[data-testid="${TESTIDS.emailInput}"]`).fill(email);
  await page.locator(`[data-testid="${TESTIDS.magicLinkSubmit}"]`).click();
  
  // Wait for magic link sent confirmation and click login button using test ID
  await page.locator(`[data-testid="${TESTIDS.loginNowButton}"]`).waitFor({ state: 'visible', timeout: 10000 });
  await page.locator(`[data-testid="${TESTIDS.loginNowButton}"]`).click();
  
  // Wait for successful login redirect
  await page.waitForURL('**/app', { timeout: 15000 });
  console.log(`✅ User logged in: ${email}`);
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

export async function createLeague(page: Page, settings: LeagueSettings): Promise<string> {
  console.log(`🏆 Creating league: ${settings.name}`);
  
  // Open create league dialog
  await page.locator(`[data-testid="${TESTIDS.landingCtaCreate}"]`).click();
  await page.locator(`[data-testid="${TESTIDS.createDialog}"]`).waitFor({ state: 'visible' });
  
  // Fill form fields
  await page.locator(`[data-testid="${TESTIDS.createNameInput}"]`).fill(settings.name);
  await page.locator(`[data-testid="${TESTIDS.createSlotsInput}"]`).fill(settings.clubSlots.toString());
  await page.locator(`[data-testid="${TESTIDS.createBudgetInput}"]`).fill(settings.budgetPerManager.toString());
  await page.locator(`[data-testid="${TESTIDS.createMinInput}"]`).fill(settings.minManagers.toString());
  await page.locator(`[data-testid="${TESTIDS.createMaxInput}"]`).fill(settings.maxManagers.toString());
  
  // Submit form
  await page.locator(`[data-testid="${TESTIDS.createSubmit}"]`).click();
  
  // Wait for success and extract league ID from URL
  await page.waitForURL('**/leagues/**', { timeout: 15000 });
  const url = page.url();
  const leagueId = url.split('/leagues/')[1]?.split('/')[0] || '';
  
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
  
  // Click join button
  await page.locator(`[data-testid="${TESTIDS.joinLeagueButton}"]`).click();
  
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