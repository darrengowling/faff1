#!/usr/bin/env node

/**
 * TestID CI Audit Script
 * 
 * Calls the backend /test/testids/verify endpoint for critical routes
 * and fails the CI pipeline if any testids are missing or hidden.
 * 
 * Usage: npm run audit:testids
 */

const https = require('https');
const http = require('http');

// Configuration
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const CRITICAL_ROUTES = [
  '/login',
  '/app',
  '/app/leagues/new',
  '/app/leagues/dummy-league-id/lobby'  // Use dummy id for :id route
];

/**
 * Make HTTP request to verification endpoint
 */
function makeRequest(url) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const client = urlObj.protocol === 'https:' ? https : http;
    
    const request = client.get(url, (response) => {
      let data = '';
      
      response.on('data', (chunk) => {
        data += chunk;
      });
      
      response.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({
            statusCode: response.statusCode,
            data: jsonData
          });
        } catch (error) {
          reject(new Error(`Failed to parse JSON response: ${error.message}`));
        }
      });
    });
    
    request.on('error', (error) => {
      reject(error);
    });
    
    request.setTimeout(10000, () => {
      request.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

/**
 * Verify testids for a specific route
 */
async function verifyRoute(route) {
  const url = `${BACKEND_URL}/api/test/testids/verify?route=${encodeURIComponent(route)}`;
  
  try {
    console.log(`🔍 Verifying testids for route: ${route}`);
    
    const response = await makeRequest(url);
    
    if (response.statusCode !== 200) {
      throw new Error(`HTTP ${response.statusCode}: ${response.data.detail || 'Unknown error'}`);
    }
    
    const { present, missing, hidden } = response.data;
    
    // Log results
    console.log(`   ✅ Present: ${present.length} (${present.join(', ')})`);
    
    if (missing.length > 0) {
      console.log(`   ❌ Missing: ${missing.length} (${missing.join(', ')})`);
    }
    
    if (hidden.length > 0) {
      console.log(`   👁️  Hidden: ${hidden.length} (${hidden.join(', ')})`);
    }
    
    return {
      route,
      success: missing.length === 0 && hidden.length === 0,
      present: present.length,
      missing: missing.length,
      hidden: hidden.length,
      missingTestIds: missing,
      hiddenTestIds: hidden,
      data: response.data
    };
    
  } catch (error) {
    console.log(`   💥 Error: ${error.message}`);
    return {
      route,
      success: false,
      error: error.message,
      present: 0,
      missing: 0,
      hidden: 0,
      missingTestIds: [],
      hiddenTestIds: []
    };
  }
}

/**
 * Main audit function
 */
async function auditTestIds() {
  console.log('🚀 Starting TestID CI Audit...');
  console.log(`📍 Backend URL: ${BACKEND_URL}`);
  console.log(`📝 Routes to verify: ${CRITICAL_ROUTES.length}`);
  console.log('');
  
  const results = [];
  let overallSuccess = true;
  
  // Test each route
  for (const route of CRITICAL_ROUTES) {
    const result = await verifyRoute(route);
    results.push(result);
    
    if (!result.success) {
      overallSuccess = false;
    }
    
    console.log(''); // Add spacing between routes
  }
  
  // Generate summary report
  console.log('='.repeat(60));
  console.log('📊 TESTID CI AUDIT SUMMARY');
  console.log('='.repeat(60));
  
  const totalPresent = results.reduce((sum, r) => sum + r.present, 0);
  const totalMissing = results.reduce((sum, r) => sum + r.missing, 0);
  const totalHidden = results.reduce((sum, r) => sum + r.hidden, 0);
  const successfulRoutes = results.filter(r => r.success).length;
  
  console.log(`Routes Tested: ${CRITICAL_ROUTES.length}`);
  console.log(`Routes Passing: ${successfulRoutes}/${CRITICAL_ROUTES.length}`);
  console.log(`TestIDs Present: ${totalPresent}`);
  console.log(`TestIDs Missing: ${totalMissing}`);
  console.log(`TestIDs Hidden: ${totalHidden}`);
  console.log('');
  
  // Detailed results per route
  results.forEach(result => {
    const status = result.success ? '✅' : '❌';
    const errorInfo = result.error ? ` (${result.error})` : '';
    console.log(`${status} ${result.route}: ${result.present} present, ${result.missing} missing, ${result.hidden} hidden${errorInfo}`);
  });
  
  console.log('');
  
  if (overallSuccess) {
    console.log('🎉 All routes passed! TestIDs are ready for E2E testing.');
    console.log('✅ CI Pipeline can proceed to E2E tests.');
    process.exit(0);
  } else {
    console.log('💥 TestID audit failed!');
    console.log('❌ CI Pipeline should STOP before E2E tests.');
    console.log('');
    console.log('🔧 Actions Required:');
    
    // Show specific actions needed
    const failedRoutes = results.filter(r => !r.success);
    failedRoutes.forEach(result => {
      if (result.error) {
        console.log(`   • Fix error for ${result.route}: ${result.error}`);
      } else {
        if (result.missingTestIds.length > 0) {
          console.log(`   • Add missing testids for ${result.route}: ${result.missingTestIds.join(', ')}`);
        }
        if (result.hiddenTestIds.length > 0) {
          console.log(`   • Make visible testids for ${result.route}: ${result.hiddenTestIds.join(', ')}`);
        }
      }
    });
    
    console.log('');
    console.log('💡 Run contract tests first: npm run test:contract');
    console.log('🔍 Debug individual routes at: ' + BACKEND_URL + '/api/test/testids/verify?route=ROUTE_NAME');
    
    process.exit(1);
  }
}

/**
 * Handle CLI execution
 */
if (require.main === module) {
  // Add signal handlers for clean exit
  process.on('SIGINT', () => {
    console.log('\n⚠️  TestID audit interrupted');
    process.exit(1);
  });
  
  process.on('SIGTERM', () => {
    console.log('\n⚠️  TestID audit terminated');
    process.exit(1);
  });
  
  // Run the audit
  auditTestIds().catch((error) => {
    console.error('💥 Unexpected error during TestID audit:', error.message);
    console.error('Stack trace:', error.stack);
    process.exit(1);
  });
}

module.exports = { auditTestIds, verifyRoute };