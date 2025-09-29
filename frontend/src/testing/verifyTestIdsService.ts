/**
 * TestID Verification Service
 * 
 * Provides client-side and server-side testid verification capabilities.
 * Integrates with both local DOM verification and backend verification endpoint.
 */

import { verifyTestIds, TestIdVerificationResult } from './verifyTestIds';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export interface RemoteVerificationResult extends TestIdVerificationResult {
  source: 'local' | 'remote';
  error?: string;
}

/**
 * Call the backend testid verification endpoint
 */
export async function verifyTestIdsRemote(route: string): Promise<RemoteVerificationResult> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/test/testids/verify?route=${encodeURIComponent(route)}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    return {
      ...result,
      source: 'remote'
    };
  } catch (error) {
    console.error('Remote testid verification failed:', error);
    return {
      present: [],
      missing: [],
      hidden: [],
      route,
      timestamp: new Date().toISOString(),
      source: 'remote',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Comprehensive testid verification using both local and remote methods
 */
export async function verifyTestIdsComprehensive(route?: string): Promise<{
  local: TestIdVerificationResult;
  remote: RemoteVerificationResult;
  combined: TestIdVerificationResult & { source: 'combined' };
}> {
  const currentRoute = route || window.location.pathname;
  
  // Run local verification
  const localResult = verifyTestIds(currentRoute);
  
  // Run remote verification (if in TEST_MODE)
  const remoteResult = await verifyTestIdsRemote(currentRoute);
  
  // Combine results (prefer local results as they are more accurate)
  const combinedResult: TestIdVerificationResult & { source: 'combined' } = {
    present: localResult.present,
    missing: localResult.missing,
    hidden: localResult.hidden,
    route: currentRoute,
    timestamp: new Date().toISOString(),
    source: 'combined'
  };
  
  return {
    local: localResult,
    remote: remoteResult,
    combined: combinedResult
  };
}

/**
 * Log comprehensive verification results
 */
export function logComprehensiveResults(results: {
  local: TestIdVerificationResult;
  remote: RemoteVerificationResult;
  combined: TestIdVerificationResult & { source: 'combined' };
}): void {
  if (process.env.NODE_ENV !== 'development') return;
  
  const { local, remote, combined } = results;
  
  console.group(`🔍 Comprehensive TestID Verification for ${combined.route}`);
  
  // Local results
  console.group(`📱 Local DOM Verification`);
  console.log(`✅ Present (${local.present.length}):`, local.present);
  if (local.missing.length > 0) {
    console.log(`❌ Missing (${local.missing.length}):`, local.missing);
  }
  if (local.hidden.length > 0) {
    console.log(`👁️ Hidden (${local.hidden.length}):`, local.hidden);
  }
  console.log(`📊 Coverage: ${local.present.length}/${local.present.length + local.missing.length + local.hidden.length} visible`);
  console.groupEnd();
  
  // Remote results
  console.group(`🖥️ Remote Verification`);
  if (remote.error) {
    console.log(`❌ Error:`, remote.error);
  } else {
    console.log(`📝 Note:`, remote.note || 'Remote verification completed');
    console.log(`✅ Present (${remote.present.length}):`, remote.present);
    if (remote.missing.length > 0) {
      console.log(`❌ Missing (${remote.missing.length}):`, remote.missing);
    }
    if (remote.hidden.length > 0) {
      console.log(`👁️ Hidden (${remote.hidden.length}):`, remote.hidden);
    }
  }
  console.groupEnd();
  
  // Summary
  console.group(`📋 Combined Summary`);
  const totalExpected = combined.present.length + combined.missing.length + combined.hidden.length;
  const successRate = totalExpected > 0 ? (combined.present.length / totalExpected * 100).toFixed(1) : '0';
  console.log(`🎯 Success Rate: ${successRate}% (${combined.present.length}/${totalExpected})`);
  
  if (combined.missing.length > 0) {
    console.warn(`🚨 Critical Missing:`, combined.missing);
  }
  if (combined.hidden.length > 0) {
    console.warn(`⚠️ Hidden Elements:`, combined.hidden);
  }
  console.groupEnd();
  
  console.groupEnd();
}

/**
 * Run comprehensive verification and log results
 */
export async function verifyAndLogComprehensive(route?: string): Promise<{
  local: TestIdVerificationResult;
  remote: RemoteVerificationResult;
  combined: TestIdVerificationResult & { source: 'combined' };
}> {
  const results = await verifyTestIdsComprehensive(route);
  logComprehensiveResults(results);
  return results;
}

// Export for window access in development
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  (window as any).verifyTestIdsComprehensive = verifyAndLogComprehensive;
  (window as any).testIdService = {
    local: verifyTestIds,
    remote: verifyTestIdsRemote,
    comprehensive: verifyTestIdsComprehensive,
    verify: verifyAndLogComprehensive
  };
}