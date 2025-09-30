/**
 * TypeScript Contract Test - Integration TestIDs
 * Validates that critical integration testids are present and functional
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TESTIDS } from '../testids.ts';

// Simple mock components for integration testing (no external deps)
const MockAuthLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div>
    <div data-testid={TESTIDS.authEmailInput}>
      <input type="email" placeholder="Email" />
    </div>
    <button data-testid={TESTIDS.authSubmitBtn}>Submit</button>
    <div data-testid={TESTIDS.authError} style={{ display: 'none' }}>
      Error message
    </div>
    {children}
  </div>
);

describe('Integration TestID Contract Tests', () => {
  describe('Authentication Integration TestIDs', () => {
    test('should render auth components with correct testids', () => {
      render(<MockAuthLayout><div>Test</div></MockAuthLayout>);
      
      expect(screen.getByTestId(TESTIDS.authEmailInput)).toBeInTheDocument();
      expect(screen.getByTestId(TESTIDS.authSubmitBtn)).toBeInTheDocument();
      expect(screen.getByTestId(TESTIDS.authError)).toBeInTheDocument();
    });

    test('should have consistent auth testid constants', () => {
      expect(TESTIDS.authEmailInput).toBe('auth-email-input');
      expect(TESTIDS.authSubmitBtn).toBe('auth-submit-btn');
      expect(TESTIDS.authError).toBe('auth-error');
    });
  });

  describe('Navigation Integration TestIDs', () => {
    test('should have navigation testid constants defined', () => {
      expect(TESTIDS.navBrand).toBeDefined();
      expect(TESTIDS.createLeagueBtn).toBeDefined();
      expect(TESTIDS.joinViaInviteBtn).toBeDefined();
    });

    test('should have consistent navigation testid values', () => {
      expect(TESTIDS.navBrand).toBe('nav-brand');
      expect(TESTIDS.createLeagueBtn).toBe('create-league-btn');
      expect(TESTIDS.joinViaInviteBtn).toBe('join-via-invite-btn');
    });
  });
});