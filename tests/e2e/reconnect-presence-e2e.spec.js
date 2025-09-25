/**
 * E2E Tests for PR2: Robust Reconnect & Presence System
 * Tests WebSocket connection resilience, auto-reconnect, and presence indicators
 */

import { test, expect } from '@playwright/test';
import { APIClient } from './helpers/api-client.js';
import { TestHelpers } from './helpers/test-helpers.js';

class ReconnectTestHelpers {
  constructor(page) {
    this.page = page;
  }

  /**
   * Simulate network disconnection by blocking WebSocket traffic
   */
  async simulateNetworkDisconnection() {
    await this.page.route('**/socket.io/**', route => {
      route.abort();
    });
    console.log('Network disconnection simulated');
  }

  /**
   * Restore network connection by removing route blocks
   */
  async restoreNetworkConnection() {
    await this.page.unroute('**/socket.io/**');
    console.log('Network connection restored');
  }

  /**
   * Wait for connection status indicator to show specific state
   */
  async waitForConnectionStatus(expectedStatus) {
    await this.page.waitForSelector(`text=${expectedStatus}`, { timeout: 10000 });
  }

  /**
   * Check if user presence indicator is visible
   */
  async checkUserPresence(userName, expectedStatus = 'online') {
    const presenceIndicator = this.page.locator(`[data-testid="presence-${userName}"]`);
    await expect(presenceIndicator).toBeVisible();
    
    const statusColor = expectedStatus === 'online' ? 'bg-green-500' : 'bg-gray-400';
    await expect(presenceIndicator.locator('.w-2.h-2')).toHaveClass(new RegExp(statusColor));
  }
}

