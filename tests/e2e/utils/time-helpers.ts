/**
 * Time Control Helpers for Deterministic Testing
 * Provides utilities to control time in TEST_MODE for consistent test results
 */

import { Page } from '@playwright/test';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://test-harmony.preview.emergentagent.com';

/**
 * Set the test time to a specific timestamp
 * @param page - Playwright page instance
 * @param timeMs - Timestamp in milliseconds since epoch
 */
export async function setTestTime(page: Page, timeMs: number): Promise<void> {
  const response = await page.request.post(`${BACKEND_URL}/api/test/time/set`, {
    data: { nowMs: timeMs }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to set test time: ${response.status()} ${await response.text()}`);
  }
  
  const result = await response.json();
  console.log(`🕐 Test time set to: ${result.currentTime} (${result.currentTimeMs}ms)`);
}

/**
 * Advance the test time by specified milliseconds
 * @param page - Playwright page instance  
 * @param deltaMs - Milliseconds to advance
 */
export async function advanceTime(page: Page, deltaMs: number): Promise<void> {
  const response = await page.request.post(`${BACKEND_URL}/api/test/time/advance`, {
    data: { ms: deltaMs }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to advance test time: ${response.status()} ${await response.text()}`);
  }
  
  const result = await response.json();
  console.log(`🕐 Test time advanced by ${result.advancedMs}ms to: ${result.currentTime} (${result.currentTimeMs}ms)`);
}

/**
 * Advance the test time by specified seconds (convenience method)
 * @param page - Playwright page instance
 * @param deltaSeconds - Seconds to advance
 */
export async function advanceTimeSeconds(page: Page, deltaSeconds: number): Promise<void> {
  await advanceTime(page, deltaSeconds * 1000);
}

/**
 * Set test time to a specific date
 * @param page - Playwright page instance
 * @param date - Date object to set as current time
 */
export async function setTestDate(page: Page, date: Date): Promise<void> {
  await setTestTime(page, date.getTime());
}

/**
 * Get current test time from the backend
 * @param page - Playwright page instance
 * @returns Current time information
 */
export async function getCurrentTestTime(page: Page): Promise<{ timeMs: number; time: string }> {
  // We can get current time by advancing by 0
  const response = await page.request.post(`${BACKEND_URL}/api/test/time/advance`, {
    data: { ms: 0 }
  });
  
  if (!response.ok()) {
    throw new Error(`Failed to get current test time: ${response.status()} ${await response.text()}`);
  }
  
  const result = await response.json();
  return {
    timeMs: result.currentTimeMs,
    time: result.currentTime
  };
}

/**
 * Initialize test time to a fixed baseline for consistent testing
 * @param page - Playwright page instance
 * @param baseDate - Optional base date (defaults to 2025-01-01T12:00:00Z)
 */
export async function initializeTestTime(page: Page, baseDate?: Date): Promise<void> {
  const baseline = baseDate || new Date('2025-01-01T12:00:00.000Z');
  await setTestDate(page, baseline);
  console.log(`🕐 Test time initialized to baseline: ${baseline.toISOString()}`);
}

/**
 * Simulate auction timer progression for deterministic testing
 * @param page - Playwright page instance
 * @param timerSeconds - Total timer duration in seconds
 * @param steps - Number of steps to advance in (default: 4)
 */
export async function simulateAuctionTimer(page: Page, timerSeconds: number, steps: number = 4): Promise<void> {
  const stepSize = Math.floor((timerSeconds * 1000) / steps);
  
  console.log(`🕐 Simulating ${timerSeconds}s auction timer in ${steps} steps of ${stepSize}ms each`);
  
  for (let i = 0; i < steps; i++) {
    await advanceTime(page, stepSize);
    await page.waitForTimeout(100); // Small wait for UI updates
  }
}

/**
 * Advance time to trigger anti-snipe logic
 * @param page - Playwright page instance
 * @param antiSnipeThreshold - Anti-snipe threshold in seconds (default: 3)
 */
export async function triggerAntiSnipe(page: Page, antiSnipeThreshold: number = 3): Promise<void> {
  // Advance to just before the threshold to trigger anti-snipe
  const triggerTime = (antiSnipeThreshold - 0.5) * 1000; // 0.5s before threshold
  await advanceTime(page, triggerTime);
  console.log(`🕐 Advanced time to trigger anti-snipe (${antiSnipeThreshold}s threshold)`);
}