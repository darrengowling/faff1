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

  // Create League Wizard  
  createLeagueWizardName: 'create-name',
  createLeagueWizardSlots: 'create-slots', 
  createLeagueWizardBudget: 'create-budget',
  createLeagueWizardMin: 'create-min',
  createLeagueWizardSubmit: 'create-submit',
  
  // League creation (Dialog)
  createDialog: 'create-league-dialog',
  createNameInput: 'create-name',
  createSlotsInput: 'create-slots',
  createBudgetInput: 'create-budget',
  createMinInput: 'create-min',
  createMaxInput: 'create-max',
  createSubmit: 'create-submit',
  createCancel: 'create-cancel',
  
  // Create League Error States
  createErrorName: 'create-error-name',
  createErrorSlots: 'create-error-slots',
  createErrorBudget: 'create-error-budget',
  createErrorMin: 'create-error-min',
  
  // Authentication (Legacy - use auth* versions instead)
  emailInput: 'auth-email-input', // Legacy: use authEmailInput instead
  magicLinkSubmit: 'auth-magic-link-submit', // Legacy: use authSubmitBtn instead
  loginNowButton: 'auth-login-now-button', // Legacy: use dev-magic-link-btn directly
  
  // Authentication Page (/login) - Current
  authEmailInput: 'auth-email-input',
  authSubmitBtn: 'auth-submit-btn',
  authError: 'auth-error',
  authSuccess: 'auth-success',
  authLoading: 'auth-loading',
  
  // Create League Form
  createLoading: 'create-loading',
  createError: 'create-error',
  
  // Navigation
  navBrand: 'nav-brand',
  navSignIn: 'nav-sign-in',
  navDropdownProduct: 'nav-dd-product',
  navDdAuction: 'nav-dd-auction',
  navDdRoster: 'nav-dd-roster',
  navDdFixtures: 'nav-dd-fixtures',
  navDdLeaderboard: 'nav-dd-leaderboard',
  navDdSettings: 'nav-dd-settings',
  navDropdownItemAuction: 'nav-dd-auction', // Legacy alias
  navDropdownItemRoster: 'nav-dd-roster', // Legacy alias
  navDropdownItemFixtures: 'nav-dd-fixtures', // Legacy alias
  navDropdownItemLeaderboard: 'nav-dd-leaderboard', // Legacy alias
  navDropdownItemSettings: 'nav-dd-settings', // Legacy alias
  navHamburger: 'nav-hamburger',
  navMobileDrawer: 'nav-mobile-drawer',
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

  // League Creation/Management
  createSubmit: 'create-submit',
  createCancel: 'create-cancel',
  
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
  yourBudget: 'your-budget',
  yourSlotsRemaining: 'your-slots-remaining',

  // Missing invite testids
  inviteLinkUrl: 'invite-link-url',
  inviteSubmitButton: 'invite-submit-button', 
  joinLeagueButton: 'join-league-button',

  // Missing admin testids
  adminPanel: 'admin-panel',

  // Missing hardcoded testids
  loginHeader: 'login-header',
  devMagicLinkBtn: 'dev-magic-link-btn',
} as const;

// Type for testid values (for TypeScript safety)
export type TestId = typeof TESTIDS[keyof typeof TESTIDS];

export default TESTIDS;