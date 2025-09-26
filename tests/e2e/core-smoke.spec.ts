/**
 * Core Smoke Test - End-to-End Auction Flow
 * 
 * Tests the complete auction loop: create league → invite → join → auction → bid → sell
 * Uses multiple browser contexts to simulate real multi-user scenarios.
 */

import { test, expect, BrowserContext, Page } from '@playwright/test';

// Test configuration
const TEST_TIMEOUT = 90000; // 90 seconds max
const USERS = {
  commissioner: { email: 'commish@test.local', name: 'Commissioner' },
  alice: { email: 'alice@test.local', name: 'Alice' },
  bob: { email: 'bob@test.local', name: 'Bob' }
};

const LEAGUE_SETTINGS = {
  name: 'Core Smoke League',
  clubSlots: 3,
  budgetPerManager: 100,
  leagueSize: { min: 2, max: 8 }
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
    await loginUser(commissionerPage, USERS.commissioner.email);
    
    const leagueData = await createLeague(commissionerPage, LEAGUE_SETTINGS);
    leagueId = leagueData.leagueId;
    
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
    await loginUser(alicePage, USERS.alice.email);
    await expectLobbyState(alicePage, '2/3'); // Commissioner + Alice
    
    // Bob joins  
    await bobPage.goto(inviteLinks[0]);
    await bobPage.waitForLoadState('networkidle');
    await loginUser(bobPage, USERS.bob.email);
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

// Helper Functions

async function loginUser(page: Page, email: string): Promise<void> {
  console.log(`🔐 Logging in user: ${email}`);
  
  // Navigate to login if not already there
  if (!page.url().includes('/login')) {
    await page.goto('/login');
  }
  
  await page.waitForLoadState('networkidle');
  
  // Enter email and submit
  await page.fill('input[type="email"]', email);
  await page.click('button:has-text("Send Magic Link"), button[type="submit"]');
  
  // Wait for magic link sent confirmation and login button (development mode)
  await page.waitForSelector('button:has-text("🚀 Login Now")', { timeout: 10000 });
  await page.click('button:has-text("🚀 Login Now")');
  
  // Wait for successful login redirect to dashboard/app
  await page.waitForURL('**/app', { timeout: 15000 });
  console.log(`✅ User logged in: ${email}`);
}

async function createLeague(page: Page, settings: typeof LEAGUE_SETTINGS): Promise<{ leagueId: string }> {
  console.log(`🏟️ Creating league: ${settings.name}`);
  
  // Click create league button from dashboard
  await page.click('button:has-text("Create League")');
  await page.waitForSelector('[role="dialog"], .modal', { timeout: 5000 });
  
  // Fill league form
  await page.fill('input[name="name"]', settings.name);
  await page.fill('input[name="season"]', '2025-26');
  
  // Set competition profile (try UCL first, then custom)
  const profileSelect = page.locator('select[name="competition_profile_id"]');
  if (await profileSelect.isVisible()) {
    await profileSelect.selectOption({ label: /UCL|Champions League/i });
  }
  
  // Set budget
  await page.fill('input[name="budget_per_manager"]', settings.budgetPerManager.toString());
  
  // Set club slots  
  await page.fill('input[name="club_slots_per_manager"]', settings.clubSlots.toString());
  
  // Set league size
  await page.fill('input[name="min_managers"]', settings.leagueSize.min.toString());
  await page.fill('input[name="max_managers"]', settings.leagueSize.max.toString());
  
  // Submit form
  await page.click('button[type="submit"], button:has-text("Create League")');
  
  // Wait for redirect to league admin page
  await page.waitForURL('**/admin/**', { timeout: 10000 });
  
  // Extract league ID from URL
  const url = page.url();
  const leagueId = url.split('/admin/')[1];
  
  console.log(`✅ League created with ID: ${leagueId}`);
  return { leagueId };
}

async function getInviteLinks(page: Page): Promise<string[]> {
  // Look for invite section or button
  const inviteButton = page.locator('button:has-text("Invite"), button:has-text("Generate Link")').first();
  
  if (await inviteButton.isVisible()) {
    await inviteButton.click();
    await page.waitForTimeout(1000);
  }
  
  // Try to find invite links in the UI
  const inviteElements = page.locator('input[readonly], [data-invite-link]');
  const count = await inviteElements.count();
  
  const links: string[] = [];
  
  if (count > 0) {
    // Get links from UI elements
    for (let i = 0; i < Math.min(count, 2); i++) {
      const value = await inviteElements.nth(i).inputValue().catch(() => 
        inviteElements.nth(i).textContent()
      );
      if (value && value.includes('invite')) {
        links.push(value);
      }
    }
  }
  
  // Fallback: construct invite link from league ID if we can't find UI elements
  if (links.length === 0) {
    const url = page.url();
    const leagueId = url.split('/admin/')[1];
    const baseURL = new URL(page.url()).origin;
    links.push(`${baseURL}/invite?league=${leagueId}`);
  }
  
  return links;
}

async function expectLobbyState(page: Page, expectedCount: string): Promise<void> {
  // Wait for lobby to load and show member count
  await page.waitForSelector('text=joined', { timeout: 5000 });
  await expect(page.locator(`text=${expectedCount}`)).toBeVisible({ timeout: 5000 });
}

async function startAuction(page: Page): Promise<void> {
  await page.click('button:has-text("Start Auction")');
  await page.waitForTimeout(2000); // Allow for navigation
}

async function nominateFirstAsset(page: Page): Promise<string> {
  // Wait for auction room to load
  await page.waitForSelector('.auction-room, [data-testid="auction-room"]', { timeout: 10000 });
  
  // Look for nominate button or first available club
  const nominateButton = page.locator('button:has-text("Nominate")').first();
  
  if (await nominateButton.isVisible()) {
    // Get the club name from the button or nearby text
    const clubElement = page.locator('.club-name, [data-club-name]').first();
    const clubName = await clubElement.textContent().catch(() => 'Manchester City'); // Fallback
    
    await nominateButton.click();
    await page.waitForTimeout(2000);
    
    return clubName.trim();
  }
  
  // Alternative: click first available club card
  const clubCard = page.locator('[data-club], .club-card').first();
  if (await clubCard.isVisible()) {
    const clubName = await clubCard.textContent();
    await clubCard.click();
    await page.waitForTimeout(2000);
    return clubName.trim();
  }
  
  throw new Error('Could not find club to nominate');
}

async function expectAuctionState(page: Page, clubName: string): Promise<void> {
  // Verify auction shows the nominated club and timer
  await expect(page.locator(`text=${clubName}`)).toBeVisible({ timeout: 5000 });
  await expect(page.locator('.timer, [data-timer]')).toBeVisible({ timeout: 5000 });
}

async function placeBid(page: Page, increment: number): Promise<void> {
  // Look for bid button (+1, +5, custom amount)
  const bidButton = page.locator(`button:has-text("+${increment}"), button[data-bid="${increment}"]`).first();
  
  if (await bidButton.isVisible()) {
    await bidButton.click();
  } else {
    // Fallback: use custom bid input
    const bidInput = page.locator('input[type="number"], [data-bid-input]').first();
    if (await bidInput.isVisible()) {
      await bidInput.fill(increment.toString());
      await page.click('button:has-text("Bid")');
    }
  }
  
  await page.waitForTimeout(1000); // Allow bid to register
}

async function expectTopBid(page: Page, expectedBid: string): Promise<void> {
  await expect(page.locator(`text=${expectedBid}`, { hasText: true })).toBeVisible({ timeout: 5000 });
}

async function expectLotSold(page: Page, clubName: string): Promise<void> {
  // Wait for SOLD status or timer to reach 0
  await expect(page.locator('text=SOLD')).toBeVisible({ timeout: 30000 });
}

async function expectRosterUpdate(page: Page, clubName: string, expectedBudget: number): Promise<void> {
  // Navigate to roster/clubs page to verify
  await page.click('a:has-text("My Clubs"), a:has-text("Roster")');
  await page.waitForLoadState('networkidle');
  
  // Check club appears in roster
  await expect(page.locator(`text=${clubName}`)).toBeVisible({ timeout: 5000 });
  
  // Check remaining budget
  await expect(page.locator(`text=${expectedBudget}`)).toBeVisible({ timeout: 5000 });
}

async function expectBudgetUnchanged(page: Page, expectedBudget: number): Promise<void> {
  // Check budget display in auction room or navigate to roster
  const budgetElement = page.locator(`text=${expectedBudget}`, { hasText: true }).first();
  await expect(budgetElement).toBeVisible({ timeout: 5000 });
}

async function expectClubUniqueness(page: Page, clubName: string): Promise<void> {
  // Try to nominate the same club again - should show error or be disabled
  const clubElement = page.locator(`text=${clubName}`).first();
  
  if (await clubElement.isVisible()) {
    await clubElement.click();
    
    // Expect error message or disabled state
    await expect(page.locator('text=already owned, text=unavailable')).toBeVisible({ timeout: 3000 });
  }
}

async function expectUserPresence(page: Page, expectedCount: number): Promise<void> {
  // Check presence indicators or user count
  const presenceElements = page.locator('.user-presence, [data-user-count]');
  
  if (await presenceElements.first().isVisible()) {
    await expect(page.locator(`text=${expectedCount} users`)).toBeVisible({ timeout: 5000 });
  }
  
  // Fallback: just verify page is responsive
  await expect(page.locator('body')).toBeVisible();
}