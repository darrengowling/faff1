/**
 * Overlay Detection Utility
 * Detects if elements are intercepted by overlays before clicking
 */

import { Page, Locator } from '@playwright/test';

export interface OverlayDetectionResult {
  isBlocked: boolean;
  targetSelector?: string;
  interceptingSelector?: string;
  interceptingZIndex?: string;
  targetZIndex?: string;
  elementsAtPoint?: string[];
}

/**
 * Detect if a target element is blocked by overlays using elementsFromPoint
 * 
 * @param page Playwright page
 * @param target Target element locator
 * @param options Detection options
 * @returns Promise<OverlayDetectionResult>
 */
export async function detectOverlay(
  page: Page, 
  target: Locator,
  options: {
    logDetails?: boolean;
    failOnBlock?: boolean;
    timeout?: number;
  } = {}
): Promise<OverlayDetectionResult> {
  const { logDetails = false, failOnBlock = true, timeout = 5000 } = options;
  
  try {
    // Wait for target to be visible
    await target.waitFor({ state: 'visible', timeout });
    
    // Get target element's bounding box
    const targetBox = await target.boundingBox();
    if (!targetBox) {
      throw new Error('Target element has no bounding box');
    }
    
    // Calculate center point
    const centerX = targetBox.x + targetBox.width / 2;
    const centerY = targetBox.y + targetBox.height / 2;
    
    if (logDetails) {
      console.log(`🎯 Checking overlay at center point (${centerX}, ${centerY})`);
    }
    
    // Get elements at the center point
    const elementsAtPoint = await page.evaluate(({ x, y }) => {
      const elements = document.elementsFromPoint(x, y);
      return elements.map((el, index) => {
        const styles = window.getComputedStyle(el);
        const selector = el.tagName.toLowerCase() + 
          (el.id ? `#${el.id}` : '') + 
          (el.className ? `.${el.className.split(' ').join('.')}` : '') +
          (el.getAttribute('data-testid') ? `[data-testid="${el.getAttribute('data-testid')}"]` : '');
        
        return {
          index,
          selector,
          zIndex: styles.zIndex,
          pointerEvents: styles.pointerEvents,
          position: styles.position,
          tag: el.tagName
        };
      });
    }, { x: centerX, y: centerY });
    
    if (logDetails) {
      console.log('📍 Elements at point (top to bottom):');
      elementsAtPoint.forEach((el, i) => {
        console.log(`  ${i}: ${el.selector} (z-index: ${el.zIndex}, pointer-events: ${el.pointerEvents})`);
      });
    }
    
    // Check if target element is the top-most clickable element
    const topElement = elementsAtPoint[0];
    
    // Get target element info for comparison
    const targetInfo = await target.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      const selector = el.tagName.toLowerCase() + 
        (el.id ? `#${el.id}` : '') + 
        (el.className ? `.${el.className.split(' ').join('.')}` : '') +
        (el.getAttribute('data-testid') ? `[data-testid="${el.getAttribute('data-testid')}"]` : '');
      
      return {
        selector,
        zIndex: styles.zIndex,
        pointerEvents: styles.pointerEvents,
        tag: el.tagName
      };
    });
    
    // Check if target is at the top or if top elements have pointer-events: none
    let isBlocked = false;
    let interceptingSelector = '';
    let interceptingZIndex = '';
    
    // Find first element with pointer-events: auto/unset that's not the target
    for (const element of elementsAtPoint) {
      if (element.pointerEvents !== 'none') {
        // Check if this is the target element by comparing selectors or tags
        const isTargetElement = element.selector.includes(targetInfo.tag.toLowerCase()) ||
                               element.selector === targetInfo.selector ||
                               element.index === 0; // Assume first clickable element is target
        
        if (!isTargetElement) {
          isBlocked = true;
          interceptingSelector = element.selector;
          interceptingZIndex = element.zIndex;
          break;
        } else {
          // Target found at appropriate position
          break;
        }
      }
    }
    
    const result: OverlayDetectionResult = {
      isBlocked,
      targetSelector: targetInfo.selector,
      interceptingSelector: isBlocked ? interceptingSelector : undefined,
      interceptingZIndex: isBlocked ? interceptingZIndex : undefined,
      targetZIndex: targetInfo.zIndex,
      elementsAtPoint: elementsAtPoint.map(el => `${el.selector} (z:${el.zIndex}, pe:${el.pointerEvents})`)
    };
    
    if (logDetails || isBlocked) {
      if (isBlocked) {
        console.log(`❌ Overlay detected! Target blocked by: ${interceptingSelector} (z-index: ${interceptingZIndex})`);
        console.log(`   Target: ${targetInfo.selector} (z-index: ${targetInfo.zIndex})`);
      } else {
        console.log(`✅ No overlay blocking target: ${targetInfo.selector}`);
      }
    }
    
    if (failOnBlock && isBlocked) {
      throw new Error(`Overlay blocking target element! Intercepting: ${interceptingSelector} (z-index: ${interceptingZIndex})`);
    }
    
    return result;
    
  } catch (error) {
    const result: OverlayDetectionResult = {
      isBlocked: true,
      targetSelector: 'unknown',
      interceptingSelector: 'error-during-detection',
      interceptingZIndex: 'unknown'
    };
    
    if (failOnBlock) {
      throw new Error(`Overlay detection failed: ${error.message}`);
    }
    
    return result;
  }
}

