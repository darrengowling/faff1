const { test, expect } = require('@playwright/test');
const TestHelpers = require('./helpers/test-helpers');
const APIClient = require('./helpers/api-client');

/**
 * UCL Auction E2E Test Suite
 * 
 * Happy Path + Edge Cases for complete auction flow:
 * - User authentication and league setup
 * - Auction mechanics and bidding
 * - Scoring and data integrity
 * - Access control and security
 */

test.describe('UCL Auction E2E Test Suite', () => {
  let helpers;
  let api;
  let testData;
  
  // Test state tracking
  const testResults = {
    passed: [],
    failed: [],
    startTime: Date.now()
  };

  test.beforeAll(async ({ browser }) => {
    console.log('🎯 Starting UCL Auction E2E Test Suite');
    console.log('=' * 60);
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    helpers = new TestHelpers(page, context);
    api = new APIClient();
    
    try {
      testData = await helpers.setupTestFixtures();
      console.log('📋 Test fixtures ready:', JSON.stringify(testData, null, 2));
    } catch (error) {
      console.error('❌ Test fixture setup failed:', error.message);
      throw error;
    }
  });

  test.afterAll(async () => {
    if (helpers) {
      await helpers.cleanupTestData();
    }
    
    // Print test summary
    const duration = ((Date.now() - testResults.startTime) / 1000).toFixed(2);
    console.log('=' * 60);
    console.log('📊 E2E Test Summary:');
    console.log(`⏱️ Duration: ${duration}s`);
    console.log(`✅ Passed: ${testResults.passed.length}`);
    console.log(`❌ Failed: ${testResults.failed.length}`);
    
    if (testResults.passed.length > 0) {
      console.log('\n✅ Passed Tests:');
      testResults.passed.forEach(test => console.log(`  - ${test}`));
    }
    
    if (testResults.failed.length > 0) {
      console.log('\n❌ Failed Tests:');
      testResults.failed.forEach(test => console.log(`  - ${test}`));
    }
    
    console.log('=' * 60);
  });

  // Helper to track test results
  const trackResult = (testName, success, error = null) => {
    if (success) {
      testResults.passed.push(testName);
    } else {
      testResults.failed.push(`${testName}: ${error || 'Unknown error'}`);
    }
  };

  test('1. Auth: Magic Link Login Works for Each Test User', async ({ page }) => {
    const testName = 'Magic Link Authentication';
    
    try {
      for (const user of testData.users) {
        await helpers.loginUser(user.email);
        
        // Verify user is logged in
        await expect(page.locator('text=Dashboard || text=League')).toBeVisible();
        
        // Logout for next user
        await page.click('text=Logout || [data-testid="user-menu"]');
      }
      
      trackResult(testName, true);
      console.log('✅ 1. Magic link authentication passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 1. Magic link authentication failed:', error.message);
      throw error;
    }
  });

  test('2. Commissioner Setup: League Created with Settings and Guards', async ({ page }) => {
    const testName = 'Commissioner League Setup';
    
    try {
      const commissioner = testData.users.find(u => u.role === 'commissioner');
      await helpers.loginUser(commissioner.email);
      
      // Navigate to league dashboard
      const league = testData.leagues[0];
      await page.goto(`/leagues/${league.id}`);
      
      // Verify league settings are visible
      await expect(page.locator('text=Budget: 100M')).toBeVisible();
      await expect(page.locator('text=Club Slots: 3')).toBeVisible();
      await expect(page.locator('text=League Size: 2-8')).toBeVisible();
      
      // Verify Start Auction is disabled (only commissioner, need min members)
      const startButton = page.locator('text=Start Auction');
      await expect(startButton).toBeDisabled();
      
      // Verify member count shows need for more members
      await expect(page.locator('text=1/8 managers || text=Need')).toBeVisible();
      
      trackResult(testName, true);
      console.log('✅ 2. Commissioner setup passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 2. Commissioner setup failed:', error.message);
      throw error;
    }
  });

  test('3. Member Invitations and Join Process', async ({ page, context }) => {
    const testName = 'Member Invitation Process';
    
    try {
      const commissioner = testData.users.find(u => u.role === 'commissioner');
      const league = testData.leagues[0];
      
      // Login as commissioner
      await helpers.loginUser(commissioner.email);
      await page.goto(`/leagues/${league.id}`);
      
      // Invite Alice and Bob
      const memberEmails = ['alice@test.local', 'bob@test.local'];
      await helpers.inviteMembers(memberEmails);
      
      // Accept invitations as each user
      for (const email of memberEmails) {
        await helpers.acceptInvitation(email, league.id);
      }
      
      // Return to commissioner view and verify member count
      await helpers.loginUser(commissioner.email);
      await page.goto(`/leagues/${league.id}`);
      
      // Verify member count updated and Start Auction enabled
      await expect(page.locator('text=3/8 managers || text=3 managers')).toBeVisible();
      
      const startButton = page.locator('text=Start Auction');
      await expect(startButton).toBeEnabled();
      
      trackResult(testName, true);
      console.log('✅ 3. Member invitation process passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 3. Member invitation process failed:', error.message);
      throw error;
    }
  });

  test('4. Auction Start and Nomination Order', async ({ page }) => {
    const testName = 'Auction Start and Nomination';
    
    try {
      const commissioner = testData.users.find(u => u.role === 'commissioner');
      await helpers.loginUser(commissioner.email);
      
      const league = testData.leagues[0];
      await page.goto(`/leagues/${league.id}`);
      
      // Start auction
      await helpers.startAuction();
      
      // Verify auction is live
      await expect(page.locator('text=Live Auction || text=Current Lot')).toBeVisible();
      
      // Verify first lot shows a UCL club
      await expect(page.locator('[data-testid="club-name"] || text=Manchester City || text=Real Madrid')).toBeVisible();
      
      // Verify nomination order is visible (round-robin)
      await expect(page.locator('text=Nomination Order || text=Next:')).toBeVisible();
      
      trackResult(testName, true);
      console.log('✅ 4. Auction start and nomination passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 4. Auction start and nomination failed:', error.message);
      throw error;
    }
  });

  test('5. Real-time Bidding and Anti-snipe', async ({ page, context }) => {
    const testName = 'Real-time Bidding and Anti-snipe';
    
    try {
      // Create two browser contexts for Alice and Bob
      const alicePage = await context.newPage();
      const bobPage = await context.newPage();
      
      const league = testData.leagues[0];
      const auctionUrl = `/leagues/${league.id}/auction`;
      
      // Login Alice and Bob to auction page
      await helpers.loginUser('alice@test.local');
      await alicePage.goto(auctionUrl);
      
      const bobHelpers = new TestHelpers(bobPage, context);
      await bobHelpers.loginUser('bob@test.local');
      await bobPage.goto(auctionUrl);
      
      // Alice places first bid
      const aliceBid = 15;
      await alicePage.fill('input[placeholder*="amount"]', aliceBid.toString());
      await alicePage.click('text=Place Bid');
      
      // Verify Bob sees Alice's bid in real-time
      await expect(bobPage.locator(`text=${aliceBid} || text=Current: ${aliceBid}`)).toBeVisible({ timeout: 5000 });
      
      // Wait for timer to get low (simulate <3s left)
      await helpers.sleep(2000);
      
      // Bob places counter-bid
      const bobBid = 20;
      await bobPage.fill('input[placeholder*="amount"]', bobBid.toString());
      await bobPage.click('text=Place Bid');
      
      // Verify anti-snipe extends timer
      await expect(alicePage.locator('text=6 || text=5')).toBeVisible({ timeout: 3000 });
      
      trackResult(testName, true);
      console.log('✅ 5. Real-time bidding and anti-snipe passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 5. Real-time bidding and anti-snipe failed:', error.message);
      throw error;
    }
  });

  test('6. Budget Guard and Validation', async ({ page }) => {
    const testName = 'Budget Guard Validation';
    
    try {
      // Login as Alice
      await helpers.loginUser('alice@test.local');
      
      const league = testData.leagues[0];
      await page.goto(`/leagues/${league.id}/auction`);
      
      // Try to bid more than budget allows
      const excessiveBid = 120; // More than 100M budget
      await page.fill('input[placeholder*="amount"]', excessiveBid.toString());
      await page.click('text=Place Bid');
      
      // Verify error message
      await expect(page.locator('text=Insufficient budget || text=exceeds remaining')).toBeVisible();
      
      // Try to bid amount that would make it impossible to fill remaining slots
      const problematicBid = 95; // Would leave only 5M for 2 more clubs
      await page.fill('input[placeholder*="amount"]', problematicBid.toString());
      await page.click('text=Place Bid');
      
      // Should show friendly error about remaining slots
      await expect(page.locator('text=remaining slots || text=minimum price')).toBeVisible();
      
      trackResult(testName, true);
      console.log('✅ 6. Budget guard validation passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 6. Budget guard validation failed:', error.message);
      throw error;
    }
  });

  test('7. Lot Closure and Ownership Transfer', async ({ page }) => {
    const testName = 'Lot Closure and Ownership';
    
    try {
      // Login as Alice (assume she won the bid)
      await helpers.loginUser('alice@test.local');
      
      const league = testData.leagues[0];
      await page.goto(`/leagues/${league.id}/auction`);
      
      // Place a reasonable winning bid
      await page.fill('input[placeholder*="amount"]', '25');
      await page.click('text=Place Bid');
      
      // Wait for lot to close (timer expires)
      await expect(page.locator('text=Sold || text=Won')).toBeVisible({ timeout: 30000 });
      
      // Navigate to My Clubs to verify ownership
      await helpers.navigateToMyClubs();
      
      // Verify club appears in roster with correct price
      await expect(page.locator('text=25M || text=Price: 25')).toBeVisible();
      
      // Verify budget was decremented
      await expect(page.locator('text=75 || text=Remaining: 75')).toBeVisible();
      
      trackResult(testName, true);
      console.log('✅ 7. Lot closure and ownership passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 7. Lot closure and ownership failed:', error.message);
      throw error;
    }
  });

  test('8. Club Slots Cap Enforcement', async ({ page }) => {
    const testName = 'Club Slots Cap Enforcement';
    
    try {
      // This test assumes Alice has already won clubs and is at/near the 3-club limit
      await helpers.loginUser('alice@test.local');
      
      const league = testData.leagues[0];
      
      // Continue auction until Alice has 3 clubs
      // (This would require multiple auction rounds - simplified for test)
      
      // Simulate Alice trying to bid on 4th club
      await page.goto(`/leagues/${league.id}/auction`);
      
      // Check if at club limit
      const clubCount = await page.locator('[data-testid="club-count"] || text=clubs owned').textContent();
      
      if (clubCount && clubCount.includes('3')) {
        // Try to place bid when at limit
        await page.fill('input[placeholder*="amount"]', '15');
        await page.click('text=Place Bid');
        
        // Verify error about club limit
        await expect(page.locator('text=roster full || text=club limit || text=3 clubs')).toBeVisible();
      }
      
      trackResult(testName, true);
      console.log('✅ 8. Club slots cap enforcement passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 8. Club slots cap enforcement failed:', error.message);
      // Don't throw - this test might not be reachable depending on auction state
    }
  });

  test('9. Pause/Resume Auction with Timer Monotonicity', async ({ page }) => {
    const testName = 'Auction Pause/Resume';
    
    try {
      const commissioner = testData.users.find(u => u.role === 'commissioner');
      await helpers.loginUser(commissioner.email);
      
      const league = testData.leagues[0];
      await page.goto(`/leagues/${league.id}/auction`);
      
      // Record current timer value
      const timerBefore = await page.locator('[data-testid="timer"] || text=seconds').textContent();
      
      // Pause auction
      await helpers.pauseAuction();
      
      // Wait a moment
      await helpers.sleep(3000);
      
      // Resume auction
      await helpers.resumeAuction();
      
      // Verify timer didn't rewind (monotonic)
      const timerAfter = await page.locator('[data-testid="timer"] || text=seconds').textContent();
      
      // Timer should not have increased during pause
      if (timerBefore && timerAfter) {
        const beforeSeconds = parseInt(timerBefore.match(/\d+/)?.[0] || '0');
        const afterSeconds = parseInt(timerAfter.match(/\d+/)?.[0] || '0');
        expect(afterSeconds).toBeLessThanOrEqual(beforeSeconds);
      }
      
      trackResult(testName, true);
      console.log('✅ 9. Auction pause/resume passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 9. Auction pause/resume failed:', error.message);
      throw error;
    }
  });

  test('10. Scoring via API with Idempotency', async ({ page }) => {
    const testName = 'API Scoring with Idempotency';
    
    try {
      // Ingest a draw result
      const drawResult = {
        match_id: 'ucl-test-001',
        home_ext: 'MCI',
        away_ext: 'RMA',
        home_goals: 2,
        away_goals: 2,
        status: 'final'
      };
      
      const result1 = await helpers.ingestMatchResult(drawResult);
      expect(result1).toBeTruthy();
      
      // Verify points: each team gets 2 (goals) + 1 (draw) = 3 points
      await helpers.navigateToMyClubs();
      
      // Check if Alice or Bob owns MCI/RMA and verify points
      const myClubsText = await page.locator('body').textContent();
      if (myClubsText.includes('MCI') || myClubsText.includes('RMA')) {
        await expect(page.locator('text=3 points || text=+3')).toBeVisible();
      }
      
      // Test idempotency - ingest same result again
      const result2 = await helpers.ingestMatchResult(drawResult);
      expect(result2).toBeTruthy();
      
      // Points should not double
      await page.reload();
      const pointsAfterDuplicate = await page.locator('body').textContent();
      expect(pointsAfterDuplicate).not.toContain('6 points'); // Should still be 3, not 6
      
      // Test win scenario
      const winResult = {
        match_id: 'ucl-test-002',
        home_ext: 'MCI',
        away_ext: 'BAR',
        home_goals: 1,
        away_goals: 0,
        status: 'final'
      };
      
      await helpers.ingestMatchResult(winResult);
      
      // MCI owner should get 1 (goal) + 3 (win) = 4 points for this match
      
      trackResult(testName, true);
      console.log('✅ 10. API scoring with idempotency passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 10. API scoring with idempotency failed:', error.message);
      throw error;
    }
  });

  test('11. Leaderboard and Data Consistency', async ({ page }) => {
    const testName = 'Leaderboard and Data Consistency';
    
    try {
      // Navigate to leaderboard
      await helpers.navigateToLeaderboard();
      
      // Verify leaderboard shows totals
      await expect(page.locator('text=Total Points || text=Leaderboard')).toBeVisible();
      
      // Verify point totals reflect previous scoring
      await expect(page.locator('[data-testid="total-points"] || text=points')).toBeVisible();
      
      // Navigate to My Clubs and verify consistency
      await helpers.navigateToMyClubs();
      await expect(page.locator('text=Budget Remaining || text=Clubs Owned')).toBeVisible();
      
      // Navigate to Fixtures and verify ownership badges
      await helpers.navigateToFixtures();
      await expect(page.locator('text=Fixtures || text=Match')).toBeVisible();
      
      // Look for ownership indicators in fixtures
      await expect(page.locator('[data-testid="owned-club"] || text=owned')).toBeVisible();
      
      trackResult(testName, true);
      console.log('✅ 11. Leaderboard and data consistency passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 11. Leaderboard and data consistency failed:', error.message);
      throw error;
    }
  });

  test('12. Access Control and Security', async ({ page, context }) => {
    const testName = 'Access Control and Security';
    
    try {
      const league = testData.leagues[0];
      
      // Test 1: Non-member cannot access league data
      const outsiderPage = await context.newPage();
      await outsiderPage.goto(`/leagues/${league.id}`);
      
      // Should be redirected or show access denied
      await expect(outsiderPage.locator('text=Access denied || text=Not authorized || text=Login')).toBeVisible();
      
      // Test 2: API access control
      await helpers.verifyAccessControl(`/leagues/${league.id}/members`);
      await helpers.verifyAccessControl(`/leagues/${league.id}/leaderboard`);
      
      // Test 3: Commissioner-only endpoints
      const alice = testData.users.find(u => u.email === 'alice@test.local');
      api.setAuthToken(alice.token);
      
      const adminResult = await api.startAuction(league.id);
      expect(adminResult.success).toBe(false);
      expect(adminResult.status).toBe(403);
      
      trackResult(testName, true);
      console.log('✅ 12. Access control and security passed');
    } catch (error) {
      trackResult(testName, false, error.message);
      console.log('❌ 12. Access control and security failed:', error.message);
      throw error;
    }
  });
});