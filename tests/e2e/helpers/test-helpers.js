const { expect } = require('@playwright/test');
const APIClient = require('./api-client');

class TestHelpers {
  constructor(page, context) {
    this.page = page;
    this.context = context;
    this.api = new APIClient();
    this.testData = {
      users: [],
      leagues: [],
      tokens: {}
    };
  }

  // Test fixture setup
  async setupTestFixtures() {
    console.log('🏗️ Setting up test fixtures...');
    
    // Create test users
    const testUsers = [
      { email: 'commish@test.local', role: 'commissioner' },
      { email: 'alice@test.local', role: 'manager' },
      { email: 'bob@test.local', role: 'manager' }
    ];

    for (const user of testUsers) {
      const result = await this.createTestUser(user.email);
      if (result.success) {
        this.testData.users.push({
          ...user,
          id: result.userId,
          token: result.token
        });
        console.log(`✅ Created test user: ${user.email}`);
      } else {
        throw new Error(`Failed to create test user ${user.email}: ${result.error}`);
      }
    }

    // Create test league
    const commissioner = this.testData.users.find(u => u.role === 'commissioner');
    this.api.setAuthToken(commissioner.token);
    
    const leagueData = {
      name: 'E2E Test League 2025-26',
      season: '2025-26',
      settings: {
        club_slots_per_manager: 3,
        budget_per_manager: 100,
        league_size: { min: 2, max: 8 }
      }
    };

    const leagueResult = await this.api.createLeague(leagueData);
    if (leagueResult.success) {
      this.testData.leagues.push({
        id: leagueResult.data.id,
        name: leagueData.name,
        commissioner_id: commissioner.id
      });
      console.log(`✅ Created test league: ${leagueData.name}`);
    } else {
      throw new Error(`Failed to create test league: ${leagueResult.error}`);
    }

    console.log('🎉 Test fixtures ready!');
    return this.testData;
  }

