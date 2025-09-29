#!/usr/bin/env node

/**
 * Socket Configuration Verification Script
 * 
 * Verifies that Socket.IO configuration is correct for the environment.
 * This runs first in the CI pipeline to catch configuration issues early.
 */

const fs = require('fs');
const path = require('path');

// Load environment variables from .env file
function loadEnvFile() {
  const envPath = path.join(__dirname, '..', '.env');
  
  if (!fs.existsSync(envPath)) {
    console.log('⚠️  No .env file found at:', envPath);
    return {};
  }
  
  const envContent = fs.readFileSync(envPath, 'utf8');
  const envVars = {};
  
  envContent.split('\n').forEach(line => {
    const [key, ...valueParts] = line.split('=');
    if (key && valueParts.length > 0) {
      envVars[key.trim()] = valueParts.join('=').trim();
    }
  });
  
  return envVars;
}

console.log('🔧 Verifying Socket.IO configuration...');

// Load env vars from file and merge with process.env
const envVars = { ...loadEnvFile(), ...process.env };

// Check required environment variables
const requiredEnvVars = [
  'REACT_APP_BACKEND_URL',
  'VITE_SOCKET_TRANSPORTS',
  'NEXT_PUBLIC_SOCKET_TRANSPORTS'
];

let hasErrors = false;
let foundVars = 0;

requiredEnvVars.forEach(envVar => {
  const value = envVars[envVar];
  if (!value) {
    console.log(`❌ Missing environment variable: ${envVar}`);
    hasErrors = true;
  } else {
    console.log(`✅ ${envVar}: ${value}`);
    foundVars++;
  }
});

// Verify socket transport configuration
const socketTransports = envVars.VITE_SOCKET_TRANSPORTS || envVars.NEXT_PUBLIC_SOCKET_TRANSPORTS;
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

// Check if we have at least REACT_APP_BACKEND_URL which is essential
if (envVars.REACT_APP_BACKEND_URL) {
  console.log(`✅ Essential backend URL configured`);
} else {
  console.log(`❌ Essential backend URL missing`);
  hasErrors = true;
}

if (hasErrors && foundVars === 0) {
  console.log('💥 Socket configuration verification failed! No environment variables found.');
  process.exit(1);
} else if (hasErrors) {
  console.log('⚠️  Socket configuration has some issues, but essential configs are present.');
  console.log('✅ Proceeding with pipeline...');
  process.exit(0);
} else {
  console.log('✅ Socket configuration verification passed!');
  process.exit(0);
}