/**
 * Generated Contract Tests for Critical Route TestIDs
 * 
 * Automatically tests that all required testids are present and visible
 * for each route defined in CRITICAL_ROUTE_TESTIDS.
 * 
 * This suite runs before E2E tests to catch testid issues early.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter as Router, Routes, Route, MemoryRouter } from 'react-router-dom';
import { CRITICAL_ROUTE_TESTIDS } from '../testing/critical-routes.ts';
import App from '../App';

// Mock external dependencies
jest.mock('axios');
jest.mock('sonner');
jest.mock('socket.io-client');

// Mock auth context for authenticated routes
const mockAuthContext = {
  user: { id: 'test-user', email: 'test@example.com', verified: true, display_name: 'Test User' },
  login: jest.fn(),
  logout: jest.fn(),
  loading: false
};

// Mock league context for league-specific routes
const mockLeagueContext = {
  selectedLeague: { id: 'test-league', name: 'Test League' },
  leagues: [{ id: 'test-league', name: 'Test League' }],
  loading: false
};

// Mock useAuth hook
jest.mock('../App', () => {
  const originalModule = jest.requireActual('../App');
  return {
    ...originalModule,
    useAuth: () => mockAuthContext
  };
});

/**
 * Check if element is visible (not display: none, visibility: hidden, etc.)
 */
function isElementVisible(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);
  
  if (style.display === 'none') return false;
  if (style.visibility === 'hidden') return false;
  if (style.opacity === '0') return false;
  
  const rect = element.getBoundingClientRect();
  if (rect.width === 0 && rect.height === 0) return false;
  
  return true;
}

/**
 * Find all elements with a specific testid
 */
function getAllByTestId(testId: string): HTMLElement[] {
  return Array.from(document.querySelectorAll(`[data-testid="${testId}"]`));
}

/**
 * Test a specific route for testid compliance
 */
async function testRouteTestIds(route: string, requiredTestIds: string[]) {
  // Handle route parameters by replacing them with test values
  const testRoute = route
    .replace(':id', 'test-league-id')
    .replace(':leagueId', 'test-league-id')
    .replace(':userId', 'test-user-id');

  // Render the route within the app context
  render(
    <MemoryRouter initialEntries={[testRoute]}>
      <App />
    </MemoryRouter>
  );

  // Wait for the route to load and any async operations to complete
  await waitFor(() => {
    // Check if we're on the expected route by looking for any of the expected testids
    const hasAnyExpectedTestId = requiredTestIds.some(testId => {
      try {
        const elements = getAllByTestId(testId);
        return elements.length > 0;
      } catch {
        return false;
      }
    });
    
    if (requiredTestIds.length > 0 && !hasAnyExpectedTestId) {
      throw new Error(`Route ${route} not fully loaded - none of the expected testids found`);
    }
  }, { timeout: 5000 });

  // Test results collection
  const results = {
    route,
    testRoute,
    passed: [] as string[],
    missing: [] as string[],
    hidden: [] as string[],
    duplicates: [] as string[]
  };

  // Test each required testid
  for (const testId of requiredTestIds) {
    const elements = getAllByTestId(testId);
    
    if (elements.length === 0) {
      results.missing.push(testId);
    } else if (elements.length > 1) {
      results.duplicates.push(testId);
    } else {
      const element = elements[0];
      if (isElementVisible(element)) {
        results.passed.push(testId);
      } else {
        results.hidden.push(testId);
      }
    }
  }

  return results;
}

/**
 * Generate test suite for all routes
 */
