/**
 * Stable Test IDs for E2E Testing
 * 
 * Centralized constants for data-testid attributes used in Playwright tests.
 * These IDs should remain stable across UI changes to ensure reliable automation.
 */

export const TESTIDS = {
  // Home/Dashboard Create League CTAs
  homeCreateLeagueBtn: 'create-league-btn', // main CTA on /app
  navCreateLeagueBtn: 'nav-create-league-btn', // header "+ New League" button
  joinViaInviteBtn: 'join-via-invite-btn',

  // Create League Wizard - Single definitions
  createDialog: 'create-league-dialog',
  createName: 'create-name',
  createSlots: 'create-slots', 
  createBudget: 'create-budget',
  createMin: 'create-min',
  createMaxInput: 'create-max',
  createSubmit: 'create-submit',
  createCancel: 'create-cancel',
  
  // Create League Error States
  createErrorName: 'create-error-name',
  createErrorSlots: 'create-error-slots',
  createErrorBudget: 'create-error-budget',
  createErrorMin: 'create-error-min',
  
  // Authentication - Single definitions
  authEmailInput: 'auth-email-input',
  authSubmitBtn: 'auth-submit-btn',
  authError: 'auth-error',
  authSuccess: 'auth-success',
  authLoading: 'auth-loading',
  authFormReady: 'auth-ready',
  loginHeader: 'login-header',
  
  // Create League Form
  createLoading: 'create-loading',
  createError: 'create-error',
  
  // Navigation - Single definitions only
  navBrand: 'nav-brand',
  navHamburger: 'nav-hamburger',
  navSignIn: 'nav-sign-in',
  backToHome: 'back-to-home-link',
  mobileDrawer: 'nav-mobile-drawer',
  navMobileItemAuction: 'nav-mobile-item-auction-room',
  navMobileItemRoster: 'nav-mobile-item-my-roster',
  navMobileItemFixtures: 'nav-mobile-item-fixtures',
  navMobileItemLeaderboard: 'nav-mobile-item-leaderboard',
  navMobileItemSettings: 'nav-mobile-item-league-admin',
  
  // Landing Page
  landingCtaCreate: 'cta-create-league',
  landingCtaJoin: 'cta-join-league',
  inPageTabHome: 'tab-home',
  inPageTabWhy: 'tab-why',
  inPageTabHow: 'tab-how',
  inPageTabFair: 'tab-fair',
  inPageTabFaq: 'tab-faq',
  
  // Landing Page Sections
  sectionHome: 'section-home',
  sectionHow: 'section-how', 
  sectionWhy: 'section-why',
  sectionFeatures: 'section-features',
  sectionSafety: 'section-safety',
  sectionFaq: 'section-faq',
  
  // Branding
  AuthBrand: 'auth-brand',
  HeaderBrand: 'header-brand',
  MinimalBrand: 'minimal-brand',
  
  // Home/dashboard
  homeGotoDropdown: 'home-goto',
  homeGotoAuction: 'home-goto-auction',
  homeGotoRoster: 'home-goto-roster',
  homeGotoFixtures: 'home-goto-fixtures',
  homeGotoLeaderboard: 'home-goto-leaderboard',
  homeGotoSettings: 'home-goto-settings',
  createLeagueBtn: 'create-league-btn', // Legacy alias for homeCreateLeagueBtn
  
  // Navigation & Breadcrumbs
  breadcrumbHome: 'breadcrumb-home',
  backButton: 'back-button',
  backToHomeButton: 'back-to-home-button',

  // League Creation/Management (removed duplicates - using earlier definitions)
  
  // Auction
  auctionRoom: 'auction-room',
  auctionStatus: 'auction-status',
  auctionLot: 'auction-lot-number',
  auctionTopBidder: 'auction-top-bidder',
  auctionBudget: 'auction-budget',
  auctionSlots: 'auction-slots',
  auctionNextLot: 'auction-next-lot',
  nominateSelect: 'nominate-select',
  nominateSubmit: 'nominate-submit',
  bidInput: 'bid-input',
  bidSubmit: 'bid-submit',
  
  // Dashboard Actions  
  startAuctionBtn: 'start-auction',
  joinAuctionBtn: 'join-auction-btn',
  
  // Lobby & Auction Info
  lobbyReady: 'lobby-ready',
  lobbyJoined: 'lobby-joined',
  lobbyJoinedCount: 'lobby-joined-count',
  rulesBadge: 'rules-badge',

  // League List & Management
  leagueList: 'league-list',
  leagueItem: 'league-item',
  leagueCreate: 'league-create',
  leagueJoin: 'league-join',
  leagueInviteCode: 'league-invite-code',
  leagueInviteSubmit: 'league-invite-submit',
  inviteEmailInput: 'invite-email-input',
  inviteEmailSubmit: 'invite-email-submit',
  inviteLinkCopy: 'invite-link-copy',
  inviteLinkItem: 'invite-link-0',
  inviteLinkShare: 'invite-link-share',

  // Roster/Club Management
  clubList: 'club-list',
  clubBudget: 'club-budget',
  clubSlots: 'club-slots',

  // Leaderboard
  leaderboardTable: 'leaderboard-table',
  leaderboardManager: 'leaderboard-manager',
  // Note: leaderboardGoals, leaderboardWins, leaderboardDraws removed as they're not implemented in current scoring system

  // Admin Dashboard
  adminSettings: 'admin-settings',
  adminSaveBtn: 'admin-save-btn',
  adminCloseBtn: 'admin-close-btn',
  adminUndoBtn: 'admin-undo-btn',
  
  // UI Components
  loadingSpinner: 'loading-spinner',
  errorMessage: 'error-message',
  toastMessage: 'toast-message',
  dialogClose: 'dialog-close',
  dialogOverlay: 'dialog-overlay',
  confirmBtn: 'confirm-btn',
  cancelBtn: 'cancel-btn',
  alertConfirm: 'alert-confirm',
  alertCancel: 'alert-cancel',
  
  // Quick Actions
  quickJoinLeague: 'quick-join-league',

  // Missing auction testids
  auctionAssetName: 'auction-asset-name',
  auctionTimer: 'auction-timer', 
  auctionTopBid: 'auction-top-bid',
  closeLotButton: 'close-lot-button',
  nextLotButton: 'next-lot-button',
  nominateBtn: 'nominate-btn',
  soldBadge: 'sold-badge',
  undoButton: 'undo-button',

  // Missing roster testids  
  rosterEmpty: 'roster-empty',
  rosterItem: 'roster-item',
  rosterItemName: 'roster-item-name', 
  rosterItemPrice: 'roster-item-price',
  rosterList: 'roster-list',

  // Missing budget/slots testids
  budgetRemaining: 'budget-remaining',
  budgetDisplay: 'budget-display',
  slotsDisplay: 'slots-display', 
  slotsRemaining: 'slots-remaining',
  yourBudget: 'your-budget',
  yourSlotsRemaining: 'your-slots-remaining',

  // Missing invite testids
  inviteLinkUrl: 'invite-link-url',
  inviteSubmitButton: 'invite-submit-button', 
  joinLeagueButton: 'join-league-button',

  // Missing admin testids
  adminPanel: 'admin-panel',

  // Missing hardcoded testids (removed duplicates - using earlier definitions)
  backToHome: 'back-to-home-link',
  
  // App navigation testids
  appHeader: 'app-header',
  homeNavButton: 'home-nav-button',
  
  // Mobile drawer testids
  mobileDrawer: 'nav-mobile-drawer',

  // Navigation item testids
  navItemHome: 'nav-item-home',
  navItemHow: 'nav-item-how',
  navItemWhy: 'nav-item-why',
  navItemFeatures: 'nav-item-features',
  navItemSafety: 'nav-item-safety',
  navItemFaq: 'nav-item-faq',
  navItemAuction: 'nav-item-auction',
  navItemRoster: 'nav-item-roster',
  navItemDashboard: 'nav-item-dashboard',
  navItemLeaderboard: 'nav-item-leaderboard',

  // Hash navigation
  navCurrentHash: 'nav-current-hash',

  // Missing testids from tests
  auctionTitle: 'auction-title',
  authRequiredToast: 'auth-required-toast',
  backToHomeLink: 'back-to-home-link',
  clubCount: 'club-count',
  clubName: 'club-name',
  connectionStatus: 'connection-status',
  createDialogLegacy: 'create-dialog', // Legacy - use createDialog instead 
  createSuccess: 'create-success',
  currentLot: 'current-lot',
  joinLeagueBtn: 'join-league-btn',
  leagueSettings: 'league-settings',
  memberCount: 'member-count',
  ownedClub: 'owned-club',
  placeBidBtn: 'place-bid-btn',
  placeBidButton: 'place-bid-button',
  stickyPageNav: 'sticky-page-nav',
  timer: 'timer',
  timerDisplay: 'timer-display',
  totalPoints: 'total-points',
  userBudget: 'user-budget',
  userMenu: 'user-menu',
} as const;

// Type for testid values (for TypeScript safety)
export type TestId = typeof TESTIDS[keyof typeof TESTIDS];

export default TESTIDS;