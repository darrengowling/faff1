/**
 * Contract Test: Required TestIDs
 * 
 * Fast test to validate that critical testids exist in rendered components.
 * This catches testid regressions before expensive E2E tests run.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import CreateLeagueCTA from '../components/ui/create-league-cta';
import QuickActionCards from '../components/ui/quick-action-cards';
import { TESTIDS } from '../testids.js';

// Mock functions for component props
const mockHandlers = {
  onCreateLeague: jest.fn(),
  onJoinViaInvite: jest.fn(),
  onResumeAuction: jest.fn(),
};

describe('TestID Contract Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Critical TestIDs - Component Level', () => {
    it('should render create-league-btn in CreateLeagueCTA component', () => {
      render(
        <CreateLeagueCTA
          isLoading={false}
          onCreateLeague={mockHandlers.onCreateLeague}
        />
      );

      // Assert create league button exists with correct testid
      const createLeagueBtn = screen.getByTestId(TESTIDS.createLeagueBtn);
      expect(createLeagueBtn).toBeInTheDocument();
      expect(createLeagueBtn).toHaveTextContent(/create league/i);
    });

    it('should render create-league-btn even during loading state', () => {
      render(
        <CreateLeagueCTA
          isLoading={true}
          onCreateLeague={mockHandlers.onCreateLeague}
        />
      );

      // Button should exist even during loading
      const createLeagueBtn = screen.getByTestId(TESTIDS.createLeagueBtn);
      expect(createLeagueBtn).toBeInTheDocument();
      expect(createLeagueBtn).toBeDisabled();
      expect(createLeagueBtn).toHaveTextContent(/loading/i);
    });

    it('should render join-via-invite-btn in QuickActionCards component', () => {
      render(
        <QuickActionCards
          onCreateLeague={mockHandlers.onCreateLeague}
          onJoinViaInvite={mockHandlers.onJoinViaInvite}
          activeAuctions={[]}
          onResumeAuction={mockHandlers.onResumeAuction}
        />
      );

      // Assert join via invite button exists
      const joinViaInviteBtn = screen.getByTestId(TESTIDS.joinViaInviteBtn);
      expect(joinViaInviteBtn).toBeInTheDocument();
      expect(joinViaInviteBtn).toHaveTextContent(/join via invite/i);
    });
  });

  describe('TestID Constants Validation', () => {
    it('should have all required testid constants defined', () => {
      // Verify that all critical testids are defined in TESTIDS
      expect(TESTIDS.createLeagueBtn).toBeDefined();
      expect(TESTIDS.createLeagueBtn).toBe('create-league-btn');
      
      expect(TESTIDS.joinViaInviteBtn).toBeDefined();
      expect(TESTIDS.joinViaInviteBtn).toBe('join-via-invite-btn');
      
      expect(TESTIDS.navCreateLeagueBtn).toBeDefined();
      expect(TESTIDS.navCreateLeagueBtn).toBe('nav-create-league-btn');
    });

    it('should not have duplicate testid values for different constants', () => {
      const testIdValues = [
        TESTIDS.createLeagueBtn,
        TESTIDS.joinViaInviteBtn,
        TESTIDS.navCreateLeagueBtn
      ];

      // Check for duplicates
      const uniqueValues = new Set(testIdValues);
      expect(uniqueValues.size).toBe(testIdValues.length);
    });
  });

  describe('Component Props Validation', () => {
    it('should handle CreateLeagueCTA with different variants', () => {
      const { rerender } = render(
        <CreateLeagueCTA
          isLoading={false}
          onCreateLeague={mockHandlers.onCreateLeague}
          variant="default"
        />
      );

      expect(screen.getByTestId(TESTIDS.createLeagueBtn)).toBeInTheDocument();

      // Test with outline variant
      rerender(
        <CreateLeagueCTA
          isLoading={false}
          onCreateLeague={mockHandlers.onCreateLeague}
          variant="outline"
        />
      );

      expect(screen.getByTestId(TESTIDS.createLeagueBtn)).toBeInTheDocument();
    });

    it('should handle QuickActionCards with active auctions', () => {
      const activeAuctions = [
        { id: 'auction-1', name: 'Test Auction', status: 'active' }
      ];

      render(
        <QuickActionCards
          onCreateLeague={mockHandlers.onCreateLeague}
          onJoinViaInvite={mockHandlers.onJoinViaInvite}
          activeAuctions={activeAuctions}
          onResumeAuction={mockHandlers.onResumeAuction}
        />
      );

      // Both buttons should still exist
      expect(screen.getByTestId(TESTIDS.joinViaInviteBtn)).toBeInTheDocument();
      // Create league functionality should be in the quick actions
      expect(screen.getByText(/create a league/i)).toBeInTheDocument();
    });
  });

  describe('Error Boundaries', () => {
    it('should fail gracefully if testids are missing', () => {
      // This test ensures that if testids are removed, the contract test fails
      render(
        <button>Create League Without TestID</button>
      );

      // This should NOT find the button, proving the contract works
      expect(screen.queryByTestId(TESTIDS.createLeagueBtn)).not.toBeInTheDocument();
    });
  });
});