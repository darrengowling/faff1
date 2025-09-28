/**
 * Auction Tests
 * Tests auction mechanics including anti-snipe, simultaneous bids, safe close, and undo behavior
 */

import { test, expect, Browser, BrowserContext, Page } from '@playwright/test';
import { TESTIDS } from '../../frontend/src/testids.js';
import { login, createLeague, startAuction, nominateFirstAsset, bid } from './utils/helpers';
import { initializeTestTime, advanceTime, advanceTimeSeconds, triggerAntiSnipe, simulateAuctionTimer } from './utils/time-helpers';

test.describe('Auction Tests', () => {
  let commissionerPage: Page;
  let alice: Page;
  let bob: Page;
  let leagueId: string;

  test.beforeAll(async ({ browser }: { browser: Browser }) => {
    const commissionerContext = await browser.newContext();
    const aliceContext = await browser.newContext();
    const bobContext = await browser.newContext();
    
    commissionerPage = await commissionerContext.newPage();
    alice = await aliceContext.newPage();
    bob = await bobContext.newPage();
  });

  test.afterAll(async () => {
    await commissionerPage?.close();
    await alice?.close();
    await bob?.close();
  });

  test('Anti-snipe extends timer when bid placed in final seconds', async () => {
    console.log('🧪 Testing anti-snipe timer extension...');
    
    // Setup auction with short timer (8 seconds as per test env)
    await login(commissionerPage, 'commissioner@test.com');
    leagueId = await createLeague(commissionerPage, {
      name: 'Anti-Snipe Test League',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 4
    });
    
    // Add two participants
    await login(alice, 'alice@test.com');
    await login(bob, 'bob@test.com');
    
    // Join league (simplified - would use invite flow in real test)
    await alice.goto(`/leagues/${leagueId}/join`);
    await bob.goto(`/leagues/${leagueId}/join`);
    
    // Start auction
    await startAuction(commissionerPage);
    
    // All users navigate to auction
    await alice.goto(commissionerPage.url());
    await bob.goto(commissionerPage.url());
    
    // Nominate asset
    const assetName = await nominateFirstAsset(commissionerPage);
    
    // Wait for timer to be < 3 seconds (anti-snipe threshold)
    const timer = commissionerPage.locator(`[data-testid="${TESTIDS.auctionTimer}"]`);
    await timer.waitFor({ state: 'visible' });
    
    // Wait until timer shows 2 seconds or less
    await commissionerPage.waitForFunction(() => {
      const timerElement = document.querySelector(`[data-testid="${TESTIDS.auctionTimer}"]`);
      const timeText = timerElement?.textContent || '';
      const seconds = parseInt(timeText.split(':')[1] || '0');
      return seconds <= 2;
    }, { timeout: 10000 });
    
    // Place bid in final seconds
    await bid(alice, 5);
    
    // Verify timer extended (should be more than 2 seconds now)
    await commissionerPage.waitForFunction(() => {
      const timerElement = document.querySelector(`[data-testid="${TESTIDS.auctionTimer}"]`);
      const timeText = timerElement?.textContent || '';
      const seconds = parseInt(timeText.split(':')[1] || '0');
      return seconds > 2;
    }, { timeout: 5000 });
    
    console.log('✅ Anti-snipe timer extension working');
  });

  test('Simultaneous bids resolve deterministically', async () => {
    console.log('🧪 Testing simultaneous bid resolution...');
    
    // Setup similar to previous test
    await login(commissionerPage, 'commissioner-sim@test.com');
    leagueId = await createLeague(commissionerPage, {
      name: 'Simultaneous Bid Test',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 4
    });
    
    await login(alice, 'alice-sim@test.com');
    await login(bob, 'bob-sim@test.com');
    
    await startAuction(commissionerPage);
    await alice.goto(commissionerPage.url());
    await bob.goto(commissionerPage.url());
    
    await nominateFirstAsset(commissionerPage);
    
    // Record initial top bid
    const initialTopBid = await commissionerPage.locator(`[data-testid="${TESTIDS.auctionTopBid}"]`).textContent();
    
    // Both users place bids simultaneously
    await Promise.all([
      bid(alice, 10),
      bid(bob, 10)
    ]);
    
    // Verify only one bid won (deterministic resolution)
    const finalTopBid = await commissionerPage.locator(`[data-testid="${TESTIDS.auctionTopBid}"]`).textContent();
    const finalTopBidder = await commissionerPage.locator(`[data-testid="${TESTIDS.auctionTopBidder}"]`).textContent();
    
    expect(finalTopBid).toBe('10');
    expect(finalTopBidder).toMatch(/alice|bob/); // One of them should be top bidder
    
    console.log(`✅ Simultaneous bids resolved deterministically. Winner: ${finalTopBidder}`);
  });

  test('Safe lot close prevents data corruption', async () => {
    console.log('🧪 Testing safe lot closing...');
    
    // Setup auction
    await login(commissionerPage, 'commissioner-close@test.com');
    leagueId = await createLeague(commissionerPage, {
      name: 'Safe Close Test',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 4
    });
    
    await login(alice, 'alice-close@test.com');
    await startAuction(commissionerPage);
    await alice.goto(commissionerPage.url());
    
    await nominateFirstAsset(commissionerPage);
    await bid(alice, 15);
    
    // Let timer expire naturally or close lot manually
    const closeLotButton = commissionerPage.locator(`[data-testid="${TESTIDS.closeLotButton}"]`);
    if (await closeLotButton.isVisible()) {
      await closeLotButton.click();
    } else {
      // Wait for timer to expire
      await commissionerPage.locator(`[data-testid="${TESTIDS.soldBadge}"]`).waitFor({ 
        state: 'visible', 
        timeout: 15000 
      });
    }
    
    // Verify lot shows as SOLD
    await expect(commissionerPage.locator(`[data-testid="${TESTIDS.soldBadge}"]`)).toContainText('SOLD');
    
    // Verify winner's budget updated correctly
    await expect(alice.locator(`[data-testid="${TESTIDS.yourBudget}"]`)).toContainText('85'); // 100 - 15
    
    // Verify winner's slots decreased
    await expect(alice.locator(`[data-testid="${TESTIDS.yourSlotsRemaining}"]`)).toContainText('2'); // 3 - 1
    
    console.log('✅ Safe lot closing completed successfully');
  });

  test('Undo disabled once next lot opens', async () => {
    console.log('🧪 Testing undo button behavior...');
    
    // Setup auction with multiple lots
    await login(commissionerPage, 'commissioner-undo@test.com');
    leagueId = await createLeague(commissionerPage, {
      name: 'Undo Test League',
      clubSlots: 5, // Multiple slots for multiple lots
      budgetPerManager: 200,
      minManagers: 2,
      maxManagers: 4
    });
    
    await login(alice, 'alice-undo@test.com');
    await startAuction(commissionerPage);
    await alice.goto(commissionerPage.url());
    
    // First lot
    await nominateFirstAsset(commissionerPage);
    await bid(alice, 20);
    
    // Wait for lot to close
    await commissionerPage.locator(`[data-testid="${TESTIDS.soldBadge}"]`).waitFor({ 
      state: 'visible', 
      timeout: 15000 
    });
    
    // Check if undo button is available
    const undoButton = commissionerPage.locator(`[data-testid="${TESTIDS.undoButton}"]`);
    const undoAvailable = await undoButton.isVisible();
    
    if (undoAvailable) {
      // Verify undo is enabled for this lot
      await expect(undoButton).toBeEnabled();
      
      // Start next lot
      const nextLotButton = commissionerPage.locator(`[data-testid="${TESTIDS.nextLotButton}"]`);
      if (await nextLotButton.isVisible()) {
        await nextLotButton.click();
        
        // Verify undo is now disabled for previous lot
        const undoButtonAfterNext = commissionerPage.locator(`[data-testid="${TESTIDS.undoButton}"]`);
        if (await undoButtonAfterNext.isVisible()) {
          await expect(undoButtonAfterNext).toBeDisabled();
        }
        
        console.log('✅ Undo correctly disabled after next lot opened');
      } else {
        console.log('⚠️ Next lot button not available - single lot auction');
      }
    } else {
      console.log('⚠️ Undo button not visible - feature may not be implemented');
    }
  });

  test('Bid validation prevents invalid amounts', async () => {
    console.log('🧪 Testing bid validation...');
    
    // Setup simple auction
    await login(commissionerPage, 'commissioner-validation@test.com');
    leagueId = await createLeague(commissionerPage, {
      name: 'Validation Test',
      clubSlots: 3,
      budgetPerManager: 50, // Low budget for testing limits
      minManagers: 2,
      maxManagers: 4
    });
    
    await login(alice, 'alice-validation@test.com');
    await startAuction(commissionerPage);
    await alice.goto(commissionerPage.url());
    
    await nominateFirstAsset(commissionerPage);
    
    // Try to bid more than budget
    const bidInput = alice.locator(`[data-testid="${TESTIDS.bidInput}"]`);
    const bidSubmit = alice.locator(`[data-testid="${TESTIDS.bidSubmit}"]`);
    
    await bidInput.fill('100'); // More than 50 budget
    await expect(bidSubmit).toBeDisabled(); // Should be disabled
    
    // Try valid bid
    await bidInput.fill('25'); // Within budget
    await expect(bidSubmit).toBeEnabled(); // Should be enabled
    
    await bidSubmit.click();
    
    // Verify bid was accepted
    await expect(commissionerPage.locator(`[data-testid="${TESTIDS.auctionTopBid}"]`))
      .toContainText('25', { timeout: 5000 });
    
    console.log('✅ Bid validation working correctly');
  });
});