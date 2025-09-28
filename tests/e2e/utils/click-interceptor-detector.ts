/**
 * Playwright Utility: Click Interceptor Detector
 * 
 * Detects UI elements that intercept clicks and provides detailed debugging information
 * about z-index, positioning, and which elements are blocking interactions.
 */

import { Page, Locator } from '@playwright/test';

interface InterceptionDetails {
  targetElement: string;
  interceptingElements: Array<{
    selector: string;
    tagName: string;
    zIndex: string;
    position: string;
    pointerEvents: string;
    opacity: string;
    visibility: string;
  }>;
  clickCoordinates: { x: number; y: number };
}

/**
 * Checks if an element can be clicked without interception
 * Throws detailed error if click would be intercepted
 */
export async function ensureClickable(page: Page, locator: Locator): Promise<void> {
  // Get the target element's bounding box
  const boundingBox = await locator.boundingBox();
  if (!boundingBox) {
    throw new Error('Target element not found or has no bounding box');
  }

  // Calculate center point for click
  const clickX = boundingBox.x + boundingBox.width / 2;
  const clickY = boundingBox.y + boundingBox.height / 2;

  // Check elements at click point using elementsFromPoint
  const interceptionDetails = await page.evaluate(({ x, y }) => {
    const elementsAtPoint = document.elementsFromPoint(x, y);
    
    if (elementsAtPoint.length === 0) {
      return { intercepted: false, elements: [] };
    }

    // Get detailed info about each element at the click point
    const elementDetails = elementsAtPoint.map((element, index) => {
      const computedStyle = window.getComputedStyle(element);
      
      // Generate a more specific selector
      let selector = element.tagName.toLowerCase();
      if (element.id) {
        selector += `#${element.id}`;
      }
      if (element.className && typeof element.className === 'string') {
        const classes = element.className.split(' ').filter(c => c.trim()).slice(0, 3);
        if (classes.length > 0) {
          selector += '.' + classes.join('.');
        }
      }
      if (element.hasAttribute('data-testid')) {
        selector += `[data-testid="${element.getAttribute('data-testid')}"]`;
      }

      return {
        index,
        selector,
        tagName: element.tagName,
        zIndex: computedStyle.zIndex,
        position: computedStyle.position,
        pointerEvents: computedStyle.pointerEvents,
        opacity: computedStyle.opacity,
        visibility: computedStyle.visibility,
        display: computedStyle.display,
        isVisible: element.offsetParent !== null,
        hasDataOverlay: element.hasAttribute('data-overlay'),
        hasPointerEventsNone: computedStyle.pointerEvents === 'none'
      };
    });

    return {
      intercepted: elementsAtPoint.length > 1,
      elements: elementDetails,
      topElement: elementDetails[0]
    };
  }, { x: clickX, y: clickY });

  // Check if target element is the topmost clickable element
  const targetSelector = await locator.getAttribute('data-testid').then(testid => 
    testid ? `[data-testid="${testid}"]` : null
  ).catch(() => null);

  if (interceptionDetails.intercepted) {
    const topElement = interceptionDetails.elements[0];
    
    // Check if the top element is the target (good)
    const isTargetOnTop = targetSelector && topElement.selector.includes(targetSelector);
    
    // Check if top element has pointer-events: none (should allow click through)
    const hasPointerEventsNone = topElement.hasPointerEventsNone;
    
    // If target is not on top and intercepting element doesn't have pointer-events: none
    if (!isTargetOnTop && !hasPointerEventsNone) {
      const interceptingInfo: InterceptionDetails = {
        targetElement: targetSelector || 'unknown',
        interceptingElements: interceptionDetails.elements.slice(0, 3), // Top 3 elements
        clickCoordinates: { x: clickX, y: clickY }
      };

      const errorMessage = `
🚫 CLICK INTERCEPTED at coordinates (${clickX}, ${clickY})

🎯 Target Element: ${interceptingInfo.targetElement}

🔴 Intercepting Elements:
${interceptingInfo.interceptingElements.map((el, i) => `
  ${i + 1}. ${el.selector}
     • Tag: ${el.tagName}
     • Z-Index: ${el.zIndex}
     • Position: ${el.position}
     • Pointer Events: ${el.pointerEvents}
     • Opacity: ${el.opacity}
     • Visibility: ${el.visibility}
     • Has data-overlay: ${el.hasDataOverlay || false}
`).join('')}

💡 Solutions:
- Add 'pointer-events: none' to intercepting elements
- Add '[data-overlay]' attribute to overlay elements
- Adjust z-index stacking order
- Check CSS header rules: 'header *[data-overlay] { pointer-events: none }'
`;

      throw new Error(errorMessage);
    }
  }

  // If we get here, the element should be clickable
  console.log(`✅ Element is clickable at (${clickX}, ${clickY})`);
}

/**
 * Safe click that checks for interception first
 */
export async function safeClick(page: Page, locator: Locator, options?: { force?: boolean; timeout?: number }): Promise<void> {
  try {
    // Skip interception check if force is true
    if (!options?.force) {
      await ensureClickable(page, locator);
    }
    
    // Proceed with click
    await locator.click({ timeout: options?.timeout });
    console.log('✅ Safe click completed successfully');
    
  } catch (error) {
    console.error('❌ Safe click failed:', error.message);
    
    // Take screenshot for debugging
    await page.screenshot({ 
      path: `click-interception-debug-${Date.now()}.png`, 
      quality: 20,
      fullPage: false 
    });
    
    throw error;
  }
}

/**
 * Get detailed information about all elements at a specific point
 */
export async function analyzeClickPoint(page: Page, x: number, y: number): Promise<any> {
  return await page.evaluate(({ x, y }) => {
    const elementsAtPoint = document.elementsFromPoint(x, y);
    
    return elementsAtPoint.map((element, index) => {
      const computedStyle = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      
      return {
        index,
        tagName: element.tagName,
        id: element.id,
        className: element.className,
        dataTestId: element.getAttribute('data-testid'),
        zIndex: computedStyle.zIndex,
        position: computedStyle.position,
        pointerEvents: computedStyle.pointerEvents,
        opacity: computedStyle.opacity,
        visibility: computedStyle.visibility,
        display: computedStyle.display,
        dimensions: {
          width: rect.width,
          height: rect.height,
          x: rect.x,
          y: rect.y
        },
        isVisible: element.offsetParent !== null,
        hasDataOverlay: element.hasAttribute('data-overlay'),
        innerHTML: element.innerHTML.substring(0, 100) + (element.innerHTML.length > 100 ? '...' : '')
      };
    });
  }, { x, y });
}