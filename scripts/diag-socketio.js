#!/usr/bin/env node

/**
 * Socket.IO Diagnostics Script
 * Tests Socket.IO handshake for both polling and websocket transports
 */

const io = require('socket.io-client');

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const TRANSPORTS = (process.env.NEXT_PUBLIC_SOCKET_TRANSPORTS || 'polling,websocket').split(',');

async function testSocketTransport(transport) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const socket = io(BACKEND_URL, {
      transports: [transport],
      timeout: 10000,
      forceNew: true
    });
    
    const timeout = setTimeout(() => {
      socket.close();
      reject(new Error(`${transport} handshake timeout after 10s`));
    }, 10000);
    
    socket.on('connect', () => {
      const duration = Date.now() - startTime;
      clearTimeout(timeout);
      socket.close();
      resolve({ transport, duration, success: true });
    });
    
    socket.on('connect_error', (error) => {
      clearTimeout(timeout);
      socket.close(); 
      reject({ transport, error: error.message, success: false });
    });
  });
}

async function runSocketDiagnostics() {
  console.log('🔌 Socket.IO Diagnostics Starting...');
  console.log(`Backend URL: ${BACKEND_URL}`);
  console.log(`Transports: ${TRANSPORTS.join(', ')}`);
  console.log('');
  
  const results = [];
  
  for (const transport of TRANSPORTS) {
    try {
      console.log(`Testing ${transport} transport...`);
      const result = await testSocketTransport(transport);
      console.log(`✅ ${transport}: Connected in ${result.duration}ms`);
      results.push(result);
    } catch (error) {
      console.error(`❌ ${transport}: ${error.error || error.message}`);
      results.push(error);
    }
  }
  
  console.log('');
  console.log('=== DIAGNOSTICS SUMMARY ===');
  
  let allPassed = true;
  for (const result of results) {
    if (result.success) {
      console.log(`✅ ${result.transport}: ${result.duration}ms`);
    } else {
      console.log(`❌ ${result.transport}: FAILED`);
      allPassed = false;
    }
  }
  
  if (!allPassed) {
    console.log('');
    console.log('🚨 TROUBLESHOOTING:');
    console.log('1. Check if backend server is running on ' + BACKEND_URL);
    console.log('2. Verify Socket.IO is properly configured');
    console.log('3. Check for firewall/proxy issues');
    console.log('4. Ensure CORS is configured for Socket.IO');
    process.exit(1);
  }
  
  console.log('✅ All socket transports working correctly');
  return true;
}

if (require.main === module) {
  runSocketDiagnostics().catch((error) => {
    console.error('Diagnostics failed:', error);
    process.exit(1);
  });
}

module.exports = { runSocketDiagnostics };