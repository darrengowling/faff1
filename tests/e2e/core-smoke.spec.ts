/**
 * Core Smoke Test - End-to-End Auction Flow
 * 
 * Tests the complete auction loop: create league → invite → join → auction → bid → sell
 * Uses multiple browser contexts to simulate real multi-user scenarios.
 */

import { test, expect, BrowserContext, Page } from '@playwright/test';
import { login } from './utils/login';
import { 
  clickCreateLeague, 
  createLeague, 
  getInviteLinks, 
  startAuction,
  expectLobbyState,
  nominateFirstAsset,
  placeBid,
  expectTopBid,
  expectRosterUpdate,
  expectBudgetUnchanged,
  expectClubUniqueness,
  expectUserPresence
} from './utils/helpers';
import { ensureClickable, clickWhenReady } from './utils/ensureClickable';
import { TESTIDS } from '../../frontend/src/testids.js';

// Test configuration
const TEST_TIMEOUT = 90000; // 90 seconds max
const USERS = {
  commissioner: { email: 'commish@example.com', name: 'Commissioner' },
  alice: { email: 'alice@example.com', name: 'Alice' },
  bob: { email: 'bob@example.com', name: 'Bob' }
};

const LEAGUE_SETTINGS = {
  name: 'Core Smoke League',
  clubSlots: 3,
  budgetPerManager: 100,
  minManagers: 2,
  maxManagers: 8
};

