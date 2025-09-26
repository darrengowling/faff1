/**
 * ESLint Rule: no-window-at-module-scope
 * 
 * Prevents usage of window, document, or other browser globals at module scope
 * to ensure SSR compatibility and prevent runtime crashes in server environments.
 * 
 * @fileoverview Rule to prevent module-scope browser API usage
 * @author Friends of PIFA Development Team
 */

export default {
  meta: {
    type: "problem",
    docs: {
      description: "disallow window, document, and other browser globals at module scope",
      category: "SSR Safety",
      recommended: true,
    },
    fixable: null,
    schema: [
      {
        type: "object",
        properties: {
          allowedGlobals: {
            type: "array",
            items: {
              type: "string"
            }
          }
        },
        additionalProperties: false
      }
    ],
    messages: {
      moduleScope: "{{name}} should not be used at module scope. Use inside functions, React components, or useEffect hooks for SSR compatibility.",
      suggestion: "Consider moving this code inside a component, useEffect, or using a safe browser detection utility."
    }
  },

  create(context) {
    // Browser globals that should not be used at module scope
    const defaultForbiddenGlobals = [
      'window',
      'document',
      'navigator',
      'location',
      'history',
      'localStorage',
      'sessionStorage',
      'screen',
      'performance'
    ];

    const options = context.options[0] || {};
    const allowedGlobals = options.allowedGlobals || [];
    const forbiddenGlobals = defaultForbiddenGlobals.filter(
      global => !allowedGlobals.includes(global)
    );

    // Track scope depth to determine if we're at module scope
    let scopeDepth = 0;
    let functionDepth = 0;

    return {
      Program() {
        scopeDepth = 0;
        functionDepth = 0;
      },

      // Track entering function/class scopes
      "FunctionDeclaration"() {
        functionDepth++;
      },
      "FunctionExpression"() {
        functionDepth++;
      },
      "ArrowFunctionExpression"() {
        functionDepth++;
      },

      // Track exiting function/class scopes
      "FunctionDeclaration:exit"() {
        functionDepth--;
      },
      "FunctionExpression:exit"() {
        functionDepth--;
      },
      "ArrowFunctionExpression:exit"() {
        functionDepth--;
      },

      // Track entering block scopes
      "BlockStatement"() {
        scopeDepth++;
      },
      "ClassBody"() {
        scopeDepth++;
      },

      // Track exiting block scopes
      "BlockStatement:exit"() {
        scopeDepth--;
      },
      "ClassBody:exit"() {
        scopeDepth--;
      },

      // Check identifier usage
      Identifier(node) {
        // Skip if we're inside a function or class method
        if (functionDepth > 0) {
          return;
        }

        // Skip if this identifier is not a forbidden global
        if (!forbiddenGlobals.includes(node.name)) {
          return;
        }

        // Skip if this is a property name (e.g., obj.window)
        if (node.parent.type === 'MemberExpression' && node.parent.property === node) {
          return;
        }

        // Skip if this is in a typeof check (allowed pattern)
        if (node.parent.type === 'UnaryExpression' && node.parent.operator === 'typeof') {
          return;
        }

        // Skip if this is a string literal (e.g., 'window')
        if (node.parent.type === 'Literal') {
          return;
        }

        // Skip if this is in an object key
        if (node.parent.type === 'Property' && node.parent.key === node) {
          return;
        }

        // Skip if this is in a function/variable name
        if (
          (node.parent.type === 'FunctionDeclaration' && node.parent.id === node) ||
          (node.parent.type === 'VariableDeclarator' && node.parent.id === node)
        ) {
          return;
        }

        // This is a forbidden global usage at module scope
        context.report({
          node: node,
          messageId: "moduleScope",
          data: {
            name: node.name
          },
          suggest: [
            {
              desc: "Move this code inside a function or React component"
            }
          ]
        });
      },

      // Special handling for member expressions (e.g., window.location)
      MemberExpression(node) {
        // Skip if we're inside a function
        if (functionDepth > 0) {
          return;
        }

        // Check if the object is a forbidden global
        if (
          node.object.type === 'Identifier' &&
          forbiddenGlobals.includes(node.object.name)
        ) {
          // Skip typeof checks
          if (node.parent.type === 'UnaryExpression' && node.parent.operator === 'typeof') {
            return;
          }

          context.report({
            node: node.object,
            messageId: "moduleScope",
            data: {
              name: node.object.name
            }
          });
        }
      }
    };
  },
};