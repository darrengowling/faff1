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
    // Clear any previous renders
    jest.clearAllMocks();
  });

  describe('Required Navigation TestIDs', () => {
    it('should render nav-create-league-btn in authenticated header', () => {
      render(
        <TestWrapper>
          <GlobalNavbar />
        </TestWrapper>
      );

      // Assert nav create league button exists (only shown when authenticated)
      const navCreateLeagueBtn = screen.getByTestId('nav-create-league-btn');
      expect(navCreateLeagueBtn).toBeInTheDocument();
      expect(navCreateLeagueBtn).toHaveTextContent(/new league/i);
    });
  });

  describe('Required Dashboard TestIDs', () => {
    it('should render create-league-btn in dashboard content', () => {
      render(
        <TestWrapper>
          <DashboardContent
            leagues={mockLeagues}
            onCreateLeague={jest.fn()}
            onViewLeague={jest.fn()}
            onStartAuction={jest.fn()}
            onViewAuction={jest.fn()}
            loading={false}
          />
        </TestWrapper>
      );

      // Assert create league button exists (should be multiple instances)
      const createLeagueButtons = screen.getAllByTestId('create-league-btn');
      expect(createLeagueButtons.length).toBeGreaterThan(0);
      
      // Verify at least one is visible and has expected content
      const firstButton = createLeagueButtons[0];
      expect(firstButton).toBeInTheDocument();
      expect(firstButton).toHaveTextContent(/create league/i);
    });

    it('should render join-via-invite-btn in dashboard content', () => {
      render(
        <TestWrapper>
          <DashboardContent
            leagues={mockLeagues}
            onCreateLeague={jest.fn()}
            onViewLeague={jest.fn()}
            onStartAuction={jest.fn()}
            onViewAuction={jest.fn()}
            loading={false}
          />
        </TestWrapper>
      );

      // Assert join via invite button exists
      const joinViaInviteBtn = screen.getByTestId('join-via-invite-btn');
      expect(joinViaInviteBtn).toBeInTheDocument();
    });
  });

  describe('Critical TestIDs Integration Test', () => {
    it('should render all required testids together in full app context', () => {
      // Render both header and dashboard content together
      render(
        <TestWrapper>
          <div>
            <GlobalNavbar />
            <main>
              <DashboardContent
                leagues={mockLeagues}
                onCreateLeague={jest.fn()}
                onViewLeague={jest.fn()}
                onStartAuction={jest.fn()}
                onViewAuction={jest.fn()}
                loading={false}
              />
            </main>
          </div>
        </TestWrapper>
      );

      // Assert all critical testids exist
      expect(screen.getByTestId('nav-create-league-btn')).toBeInTheDocument();
      expect(screen.getAllByTestId('create-league-btn').length).toBeGreaterThan(0);
      expect(screen.getByTestId('join-via-invite-btn')).toBeInTheDocument();
    });
  });

  describe('TestID Accessibility', () => {
    it('should have accessible names for all required buttons', () => {
      render(
        <TestWrapper>
          <div>
            <GlobalNavbar />
            <main>
              <DashboardContent
                leagues={[]}
                onCreateLeague={jest.fn()}
                onViewLeague={jest.fn()}
                onStartAuction={jest.fn()}
                onViewAuction={jest.fn()}
                loading={false}
              />
            </main>
          </div>
        </TestWrapper>
      );

      // Verify buttons have accessible content
      const navCreateBtn = screen.getByTestId('nav-create-league-btn');
      const joinInviteBtn = screen.getByTestId('join-via-invite-btn');
      const createLeagueButtons = screen.getAllByTestId('create-league-btn');

      // Check accessible names exist
      expect(navCreateBtn).toHaveAccessibleName();
      expect(joinInviteBtn).toHaveAccessibleName();
      expect(createLeagueButtons[0]).toHaveAccessibleName();
    });
  });

  describe('Empty State TestIDs', () => {
    it('should render create-league-btn even with no leagues (empty state)', () => {
      render(
        <TestWrapper>
          <DashboardContent
            leagues={[]}
            onCreateLeague={jest.fn()}
            onViewLeague={jest.fn()}
            onStartAuction={jest.fn()}
            onViewAuction={jest.fn()}
            loading={false}
          />
        </TestWrapper>
      );

      // Even with empty leagues, create league button should exist
      const createLeagueButtons = screen.getAllByTestId('create-league-btn');
      expect(createLeagueButtons.length).toBeGreaterThan(0);
    });
  });

  describe('Loading State TestIDs', () => {
    it('should render create-league-btn even during loading state', () => {
      render(
        <TestWrapper>
          <DashboardContent
            leagues={[]}
            onCreateLeague={jest.fn()}
            onViewLeague={jest.fn()}
            onStartAuction={jest.fn()}
            onViewAuction={jest.fn()}
            loading={true}
          />
        </TestWrapper>
      );

      // During loading, create league button should still exist
      // (CreateLeagueCTA always renders with testid)
      const createLeagueButtons = screen.getAllByTestId('create-league-btn');
      expect(createLeagueButtons.length).toBeGreaterThan(0);
    });
  });
});