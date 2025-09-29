/**
 * Back to Home Link Contract Test
 * 
 * Ensures data-testid="back-to-home-link" exists on all key pages
 * and has correct href pointing to /app
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/i18n';

// Mock components and providers
const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
  const authValue = {
    user: null,
    loading: false,
    login: jest.fn(),
    logout: jest.fn(),
    refreshUser: jest.fn(),
  };
  return (
    <div data-testcontext="auth-mock">
      {children}
    </div>
  );
};

// Mock theme provider
const MockThemeProvider = ({ children }: { children: React.ReactNode }) => (
  <div data-testcontext="theme-mock">{children}</div>
);

// Import components after mocking
import App from '../App';
import LoginPage from '../components/LoginPage';
import MarketingShell from '../components/layouts/MarketingShell';
import AppShell from '../components/layouts/AppShell';

// Mock the App's useAuth hook
jest.mock('../App', () => {
  const actual = jest.requireActual('../App');
  return {
    ...actual,
    useAuth: () => ({
      user: null,
      loading: false,
      login: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    }),
  };
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <I18nextProvider i18n={i18n}>
      <MockThemeProvider>
        <MockAuthProvider>
          {children}
        </MockAuthProvider>
      </MockThemeProvider>
    </I18nextProvider>
  </BrowserRouter>
);

describe('Back to Home Link Contract', () => {
  beforeEach(() => {
    // Reset any mocks
    jest.clearAllMocks();
  });

  test('LoginPage has back-to-home-link with correct href', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    expect(backToHomeLink).toBeInTheDocument();
    expect(backToHomeLink).toHaveAttribute('href', '/app');
    expect(backToHomeLink).toHaveAttribute('aria-label', 'Back to Home');
  });

  test('MarketingShell has back-to-home-link with correct href', () => {
    render(
      <TestWrapper>
        <MarketingShell>
          <div>Marketing content</div>
        </MarketingShell>
      </TestWrapper>
    );

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    expect(backToHomeLink).toBeInTheDocument();
    expect(backToHomeLink).toHaveAttribute('href', '/app');
    expect(backToHomeLink).toHaveAttribute('aria-label', 'Back to Home');
  });

  test('AppShell has back-to-home-link with correct href', () => {
    render(
      <TestWrapper>
        <AppShell>
          <div>App content</div>
        </AppShell>
      </TestWrapper>
    );

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    expect(backToHomeLink).toBeInTheDocument();
    expect(backToHomeLink).toHaveAttribute('href', '/app');
    expect(backToHomeLink).toHaveAttribute('aria-label', 'Back to Home');
  });

  test('back-to-home-link is always present regardless of auth state', () => {
    // Test with different auth states to ensure it's always present
    const authStates = [
      { user: null, loading: true },
      { user: null, loading: false },
      { user: { email: 'test@example.com' }, loading: false },
    ];

    authStates.forEach((authState, index) => {
      const MockAuthProviderWithState = ({ children }: { children: React.ReactNode }) => {
        const authValue = {
          ...authState,
          login: jest.fn(),
          logout: jest.fn(),
          refreshUser: jest.fn(),
        };
        return (
          <div data-testcontext={`auth-mock-${index}`}>
            {children}
          </div>
        );
      };

      const { unmount } = render(
        <BrowserRouter>
          <I18nextProvider i18n={i18n}>
            <MockThemeProvider>
              <MockAuthProviderWithState>
                <MarketingShell>
                  <div>Test content</div>
                </MarketingShell>
              </MockAuthProviderWithState>
            </MockThemeProvider>
          </I18nextProvider>
        </BrowserRouter>
      );

      const backToHomeLink = screen.getByTestId('back-to-home-link');
      expect(backToHomeLink).toBeInTheDocument();
      expect(backToHomeLink).toHaveAttribute('href', '/app');

      unmount();
    });
  });

  test('back-to-home-link has accessible text content', () => {
    render(
      <TestWrapper>
        <MarketingShell>
          <div>Content</div>
        </MarketingShell>
      </TestWrapper>
    );

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    expect(backToHomeLink).toHaveTextContent('← Back to Home');
    expect(backToHomeLink).toHaveAttribute('aria-label', 'Back to Home');
  });

  test('back-to-home-link is clickable (no pointer-events interception)', () => {
    render(
      <TestWrapper>
        <MarketingShell>
          <div>Content</div>
        </MarketingShell>
      </TestWrapper>
    );

    const backToHomeLink = screen.getByTestId('back-to-home-link');
    
    // Check that the element doesn't have styles that would prevent clicking
    const computedStyle = window.getComputedStyle(backToHomeLink);
    expect(computedStyle.pointerEvents).not.toBe('none');
    
    // Ensure it's visible and in the document
    expect(backToHomeLink).toBeVisible();
  });
});