test.describe('Core Smoke Test', () => {
  let commissionerContext: BrowserContext;
  let aliceContext: BrowserContext;
  let bobContext: BrowserContext;
  
  let commissionerPage: Page;
  let alicePage: Page;
  let bobPage: Page;
  
  let leagueId: string;
  let inviteLinks: string[] = [];

  test.setTimeout(TEST_TIMEOUT);

  // Set socket transport to polling for CI environments
  test.beforeAll(async ({ browser }) => {
    if (process.env.CI) {
      process.env.NEXT_PUBLIC_SOCKET_TRANSPORTS = 'polling';
    }

    // Create separate browser contexts for each user
    commissionerContext = await browser.newContext();
    aliceContext = await browser.newContext();
    bobContext = await browser.newContext();
    
    commissionerPage = await commissionerContext.newPage();
    alicePage = await aliceContext.newPage();
    bobPage = await bobContext.newPage();

    // Set up console error tracking
    [commissionerPage, alicePage, bobPage].forEach(page => {
      page.on('console', msg => {
        if (msg.type() === 'error') {
          console.log(`Console error on ${page === commissionerPage ? 'Commissioner' : page === alicePage ? 'Alice' : 'Bob'}: ${msg.text()}`);
        }
      });
    });
  });

  test.afterEach(async ({ }, testInfo) => {
    // Take screenshot and save console logs on failure
    if (testInfo.status !== testInfo.expectedStatus) {
      console.log('Test failed, capturing artifacts...');
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      
      // Screenshots
      await commissionerPage.screenshot({ 
        path: `test-results/commissioner-${timestamp}.png`, 
        fullPage: true 
      });
      await alicePage.screenshot({ 
        path: `test-results/alice-${timestamp}.png`, 
        fullPage: true 
      });
      await bobPage.screenshot({ 
        path: `test-results/bob-${timestamp}.png`, 
        fullPage: true 
      });
      
      console.log(`Screenshots saved with timestamp: ${timestamp}`);
    }
  });

  test.afterAll(async () => {
    await commissionerContext?.close();
    await aliceContext?.close();
    await bobContext?.close();
  });

  test('Complete auction flow: create → invite → join → auction → bid → sell', async () => {
    console.log('🚀 Starting core smoke test...');

    // Step 1: Commissioner login and create league
    console.log('📝 Step 1: Commissioner creates league...');
    await login(commissionerPage, USERS.commissioner.email, { mode: 'test' });
    
    leagueId = await createLeague(commissionerPage, LEAGUE_SETTINGS);
    
    // Verify league settings displayed correctly
    await expect(commissionerPage.locator('text=Slots: 3')).toBeVisible();
    await expect(commissionerPage.locator('text=Budget: 100')).toBeVisible();
    await expect(commissionerPage.locator('text=Min: 2')).toBeVisible();
    
    console.log(`✅ League created: ${leagueId}`);

    // Step 2: Get invite links
    console.log('🔗 Step 2: Getting invite links...');
    inviteLinks = await getInviteLinks(commissionerPage);
    expect(inviteLinks.length).toBeGreaterThanOrEqual(1);
    console.log(`✅ Got ${inviteLinks.length} invite links`);

    // Step 3: Alice and Bob join via invite links
    console.log('👥 Step 3: Alice and Bob join league...');
    
    // Alice joins
    await alicePage.goto(inviteLinks[0]);
    await alicePage.waitForLoadState('networkidle');
    await login(alicePage, USERS.alice.email, { mode: 'test' });
    await expectLobbyState(alicePage, '2/3'); // Commissioner + Alice
    
    // Bob joins  
    await bobPage.goto(inviteLinks[0]);
    await bobPage.waitForLoadState('networkidle');
    await login(bobPage, USERS.bob.email, { mode: 'test' });
    await expectLobbyState(bobPage, '3/3'); // All joined
    
    console.log('✅ All users joined lobby');

    // Step 4: Verify Start Auction is enabled (min=2 requirement met)
    console.log('🎯 Step 4: Checking Start Auction state...');
    const startButton = commissionerPage.locator('button:has-text("Start Auction")');
    await expect(startButton).toBeEnabled();
    console.log('✅ Start Auction enabled with 3 members (min=2)');

    // Step 5: Start auction - all users navigate to auction room
    console.log('🔨 Step 5: Starting auction...');
    await startAuction(commissionerPage);
    
    // Wait for all users to be in auction room
    await Promise.all([
      commissionerPage.waitForURL('**/auction/**'),
      alicePage.waitForURL('**/auction/**'),
      bobPage.waitForURL('**/auction/**')
    ]);
    
    console.log('✅ All users in auction room');

    // Step 6: Nominate first available club
    console.log('🏆 Step 6: Nominating first club...');
    const clubName = await nominateFirstAsset(commissionerPage);
    
    // Verify all users see the nomination
    await Promise.all([
      expectAuctionState(commissionerPage, clubName),
      expectAuctionState(alicePage, clubName), 
      expectAuctionState(bobPage, clubName)
    ]);
    
    console.log(`✅ ${clubName} nominated and visible to all users`);

    // Step 7: Bidding sequence
    console.log('💰 Step 7: Bidding sequence...');
    
    // Alice bids first
    await placeBid(alicePage, 1); // +1 from starting price
    await expectTopBid(commissionerPage, '11'); // Assuming starting price is 10
    await expectTopBid(alicePage, '11');
    await expectTopBid(bobPage, '11');
    
    // Bob overbids
    await placeBid(bobPage, 5); // +5 more 
    await expectTopBid(commissionerPage, '16');
    await expectTopBid(alicePage, '16');
    await expectTopBid(bobPage, '16');
    
    // Verify Alice sees "Outbid" status
    await expect(alicePage.locator('text=Outbid')).toBeVisible({ timeout: 5000 });
    
    console.log('✅ Bidding sequence completed, Bob is top bidder at 16');

    // Step 8: Let timer expire and lot sells
    console.log('⏰ Step 8: Waiting for lot to close...');
    
    // Wait for timer to reach 0 or SOLD status to appear
    await Promise.all([
      expectLotSold(commissionerPage, clubName),
      expectLotSold(alicePage, clubName),
      expectLotSold(bobPage, clubName)
    ]);
    
    console.log('✅ Lot closed and sold to Bob');

    // Step 9: Verify final state
    console.log('📊 Step 9: Verifying final state...');
    
    // Check Bob's roster and budget
    await expectRosterUpdate(bobPage, clubName, 84); // 100 - 16 = 84 remaining budget
    
    // Check Alice and Commissioner unchanged (lost auction)
    await expectBudgetUnchanged(alicePage, 100);
    await expectBudgetUnchanged(commissionerPage, 100);
    
    // Verify club uniqueness - try to nominate same club again
    await expectClubUniqueness(commissionerPage, clubName);
    
    console.log('✅ Final state verified - auction flow complete!');

    // Step 10: Optional checks
    console.log('🔍 Step 10: Final checks...');
    
    // Verify presence of all users
    await expectUserPresence(commissionerPage, 3);
    await expectUserPresence(alicePage, 3);
    await expectUserPresence(bobPage, 3);
    
    console.log('🎉 Core smoke test completed successfully!');
  });
});

// Helper Functions - All imported from utils/helpers.ts