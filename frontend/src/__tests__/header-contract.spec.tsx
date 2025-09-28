/**
 * Header Contract Tests
 * 
 * Ensures exactly one <header> element renders across all routes
 * to prevent duplicate header issues and overlay problems
 */

import React from 'react';
import { render } from '@testing-library/react';
import AppShell from '../components/layouts/AppShell';
import MarketingShell from '../components/layouts/MarketingShell';

// Mock dependencies to avoid external API calls
jest.mock('../components/ui/HeaderBrand', () => {
  return function MockHeaderBrand() {
    return <div data-testid="header-brand">Brand</div>;
  };
});

jest.mock('../components/navigation/ProductDropdownMenu', () => {
  return function MockProductDropdownMenu() {
    return <div data-testid="product-dropdown">Dropdown</div>;
  };
});

jest.mock('../components/navigation/AuthNavigation', () => {
  return function MockAuthNavigation() {
    return <div data-testid="auth-navigation">Auth Nav</div>;
  };
});

jest.mock('../components/ui/theme-toggle', () => {
  return {
    IconThemeToggle: function MockThemeToggle() {
      return <div data-testid="theme-toggle">Theme</div>;
    }
  };
});

jest.mock('../components/ui/footer', () => {
  return {
    InAppFooter: function MockFooter() {
      return <footer data-testid="app-footer">Footer</footer>;
    }
  };
});

jest.mock('../App', () => {
  return {
    useAuth: () => ({ user: { email: 'test@example.com' } })
  };
});

// Mock react-router-dom
const mockNavigate = jest.fn();
const mockLocation = { pathname: '/app' };
jest.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useLocation: () => mockLocation
}));

// Mock react-i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key
  })
}));

describe('Header Contract Tests', () => {
  beforeEach(() => {
    // Clear any existing DOM
    document.body.innerHTML = '';
    
    // Mock authentication state
    const mockUser = { email: 'test@example.com', id: 'test-user' };
    localStorage.setItem('auth', JSON.stringify({ user: mockUser }));
  });

  afterEach(() => {
    // Clean up
    localStorage.clear();
    jest.clearAllMocks();
  });

  test('Login route (/login) renders exactly one header', async () => {
    render(
      <TestWrapper initialRoute="/login">
        <App />
      </TestWrapper>
    );

    // Wait for component to render
    await screen.findByTestId('login-page');

    // Count header elements
    const headers = document.querySelectorAll('header');
    expect(headers).toHaveLength(1);
    
    // Verify it's the correct header
    expect(headers[0]).toHaveAttribute('data-testid', 'app-header');
  });

  test('Root route (/) renders exactly one header', async () => {
    render(
      <TestWrapper initialRoute="/">
        <App />
      </TestWrapper>
    );

    // Wait for component to render
    await screen.findByTestId('landing-page');

    // Count header elements
    const headers = document.querySelectorAll('header');
    expect(headers).toHaveLength(1);
    
    // Verify it's the correct header
    expect(headers[0]).toHaveAttribute('data-testid', 'app-header');
  });

  test('App dashboard (/app) renders exactly one header', async () => {
    render(
      <TestWrapper initialRoute="/app">
        <App />
      </TestWrapper>
    );

    // Wait for component to render
    await screen.findByTestId('dashboard');

    // Count header elements
    const headers = document.querySelectorAll('header');
    expect(headers).toHaveLength(1);
    
    // Verify it's the correct header
    expect(headers[0]).toHaveAttribute('data-testid', 'app-header');
  });

  test('Create league route (/app/leagues/new) renders exactly one header', async () => {
    render(
      <TestWrapper initialRoute="/app/leagues/new">
        <App />
      </TestWrapper>
    );

    // Wait for component to render
    await screen.findByTestId('create-league-wizard');

    // Count header elements
    const headers = document.querySelectorAll('header');
    expect(headers).toHaveLength(1);
    
    // Verify it's the correct header
    expect(headers[0]).toHaveAttribute('data-testid', 'app-header');
  });

  test('All headers have proper testid for identification', async () => {
    const routes = ['/login', '/', '/app', '/app/leagues/new'];
    
    for (const route of routes) {
      // Clear previous render
      document.body.innerHTML = '';
      
      render(
        <TestWrapper initialRoute={route}>
          <App />
        </TestWrapper>
      );

      // Wait a bit for render
      await new Promise(resolve => setTimeout(resolve, 100));

      // Check header has proper testid
      const headers = document.querySelectorAll('header');
      expect(headers).toHaveLength(1);
      expect(headers[0]).toHaveAttribute('data-testid', 'app-header');
    }
  });

  test('Header contract validation across all tested routes', async () => {
    const routes = [
      { path: '/login', expectation: 'MarketingShell header' },
      { path: '/', expectation: 'MarketingShell header' },
      { path: '/app', expectation: 'AppShell header' },
      { path: '/app/leagues/new', expectation: 'AppShell header' }
    ];

    for (const { path, expectation } of routes) {
      // Clear previous render
      document.body.innerHTML = '';
      
      const { container } = render(
        <TestWrapper initialRoute={path}>
          <App />
        </TestWrapper>
      );

      // Wait for render
      await new Promise(resolve => setTimeout(resolve, 100));

      // Validate exactly one header exists
      const headers = container.querySelectorAll('header');
      expect(headers).toHaveLength(1);
      
      // Validate header has required testid
      expect(headers[0]).toHaveAttribute('data-testid', 'app-header');
      
      console.log(`✅ ${path}: ${expectation} - exactly 1 header found`);
    }
  });
});