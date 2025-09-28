/**
 * League creation and management helpers
 * Uses type-aware form helpers to work with various form field types
 */

import { Page } from '@playwright/test';
import { setFormValue, waitForFormReady } from './form';
import { TESTIDS } from '../../../frontend/src/testids.js';

export interface CreateLeagueFormData {
  name: string;
  slots: number;
  budget: number;
  min: number;
  max?: number;
}

/**
 * Fill the Create League form using type-aware field setters
 * Works with both the CreateLeagueDialog (dashboard) and CreateLeagueWizard (page) forms
 */
export async function fillCreateLeague(page: Page, data: CreateLeagueFormData): Promise<void> {
  console.log(`📋 Filling Create League form: ${data.name}`);
  
  // Try to detect which form we're dealing with by checking for specific testids
  const dialogSlotsField = page.getByTestId('create-slots-input');
  const wizardSlotsField = page.getByTestId('create-slots');
  
  let isDialog = false;
  let isWizard = false;
  
  // Check which form is present (with timeout to avoid hanging)
  try {
    await dialogSlotsField.waitFor({ state: 'visible', timeout: 3000 });
    isDialog = true;
    console.log('📋 Detected CreateLeagueDialog (modal) form');
  } catch {
    try {
      await wizardSlotsField.waitFor({ state: 'visible', timeout: 3000 });
      isWizard = true;
      console.log('📋 Detected CreateLeagueWizard (page) form');
    } catch {
      throw new Error('No Create League form detected - neither dialog nor wizard form found');
    }
  }
  
  // Use appropriate testids based on detected form
  const testIds = isDialog ? {
    name: 'create-name',
    slots: 'create-slots-input',
    budget: 'create-budget',
    min: 'create-min',
    max: 'create-max'
  } : {
    name: TESTIDS.createLeagueWizardName || 'create-name',
    slots: TESTIDS.createLeagueWizardSlots || 'create-slots',
    budget: TESTIDS.createLeagueWizardBudget || 'create-budget',
    min: TESTIDS.createLeagueWizardMin || 'create-min',
    max: TESTIDS.createLeagueWizardMax || 'create-max'
  };
  
  console.log(`📝 Using ${isDialog ? 'dialog' : 'wizard'} testids:`, testIds);
  
  // Fill form fields using appropriate methods
  console.log('📝 Filling league name...');
  await page.getByTestId(testIds.name).fill(data.name);
  
  console.log('📝 Filling form fields with type-aware setters...');
  await setFormValue(page, testIds.slots, data.slots);
  await setFormValue(page, testIds.budget, data.budget);
  await setFormValue(page, testIds.min, data.min);
  
  // Fill max managers if provided and field exists
  if (data.max !== undefined) {
    const maxField = page.getByTestId(testIds.max);
    if (await maxField.count() > 0) {
      await setFormValue(page, testIds.max, data.max);
    }
  }
  
  console.log(`✅ Create League form filled successfully: ${data.name}`);
}

/**
 * Complete league creation flow: fill form + submit + wait for success
 */
export async function createLeagueFlow(page: Page, data: CreateLeagueFormData): Promise<string> {
  console.log(`🚀 Starting league creation flow: ${data.name}`);
  
  // Fill the form
  await fillCreateLeague(page, data);
  
  // Submit the form
  console.log('📤 Submitting Create League form...');
  const submitBtn = page.getByTestId(TESTIDS.createSubmit || 'create-submit');
  await submitBtn.click();
  
  // Wait for success or URL change
  console.log('⏳ Waiting for league creation success...');
  try {
    // Option 1: Wait for success marker
    await page.getByTestId('create-success').waitFor({ state: 'visible', timeout: 15000 });
    console.log('✅ Success marker detected');
  } catch (successError) {
    // Option 2: Wait for URL change to lobby
    console.log('Success marker not found, checking URL...');
    await page.waitForURL('**/lobby', { timeout: 10000 });
    console.log('✅ URL changed to lobby');
  }
  
  // Extract league ID from URL
  const currentUrl = page.url();
  const leagueIdMatch = currentUrl.match(/\/leagues\/([^\/]+)\//);
  
  if (!leagueIdMatch) {
    throw new Error(`Could not extract league ID from URL: ${currentUrl}`);
  }
  
  const leagueId = leagueIdMatch[1];
  console.log(`✅ League created successfully: ${data.name} (ID: ${leagueId})`);
  
  return leagueId;
}