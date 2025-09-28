# CI Pipeline Guide

## Overview

The CI pipeline provides comprehensive testing with flake detection and actionable failure reporting. It aims for ≥90% pass rate with zero blocker specs for deployment approval.

## Pipeline Phases

### Phase 1: Basic Verification
1. **verify-socket-config** - Validates Socket.IO configuration consistency
2. **test:contract** - Frontend contract tests (critical UI testids)
3. **diag:socketio** - Runtime Socket.IO connectivity diagnostics  
4. **verify-auth-ui** - Authentication UI element verification

### Phase 2: Core E2E Tests
Essential user journey: auth → create → start auction → nominate → bid → roster/budget

- `tests/e2e/time-control.spec.ts` - Deterministic time control system
- `tests/e2e/hooks-unit.spec.ts` - Test-only hooks functionality
- `tests/e2e/scoring_ingest.spec.ts` - Scoring ingestion and idempotency

### Phase 3: Extended E2E Tests  
Advanced features: anti-snipe, simultaneous bids, reconnect, scoring

- `tests/e2e/auction-hooks.spec.ts` - Advanced auction flows
- `tests/e2e/anti-snipe-unit.spec.ts` - Anti-snipe logic testing

## Flake Detection

Each spec runs **up to 3 times** with classification:
- **PASS**: 3/3 attempts successful
- **FLAKY**: 1-2/3 attempts successful (⚠️ non-blocking)
- **BLOCKER**: 0/3 attempts successful (❌ deployment blocking)

## Success Criteria

- **Pass Rate**: ≥90% overall (passed + flaky specs)
- **Zero Blockers**: No specs with 0/3 success rate
- **Phase Gates**: Basic verification phases must all pass

## Running the Pipeline

```bash
# Full CI pipeline with flake detection  
npm run ci:pipeline

# Individual phases
npm run verify-socket-config
npm run test:contract
npm run diag:socketio
npm run verify-auth-ui
npm run test:core-e2e
npm run test:extended-e2e
```

## Output Format

```
🎯 SIMPLE CI PIPELINE RESULTS
================================================================================

📋 PHASE RESULTS:
  ✅ PASS verify-socket-config: Socket.IO configuration verification (349ms)
  ✅ PASS test:contract: Frontend contract tests (direct) (7304ms)
  ❌ FAIL diag:socketio: Socket.IO runtime diagnostics (timeout)

📊 OVERALL STATISTICS:
  Duration: 1.9 minutes
  Total specs: 5
  Passed: 3
  Flaky: 0  
  Blockers: 2
  Pass rate: 60.0%

📈 SPEC RESULTS:
┌─────────────────────────────┬─────────┬───────────────────────┬─────────────────────┐
│ Spec Name                   │ Status  │ Top Error             │ Suggested Fix       │
├─────────────────────────────┼─────────┼───────────────────────┼─────────────────────┤
│ time-control.spec.ts        │ ✅ PASS  │ -                     │ -                   │
│ auction-hooks.spec.ts       │ ❌ BLOCK │ League creation fails │ Use test hooks      │
└─────────────────────────────┴─────────┴───────────────────────┴─────────────────────┘

🎯 SUCCESS CRITERIA:
  Pass rate ≥90%: ❌ (60.0%)
  Zero blockers: ❌ (2 blockers)

💥 CI PIPELINE FAILURE:
  - 2 blocker specs prevent deployment

🔧 RECOMMENDED ACTIONS:
  - Fix tests/e2e/auction-hooks.spec.ts: Use test hooks for setup
```

## Error Categories & Fixes

### Common Error Patterns
- **Timeout**: Increase timeout or add wait conditions
- **Element not found**: Check data-testid selectors  
- **Navigation failed**: Add navigation wait or check URL patterns
- **Socket/connection**: Check socket.io configuration
- **Auth failed**: Verify authentication flow

### Spec-Specific Fixes
- **auction-hooks.spec.ts**: Use test hooks instead of UI interaction
- **scoring_ingest.spec.ts**: Use scoring reset hook before test
- **reconnect tests**: Check socket drop test hooks

## Deployment Gates

The pipeline **blocks deployment** when:
1. Pass rate < 90%
2. Any BLOCKER specs (0/3 success rate)
3. Basic verification phases fail

The pipeline **allows deployment** when:
1. Pass rate ≥ 90% 
2. Zero BLOCKER specs
3. All basic verification phases pass

FLAKY specs (1-2/3 success) are **non-blocking** but should be investigated for stability.

## Troubleshooting

### Pipeline Hangs
- Check for infinite loops in contract tests
- Verify Jest `--forceExit` flag is present
- Ensure proper timeout configuration

### High Failure Rates  
- Review recent changes to core test infrastructure
- Check if test hooks are working correctly
- Verify database and service health

### Flaky Tests
- Use deterministic time control (`initializeTestTime`)
- Replace UI interactions with test hooks
- Add proper wait conditions and state verification