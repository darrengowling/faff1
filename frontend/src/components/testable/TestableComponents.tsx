/**
 * Testable UI Components
 * 
 * Wrapper components that enforce data-testid attributes at compile time.
 * TypeScript will fail builds where testids are missing on critical interactive elements.
 */

import React from 'react';

// Type that enforces data-testid presence
type MustHaveTestId = { 'data-testid': string };

/**
 * TestableButton - Button that must have a data-testid
 * Used for critical actions like form submission, navigation, etc.
 */
export function TestableButton(
  props: JSX.IntrinsicElements['button'] & MustHaveTestId
) {
  return <button {...props} />;
}

/**
 * TestableInput - Input that must have a data-testid
 * Used for critical form fields like email, passwords, etc.
 */
export function TestableInput(
  props: JSX.IntrinsicElements['input'] & MustHaveTestId
) {
  return <input {...props} />;
}

/**
 * TestableLink - Link that must have a data-testid
 * Used for critical navigation like back-to-home, primary CTAs, etc.
 */
export function TestableLink(
  props: JSX.IntrinsicElements['a'] & MustHaveTestId
) {
  return <a {...props} />;
}

/**
 * TestableForm - Form that must have a data-testid
 * Used for critical forms like login, create league, etc.
 */
export function TestableForm(
  props: JSX.IntrinsicElements['form'] & MustHaveTestId
) {
  return <form {...props} />;
}

/**
 * TestableSection - Section that must have a data-testid
 * Used for critical page sections for navigation testing
 */
export function TestableSection(
  props: JSX.IntrinsicElements['section'] & MustHaveTestId
) {
  return <section {...props} />;
}

/**
 * TestableDiv - Div that must have a data-testid
 * Used for critical containers like mobile drawers, dialogs, etc.
 */
export function TestableDiv(
  props: JSX.IntrinsicElements['div'] & MustHaveTestId
) {
  return <div {...props} />;
}