#!/usr/bin/env node
/**
 * Socket.IO Diagnostics Test Script
 * Tests both polling and websocket connections against the configured origin/path
 */

const { io } = require('socket.io-client');
const https = require('https');
const http = require('http');

// Configuration from environment using cross-origin pattern
const origin = process.env.NEXT_PUBLIC_API_URL || 
               process.env.VITE_PUBLIC_API_URL || 
               process.env.REACT_APP_API_ORIGIN || 
               'https://pifa-friends-1.preview.emergentagent.com';

const path = process.env.NEXT_PUBLIC_SOCKET_PATH || 
             '/api/socketio';

const transports = (process.env.NEXT_PUBLIC_SOCKET_TRANSPORTS || 
                   process.env.VITE_SOCKET_TRANSPORTS || 
                   'polling,websocket').split(',');

console.log('🔍 Socket.IO Diagnostics Test');
console.log('================================');
console.log(`API Origin: ${origin}`);
console.log(`Socket Path: ${path}`);
console.log(`Transports: ${transports.join(', ')}`);
console.log(`Full URL: ${origin}${path}`);
console.log('');

// Test results tracker
let totalTests = 0;
let passedTests = 0;

function logTest(name, passed, details = '') {
    totalTests++;
    if (passed) {
        passedTests++;
        console.log(`✅ ${name} - PASS ${details}`);
    } else {
        console.log(`❌ ${name} - FAIL ${details}`);
    }
}

function logSummary() {
    console.log('');
    console.log('================================');
    console.log(`📊 Test Results: ${passedTests}/${totalTests} passed`);
    
    if (passedTests === totalTests) {
        console.log('🎉 All tests passed!');
        process.exit(0);
    } else {
        console.log('⚠️  Some tests failed');
        process.exit(1);
    }
}

// Test 1: Diagnostic endpoint
async function testDiagnosticEndpoint() {
    return new Promise((resolve) => {
        const url = `${origin}/api/socketio-diag`;
        const client = origin.startsWith('https:') ? https : http;
        
        const req = client.get(url, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    const passed = res.statusCode === 200 && parsed.ok === true && parsed.path && parsed.now;
                    logTest('Diagnostic Endpoint', passed, `(${res.statusCode}) ${passed ? `Path: ${parsed.path}` : data.substring(0, 50)}`);
                } catch (err) {
                    logTest('Diagnostic Endpoint', false, `Parse error: ${err.message}`);
                }
                resolve();
            });
        });
        
        req.on('error', (err) => {
            logTest('Diagnostic Endpoint', false, `Request error: ${err.message}`);
            resolve();
        });
        
        req.setTimeout(10000, () => {
            logTest('Diagnostic Endpoint', false, 'Timeout');
            req.destroy();
            resolve();
        });
    });
}

// Test 2: Socket.IO Polling connection
async function testPollingConnection() {
    return new Promise((resolve) => {
        const socket = io(origin, {
            path: path,
            transports: ['polling'],
            timeout: 10000,
            forceNew: true
        });

        let connected = false;
        let error = null;

        socket.on('connect', () => {
            connected = true;
            logTest('Socket.IO Polling', true, `Connected with ID: ${socket.id}`);
            socket.disconnect();
            resolve();
        });

        socket.on('connect_error', (err) => {
            error = err;
            logTest('Socket.IO Polling', false, `Connection error: ${err.message}`);
            resolve();
        });

        // Timeout handler
        setTimeout(() => {
            if (!connected && !error) {
                logTest('Socket.IO Polling', false, 'Timeout - no connection or error');
                socket.disconnect();
                resolve();
            }
        }, 15000);
    });
}

// Test 3: Socket.IO WebSocket connection
async function testWebSocketConnection() {
    return new Promise((resolve) => {
        const socket = io(origin, {
            path: path,
            transports: ['websocket'],
            timeout: 10000,
            forceNew: true
        });

        let connected = false;
        let error = null;

        socket.on('connect', () => {
            connected = true;
            logTest('Socket.IO WebSocket', true, `Connected with ID: ${socket.id}`);
            socket.disconnect();
            resolve();
        });

        socket.on('connect_error', (err) => {
            error = err;
            logTest('Socket.IO WebSocket', false, `Connection error: ${err.message}`);
            resolve();
        });

        // Timeout handler
        setTimeout(() => {
            if (!connected && !error) {
                logTest('Socket.IO WebSocket', false, 'Timeout - no connection or error');
                socket.disconnect();
                resolve();
            }
        }, 15000);
    });
}

// Test 4: Socket.IO Mixed transport connection (polling + websocket upgrade)
async function testMixedTransportConnection() {
    return new Promise((resolve) => {
        const socket = io(origin, {
            path: path,
            transports: transports,
            timeout: 10000,
            forceNew: true
        });

        let connected = false;
        let error = null;
        let transportUsed = null;

        socket.on('connect', () => {
            connected = true;
            transportUsed = socket.io.engine.transport.name;
            logTest('Socket.IO Mixed Transport', true, `Connected via ${transportUsed} with ID: ${socket.id}`);
            
            // Listen for transport upgrade
            socket.io.engine.on('upgrade', () => {
                const newTransport = socket.io.engine.transport.name;
                console.log(`  🔄 Transport upgraded to: ${newTransport}`);
            });
            
            // Wait a bit for potential upgrade, then disconnect
            setTimeout(() => {
                socket.disconnect();
                resolve();
            }, 3000);
        });

        socket.on('connect_error', (err) => {
            error = err;
            logTest('Socket.IO Mixed Transport', false, `Connection error: ${err.message}`);
            resolve();
        });

        // Timeout handler
        setTimeout(() => {
            if (!connected && !error) {
                logTest('Socket.IO Mixed Transport', false, 'Timeout - no connection or error');
                socket.disconnect();
                resolve();
            }
        }, 15000);
    });
}

// Main test execution
async function runTests() {
    console.log('🧪 Running Socket.IO diagnostics tests...\n');
    
    try {
        await testDiagnosticEndpoint();
        await testPollingConnection();
        await testWebSocketConnection();
        await testMixedTransportConnection();
    } catch (error) {
        console.error('Unexpected error during testing:', error);
    }
    
    logSummary();
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

// Run the tests
runTests().catch((error) => {
    console.error('Failed to run tests:', error);
    process.exit(1);
});