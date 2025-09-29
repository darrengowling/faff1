/**
 * Mobile Navigation Test Helpers
 * 
 * Provides utilities for stable mobile navigation testing
 */

/**
 * Ensures an element is clickable by checking elementsFromPoint
 * Prevents flaky tests caused by elements being obscured or not interactive
 */
export const ensureClickable = async (page, locator) => {
  // Wait for element to be attached and visible
  await locator.waitFor({ state: 'attached' });
  await locator.waitFor({ state: 'visible' });
  
  // Get element bounding box
  const box = await locator.boundingBox();
  if (!box) {
    throw new Error('Element has no bounding box - not clickable');
  }
  
  // Calculate center point
  const centerX = box.x + box.width / 2;
  const centerY = box.y + box.height / 2;
  
  // Check if element is at the center point (not obscured)
  const elementAtPoint = await page.evaluate((x, y) => {
    const elements = document.elementsFromPoint(x, y);
    return elements.length > 0;
  }, centerX, centerY);
  
  if (!elementAtPoint) {
    throw new Error(`No element found at point (${centerX}, ${centerY}) - element may be obscured`);
  }
  
  // Scroll element into view if needed
  await locator.scrollIntoViewIfNeeded();
  
  console.log(`✅ Element is clickable at (${centerX}, ${centerY})`);
  return true;
};

/**
 * Get mobile drawer count as number
 */
export const getMobileDrawerCount = async (drawer) => {
  const countAttr = await drawer.getAttribute('data-count');
  return Number(countAttr || 0);
};

/**
 * Wait for drawer state change with timeout
 */
export const waitForDrawerState = async (drawer, expectedState, timeout = 2000) => {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const currentState = await drawer.getAttribute('data-state');
    if (currentState === expectedState) {
      return true;
    }
    
    // Wait 50ms before checking again
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  
  const actualState = await drawer.getAttribute('data-state');
  throw new Error(`Drawer state timeout: expected "${expectedState}", got "${actualState}" after ${timeout}ms`);
};

/**
 * Assert complete navigation state after click
 */
export const assertNavigationState = async (page, drawer, expectedHash, expectedDrawerState = 'closed') => {
  // Check drawer state
  const drawerState = await drawer.getAttribute('data-state');
  if (drawerState !== expectedDrawerState) {
    throw new Error(`Expected drawer state "${expectedDrawerState}", got "${drawerState}"`);
  }
  
  // Check URL hash
  const currentUrl = page.url();
  const currentHash = new URL(currentUrl).hash;
  if (currentHash !== expectedHash) {
    throw new Error(`Expected URL hash "${expectedHash}", got "${currentHash}"`);
  }
  
  // Check nav-current-hash marker
  const hashMarker = page.locator('[data-testid="nav-current-hash"]');
  const markerText = await hashMarker.textContent();
  if (markerText.trim() !== expectedHash) {
    throw new Error(`Expected nav-current-hash "${expectedHash}", got "${markerText}"`);
  }
  
  console.log(`✅ Navigation state verified: drawer="${drawerState}", hash="${expectedHash}"`);
  return true;
};

export default {
  ensureClickable,
  getMobileDrawerCount,
  waitForDrawerState,
  assertNavigationState
};