#!/usr/bin/env node
/**
 * Socket.IO Handshake Diagnostics Script
 * Tests Socket.IO polling and websocket handshakes with timeout
 */

import { io } from 'socket.io-client';
import fetch from 'node-fetch';

// Read environment variables
const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL || 
                   process.env.VITE_PUBLIC_API_URL || 
                   process.env.REACT_APP_API_ORIGIN || 
                   'https://auction-platform-6.preview.emergentagent.com';

const SOCKET_PATH = process.env.NEXT_PUBLIC_SOCKET_PATH || 
                   process.env.VITE_SOCKET_PATH || 
                   '/api/socketio';

console.log('🔍 Socket.IO Handshake Diagnostics');
console.log('===================================');
console.log(`API Origin: ${API_ORIGIN}`);
console.log(`Socket Path: ${SOCKET_PATH}`);
console.log(`Full URL: ${API_ORIGIN}${SOCKET_PATH}`);
console.log('');

let testsRun = 0;
let testsPassed = 0;
let testsFailed = 0;

function logTest(name, passed, details = '') {
    testsRun++;
    if (passed) {
        testsPassed++;
        console.log(`✅ ${name} - PASS ${details}`);
    } else {
        testsFailed++;
        console.log(`❌ ${name} - FAIL ${details}`);
    }
}

// Test 1: Polling handshake via direct fetch
async function testPollingHandshake() {
    try {
        const timestamp = Date.now().toString(36);
        const url = `${API_ORIGIN}${SOCKET_PATH}/?EIO=4&transport=polling&t=${timestamp}`;
        
        const response = await fetch(url, {
            method: 'GET',
            timeout: 5000
        });
        
        const responseText = await response.text();
        
        // Check for Engine.IO handshake response (starts with '0' + JSON with sid)
        const isValidHandshake = response.status === 200 && 
                                responseText.startsWith('0{') && 
                                responseText.includes('"sid":');
        
        logTest('Polling Handshake', isValidHandshake, `(${response.status}) ${isValidHandshake ? 'Valid Engine.IO response' : responseText.substring(0, 50)}`);
        
        return isValidHandshake;
    } catch (error) {
        logTest('Polling Handshake', false, `Error: ${error.message}`);
        return false;
    }
}

// Test 2: WebSocket connection via socket.io-client
async function testWebSocketConnection() {
    return new Promise((resolve) => {
        let resolved = false;
        
        const socket = io(API_ORIGIN, {
            path: SOCKET_PATH,
            transports: ['websocket'],
            timeout: 2000,
            forceNew: true
        });

        const timeout = setTimeout(() => {
            if (!resolved) {
                resolved = true;
                logTest('WebSocket Connection', false, '2s timeout reached');
                socket.disconnect();
                resolve(false);
            }
        }, 2000);

        socket.on('connect', () => {
            if (!resolved) {
                resolved = true;
                clearTimeout(timeout);
                logTest('WebSocket Connection', true, `Connected with SID: ${socket.id}`);
                socket.disconnect();
                resolve(true);
            }
        });

        socket.on('connect_error', (error) => {
            if (!resolved) {
                resolved = true;
                clearTimeout(timeout);
                logTest('WebSocket Connection', false, `Connection error: ${error.message}`);
                resolve(false);
            }
        });
    });
}

// Main execution
async function runDiagnostics() {
    console.log('🧪 Running Socket.IO handshake diagnostics...\n');
    
    const pollingResult = await testPollingHandshake();
    const websocketResult = await testWebSocketConnection();
    
    console.log('');
    console.log('===================================');
    console.log(`📊 Results: ${testsPassed}/${testsRun} tests passed`);
    
    if (testsPassed === testsRun) {
        console.log('🎉 All handshake tests passed!');
        process.exit(0);
    } else if (testsPassed === 0) {
        console.log('❌ All handshake tests failed!');
        process.exit(1);
    } else {
        console.log('⚠️  Some handshake tests failed');
        process.exit(0);
    }
}

// Handle process signals
process.on('SIGINT', () => {
    console.log('\n\n⚠️  Tests interrupted by user');
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled rejection:', reason);
    process.exit(1);
});

// Run diagnostics
runDiagnostics().catch((error) => {
    console.error('Failed to run diagnostics:', error);
    process.exit(1);
});