/**
 * Safe click with overlay detection
 * Detects overlays before clicking and provides detailed error info
 */
export async function safeClickWithOverlayDetection(
  page: Page,
  target: Locator,
  options: {
    logDetails?: boolean;
    force?: boolean;
    timeout?: number;
  } = {}
): Promise<void> {
  const { logDetails = false, force = false, timeout = 5000 } = options;
  
  try {
    // Detect overlay first
    const detection = await detectOverlay(page, target, {
      logDetails,
      failOnBlock: !force,
      timeout
    });
    
    if (detection.isBlocked && !force) {
      throw new Error(
        `Cannot click - element blocked by overlay!\n` +
        `Target: ${detection.targetSelector}\n` +
        `Intercepting: ${detection.interceptingSelector} (z-index: ${detection.interceptingZIndex})\n` +
        `Elements at point: ${JSON.stringify(detection.elementsAtPoint, null, 2)}`
      );
    }
    
    // Proceed with click
    if (force && detection.isBlocked) {
      console.log(`⚠️ Force clicking despite overlay: ${detection.interceptingSelector}`);
      await target.click({ force: true });
    } else {
      await target.click();
    }
    
    if (logDetails) {
      console.log(`✅ Click successful on: ${detection.targetSelector}`);
    }
    
  } catch (error) {
    console.error(`❌ Safe click failed: ${error.message}`);
    throw error;
  }
}

/**
 * Check if landing page CTAs are clickable (for landing-page.spec.ts)
 */
export async function checkLandingCTAsClickable(page: Page): Promise<void> {
  console.log('🔍 Checking landing page CTAs for overlay issues...');
  
  const ctaSelectors = [
    '[data-testid="create-league-btn"]',
    '[data-testid="join-league-btn"]',
    'button:has-text("Create a League")',
    'button:has-text("Join with an Invite")'
  ];
  
  for (const selector of ctaSelectors) {
    try {
      const element = page.locator(selector).first();
      const count = await element.count();
      
      if (count > 0) {
        console.log(`🎯 Checking CTA: ${selector}`);
        await detectOverlay(page, element, { 
          logDetails: true, 
          failOnBlock: true,
          timeout: 5000 
        });
        console.log(`✅ CTA clickable: ${selector}`);
      } else {
        console.log(`⏭️ CTA not found: ${selector}`);
      }
    } catch (error) {
      throw new Error(`CTA blocked by overlay: ${selector} - ${error.message}`);
    }
  }
  
  console.log('✅ All landing page CTAs are clickable');
}

/**
 * Check anchor scroll functionality
 */
export async function checkAnchorScrolling(page: Page, anchors: string[]): Promise<void> {
  console.log('🔍 Checking anchor scrolling functionality...');
  
  for (const anchor of anchors) {
    try {
      console.log(`📍 Testing anchor: ${anchor}`);
      
      // Click anchor link
      const anchorLink = page.locator(`a[href="#${anchor}"]`).first();
      const linkCount = await anchorLink.count();
      
      if (linkCount > 0) {
        // Check if link is clickable
        await detectOverlay(page, anchorLink, { 
          logDetails: true, 
          failOnBlock: true 
        });
        
        // Get current scroll position
        const initialScroll = await page.evaluate(() => window.scrollY);
        
        // Click the anchor
        await anchorLink.click();
        await page.waitForTimeout(1000); // Allow scroll animation
        
        // Check if scroll position changed
        const finalScroll = await page.evaluate(() => window.scrollY);
        
        if (Math.abs(finalScroll - initialScroll) < 10) {
          throw new Error(`Anchor scroll failed - no scroll movement detected for #${anchor}`);
        }
        
        console.log(`✅ Anchor scroll working: #${anchor} (${initialScroll} → ${finalScroll})`);
      } else {
        console.log(`⏭️ Anchor link not found: #${anchor}`);
      }
    } catch (error) {
      throw new Error(`Anchor scroll test failed for #${anchor}: ${error.message}`);
    }
  }
  
  console.log('✅ All anchor scrolling tests passed');
}