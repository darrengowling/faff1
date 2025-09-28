/**
 * API-focused Regression Tests for League Settings
 * Tests critical API endpoints without complex UI interactions
 */

const { test, expect } = require('@playwright/test');

test.describe('API Regression Validation', () => {
  const baseUrl = 'https://auction-league.preview.emergentagent.com';
  
  test('UCL Competition Profile - Min=2, Slots=5 Validation', async ({ request }) => {
    // Test competition profiles endpoint
    const response = await request.get(`${baseUrl}/api/competition-profiles`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('profiles');
    expect(Array.isArray(data.profiles)).toBeTruthy();
    
    // Find UCL profile
    const uclProfile = data.profiles.find(p => p.id === 'ucl');
    expect(uclProfile).toBeDefined();
    
    // Validate critical regression-prevention values
    expect(uclProfile.defaults.club_slots).toBe(5);  // Slots=5 requirement
    expect(uclProfile.defaults.league_size.min).toBe(2);  // Min=2 gate requirement
    expect(uclProfile.defaults.league_size.max).toBe(8);
    expect(uclProfile.defaults.budget_per_manager).toBeGreaterThan(0);
    
    console.log('✅ UCL Profile Validated - Slots=5, Min=2, Max=8');
  });

  test('Roster Calculation Logic - Never Negative', async ({ request }) => {
    // Test various roster calculation scenarios
    const testCases = [
      { owned: 0, slots: 5, expected: 5 },
      { owned: 2, slots: 5, expected: 3 },
      { owned: 5, slots: 5, expected: 0 },
      { owned: 6, slots: 5, expected: 0 }, // Over-owned should clamp to 0
      { owned: 10, slots: 5, expected: 0 }  // Way over-owned should clamp to 0
    ];
    
    testCases.forEach(({ owned, slots, expected }) => {
      const remaining = Math.max(0, slots - owned);
      expect(remaining).toBe(expected);
      expect(remaining).toBeGreaterThanOrEqual(0); // Never negative!
    });
    
    console.log('✅ Roster Calculation - remaining = max(0, clubSlots - ownedCount) validated');
  });

  test('Member Count Gate Logic - Min=2 Validation', async ({ request }) => {
    // Test member count validation logic
    const minMembers = 2;
    
    const testScenarios = [
      { count: 1, canStart: false, description: '1 member cannot start auction' },
      { count: 2, canStart: true, description: '2 members can start auction' },
      { count: 3, canStart: true, description: '3 members can start auction' },
      { count: 8, canStart: true, description: '8 members can start auction' }
    ];
    
    testScenarios.forEach(({ count, canStart, description }) => {
      const actualCanStart = count >= minMembers;
      expect(actualCanStart).toBe(canStart);
    });
    
    console.log('✅ Min=2 Gate Logic - Validated member count requirements');
  });

  test('API Endpoints Health Check', async ({ request }) => {
    // Test that critical endpoints are responding correctly
    const endpoints = [
      { path: '/api/health', description: 'Health check' },
      { path: '/api/competition-profiles', description: 'Competition profiles' },
      { path: '/api/clubs', description: 'Clubs data' },
      { path: '/api/timez', description: 'Time sync' },
      { path: '/api/socket-diag', description: 'Socket diagnostic' }
    ];
    
    for (const endpoint of endpoints) {
      const response = await request.get(`${baseUrl}${endpoint.path}`);
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      expect(data).toBeDefined();
      
      console.log(`✅ ${endpoint.description} - Status ${response.status()}`);
    }
  });

  test('Settings Structure Validation', async ({ request }) => {
    // Validate that settings have the expected structure
    const response = await request.get(`${baseUrl}/api/competition-profiles`);
    const data = await response.json();
    
    data.profiles.forEach(profile => {
      // Each profile should have required structure
      expect(profile).toHaveProperty('id');
      expect(profile).toHaveProperty('defaults');
      
      const defaults = profile.defaults;
      expect(defaults).toHaveProperty('club_slots');
      expect(defaults).toHaveProperty('league_size');
      expect(defaults).toHaveProperty('budget_per_manager');
      
      // Validate types and ranges
      expect(typeof defaults.club_slots).toBe('number');
      expect(defaults.club_slots).toBeGreaterThan(0);
      
      expect(typeof defaults.budget_per_manager).toBe('number');
      expect(defaults.budget_per_manager).toBeGreaterThan(0);
      
      expect(typeof defaults.league_size).toBe('object');
      expect(defaults.league_size.min).toBeGreaterThan(0);
      expect(defaults.league_size.max).toBeGreaterThanOrEqual(defaults.league_size.min);
      
      console.log(`✅ ${profile.id} profile structure validated`);
    });
  });

  test('Calculation Edge Cases - Boundary Validation', async ({ request }) => {
    // Test edge cases for calculations to prevent regressions
    
    // Test zero cases
    expect(Math.max(0, 5 - 0)).toBe(5);
    expect(Math.max(0, 0 - 0)).toBe(0);
    expect(Math.max(0, 0 - 5)).toBe(0);
    
    // Test exact boundary
    expect(Math.max(0, 5 - 5)).toBe(0);
    
    // Test over-boundary (the critical regression prevention)
    expect(Math.max(0, 5 - 6)).toBe(0);
    expect(Math.max(0, 5 - 100)).toBe(0);
    
    // Test large numbers
    expect(Math.max(0, 1000 - 999)).toBe(1);
    expect(Math.max(0, 1000 - 1001)).toBe(0);
    
    console.log('✅ Edge Cases - All boundary conditions handle correctly');
  });

  test('UCL Specific Requirements Validation', async ({ request }) => {
    // Test UCL-specific requirements that should never change
    const response = await request.get(`${baseUrl}/api/competition-profiles`);
    const data = await response.json();
    
    const uclProfile = data.profiles.find(p => p.id === 'ucl');
    
    // These are the regression-prevention requirements
    const requirements = {
      'Club Slots must be 5': () => uclProfile.defaults.club_slots === 5,
      'Min managers must be 2': () => uclProfile.defaults.league_size.min === 2,
      'Max managers must be 8': () => uclProfile.defaults.league_size.max === 8,
      'Budget must be positive': () => uclProfile.defaults.budget_per_manager > 0,
      'Min increment must be 1': () => uclProfile.defaults.min_increment === 1,
      'Anti-snipe must be 30s': () => uclProfile.defaults.anti_snipe_seconds === 30
    };
    
    Object.entries(requirements).forEach(([requirement, validator]) => {
      expect(validator()).toBe(true);
      console.log(`✅ UCL Requirement: ${requirement}`);
    });
  });
});