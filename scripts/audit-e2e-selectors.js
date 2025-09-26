#!/usr/bin/env node

/**
 * E2E Selector Audit Script
 * Scans E2E test files for non-testid selectors and fails if found
 * Ensures all E2E tests use stable data-testid selectors only
 */

const fs = require('fs');
const path = require('path');

// Patterns that indicate non-testid selectors (should be avoided)
const FORBIDDEN_SELECTOR_PATTERNS = [
  // Text-based selectors
  /page\.locator\(['"`]text=/i,
  /page\.waitForSelector\(['"`]text=/i,
  /page\.click\(['"`]text=/i,
  /page\.fill\(['"`]text=/i,
  
  // Role-based selectors
  /page\.locator\(['"`]role=/i,
  /page\.waitForSelector\(['"`]role=/i,
  /page\.click\(['"`]role=/i,
  
  // CSS selectors without data-testid
  /page\.locator\(['"`][^'"`]*(?<!data-testid=)[.#][^'"`]*['"`]\)/i,
  /page\.waitForSelector\(['"`][^'"`]*(?<!data-testid=)[.#][^'"`]*['"`]\)/i,
  /page\.click\(['"`][^'"`]*(?<!data-testid=)[.#][^'"`]*['"`]\)/i,
  
  // Button text selectors
  /button:has-text\(/i,
  /text\s*=\s*['"`]/i,
  
  // Generic element selectors without testid
  /page\.locator\(['"`](button|input|div|span|a|form)[^'"`]*['"`]\)(?!.*data-testid)/i,
  /page\.click\(['"`](button|input|div|span|a|form)[^'"`]*['"`]\)(?!.*data-testid)/i,
];

// Allowed patterns (these are OK to use)
const ALLOWED_SELECTOR_PATTERNS = [
  // data-testid selectors
  /data-testid=/i,
  
  // URL/navigation patterns
  /waitForURL/i,
  /goto\(/i,
  
  // TESTIDS constant usage
  /TESTIDS\./i,
  
  // Specific exceptions for debugging
  /screenshot/i,
  /console\./i,
];

function scanFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const violations = [];
  
  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    const trimmedLine = line.trim();
    
    // Skip comments and empty lines
    if (trimmedLine.startsWith('//') || trimmedLine.startsWith('*') || trimmedLine === '') {
      return;
    }
    
    // Check for forbidden patterns
    for (const pattern of FORBIDDEN_SELECTOR_PATTERNS) {
      if (pattern.test(line)) {
        // Check if this line has any allowed patterns that would make it OK
        const hasAllowedPattern = ALLOWED_SELECTOR_PATTERNS.some(allowedPattern => 
          allowedPattern.test(line)
        );
        
        if (!hasAllowedPattern) {
          violations.push({
            file: filePath,
            line: lineNumber,
            content: trimmedLine,
            pattern: pattern.toString()
          });
        }
      }
    }
  });
  
  return violations;
}

function scanDirectory(dirPath) {
  const allViolations = [];
  
  function walkDir(dir) {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        walkDir(fullPath);
      } else if (item.endsWith('.spec.ts') || item.endsWith('.spec.js') || item.endsWith('.test.ts')) {
        const violations = scanFile(fullPath);
        allViolations.push(...violations);
      }
    }
  }
  
  walkDir(dirPath);
  return allViolations;
}

function main() {
  console.log('🔍 E2E Selector Audit Starting...');
  console.log('Scanning for non-testid selectors in E2E tests...');
  console.log('');
  
  const e2eDir = path.join(__dirname, '..', 'tests', 'e2e');
  
  if (!fs.existsSync(e2eDir)) {
    console.error('❌ E2E test directory not found:', e2eDir);
    process.exit(1);
  }
  
  const violations = scanDirectory(e2eDir);
  
  if (violations.length === 0) {
    console.log('✅ Selector audit passed!');
    console.log('All E2E tests are using data-testid selectors correctly.');
    console.log('');
    process.exit(0);
  }
  
  console.log(`❌ Found ${violations.length} selector violations:`);
  console.log('');
  
  // Group violations by file
  const violationsByFile = {};
  violations.forEach(v => {
    if (!violationsByFile[v.file]) {
      violationsByFile[v.file] = [];
    }
    violationsByFile[v.file].push(v);
  });
  
  // Print violations
  Object.keys(violationsByFile).forEach(file => {
    const relativePath = path.relative(process.cwd(), file);
    console.log(`📁 ${relativePath}:`);
    
    violationsByFile[file].forEach(violation => {
      console.log(`  Line ${violation.line}: ${violation.content}`);
      console.log(`    ⚠️  Matches forbidden pattern: ${violation.pattern}`);
      console.log('');
    });
  });
  
  console.log('💡 Fix Guide:');
  console.log('  - Replace text selectors with data-testid selectors');
  console.log('  - Replace role selectors with data-testid selectors');
  console.log('  - Replace CSS class/ID selectors with data-testid selectors');
  console.log('  - Use TESTIDS constants for consistent selector naming');
  console.log('');
  console.log('  Example fixes:');
  console.log('    ❌ page.click("text=Create League")');
  console.log('    ✅ page.click(`[data-testid="${TESTIDS.createLeagueBtn}"]`)');
  console.log('');
  console.log('    ❌ page.locator("button")');
  console.log('    ✅ page.locator(`[data-testid="${TESTIDS.submitBtn}"]`)');
  console.log('');
  
  process.exit(1);
}

if (require.main === module) {
  main();
}

module.exports = { scanFile, scanDirectory };