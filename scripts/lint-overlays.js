#!/usr/bin/env node

/**
 * Overlay Linting Script
 * 
 * Detects pointer-events:auto usage in header/drawer selectors that could
 * cause overlay issues blocking user interactions.
 * 
 * Treats as warning locally, error in CI.
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Configuration
const isCI = process.env.CI === 'true' || process.env.NODE_ENV === 'production';
const VIOLATION_PATTERNS = [
  // CSS patterns
  {
    pattern: /header[^{]*\{[^}]*pointer-events\s*:\s*auto/gi,
    description: 'header with pointer-events:auto',
    fileTypes: ['css', 'scss', 'less']
  },
  {
    pattern: /\.drawer[^{]*\{[^}]*pointer-events\s*:\s*auto/gi,
    description: 'drawer class with pointer-events:auto',
    fileTypes: ['css', 'scss', 'less']
  },
  // JavaScript/JSX patterns
  {
    pattern: /header[^>]*style\s*=\s*\{\{[^}]*pointerEvents\s*:\s*['"']auto['"']/gi,
    description: 'header with inline pointerEvents:auto',
    fileTypes: ['js', 'jsx', 'ts', 'tsx']
  },
  {
    pattern: /drawer[^>]*style\s*=\s*\{\{[^}]*pointerEvents\s*:\s*['"']auto['"']/gi,
    description: 'drawer with inline pointerEvents:auto',
    fileTypes: ['js', 'jsx', 'ts', 'tsx']
  },
  // Tailwind/className patterns
  {
    pattern: /header[^>]*className\s*=\s*[^>]*pointer-events-auto/gi,
    description: 'header with pointer-events-auto class',
    fileTypes: ['js', 'jsx', 'ts', 'tsx']
  },
  {
    pattern: /drawer[^>]*className\s*=\s*[^>]*pointer-events-auto/gi,
    description: 'drawer with pointer-events-auto class',
    fileTypes: ['js', 'jsx', 'ts', 'tsx']
  },
  // Component name patterns
  {
    pattern: /<Header[^>]*style\s*=\s*\{\{[^}]*pointerEvents\s*:\s*['"']auto['"']/gi,
    description: 'Header component with pointerEvents:auto',
    fileTypes: ['js', 'jsx', 'ts', 'tsx']
  },
  {
    pattern: /<.*Drawer[^>]*style\s*=\s*\{\{[^}]*pointerEvents\s*:\s*['"']auto['"']/gi,
    description: 'Drawer component with pointerEvents:auto',
    fileTypes: ['js', 'jsx', 'ts', 'tsx']
  }
];

// File search patterns
const SEARCH_PATTERNS = [
  'frontend/src/**/*.css',
  'frontend/src/**/*.scss',
  'frontend/src/**/*.less',
  'frontend/src/**/*.js',
  'frontend/src/**/*.jsx',
  'frontend/src/**/*.ts',
  'frontend/src/**/*.tsx'
];

/**
 * Find lines in file content that match a pattern
 */
function findMatchingLines(content, pattern, filename) {
  const lines = content.split('\n');
  const matches = [];
  
  lines.forEach((line, index) => {
    if (pattern.test(line)) {
      matches.push({
        line: index + 1,
        content: line.trim(),
        filename
      });
    }
  });
  
  return matches;
}

/**
 * Check a file for overlay violations
 */
function checkFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const violations = [];
    
    VIOLATION_PATTERNS.forEach(({ pattern, description, fileTypes }) => {
      const fileExt = path.extname(filePath).slice(1);
      
      if (fileTypes.includes(fileExt)) {
        const matches = findMatchingLines(content, pattern, filePath);
        matches.forEach(match => {
          violations.push({
            ...match,
            description,
            pattern: pattern.source
          });
        });
      }
    });
    
    return violations;
    
  } catch (error) {
    console.warn(`Warning: Could not read file ${filePath}: ${error.message}`);
    return [];
  }
}

/**
 * Get all files to check
 */
function getFilesToCheck() {
  const files = [];
  
  SEARCH_PATTERNS.forEach(pattern => {
    const matchingFiles = glob.sync(pattern, { 
      cwd: process.cwd(),
      ignore: ['**/node_modules/**', '**/dist/**', '**/build/**']
    });
    files.push(...matchingFiles);
  });
  
  return [...new Set(files)]; // Remove duplicates
}

/**
 * Format violation report
 */
function formatViolations(violations) {
  if (violations.length === 0) {
    return '✅ No pointer-events overlay violations found';
  }
  
  let report = `${isCI ? '❌' : '⚠️'} Found ${violations.length} pointer-events overlay violation(s):\n\n`;
  
  // Group by file
  const byFile = violations.reduce((acc, violation) => {
    if (!acc[violation.filename]) {
      acc[violation.filename] = [];
    }
    acc[violation.filename].push(violation);
    return acc;
  }, {});
  
  Object.entries(byFile).forEach(([filename, fileViolations]) => {
    report += `📄 ${filename}:\n`;
    fileViolations.forEach(violation => {
      report += `   Line ${violation.line}: ${violation.description}\n`;
      report += `   Code: ${violation.content}\n`;
      report += `\n`;
    });
  });
  
  report += `\n💡 Fix suggestions:\n`;
  report += `   • Use 'pointer-events: none' for decorative header/drawer elements\n`;
  report += `   • Only allow 'pointer-events: auto' on interactive elements within headers/drawers\n`;
  report += `   • Consider using CSS classes like 'pointer-events-none' instead of inline styles\n`;
  report += `   • Test that user interactions are not blocked by overlays\n`;
  
  return report;
}

/**
 * Main execution
 */
function main() {
  console.log('🔍 Linting for pointer-events overlay violations...');
  
  const files = getFilesToCheck();
  console.log(`   Checking ${files.length} files...`);
  
  const allViolations = [];
  
  files.forEach(file => {
    const violations = checkFile(file);
    allViolations.push(...violations);
  });
  
  const report = formatViolations(allViolations);
  console.log(report);
  
  if (allViolations.length > 0) {
    if (isCI) {
      console.log('\n🚨 CI Mode: Treating overlay violations as errors');
      process.exit(1);
    } else {
      console.log('\n⚠️ Local Mode: Treating overlay violations as warnings');
      console.log('   Run in CI or set CI=true to treat as errors');
      process.exit(0);
    }
  } else {
    console.log('\n✅ No overlay violations found - safe to proceed');
    process.exit(0);
  }
}

// Handle command line execution
if (require.main === module) {
  main();
}

module.exports = {
  checkFile,
  getFilesToCheck,
  formatViolations,
  VIOLATION_PATTERNS
};