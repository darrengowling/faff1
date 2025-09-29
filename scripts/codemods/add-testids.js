#!/usr/bin/env node

/**
 * JSCodeshift Codemod: Add data-testid attributes to known components
 * 
 * Maps known selectors and patterns to testid keys from the registry
 * and adds data-testid={TESTIDS.<key>} attributes if missing.
 * 
 * Usage: npx jscodeshift -t scripts/codemods/add-testids.js frontend/src/components/** frontend/src/pages/**
 */

const { execSync } = require('child_process');
const path = require('path');

// Import testids mapping (we'll read this dynamically)
const TESTIDS_MAPPING = {
  // Auth components
  authEmailInput: { selector: 'input', attributes: { id: 'email', type: 'email' } },
  authSubmitBtn: { selector: 'button', attributes: { type: 'submit' }, textContent: /send.*magic.*link|submit/i },
  loginHeader: { selector: 'h1,h2,h3', textContent: /sign.*in|login/i },
  backToHome: { selector: 'a,Link', attributes: { href: '/' }, textContent: /back.*home|home/i },
  
  // Landing page sections
  sectionHome: { selector: 'section', attributes: { id: 'home' } },
  sectionHow: { selector: 'section', attributes: { id: 'how' } },
  sectionWhy: { selector: 'section', attributes: { id: 'why' } },
  sectionFeatures: { selector: 'section', attributes: { id: 'features' } },
  sectionSafety: { selector: 'section', attributes: { id: 'safety' } },
  sectionFaq: { selector: 'section', attributes: { id: 'faq' } },
  
  // CTA buttons
  landingCtaCreate: { selector: 'button,Button', textContent: /create.*league/i },
  landingCtaJoin: { selector: 'button,Button', textContent: /join.*invite/i },
  
  // Navigation elements
  navHamburger: { selector: 'button', className: /hamburger|menu-toggle|mobile-menu/i, children: ['Menu', 'X'] },
  navBrand: { selector: 'a,Link', className: /brand|logo/i },
  navSignIn: { selector: 'button,a,Link', textContent: /sign.*in/i },
  
  // Create league form
  createName: { selector: 'input', attributes: { name: 'name', type: 'text' } },
  createSlots: { selector: 'input', attributes: { name: 'slots', type: 'number' } },
  createBudget: { selector: 'input', attributes: { name: 'budget', type: 'number' } },
  createSubmit: { selector: 'button', attributes: { type: 'submit' }, textContent: /create|submit/i },
  
  // Lobby components
  lobbyJoined: { selector: 'div', textContent: /\d+\/\d+|joined|members/i },
  startAuction: { selector: 'button,Button', textContent: /start.*auction/i },
  rulesBadge: { selector: 'div,span', className: /rules|badge/i },
  
  // Auction components
  auctionAsset: { selector: 'h1,h2,h3', className: /title|asset|club/i },
  auctionTimer: { selector: 'div', className: /timer|countdown/i },
  auctionTopBid: { selector: 'div', className: /bid|price/i, textContent: /\$|\d+.*credit/i },
  
  // Roster components
  rosterList: { selector: 'div', className: /roster|list|grid/i },
  rosterItem: { selector: 'div,li', className: /item|card|club/i },
  rosterEmpty: { selector: 'div', textContent: /no.*club|empty/i },
  
  // Admin components
  adminPanel: { selector: 'div', className: /admin|panel|tabs/i }
};

// Helper function to check if element matches selector criteria
function matchesSelector(node, mapping) {
  const { selector, attributes = {}, className, textContent, children } = mapping;
  
  // Check if node type matches selector
  const elementTypes = selector.split(',').map(s => s.trim());
  if (!elementTypes.includes(node.name.name)) {
    return false;
  }
  
  // Check attributes
  for (const [attr, value] of Object.entries(attributes)) {
    const attrNode = node.attributes.find(a => a.name && a.name.name === attr);
    if (!attrNode) return false;
    
    if (typeof value === 'string') {
      const attrValue = attrNode.value.value || attrNode.value.expression?.value;
      if (attrValue !== value) return false;
    }
  }
  
  // Check className (simplified check)
  if (className) {
    const classAttr = node.attributes.find(a => a.name && a.name.name === 'className');
    if (!classAttr) return false;
    // This is a simplified check - in practice we'd need to parse className values
  }
  
  return true;
}

