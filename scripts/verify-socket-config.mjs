#!/usr/bin/env node

/**
 * Socket.IO Config Gate Script
 * Verifies frontend and backend Socket.IO path consistency before testing
 * Exits with error code 1 if paths don't match
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function verifySocketConfig() {
    try {
        // 1. Read frontend .env file to get NEXT_PUBLIC_SOCKET_PATH
        const frontendEnvPath = join(__dirname, '../frontend/.env');
        const frontendEnv = readFileSync(frontendEnvPath, 'utf8');
        
        const frontendSocketPathMatch = frontendEnv.match(/^NEXT_PUBLIC_SOCKET_PATH=(.+)$/m);
        const frontendSocketPath = frontendSocketPathMatch ? frontendSocketPathMatch[1].trim() : null;
        
        console.log('🔍 Verifying Socket.IO Configuration...');
        console.log(`Frontend Socket Path: ${frontendSocketPath || 'NOT FOUND'}`);
        
        // 2. Fetch backend socket config from /api/socket/config endpoint
        const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://pifa-stability.preview.emergentagent.com';
        const configUrl = `${backendUrl}/api/socket/config`;
        
        console.log(`Fetching backend config from: ${configUrl}`);
        
        const response = await fetch(configUrl);
        if (!response.ok) {
            throw new Error(`Backend config endpoint returned ${response.status}: ${response.statusText}`);
        }
        
        const backendConfig = await response.json();
        const backendSocketPath = backendConfig.path;
        
        console.log(`Backend Socket Path: ${backendSocketPath}`);
        
        // 3. Compare paths
        if (!frontendSocketPath) {
            console.error('❌ CONFIGURATION ERROR: NEXT_PUBLIC_SOCKET_PATH not found in frontend/.env');
            process.exit(1);
        }
        
        if (frontendSocketPath !== backendSocketPath) {
            console.error('❌ SOCKET PATH MISMATCH DETECTED!');
            console.error(`Frontend: ${frontendSocketPath}`);
            console.error(`Backend: ${backendSocketPath}`);
            console.error('');
            console.error('Fix required: Update frontend/.env to match backend configuration');
            process.exit(1);
        }
        
        // 4. Success
        console.log('✅ Socket.IO Configuration Verified');
        console.log(`Both frontend and backend use path: ${frontendSocketPath}`);
        console.log('');
        
    } catch (error) {
        console.error('❌ Configuration verification failed:', error.message);
        process.exit(1);
    }
}

// Run verification if called directly
if (process.argv[1] === __filename || process.argv[1].endsWith('verify-socket-config.mjs')) {
    verifySocketConfig();
}

export { verifySocketConfig };