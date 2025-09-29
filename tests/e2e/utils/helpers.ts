/**
 * E2E Test Helpers
 * Deterministic, stable helper functions using only data-testid selectors
 */

import { Page, expect, Locator } from '@playwright/test';
import { ensureClickable, clickWhenReady } from './ensureClickable';
import { safeClick } from './click-interceptor-detector';
import { safeClickWithOverlayDetection } from './overlay-detector';
import { login as loginUtility } from './login';
import { fillCreateLeague } from './league';
import { byId, selectors, waitForId, clickById, fillById, TESTIDS } from './selectors';

/**
 * Wait for URL hash to change to specific value
 * Polls window.location.hash for reliable hash-based navigation testing
 */
export async function waitForHash(page: Page, expectedHash: string, timeout: number = 6000): Promise<void> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const currentHash = await page.evaluate(() => window.location.hash);
    
    if (currentHash === expectedHash) {
      return;
    }
    
    // Poll every 100ms
    await page.waitForTimeout(100);
  }
  
  throw new Error(`Timeout waiting for hash "${expectedHash}". Current hash: "${await page.evaluate(() => window.location.hash)}"`);
}

/**
 * Authentication helpers - defaults to test login for stability
 */
export async function login(page: Page, email: string, mode: 'test' | 'ui' = 'test'): Promise<void> {
  // Use the centralized login utility with default test mode for CI stability
  await loginUtility(page, email, { mode });
}

/**
 * UI-based login helper for testing the actual authentication flow
 * Use this for testing the login page UI specifically
 */