// Main transform function
function transformer(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);
  let hasChanges = false;

  // First, ensure TESTIDS import exists
  const testidsImportPath = '../testing/testids.ts';
  let hasTestidsImport = false;
  
  root.find(j.ImportDeclaration).forEach(path => {
    if (path.value.source.value.includes('testids')) {
      hasTestidsImport = true;
    }
  });

  // Add TESTIDS import if missing
  if (!hasTestidsImport) {
    const firstImport = root.find(j.ImportDeclaration).at(0);
    if (firstImport.length > 0) {
      const testidsImport = j.importDeclaration(
        [j.importSpecifier(j.identifier('TESTIDS'))],
        j.literal(testidsImportPath)
      );
      firstImport.insertBefore(testidsImport);
      hasChanges = true;
    }
  }

  // Process each JSX element
  root.find(j.JSXElement).forEach(path => {
    const node = path.value.openingElement;
    
    // Skip if data-testid already exists
    const hasTestId = node.attributes.some(attr => 
      attr.name && attr.name.name === 'data-testid'
    );
    
    if (hasTestId) return;
    
    // Check against each mapping
    for (const [testidKey, mapping] of Object.entries(TESTIDS_MAPPING)) {
      if (matchesSelector(node, mapping)) {
        // Add data-testid attribute
        const testidAttr = j.jsxAttribute(
          j.jsxIdentifier('data-testid'),
          j.jsxExpressionContainer(
            j.memberExpression(
              j.identifier('TESTIDS'),
              j.identifier(testidKey)
            )
          )
        );
        
        node.attributes.push(testidAttr);
        hasChanges = true;
        console.log(`Added ${testidKey} testid to ${node.name.name} in ${fileInfo.path}`);
        break; // Only add one testid per element
      }
    }
  });

  return hasChanges ? root.toSource({ quote: 'single' }) : null;
}

