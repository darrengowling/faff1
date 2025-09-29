export const CRITICAL_ROUTE_TESTIDS: Record<string, string[]> = {
  '/login': ['loginHeader','authFormReady','authEmailInput','authSubmitBtn','backToHome'],
  '/app':   ['appHeader','backToHome','homeNavButton'],
  '/app/leagues/new': ['createName','createSlots','createBudget','createMin','createSubmit','backToHome'],
  '/app/leagues/:id/lobby': ['lobbyJoined','rulesBadge','startAuction','backToHome'],
};