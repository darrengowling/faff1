/**
 * Time Control System Tests
 * Verifies deterministic time control for auction testing
 */

import { test, expect } from '@playwright/test';
import { initializeTestTime, advanceTime, advanceTimeSeconds, getCurrentTestTime, setTestTime } from './utils/time-helpers';

test.describe('Time Control System', () => {
  test('Time control endpoints work correctly', async ({ page }) => {
    console.log('🧪 Testing basic time control functionality...');
    
    // Test setting a specific time
    const fixedTime = new Date('2025-01-01T12:00:00.000Z').getTime();
    await setTestTime(page, fixedTime);
    
    // Verify the time was set
    const currentTime = await getCurrentTestTime(page);
    expect(currentTime.timeMs).toBe(fixedTime);
    expect(currentTime.time).toBe('2025-01-01T12:00:00+00:00');
    
    // Test advancing time
    await advanceTimeSeconds(page, 5);
    
    // Verify time advanced correctly
    const newTime = await getCurrentTestTime(page);
    expect(newTime.timeMs).toBe(fixedTime + 5000);
    expect(newTime.time).toBe('2025-01-01T12:00:05+00:00');
    
    console.log('✅ Basic time control working correctly');
  });

  test('Initialize test time creates consistent baseline', async ({ page }) => {
    console.log('🧪 Testing test time initialization...');
    
    // Initialize with default baseline
    await initializeTestTime(page);
    
    const time1 = await getCurrentTestTime(page);
    console.log(`First baseline: ${time1.time}`);
    
    // Initialize again - should get same baseline
    await initializeTestTime(page);
    
    const time2 = await getCurrentTestTime(page);
    console.log(`Second baseline: ${time2.time}`);
    
    expect(time2.time).toBe(time1.time);
    expect(time2.timeMs).toBe(time1.timeMs);
    
    console.log('✅ Test time initialization is deterministic');
  });

  test('Time advancement is deterministic and precise', async ({ page }) => {
    console.log('🧪 Testing deterministic time advancement...');
    
    // Set a known starting point
    const startTime = new Date('2025-01-01T10:00:00.000Z').getTime();
    await setTestTime(page, startTime);
    
    // Advance in multiple steps
    await advanceTime(page, 1500); // 1.5 seconds
    await advanceTime(page, 2300); // 2.3 seconds
    await advanceTimeSeconds(page, 1.2); // 1.2 seconds
    
    // Total advancement: 1500 + 2300 + 1200 = 5000ms = 5 seconds
    const finalTime = await getCurrentTestTime(page);
    const expectedTime = startTime + 5000;
    
    expect(finalTime.timeMs).toBe(expectedTime);
    expect(finalTime.time).toBe('2025-01-01T10:00:05+00:00');
    
    console.log('✅ Time advancement is precise and deterministic');
  });

  test('Time control provides millisecond precision', async ({ page }) => {
    console.log('🧪 Testing millisecond precision...');
    
    const baseTime = new Date('2025-01-01T15:30:45.123Z').getTime();
    await setTestTime(page, baseTime);
    
    // Advance by exact milliseconds
    await advanceTime(page, 456);
    
    const result = await getCurrentTestTime(page);
    expect(result.timeMs).toBe(baseTime + 456);
    expect(result.time).toBe('2025-01-01T15:30:45.579+00:00');
    
    console.log('✅ Millisecond precision maintained');
  });

  test('Multiple time operations are sequential and consistent', async ({ page }) => {
    console.log('🧪 Testing sequential time operations...');
    
    await initializeTestTime(page);
    const startTime = await getCurrentTestTime(page);
    
    // Perform multiple operations
    const operations = [
      { advance: 1000, expected: startTime.timeMs + 1000 },
      { advance: 500, expected: startTime.timeMs + 1500 },
      { advance: 2300, expected: startTime.timeMs + 3800 },
      { advance: 1200, expected: startTime.timeMs + 5000 }
    ];
    
    for (const op of operations) {
      await advanceTime(page, op.advance);
      const currentTime = await getCurrentTestTime(page);
      expect(currentTime.timeMs).toBe(op.expected);
      console.log(`Step: +${op.advance}ms -> ${currentTime.time} (${currentTime.timeMs})`);
    }
    
    console.log('✅ Sequential operations maintain consistency');
  });
});