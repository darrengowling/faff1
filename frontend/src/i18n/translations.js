/**
 * Translation keys for Friends of PIFA application
 * Organized by feature/component areas for maintainability
 */

export const translations = {
  // Common/Generic terms
  common: {
    loading: "Loading...",
    back: "Back",
    cancel: "Cancel",
    save: "Save",
    edit: "Edit", 
    delete: "Delete",
    confirm: "Confirm",
    close: "Close",
    retry: "Retry",
    refresh: "Refresh",
    settings: "Settings",
    search: "Search",
    filter: "Filter",
    sort: "Sort",
    error: "Error",
    success: "Success",
    warning: "Warning",
    info: "Info",
    yes: "Yes",
    no: "No",
    submit: "Submit",
    continue: "Continue",
    next: "Next",
    previous: "Previous",
    finish: "Finish",
    skip: "Skip",
    logout: "Logout",
    login: "Login",
    register: "Register",
    email: "Email",
    password: "Password",
    name: "Name",
    date: "Date",
    time: "Time",
    status: "Status"
  },

  // Authentication
  auth: {
    loginTitle: "{{brandName}}", // Dynamic brand name
    loginSubtitle: "Enter your email to get started",
    sendMagicLink: "Send Magic Link",
    sending: "Sending...",
    magicLinkReady: "Magic Link Ready!",
    checkEmail: "Check Your Email",
    developmentMode: "Development Mode",
    developmentLoginText: "Click the button below to login instantly:",
    loginNow: "🚀 Login Now",
    copyLink: "📋 Copy Link",
    orCopyLink: "Or copy this link:",
    magicLinkCopied: "Magic link copied to clipboard!",
    magicLinkSent: "Magic link sent! Check your email.",
    sendAnotherLink: "← Send Another Link",
    verifyingLogin: "Verifying your login...",
    loginSuccess: "Successfully logged in!",
    invalidToken: "Invalid or expired token",
    invalidMagicLink: "Invalid or expired magic link",
    backToLogin: "Back to Login",
    emailNotVerified: "Email Not Verified",
    verifyEmailPrompt: "Please verify your email address to continue."
  },

  // Navigation & Headers
  nav: {
    dashboard: "Dashboard",
    myClubs: "My Clubs",
    fixtures: "Fixtures & Results", 
    leaderboard: "Leaderboard",
    auction: "Auction",
    admin: "Admin",
    appName: "{{brandName}}", // Dynamic brand name
    fixturesResults: "{{brandName}} Fixtures & Results", // Dynamic
    backToDashboard: "Back to Dashboard",
    manageLeague: "Manage League",
    goToDashboard: "Go to Dashboard"
  },

  // Dashboard & Leagues
  dashboard: {
    myLeagues: "My Leagues",
    createLeague: "Create League",
    noLeaguesYet: "No Leagues Yet",
    createFirstLeague: "Create your first league to start auctioning football clubs!",
    members: "Members",
    budget: "Budget",
    clubSlots: "Club Slots",
    credits: "credits",
    commissioner: "Commissioner",
    startAuction: "Start Auction",
    joinAuction: "Join Auction",
    season: "Season",
    viewAuction: "View Auction",
    ready: "ready"
  },

  // League Creation
  leagueCreation: {
    createNewLeague: "Create New League",
    leagueName: "League Name",
    leagueNamePlaceholder: "European Competition 2025-26",
    competitionTemplate: "Competition Template",
    templateDescription: "Choose a template to set default values. You can customize them below.",
    leagueSettings: "League Settings",
    budgetPerManager: "Budget per Manager",
    clubSlotsPerManager: "Club Slots per Manager",
    minBidIncrement: "Min Bid Increment",
    bidTimer: "Bid Timer (seconds)",
    minManagers: "Min Managers", 
    maxManagers: "Max Managers",
    scoringRules: "Scoring Rules",
    pointsPerGoal: "Points per Goal",
    pointsPerWin: "Points per Win",
    pointsPerDraw: "Points per Draw",
    creating: "Creating...",
    leagueCreatedSuccess: "League created successfully!"
  },

  // League Management
  leagueManagement: {
    leagueStatus: "League Status",
    minRequired: "Min Required",
    maxAllowed: "Max Allowed",
    leagueReady: "🎉 League is ready! You can now start the auction when all members are prepared.",
    invitations: "Invitations",
    inviteEmailPlaceholder: "manager@example.com",
    noInvitationsSent: "No invitations sent yet",
    invitationSent: "Invitation sent successfully!",
    resendInvitation: "Resend invitation",
    processingInvitation: "Processing invitation...",
    welcomeToLeague: "Welcome to the League!",
    joinedSuccessfully: "You've successfully joined",
    redirectingToDashboard: "Redirecting to dashboard...",
    failedToAcceptInvitation: "Failed to accept invitation",
    noInvitationToken: "No invitation token provided"
  },

  // Invitation statuses
  invitationStatus: {
    pending: "pending",
    accepted: "accepted", 
    expired: "expired"
  },

  // Auction Room
  auction: {
    connectingToAuction: "Connecting to auction...",
    auctionLoading: "Auction Loading",
    waitingToBegin: "Waiting for auction to begin...",
    currentBid: "Current Bid",
    topBidder: "Top Bidder",
    noBids: "No Bids",
    timeLeft: "Time Left",
    timeRemaining: "Time Remaining",
    placeBid: "Place Bid",
    bidding: "Bidding...",
    enterBidAmount: "Enter bid amount",
    insufficientBudget: "⚠️ Insufficient budget (You have {budget} credits)",
    yourWallet: "Your Wallet",
    budgetLabel: "Budget:",
    slotsUsed: "Slots Used:",
    budgetReminder: "Remember: You must be able to fill remaining slots at minimum price!",
    managersCount: "Managers ({count})",
    chat: "Chat",
    typeChatMessage: "Type a message...",
    sendMessage: "Send message",
    pause: "Pause",
    resume: "Resume",
    auctionPaused: "Auction paused by commissioner",
    auctionResumed: "Auction resumed",
    auctionCompleted: "Auction completed!",
    userJoinedAuction: "{displayName} joined the auction",
    userLeftAuction: "{displayName} left the auction",
    bidPlaced: "Bid placed: {amount} credits",
    bidFailed: "Bid failed: {error}",
    bidMustBeHigher: "Bid must be higher than current bid",
    live: "LIVE",
    disconnected: "DISCONNECTED"
  },

  // Auction Statuses
  auctionStatus: {
    open: "BIDDING OPEN",
    goingOnce: "GOING ONCE!",
    goingTwice: "GOING TWICE!",
    sold: "SOLD!",
    unsold: "UNSOLD",
    waiting: "WAITING"
  },

  // Connection Status
  connection: {
    connected: "Connected",
    connecting: "Connecting...",
    reconnecting: "Reconnecting... ({attempts}/{maxAttempts})",
    offline: "Offline",
    unknown: "Unknown",
    connectionLost: "Connection lost. Please refresh the page."
  },

  // My Clubs
  myClubs: {
    title: "My Clubs",
    ownedClubs: "Owned Clubs ({count})",
    budgetRemaining: "Budget Remaining",
    slotsAvailable: "Slots Available",
    goToAuction: "Go to Auction",
    upcomingFixtures: "Upcoming Fixtures", 
    recentResults: "Recent Results",
    yourClubs: "Your Clubs",
    clubsCount: "{current} / {total} Clubs",
    final: "FINAL",
    matchday: "Matchday {number}",
    points: "pts",
    loadingClubs: "Loading your clubs..."
  },

  // Empty States for My Clubs
  myClubsEmpty: {
    noClubsYet: "No Clubs Owned Yet",
    noClubsDescription: "You haven't acquired any clubs yet. Join the auction to build your football squad and compete for points!",
    noFixtures: "No Fixtures Scheduled", 
    noFixturesDescription: "The competition fixtures haven't been loaded yet. Check back soon for the match schedule!",
    noResults: "No Results Yet",
    noResultsDescription: "Match results will appear here once games are completed and scores are recorded."
  },

  // Fixtures
  fixtures: {
    title: "UCL Fixtures & Results",
    groupStage: "Group Stage",
    roundOf16: "Round of 16",
    quarterFinals: "Quarter Finals",
    semiFinals: "Semi Finals",
    final: "Final",
    totalMatches: "Total Matches: {count}",
    completed: "Completed: {count}",
    noFixtures: "No {stage} Fixtures",
    noFixturesDescription: "No fixtures scheduled for this stage yet.",
    ownershipLegend: "Ownership Legend",
    yourClub: "Your club",
    otherManagerClub: "Other manager's club", 
    unownedClub: "Unowned club",
    noOwner: "No owner",
    vs: "VS"
  },

  // Stage descriptions
  stageDescriptions: {
    groupStage: "Clubs compete in groups for qualification to knockout rounds",
    roundOf16: "First knockout round - Winner takes all", 
    quarterFinals: "Quarter-final stage - 8 teams remain",
    semiFinals: "Semi-final stage - 4 teams battle for the final",
    final: "The ultimate match - Champions League Final"
  },

  // Leaderboard
  leaderboard: {
    title: "Leaderboard",
    yourPosition: "Your Position",
    position: "Position",
    totalPoints: "Total Points",
    matches: "Matches",
    avgMatch: "Avg/Match", 
    pointsBehindLeader: "Points behind leader",
    points: "points",
    overallStandings: "Overall Standings",
    weeklyBreakdown: "Weekly Breakdown",
    noPointsYet: "No Points Yet",
    noPointsDescription: "No points have been scored in this league yet.",
    matchdayPerformance: "Matchday Performance",
    matchdayDescription: "Points scored by all managers across different matchdays",
    totalMatches: "{count} matches",
    topPerformers: "Top Performers",
    you: "You",
    leagueStatistics: "League Statistics",
    totalMatchesPlayed: "Total Matches",
    leagueAvg: "League Avg",
    matchdays: "Matchdays",
    budgetLeft: "Budget Left",
    noWeeklyData: "No weekly data available yet"
  },

  // Admin Dashboard  
  admin: {
    title: "Admin Dashboard",
    overview: "Overview",
    leagueSettings: "League Settings",
    memberManagement: "Member Management",
    auctionControl: "Auction Control",
    auditLogs: "Audit & Logs",
    startAuctionButton: "Start Auction",
    needMoreManagers: "Need {count} more managers to start auction",
    managersJoined: "{current}/{max} managers joined",
    cannotStartYet: "Cannot start auction yet - need minimum {min} managers",
    auctionStarted: "Auction started successfully!",
    failedToStartAuction: "Failed to start auction"
  },

  // Rules Badge
  rules: {
    loading: "Loading rules...",
    rules: "Rules",
    leagueRules: "League Rules",
    clubSlotsPerManager: "Club Slots per Manager: {slots}",
    budgetPerManager: "Budget per Manager: ${budget}M", 
    minManagers: "Min Managers: {min}",
    maxManagers: "Max Managers: {max}",
    slots: "Slots: {slots}",
    budget: "Budget: {budget}",
    min: "Min: {min}",
    max: "Max: {max}"
  },

  // Tooltip Content
  tooltips: {
    scoringSystem: "UCL Scoring System",
    goals: "Goals: +1 point each",
    wins: "Wins: +3 points", 
    draws: "Draws: +1 point",
    examples: "Examples:",
    winExample: "2-1 Win: 2 goals + 3 win = 5 points",
    drawExample: "2-2 Draw: 2 goals + 1 draw = 3 points",
    lossExample: "0-1 Loss: 0 goals + 0 = 0 points",
    budgetStatus: "Budget Status",
    remaining: "Remaining: {amount}M",
    slotsLeft: "Slots Left: {count}",
    minReserveNeeded: "Min Reserve Needed: {amount}M",
    budgetConstraint: "You must keep enough budget to fill remaining slots at minimum bid",
    auctionRules: "Auction Rules",
    minIncrement: "• Minimum increment: 1M",
    antiSnipe: "• Anti-snipe: Timer extends if bid placed in last 30 seconds", 
    budgetConstraintRule: "• Budget constraint: Must keep enough for remaining slots",
    oneOwnerPerClub: "• One owner per club"
  },

  // Auction Help
  auctionHelp: {
    howItWorks: "How it works",
    auctionGuide: "🏆 UCL Auction Guide",
    timerSystem: "Timer System",
    timerDescription: "Each club has a bidding timer. New bids extend the timer to prevent sniping.",
    budgetManagement: "Budget Management", 
    budgetDescription: "You must keep enough budget to fill all remaining club slots at minimum price.",
    clubOwnership: "Club Ownership",
    clubOwnershipDescription: "Each club can only be owned by one manager. Plan your strategy accordingly.",
    scoringSystemHelp: "Scoring System",
    scoringDescription: "Goals (+1), Wins (+3), Draws (+1). Higher scores = better leaderboard position.",
    strategyTip: "💡 Tip: Bid strategically - expensive clubs need to perform well to justify their cost!",
    biddingTips: "Bidding Tips",
    smartBiddingStrategy: "💰 Smart Bidding Strategy",
    quickBidTip: "✓ Use quick bid buttons (+1, +5, +10) for faster bidding",
    monitorBudgetTip: "✓ Monitor your budget - keep reserves for remaining slots", 
    bidEarlyTip: "✓ Bid early on clubs you really want - prices tend to rise",
    avoidLastSecondTip: "✗ Don't bid at the last second - timer extends automatically",
    avoidOverspendingTip: "✗ Avoid overspending on one club - balance is key",
    proTip: "⚡ Pro tip: Watch other managers' budgets to predict their bidding limits!",
    budgetRules: "Budget Rules",
    yourBudgetStatus: "💳 Your Budget Status",
    totalRemaining: "Total Remaining:",
    canSpendNow: "Can Spend Now:",
    mustReserve: "Must Reserve:",
    budgetWarning: "You must keep at least {amount}M per remaining slot to ensure you can buy clubs for all positions."
  },

  // Lot Closing
  lotClosing: {
    closeLot: "Close Lot",
    reasonOptional: "Reason (optional)",
    reasonPlaceholder: "e.g., Time limit reached",
    forceClose: "Force close (timer still active)",
    undoNote: "Note: You'll have 10 seconds to undo this action after closing.",
    closing: "Closing...",
    lotClosingInProgress: "Lot closing in progress", 
    secondsLeftToUndo: "{seconds} seconds left to undo",
    undo: "Undo",
    undoing: "Undoing...",
    lotClosed: "Lot closed - finalizing...",
    lotClosingFinalized: "Lot closing finalized"
  },

  // Lot Status
  lotStatus: {
    open: "Open",
    closing: "Closing...",
    sold: "Sold", 
    unsold: "Unsold",
    unknown: "Unknown"
  },

  // Diagnostic Page
  diagnostic: {
    title: "Socket.IO Diagnostic Page",
    description: "This page shows the current API configuration and allows testing Socket.IO connectivity.",
    activeConfiguration: "Active Configuration",
    apiOrigin: "API Origin:",
    socketPath: "Socket Path:",
    transports: "Transports:",
    fullSocketUrl: "Full Socket URL:",
    windowOrigin: "Window Origin:",
    pollingOnlyConnection: "Polling-Only Connection", 
    pollingOnlyDescription: "WebSocket upgrade failed. Connection is using HTTP polling which may impact performance.",
    liveConnectionStatus: "Live Connection Status",
    sessionId: "Session ID (SID):",
    activeTransport: "Active Transport:",
    connectionDetails: "Connection Details:",
    testConnection: "Test Connection",
    testing: "Testing...",
    disconnect: "Disconnect",
    lastTest: "Last test: {timestamp}",
    environmentVariables: "Environment Variables",
    reactConfigLegacy: "React Configuration (Legacy):",
    crossOriginNextjs: "Cross-Origin Configuration (Next.js):",
    crossOriginVite: "Cross-Origin Configuration (Vite):",
    browserInformation: "Browser Information",
    userAgent: "User Agent:",
    timestamp: "Timestamp:",
    connected: "Connected",
    error: "Error",
    timeout: "Timeout", 
    disconnected: "Disconnected",
    notSet: "Not set"
  },

  // Error Messages
  errors: {
    failedToLoad: "Failed to Load",
    failedToLoadDescription: "Unable to load {item} data. Please try refreshing the page.",
    failedToFetch: "Failed to fetch {item}",
    failedToSave: "Failed to save {item}",
    failedToDelete: "Failed to delete {item}",
    failedToCreate: "Failed to create {item}",
    failedToUpdate: "Failed to update {item}",
    noData: "No data available",
    tryAgain: "Please try again",
    somethingWentWrong: "Something went wrong",
    networkError: "Network error. Please check your connection.",
    serverError: "Server error. Please try again later.",
    unauthorized: "You are not authorized to perform this action.",
    notFound: "The requested resource was not found.",
    validationError: "Please check your input and try again."
  },

  // Success Messages  
  success: {
    saved: "{item} saved successfully!",
    created: "{item} created successfully!",
    updated: "{item} updated successfully!",
    deleted: "{item} deleted successfully!",
    sent: "{item} sent successfully!",
    completed: "{item} completed successfully!"
  },

  // Loading States
  loading: {
    loading: "Loading...",
    loadingItem: "Loading {item}...",
    pleaseWait: "Please wait while we fetch your data.",
    processing: "Processing...",
    saving: "Saving...",
    creating: "Creating...",
    updating: "Updating...",
    deleting: "Deleting...",
    sending: "Sending..."
  },

  // Countries (for club display)
  countries: {
    spain: "Spain",
    england: "England", 
    germany: "Germany",
    italy: "Italy",
    france: "France",
    netherlands: "Netherlands"
  },

  // Time/Date
  time: {
    seconds: "seconds",
    minutes: "minutes", 
    hours: "hours",
    days: "days",
    ago: "ago",
    now: "now",
    today: "Today",
    yesterday: "Yesterday",
    tomorrow: "Tomorrow"
  }
};

export default translations;