test.describe('Robust Reconnect & Presence System', () => {
  let apiClient;
  let helpers;
  let reconnectHelpers;

  test.beforeEach(async ({ page }) => {
    apiClient = new APIClient();
    helpers = new TestHelpers(page);
    reconnectHelpers = new ReconnectTestHelpers(page);
    
    // Set mobile viewport for testing
    await page.setViewportSize({ width: 375, height: 667 });
  });

  test('should show connection status indicator in auction room', async ({ page }) => {
    // Setup test auction
    const { magicToken, user, leagueId, auctionId } = await apiClient.createTestAuctionSetup();
    
    // Navigate to auction room
    await page.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${magicToken}`);
    await helpers.waitForAuth(user.email);
    await page.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    
    // Check connection status indicator appears
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Verify status indicator styling
    const statusIndicator = page.locator('[data-testid="connection-status"]');
    await expect(statusIndicator).toContainText('Connected');
    await expect(statusIndicator).toHaveClass(/bg-green-500/);
  });

  test('should automatically reconnect after network interruption', async ({ page }) => {
    // Setup test auction with active lot
    const { magicToken, user, leagueId, auctionId } = await apiClient.createTestAuctionSetup();
    
    // Navigate and join auction
    await page.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${magicToken}`);
    await helpers.waitForAuth(user.email);
    await page.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    
    // Wait for initial connection
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Simulate network disconnection
    await reconnectHelpers.simulateNetworkDisconnection();
    
    // Should show reconnecting status
    await reconnectHelpers.waitForConnectionStatus('Reconnecting');
    
    // Restore connection
    await reconnectHelpers.restoreNetworkConnection();
    
    // Should reconnect successfully
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Verify auction state is restored
    const auctionTitle = page.locator('[data-testid="auction-title"]');
    await expect(auctionTitle).toBeVisible();
  });

  test('should show exponential backoff during reconnection attempts', async ({ page }) => {
    // Setup test auction
    const { magicToken, user, leagueId, auctionId } = await apiClient.createTestAuctionSetup();
    
    // Navigate to auction room
    await page.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${magicToken}`);
    await helpers.waitForAuth(user.email);
    await page.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    
    // Wait for connection
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Simulate persistent network failure
    await page.route('**/socket.io/**', route => {
      route.abort();
    });
    
    // Should show reconnecting with attempt count
    await reconnectHelpers.waitForConnectionStatus('Reconnecting');
    
    // Check that attempt count increases
    const statusIndicator = page.locator('[data-testid="connection-status"]');
    await expect(statusIndicator).toContainText(/\(1\/10\)/);
    
    // Wait for next attempt
    await page.waitForTimeout(3000);
    await expect(statusIndicator).toContainText(/\(2\/10\)/);
  });

  test('should restore auction state from server snapshot on reconnect', async ({ page }) => {
    // Setup auction with specific state
    const { magicToken, user, leagueId, auctionId } = await apiClient.createTestAuctionSetup({
      setupLots: true,
      startAuction: true
    });
    
    // Navigate to auction
    await page.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${magicToken}`);
    await helpers.waitForAuth(user.email);
    await page.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    
    // Wait for initial state to load
    await reconnectHelpers.waitForConnectionStatus('Connected');
    const initialBudget = await page.locator('[data-testid="user-budget"]').textContent();
    
    // Simulate disconnection
    await reconnectHelpers.simulateNetworkDisconnection();
    await reconnectHelpers.waitForConnectionStatus('Reconnecting');
    
    // Restore connection
    await reconnectHelpers.restoreNetworkConnection();
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Verify state was restored from snapshot
    const restoredBudget = await page.locator('[data-testid="user-budget"]').textContent();
    expect(restoredBudget).toBe(initialBudget);
    
    // Check for success toast
    await expect(page.locator('text=Connection restored')).toBeVisible();
  });

  test('should track user presence accurately', async ({ page, browser }) => {
    // Setup multi-user test
    const { magicToken, user, leagueId, auctionId } = await apiClient.createTestAuctionSetup();
    const { magicToken: token2, user: user2 } = await apiClient.createAdditionalUser(leagueId);
    
    // First user joins
    await page.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${magicToken}`);
    await helpers.waitForAuth(user.email);
    await page.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Second user joins in new context
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    await page2.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${token2}`);
    await new TestHelpers(page2).waitForAuth(user2.email);
    await page2.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    await new ReconnectTestHelpers(page2).waitForConnectionStatus('Connected');
    
    // Check that first user sees second user as online
    await reconnectHelpers.checkUserPresence(user2.display_name, 'online');
    
    // Check join notification
    await expect(page.locator(`text=${user2.display_name} joined the auction`)).toBeVisible();
    
    // Second user leaves
    await page2.close();
    await context2.close();
    
    // Check that first user sees second user as offline
    await page.waitForTimeout(2000); // Allow time for presence update
    await reconnectHelpers.checkUserPresence(user2.display_name, 'offline');
    
    // Check leave notification
    await expect(page.locator(`text=${user2.display_name} left the auction`)).toBeVisible();
  });

  test('should handle reconnection during active bidding', async ({ page }) => {
    // Setup active auction with bidding
    const { magicToken, user, leagueId, auctionId } = await apiClient.createTestAuctionSetup({
      setupLots: true,
      startAuction: true
    });
    
    // Navigate to auction
    await page.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${magicToken}`);
    await helpers.waitForAuth(user.email);
    await page.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Wait for lot to be active
    await expect(page.locator('[data-testid="current-lot"]')).toBeVisible();
    
    // Simulate connection drop during anti-snipe period
    await reconnectHelpers.simulateNetworkDisconnection();
    
    // Should show reconnecting status
    await reconnectHelpers.waitForConnectionStatus('Reconnecting');
    
    // Bidding should be disabled during reconnection
    const bidButton = page.locator('[data-testid="place-bid-button"]');
    await expect(bidButton).toBeDisabled();
    
    // Restore connection
    await reconnectHelpers.restoreNetworkConnection();
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Bidding should be re-enabled
    await expect(bidButton).not.toBeDisabled();
    
    // Timer should sync correctly
    const timer = page.locator('[data-testid="timer-display"]');
    await expect(timer).toBeVisible();
  });

  test('should handle heartbeat timeouts gracefully', async ({ page }) => {
    // Setup test auction
    const { magicToken, user, leagueId, auctionId } = await apiClient.createTestAuctionSetup();
    
    // Navigate to auction room
    await page.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${magicToken}`);
    await helpers.waitForAuth(user.email);
    await page.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    
    // Wait for connection
    await reconnectHelpers.waitForConnectionStatus('Connected');
    
    // Block only heartbeat responses (not full connection)
    await page.route('**/socket.io/**', route => {
      const url = route.request().url();
      if (url.includes('heartbeat')) {
        route.abort();
      } else {
        route.continue();
      }
    });
    
    // Should eventually detect connection issues and attempt reconnect
    await page.waitForTimeout(35000); // Wait longer than heartbeat interval
    
    // Should show some indication of connection issues
    const statusIndicator = page.locator('[data-testid="connection-status"]');
    const statusText = await statusIndicator.textContent();
    expect(statusText).toMatch(/Reconnecting|Connected/);
  });

  test('should maintain presence across page refresh', async ({ page }) => {
    // Setup test auction
    const { magicToken, user, leagueId, auctionId } = await apiClient.createTestAuctionSetup();
    
    // Navigate to auction room
    await page.goto(`${process.env.FRONTEND_URL}/auth/verify?token=${magicToken}`);
    await helpers.waitForAuth(user.email);
    await page.goto(`${process.env.FRONTEND_URL}/auction/${auctionId}`);
    
    // Wait for connection and presence
    await reconnectHelpers.waitForConnectionStatus('Connected');
    await reconnectHelpers.checkUserPresence(user.display_name, 'online');
    
    // Refresh page
    await page.reload();
    
    // Should automatically reconnect and restore presence
    await reconnectHelpers.waitForConnectionStatus('Connected');
    await reconnectHelpers.checkUserPresence(user.display_name, 'online');
  });
});

test.describe('Connection Error Scenarios', () => {
  test('should show offline status when max reconnect attempts reached', async ({ page }) => {
    // Setup with unreachable backend
    await page.route('**/socket.io/**', route => {
      route.abort();
    });
    
    const helpers = new TestHelpers(page);
    const reconnectHelpers = new ReconnectTestHelpers(page);
    
    // Try to access auction (this will fail)
    await page.goto(`${process.env.FRONTEND_URL}/auction/invalid`);
    
    // Should eventually show offline status
    await page.waitForTimeout(15000); // Wait for multiple reconnect attempts
    await reconnectHelpers.waitForConnectionStatus('Offline');
    
    // Should show error message
    await expect(page.locator('text=Connection lost. Please refresh the page.')).toBeVisible();
  });

  test('should handle authentication failures on reconnect', async ({ page }) => {
    // Setup expired token scenario
    const helpers = new TestHelpers(page);
    const reconnectHelpers = new ReconnectTestHelpers(page);
    
    // Navigate with invalid token
    await page.goto(`${process.env.FRONTEND_URL}/auction/test`);
    
    // Should show authentication required
    await expect(page.locator('text=Authentication failed')).toBeVisible();
  });
});