// Enhanced selector matching with more sophisticated patterns
function createAdvancedTransformer() {
  return function(fileInfo, api) {
    const j = api.jscodeshift;
    const root = j(fileInfo.source);
    let hasChanges = false;

    // Specific patterns for different components
    const patterns = [
      // Auth patterns
      {
        testid: 'authEmailInput',
        match: (node) => {
          return node.name.name === 'input' && 
                 node.attributes.some(attr => 
                   attr.name.name === 'type' && attr.value.value === 'email'
                 );
        }
      },
      {
        testid: 'authSubmitBtn',
        match: (node) => {
          return (node.name.name === 'button' || node.name.name === 'Button') &&
                 node.attributes.some(attr => 
                   attr.name.name === 'type' && attr.value.value === 'submit'
                 );
        }
      },
      
      // Section patterns
      {
        testid: 'sectionHome',
        match: (node) => {
          return node.name.name === 'section' &&
                 node.attributes.some(attr => 
                   attr.name.name === 'id' && attr.value.value === 'home'
                 );
        }
      },
      {
        testid: 'sectionHow',
        match: (node) => {
          return node.name.name === 'section' &&
                 node.attributes.some(attr => 
                   attr.name.name === 'id' && attr.value.value === 'how'
                 );
        }
      },
      {
        testid: 'sectionWhy',
        match: (node) => {
          return node.name.name === 'section' &&
                 node.attributes.some(attr => 
                   attr.name.name === 'id' && attr.value.value === 'why'
                 );
        }
      },
      {
        testid: 'sectionFeatures',
        match: (node) => {
          return node.name.name === 'section' &&
                 node.attributes.some(attr => 
                   attr.name.name === 'id' && attr.value.value === 'features'
                 );
        }
      },
      {
        testid: 'sectionSafety',
        match: (node) => {
          return node.name.name === 'section' &&
                 node.attributes.some(attr => 
                   attr.name.name === 'id' && attr.value.value === 'safety'
                 );
        }
      },
      {
        testid: 'sectionFaq',
        match: (node) => {
          return node.name.name === 'section' &&
                 node.attributes.some(attr => 
                   attr.name.name === 'id' && attr.value.value === 'faq'
                 );
        }
      },

      // CTA button patterns (match by onClick handlers or text content)
      {
        testid: 'landingCtaCreate',
        match: (node, parent) => {
          if (node.name.name !== 'button' && node.name.name !== 'Button') return false;
          
          // Check if parent JSX element contains text about creating league
          const hasCreateText = parent && parent.children && 
            parent.children.some(child => 
              child.type === 'JSXText' && /create.*league/i.test(child.value)
            );
          
          // Or check onClick handler for navigation to create
          const hasCreateAction = node.attributes.some(attr =>
            attr.name.name === 'onClick' && 
            attr.value && 
            attr.value.expression &&
            /create|new.*league/i.test(attr.value.expression.toString())
          );
          
          return hasCreateText || hasCreateAction;
        }
      },
      {
        testid: 'landingCtaJoin',
        match: (node, parent) => {
          if (node.name.name !== 'button' && node.name.name !== 'Button') return false;
          
          const hasJoinText = parent && parent.children && 
            parent.children.some(child => 
              child.type === 'JSXText' && /join.*invite/i.test(child.value)
            );
          
          return hasJoinText;
        }
      },

      // Mobile navigation patterns
      {
        testid: 'navHamburger',
        match: (node) => {
          return node.name.name === 'button' &&
                 (node.attributes.some(attr => 
                   attr.name.name === 'className' && 
                   /hamburger|menu.*toggle/i.test(attr.value.value)
                 ) ||
                 node.attributes.some(attr =>
                   attr.name.name === 'aria-label' &&
                   /menu|hamburger/i.test(attr.value.value)
                 ));
        }
      }
    ];

    // Check imports and add TESTIDS import if missing
    let hasTestidsImport = false;
    root.find(j.ImportDeclaration).forEach(path => {
      const source = path.value.source.value;
      if (source.includes('testids') || source.includes('testing/testids')) {
        hasTestidsImport = true;
      }
    });

    if (!hasTestidsImport) {
      const imports = root.find(j.ImportDeclaration);
      if (imports.length > 0) {
        const relativePath = fileInfo.path.includes('/components/') ? 
          '../testing/testids.ts' : 
          '../../testing/testids.ts';
        
        const testidsImport = j.importDeclaration(
          [j.importSpecifier(j.identifier('TESTIDS'))],
          j.literal(relativePath)
        );
        
        imports.at(0).insertAfter(testidsImport);
        hasChanges = true;
      }
    }

    // Apply patterns to JSX elements
    root.find(j.JSXElement).forEach(path => {
      const node = path.value.openingElement;
      
      // Skip if already has data-testid
      const hasTestId = node.attributes.some(attr => 
        attr.name && attr.name.name === 'data-testid'
      );
      
      if (hasTestId) return;

      // Check each pattern
      for (const pattern of patterns) {
        if (pattern.match(node, path.value)) {
          const testidAttr = j.jsxAttribute(
            j.jsxIdentifier('data-testid'),
            j.jsxExpressionContainer(
              j.memberExpression(
                j.identifier('TESTIDS'),
                j.identifier(pattern.testid)
              )
            )
          );
          
          node.attributes.push(testidAttr);
          hasChanges = true;
          console.log(`✅ Added ${pattern.testid} to ${node.name.name} in ${fileInfo.path}`);
          break;
        }
      }
    });

    return hasChanges ? root.toSource({ quote: 'single' }) : null;
  };
}

module.exports = createAdvancedTransformer();
module.exports.parser = 'tsx';