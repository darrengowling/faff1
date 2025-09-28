/**
 * Header Contract Tests
 * 
 * Ensures exactly one <header> element renders across all routes
 * to prevent duplicate header issues and overlay problems
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/translations';
import App from '../App';

// Mock components and dependencies to avoid external API calls
jest.mock('../components/GlobalNavbar', () => {
  return function MockGlobalNavbar() {
    return <header data-testid="mock-global-navbar">Mock Global Navbar</header>;
  };
});

jest.mock('../components/LoginPage', () => {
  return function MockLoginPage() {
    return (
      <div data-testid="login-page">
        <header data-testid="login-header">Login Header</header>
        <form>Login Form</form>
      </div>
    );
  };
});

jest.mock('../components/SimpleLandingPage', () => {
  return function MockLandingPage() {
    return (
      <div data-testid="landing-page">
        <header data-testid="landing-header">Landing Header</header>
        <main>Landing Content</main>
      </div>
    );
  };
});

jest.mock('../components/EnhancedHomeScreen', () => {
  return function MockDashboard() {
    return (
      <div data-testid="dashboard">
        <header data-testid="dashboard-header">Dashboard Header</header>
        <main>Dashboard Content</main>
      </div>
    );
  };
});

jest.mock('../components/CreateLeagueWizard', () => {
  return function MockCreateLeagueWizard() {
    return (
      <div data-testid="create-league-wizard">
        <header data-testid="wizard-header">Create League Header</header>
        <form>Create League Form</form>
      </div>
    );
  };
});

// Mock axios to avoid real API calls
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    }
  })),
  get: jest.fn(),
  post: jest.fn()
}));

// Test wrapper component
const TestWrapper = ({ children, initialRoute = '/' }) => {
  // Set initial route
  window.history.pushState({}, 'Test page', initialRoute);
  
  return (
    <BrowserRouter>
      <I18nextProvider i18n={i18n}>
        {children}
      </I18nextProvider>
    </BrowserRouter>
  );
};

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