/**
 * E2E Test Selectors Registry
 * 
 * Centralized selectors using canonical testids from the registry.
 * Replaces ad-hoc selectors with registry lookups for consistency.
 */

import { TESTIDS } from '../../../frontend/src/testing/testids';
import type { Page } from '@playwright/test';

/**
 * Get element by testid key from registry
 * Usage: byId(page, 'authEmailInput') instead of page.getByTestId('auth-email-input')
 */
export const byId = (page: Page, key: keyof typeof TESTIDS) => {
  return page.getByTestId(TESTIDS[key]);
};

/**
 * Get multiple elements by testid key from registry
 */
export const allById = (page: Page, key: keyof typeof TESTIDS) => {
  return page.getByTestId(TESTIDS[key]);
};

/**
 * Check if element with testid exists
 */
export const hasId = async (page: Page, key: keyof typeof TESTIDS): Promise<boolean> => {
  const element = byId(page, key);
  return (await element.count()) > 0;
};

/**
 * Wait for element by testid key to be visible
 */
export const waitForId = (page: Page, key: keyof typeof TESTIDS, options?: { timeout?: number }) => {
  return byId(page, key).waitFor({ state: 'visible', ...options });
};

/**
 * Wait for element by testid key to be hidden
 */
export const waitForIdHidden = (page: Page, key: keyof typeof TESTIDS, options?: { timeout?: number }) => {
  return byId(page, key).waitFor({ state: 'hidden', ...options });
};

/**
 * Click element by testid key
 */
export const clickById = async (page: Page, key: keyof typeof TESTIDS, options?: { force?: boolean; timeout?: number }) => {
  const element = byId(page, key);
  return element.click(options);
};

/**
 * Fill input by testid key
 */
export const fillById = async (page: Page, key: keyof typeof TESTIDS, value: string, options?: { force?: boolean; timeout?: number }) => {
  const element = byId(page, key);
  return element.fill(value, options);
};

/**
 * Type into input by testid key
 */
export const typeById = async (page: Page, key: keyof typeof TESTIDS, text: string, options?: { delay?: number }) => {
  const element = byId(page, key);
  return element.type(text, options);
};

/**
 * Get text content by testid key
 */
export const getTextById = async (page: Page, key: keyof typeof TESTIDS): Promise<string> => {
  const element = byId(page, key);
  return element.textContent() || '';
};

/**
 * Get attribute value by testid key
 */
export const getAttributeById = async (page: Page, key: keyof typeof TESTIDS, attribute: string): Promise<string | null> => {
  const element = byId(page, key);
  return element.getAttribute(attribute);
};

/**
 * Check if element is visible by testid key
 */
export const isVisibleById = async (page: Page, key: keyof typeof TESTIDS): Promise<boolean> => {
  const element = byId(page, key);
  return element.isVisible();
};

/**
 * Check if element is enabled by testid key
 */
export const isEnabledById = async (page: Page, key: keyof typeof TESTIDS): Promise<boolean> => {
  const element = byId(page, key);
  return element.isEnabled();
};

/**
 * Check if element is disabled by testid key
 */
export const isDisabledById = async (page: Page, key: keyof typeof TESTIDS): Promise<boolean> => {
  const element = byId(page, key);
  return element.isDisabled();
};

/**
 * Hover over element by testid key
 */
export const hoverById = async (page: Page, key: keyof typeof TESTIDS, options?: { force?: boolean; timeout?: number }) => {
  const element = byId(page, key);
  return element.hover(options);
};

/**
 * Focus element by testid key
 */
export const focusById = async (page: Page, key: keyof typeof TESTIDS, options?: { timeout?: number }) => {
  const element = byId(page, key);
  return element.focus(options);
};

/**
 * Screenshot element by testid key
 */
export const screenshotById = async (page: Page, key: keyof typeof TESTIDS, options?: { path?: string; quality?: number }) => {
  const element = byId(page, key);
  return element.screenshot(options);
};

// Common selector combinations for complex interactions
export const selectors = {
  // Authentication flow
  auth: {
    emailInput: (page: Page) => byId(page, 'authEmailInput'),
    submitBtn: (page: Page) => byId(page, 'authSubmitBtn'),
    errorMessage: (page: Page) => byId(page, 'authError'),
    successMessage: (page: Page) => byId(page, 'authSuccess'),
    loadingState: (page: Page) => byId(page, 'authLoading'),
  },

  // Navigation
  nav: {
    backToHome: (page: Page) => byId(page, 'backToHome'),
    hamburger: (page: Page) => byId(page, 'navHamburger'),
    mobileDrawer: (page: Page) => byId(page, 'mobileDrawer'),
    brand: (page: Page) => byId(page, 'navBrand'),
  },

  // Create league flow
  create: {
    name: (page: Page) => byId(page, 'createName'),
    budget: (page: Page) => byId(page, 'createBudget'),
    slots: (page: Page) => byId(page, 'createSlots'),
    submit: (page: Page) => byId(page, 'createSubmit'),
  },

  // League lobby
  lobby: {
    joined: (page: Page) => byId(page, 'lobbyJoined'),
    rules: (page: Page) => byId(page, 'rulesBadge'),
    startAuction: (page: Page) => byId(page, 'startAuction'),
  },

  // Landing page
  landing: {
    ctaCreate: (page: Page) => byId(page, 'landingCtaCreate'),
    ctaJoin: (page: Page) => byId(page, 'landingCtaJoin'),
    sectionHome: (page: Page) => byId(page, 'sectionHome'),
    sectionHow: (page: Page) => byId(page, 'sectionHow'),
    sectionWhy: (page: Page) => byId(page, 'sectionWhy'),
    sectionFeatures: (page: Page) => byId(page, 'sectionFeatures'),
    sectionSafety: (page: Page) => byId(page, 'sectionSafety'),
    sectionFaq: (page: Page) => byId(page, 'sectionFaq'),
  },

  // Roster/clubs
  roster: {
    list: (page: Page) => byId(page, 'rosterList'),
    item: (page: Page) => byId(page, 'rosterItem'),
    empty: (page: Page) => byId(page, 'rosterEmpty'),
    budgetRemaining: (page: Page) => byId(page, 'budgetRemaining'),
  }
};

// Type-safe selector key validation
export type TestIdKey = keyof typeof TESTIDS;

// Export TESTIDS for direct access if needed
export { TESTIDS };