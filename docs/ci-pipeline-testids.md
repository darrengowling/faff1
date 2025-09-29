# CI Pipeline with TestID Validation

This document describes the CI pipeline steps that validate testids before running E2E tests.

## Pipeline Order

The CI pipeline follows this strict order to catch issues early and minimize resource waste:

```
verify-socket-config → test:contract → audit:testids → diag:socketio → E2E
```

### 1. verify-socket-config
- **Purpose**: Verify Socket.IO configuration is correct
- **Script**: `npm run verify:socket-config`
- **Checks**: Environment variables, transport configuration
- **Fails on**: Missing essential configs

### 2. test:contract 
- **Purpose**: Validate testid structure and naming conventions
- **Script**: `npm run test:contract`
- **Checks**: RTL tests for all critical routes, testid presence, uniqueness
- **Fails on**: Missing testids in contract definitions, syntax errors

### 3. audit:testids
- **Purpose**: Verify testids are accessible in actual DOM
- **Script**: `npm run audit:testids`  
- **Checks**: Calls `/test/testids/verify` endpoint for critical routes
- **Fails on**: Any missing or hidden testids
- **Routes tested**:
  - `/login`
  - `/app`
  - `/app/leagues/new`
  - `/app/leagues/:id/lobby` (with dummy id)

### 4. diag:socketio
- **Purpose**: Verify Socket.IO connectivity before E2E
- **Script**: `npm run diag:socketio`
- **Checks**: Polling handshake, WebSocket connection
- **Fails on**: Connection failures, handshake errors

### 5. E2E Tests
- **Purpose**: Full end-to-end testing
- **Script**: `npm run test:e2e`
- **Only runs if all previous steps pass**

## Usage

### Full Pipeline (Production)
```bash
npm run ci:pipeline:with-audit && npm run test:e2e
```

### Individual Steps (Development)
```bash
npm run verify:socket-config
npm run test:contract  
npm run audit:testids
npm run diag:socketio
```

### Quick Pipeline (Without Audit)
```bash
npm run ci:pipeline
```

## TestID Audit Details

The `audit:testids` script:

1. **Calls Backend Endpoint**: `GET /api/test/testids/verify?route=<route>`
2. **Analyzes Response**: Checks `present`, `missing`, `hidden` arrays
3. **Fails Pipeline**: If any testids are missing or inaccessible
4. **Provides Actions**: Specific steps to fix identified issues

### Example Output (Failure)
```
💥 TestID audit failed!
❌ CI Pipeline should STOP before E2E tests.

🔧 Actions Required:
   • Add missing testids for /login: backToHome
   • Add missing testids for /app: homeNavButton
   • Make visible testids for /app/leagues/new: backToHome
```

### Example Output (Success)
```
🎉 All routes passed! TestIDs are ready for E2E testing.
✅ CI Pipeline can proceed to E2E tests.
```

## Benefits

1. **Early Detection**: Catch testid issues before expensive E2E tests
2. **Cost Savings**: Prevent resource waste on doomed test runs
3. **Clear Feedback**: Specific actionable error messages
4. **Build Safety**: Pipeline stops automatically when testids are missing
5. **Development Speed**: Fast feedback loop for testid issues