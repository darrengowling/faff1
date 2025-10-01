#!/usr/bin/env node

/**
 * Socket Configuration Verification Script
 * 
 * Verifies that Socket.IO configuration is correct for the environment.
 * Asserts that server socketio_path === "socket.io" and client path === "/api/socket.io"
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

// Check server socketio_path configuration
function verifyServerSocketConfig() {
  const serverPath = path.join(__dirname, '..', '..', 'backend', 'server.py');
  
  if (!fs.existsSync(serverPath)) {
    console.log('❌ Server file not found at:', serverPath);
    return false;
  }
  
  const serverContent = fs.readFileSync(serverPath, 'utf8');
  
  // Look for socketio_path configuration
  const socketioPathRegex = /socketio_path\s*=\s*['"](.*?)['"]/;
  const match = serverContent.match(socketioPathRegex);
  
  if (!match) {
    console.log('❌ socketio_path configuration not found in server.py');
    return false;
  }
  
  const serverSocketPath = match[1];
  const expectedServerPath = 'api/socket.io';
  
  if (serverSocketPath === expectedServerPath) {
    console.log(`✅ Server socketio_path: ${serverSocketPath} (correct)`);
    return true;
  } else {
    console.log(`❌ Server socketio_path: ${serverSocketPath}, expected: ${expectedServerPath}`);
    return false;
  }
}

// Check client socket path configuration
function verifyClientSocketConfig() {
  const socketClientPath = path.join(__dirname, '..', 'src', 'lib', 'socket.js');
  
  if (!fs.existsSync(socketClientPath)) {
    console.log('❌ Client socket file not found at:', socketClientPath);
    return false;
  }
  
  const clientContent = fs.readFileSync(socketClientPath, 'utf8');
  
  // Look for path configuration in socket.io client
  const pathRegex = /path:\s*['"](.*?)['"]/;
  const match = clientContent.match(pathRegex);
  
  if (!match) {
    console.log('❌ Client socket path configuration not found in socket.js');
    return false;
  }
  
  const clientPath = match[1];
  const expectedClientPath = '/api/socket.io';
  
  if (clientPath === expectedClientPath) {
    console.log(`✅ Client socket path: ${clientPath} (correct)`);
    return true;
  } else {
    console.log(`❌ Client socket path: ${clientPath}, expected: ${expectedClientPath}`);
    return false;
  }
}

console.log('🔧 Verifying Socket.IO configuration...');
console.log('=====================================');

// Load env vars from file and merge with process.env
const envVars = { ...loadEnvFile(), ...process.env };

let hasErrors = false;

// Verify server and client socket configurations
const serverConfigValid = verifyServerSocketConfig();
const clientConfigValid = verifyClientSocketConfig();

if (!serverConfigValid) {
  hasErrors = true;
}

if (!clientConfigValid) {
  hasErrors = true;
}

// Check required environment variables
const requiredEnvVars = [
  'REACT_APP_BACKEND_URL'
];

const optionalEnvVars = [
  'VITE_SOCKET_TRANSPORTS',
  'NEXT_PUBLIC_SOCKET_TRANSPORTS'
];

let foundVars = 0;

requiredEnvVars.forEach(envVar => {
  const value = envVars[envVar];
  if (!value) {
    console.log(`❌ Missing required environment variable: ${envVar}`);
    hasErrors = true;
  } else {
    console.log(`✅ ${envVar}: ${value}`);
    foundVars++;
  }
});

optionalEnvVars.forEach(envVar => {
  const value = envVars[envVar];
  if (value) {
    console.log(`✅ ${envVar}: ${value}`);
    foundVars++;
  } else {
    console.log(`⚠️  Optional ${envVar}: not set`);
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

console.log('=====================================');

if (hasErrors) {
  console.log('❌ Socket configuration verification failed!');
  console.log('   Required: Server socketio_path === "api/socket.io"');  
  console.log('   Required: Client path === "/api/socket.io"');
  process.exit(1);
} else {
  console.log('✅ Socket configuration verification passed!');
  console.log('   ✓ Server socketio_path matches expected configuration');
  console.log('   ✓ Client path matches expected configuration'); 
  console.log('   ✓ Environment variables are properly set');
  process.exit(0);
}