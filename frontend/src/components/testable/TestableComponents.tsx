/**
 * Testable UI Components
 * 
 * Wrapper components that enforce data-testid attributes at compile time.
 * TypeScript will fail builds where testids are missing on critical interactive elements.
 * 
 * Enhanced with stable DOM patterns - elements stay mounted with disabled states
 * instead of being unmounted during loading or conditional states.
 */

import React from 'react';
import { Link } from 'react-router-dom';

// Type that enforces data-testid presence
type MustHaveTestId = { 'data-testid': string };

// Helper function to manage stable element classes
function getStableClasses(loading?: boolean, hidden?: boolean, className?: string): string {
  const classes = [className || ''];
  
  if (loading) classes.push('loading');
  if (hidden) classes.push('visually-hidden');
  
  return classes.filter(Boolean).join(' ');
}

/**
 * TestableButton - Button that must have a data-testid
 * Used for critical actions like form submission, navigation, etc.
 * Supports stable disabled states during loading.
 */
export function TestableButton(
  props: React.ButtonHTMLAttributes<HTMLButtonElement> & MustHaveTestId & {
    loading?: boolean;
    stableHidden?: boolean;
  }
) {
  const { loading, stableHidden, className, disabled, ...otherProps } = props;
  
  return (
    <button 
      {...otherProps} 
      className={getStableClasses(loading, stableHidden, className)}
      disabled={disabled || loading}
      aria-disabled={disabled || loading ? 'true' : 'false'}
      aria-hidden={stableHidden ? 'true' : 'false'}
    />
  );
}

/**
 * TestableInput - Input that must have a data-testid
 * Used for critical form fields like email, passwords, etc.
 * Supports stable disabled states during loading.
 */
export function TestableInput(
  props: React.InputHTMLAttributes<HTMLInputElement> & MustHaveTestId & {
    loading?: boolean;
    stableHidden?: boolean;
  }
) {
  const { loading, stableHidden, className, disabled, readOnly, ...otherProps } = props;
  
  return (
    <input 
      {...otherProps} 
      className={getStableClasses(loading, stableHidden, className)}
      disabled={disabled || loading}
      readOnly={readOnly || loading}
      aria-disabled={disabled || loading ? 'true' : 'false'}
      aria-hidden={stableHidden ? 'true' : 'false'}
    />
  );
}

/**
 * TestableLink - Link that must have a data-testid
 * Used for critical navigation like back-to-home, primary CTAs, etc.
 */
export function TestableLink(
  props: React.AnchorHTMLAttributes<HTMLAnchorElement> & MustHaveTestId & {
    loading?: boolean;
    stableHidden?: boolean;
  }
) {
  const { loading, stableHidden, className, ...otherProps } = props;
  
  return (
    <a 
      {...otherProps} 
      className={getStableClasses(loading, stableHidden, className)}
      aria-disabled={loading ? 'true' : 'false'}
      aria-hidden={stableHidden ? 'true' : 'false'}
    />
  );
}

/**
 * TestableRouterLink - React Router Link that must have a data-testid
 * Used for critical navigation with React Router
 */
export function TestableRouterLink(
  props: React.ComponentProps<typeof Link> & MustHaveTestId & {
    loading?: boolean;
    stableHidden?: boolean;
  }
) {
  const { loading, stableHidden, className, ...otherProps } = props;
  
  return (
    <Link 
      {...otherProps} 
      className={getStableClasses(loading, stableHidden, className)}
      aria-disabled={loading ? 'true' : 'false'}
      aria-hidden={stableHidden ? 'true' : 'false'}
    />
  );
}

/**
 * TestableForm - Form that must have a data-testid
 * Used for critical forms like login, create league, etc.
 */
export function TestableForm(
  props: React.FormHTMLAttributes<HTMLFormElement> & MustHaveTestId & {
    loading?: boolean;
    stableHidden?: boolean;
  }
) {
  const { loading, stableHidden, className, ...otherProps } = props;
  
  return (
    <form 
      {...otherProps} 
      className={getStableClasses(loading, stableHidden, className)}
      aria-disabled={loading ? 'true' : 'false'}
      aria-hidden={stableHidden ? 'true' : 'false'}
    />
  );
}

/**
 * TestableSection - Section that must have a data-testid
 * Used for critical page sections for navigation testing
 */
export function TestableSection(
  props: React.HTMLAttributes<HTMLElement> & MustHaveTestId & {
    loading?: boolean;
    stableHidden?: boolean;
  }
) {
  const { loading, stableHidden, className, ...otherProps } = props;
  
  return (
    <section 
      {...otherProps} 
      className={getStableClasses(loading, stableHidden, className)}
      aria-hidden={stableHidden ? 'true' : 'false'}
    />
  );
}

/**
 * TestableDiv - Div that must have a data-testid
 * Used for critical containers like mobile drawers, dialogs, etc.
 */
export function TestableDiv(
  props: React.HTMLAttributes<HTMLDivElement> & MustHaveTestId & {
    loading?: boolean;
    stableHidden?: boolean;
  }
) {
  const { loading, stableHidden, className, ...otherProps } = props;
  
  return (
    <div 
      {...otherProps} 
      className={getStableClasses(loading, stableHidden, className)}
      aria-hidden={stableHidden ? 'true' : 'false'}
    />
  );
}