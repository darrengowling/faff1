#!/usr/bin/env node

/**
 * Database Migration Runner for Configurable Settings
 * Usage: npm run db:migrate:config
 */

const { spawn } = require('child_process');
const path = require('path');

const PYTHON_SCRIPT = path.join(__dirname, '..', 'backend', 'migrations', '001_add_configurable_settings.py');

console.log('🚀 Starting Database Migration: Configurable Settings');
console.log('=' .repeat(60));

// Set environment variables
const env = {
    ...process.env,
    PYTHONPATH: path.join(__dirname, '..', 'backend')
};

// Run Python migration script
const migration = spawn('python3', [PYTHON_SCRIPT], {
    stdio: 'inherit',
    env: env,
    cwd: path.join(__dirname, '..')
});

migration.on('close', (code) => {
    if (code === 0) {
        console.log('\n✅ Migration completed successfully!');
        console.log('📋 Changes applied:');
        console.log('   • Competition profiles collection created');
        console.log('   • Leagues schema updated with configurable settings');
        console.log('   • Existing leagues backfilled with defaults');
        console.log('   • Rosters updated with new settings');
        process.exit(0);
    } else {
        console.error(`\n❌ Migration failed with exit code ${code}`);
        process.exit(1);
    }
});

migration.on('error', (error) => {
    console.error(`❌ Failed to start migration: ${error.message}`);
    process.exit(1);
});