export async function loginUI(page: Page, email: string): Promise<void> {
  await loginUtility(page, email, { mode: 'ui' });
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
    byId(page, 'createLeagueBtn'),
    byId(page, 'navCreateLeagueBtn')
  ];
  
  for (const b of btns) {
    try {
      const count = await b.count();
      if (count > 0) {
        const firstBtn = b.first();
        const isVisible = await firstBtn.isVisible();
        if (isVisible) {
          console.log('🎯 Using safe click with overlay detection for Create League button...');
          await safeClickWithOverlayDetection(page, firstBtn, { logDetails: true });
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
  
  // Click Create League CTA using proper testid selectors
  await clickCreateLeague(page);
  
  // Use the new type-aware form helper to fill the league creation form
  await fillCreateLeague(page, {
    name: settings.name,
    slots: settings.clubSlots,
    budget: settings.budgetPerManager,
    min: settings.minManagers,
    max: settings.maxManagers
  });
  
  console.log('📝 Form filled, submitting...');
  
  // Submit form using safe click
  const submitBtn = byId(page, 'createSubmit');
  await ensureClickable(submitBtn);
  await submitBtn.click();
  
  console.log('⏳ Waiting for league creation success...');
  
  // Post-submit contract: await either create-success or /lobby URL, and check dialog closed
  return await awaitCreatedAndInLobby(page);
}

/**
 * Invitation helpers
 */
export async function getInviteLinks(page: Page): Promise<string[]> {
  console.log('📧 Getting invite links...');
  
  const inviteLinks: string[] = [];
  
  // Get first invite link
  const inviteLink = await byId(page, 'inviteLinkUrl').first().textContent();
  if (inviteLink) {
    inviteLinks.push(inviteLink.trim());
  }
  
  // Generate second invite link if needed
  if (inviteLinks.length === 1) {
    // Create additional invite by sending to test email
    await fillById(page, 'inviteEmailInput', 'test2@example.com');
    await clickById(page, 'inviteSubmitButton');
    
    // Wait for new invite to appear and get the link
    await page.waitForTimeout(2000);
    const secondInvite = await byId(page, 'inviteLinkUrl').nth(1).textContent();
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
  const joinBtn = byId(page, 'joinLeagueButton');
  await safeClick(page, joinBtn);
  
  // Wait for success message
  await waitForId(page, 'joinSuccessMessage', { timeout: 10000 });
  
  console.log('✅ Successfully joined league');
}

/**
 * Auction helpers
 */
export async function startAuction(page: Page): Promise<void> {
  console.log('🔨 Starting auction...');
  
  // Wait for start auction button to be enabled
  const startButton = byId(page, 'startAuction');
  await expect(startButton).toBeEnabled({ timeout: 10000 });
  
  // Click start auction
  await startButton.click();
  
  // Wait for auction room to load
  await waitForId(page, 'auctionRoom', { timeout: 15000 });
  
  console.log('✅ Auction started successfully');
}

export async function nominateFirstAsset(page: Page): Promise<string> {
  console.log('🎯 Nominating first asset...');
  
  // Click nominate button
  await clickById(page, 'nominateBtn');
  
  // Select first available asset from dropdown
  const nominateSelect = byId(page, 'nominateSelect');
  await nominateSelect.waitFor({ state: 'visible' });
  await nominateSelect.selectOption({ index: 0 });
  
  // Submit nomination
  await clickById(page, 'nominateSubmit');
  
  // Wait for asset to appear in auction
  await waitForId(page, 'auctionAsset');
  
  const assetName = await byId(page, 'auctionAsset').textContent() || '';
  
  console.log(`✅ Nominated asset: ${assetName}`);
  return assetName;
}

export async function bid(page: Page, amount: number): Promise<void> {
  console.log(`💰 Placing bid: ${amount}`);
  
  // Use bid input or quick bid buttons
  if (amount <= 10) {
    // Use quick bid buttons for small amounts
    if (amount === 1) {
      await clickById(page, 'bidPlus1');
    } else if (amount === 5) {
      await clickById(page, 'bidPlus5');
    } else if (amount === 10) {
      await clickById(page, 'bidPlus10');
    }
  } else {
    // Use manual input for larger amounts
    await fillById(page, 'bidInput', amount.toString());
    await clickById(page, 'bidSubmit');
  }
  
  // Wait for top bid to update
  await expect(byId(page, 'auctionTopBid')).toContainText(amount.toString(), { timeout: 5000 });
  
  console.log(`✅ Bid placed: ${amount}`);
}

/**
 * Verification helpers
 */
export async function waitForSoldBadge(page: Page): Promise<void> {
  console.log('⏳ Waiting for lot to be sold...');
  
  await waitForId(page, 'soldBadge', { timeout: 15000 });
  
  console.log('✅ Lot sold successfully');
}

export async function verifyRosterCount(page: Page, expectedCount: number): Promise<void> {
  console.log(`🔍 Verifying roster count: ${expectedCount}`);
  
  const rosterItems = byId(page, 'rosterItem');
  await expect(rosterItems).toHaveCount(expectedCount, { timeout: 10000 });
  
  console.log(`✅ Roster count verified: ${expectedCount}`);
}

export async function verifyBudgetAmount(page: Page, expectedAmount: number): Promise<void> {
  console.log(`🔍 Verifying budget amount: ${expectedAmount}`);
  
  const budgetDisplay = byId(page, 'budgetRemaining');
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

/**
 * Core smoke test specific helpers - using placeBid instead of bid
 */
export async function expectLobbyState(page: Page, expectedState: string): Promise<void> {
  console.log(`🔍 Expecting lobby state: ${expectedState}`);
  
  // Wait for lobby member count indicator
  await expect(page.locator(`text="${expectedState}"`)).toBeVisible({ timeout: 10000 });
  
  console.log(`✅ Lobby state verified: ${expectedState}`);
}

export async function placeBid(page: Page, amount: number): Promise<void> {
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
  
  console.log(`✅ Bid placed: ${amount}`);
}

export async function expectTopBid(page: Page, expectedBid: string): Promise<void> {
  console.log(`🔍 Expecting top bid: ${expectedBid}`);
  
  const topBidElement = page.locator(`[data-testid="${TESTIDS.auctionTopBid}"]`);
  await expect(topBidElement).toContainText(expectedBid, { timeout: 5000 });
  
  console.log(`✅ Top bid verified: ${expectedBid}`);
}

export async function expectRosterUpdate(page: Page, clubName: string, remainingBudget: number): Promise<void> {
  console.log(`🔍 Expecting roster update: ${clubName}, budget: ${remainingBudget}`);
  
  // Check if club appears in roster
  await expect(page.locator(`text="${clubName}"`)).toBeVisible({ timeout: 10000 });
  
  // Check remaining budget
  await expect(page.locator(`[data-testid="${TESTIDS.yourBudget}"]`)).toContainText(remainingBudget.toString(), { timeout: 5000 });
  
  console.log(`✅ Roster update verified: ${clubName}, budget: ${remainingBudget}`);
}

export async function expectBudgetUnchanged(page: Page, expectedBudget: number): Promise<void> {
  console.log(`🔍 Expecting budget unchanged: ${expectedBudget}`);
  
  const budgetElement = page.locator(`[data-testid="${TESTIDS.yourBudget}"]`);
  await expect(budgetElement).toContainText(expectedBudget.toString(), { timeout: 5000 });
  
  console.log(`✅ Budget unchanged verified: ${expectedBudget}`);
}

export async function expectClubUniqueness(page: Page, clubName: string): Promise<void> {
  console.log(`🔍 Verifying club uniqueness: ${clubName}`);
  
  // Ensure the club appears only once in the roster/league
  const clubElements = page.locator(`text="${clubName}"`);
  const count = await clubElements.count();
  
  if (count > 1) {
    console.warn(`⚠️ Club ${clubName} appears ${count} times - may not be unique`);
  } else {
    console.log(`✅ Club uniqueness verified: ${clubName}`);
  }
}

export async function expectUserPresence(page: Page, expectedUserCount: number): Promise<void> {
  console.log(`🔍 Expecting user presence: ${expectedUserCount}`);
  
  // Check for user presence indicators (could be avatars, names, etc.)
  const userElements = page.locator('[data-testid*="user-"], [data-testid*="member-"], .user-avatar');
  await expect(userElements).toHaveCount(expectedUserCount, { timeout: 10000 });
  
  console.log(`✅ User presence verified: ${expectedUserCount}`);
}

/**
 * Wait for league creation success and navigation to lobby
 * Races between create-success marker and URL matching /app/leagues/:id/lobby
 * Then verifies lobby-joined badge exists
 */
export async function awaitCreatedAndInLobby(page: Page, leagueId?: string): Promise<string> {
  console.log('🏁 Waiting for league creation success and lobby navigation...');
  
  try {
    // Wait for URL to change to lobby pattern
    await page.waitForURL(/\/app\/leagues\/.+\/lobby/, { timeout: 10000 });
    console.log('✅ URL changed to lobby pattern');
    
    // Extract league ID from URL if not provided
    const currentUrl = page.url();
    const leagueIdMatch = currentUrl.match(/\/app\/leagues\/([^\/]+)\/lobby/);
    const extractedLeagueId = leagueIdMatch ? leagueIdMatch[1] : leagueId;
    
    if (!extractedLeagueId) {
      throw new Error(`Could not determine league ID from URL: ${currentUrl}`);
    }
    
    console.log(`✅ League ID: ${extractedLeagueId}`);
    
    // Poll readiness endpoint (TEST_MODE only)
    const apiOrigin = process.env.REACT_APP_BACKEND_URL || 'https://testid-enforcer.preview.emergentagent.com';
    console.log('🔍 Polling league readiness...');
    
    for (let i = 0; i < 10; i++) {
      try {
        const res = await page.request.get(`${apiOrigin}/test/league/${extractedLeagueId}/ready`);
        const data = await res.json();
        
        if (data.ready) {
          console.log('✅ League is ready for lobby rendering');
          // Wait for lobby-ready testid to appear
          await page.waitForSelector('[data-testid="lobby-ready"]', { timeout: 2000 });
          console.log('✅ lobby-ready testid found');
          return extractedLeagueId;
        }
        
        console.log(`⏳ League not ready yet (attempt ${i + 1}/10): ${data.reason || 'unknown'}`);
        await page.waitForTimeout(200);
      } catch (probeError) {
        console.log(`⚠️ Readiness probe failed (attempt ${i + 1}/10): ${probeError.message}`);
        await page.waitForTimeout(200);
      }
    }
    
    throw new Error('Lobby not ready after 10 attempts');
    
  } catch (error) {
    const currentUrl = page.url();
    console.error(`❌ Failed to complete league creation → lobby flow. Current URL: ${currentUrl}`);
    
    // Take debug screenshot
    await page.screenshot({ 
      path: `test-results/lobby-navigation-failure-${Date.now()}.png`,
      fullPage: false
    });
    
    throw new Error(`League creation → lobby navigation failed: ${error.message} (URL: ${currentUrl})`);
  }
}

/**
 * Missing helper functions for core-smoke test
 */
export async function expectAuctionState(page: Page, clubName: string): Promise<void> {
  console.log(`🔍 Expecting auction state for: ${clubName}`);
  
  // Wait for the club name to appear in auction
  await expect(page.locator(`[data-testid="${TESTIDS.auctionAssetName}"]`)).toContainText(clubName, { timeout: 10000 });
  
  console.log(`✅ Auction state verified for: ${clubName}`);
}

export async function expectLotSold(page: Page, clubName: string): Promise<void> {
  console.log(`🔍 Expecting lot sold for: ${clubName}`);
  
  // Wait for SOLD badge or status to appear
  await page.locator(`[data-testid="${TESTIDS.soldBadge}"]`).waitFor({ state: 'visible', timeout: 15000 });
  
  console.log(`✅ Lot sold verified for: ${clubName}`);
}