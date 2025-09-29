export const TESTIDS = {
  // Auth
  loginHeader: 'login-header',
  authFormReady: 'auth-ready',
  authEmailInput: 'authEmailInput',
  authSubmitBtn: 'authSubmitBtn',
  authLoading: 'auth-loading',
  authError: 'auth-error',
  authSuccess: 'auth-success',
  backToHome: 'back-to-home-link',
  homeNavButton: 'home-nav-button',
  // Create league
  createName: 'create-name',
  createSlots: 'create-slots',
  createBudget: 'create-budget',
  createMin: 'create-min',
  createSubmit: 'create-submit',
  createSuccess: 'create-success',
  // Lobby/Auction
  lobbyJoined: 'lobby-joined',
  rulesBadge: 'rules-badge',
  startAuction: 'start-auction',
  auctionAsset: 'auction-asset-name',
  auctionTimer: 'auction-timer',
  auctionTopBid: 'auction-top-bid',
  bidPlus1: 'bid-plus-1',
  soldBadge: 'lot-sold',
  // Nav / Mobile
  appHeader: 'app-header',
  mobileDrawer: 'nav-mobile-drawer',
  navCurrentHash: 'nav-current-hash',
} as const;

export type TestIdKey = keyof typeof TESTIDS;
export default TESTIDS;