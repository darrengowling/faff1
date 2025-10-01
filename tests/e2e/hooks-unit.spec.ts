/**
 * Hooks Unit Tests
 * Test individual hook endpoints for debugging
 */

import { test, expect } from '@playwright/test';
import { initializeTestTime } from './utils/time-helpers';

const BACKEND_URL = 'https://leaguemate-1.preview.emergentagent.com';

test.describe('Hooks Unit Tests', () => {
  
  test('Test auction creation hook', async ({ page }) => {
    console.log('🧪 Testing auction creation hook...');
    
    const response = await page.request.post(`${BACKEND_URL}/api/test/auction/create`, {
      data: {
        leagueSettings: {
          name: 'Unit Test League',
          clubSlots: 2,
          budgetPerManager: 100,
          minManagers: 2,
          maxManagers: 3
        }
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    
    expect(result.leagueId).toBeDefined();
    expect(result.message).toContain('Test league created successfully');
    
    console.log(`✅ League created: ${result.leagueId}`);
  });

  test('Test member addition hook', async ({ page }) => {
    console.log('🧪 Testing member addition hook...');
    
    // First create a league
    const createResponse = await page.request.post(`${BACKEND_URL}/api/test/auction/create`, {
      data: {
        leagueSettings: {
          name: 'Member Test League',
          clubSlots: 2,
          budgetPerManager: 100,
          minManagers: 2,
          maxManagers: 3
        }
      }
    });
    
    const league = await createResponse.json();
    console.log(`League for member test: ${league.leagueId}`);
    
    // Add a member
    const memberResponse = await page.request.post(`${BACKEND_URL}/api/test/auction/add-member`, {
      data: {
        leagueId: league.leagueId,
        email: 'test@member.local'
      }
    });
    
    expect(memberResponse.ok()).toBeTruthy();
    const memberResult = await memberResponse.json();
    
    expect(memberResult.userId).toBeDefined();
    expect(memberResult.message).toContain('added to league');
    
    console.log(`✅ Member added: ${memberResult.userId}`);
  });

  test('Test auction start hook', async ({ page }) => {
    console.log('🧪 Testing auction start hook...');
    
    // Create league
    const createResponse = await page.request.post(`${BACKEND_URL}/api/test/auction/create`, {
      data: {
        leagueSettings: {
          name: 'Start Test League',
          clubSlots: 2,
          budgetPerManager: 100,
          minManagers: 2,
          maxManagers: 3
        }
      }
    });
    
    const league = await createResponse.json();
    console.log(`League for start test: ${league.leagueId}`);
    
    // Add required members
    const members = ['alice@example.com', 'bob@example.com'];
    for (const email of members) {
      const memberResponse = await page.request.post(`${BACKEND_URL}/api/test/auction/add-member`, {
        data: {
          leagueId: league.leagueId,
          email: email
        }
      });
      
      if (memberResponse.ok()) {
        const memberResult = await memberResponse.json();
        console.log(`Member added: ${email} -> ${memberResult.userId}`);
      } else {
        console.log(`Failed to add member: ${email}`);
      }
    }
    
    // Try to start auction
    const startResponse = await page.request.post(`${BACKEND_URL}/api/test/auction/start`, {
      data: {
        leagueId: league.leagueId
      }
    });
    
    if (startResponse.ok()) {
      const startResult = await startResponse.json();
      expect(startResult.message).toContain('started');
      console.log(`✅ Auction started: ${startResult.auctionId || startResult.leagueId}`);
    } else {
      const errorText = await startResponse.text();
      console.log(`❌ Auction start failed: ${startResponse.status()} - ${errorText}`);
      
      // For debugging, let's check league state
      // This would be useful to understand what's missing
    }
  });

  test('Test socket drop hook', async ({ page }) => {
    console.log('🧪 Testing socket drop hook...');
    
    // Create a test user first  
    const memberResponse = await page.request.post(`${BACKEND_URL}/api/test/auction/create`, {
      data: {
        leagueSettings: {
          name: 'Socket Test League',
          clubSlots: 2,
          budgetPerManager: 100,
          minManagers: 2,
          maxManagers: 3
        }
      }
    });
    
    const league = await memberResponse.json();
    
    // Add a member so we have a user to test with
    await page.request.post(`${BACKEND_URL}/api/test/auction/add-member`, {
      data: {
        leagueId: league.leagueId,
        email: 'socket@test.local'
      }
    });
    
    // Test socket drop
    const dropResponse = await page.request.post(`${BACKEND_URL}/api/test/sockets/drop`, {
      data: {
        email: 'socket@test.local'
      }
    });
    
    expect(dropResponse.ok()).toBeTruthy();
    const dropResult = await dropResponse.json();
    
    expect(dropResult.message).toContain('socket dropped');
    expect(dropResult.email).toBe('socket@test.local');
    
    console.log(`✅ Socket dropped for: ${dropResult.email}`);
  });

  test('Test time control integration', async ({ page }) => {
    console.log('🧪 Testing time control with hooks...');
    
    // Initialize time
    await initializeTestTime(page);
    
    // Create league with time control
    const createResponse = await page.request.post(`${BACKEND_URL}/api/test/auction/create`, {
      data: {
        leagueSettings: {
          name: 'Time Control Test League',
          clubSlots: 2,
          budgetPerManager: 100,
          minManagers: 2,
          maxManagers: 3
        }
      }
    });
    
    expect(createResponse.ok()).toBeTruthy();
    const league = await createResponse.json();
    
    console.log(`✅ League created with time control: ${league.leagueId}`);
    
    // Verify time control is working
    const timeResponse = await page.request.post(`${BACKEND_URL}/api/test/time/advance`, {
      data: { ms: 1000 }
    });
    
    expect(timeResponse.ok()).toBeTruthy();
    const timeResult = await timeResponse.json();
    
    expect(timeResult.advancedMs).toBe(1000);
    console.log(`✅ Time control working: ${timeResult.currentTime}`);
  });
});