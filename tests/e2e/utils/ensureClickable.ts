/**
 * Ensure Clickable Helper
 * 
 * Verifies that an element is actually clickable before attempting to click it.
 * Fails fast with clear diagnostics if overlays are blocking the target element.
 */

import { Locator, Page } from '@playwright/test';

interface ClickabilityError extends Error {
  targetSelector: string;
  interceptingElement: {
    tagName: string;
    classes: string[];
    id: string;
    zIndex: string;
    position: string;
    visibility: string;
  };
  targetCoordinates: { x: number; y: number };
}

/**
 * Ensures an element is clickable by checking for overlaying elements
 * @param locator - Playwright locator for the target element
 * @param options - Optional configuration
 */
export async function ensureClickable(
  locator: Locator, 
  options: {
    timeout?: number;
    scrollIntoView?: boolean;
    allowChildInterception?: boolean;
  } = {}
): Promise<void> {
  const { 
    timeout = 5000, 
    scrollIntoView = true,
    allowChildInterception = true 
  } = options;

  const page = locator.page();
  
  // Wait for element to be visible first
  await locator.waitFor({ state: 'visible', timeout });
  
  // Scroll element into view if requested
  if (scrollIntoView) {
    await locator.scrollIntoViewIfNeeded();
    // Wait a moment for scroll animation to complete
    await page.waitForTimeout(200);
  }
  
  // Get element bounding box
  const boundingBox = await locator.boundingBox();
  if (!boundingBox) {
    throw new Error(`Target element has no bounding box - may not be visible`);
  }
  
  // Calculate center coordinates
  const centerX = boundingBox.x + boundingBox.width / 2;
  const centerY = boundingBox.y + boundingBox.height / 2;
  
  console.log(`🎯 Checking clickability at coordinates (${centerX.toFixed(1)}, ${centerY.toFixed(1)})`);
  
  // Get all elements at the center point
  const elementsAtPoint = await page.evaluate(({ x, y }) => {
    const elements = document.elementsFromPoint(x, y);
    return elements.map((el, index) => {
      const computedStyle = window.getComputedStyle(el);
      return {
        tagName: el.tagName,
        id: el.id || '',
        classes: Array.from(el.classList),
        zIndex: computedStyle.zIndex,
        position: computedStyle.position,
        visibility: computedStyle.visibility,
        display: computedStyle.display,
        pointerEvents: computedStyle.pointerEvents,
        opacity: computedStyle.opacity,
        isTopmost: index === 0,
        textContent: el.textContent?.slice(0, 50) || '',
        dataTestId: el.getAttribute('data-testid') || ''
      };
    });
  }, { x: centerX, y: centerY });
  
  if (elementsAtPoint.length === 0) {
    throw new Error(`No elements found at target coordinates (${centerX}, ${centerY})`);
  }
  
  // Get target element info for comparison
  const targetElement = await locator.evaluate((el) => {
    return {
      tagName: el.tagName,
      id: el.id || '',
      classes: Array.from(el.classList),
      dataTestId: el.getAttribute('data-testid') || '',
      textContent: el.textContent?.slice(0, 50) || ''
    };
  });
  
  const topmostElement = elementsAtPoint[0];
  
  console.log(`🔍 Target: ${targetElement.tagName}${targetElement.id ? '#' + targetElement.id : ''}${targetElement.dataTestId ? `[data-testid="${targetElement.dataTestId}"]` : ''}`);
  console.log(`🔍 Topmost: ${topmostElement.tagName}${topmostElement.id ? '#' + topmostElement.id : ''}${topmostElement.dataTestId ? `[data-testid="${topmostElement.dataTestId}"]` : ''}`);
  
  // Check if topmost element is the target or its child
  const isTargetOrChild = await page.evaluate(({ targetSelector, centerX, centerY }) => {
    const target = document.querySelector(targetSelector);
    const topmost = document.elementFromPoint(centerX, centerY);
    
    if (!target || !topmost) return false;
    
    // Check if topmost is the target itself
    if (topmost === target) return true;
    
    // Check if topmost is a child of target
    return target.contains(topmost);
  }, { 
    targetSelector: await getSelector(locator),
    centerX, 
    centerY 
  });
  
  // If target is directly clickable or child interception is allowed, we're good
  if (isTargetOrChild) {
    if (allowChildInterception || topmostElement.tagName === targetElement.tagName) {
      console.log('✅ Element is clickable');
      return;
    }
  }
  
  // Build diagnostic error message
  const diagnosticInfo = {
    target: {
      ...targetElement,
      coordinates: { x: centerX, y: centerY }
    },
    intercepting: topmostElement,
    allElementsAtPoint: elementsAtPoint.slice(0, 5), // Show top 5 elements
    recommendations: []
  };
  
  // Add specific recommendations based on intercepting element
  if (topmostElement.pointerEvents === 'none') {
    diagnosticInfo.recommendations.push('Intercepting element has pointer-events: none - this should allow clicks through');
  }
  
  if (topmostElement.zIndex !== 'auto' && parseInt(topmostElement.zIndex) > 0) {
    diagnosticInfo.recommendations.push(`Intercepting element has high z-index (${topmostElement.zIndex}) - consider reducing it`);
  }
  
  if (topmostElement.position === 'fixed' || topmostElement.position === 'absolute') {
    diagnosticInfo.recommendations.push(`Intercepting element is positioned (${topmostElement.position}) - may need better positioning`);
  }
  
  if (topmostElement.tagName === 'DIV' && topmostElement.classes.length === 0) {
    diagnosticInfo.recommendations.push('Intercepting element is an unstyled div - may be an unintended overlay');
  }
  
  // Create detailed error
  const error = new Error(`Element not clickable - intercepted by overlay element`) as ClickabilityError;
  error.targetSelector = await getSelector(locator);
  error.interceptingElement = {
    tagName: topmostElement.tagName,
    classes: topmostElement.classes,
    id: topmostElement.id,
    zIndex: topmostElement.zIndex,
    position: topmostElement.position,
    visibility: topmostElement.visibility
  };
  error.targetCoordinates = { x: centerX, y: centerY };
  
  // Enhanced error message
  let errorMessage = `❌ ELEMENT NOT CLICKABLE - OVERLAY DETECTED\n\n`;
  errorMessage += `🎯 Target Element:\n`;
  errorMessage += `   ${targetElement.tagName}${targetElement.id ? '#' + targetElement.id : ''}`;
  errorMessage += `${targetElement.dataTestId ? ` [data-testid="${targetElement.dataTestId}"]` : ''}\n`;
  errorMessage += `   Text: "${targetElement.textContent}"\n`;
  errorMessage += `   Coordinates: (${centerX.toFixed(1)}, ${centerY.toFixed(1)})\n\n`;
  
  errorMessage += `🚫 Intercepting Element:\n`;
  errorMessage += `   ${topmostElement.tagName}${topmostElement.id ? '#' + topmostElement.id : ''}`;
  errorMessage += `${topmostElement.classes.length > 0 ? `.${topmostElement.classes.join('.')}` : ''}\n`;
  errorMessage += `   Z-Index: ${topmostElement.zIndex}\n`;
  errorMessage += `   Position: ${topmostElement.position}\n`;
  errorMessage += `   Pointer Events: ${topmostElement.pointerEvents}\n`;
  errorMessage += `   Opacity: ${topmostElement.opacity}\n\n`;
  
  if (diagnosticInfo.recommendations.length > 0) {
    errorMessage += `💡 Suggested Fixes:\n`;
    diagnosticInfo.recommendations.forEach(rec => {
      errorMessage += `   • ${rec}\n`;
    });
    errorMessage += `\n`;
  }
  
  errorMessage += `📋 All Elements at Click Point:\n`;
  elementsAtPoint.slice(0, 5).forEach((el, i) => {
    errorMessage += `   ${i + 1}. ${el.tagName}${el.id ? '#' + el.id : ''}`;
    errorMessage += `${el.classes.length > 0 ? `.${el.classes.join('.')}` : ''}`;
    errorMessage += ` (z: ${el.zIndex})${el.isTopmost ? ' ← TOPMOST' : ''}\n`;
  });
  
  error.message = errorMessage;
  throw error;
}

