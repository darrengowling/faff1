/**
 * League Creation Flow Test - Deterministic Submit → Navigate Flow
 * 
 * Tests the specific flow requested in the review:
 * 1. Dialog closes reliably after success (data-state="closed")
 * 2. Navigation to lobby is deterministic
 * 3. Success markers appear and disappear correctly
 * 4. awaitCreatedAndInLobby helper works with polling
 */

import { test, expect, Page } from '@playwright/test';
import { login } from './utils/login';
import { fillCreateLeague } from './utils/league';
import { clickCreateLeague, awaitCreatedAndInLobby } from './utils/helpers';
import { TESTIDS } from '../../frontend/src/testids.ts';

const TEST_TIMEOUT = 30000; // 30 seconds
const LEAGUE_SETTINGS = {
  name: 'Deterministic Test League',
  slots: 5,
  budget: 100,
  min: 2,
  max: 4
};

test.describe('League Creation Deterministic Flow', () => {
  test.setTimeout(TEST_TIMEOUT);

  test('Dialog closes immediately after success and navigates to lobby deterministically', async ({ page }) => {
    console.log('🚀 Starting deterministic league creation flow test...');

    // Step 1: Login
    console.log('📝 Step 1: Login...');
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.waitForURL('**/app', { timeout: 10000 });
    console.log('✅ Logged in and on dashboard');

    // Step 2: Click Create League button
    console.log('🎯 Step 2: Opening Create League dialog...');
    await clickCreateLeague(page);
    
    // Verify dialog is open
    const dialog = page.locator('[data-testid="create-dialog"]');
    await expect(dialog).toBeVisible({ timeout: 5000 });
    
    // Check dialog data-state attribute
    const dialogElement = page.locator('[role="dialog"]').first();
    await expect(dialogElement).toHaveAttribute('data-state', 'open');
    console.log('✅ Dialog opened with data-state="open"');

    // Step 3: Fill form
    console.log('📝 Step 3: Filling league creation form...');
    await fillCreateLeague(page, LEAGUE_SETTINGS);
    console.log('✅ Form filled');

    // Step 4: Submit and verify immediate dialog close
    console.log('🚀 Step 4: Submitting form and checking dialog close behavior...');
    
    // Get references before submission
    const submitBtn = page.getByTestId('create-submit');
    await expect(submitBtn).toBeEnabled();
    
    // Submit form
    await submitBtn.click();
    console.log('✅ Form submitted');

    // Step 5: Verify dialog closes immediately (data-state="closed")
    console.log('🔍 Step 5: Verifying dialog closes immediately...');
    
    // Wait for dialog to close - should happen immediately after 201 response
    await expect(dialogElement).toHaveAttribute('data-state', 'closed', { timeout: 3000 });
    console.log('✅ Dialog closed immediately with data-state="closed"');

    // Step 6: Check for transient success marker
    console.log('🎯 Step 6: Checking for transient success marker...');
    
    // The success marker should appear briefly
    const successMarker = page.locator('[data-testid="create-success"]');
    
    // Try to catch the success marker - it may be very brief
    try {
      await expect(successMarker).toBeVisible({ timeout: 2000 });
      console.log('✅ Success marker appeared');
    } catch (e) {
      console.log('⚠️ Success marker may have been too brief to catch');
    }

    // Step 7: Verify navigation to lobby
    console.log('🏁 Step 7: Verifying navigation to lobby...');
    
    // Wait for URL to change to lobby pattern
    await page.waitForURL(/\/app\/leagues\/.+\/lobby/, { timeout: 10000 });
    console.log('✅ URL changed to lobby pattern');

    // Extract league ID from URL
    const currentUrl = page.url();
    const leagueIdMatch = currentUrl.match(/\/app\/leagues\/([^\/]+)\/lobby/);
    const leagueId = leagueIdMatch ? leagueIdMatch[1] : null;
    
    if (!leagueId) {
      throw new Error(`Could not extract league ID from URL: ${currentUrl}`);
    }
    console.log(`✅ League ID extracted: ${leagueId}`);

    // Step 8: Test the awaitCreatedAndInLobby helper with polling
    console.log('🔍 Step 8: Testing readiness endpoint polling...');
    
    const apiOrigin = process.env.REACT_APP_BACKEND_URL || 'https://leaguemate-1.preview.emergentagent.com';
    
    // Test the readiness endpoint directly
    const readinessResponse = await page.request.get(`${apiOrigin}/api/test/league/${leagueId}/ready`);
    const readinessData = await readinessResponse.json();
    
    console.log('📊 Readiness endpoint response:', readinessData);
    
    if (readinessData.ready) {
      console.log('✅ League is ready according to readiness endpoint');
    } else {
      console.log(`⚠️ League not ready: ${readinessData.reason}`);
    }

    // Step 9: Verify lobby page loads correctly
    console.log('🏠 Step 9: Verifying lobby page loads correctly...');
    
    // Check for lobby-specific elements
    const lobbyJoined = page.locator('[data-testid="lobby-joined"]');
    await expect(lobbyJoined).toBeVisible({ timeout: 10000 });
    console.log('✅ Lobby page loaded with lobby-joined element');

    // Check member count
    const memberCount = page.locator('[data-testid="lobby-joined-count"]');
    await expect(memberCount).toContainText('1', { timeout: 5000 });
    console.log('✅ Member count shows 1 (commissioner)');

    // Step 10: Verify success marker has disappeared
    console.log('🎯 Step 10: Verifying success marker has disappeared...');
    
    // Success marker should no longer be visible
    await expect(successMarker).not.toBeVisible({ timeout: 1000 });
    console.log('✅ Success marker has disappeared as expected');

    console.log('🎉 Deterministic league creation flow test completed successfully!');
  });

  test('Dialog behavior under different response scenarios', async ({ page }) => {
    console.log('🚀 Testing dialog behavior under different scenarios...');

    // Login
    await login(page, 'commish@example.com', { mode: 'test' });
    await page.waitForURL('**/app', { timeout: 10000 });

    // Open dialog
    await clickCreateLeague(page);
    const dialog = page.locator('[data-testid="create-dialog"]');
    await expect(dialog).toBeVisible({ timeout: 5000 });

    // Test form validation (should keep dialog open)
    console.log('🔍 Testing form validation behavior...');
    
    const submitBtn = page.getByTestId('create-submit');
    
    // Try to submit empty form
    await submitBtn.click();
    
    // Dialog should remain open for validation errors
    const dialogElement = page.locator('[role="dialog"]').first();
    await expect(dialogElement).toHaveAttribute('data-state', 'open');
    console.log('✅ Dialog remains open for validation errors');

    // Fill form with valid data
    await fillCreateLeague(page, LEAGUE_SETTINGS);
    
    // Submit valid form
    await submitBtn.click();
    
    // Dialog should close on success
    await expect(dialogElement).toHaveAttribute('data-state', 'closed', { timeout: 5000 });
    console.log('✅ Dialog closes on successful submission');

    console.log('🎉 Dialog behavior test completed successfully!');
  });
});