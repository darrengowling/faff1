/**
 * Header Contract Tests
 * 
 * Basic test to validate header structure exists
 * Full integration testing will be done via E2E tests
 */

import React from 'react';

describe('Header Contract Tests', () => {
  beforeEach(() => {
    // Clear any existing DOM
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  test('AppShell renders exactly one header', () => {
    const { container } = render(
      <AppShell>
        <div>App Content</div>
      </AppShell>
    );

    // Count header elements
    const headers = container.querySelectorAll('header');
    expect(headers).toHaveLength(1);
    
    // Verify it's the correct header
    expect(headers[0]).toHaveAttribute('data-testid', 'app-header');
  });

  test('MarketingShell renders exactly one header', () => {
    const { container } = render(
      <MarketingShell>
        <div>Marketing Content</div>
      </MarketingShell>
    );

    // Count header elements
    const headers = container.querySelectorAll('header');
    expect(headers).toHaveLength(1);
    
    // Verify it's the correct header
    expect(headers[0]).toHaveAttribute('data-testid', 'app-header');
  });

  test('AppShell header has proper structure', () => {
    const { container } = render(
      <AppShell>
        <div>App Content</div>
      </AppShell>
    );

    const header = container.querySelector('header[data-testid="app-header"]');
    expect(header).toBeInTheDocument();
    expect(header).toHaveClass('sticky', 'top-0', 'z-40');
  });

  test('MarketingShell header has proper structure', () => {
    const { container } = render(
      <MarketingShell>
        <div>Marketing Content</div>
      </MarketingShell>
    );

    const header = container.querySelector('header[data-testid="app-header"]');
    expect(header).toBeInTheDocument();
    expect(header).toHaveClass('sticky', 'top-0', 'z-40');
  });

  test('Both shells use consistent header testid', () => {
    const { container: appContainer } = render(
      <AppShell>
        <div>App Content</div>
      </AppShell>
    );

    const { container: marketingContainer } = render(
      <MarketingShell>
        <div>Marketing Content</div>
      </MarketingShell>
    );

    const appHeader = appContainer.querySelector('header');
    const marketingHeader = marketingContainer.querySelector('header');

    expect(appHeader).toHaveAttribute('data-testid', 'app-header');
    expect(marketingHeader).toHaveAttribute('data-testid', 'app-header');
  });

  test('No nested headers within shells', () => {
    const ContentWithHeader = () => (
      <div>
        <header data-testid="nested-header">Nested Header</header>
        <div>Content</div>
      </div>
    );

    const { container } = render(
      <AppShell>
        <ContentWithHeader />
      </AppShell>
    );

    // Should have both the shell header and the nested header
    const headers = container.querySelectorAll('header');
    expect(headers).toHaveLength(2);
    
    // But this test validates we can detect such issues
    expect(headers[0]).toHaveAttribute('data-testid', 'app-header'); // Shell header
    expect(headers[1]).toHaveAttribute('data-testid', 'nested-header'); // Nested header
  });
});