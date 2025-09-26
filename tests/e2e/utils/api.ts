/**
 * API Utilities for E2E Tests
 * Direct API calls for test data manipulation and verification
 */

import { APIRequestContext } from '@playwright/test';

export class APIHelper {
  private request: APIRequestContext;
  private baseURL: string;
  
  constructor(request: APIRequestContext, baseURL: string) {
    this.request = request;
    this.baseURL = baseURL;
  }
  
  /**
   * Ingest final match result for scoring
   */
  async ingestFinalResult(matchData: {
    home_team: string;
    away_team: string;
    home_score: number;
    away_score: number;
    match_date: string;
  }) {
    const response = await this.request.post(`${this.baseURL}/api/ingest/final_result`, {
      data: matchData
    });
    
    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }
  
  /**
   * Get leaderboard data for verification
   */
  async getLeaderboard(leagueId: string, token: string) {
    const response = await this.request.get(`${this.baseURL}/api/leagues/${leagueId}/leaderboard`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }
  
  /**
   * Get league roster for verification
   */
  async getLeagueRoster(leagueId: string, token: string) {
    const response = await this.request.get(`${this.baseURL}/api/leagues/${leagueId}/roster`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }
  
  /**
   * Get league members
   */
  async getLeagueMembers(leagueId: string, token: string) {
    const response = await this.request.get(`${this.baseURL}/api/leagues/${leagueId}/members`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }
  
  /**
   * Get auction status
   */
  async getAuctionStatus(auctionId: string, token: string) {
    const response = await this.request.get(`${this.baseURL}/api/auctions/${auctionId}/status`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return {
      success: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  }
  
  /**
   * Clean up test data (for teardown)
   */
  async cleanupTestData(testPrefix: string) {
    // Implementation depends on backend cleanup endpoints
    console.log(`🧹 Cleaning up test data with prefix: ${testPrefix}`);
  }
}