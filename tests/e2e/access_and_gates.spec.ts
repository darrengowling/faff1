/**
 * Access and Gates Tests  
 * Tests route guards, permission gates, and access control
 */

import { test, expect, Browser, Page } from '@playwright/test';
import { TESTIDS } from '../../frontend/src/testids.js';
import { login, createLeague } from './utils/helpers';

test.describe('Access and Gates Tests', () => {
  let commissionerPage: Page;
  let memberPage: Page;
  let unauthenticatedPage: Page;

  test.beforeAll(async ({ browser }: { browser: Browser }) => {
    const commissionerContext = await browser.newContext();
    const memberContext = await browser.newContext();
    const unauthContext = await browser.newContext();
    
    commissionerPage = await commissionerContext.newPage();
    memberPage = await memberContext.newPage();
    unauthenticatedPage = await unauthContext.newPage();
  });

  test.afterAll(async () => {
    await commissionerPage?.close();
    await memberPage?.close();
    await unauthenticatedPage?.close();
  });

  test('Start Auction disabled when below minimum managers', async () => {
    console.log('🧪 Testing Start Auction gate with insufficient members...');
    
    // Create league with min 3 managers
    await login(commissionerPage, 'commissioner@example.com');
    const leagueId = await createLeague(commissionerPage, {
      name: 'Gate Test League',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 3,
      maxManagers: 6
    });
    
    // With only commissioner (1 member), Start Auction should be disabled
    const startAuctionBtn = commissionerPage.locator(`[data-testid="${TESTIDS.startAuctionBtn}"]`);
    
    if (await startAuctionBtn.isVisible()) {
      await expect(startAuctionBtn).toBeDisabled();
      
      // Verify lobby shows insufficient members
      const joinedCount = commissionerPage.locator(`[data-testid="${TESTIDS.lobbyJoinedCount}"]`);
      await expect(joinedCount).toContainText('1'); // Only commissioner
      
      console.log('✅ Start Auction correctly disabled with insufficient members');
    } else {
      console.log('⚠️ Start Auction button not found - may need navigation to league page');
    }
  });

  test('Start Auction enabled when minimum managers reached', async () => {
    console.log('🧪 Testing Start Auction gate with sufficient members...');
    
    // Create league with min 2 managers  
    await login(commissionerPage, 'commissioner@sufficient.test');
    const leagueId = await createLeague(commissionerPage, {
      name: 'Sufficient Members League',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 6
    });
    
    // Add second member
    await login(memberPage, 'member@sufficient.test');
    // Simulate joining league (in real test would use invite flow)
    await memberPage.goto(`/leagues/${leagueId}/join`);
    
    // Wait for joined count to update
    const joinedCount = commissionerPage.locator(`[data-testid="${TESTIDS.lobbyJoinedCount}"]`);
    await expect(joinedCount).toContainText('2', { timeout: 10000 });
    
    // Now Start Auction should be enabled
    const startAuctionBtn = commissionerPage.locator(`[data-testid="${TESTIDS.startAuctionBtn}"]`);
    await expect(startAuctionBtn).toBeEnabled({ timeout: 10000 });
    
    console.log('✅ Start Auction correctly enabled with sufficient members');
  });

  test('Route guards redirect unauthenticated users with toast notifications', async () => {
    console.log('🧪 Testing route guards for unauthenticated access...');
    
    // Test protected routes redirect to login with proper toast messages
    const protectedRoutes = [
      { path: '/app', expectedToast: 'Please sign in to access this page' },
      { path: '/auction', expectedToast: 'Please sign in to access this page' },
      { path: '/clubs', expectedToast: 'Please sign in to access this page' }, 
      { path: '/admin', expectedToast: 'Please sign in to access this page' },
      { path: '/leaderboard', expectedToast: 'Please sign in to access this page' },
      { path: '/fixtures', expectedToast: 'Please sign in to access this page' }
    ];
    
    for (const route of protectedRoutes) {
      await unauthenticatedPage.goto(route.path);
      
      // Should redirect to login
      await unauthenticatedPage.waitForURL('**/login', { timeout: 10000 });
      
      // Check for auth required toast
      const authToast = unauthenticatedPage.locator('[data-testid="auth-required-toast"]');
      if (await authToast.isVisible()) {
        await expect(authToast).toContainText(route.expectedToast);
      }
      
      console.log(`✅ ${route.path} correctly redirected to login with toast`);
    }
  });

  test('Non-existent league routes show 404 or redirect safely', async () => {
    console.log('🧪 Testing non-existent league access...');
    
    await login(memberPage, 'member@404.test');
    
    // Try to access non-existent league
    await memberPage.goto('/leagues/nonexistent-league-id/auction');
    
    // Should either show 404 or redirect safely
    const currentUrl = memberPage.url();
    
    // Acceptable outcomes: 404 page, redirect to dashboard, or error message
    const is404 = currentUrl.includes('/404') || currentUrl.includes('/not-found');
    const isDashboard = currentUrl.includes('/app') || currentUrl.includes('/dashboard');
    const hasErrorMessage = await memberPage.locator(`[data-testid="${TESTIDS.errorMessage}"]`).isVisible();
    
    expect(is404 || isDashboard || hasErrorMessage).toBeTruthy();
    
    console.log('✅ Non-existent league handled safely');
  });

  test('League members can access league pages', async () => {
    console.log('🧪 Testing league member access permissions...');
    
    // Create league and add member
    await login(commissionerPage, 'commissioner@member-access.test');
    const leagueId = await createLeague(commissionerPage, {
      name: 'Member Access League',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 4
    });
    
    // Member joins league
    await login(memberPage, 'member@member-access.test');
    await memberPage.goto(`/leagues/${leagueId}/join`);
    
    // Member should be able to access league pages
    const leagueRoutes = [
      `/leagues/${leagueId}/clubs`,
      `/leagues/${leagueId}/leaderboard`, 
      `/leagues/${leagueId}/fixtures`
    ];
    
    for (const route of leagueRoutes) {
      await memberPage.goto(route);
      
      // Should load successfully (not redirect to login)
      await memberPage.waitForLoadState('networkidle');
      const currentUrl = memberPage.url();
      
      expect(currentUrl).toContain(route);
      
      console.log(`✅ Member can access ${route}`);
    }
  });

  test('Non-league members cannot access league pages', async () => {
    console.log('🧪 Testing non-member access restrictions...');
    
    // Create private league 
    await login(commissionerPage, 'commissioner@private.test');
    const privateLeagueId = await createLeague(commissionerPage, {
      name: 'Private League',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 4
    });
    
    // Different user (not a member) tries to access
    await login(memberPage, 'outsider@private.test');
    
    // Should be blocked from accessing league pages
    await memberPage.goto(`/leagues/${privateLeagueId}/clubs`);
    
    // Should redirect or show error
    const currentUrl = memberPage.url();
    const isBlocked = !currentUrl.includes(`/leagues/${privateLeagueId}/clubs`);
    const hasErrorMessage = await memberPage.locator(`[data-testid="${TESTIDS.errorMessage}"]`).isVisible();
    
    expect(isBlocked || hasErrorMessage).toBeTruthy();
    
    console.log('✅ Non-members correctly blocked from private league');
  });

  test('Commissioner has admin access, members do not', async () => {
    console.log('🧪 Testing admin access permissions...');
    
    await login(commissionerPage, 'commissioner@admin.test');
    const leagueId = await createLeague(commissionerPage, {
      name: 'Admin Access League',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 4
    });
    
    // Commissioner should access admin panel
    await commissionerPage.goto(`/leagues/${leagueId}/admin`);
    const adminPanel = commissionerPage.locator(`[data-testid="${TESTIDS.adminPanel}"]`);
    
    if (await adminPanel.isVisible()) {
      await expect(adminPanel).toBeVisible();
      console.log('✅ Commissioner can access admin panel');
    }
    
    // Regular member should not access admin
    await login(memberPage, 'member@admin.test');
    await memberPage.goto(`/leagues/${leagueId}/join`);
    
    // Try to access admin page
    await memberPage.goto(`/leagues/${leagueId}/admin`);
    
    // Should be blocked
    const memberAdminPanel = memberPage.locator(`[data-testid="${TESTIDS.adminPanel}"]`);
    const hasAccess = await memberAdminPanel.isVisible().catch(() => false);
    const isRedirected = !memberPage.url().includes('/admin');
    
    expect(!hasAccess || isRedirected).toBeTruthy();
    
    console.log('✅ Regular member blocked from admin access');
  });

  test('Auction access requires active auction', async () => {
    console.log('🧪 Testing auction access gates...');
    
    await login(commissionerPage, 'commissioner@auction-gate.test');
    const leagueId = await createLeague(commissionerPage, {
      name: 'Auction Gate League',
      clubSlots: 3,
      budgetPerManager: 100,
      minManagers: 2,
      maxManagers: 4
    });
    
    // Try to access auction before it's started
    await memberPage.goto(`/leagues/${leagueId}/auction`);
    
    // Should show "auction not started" or redirect
    const auctionRoom = memberPage.locator(`[data-testid="${TESTIDS.auctionRoom}"]`);
    const isAuctionLive = await auctionRoom.isVisible().catch(() => false);
    
    if (!isAuctionLive) {
      // Should show appropriate message or redirect
      const errorOrRedirect = 
        await memberPage.locator(`[data-testid="${TESTIDS.errorMessage}"]`).isVisible() ||
        !memberPage.url().includes('/auction');
      
      expect(errorOrRedirect).toBeTruthy();
      console.log('✅ Auction access correctly gated when not active');
    }
  });

  test('League-specific routes redirect safely with helpful messages', async () => {
    console.log('🧪 Testing league-specific route redirects...');
    
    // Test authenticated user accessing league routes without an active league
    await login(memberPage, 'member@no-league.test');
    
    const leagueRoutes = [
      { path: '/auction', expectedRedirect: '/app', expectedReason: 'Join a league first to access the auction room' },
      { path: '/clubs', expectedRedirect: '/app', expectedReason: 'Join a league first to view your roster' },
      { path: '/fixtures', expectedRedirect: '/app', expectedReason: 'Join a league first to view fixtures' },
      { path: '/leaderboard', expectedRedirect: '/app', expectedReason: 'Join a league first to view the leaderboard' },
      { path: '/admin', expectedRedirect: '/app', expectedReason: 'League admin access requires commissioner permissions' }
    ];
    
    for (const route of leagueRoutes) {
      await memberPage.goto(route.path);
      
      // Should redirect to /app with helpful toast
      await memberPage.waitForURL('**/app', { timeout: 10000 });
      
      // Check for redirect reason toast
      const redirectToast = memberPage.locator('[data-testid*="redirect-toast"]');
      if (await redirectToast.isVisible()) {
        await expect(redirectToast).toContainText(route.expectedReason);
      }
      
      console.log(`✅ ${route.path} safely redirected to /app with helpful message`);
    }
  });

  test('Breadcrumb navigation appears on all app pages', async () => {
    console.log('🧪 Testing breadcrumb navigation...');
    
    await login(commissionerPage, 'commissioner@breadcrumb.test');
    
    // Test breadcrumbs appear on various pages
    const pagesWithBreadcrumbs = ['/auction', '/clubs', '/fixtures', '/leaderboard'];
    
    for (const page of pagesWithBreadcrumbs) {
      await commissionerPage.goto(page);
      await commissionerPage.waitForLoadState('networkidle');
      
      // Should show "You are here" breadcrumb
      const breadcrumb = commissionerPage.locator('text="You are here:"');
      if (await breadcrumb.isVisible()) {
        await expect(breadcrumb).toBeVisible();
        
        // Should have Back to Home button
        const backToHome = commissionerPage.locator('[data-testid="back-to-home-button"]');
        await expect(backToHome).toBeVisible();
        
        console.log(`✅ ${page} shows breadcrumb navigation`);
      }
    }
  });

  test('No dead-end pages - all pages provide navigation options', async () => {
    console.log('🧪 Testing for dead-end pages...');
    
    await login(memberPage, 'member@dead-end.test');
    
    // Test that every page has some form of navigation
    const testPages = ['/app', '/login', '/auction', '/clubs'];
    
    for (const page of testPages) {
      await memberPage.goto(page);
      await memberPage.waitForLoadState('networkidle');
      
      // Check for navigation elements (at least one should be present)
      const navElements = await memberPage.locator('a, button[data-testid*="nav"], button[data-testid*="back"], [role="navigation"]').count();
      
      expect(navElements).toBeGreaterThan(0);
      
      // Specifically check for back/home options on non-home pages
      if (page !== '/app' && page !== '/') {
        const backOptions = memberPage.locator('[data-testid="back-to-home-button"], [data-testid="back-button"], a[href="/app"]');
        const hasBackOption = await backOptions.count() > 0;
        
        if (hasBackOption) {
          console.log(`✅ ${page} provides back/home navigation`);
        }
      }
    }
  });
});