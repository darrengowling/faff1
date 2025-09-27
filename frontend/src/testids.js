/**
 * Test IDs for Playwright E2E Tests
 * @deprecated Use testids.ts instead
 */

// Re-export from TypeScript file for backward compatibility
export { TESTIDS } from './testids.ts';

// Legacy export (to be removed)
const LEGACY_TESTIDS = {
  // Global navigation & landing
  navBrand: 'nav-brand',
  
  // Brand components
  HeaderBrand: 'header-brand',
  AuthBrand: 'auth-brand',
  MinimalBrand: 'minimal-brand',
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
  navSignIn: 'nav-sign-in',
  navGetStarted: 'nav-get-started',
  
  // Landing page
  landingCtaCreate: 'cta-create-league',
  landingCtaJoin: 'cta-join-league',
  inPageTabHome: 'tab-home',
  inPageTabHow: 'tab-how',
  inPageTabWhy: 'tab-why',
  inPageTabFeatures: 'tab-features',
  inPageTabFair: 'tab-fair',
  inPageTabFaq: 'tab-faq',
  
  // Authentication
  emailInput: 'auth-email-input',
  magicLinkSubmit: 'auth-magic-link-submit',
  loginNowButton: 'auth-login-now-button',
  
  // Authentication Page (/login)
  authEmailInput: 'auth-email-input',
  authSubmitBtn: 'auth-submit-btn',
  authError: 'auth-error',
  authSuccess: 'auth-success',
  
  // Home/dashboard
  homeGotoDropdown: 'home-goto',
  homeGotoAuction: 'home-goto-auction',
  homeGotoRoster: 'home-goto-roster',
  homeGotoFixtures: 'home-goto-fixtures',
  homeGotoLeaderboard: 'home-goto-leaderboard',
  homeGotoSettings: 'home-goto-settings',
  createLeagueBtn: 'create-league-btn',
  
  // Navigation & Breadcrumbs
  breadcrumbHome: 'breadcrumb-home',
  backButton: 'back-button',
  backToHomeButton: 'back-to-home-button',
  
  // League creation
  createDialog: 'create-league-dialog',
  createNameInput: 'create-name',
  createSlotsInput: 'create-slots',
  createBudgetInput: 'create-budget',
  createMinInput: 'create-min',
  createMaxInput: 'create-max',
  createSubmit: 'create-submit',
  createCancel: 'create-cancel',
  
  // League management & invites
  inviteEmailInput: 'invite-email-input',
  inviteSubmitButton: 'invite-submit-btn',
  inviteCopyButton: 'invite-copy',
  inviteLinkItem: 'invite-link-0',
  inviteLinkUrl: 'invite-link-url',
  lobbyJoinedCount: 'lobby-joined',
  lobbyMembersList: 'lobby-members-list',
  startAuctionBtn: 'start-auction',
  
  // Join flow
  joinLeagueButton: 'join-league-btn',
  joinSuccessMessage: 'join-success-msg',
  
  // Auction room
  auctionRoom: 'auction-room',
  auctionAssetName: 'auction-asset-name',
  auctionTimer: 'auction-timer',
  auctionTopBid: 'auction-top-bid',
  auctionTopBidder: 'auction-top-bidder',
  nominateBtn: 'nominate-btn',
  nominateSelect: 'nominate-select',
  nominateSubmit: 'nominate-submit',
  bidInput: 'bid-input',
  bidSubmit: 'bid-submit',
  bidPlus1: 'bid-plus-1',
  bidPlus5: 'bid-plus-5',
  bidPlus10: 'bid-plus-10',
  soldBadge: 'lot-sold',
  yourBudget: 'your-budget',
  yourSlotsRemaining: 'your-slots-remaining',
  auctionStatus: 'auction-status',
  lotNumber: 'lot-number',
  nextLotButton: 'next-lot-btn',
  closeLotButton: 'close-lot-btn',
  undoButton: 'undo-btn',
  
  // Roster & clubs
  rosterList: 'roster-list',
  rosterItem: 'roster-item',
  rosterItemName: 'roster-item-name',
  rosterItemPrice: 'roster-item-price',
  rosterEmpty: 'roster-empty',
  budgetDisplay: 'budget-display',
  budgetUsed: 'budget-used',
  budgetRemaining: 'budget-remaining',
  slotsDisplay: 'slots-display',
  slotsUsed: 'slots-used',
  slotsRemaining: 'slots-remaining',
  
  // Leaderboard
  leaderboardTable: 'leaderboard-table',
  leaderboardRow: 'leaderboard-row',
  leaderboardPosition: 'leaderboard-position',
  leaderboardManager: 'leaderboard-manager',
  leaderboardPoints: 'leaderboard-points',
  leaderboardGoals: 'leaderboard-goals',
  leaderboardWins: 'leaderboard-wins',
  leaderboardDraws: 'leaderboard-draws',
  
  // Fixtures
  fixturesTable: 'fixtures-table',
  fixtureRow: 'fixture-row',
  fixtureHomeTeam: 'fixture-home-team',
  fixtureAwayTeam: 'fixture-away-team',
  fixtureScore: 'fixture-score',
  fixtureStatus: 'fixture-status',
  
  // Admin/Settings
  adminPanel: 'admin-panel',
  adminTab: 'admin-tab',
  adminOverview: 'admin-overview',
  adminLeagueSettings: 'admin-league-settings',
  adminMemberManagement: 'admin-member-management',
  adminAuctionControl: 'admin-auction-control',
  settingsForm: 'settings-form',
  settingsSave: 'settings-save',
  
  // Error states
  errorMessage: 'error-message',
  loadingSpinner: 'loading-spinner',
  emptyState: 'empty-state',
  
  // Notifications/Toasts
  successToast: 'success-toast',
  errorToast: 'error-toast',
  infoToast: 'info-toast',
  
  // General UI elements
  modal: 'modal',
  modalClose: 'modal-close',
  confirmButton: 'confirm-button',
  cancelButton: 'cancel-button',
  submitButton: 'submit-button',
  backButton: 'back-button',
  
} // End of LEGACY_TESTIDS object

// Utility function to get test ID selector
export const getTestId = (testId) => `[data-testid="${TESTIDS[testId]}"]`;

// Utility function to create test ID attribute
export const testId = (id) => ({ 'data-testid': TESTIDS[id] });