describe('Contract Tests: Critical Route TestIDs', () => {
  // Set up test environment
  beforeAll(() => {
    // Mock environment variables
    process.env.REACT_APP_TEST_MODE = 'true';
    process.env.NODE_ENV = 'test';
    
    // Mock console methods to reduce noise
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterAll(() => {
    // Restore console methods
    jest.restoreAllMocks();
  });

  beforeEach(() => {
    // Clear DOM before each test
    document.body.innerHTML = '';
    
    // Reset mocks
    jest.clearAllMocks();
  });

  // Generate a test for each route in CRITICAL_ROUTE_TESTIDS
  Object.entries(CRITICAL_ROUTE_TESTIDS).forEach(([route, requiredTestIds]) => {
    describe(`Route: ${route}`, () => {
      test(`should have all required testids present and visible`, async () => {
        const results = await testRouteTestIds(route, requiredTestIds);
        
        // Create detailed error messages
        const errorMessages: string[] = [];
        
        if (results.missing.length > 0) {
          errorMessages.push(`Missing testids: ${results.missing.join(', ')}`);
        }
        
        if (results.hidden.length > 0) {
          errorMessages.push(`Hidden testids: ${results.hidden.join(', ')}`);
        }
        
        if (results.duplicates.length > 0) {
          errorMessages.push(`Duplicate testids: ${results.duplicates.join(', ')}`);
        }
        
        // Log results for debugging
        console.info(`Route ${route} TestID Results:`, {
          passed: results.passed.length,
          missing: results.missing.length,
          hidden: results.hidden.length,
          duplicates: results.duplicates.length,
          details: results
        });
        
        // Assert that all testids are present and visible
        expect(errorMessages).toEqual([]);
        expect(results.passed).toHaveLength(requiredTestIds.length);
        expect(results.missing).toHaveLength(0);
        expect(results.hidden).toHaveLength(0);
        expect(results.duplicates).toHaveLength(0);
      });

      // Individual tests for each testid for better granularity
      requiredTestIds.forEach(testId => {
        test(`should have testid "${testId}" present and visible`, async () => {
          const results = await testRouteTestIds(route, [testId]);
          
          expect(results.missing).not.toContain(testId);
          expect(results.hidden).not.toContain(testId);
          expect(results.duplicates).not.toContain(testId);
          expect(results.passed).toContain(testId);
        });
      });
    });
  });

  // Summary test that reports overall compliance
  test('Overall TestID Compliance Summary', async () => {
    const overallResults = {
      totalRoutes: Object.keys(CRITICAL_ROUTE_TESTIDS).length,
      totalTestIds: Object.values(CRITICAL_ROUTE_TESTIDS).flat().length,
      routeResults: [] as any[]
    };

    // Test all routes
    for (const [route, requiredTestIds] of Object.entries(CRITICAL_ROUTE_TESTIDS)) {
      try {
        const results = await testRouteTestIds(route, requiredTestIds);
        overallResults.routeResults.push(results);
      } catch (error) {
        overallResults.routeResults.push({
          route,
          error: error instanceof Error ? error.message : 'Unknown error',
          passed: [],
          missing: requiredTestIds,
          hidden: [],
          duplicates: []
        });
      }
    }

    // Calculate compliance statistics
    const stats = overallResults.routeResults.reduce((acc, result) => {
      acc.totalPassed += result.passed.length;
      acc.totalMissing += result.missing.length;
      acc.totalHidden += result.hidden.length;
      acc.totalDuplicates += result.duplicates.length;
      return acc;
    }, {
      totalPassed: 0,
      totalMissing: 0,
      totalHidden: 0,
      totalDuplicates: 0
    });

    const complianceRate = (stats.totalPassed / overallResults.totalTestIds * 100).toFixed(1);

    // Log comprehensive summary
    console.info('=== TestID Contract Compliance Report ===');
    console.info(`Routes Tested: ${overallResults.totalRoutes}`);
    console.info(`Total TestIDs Required: ${overallResults.totalTestIds}`);
    console.info(`Compliance Rate: ${complianceRate}%`);
    console.info(`Passed: ${stats.totalPassed}`);
    console.info(`Missing: ${stats.totalMissing}`);
    console.info(`Hidden: ${stats.totalHidden}`);
    console.info(`Duplicates: ${stats.totalDuplicates}`);
    console.info('==========================================');

    // Assert 100% compliance for contract tests
    expect(stats.totalMissing).toBe(0);
    expect(stats.totalHidden).toBe(0);
    expect(stats.totalDuplicates).toBe(0);
    expect(parseFloat(complianceRate)).toBe(100.0);
  });
});