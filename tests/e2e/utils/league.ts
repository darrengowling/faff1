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
 * Works with both input and select elements automatically
 */
export async function fillCreateLeague(page: Page, data: CreateLeagueFormData): Promise<void> {
  console.log(`📋 Filling Create League form: ${data.name}`);
  
  // Wait for form fields to be ready
  const requiredFields = [
    TESTIDS.createLeagueWizardName || 'create-name',
    TESTIDS.createLeagueWizardSlots || 'create-slots', 
    TESTIDS.createLeagueWizardBudget || 'create-budget',
    TESTIDS.createLeagueWizardMin || 'create-min'
  ];
  
  await waitForFormReady(page, requiredFields);
  
  // Fill form fields using appropriate methods
  console.log('📝 Filling league name...');
  await page.getByTestId(TESTIDS.createLeagueWizardName || 'create-name').fill(data.name);
  
  console.log('📝 Filling form fields with type-aware setters...');
  await setFormValue(page, TESTIDS.createLeagueWizardSlots || 'create-slots', data.slots);
  await setFormValue(page, TESTIDS.createLeagueWizardBudget || 'create-budget', data.budget);
  await setFormValue(page, TESTIDS.createLeagueWizardMin || 'create-min', data.min);
  
  // Fill max managers if provided and field exists
  if (data.max !== undefined) {
    const maxField = page.getByTestId(TESTIDS.createLeagueWizardMax || 'create-max');
    if (await maxField.count() > 0) {
      await setFormValue(page, TESTIDS.createLeagueWizardMax || 'create-max', data.max);
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