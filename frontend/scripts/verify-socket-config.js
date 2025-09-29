#!/usr/bin/env node

/**
 * Socket Configuration Verification Script
 * 
 * Verifies that Socket.IO configuration is correct for the environment.
 * This runs first in the CI pipeline to catch configuration issues early.
 */

console.log('🔧 Verifying Socket.IO configuration...');

// Check environment variables
const requiredEnvVars = [
  'REACT_APP_BACKEND_URL',
  'VITE_SOCKET_TRANSPORTS',
  'NEXT_PUBLIC_SOCKET_TRANSPORTS'
];

let hasErrors = false;

requiredEnvVars.forEach(envVar => {
  const value = process.env[envVar];
  if (!value) {
    console.log(`❌ Missing environment variable: ${envVar}`);
    hasErrors = true;
  } else {
    console.log(`✅ ${envVar}: ${value}`);
  }
});

// Verify socket transport configuration
const socketTransports = process.env.VITE_SOCKET_TRANSPORTS || process.env.NEXT_PUBLIC_SOCKET_TRANSPORTS;
if (socketTransports) {
  const transports = socketTransports.split(',').map(t => t.trim());
  const validTransports = ['polling', 'websocket'];
  
  const invalidTransports = transports.filter(t => !validTransports.includes(t));
  if (invalidTransports.length > 0) {
    console.log(`❌ Invalid socket transports: ${invalidTransports.join(', ')}`);
    hasErrors = true;
  } else {
    console.log(`✅ Socket transports valid: ${transports.join(', ')}`);
  }
}

if (hasErrors) {
  console.log('💥 Socket configuration verification failed!');
  process.exit(1);
} else {
  console.log('✅ Socket configuration verification passed!');
  process.exit(0);
}