  async createTestUser(email) {
    try {
      // Request magic link
      const linkResult = await this.api.requestMagicLink(email);
      if (!linkResult.success) {
        return { success: false, error: `Magic link request failed: ${linkResult.error}` };
      }

      // Extract token from email/logs simulation
      const token = this.generateTestToken(email);
      
      // Verify magic link (simulate)
      const verifyResult = await this.api.verifyMagicLink(token);
      if (verifyResult.success) {
        return {
          success: true,
          userId: verifyResult.data.user.id,
          token: verifyResult.data.access_token
        };
      } else {
        return { success: false, error: `Magic link verification failed: ${verifyResult.error}` };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  generateTestToken(email) {
    // Generate a consistent test token for simulation
    const base64Email = Buffer.from(email).toString('base64');
    return `test_token_${base64Email}_${Date.now()}`;
  }

  // Auth helpers
  async loginUser(email) {
    console.log(`🔐 Logging in user: ${email}`);
    
    await this.page.goto('/');
    await this.page.click('text=Login');
    await this.page.fill('input[type="email"]', email);
    await this.page.click('button[type="submit"]');
    
    // Wait for magic link message
    await expect(this.page.locator('text=Check your email')).toBeVisible();
    
    // Simulate clicking magic link by directly navigating
    const user = this.testData.users.find(u => u.email === email);
    if (user && user.token) {
      await this.page.goto(`/auth/verify?token=${user.token}`);
      await expect(this.page.locator('text=League' || 'text=Dashboard')).toBeVisible({ timeout: 10000 });
      console.log(`✅ User logged in: ${email}`);
      return true;
    }
    
    throw new Error(`Failed to login user: ${email}`);
  }

  // League helpers
  async createLeague(leagueData) {
    console.log(`🏟️ Creating league: ${leagueData.name}`);
    
    await this.page.click('text=Create League');
    await this.page.fill('input[name="name"]', leagueData.name);
    await this.page.fill('input[name="season"]', leagueData.season);
    
    if (leagueData.settings) {
      await this.page.fill('input[name="budget_per_manager"]', leagueData.settings.budget_per_manager.toString());
      await this.page.fill('input[name="club_slots_per_manager"]', leagueData.settings.club_slots_per_manager.toString());
      await this.page.fill('input[name="min_managers"]', leagueData.settings.league_size.min.toString());
      await this.page.fill('input[name="max_managers"]', leagueData.settings.league_size.max.toString());
    }
    
    await this.page.click('button[type="submit"]');
    await expect(this.page.locator('text=League created successfully' || 'text=Dashboard')).toBeVisible();
    
    console.log(`✅ League created successfully`);
  }

  async inviteMembers(emails) {
    console.log(`📧 Inviting members: ${emails.join(', ')}`);
    
    await this.page.click('text=Invite Members');
    
    for (const email of emails) {
      await this.page.fill('input[placeholder*="email"]', email);
      await this.page.press('input[placeholder*="email"]', 'Enter');
    }
    
    await this.page.click('text=Send Invitations');
    await expect(this.page.locator('text=Invitations sent')).toBeVisible();
    
    console.log(`✅ Invitations sent successfully`);
  }

  async acceptInvitation(userEmail, leagueId) {
    console.log(`✉️ Accepting invitation for: ${userEmail}`);
    
    // Switch to user's context
    await this.loginUser(userEmail);
    
    // Navigate to invitations or direct league join
    await this.page.goto(`/leagues/${leagueId}/join`);
    await this.page.click('text=Accept Invitation' || 'text=Join League');
    
    await expect(this.page.locator('text=Welcome to the league' || 'text=League Dashboard')).toBeVisible();
    console.log(`✅ Invitation accepted by: ${userEmail}`);
  }

  // Auction helpers
  async startAuction() {
    console.log(`🎪 Starting auction...`);
    
    await this.page.click('text=Admin' || 'text=Manage League');
    await this.page.click('text=Start Auction');
    
    await expect(this.page.locator('text=Auction started' || 'text=Live Auction')).toBeVisible();
    console.log(`✅ Auction started successfully`);
  }

  async placeBid(amount) {
    console.log(`💰 Placing bid: ${amount}`);
    
    await this.page.fill('input[placeholder*="amount" || placeholder*="bid"]', amount.toString());
    await this.page.click('text=Place Bid' || 'button[type="submit"]');
    
    // Wait for bid confirmation
    await expect(this.page.locator(`text=${amount}` || 'text=Bid placed')).toBeVisible();
    console.log(`✅ Bid placed: ${amount}`);
  }

  async waitForTimerUpdate(expectedSeconds) {
    console.log(`⏱️ Waiting for timer: ${expectedSeconds}s`);
    
    // Wait for timer element and check value
    const timer = this.page.locator('[data-testid="auction-timer"] || text=seconds');
    await expect(timer).toBeVisible();
    
    // Check if timer shows expected value
    await expect(timer).toContainText(expectedSeconds.toString(), { timeout: 2000 });
    console.log(`✅ Timer updated to: ${expectedSeconds}s`);
  }

  async pauseAuction() {
    console.log(`⏸️ Pausing auction...`);
    
    await this.page.click('text=Pause Auction');
    await expect(this.page.locator('text=Auction paused' || 'text=Paused')).toBeVisible();
    console.log(`✅ Auction paused`);
  }

  async resumeAuction() {
    console.log(`▶️ Resuming auction...`);
    
    await this.page.click('text=Resume Auction');
    await expect(this.page.locator('text=Auction resumed' || 'text=Live')).toBeVisible();
    console.log(`✅ Auction resumed`);
  }

  // Scoring helpers
  async ingestMatchResult(resultData) {
    console.log(`⚽ Ingesting match result: ${resultData.homeExt} ${resultData.homeGoals}-${resultData.awayGoals} ${resultData.awayExt}`);
    
    const result = await this.api.ingestResult(resultData);
    if (result.success) {
      console.log(`✅ Match result ingested successfully`);
      return result.data;
    } else {
      throw new Error(`Failed to ingest result: ${result.error}`);
    }
  }

  async verifyScoring(expectedPoints) {
    console.log(`📊 Verifying scoring: ${JSON.stringify(expectedPoints)}`);
    
    await this.page.goto('/my-clubs');
    
    for (const [userEmail, points] of Object.entries(expectedPoints)) {
      if (userEmail === this.getCurrentUserEmail()) {
        await expect(this.page.locator(`text=${points} points` || `text=Total: ${points}`)).toBeVisible();
      }
    }
    
    console.log(`✅ Scoring verified`);
  }

  // Navigation helpers
  async navigateToMyClubs() {
    await this.page.click('text=My Clubs');
    await expect(this.page.locator('text=My Clubs' || 'text=Budget Remaining')).toBeVisible();
  }

  async navigateToFixtures() {
    await this.page.click('text=Fixtures');
    await expect(this.page.locator('text=Fixtures' || 'text=Match Results')).toBeVisible();
  }

  async navigateToLeaderboard() {
    await this.page.click('text=Leaderboard');
    await expect(this.page.locator('text=Leaderboard' || 'text=Total Points')).toBeVisible();
  }

  // Verification helpers
  async verifyAccessControl(restrictedEndpoint, expectedError = 'Unauthorized') {
    console.log(`🔒 Verifying access control for: ${restrictedEndpoint}`);
    
    // Clear auth token
    this.api.setAuthToken(null);
    
    const result = await this.api.request('GET', restrictedEndpoint);
    expect(result.success).toBe(false);
    expect(result.status).toBe(401 || 403);
    
    console.log(`✅ Access control verified - unauthorized access blocked`);
  }

  getCurrentUserEmail() {
    // Get current user email from test context
    return this.context.currentUser?.email || 'unknown@test.local';
  }

  // Cleanup helpers
  async cleanupTestData() {
    console.log('🧹 Cleaning up test data...');
    
    try {
      // Delete leagues
      for (const league of this.testData.leagues) {
        await this.api.deleteLeague(league.id);
        console.log(`✅ Deleted league: ${league.name}`);
      }
      
      // Delete users
      for (const user of this.testData.users) {
        await this.api.deleteUser(user.id);
        console.log(`✅ Deleted user: ${user.email}`);
      }
      
      console.log('🎉 Cleanup completed!');
    } catch (error) {
      console.warn(`⚠️ Cleanup warning: ${error.message}`);
    }
  }

  // Utility methods
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async takeScreenshot(name) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }
}

module.exports = TestHelpers;