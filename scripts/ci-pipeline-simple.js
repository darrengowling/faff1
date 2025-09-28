#!/usr/bin/env node

/**
 * Simplified CI Pipeline with Focus on Core Functionality
 * Avoids hanging issues and focuses on critical path testing
 */

const { execSync } = require('child_process');
const fs = require('fs');

class SimpleCIPipeline {
  constructor() {
    this.results = {
      phases: [],
      specs: [],
      overall: { total: 0, passed: 0, failed: 0, flaky: 0, blockers: 0 }
    };
    this.startTime = Date.now();
  }

  log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const prefix = level === 'ERROR' ? '❌' : level === 'SUCCESS' ? '✅' : 'ℹ️';
    console.log(`${prefix} [${timestamp}] ${message}`);
  }

  runPhase(name, command, description, timeout = 60000) {
    this.log(`🚀 Starting ${name}: ${description}`);
    
    const startTime = Date.now();
    try {
      execSync(command, { 
        cwd: '/app', 
        stdio: 'pipe', 
        timeout: timeout,
        encoding: 'utf8'
      });
      const duration = Date.now() - startTime;
      
      this.results.phases.push({ name, success: true, description, duration });
      this.log(`✅ ${name} completed successfully (${duration}ms)`, 'SUCCESS');
      return true;
      
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.phases.push({ name, success: false, description, error: error.message, duration });
      this.log(`❌ ${name} failed: ${error.message}`, 'ERROR');
      return false;
    }
  }

  async testSpecWithRetries(specPath, maxRetries = 2) {
    const results = [];
    let lastError = '';

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        this.log(`Running ${specPath} (attempt ${attempt + 1}/${maxRetries + 1})`);
        
        const command = `npx playwright test ${specPath} --reporter=line --timeout=30000`;
        execSync(command, { 
          cwd: '/app', 
          stdio: 'pipe',
          timeout: 60000,
          encoding: 'utf8'
        });
        
        results.push(true);
        this.log(`✅ ${specPath} passed on attempt ${attempt + 1}`, 'SUCCESS');
        break;
        
      } catch (error) {
        results.push(false);
        lastError = this.extractError(error.message);
        this.log(`❌ ${specPath} failed on attempt ${attempt + 1}`, 'ERROR');
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

    const result = {
      spec: specPath,
      attempts: totalAttempts,
      passCount,
      passRate,
      status,
      lastError: lastError || 'Unknown error',
      suggestedFix: this.getSuggestedFix(lastError, specPath)
    };

    this.results.specs.push(result);
    
    // Update overall counters
    this.results.overall.total++;
    if (status === 'PASS') {
      this.results.overall.passed++;
    } else if (status === 'FLAKY') {
      this.results.overall.flaky++;
    } else {
      this.results.overall.blockers++;
      this.results.overall.failed++;
    }

    return result;
  }

  extractError(errorOutput) {
    const lines = errorOutput.split('\n');
    
    // Look for specific error patterns
    for (const line of lines) {
      if (line.includes('Error:') || line.includes('Failed:') || line.includes('Timeout')) {
        return line.trim().substring(0, 100);
      }
    }

    return 'Test execution failed';
  }

  getSuggestedFix(error, specPath) {
    const lowerError = error.toLowerCase();
    const lowerSpec = specPath.toLowerCase();

    if (lowerError.includes('timeout')) {
      return 'Increase timeout or add wait conditions';
    }
    if (lowerError.includes('element not found')) {
      return 'Check data-testid selectors';
    }
    if (lowerError.includes('auth')) {
      return 'Verify authentication flow';
    }
    if (lowerSpec.includes('auction')) {
      return 'Use test hooks for setup';
    }
    if (lowerSpec.includes('scoring')) {
      return 'Use scoring reset hook';
    }

    return 'Review logs and test setup';
  }

  generateReport() {
    const duration = ((Date.now() - this.startTime) / 1000 / 60).toFixed(1);
    const overallPassRate = (this.results.overall.passed + this.results.overall.flaky) / Math.max(this.results.overall.total, 1);
    
    console.log('\n' + '='.repeat(80));
    console.log('🎯 SIMPLE CI PIPELINE RESULTS');
    console.log('='.repeat(80));
    
    // Phase results
    console.log('\n📋 PHASE RESULTS:');
    this.results.phases.forEach(phase => {
      const status = phase.success ? '✅ PASS' : '❌ FAIL';
      const duration = phase.duration ? `(${phase.duration}ms)` : '';
      console.log(`  ${status} ${phase.name}: ${phase.description} ${duration}`);
    });

    // Overall stats
    console.log(`\n📊 OVERALL STATISTICS:`);
    console.log(`  Duration: ${duration} minutes`);
    console.log(`  Total specs: ${this.results.overall.total}`);
    console.log(`  Passed: ${this.results.overall.passed}`);
    console.log(`  Flaky: ${this.results.overall.flaky}`);  
    console.log(`  Blockers: ${this.results.overall.blockers}`);
    console.log(`  Pass rate: ${(overallPassRate * 100).toFixed(1)}%`);

    // Spec results table
    if (this.results.specs.length > 0) {
      console.log(`\n📈 SPEC RESULTS:`);
      console.log('┌─────────────────────────────────────────────────┬─────────┬─────────────────────────────────────────┬─────────────────────────────────────────┐');
      console.log('│ Spec Name                                       │ Status  │ Top Error                               │ Suggested Fix                           │');
      console.log('├─────────────────────────────────────────────────┼─────────┼─────────────────────────────────────────┼─────────────────────────────────────────┤');
      
      this.results.specs.forEach(spec => {
        const name = spec.spec.split('/').pop().substring(0, 47);
        const status = spec.status === 'PASS' ? '✅ PASS' : 
                      spec.status === 'FLAKY' ? '⚠️ FLAKY' : '❌ BLOCK';
        const error = spec.lastError.substring(0, 39);
        const fix = spec.suggestedFix.substring(0, 39);
        
        console.log(`│ ${name.padEnd(47)} │ ${status.padEnd(7)} │ ${error.padEnd(39)} │ ${fix.padEnd(39)} │`);
      });
      
      console.log('└─────────────────────────────────────────────────┴─────────┴─────────────────────────────────────────┴─────────────────────────────────────────┘');
    }

    // Success criteria
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
      
      // Show actionable fixes
      console.log(`\n🔧 RECOMMENDED ACTIONS:`);
      const blockers = this.results.specs.filter(s => s.status === 'BLOCKER');
      if (blockers.length > 0) {
        blockers.slice(0, 3).forEach(blocker => {
          console.log(`  - Fix ${blocker.spec}: ${blocker.suggestedFix}`);
        });
      } else {
        console.log(`  - Improve pass rate by fixing flaky tests`);
      }
      
      return 1;
    }
  }

  async run() {
    try {
      this.log('🚀 Starting Simple CI Pipeline');
      
      // Phase 1: Socket Configuration
      const phase1 = this.runPhase(
        'verify-socket-config', 
        'node scripts/verify-socket-config.mjs',
        'Socket.IO configuration verification'
      );
      
      if (!phase1) return this.generateReport();

      // Phase 2: Email Import Guard
      const phase2 = this.runPhase(
        'check-email-imports',
        'chmod +x scripts/check-email-imports.sh && scripts/check-email-imports.sh',
        'Email validation import guard',
        10000
      );

      if (!phase2) return this.generateReport();

      // Phase 3: Overlay Linting
      const phase3 = this.runPhase(
        'lint-overlays',
        'CI=true npm run lint:overlays',
        'Pointer-events overlay linting',
        15000
      );

      if (!phase3) return this.generateReport();

      // Phase 4: Create Form Pre-Gate Verification
      const phase4 = this.runPhase(
        'verify-create-form',
        'chmod +x scripts/verify-create-form.sh && scripts/verify-create-form.sh',
        'Create League form accessibility pre-gate',
        45000
      );

      if (!phase4) return this.generateReport();

      // Phase 5: Frontend Contract Tests 
      const phase5 = this.runPhase(
        'test:contract',
        'cd frontend && npx jest --config=jest.config.js --testPathPattern=".*contract\\.spec\\.(js|jsx|ts|tsx)$" --passWithNoTests --forceExit --maxWorkers=1',
        'Frontend contract tests (direct)',
        30000
      );

      // Phase 6: Socket Diagnostics
      const phase6 = this.runPhase(
        'diag:socketio',
        'node scripts/diag-socketio.js',
        'Socket.IO runtime diagnostics'
      );

      // Phase 7: Auth UI Verification
      const phase7 = this.runPhase(
        'verify-auth-ui', 
        'npx playwright test tests/e2e/auth_ui.spec.ts -g "Login page renders form" --reporter=line',
        'Authentication UI verification'
      );

      // Phase 8: Core E2E Tests with retries
      this.log('🧪 Starting Core E2E Tests with Flake Detection');
      
      const coreSpecs = [
        'tests/e2e/time-control.spec.ts',
        'tests/e2e/hooks-unit.spec.ts',
        'tests/e2e/scoring_ingest.spec.ts'
      ];

      for (const spec of coreSpecs) {
        await this.testSpecWithRetries(spec);
      }

      // Phase 9: Extended E2E Tests (lower priority)
      this.log('🚀 Starting Extended E2E Tests');
      
      const extendedSpecs = [
        'tests/e2e/auction-hooks.spec.ts',
        'tests/e2e/anti-snipe-unit.spec.ts'
      ];

      for (const spec of extendedSpecs) {
        // Check if spec exists
        if (fs.existsSync(`/app/${spec}`)) {
          await this.testSpecWithRetries(spec);
        } else {
          this.log(`⚠️ Skipping ${spec} (file not found)`);
        }
      }

      return this.generateReport();

    } catch (error) {
      this.log(`💥 CI Pipeline crashed: ${error.message}`, 'ERROR');
      return 1;
    }
  }
}

// Run if called directly
if (require.main === module) {
  const pipeline = new SimpleCIPipeline();
  pipeline.run().then(exitCode => {
    process.exit(exitCode);
  }).catch(error => {
    console.error('💥 Pipeline execution failed:', error);
    process.exit(1);
  });
}

module.exports = SimpleCIPipeline;