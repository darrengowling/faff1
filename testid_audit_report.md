# TESTID IMPLEMENTATION AUDIT REPORT

## CRITICAL ISSUES FOUND

### 1. TESTIDS EXPECTED BY TESTS BUT NOT DEFINED IN TESTIDS.TS

**Missing TESTIDS definitions:**
- `adminPanel` - Expected by tests, not defined
- `auctionAssetName` - Expected by tests, not defined  
- `auctionTimer` - Expected by tests, not defined
- `auctionTopBid` - Expected by tests, not defined
- `budgetRemaining` - Expected by tests, not defined
- `closeLotButton` - Expected by tests, not defined
- `inviteLinkUrl` - Expected by tests, not defined
- `inviteSubmitButton` - Expected by tests, not defined
- `joinLeagueButton` - Expected by tests, not defined
- `nextLotButton` - Expected by tests, not defined
- `nominateBtn` - Expected by tests, not defined
- `rosterEmpty` - Expected by tests, not defined
- `rosterItemName` - Expected by tests, not defined
- `rosterItemPrice` - Expected by tests, not defined
- `rosterItem` - Expected by tests, not defined
- `rosterList` - Expected by tests, not defined
- `soldBadge` - Expected by tests, not defined
- `undoButton` - Expected by tests, not defined
- `yourBudget` - Expected by tests, not defined
- `yourSlotsRemaining` - Expected by tests, not defined

### 2. TESTIDS DEFINED BUT NOT IMPLEMENTED IN COMPONENTS

**Missing implementations:**
- `navBrand` - Defined but missing from HeaderBrand component
- `authError` - Defined but may be missing from LoginPage error states
- `authSuccess` - Defined but may be missing from LoginPage success states
- `rulesBadge` - Defined but missing from rules components
- `lobbyJoinedCount` - Defined but missing from lobby components
- `startAuctionBtn` - Defined but missing from auction components

### 3. HARDCODED TESTIDS IN TESTS (Not using TESTIDS constants)

**Hardcoded testids that should use TESTIDS:**
- `"back-to-home-link"` - Should use TESTIDS constant
- `"login-header"` - Should be added to TESTIDS
- `"dev-magic-link-btn"` - Should be added to TESTIDS  
- `"create-success"` - Should use TESTIDS constant
- `"nav-hamburger"` - Should use TESTIDS constant
- `"nav-mobile-drawer"` - Should use TESTIDS constant

### 4. DUPLICATE TESTIDS IN COMPONENTS

**Found duplicates:**
- `nav-mobile-drawer` appears in both visible drawer and hidden state tracker
- `back-to-home-link` may appear in both header and mobile menu

## IMMEDIATE ACTION ITEMS

### Priority 1: Add Missing TESTIDS Definitions
Add these to `/app/frontend/src/testids.ts`:

```typescript
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
```

### Priority 2: Implement Missing Testids in Components

1. **LoginPage.jsx**: Add `loginHeader`, `authError`, `authSuccess` testids
2. **Navigation components**: Add `navBrand` testid to HeaderBrand  
3. **Lobby components**: Add `lobbyJoinedCount`, `rulesBadge` testids
4. **Auction components**: Add all auction-related testids
5. **Roster components**: Add all roster-related testids

### Priority 3: Fix Duplicate Testids

1. Remove duplicate `nav-mobile-drawer` testids (keep only one)
2. Ensure `back-to-home-link` appears only once per page

### Priority 4: Replace Hardcoded Testids in Tests

Update all test files to use TESTIDS constants instead of hardcoded strings.

## COMPONENT-SPECIFIC ISSUES

### LoginPage.jsx
- ✅ `authEmailInput` implemented correctly
- ❌ `loginHeader` missing - add to page title
- ❌ `authError` needs verification  
- ❌ `authSuccess` needs verification

### Navigation Components  
- ❌ `navBrand` missing from HeaderBrand component
- ✅ `navHamburger` implemented
- ⚠️  `navMobileDrawer` has duplicates

### Lobby Components
- ❌ `lobbyJoinedCount` missing implementation
- ❌ `rulesBadge` missing implementation  
- ❌ `startAuctionBtn` missing implementation

### Auction Components
- ❌ Multiple auction testids missing (see Priority 1 list)

## TESTING IMPACT

These missing testids are causing:
- **auth_ui.spec.ts**: 66.7% pass rate due to missing testids
- **navigation.spec.ts**: 0% pass rate due to duplicate testids
- **core-smoke.spec.ts**: Complete failure due to missing lobby testids

## RECOMMENDED FIX ORDER

1. Add missing TESTIDS definitions (5 min)
2. Fix duplicate nav-mobile-drawer testids (2 min) 
3. Implement missing testids in critical components (20 min)
4. Update tests to use TESTIDS constants (10 min)
5. Run canary tests to verify fixes

**Estimated total fix time: 37 minutes**