#!/usr/bin/env node

/**
 * Comprehensive CI Pipeline with Flake Detection
 * Runs tests in order, detects flaky tests, and provides actionable failure reports
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class CIPipeline {
  constructor() {
    this.results = {
      phases: {},
      specs: {},
      overall: {
        total: 0,
        passed: 0,
        failed: 0,
        flaky: 0,
        blockers: 0
      }
    };
    this.startTime = Date.now();
  }

  log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const prefix = level === 'ERROR' ? '❌' : level === 'WARN' ? '⚠️' : level === 'SUCCESS' ? '✅' : 'ℹ️';
    console.log(`${prefix} [${timestamp}] ${message}`);
  }

  async runCommand(command, cwd = process.cwd(), timeout = 300000) {
    return new Promise((resolve, reject) => {
      const child = spawn('bash', ['-c', command], { 
        cwd, 
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, FORCE_COLOR: '0' }
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      const timer = setTimeout(() => {
        child.kill('SIGTERM');
        reject(new Error(`Command timed out after ${timeout}ms: ${command}`));
      }, timeout);

      child.on('close', (code) => {
        clearTimeout(timer);
        resolve({
          code,
          stdout,
          stderr,
          success: code === 0
        });
      });

      child.on('error', (error) => {
        clearTimeout(timer);  
        reject(error);
      });
    });
  }

  async testSpecWithRetries(specPath, maxRetries = 2) {
    const results = [];
    let lastError = '';

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        this.log(`Running ${specPath} (attempt ${attempt + 1}/${maxRetries + 1})`);
        
        const command = `npx playwright test ${specPath} --reporter=json`;
        const result = await this.runCommand(command, '/app', 60000);
        
        const success = result.code === 0;
        results.push(success);

        if (!success && result.stderr) {
          lastError = this.extractError(result.stderr, result.stdout);
        }

        if (success) {
          this.log(`✅ ${specPath} passed on attempt ${attempt + 1}`, 'SUCCESS');
          break;
        } else {
          this.log(`❌ ${specPath} failed on attempt ${attempt + 1}`, 'ERROR');
        }

      } catch (error) {
        results.push(false);
        lastError = error.message;
        this.log(`❌ ${specPath} errored on attempt ${attempt + 1}: ${error.message}`, 'ERROR');
      }
    }

    const passCount = results.filter(r => r).length;
    const totalAttempts = results.length;
    const passRate = passCount / totalAttempts;

    let status = 'BLOCKER';
    if (passRate >= 1) {
      status = 'PASS';
    } else if (passRate >= 1/3) {
      status = 'FLAKY';
    }

    return {
      spec: specPath,
      attempts: totalAttempts,
      passCount,
      passRate,
      status,
      lastError: lastError || 'Unknown error',
      suggestedFix: this.getSuggestedFix(lastError, specPath)
    };
  }

  extractError(stderr, stdout) {
    // Extract meaningful error from playwright output
    const lines = (stderr + stdout).split('\n');
    
    // Look for specific error patterns
    const errorPatterns = [
      /Error: (.+)/,
      /TimeoutError: (.+)/,
      /AssertionError: (.+)/,
      /Failed to (.+)/,
      /Cannot (.+)/,
      /Test timeout/,
      /Element not found/,
      /Navigation failed/
    ];

    for (const line of lines) {
      for (const pattern of errorPatterns) {
        const match = line.match(pattern);
        if (match) {
          return match[1] || match[0];
        }
      }
    }

    // Fallback to first non-empty line with "error" or "fail"
    for (const line of lines) {
      if (line.toLowerCase().includes('error') || line.toLowerCase().includes('fail')) {
        return line.trim().substring(0, 100);
      }
    }

    return 'Unknown test failure';
  }

  getSuggestedFix(error, specPath) {
    const lowerError = error.toLowerCase();
    const lowerSpec = specPath.toLowerCase();

    // Error-based suggestions
    if (lowerError.includes('timeout')) {
      return 'Increase timeout or add wait conditions';
    }
    if (lowerError.includes('element not found') || lowerError.includes('locator')) {
      return 'Check data-testid selectors or add wait for element';
    }
    if (lowerError.includes('navigation')) {
      return 'Add navigation wait or check URL patterns';
    }
    if (lowerError.includes('socket') || lowerError.includes('connection')) {
      return 'Check socket.io configuration or add connection retry';
    }
    if (lowerError.includes('auth')) {
      return 'Verify authentication flow or test credentials';
    }

    // Spec-based suggestions
    if (lowerSpec.includes('auction')) {
      return 'Use test hooks for auction setup instead of UI';
    }
    if (lowerSpec.includes('scoring')) {
      return 'Use scoring reset hook before test';
    }
    if (lowerSpec.includes('reconnect')) {
      return 'Check socket drop test hooks';
    }

    return 'Review logs and add deterministic test setup';
  }

  async runPhase(phaseName, command, description) {
    this.log(`🚀 Starting ${phaseName}: ${description}`);
    
    try {
      const result = await this.runCommand(command, '/app', 120000);
      
      const success = result.code === 0;
      this.results.phases[phaseName] = {
        success,
        output: result.stdout,
        error: result.stderr,
        description
      };

      if (success) {
        this.log(`✅ ${phaseName} completed successfully`, 'SUCCESS');
      } else {
        this.log(`❌ ${phaseName} failed`, 'ERROR');
        this.log(`Error: ${result.stderr}`, 'ERROR');
      }

      return success;

    } catch (error) {
      this.log(`❌ ${phaseName} errored: ${error.message}`, 'ERROR');
      this.results.phases[phaseName] = {
        success: false,
        error: error.message,
        description
      };
      return false;
    }
  }

  async runE2ESpecs(specs, phaseName) {
    this.log(`🧪 Starting ${phaseName} E2E tests`);
    
    const specResults = [];
    
    for (const spec of specs) {
      const result = await this.testSpecWithRetries(spec);
      specResults.push(result);
      this.results.specs[spec] = result;
      
      // Update overall counters
      this.results.overall.total++;
      if (result.status === 'PASS') {
        this.results.overall.passed++;
      } else if (result.status === 'FLAKY') {
        this.results.overall.flaky++;
      } else if (result.status === 'BLOCKER') {
        this.results.overall.blockers++;
        this.results.overall.failed++;
      }
    }

    const phasePassRate = specResults.filter(r => r.status !== 'BLOCKER').length / specResults.length;
    this.log(`📊 ${phaseName} completed: ${(phasePassRate * 100).toFixed(1)}% pass rate`);
    
    return specResults;
  }

  generateReport() {
    const duration = ((Date.now() - this.startTime) / 1000 / 60).toFixed(1);
    const overallPassRate = (this.results.overall.passed + this.results.overall.flaky) / this.results.overall.total;
    
    console.log('\n' + '='.repeat(80));
    console.log('🎯 CI PIPELINE RESULTS');
    console.log('='.repeat(80));
    
    // Phase results
    console.log('\n📋 PHASE RESULTS:');
    Object.entries(this.results.phases).forEach(([phase, result]) => {
      const status = result.success ? '✅ PASS' : '❌ FAIL';
      console.log(`  ${status} ${phase}: ${result.description}`);
    });

    // Overall stats
    console.log(`\n📊 OVERALL STATISTICS:`);
    console.log(`  Duration: ${duration} minutes`);
    console.log(`  Total specs: ${this.results.overall.total}`);
    console.log(`  Passed: ${this.results.overall.passed}`);
    console.log(`  Flaky: ${this.results.overall.flaky}`);  
    console.log(`  Blockers: ${this.results.overall.blockers}`);
    console.log(`  Pass rate: ${(overallPassRate * 100).toFixed(1)}%`);

    // Spec details table
    if (this.results.overall.total > 0) {
      console.log(`\n📈 SPEC RESULTS:`);
      console.log('┌─────────────────────────────────────────────────┬─────────┬─────────────────────────────────────────┬─────────────────────────────────────────┐');
      console.log('│ Spec Name                                       │ Status  │ Top Error                               │ Suggested Fix                           │');
      console.log('├─────────────────────────────────────────────────┼─────────┼─────────────────────────────────────────┼─────────────────────────────────────────┤');
      
      Object.values(this.results.specs).forEach(spec => {
        const name = spec.spec.split('/').pop().substring(0, 47);
        const status = spec.status === 'PASS' ? '✅ PASS' : 
                      spec.status === 'FLAKY' ? '⚠️ FLAKY' : '❌ BLOCK';
        const error = spec.lastError.substring(0, 39);
        const fix = spec.suggestedFix.substring(0, 39);
        
        console.log(`│ ${name.padEnd(47)} │ ${status.padEnd(7)} │ ${error.padEnd(39)} │ ${fix.padEnd(39)} │`);
      });
      
      console.log('└─────────────────────────────────────────────────┴─────────┴─────────────────────────────────────────┴─────────────────────────────────────────┘');
    }

    // Success/failure determination
    const meetsTarget = overallPassRate >= 0.9;
    const hasBlockers = this.results.overall.blockers > 0;
    
    console.log(`\n🎯 SUCCESS CRITERIA:`);
    console.log(`  Pass rate ≥90%: ${meetsTarget ? '✅' : '❌'} (${(overallPassRate * 100).toFixed(1)}%)`);
    console.log(`  Zero blockers: ${hasBlockers ? '❌' : '✅'} (${this.results.overall.blockers} blockers)`);
    
    const overallSuccess = meetsTarget && !hasBlockers;
    
    if (overallSuccess) {
      console.log(`\n🎉 CI PIPELINE SUCCESS: Ready for deployment!`);
      return 0;
    } else {
      console.log(`\n💥 CI PIPELINE FAILURE:`);
      if (!meetsTarget) {
        console.log(`  - Pass rate ${(overallPassRate * 100).toFixed(1)}% is below 90% target`);
      }
      if (hasBlockers) {
        console.log(`  - ${this.results.overall.blockers} blocker specs prevent deployment`);
      }
      console.log(`\n🔧 RECOMMENDED ACTIONS:`);
      
      // Show top blockers
      const blockers = Object.values(this.results.specs).filter(s => s.status === 'BLOCKER');
      blockers.slice(0, 3).forEach(blocker => {
        console.log(`  - Fix ${blocker.spec}: ${blocker.suggestedFix}`);
      });
      
      return 1;
    }
  }

  async run() {
    try {
      this.log('🚀 Starting CI Pipeline with Flake Detection');
      
      // Phase 1: Basic Verification
      const phase1Success = await this.runPhase('verify-socket-config', 
        'cd /app && node scripts/verify-socket-config.mjs', 
        'Socket.IO configuration verification');
      
      if (!phase1Success) {
        this.log('❌ Socket config verification failed - aborting pipeline', 'ERROR');
        return this.generateReport();
      }

      // Phase 2: Contract Tests
      const phase2Success = await this.runPhase('test:contract',
        'cd /app/frontend && npm run test:contract',
        'Frontend contract tests');
      
      if (!phase2Success) {
        this.log('❌ Contract tests failed - aborting pipeline', 'ERROR');
        return this.generateReport();
      }

      // Phase 3: Socket Diagnostics  
      const phase3Success = await this.runPhase('diag:socketio',
        'cd /app && node scripts/diag-socketio.js',
        'Socket.IO runtime diagnostics');

      // Phase 4: Auth UI Verification
      const phase4Success = await this.runPhase('verify-auth-ui',
        'cd /app && npx playwright test tests/e2e/auth_ui.spec.ts -g "Login page renders form" --reporter=line',
        'Authentication UI verification');

      // Phase 5: Core E2E Tests
      const coreSpecs = [
        'tests/e2e/auth_ui.spec.ts',
        'tests/e2e/hooks-unit.spec.ts', // Create league via hooks  
        'tests/e2e/auction-hooks.spec.ts', // Start auction, nominate, bid
        'tests/e2e/roster_and_budget.spec.ts' // Roster verification
      ];

      await this.runE2ESpecs(coreSpecs, 'Core E2E');

      // Phase 6: Extended E2E Tests  
      const extendedSpecs = [
        'tests/e2e/auction.spec.ts', // Anti-snipe, simultaneous bids
        'tests/e2e/scoring_ingest.spec.ts', // Scoring system
        'tests/e2e/time-control.spec.ts', // Time control system
        // Add more extended specs as available
      ];

      await this.runE2ESpecs(extendedSpecs, 'Extended E2E');

      return this.generateReport();

    } catch (error) {
      this.log(`💥 CI Pipeline crashed: ${error.message}`, 'ERROR');
      console.error(error.stack);
      return 1;
    }
  }
}

// Run if called directly
if (require.main === module) {
  const pipeline = new CIPipeline();
  pipeline.run().then(exitCode => {
    process.exit(exitCode);
  }).catch(error => {
    console.error('💥 Pipeline execution failed:', error);
    process.exit(1);
  });
}

module.exports = CIPipeline;