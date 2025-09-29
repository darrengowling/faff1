export const TESTIDS = {
  // Auth
  loginHeader: 'login-header',
  authFormReady: 'auth-ready',
  authEmailInput: 'authEmailInput',
  authSubmitBtn: 'authSubmitBtn',
  authLoading: 'auth-loading',
  authError: 'auth-error',
  authSuccess: 'auth-success',
  backToHome: 'backToHome',
  homeNavButton: 'homeNavButton',
  
  // Legacy auth testids (for backward compatibility)
  emailInput: 'authEmailInput',
  magicLinkSubmit: 'authSubmitBtn',
  loginNowButton: 'dev-magic-link-btn',
  
  // Create league
  createDialog: 'create-dialog',
  createName: 'create-name',
  createSlots: 'create-slots',
  createBudget: 'create-budget',
  createMin: 'create-min',
  createMaxInput: 'create-max',
  createSubmit: 'createSubmit',
  createCancel: 'create-cancel',
  createSuccess: 'create-success',
  createLoading: 'create-loading',
  createError: 'create-error',
  
  // Lobby/Auction
  lobbyReady: 'lobby-ready',
  lobbyJoined: 'lobby-joined',
  lobbyJoinedCount: 'lobby-joined-count',
  lobbyMembersList: 'lobby-members-list',
  rulesBadge: 'rules-badge',
  startAuction: 'start-auction',
  backButton: 'back-button',
  
  // Invitations
  inviteEmailInput: 'invite-email-input',
  inviteSubmitButton: 'invite-submit-button',
  inviteLinkItem: 'invite-link-item',
  inviteLinkUrl: 'invite-link-url',
  inviteCopyButton: 'invite-copy-button',
  joinSuccessMessage: 'join-success-message',
  
  // Auction
  auctionAsset: 'auction-asset-name',
  auctionTimer: 'auction-timer',
  auctionTopBid: 'auction-top-bid',
  bidPlus1: 'bid-plus-1',
  soldBadge: 'lot-sold',
  
  // Nav / Mobile
  appHeader: 'app-header',
  mobileDrawer: 'nav-mobile-drawer',
  navCurrentHash: 'nav-current-hash',
  navHamburger: 'nav-hamburger',
  
  // Landing page CTAs
  landingCtaCreate: 'cta-create-league',
  landingCtaJoin: 'cta-join-league',
  
  // Landing page sections
  sectionHome: 'section-home',
  sectionHow: 'section-how', 
  sectionWhy: 'section-why',
  sectionFeatures: 'section-features',
  sectionSafety: 'section-safety',
  sectionFaq: 'section-faq',
  
  // Navigation items for mobile drawer
  navItemHome: 'nav-item-home',
  navItemHow: 'nav-item-how',
  navItemWhy: 'nav-item-why',
  navItemFeatures: 'nav-item-features',
  navItemSafety: 'nav-item-safety',
  navItemFaq: 'nav-item-faq',
  
  // Additional testids for compatibility
  homeNavButton: 'homeNavButton',
} as const;

export type TestIdKey = keyof typeof TESTIDS;
export default TESTIDS;