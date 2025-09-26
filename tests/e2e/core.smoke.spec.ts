/**
 * Core Smoke Test - End-to-End
 * 
 * Tests the complete user journey: Create league → Invite → Join → Auction → Bid → Sell
 * Uses only data-testid selectors, no heuristic clicking
 */

import { test, expect, Browser, BrowserContext, Page } from '@playwright/test';
import { 
  login, 
  createLeague, 
  getInviteLinks, 
  joinViaInvite, 
  startAuction, 
  nominateFirstAsset, 
  bid, 
  waitForSoldBadge,
  verifyRosterCount,
  verifyBudgetAmount,
  waitForJoinedCount,
  captureDebugInfo
} from './utils/helpers';
import { TESTIDS } from '../../frontend/src/testids';

test.describe('Core Smoke Test', () => {
  let commissionerPage: Page;
  let alicePage: Page;
  let bobPage: Page;
  let leagueId: string;
  
  test.beforeAll(async ({ browser }: { browser: Browser }) => {
    // Create contexts for multiple users
    const commissionerContext = await browser.newContext();
    const aliceContext = await browser.newContext();
    const bobContext = await browser.newContext();
    
    commissionerPage = await commissionerContext.newPage();
    alicePage = await aliceContext.newPage();
    bobPage = await bobContext.newPage();
    
    // Set up console logging for debugging
    [commissionerPage, alicePage, bobPage].forEach((page, index) => {
      const userNames = ['Commissioner', 'Alice', 'Bob'];
      page.on('console', msg => {
        console.log(`[${userNames[index]}] ${msg.type()}: ${msg.text()}`);
      });
    });
  });
  
  test.afterAll(async () => {
    await commissionerPage?.close();
    await alicePage?.close();
    await bobPage?.close();
  });
  
  test('Complete auction flow: Create → Invite → Join → Start → Nominate → Bid → Sell', async () => {
    const testStart = Date.now();
    console.log('🚀 Starting core smoke test...');
    
    try {
      // Step 1: Commissioner creates league
      console.log('\n📋 Step 1: Commissioner creates league');
      await login(commissionerPage, 'commissioner@test.com');
      
      leagueId = await createLeague(commissionerPage, {
        name: 'Core E2E Test League',
        clubSlots: 3,
        budgetPerManager: 100,
        minManagers: 2,
        maxManagers: 8
      });
      
      expect(leagueId).toBeTruthy();
      
      // Step 2: Get invite links
      console.log('\n📧 Step 2: Getting invite links');
      const inviteLinks = await getInviteLinks(commissionerPage);
      expect(inviteLinks).toHaveLength(2);
      
      // Step 3: Alice joins via invite
      console.log('\n👩 Step 3: Alice joins league');
      await login(alicePage, 'alice@test.com');
      await joinViaInvite(alicePage, inviteLinks[0]);
      
      // Step 4: Bob joins via invite  
      console.log('\n👨 Step 4: Bob joins league');
      await login(bobPage, 'bob@test.com');
      await joinViaInvite(bobPage, inviteLinks[1]);
      
      // Step 5: Verify lobby shows 2/8 joined
      console.log('\n👥 Step 5: Verifying member count');
      await waitForJoinedCount(commissionerPage, 2);
      
      // Verify start auction button is enabled
      await expect(commissionerPage.locator(`[data-testid="${TESTIDS.startAuctionBtn}"]`))
        .toBeEnabled({ timeout: 10000 });
      
      // Step 6: Start auction
      console.log('\n🔨 Step 6: Starting auction');
      await startAuction(commissionerPage);
      
      // Navigate Alice and Bob to auction room
      await alicePage.goto(commissionerPage.url());
      await bobPage.goto(commissionerPage.url());
      
      // Wait for all users to see auction room
      for (const page of [commissionerPage, alicePage, bobPage]) {
        await page.locator(`[data-testid="${TESTIDS.auctionRoom}"]`)
          .waitFor({ state: 'visible', timeout: 15000 });
      }
      
      // Step 7: Nominate first asset
      console.log('\n🎯 Step 7: Nominating first asset');
      const assetName = await nominateFirstAsset(commissionerPage);
      expect(assetName).toBeTruthy();
      
      // Verify all users see the nominated asset
      for (const page of [alicePage, bobPage]) {
        await expect(page.locator(`[data-testid="${TESTIDS.auctionAssetName}"]`))
          .toContainText(assetName, { timeout: 10000 });
      }
      
      // Step 8: Alice bids +1, Bob bids +5
      console.log('\n💰 Step 8: Placing bids');
      
      // Alice bids first
      await bid(alicePage, 1);
      
      // Verify top bid updates for all users
      for (const page of [commissionerPage, bobPage]) {
        await expect(page.locator(`[data-testid="${TESTIDS.auctionTopBid}"]`))
          .toContainText('1', { timeout: 5000 });
      }
      
      // Bob outbids Alice
      await bid(bobPage, 5);
      
      // Verify Bob's bid is now top bid for all users
      for (const page of [commissionerPage, alicePage]) {
        await expect(page.locator(`[data-testid="${TESTIDS.auctionTopBid}"]`))
          .toContainText('5', { timeout: 5000 });
      }
      
      // Step 9: Wait for timer to expire and lot to be sold
      console.log('\n⏰ Step 9: Waiting for lot to close');
      await waitForSoldBadge(commissionerPage);
      
      // Verify sold badge appears for all users
      for (const page of [alicePage, bobPage]) {
        await expect(page.locator(`[data-testid="${TESTIDS.soldBadge}"]`))
          .toBeVisible({ timeout: 10000 });
      }
      
      // Step 10: Verify winner's roster and budget
      console.log('\n🏆 Step 10: Verifying winner\'s roster and budget');
      
      // Bob should have 1 item in roster
      await verifyRosterCount(bobPage, 1);
      
      // Bob's budget should be 100 - 5 = 95
      await verifyBudgetAmount(bobPage, 95);
      
      // Alice should still have 0 items and full budget
      await verifyRosterCount(alicePage, 0);
      await verifyBudgetAmount(alicePage, 100);
      
      const testDuration = Date.now() - testStart;
      console.log(`\n🎉 Core smoke test completed successfully in ${testDuration}ms`);
      
    } catch (error) {
      console.error('\n❌ Core smoke test failed:', error);
      
      // Capture debug info on failure
      await Promise.all([
        captureDebugInfo(commissionerPage, 'commissioner-failure'),
        captureDebugInfo(alicePage, 'alice-failure'),
        captureDebugInfo(bobPage, 'bob-failure'),
      ]);
      
      throw error;
    }
  });
  
  // Test timeout: 60 seconds max
  test.setTimeout(60000);
});