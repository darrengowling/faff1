#!/usr/bin/env node

/**
 * Test script for overlay linting functionality
 * Ensures the linter catches common pointer-events violations
 */

const { checkFile, VIOLATION_PATTERNS } = require('./lint-overlays.js');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Test cases
const TEST_CASES = [
  {
    name: 'CSS header with pointer-events auto',
    content: 'header { pointer-events: auto; color: red; }',
    shouldViolate: true
  },
  {
    name: 'CSS drawer with pointer-events auto',
    content: '.drawer-panel { pointer-events: auto; }',
    shouldViolate: true
  },
  {
    name: 'JSX header with inline style',
    content: '<header style={{ pointerEvents: "auto" }}>Content</header>',
    shouldViolate: true
  },
  {
    name: 'JSX with pointer-events-auto class',
    content: '<header className="flex pointer-events-auto">Menu</header>',
    shouldViolate: true
  },
  {
    name: 'React Header component with inline style',
    content: '<Header style={{ pointerEvents: "auto", color: "blue" }} />',
    shouldViolate: true
  },
  {
    name: 'Safe header with pointer-events none',
    content: 'header { pointer-events: none; }',
    shouldViolate: false
  },
  {
    name: 'Safe drawer with pointer-events none',
    content: '.drawer-backdrop { pointer-events: none !important; }',
    shouldViolate: false
  },
  {
    name: 'Non-header element with pointer-events auto',
    content: '.button { pointer-events: auto; }',
    shouldViolate: false
  },
  {
    name: 'Header with other properties only',
    content: 'header { background: blue; z-index: 40; }',
    shouldViolate: false
  }
];

/**
 * Run a single test case
 */
function runTestCase(testCase, index) {
  const tempDir = os.tmpdir();
  const extension = testCase.content.includes('<') ? '.jsx' : '.css';
  const tempFile = path.join(tempDir, `test-overlay-${index}${extension}`);
  
  try {
    // Write test content to temp file
    fs.writeFileSync(tempFile, testCase.content);
    
    // Check for violations
    const violations = checkFile(tempFile);
    const hasViolations = violations.length > 0;
    
    // Verify result matches expectation
    if (hasViolations === testCase.shouldViolate) {
      console.log(`✅ ${testCase.name}`);
      return true;
    } else {
      console.log(`❌ ${testCase.name}`);
      console.log(`   Expected violations: ${testCase.shouldViolate}, Got: ${hasViolations}`);
      if (violations.length > 0) {
        violations.forEach(v => console.log(`   Violation: ${v.description}`));
      }
      return false;
    }
    
  } catch (error) {
    console.log(`❌ ${testCase.name} - Error: ${error.message}`);
    return false;
  } finally {
    // Cleanup temp file
    try {
      if (fs.existsSync(tempFile)) {
        fs.unlinkSync(tempFile);
      }
    } catch (cleanupError) {
      // Ignore cleanup errors
    }
  }
}

/**
 * Main test execution
 */
function main() {
  console.log('🧪 Testing overlay linting functionality...\n');
  
  let passed = 0;
  let total = TEST_CASES.length;
  
  TEST_CASES.forEach((testCase, index) => {
    if (runTestCase(testCase, index)) {
      passed++;
    }
  });
  
  console.log(`\n📊 Test Results: ${passed}/${total} passed`);
  
  if (passed === total) {
    console.log('✅ All tests passed - overlay linting is working correctly');
    process.exit(0);
  } else {
    console.log('❌ Some tests failed - overlay linting needs fixes');
    process.exit(1);
  }
}

// Run tests if executed directly
if (require.main === module) {
  main();
}