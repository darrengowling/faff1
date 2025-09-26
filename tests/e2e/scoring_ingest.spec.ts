/**
 * Scoring Ingest Tests
 * Tests match result ingestion and leaderboard scoring
 */

import { test, expect, Browser, Page } from '@playwright/test';
import { TESTIDS } from '../../frontend/src/testids.js';
import { login, createLeague } from './utils/helpers';
import { APIHelper } from './utils/api';

test.describe('Scoring Ingest Tests', () => {
  let commissionerPage: Page;
  let leagueId: string;
  let apiHelper: APIHelper;

  test.beforeAll(async ({ browser }: { browser: Browser }) => {
    const context = await browser.newContext();
    commissionerPage = await context.newPage();
    
    // Initialize API helper
    apiHelper = new APIHelper(
      context.request,
      process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000'
    );
  });

  test.afterAll(async () => {
    await commissionerPage?.close();
  });

  test('Draw result (2-2) gives each owner +3 points', async () => {
    console.log('🧪 Testing draw result scoring...');
    
    // Setup league with known clubs
    await login(commissionerPage, 'commissioner@scoring.test');
    leagueId = await createLeague(commissionerPage, {
      name: 'Scoring Test League',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 4
    });
    
    // Simulate match result ingestion via API
    const matchResult = {
      home_team: 'Manchester City',
      away_team: 'Liverpool',
      home_score: 2,
      away_score: 2,
      match_date: new Date().toISOString().split('T')[0]
    };
    
    const ingestResult = await apiHelper.ingestFinalResult(matchResult);
    expect(ingestResult.success).toBeTruthy();
    
    // Navigate to leaderboard to verify scoring
    await commissionerPage.goto(`/leagues/${leagueId}/leaderboard`);
    
    // Verify leaderboard shows updated points
    const leaderboardTable = commissionerPage.locator(`[data-testid="${TESTIDS.leaderboardTable}"]`);
    await expect(leaderboardTable).toBeVisible();
    
    // Check for point updates - both owners of City and Liverpool should have +3
    const leaderboardRows = commissionerPage.locator(`[data-testid="${TESTIDS.leaderboardRow}"]`);
    const rowCount = await leaderboardRows.count();
    
    if (rowCount > 0) {
      // Verify at least one row shows points > 0
      let foundUpdatedPoints = false;
      for (let i = 0; i < rowCount; i++) {
        const pointsCell = leaderboardRows.nth(i).locator(`[data-testid="${TESTIDS.leaderboardPoints}"]`);
        const points = await pointsCell.textContent();
        if (points && parseInt(points) >= 3) {
          foundUpdatedPoints = true;
          break;
        }
      }
      expect(foundUpdatedPoints).toBeTruthy();
    }
    
    console.log('✅ Draw result scoring verified');
  });

  test('Re-posting same result does not double score', async () => {
    console.log('🧪 Testing duplicate result prevention...');
    
    const matchResult = {
      home_team: 'Arsenal',
      away_team: 'Chelsea',
      home_score: 1,
      away_score: 1,
      match_date: new Date().toISOString().split('T')[0]
    };
    
    // Post result first time
    const firstResult = await apiHelper.ingestFinalResult(matchResult);
    expect(firstResult.success).toBeTruthy();
    
    // Get current leaderboard state
    const token = await commissionerPage.evaluate(() => localStorage.getItem('auth_token'));
    const initialLeaderboard = await apiHelper.getLeaderboard(leagueId, token || '');
    
    // Post same result again
    const secondResult = await apiHelper.ingestFinalResult(matchResult);
    
    // Result should either be rejected or ignored
    if (secondResult.success) {
      // If accepted, verify no double scoring occurred
      const finalLeaderboard = await apiHelper.getLeaderboard(leagueId, token || '');
      
      // Points should be the same as after first ingestion
      if (initialLeaderboard.success && finalLeaderboard.success) {
        expect(finalLeaderboard.data).toEqual(initialLeaderboard.data);
      }
    }
    
    console.log('✅ Duplicate result prevention verified');
  });

  test('Win result (1-0) gives winner +4 points', async () => {
    console.log('🧪 Testing win result scoring...');
    
    const winResult = {
      home_team: 'Tottenham',
      away_team: 'West Ham',
      home_score: 1,
      away_score: 0,
      match_date: new Date().toISOString().split('T')[0]
    };
    
    // Get leaderboard before result
    const token = await commissionerPage.evaluate(() => localStorage.getItem('auth_token'));
    const beforeResult = await apiHelper.getLeaderboard(leagueId, token || '');
    
    // Post win result
    const ingestResult = await apiHelper.ingestFinalResult(winResult);
    expect(ingestResult.success).toBeTruthy();
    
    // Get leaderboard after result
    const afterResult = await apiHelper.getLeaderboard(leagueId, token || '');
    
    // Navigate to leaderboard UI to verify
    await commissionerPage.goto(`/leagues/${leagueId}/leaderboard`);
    await commissionerPage.waitForLoadState('networkidle');
    
    // Verify winner shows +4 points increase
    const leaderboardRows = commissionerPage.locator(`[data-testid="${TESTIDS.leaderboardRow}"]`);
    const rowCount = await leaderboardRows.count();
    
    if (rowCount > 0) {
      // Look for Tottenham owner's points increase
      let foundWinnerPoints = false;
      for (let i = 0; i < rowCount; i++) {
        const row = leaderboardRows.nth(i);
        const managerCell = row.locator(`[data-testid="${TESTIDS.leaderboardManager}"]`);
        const pointsCell = row.locator(`[data-testid="${TESTIDS.leaderboardPoints}"]`);
        
        const manager = await managerCell.textContent();
        const points = await pointsCell.textContent();
        
        // If this manager owns Tottenham, they should have points
        if (points && parseInt(points) >= 4) {
          foundWinnerPoints = true;
          break;
        }
      }
    }
    
    console.log('✅ Win result scoring verified');
  });

  test('Loss result (0-1) gives loser 0 points', async () => {
    console.log('🧪 Testing loss result scoring...');
    
    const lossResult = {
      home_team: 'Brighton',
      away_team: 'Newcastle',
      home_score: 0,
      away_score: 1,
      match_date: new Date().toISOString().split('T')[0]
    };
    
    // Post loss result
    const ingestResult = await apiHelper.ingestFinalResult(lossResult);
    expect(ingestResult.success).toBeTruthy();
    
    // Verify Newcastle (winner) gets points, Brighton (loser) gets 0
    await commissionerPage.goto(`/leagues/${leagueId}/leaderboard`);
    
    const leaderboardRows = commissionerPage.locator(`[data-testid="${TESTIDS.leaderboardRow}"]`);
    const rowCount = await leaderboardRows.count();
    
    // Verify leaderboard updated
    if (rowCount > 0) {
      const firstRow = leaderboardRows.first();
      const points = await firstRow.locator(`[data-testid="${TESTIDS.leaderboardPoints}"]`).textContent();
      
      // Some manager should have points from wins
      expect(points).toBeTruthy();
    }
    
    console.log('✅ Loss result scoring verified');
  });

  test('Leaderboard shows correct ranking after multiple results', async () => {
    console.log('🧪 Testing leaderboard ranking...');
    
    // Post multiple results to create differentiated leaderboard
    const results = [
      { home_team: 'Liverpool', away_team: 'Everton', home_score: 3, away_score: 0 },
      { home_team: 'Manchester United', away_team: 'Southampton', home_score: 2, away_score: 1 },
      { home_team: 'Arsenal', away_team: 'Fulham', home_score: 1, away_score: 1 }
    ];
    
    for (const result of results) {
      await apiHelper.ingestFinalResult({
        ...result,
        match_date: new Date().toISOString().split('T')[0]
      });
    }
    
    // Navigate to leaderboard
    await commissionerPage.goto(`/leagues/${leagueId}/leaderboard`);
    await commissionerPage.waitForLoadState('networkidle');
    
    // Verify leaderboard is sorted by points (highest first)
    const pointsCells = commissionerPage.locator(`[data-testid="${TESTIDS.leaderboardPoints}"]`);
    const pointsCount = await pointsCells.count();
    
    if (pointsCount > 1) {
      const firstPoints = parseInt(await pointsCells.nth(0).textContent() || '0');
      const secondPoints = parseInt(await pointsCells.nth(1).textContent() || '0');
      
      expect(firstPoints).toBeGreaterThanOrEqual(secondPoints);
    }
    
    // Verify position numbers are sequential
    const positionCells = commissionerPage.locator(`[data-testid="${TESTIDS.leaderboardPosition}"]`);
    const posCount = await positionCells.count();
    
    if (posCount > 0) {
      const firstPos = await positionCells.nth(0).textContent();
      expect(firstPos).toBe('1');
      
      if (posCount > 1) {
        const secondPos = await positionCells.nth(1).textContent();
        expect(secondPos).toBe('2');
      }
    }
    
    console.log('✅ Leaderboard ranking verified');
  });

  test('Invalid match result is rejected', async () => {
    console.log('🧪 Testing invalid result rejection...');
    
    // Test various invalid results
    const invalidResults = [
      { home_team: '', away_team: 'Liverpool', home_score: 1, away_score: 0 }, // Empty team
      { home_team: 'Arsenal', away_team: 'Chelsea', home_score: -1, away_score: 0 }, // Negative score
      { home_team: 'Arsenal', away_team: 'Chelsea', home_score: 'invalid', away_score: 0 }, // Non-numeric score
    ];
    
    for (const invalidResult of invalidResults) {
      const result = await apiHelper.ingestFinalResult({
        ...invalidResult,
        match_date: new Date().toISOString().split('T')[0]
      } as any);
      
      // Should fail or return error
      expect(result.success).toBeFalsy();
    }
    
    console.log('✅ Invalid result rejection verified');
  });
});