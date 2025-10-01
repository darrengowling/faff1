/**
 * Minimal Auction Smoke Test
 * 
 * Tests minimal auction path with anti-snipe extension:
 * Auth (test login) → create league (page, not only dialog) → lobby load
 * Nominate club → two bids (different users) → observe anti_snipe and sold
 */

import { test, expect, BrowserContext, Page } from '@playwright/test';
import { login } from './utils/login';
import { ensureClickable } from './utils/ensureClickable';
import { TESTIDS } from '../../frontend/src/testids.ts';

// Test configuration
const TEST_TIMEOUT = 120000; // 2 minutes max for anti-snipe testing
const USERS = {
  commissioner: { email: 'commish@example.com', name: 'Commissioner' },
  alice: { email: 'alice@example.com', name: 'Alice' },
  bob: { email: 'bob@example.com', name: 'Bob' }
};

const LEAGUE_SETTINGS = {
  name: 'Minimal Auction Smoke',
  clubSlots: 1,
  budgetPerManager: 50,
  minManagers: 2,
  maxManagers: 3,
  antiSnipeSeconds: 5 // Short for testing
};

test.describe('Minimal Auction Smoke Test', () => {
  let commissionerContext: BrowserContext;
  let aliceContext: BrowserContext;
  let bobContext: BrowserContext;
  
  let commissionerPage: Page;
  let alicePage: Page; 
  let bobPage: Page;
  
  let leagueId: string;
  let inviteCode: string;

  test.setTimeout(TEST_TIMEOUT);

  test.beforeAll(async ({ browser }) => {
    // Set socket transport to polling for consistency
    process.env.VITE_SOCKET_TRANSPORTS = 'polling';

    // Create separate browser contexts
    commissionerContext = await browser.newContext();
    aliceContext = await browser.newContext();
    bobContext = await browser.newContext();
    
    commissionerPage = await commissionerContext.newPage();
    alicePage = await aliceContext.newPage();
    bobPage = await bobContext.newPage();

    // Console error tracking
    [commissionerPage, alicePage, bobPage].forEach((page, index) => {
      const names = ['Commissioner', 'Alice', 'Bob'];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          console.log(`${names[index]} console error: ${msg.text()}`);
        }
      });
    });
  });

  test.afterAll(async () => {
    await commissionerContext?.close();
    await aliceContext?.close();  
    await bobContext?.close();
  });

  test('Minimal auction path with anti-snipe', async () => {
    console.log('🚀 Starting minimal auction smoke test with anti-snipe...');

    // Step 1: Auth (test login)
    console.log('📝 Step 1: Commissioner test login...');
    await commissionerPage.goto('/app');
    await commissionerPage.waitForLoadState('networkidle');
    await login(commissionerPage, USERS.commissioner.email, { mode: 'test' });
    
    // Verify we're authenticated and on the main app page
    await expect(commissionerPage.locator('[data-testid="create-league-btn"]')).toBeVisible();
    console.log('✅ Commissioner authenticated and in dashboard');

    // Step 2: Create league (page, not dialog) 
    console.log('🏗️  Step 2: Creating league via page...');
    
    // Navigate to create league page
    await commissionerPage.click('[data-testid="create-league-button"]');
    await commissionerPage.waitForURL('**/create-league**');
    await commissionerPage.waitForLoadState('networkidle');
    
    // Fill league form
    await commissionerPage.fill('[data-testid="league-name"]', LEAGUE_SETTINGS.name);
    
    // Set league settings
    await commissionerPage.fill('[data-testid="club-slots"]', LEAGUE_SETTINGS.clubSlots.toString());
    await commissionerPage.fill('[data-testid="budget-per-manager"]', LEAGUE_SETTINGS.budgetPerManager.toString());
    await commissionerPage.fill('[data-testid="min-managers"]', LEAGUE_SETTINGS.minManagers.toString());
    await commissionerPage.fill('[data-testid="max-managers"]', LEAGUE_SETTINGS.maxManagers.toString());
    
    // Create league
    await commissionerPage.click('[data-testid="create-league-submit"]');
    await commissionerPage.waitForURL('**/leagues/**/lobby**');
    
    // Extract league ID from URL
    const url = commissionerPage.url();
    const match = url.match(/leagues\/([^\/]+)\/lobby/);
    expect(match).not.toBeNull();
    leagueId = match![1];
    
    console.log(`✅ League created with ID: ${leagueId}`);

    // Step 3: Lobby load verification
    console.log('🏠 Step 3: Verifying lobby load...');
    
    // Check lobby elements are loaded
    await expect(commissionerPage.locator('[data-testid="league-lobby"]')).toBeVisible();
    await expect(commissionerPage.locator('[data-testid="invite-section"]')).toBeVisible();
    
    // Get invite code for other users
    const inviteCodeElement = await commissionerPage.locator('[data-testid="invite-code"]');
    inviteCode = await inviteCodeElement.textContent() || '';
    expect(inviteCode).toBeTruthy();
    
    console.log(`✅ Lobby loaded with invite code: ${inviteCode}`);

    // Step 4: Users join via invite code
    console.log('👥 Step 4: Users joining via invite code...');
    
    // Alice joins
    await alicePage.goto('/app');
    await alicePage.waitForLoadState('networkidle');
    await login(alicePage, USERS.alice.email, { mode: 'test' });
    await alicePage.click('[data-testid="join-league-button"]');
    await alicePage.fill('[data-testid="invite-code-input"]', inviteCode);
    await alicePage.click('[data-testid="join-league-submit"]');
    await alicePage.waitForURL('**/leagues/**/lobby**');
    
    // Bob joins
    await bobPage.goto('/app');
    await bobPage.waitForLoadState('networkidle');  
    await login(bobPage, USERS.bob.email, { mode: 'test' });
    await bobPage.click('[data-testid="join-league-button"]');
    await bobPage.fill('[data-testid="invite-code-input"]', inviteCode);
    await bobPage.click('[data-testid="join-league-submit"]'); 
    await bobPage.waitForURL('**/leagues/**/lobby**');
    
    // Verify all users in lobby
    await expect(commissionerPage.locator('text=3/3')).toBeVisible();
    console.log('✅ All users in lobby');

    // Step 5: Start auction
    console.log('🔨 Step 5: Starting auction...');
    await commissionerPage.click('[data-testid="start-auction-button"]');
    
    // Wait for all users to navigate to auction room
    await Promise.all([
      commissionerPage.waitForURL('**/auction/**'),
      alicePage.waitForURL('**/auction/**'),
      bobPage.waitForURL('**/auction/**')
    ]);
    
    // Wait for auction room to load
    await Promise.all([
      expect(commissionerPage.locator('[data-testid="auction-room"]')).toBeVisible(),
      expect(alicePage.locator('[data-testid="auction-room"]')).toBeVisible(),
      expect(bobPage.locator('[data-testid="auction-room"]')).toBeVisible()
    ]);
    
    console.log('✅ All users in auction room');

    // Step 6: Nominate club
    console.log('🏆 Step 6: Nominating club...');
    
    // Find first available club and nominate
    const firstClub = commissionerPage.locator('[data-testid="club-item"]').first();
    await firstClub.click();
    await commissionerPage.click('[data-testid="nominate-club-button"]');
    
    // Wait for nomination to appear
    await expect(commissionerPage.locator('[data-testid="current-lot"]')).toBeVisible();
    
    const clubName = await commissionerPage.locator('[data-testid="lot-club-name"]').textContent();
    console.log(`✅ Club nominated: ${clubName}`);

    // Verify all users see the nomination
    await Promise.all([
      expect(alicePage.locator('[data-testid="current-lot"]')).toBeVisible(),
      expect(bobPage.locator('[data-testid="current-lot"]')).toBeVisible()
    ]);

    // Step 7: Two bids (different users)
    console.log('💰 Step 7: Bidding sequence...');
    
    // Alice bids first
    await alicePage.fill('[data-testid="bid-amount-input"]', '15');
    await alicePage.click('[data-testid="place-bid-button"]');
    
    // Verify bid success
    await expect(alicePage.locator('[data-testid="bid-result"]:has-text("Bid placed")')).toBeVisible({ timeout: 10000 });
    
    // Verify all users see Alice's bid
    await Promise.all([
      expect(commissionerPage.locator('[data-testid="current-bid"]:has-text("15")')).toBeVisible(),
      expect(alicePage.locator('[data-testid="current-bid"]:has-text("15")')).toBeVisible(),
      expect(bobPage.locator('[data-testid="current-bid"]:has-text("15")')).toBeVisible()
    ]);
    
    console.log('✅ Alice bid 15 credits');

    // Wait for timer to get close to expiry (for anti-snipe testing)
    console.log('⏰ Waiting for timer to approach expiry...');
    
    // Wait until timer is under 6 seconds (to trigger anti-snipe)
    let timerText = await commissionerPage.locator('[data-testid="lot-timer"]').textContent() || '0';
    let seconds = parseInt(timerText.split(':')[1] || '0');
    
    while (seconds > 6) {
      await commissionerPage.waitForTimeout(1000);
      timerText = await commissionerPage.locator('[data-testid="lot-timer"]').textContent() || '0';
      seconds = parseInt(timerText.split(':')[1] || '0');
    }
    
    console.log(`Timer at ${seconds}s - ready for anti-snipe bid`);

    // Bob places bid to trigger anti-snipe
    await bobPage.fill('[data-testid="bid-amount-input"]', '25');
    await bobPage.click('[data-testid="place-bid-button"]');
    
    // Step 8: Observe anti_snipe event
    console.log('⚡ Step 8: Observing anti-snipe extension...');
    
    // Check for anti-snipe notification or timer extension
    await Promise.all([
      expect(commissionerPage.locator('[data-testid="anti-snipe-notification"]')).toBeVisible({ timeout: 5000 }),
      expect(alicePage.locator('[data-testid="anti-snipe-notification"]')).toBeVisible({ timeout: 5000 }),
      expect(bobPage.locator('[data-testid="anti-snipe-notification"]')).toBeVisible({ timeout: 5000 })
    ]);
    
    // Verify Bob's bid is now the highest
    await Promise.all([
      expect(commissionerPage.locator('[data-testid="current-bid"]:has-text("25")')).toBeVisible(),
      expect(alicePage.locator('[data-testid="current-bid"]:has-text("25")')).toBeVisible(), 
      expect(bobPage.locator('[data-testid="current-bid"]:has-text("25")')).toBeVisible()
    ]);
    
    // Verify timer was extended (should be more than original remaining time)
    const newTimerText = await commissionerPage.locator('[data-testid="lot-timer"]').textContent() || '0';
    const newSeconds = parseInt(newTimerText.split(':')[1] || '0');
    expect(newSeconds).toBeGreaterThan(5); // Should be extended to more than 5 seconds
    
    console.log(`✅ Anti-snipe triggered! Timer extended to ${newSeconds}s, Bob leading at 25 credits`);

    // Step 9: Observe sold event
    console.log('🔔 Step 9: Waiting for sold event...');
    
    // Wait for lot to close and get sold
    await Promise.all([
      expect(commissionerPage.locator('[data-testid="lot-status"]:has-text("SOLD")')).toBeVisible({ timeout: 30000 }),
      expect(alicePage.locator('[data-testid="lot-status"]:has-text("SOLD")')).toBeVisible({ timeout: 30000 }),
      expect(bobPage.locator('[data-testid="lot-status"]:has-text("SOLD")')).toBeVisible({ timeout: 30000 })
    ]);
    
    // Verify sold notification
    await expect(commissionerPage.locator('[data-testid="sold-notification"]')).toBeVisible();
    
    // Verify Bob won the auction
    await expect(commissionerPage.locator(`[data-testid="winner"]:has-text("${USERS.bob.name}")`)).toBeVisible();
    
    console.log(`✅ ${clubName} sold to Bob for 25 credits!`);

    // Step 10: Final verification
    console.log('✅ Step 10: Final state verification...');
    
    // Verify Bob's budget updated (50 - 25 = 25 remaining)
    await expect(bobPage.locator('[data-testid="user-budget"]:has-text("25")')).toBeVisible();
    
    // Verify Alice's budget unchanged (lost auction)
    await expect(alicePage.locator('[data-testid="user-budget"]:has-text("50")')).toBeVisible();
    
    // Verify Bob has the club in roster
    await expect(bobPage.locator(`[data-testid="roster-club"]:has-text("${clubName}")`)).toBeVisible();
    
    console.log('🎉 Minimal auction smoke test completed successfully!');
    console.log('✅ Verified: auth → create league → lobby → nominate → bidding → anti-snipe → sold');
  });
});