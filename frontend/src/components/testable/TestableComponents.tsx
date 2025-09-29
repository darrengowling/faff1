/**
 * Testable UI Components
 * 
 * Wrapper components that enforce data-testid attributes at compile time.
 * TypeScript will fail builds where testids are missing on critical interactive elements.
 */

import React from 'react';
import { Link } from 'react-router-dom';

// Type that enforces data-testid presence
type MustHaveTestId = { 'data-testid': string };

/**
 * TestableButton - Button that must have a data-testid
 * Used for critical actions like form submission, navigation, etc.
 */
export function TestableButton(
  props: React.ButtonHTMLAttributes<HTMLButtonElement> & MustHaveTestId
) {
  return <button {...props} />;
}

/**
 * TestableInput - Input that must have a data-testid
 * Used for critical form fields like email, passwords, etc.
 */
export function TestableInput(
  props: React.InputHTMLAttributes<HTMLInputElement> & MustHaveTestId
) {
  return <input {...props} />;
}

/**
 * TestableLink - Link that must have a data-testid
 * Used for critical navigation like back-to-home, primary CTAs, etc.
 */
export function TestableLink(
  props: React.AnchorHTMLAttributes<HTMLAnchorElement> & MustHaveTestId
) {
  return <a {...props} />;
}

/**
 * TestableRouterLink - React Router Link that must have a data-testid
 * Used for critical navigation with React Router
 */
export function TestableRouterLink(
  props: React.ComponentProps<typeof Link> & MustHaveTestId
) {
  return <Link {...props} />;
}

/**
 * TestableForm - Form that must have a data-testid
 * Used for critical forms like login, create league, etc.
 */
export function TestableForm(
  props: React.FormHTMLAttributes<HTMLFormElement> & MustHaveTestId
) {
  return <form {...props} />;
}

/**
 * TestableSection - Section that must have a data-testid
 * Used for critical page sections for navigation testing
 */
export function TestableSection(
  props: React.HTMLAttributes<HTMLElement> & MustHaveTestId
) {
  return <section {...props} />;
}

/**
 * TestableDiv - Div that must have a data-testid
 * Used for critical containers like mobile drawers, dialogs, etc.
 */
export function TestableDiv(
  props: React.HTMLAttributes<HTMLDivElement> & MustHaveTestId
) {
  return <div {...props} />;
}