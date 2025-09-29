/**
 * Test Helper Utilities
 * 
 * Provides TEST_MODE utilities for improving E2E test reliability
 * Only active when TEST_MODE environment variables are enabled
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Check if we're in test mode
export const isTestMode = () => {
  if (process.env.NODE_ENV === 'test') return true;
  if (process.env.REACT_APP_PLAYWRIGHT_TEST === 'true') return true;
  if (typeof window !== 'undefined' && window.location.search.includes('playwright=true')) return true;
  return false;
};

/**
 * Refresh the current test session to prevent expiry during long test runs
 */
export const refreshTestSession = async () => {
  if (!isTestMode()) {
    console.warn('refreshTestSession: Not in test mode');
    return { success: false, reason: 'not_test_mode' };
  }

  try {
    const response = await fetch(`${API}/test/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Session refresh failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('🧪 TEST SESSION REFRESHED:', data.message);
    
    return { 
      success: true, 
      data,
      expiresIn: data.expiresIn 
    };
  } catch (error) {
    console.error('Failed to refresh test session:', error);
    return { 
      success: false, 
      error: error.message 
    };
  }
};

/**
 * Quickly create a test league and return lobby URL for immediate access
 */
export const quickCreateTestLeague = async () => {
  if (!isTestMode()) {
    console.warn('quickCreateTestLeague: Not in test mode');
    return { success: false, reason: 'not_test_mode' };
  }

  try {
    const response = await fetch(`${API}/test/league/quick-create`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Quick league creation failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('🧪 QUICK TEST LEAGUE CREATED:', data.leagueId);
    
    return { 
      success: true, 
      leagueId: data.leagueId,
      lobbyUrl: data.lobbyUrl,
      name: data.name
    };
  } catch (error) {
    console.error('Failed to create quick test league:', error);
    return { 
      success: false, 
      error: error.message 
    };
  }
};

/**
 * Auto-refresh session every 30 minutes during test runs
 */
export const startSessionKeepAlive = () => {
  if (!isTestMode()) {
    return null;
  }

  console.log('🧪 Starting test session keep-alive (30min intervals)');
  
  const intervalId = setInterval(async () => {
    const result = await refreshTestSession();
    if (result.success) {
      console.log('🧪 Session keep-alive successful');
    } else {
      console.warn('🧪 Session keep-alive failed:', result.error || result.reason);
    }
  }, 30 * 60 * 1000); // 30 minutes

  return intervalId;
};

/**
 * Stop the session keep-alive interval
 */
export const stopSessionKeepAlive = (intervalId) => {
  if (intervalId) {
    clearInterval(intervalId);
    console.log('🧪 Test session keep-alive stopped');
  }
};

/**
 * Test helper: awaitCreatedAndInLobby(page,id) 
 * Waits for /lobby URL, polls /test/league/:id/ready (≤2s), then waits for lobby-ready
 */
export const awaitCreatedAndInLobby = async (page, leagueId) => {
  if (!isTestMode()) {
    console.warn('awaitCreatedAndInLobby: Not in test mode');
    return { success: false, reason: 'not_test_mode' };
  }

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const timeout = 2000; // 2 seconds max
  const pollInterval = 100; // Poll every 100ms

  try {
    console.log(`🧪 AWAIT CREATED AND IN LOBBY: Starting for league ${leagueId}`);
    
    // Step 1: Wait for /lobby URL
    console.log('🧪 Step 1: Waiting for /lobby URL...');
    const expectedUrl = `/app/leagues/${leagueId}/lobby`;
    await page.waitForURL(`**${expectedUrl}`, { timeout });
    console.log(`🧪 Step 1 Complete: On ${expectedUrl}`);
    
    // Step 2: Poll /test/league/:id/ready (≤2s)
    console.log('🧪 Step 2: Polling backend readiness...');
    const startTime = Date.now();
    let ready = false;
    
    while (Date.now() - startTime < timeout && !ready) {
      try {
        const response = await fetch(`${BACKEND_URL}/api/test/league/${leagueId}/ready`, {
          credentials: 'include'
        });
        const data = await response.json();
        
        if (data.ready) {
          ready = true;
          console.log('🧪 Step 2 Complete: Backend reports ready');
          break;
        }
        
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      } catch (error) {
        console.warn('🧪 Step 2 Poll Error:', error.message);
        // Continue polling despite errors
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }
    }
    
    if (!ready) {
      console.warn('🧪 Step 2 Timeout: Backend never reported ready within 2s');
      return { success: false, reason: 'backend_not_ready', timeoutMs: timeout };
    }
    
    // Step 3: Wait for lobby-ready testid
    console.log('🧪 Step 3: Waiting for lobby-ready testid...');
    await page.waitForSelector('[data-testid="lobby-ready"]', { timeout });
    console.log('🧪 Step 3 Complete: lobby-ready testid found');
    
    console.log(`🧪 AWAIT CREATED AND IN LOBBY: SUCCESS for league ${leagueId}`);
    return { 
      success: true, 
      leagueId,
      lobbyUrl: expectedUrl,
      totalTime: Date.now() - startTime
    };
    
  } catch (error) {
    console.error('🧪 AWAIT CREATED AND IN LOBBY: FAILED for league', leagueId, ':', error);
    return { 
      success: false, 
      error: error.message,
      leagueId
    };
  }
};

export default {
  isTestMode,
  refreshTestSession,
  quickCreateTestLeague,
  startSessionKeepAlive,
  stopSessionKeepAlive,
  awaitCreatedAndInLobby
};