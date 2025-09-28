/**
 * Auction Test Helpers
 * High-level helpers that use test-only hooks for reliable auction testing
 */

import { Page } from '@playwright/test';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://auction-league.preview.emergentagent.com';

export interface LeagueSettings {
  name: string;
  clubSlots: number;
  budgetPerManager: number;
  minManagers: number;
  maxManagers: number;
}

/**
 * Create a league directly using test hooks (bypasses UI)
 */
export async function createTestLeague(page: Page, settings: LeagueSettings): Promise<string> {
  const response = await page.request.post(`${BACKEND_URL}/api/test/auction/create`, {
    data: { leagueSettings: settings }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to create test league: ${response.status()} ${await response.text()}`);
  }
  
  const result = await response.json();
  console.log(`🏆 Test league created: ${settings.name} (ID: ${result.leagueId})`);
  return result.leagueId;
}

/**
 * Add a member to a league directly using test hooks (bypasses UI)
 */
export async function addTestMember(page: Page, leagueId: string, email: string): Promise<string> {
  const response = await page.request.post(`${BACKEND_URL}/api/test/auction/add-member`, {
    data: { leagueId, email }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to add test member: ${response.status()} ${await response.text()}`);
  }
  
  const result = await response.json();
  console.log(`👥 Test member added: ${email} to league ${leagueId}`);
  return result.userId;
}

/**
 * Start an auction directly using test hooks (bypasses UI)
 */
export async function startTestAuction(page: Page, leagueId: string): Promise<string> {
  const response = await page.request.post(`${BACKEND_URL}/api/test/auction/start`, {
    data: { leagueId }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to start test auction: ${response.status()} ${await response.text()}`);
  }
  
  const result = await response.json();
  console.log(`🔨 Test auction started: ${leagueId}`);
  return result.auctionId || leagueId;
}

/**
 * Nominate an asset directly using test hooks (bypasses UI)
 */
export async function nominateTestAsset(page: Page, leagueId: string, extRef: string): Promise<void> {
  const response = await page.request.post(`${BACKEND_URL}/api/test/auction/nominate`, {
    data: { leagueId, extRef }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to nominate test asset: ${response.status()} ${await response.text()}`);
  }
  
  console.log(`🎯 Test asset nominated: ${extRef} in league ${leagueId}`);
}

/**
 * Place a bid directly using test hooks (bypasses UI)
 */
export async function placeTestBid(page: Page, leagueId: string, email: string, amount: number): Promise<string> {
  const response = await page.request.post(`${BACKEND_URL}/api/test/auction/bid`, {
    data: { leagueId, email, amount }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to place test bid: ${response.status()} ${await response.text()}`);
  }
  
  const result = await response.json();
  console.log(`💰 Test bid placed: ${email} bid ${amount} in league ${leagueId}`);
  return result.bidId;
}

/**
 * Force disconnect a user's socket for reconnection testing
 */
export async function dropTestSocket(page: Page, email: string): Promise<void> {
  const response = await page.request.post(`${BACKEND_URL}/api/test/sockets/drop`, {
    data: { email }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to drop test socket: ${response.status()} ${await response.text()}`);
  }
  
  const result = await response.json();
  console.log(`🔌 Test socket dropped: ${email} (${result.disconnectedConnections} connections)`);
}

/**
 * Setup a complete auction scenario for testing
 * Creates league, adds members, starts auction - all via hooks
 */
export async function setupTestAuction(
  page: Page, 
  leagueSettings: LeagueSettings, 
  memberEmails: string[]
): Promise<{ leagueId: string; auctionId: string; memberIds: string[] }> {
  
  console.log(`🧪 Setting up test auction: ${leagueSettings.name}`);
  
  // Create league
  const leagueId = await createTestLeague(page, leagueSettings);
  
  // Add members
  const memberIds: string[] = [];
  for (const email of memberEmails) {
    const userId = await addTestMember(page, leagueId, email);
    memberIds.push(userId);
  }
  
  // Start auction
  const auctionId = await startTestAuction(page, leagueId);
  
  console.log(`✅ Test auction setup complete: ${memberEmails.length} members in league ${leagueId}`);
  
  return { leagueId, auctionId, memberIds };
}

/**
 * Run a basic auction flow for testing anti-snipe, bidding, etc.
 */
export async function runTestAuctionFlow(
  page: Page,
  leagueId: string,
  nominatorEmail: string,
  asset: string = 'MAN_CITY'
): Promise<void> {
  
  console.log(`🏃 Running test auction flow in league ${leagueId}`);
  
  // Nominate an asset
  await nominateTestAsset(page, leagueId, asset);
  
  // Small delay for auction to be ready
  await page.waitForTimeout(100);
  
  console.log(`✅ Test auction flow ready for bidding on ${asset}`);
}

/**
 * Simulate a bidding sequence for testing
 */
export async function simulateBiddingSequence(
  page: Page,
  leagueId: string,
  bids: Array<{ email: string; amount: number }>
): Promise<string[]> {
  
  console.log(`💰 Simulating bidding sequence: ${bids.length} bids`);
  
  const bidIds: string[] = [];
  
  for (const bid of bids) {
    const bidId = await placeTestBid(page, leagueId, bid.email, bid.amount);
    bidIds.push(bidId);
    
    // Small delay between bids
    await page.waitForTimeout(50);
  }
  
  console.log(`✅ Bidding sequence complete: ${bidIds.length} bids placed`);
  return bidIds;
}