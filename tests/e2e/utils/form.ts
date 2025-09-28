import { expect, Page } from '@playwright/test';

/**
 * Type-aware form field setter that works with both <input> and <select> elements
 * Automatically detects element type and uses appropriate interaction method
 */
export async function setFormValue(page: Page, testId: string, value: string | number): Promise<void> {
  const el = page.getByTestId(testId);
  await el.waitFor({ state: 'visible' });
  
  // Get element tag and type to determine interaction method
  const tag = await el.evaluate((n) => (n as HTMLElement).tagName.toLowerCase());
  const type = await el.getAttribute('type');
  
  console.log(`🔧 Setting form value: ${testId}=${value} (tag: ${tag}, type: ${type})`);
  
  if (tag === 'select') {
    // Handle select dropdown
    await el.selectOption(String(value));
  } else {
    // Handle generic input (including type="number", type="text", etc.)
    await el.focus();
    
    // For input fields, use fill() which is more reliable than type()
    await el.fill(String(value));
    
    await el.blur(); // Trigger any onChange events
    
    // Verify the value was set correctly
    await expect(el).toHaveValue(String(value));
  }
  
  console.log(`✅ Form value set: ${testId}=${value}`);
}

/**
 * Batch form filling utility for multiple fields
 */
export async function setFormValues(page: Page, fields: Record<string, string | number>): Promise<void> {
  for (const [testId, value] of Object.entries(fields)) {
    await setFormValue(page, testId, value);
  }
}

/**
 * Wait for form to be ready (all required fields visible)
 */
export async function waitForFormReady(page: Page, testIds: string[]): Promise<void> {
  console.log(`⏳ Waiting for form fields to be ready: ${testIds.join(', ')}`);
  
  for (const testId of testIds) {
    await page.getByTestId(testId).waitFor({ state: 'visible', timeout: 10000 });
  }
  
  console.log(`✅ Form ready: all ${testIds.length} fields visible`);
}