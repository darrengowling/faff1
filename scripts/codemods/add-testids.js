#!/usr/bin/env node

/**
 * JSCodeshift Codemod: Add data-testid attributes to known components
 * 
 * Maps known selectors and patterns to testid keys from the registry
 * and adds data-testid={TESTIDS.<key>} attributes if missing.
 * 
 * Usage: npx jscodeshift -t scripts/codemods/add-testids.js frontend/src/components/** frontend/src/pages/**
 */

function transformer(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);
  let hasChanges = false;

  console.log(`Processing: ${fileInfo.path}`);

  // Patterns to match specific elements and their corresponding testids
  const patterns = [
    // Auth patterns
    {
      testid: 'authEmailInput',
      match: (node) => {
        return node.name && node.name.name === 'input' && 
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'type' && 
                 attr.value && attr.value.value === 'email'
               );
      }
    },
    {
      testid: 'authSubmitBtn',
      match: (node) => {
        return node.name && (node.name.name === 'button' || node.name.name === 'Button') &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'type' && 
                 attr.value && attr.value.value === 'submit'
               );
      }
    },
    
    // Section patterns
    {
      testid: 'sectionHome',
      match: (node) => {
        return node.name && node.name.name === 'section' &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'id' && 
                 attr.value && attr.value.value === 'home'
               );
      }
    },
    {
      testid: 'sectionHow',
      match: (node) => {
        return node.name && node.name.name === 'section' &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'id' && 
                 attr.value && attr.value.value === 'how'
               );
      }
    },
    {
      testid: 'sectionWhy',
      match: (node) => {
        return node.name && node.name.name === 'section' &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'id' && 
                 attr.value && attr.value.value === 'why'
               );
      }
    },
    {
      testid: 'sectionFeatures',
      match: (node) => {
        return node.name && node.name.name === 'section' &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'id' && 
                 attr.value && attr.value.value === 'features'
               );
      }
    },
    {
      testid: 'sectionSafety',
      match: (node) => {
        return node.name && node.name.name === 'section' &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'id' && 
                 attr.value && attr.value.value === 'safety'
               );
      }
    },
    {
      testid: 'sectionFaq',
      match: (node) => {
        return node.name && node.name.name === 'section' &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'id' && 
                 attr.value && attr.value.value === 'faq'
               );
      }
    },

    // Navigation patterns
    {
      testid: 'navHamburger',
      match: (node) => {
        return node.name && node.name.name === 'button' &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'aria-label' &&
                 attr.value && attr.value.value && /menu/i.test(attr.value.value)
               );
      }
    },

    // Mobile drawer pattern
    {
      testid: 'mobileDrawer',
      match: (node) => {
        return node.name && node.name.name === 'div' &&
               node.attributes && node.attributes.some(attr => 
                 attr.name && attr.name.name === 'id' && 
                 attr.value && attr.value.value === 'mobile-navigation'
               );
      }
    }
  ];

  // Check imports and add TESTIDS import if missing and changes are made
  function ensureTestidsImport() {
    let hasTestidsImport = false;
    
    root.find(j.ImportDeclaration).forEach(path => {
      const source = path.value.source.value;
      if (source && (source.includes('testids') || source.includes('testing/testids'))) {
        hasTestidsImport = true;
      }
    });

    if (!hasTestidsImport && hasChanges) {
      const imports = root.find(j.ImportDeclaration);
      if (imports.length > 0) {
        // Determine relative path based on file location
        const isInComponents = fileInfo.path.includes('/components/');
        const isInPages = fileInfo.path.includes('/pages/');
        const depth = (fileInfo.path.match(/components\/.*?\//g) || []).length;
        
        let relativePath = '../testing/testids.ts';
        if (depth > 1) {
          relativePath = '../../testing/testids.ts';
        }
        if (isInPages) {
          relativePath = '../testing/testids.ts';
        }
        
        const testidsImport = j.importDeclaration(
          [j.importSpecifier(j.identifier('TESTIDS'))],
          j.literal(relativePath)
        );
        
        imports.at(0).insertAfter(testidsImport);
        console.log(`  📦 Added TESTIDS import`);
      }
    }
  }

  // Apply patterns to JSX elements
  root.find(j.JSXElement).forEach(path => {
    const node = path.value.openingElement;
    
    if (!node || !node.name) return;
    
    // Skip if already has data-testid
    const hasTestId = node.attributes && node.attributes.some(attr => 
      attr.name && attr.name.name === 'data-testid'
    );
    
    if (hasTestId) return;

    // Check each pattern
    for (const pattern of patterns) {
      try {
        if (pattern.match(node)) {
          const testidAttr = j.jsxAttribute(
            j.jsxIdentifier('data-testid'),
            j.jsxExpressionContainer(
              j.memberExpression(
                j.identifier('TESTIDS'),
                j.identifier(pattern.testid)
              )
            )
          );
          
          if (!node.attributes) node.attributes = [];
          node.attributes.push(testidAttr);
          hasChanges = true;
          console.log(`  ✅ Added ${pattern.testid} to ${node.name.name}`);
          break; // Only add one testid per element
        }
      } catch (error) {
        console.error(`Error processing pattern ${pattern.testid}:`, error.message);
      }
    }
  });

  // Add import if changes were made
  if (hasChanges) {
    ensureTestidsImport();
  }

  return hasChanges ? root.toSource({ quote: 'single', reuseParsers: true }) : null;
}

module.exports = transformer;
module.exports.parser = 'tsx';