/**
 * Ensures an element is clickable and then clicks it
 */
export async function clickWhenReady(
  locator: Locator, 
  options: {
    timeout?: number;
    force?: boolean;
    clickOptions?: Parameters<Locator['click']>[0];
  } = {}
): Promise<void> {
  const { timeout = 5000, force = false, clickOptions = {} } = options;
  
  if (!force) {
    await ensureClickable(locator, { timeout });
  }
  
  await locator.click(clickOptions);
  console.log('✅ Element clicked successfully');
}

/**
 * Helper to get a reasonable selector for an element
 */
async function getSelector(locator: Locator): Promise<string> {
  try {
    // Try to get data-testid first
    const testId = await locator.getAttribute('data-testid');
    if (testId) {
      return `[data-testid="${testId}"]`;
    }
    
    // Fall back to id
    const id = await locator.getAttribute('id');
    if (id) {
      return `#${id}`;
    }
    
    // Fall back to tag name with classes
    const tagName = await locator.evaluate(el => el.tagName.toLowerCase());
    const classes = await locator.getAttribute('class');
    if (classes) {
      return `${tagName}.${classes.split(' ').join('.')}`;
    }
    
    return tagName;
  } catch {
    return 'unknown-element';
  }
}

/**
 * Utility to take a screenshot with overlay diagnostic information
 */
export async function screenshotWithOverlayDiag(
  page: Page,
  locator: Locator,
  filename: string
): Promise<void> {
  // Add diagnostic overlay to the page
  await page.evaluate(() => {
    // Remove existing diagnostic overlays
    document.querySelectorAll('.clickability-diagnostic').forEach(el => el.remove());
  });
  
  const boundingBox = await locator.boundingBox();
  if (boundingBox) {
    await page.evaluate(({ x, y, width, height }) => {
      const overlay = document.createElement('div');
      overlay.className = 'clickability-diagnostic';
      overlay.style.cssText = `
        position: fixed;
        left: ${x}px;
        top: ${y}px;
        width: ${width}px;
        height: ${height}px;
        border: 3px solid red;
        background: rgba(255, 0, 0, 0.1);
        pointer-events: none;
        z-index: 10000;
        font-size: 12px;
        color: red;
        font-weight: bold;
      `;
      overlay.textContent = 'TARGET';
      document.body.appendChild(overlay);
      
      // Add center point marker
      const center = document.createElement('div');
      center.className = 'clickability-diagnostic';
      center.style.cssText = `
        position: fixed;
        left: ${x + width/2 - 5}px;
        top: ${y + height/2 - 5}px;
        width: 10px;
        height: 10px;
        background: red;
        border-radius: 50%;
        pointer-events: none;
        z-index: 10001;
      `;
      document.body.appendChild(center);
    }, boundingBox);
  }
  
  await page.screenshot({ path: filename, fullPage: true });
  
  // Clean up diagnostic overlays
  await page.evaluate(() => {
    document.querySelectorAll('.clickability-diagnostic').forEach(el => el.remove());
  });
}