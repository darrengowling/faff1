#!/usr/bin/env node

/**
 * Link and Navigation Linter
 * 
 * Scans for placeholder links and empty navigation arrays that indicate incomplete implementation.
 * Fails CI fast to prevent placeholder content from reaching production.
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Patterns to detect
const PATTERNS = [
  {
    name: 'Placeholder href',
    regex: /href\s*=\s*["']#["']/gi,
    description: 'Found placeholder href="#" link'
  },
  {
    name: 'Empty navigation array',
    regex: /const\s+(navigation|dropdown|menu)Items?\s*=\s*\[\s*\]/gi,
    description: 'Found empty navigation/dropdown array constant'
  },
  {
    name: 'TODO navigation',
    regex: /href\s*=\s*["']\/TODO["']/gi,
    description: 'Found TODO placeholder link'
  },
  {
    name: 'Disabled navigation comment',
    regex: /\/\*\s*(TODO|FIXME).*navigation.*\*\//gi,
    description: 'Found disabled navigation comment'
  }
];

// File patterns to scan (relative to project root)
const getScanPatterns = () => {
  // Check if we're in the frontend directory or root
  const isInFrontend = process.cwd().includes('/frontend');
  
  if (isInFrontend) {
    return [
      'src/**/*.{js,jsx,ts,tsx}',
      'public/**/*.html'
    ];
  } else {
    return [
      'frontend/src/**/*.{js,jsx,ts,tsx}',
      'frontend/public/**/*.html'
    ];
  }
};

// Files to exclude
const EXCLUDE_PATTERNS = [
  '**/node_modules/**',
  '**/build/**',
  '**/dist/**',
  '**/*.test.{js,jsx,ts,tsx}',
  '**/*.spec.{js,jsx,ts,tsx}',
  '**/test-results/**'
];

class LinkLinter {
  constructor() {
    this.issues = [];
    this.fileCount = 0;
  }

  async run() {
    console.log('🔍 Link Linter: Scanning for placeholder links and empty navigation arrays...\n');

    // Get all files to scan
    const files = await this.getFilesToScan();
    console.log(`📁 Scanning ${files.length} files...\n`);

    // Scan each file
    for (const file of files) {
      this.scanFile(file);
    }

    // Report results
    this.reportResults();

    // Exit with appropriate code
    process.exit(this.issues.length > 0 ? 1 : 0);
  }

  async getFilesToScan() {
    const allFiles = [];

    for (const pattern of SCAN_PATTERNS) {
      const files = glob.sync(pattern, {
        ignore: EXCLUDE_PATTERNS,
        cwd: process.cwd()
      });
      allFiles.push(...files);
    }

    // Remove duplicates and sort
    return [...new Set(allFiles)].sort();
  }

  scanFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');

      for (const pattern of PATTERNS) {
        this.scanForPattern(filePath, lines, pattern);
      }

      this.fileCount++;
    } catch (error) {
      console.warn(`⚠️  Warning: Could not read file ${filePath}: ${error.message}`);
    }
  }

  scanForPattern(filePath, lines, pattern) {
    lines.forEach((line, lineIndex) => {
      pattern.regex.lastIndex = 0; // Reset regex state
      const matches = [...line.matchAll(pattern.regex)];

      matches.forEach(match => {
        this.issues.push({
          file: filePath,
          line: lineIndex + 1,
          column: match.index + 1,
          pattern: pattern.name,
          description: pattern.description,
          content: line.trim(),
          match: match[0]
        });
      });
    });
  }

  reportResults() {
    console.log(`📊 Scan completed: ${this.fileCount} files processed\n`);

    if (this.issues.length === 0) {
      console.log('✅ No placeholder links or empty navigation arrays found!');
      console.log('🚀 All navigation appears to be properly implemented.\n');
      return;
    }

    console.log(`❌ Found ${this.issues.length} placeholder/navigation issue(s):\n`);

    // Group issues by type
    const groupedIssues = this.groupIssuesByPattern();

    for (const [patternName, issues] of Object.entries(groupedIssues)) {
      console.log(`🔴 ${patternName} (${issues.length} occurrence(s)):`);
      
      issues.forEach(issue => {
        console.log(`   ${issue.file}:${issue.line}:${issue.column}`);
        console.log(`   └─ ${issue.description}`);
        console.log(`   └─ Code: ${issue.content}`);
        console.log(`   └─ Match: "${issue.match}"`);
        console.log('');
      });
    }

    console.log('💡 How to fix:');
    console.log('   • Replace href="#" with proper URLs or onClick handlers');
    console.log('   • Populate empty navigation arrays with actual menu items');
    console.log('   • Remove TODO placeholders and implement proper navigation');
    console.log('   • Ensure all links have meaningful destinations\n');

    console.log('🚨 CI FAILURE: Placeholder content detected!');
    console.log('   Please fix the above issues before merging.\n');
  }

  groupIssuesByPattern() {
    const grouped = {};
    
    this.issues.forEach(issue => {
      if (!grouped[issue.pattern]) {
        grouped[issue.pattern] = [];
      }
      grouped[issue.pattern].push(issue);
    });

    return grouped;
  }
}

// Run the linter
const linter = new LinkLinter();
linter.run().catch(error => {
  console.error('💥 Link linter crashed:', error);
  process.exit(1);
});