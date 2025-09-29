/**
 * Back to Home Link Contract Test
 * 
 * Ensures data-testid="back-to-home-link" exists and has correct properties
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import BackToHomeLink from '../components/BackToHomeLink';

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

describe('Back to Home Link Contract', () => {
  test('BackToHomeLink component has required testid and href', () => {
    render(<BackToHomeLink />);

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    expect(backToHomeLink).toBeInTheDocument();
    expect(backToHomeLink).toHaveAttribute('href', '/app');
    expect(backToHomeLink).toHaveAttribute('aria-label', 'Back to Home');
  });

  test('BackToHomeLink has accessible text content', () => {
    render(<BackToHomeLink />);

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    expect(backToHomeLink).toHaveTextContent('← Back to Home');
    expect(backToHomeLink).toHaveAttribute('aria-label', 'Back to Home');
  });

  test('BackToHomeLink accepts custom className', () => {
    const customClass = 'custom-test-class';
    render(<BackToHomeLink className={customClass} />);

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    expect(backToHomeLink).toHaveClass(customClass);
  });

  test('BackToHomeLink handles onClick prop', () => {
    const handleClick = jest.fn();
    render(<BackToHomeLink onClick={handleClick} />);

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    backToHomeLink.click();
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('BackToHomeLink is clickable (no pointer-events none)', () => {
    render(<BackToHomeLink />);

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    
    // Check that the element doesn't have styles that would prevent clicking
    const computedStyle = window.getComputedStyle(backToHomeLink);
    expect(computedStyle.pointerEvents).not.toBe('none');
    
    // Ensure it's visible and in the document
    expect(backToHomeLink).toBeVisible();
  });

  test('BackToHomeLink always points to /app', () => {
    // Test multiple instances to ensure consistency
    const { rerender } = render(<BackToHomeLink />);
    expect(screen.getByTestId('back-to-home-link')).toHaveAttribute('href', '/app');

    rerender(<BackToHomeLink className="different-class" />);
    expect(screen.getByTestId('back-to-home-link')).toHaveAttribute('href', '/app');

    rerender(<BackToHomeLink onClick={() => {}} />);
    expect(screen.getByTestId('back-to-home-link')).toHaveAttribute('href', '/app');
  });
});