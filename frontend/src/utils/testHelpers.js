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

export default {
  isTestMode,
  refreshTestSession,
  quickCreateTestLeague,
  startSessionKeepAlive,
  stopSessionKeepAlive
};