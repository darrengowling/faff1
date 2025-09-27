# Regression Test Report

**Generated**: 2025-09-25T21:34:15.207045
**Duration**: 5.8 seconds

## Test Results

### Backend Health Check - ✅ PASSED
**Timestamp**: 2025-09-25T21:34:09.524453

**Output:**
```
{"ok":true}
```

**Error:**
```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed

  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100    11  100    11    0     0    126      0 --:--:-- --:--:-- --:--:--   127

```

### Unit Tests - Roster Calculation Logic - ✅ PASSED
**Timestamp**: 2025-09-25T21:34:09.591038

**Output:**
```

============================================================
REGRESSION TEST SUMMARY
============================================================
Tests run: 14
Failures: 0
Errors: 0

✅ ALL REGRESSION TESTS PASSED!
✅ remaining = max(0, clubSlots - ownedCount) never goes negative
✅ Min=2 gate validation working correctly
✅ Slots=5 calculations validated
✅ Server response structures validated

```

**Error:**
```
test_edge_cases (__main__.TestRosterCalculationLogic.test_edge_cases)
Test edge cases and boundary conditions ... ok
test_mathematical_consistency (__main__.TestRosterCalculationLogic.test_mathematical_consistency)
Test that the calculation matches the mathematical formula exactly ... ok
test_negative_clamping (__main__.TestRosterCalculationLogic.test_negative_clamping)
Test that remaining slots clamps to 0 when owned > slots ... ok
test_never_negative_property (__main__.TestRosterCalculationLogic.test_never_negative_property)
Test that remaining slots is NEVER negative under any circumstances ... ok
test_normal_remaining_slots_calculation (__main__.TestRosterCalculationLogic.test_normal_remaining_slots_calculation)
Test remaining slots calculation for normal cases ... ok
test_boundary_conditions (__main__.TestLeagueMemberValidation.test_boundary_conditions)
Test boundary conditions for member validation ... ok
test_maximum_member_limits (__main__.TestLeagueMemberValidation.test_maximum_member_limits)
Test maximum member validation ... ok
test_minimum_member_requirements (__main__.TestLeagueMemberValidation.test_minimum_member_requirements)
Test minimum member validation (Min=2 gate) ... ok
test_invalid_league_settings (__main__.TestServerResponseStructures.test_invalid_league_settings)
Test validation of invalid league settings ... ok
test_invalid_roster_summary_responses (__main__.TestServerResponseStructures.test_invalid_roster_summary_responses)
Test validation of invalid roster summary responses ... ok
test_valid_league_settings (__main__.TestServerResponseStructures.test_valid_league_settings)
Test validation of valid league settings ... ok
test_valid_roster_summary_responses (__main__.TestServerResponseStructures.test_valid_roster_summary_responses)
Test validation of valid roster summary responses ... ok
test_calculation_consistency_with_defaults (__main__.TestUCLDefaultValues.test_calculation_consistency_with_defaults)
Test calculations work correctly with UCL defaults ... ok
test_ucl_default_constants (__main__.TestUCLDefaultValues.test_ucl_default_constants)
Test UCL competition profile default values ... ok

----------------------------------------------------------------------
Ran 14 tests in 0.002s

OK

```

### API Contract Tests - ✅ PASSED
**Timestamp**: 2025-09-25T21:34:10.083502

**Output:**
```
🧪 Starting API Contract Regression Tests
Target API: https://pifa-friends-1.preview.emergentagent.com/api
============================================================
✅ Competition Profiles API Contract - PASSED UCL profile: slots=5, min=2, max=8, budget=100
✅ Roster Summary API Contract Structure - PASSED Validated 4 response structures. Issues: None
✅ League Settings API Contract Structure - PASSED Validated 2 settings structures. Issues: None
✅ Clubs API Consistency - PASSED Found 28 clubs with valid structure
✅ Time Sync API Consistency - PASSED Valid timestamp: 2025-09-25T21:34:09.913411+00:00
✅ API Health Consistency - PASSED API healthy: {'ok': True}
✅ Socket Diagnostic Consistency - PASSED Socket diagnostic ok: path=/api/socketio

============================================================
API CONTRACT REGRESSION TEST SUMMARY
============================================================
Tests run: 7
Tests passed: 7
Tests failed: 0
Success rate: 100.0%

✅ ALL API CONTRACT T...

```

### Playwright E2E Tests - ✅ PASSED
**Timestamp**: 2025-09-25T21:34:15.206918

**Output:**
```
🚀 Global E2E Test Setup Starting...
✅ Application accessible at: https://pifa-friends-1.preview.emergentagent.com (Status: 200)
🎉 Global setup completed successfully!

Running 14 tests using 1 worker

[1A[2K[1/14] [chromium] › tests/e2e/api-regression-validation.spec.js:11:3 › API Regression Validation › UCL Competition Profile - Min=2, Slots=5 Validation
[1A[2K[chromium] › tests/e2e/api-regression-validation.spec.js:11:3 › API Regression Validation › UCL Competition Profile - Min=2, Slots=5 Validation
✅ UCL Profile Validated - Slots=5, Min=2, Max=8

[1A[2K[2/14] [chromium] › tests/e2e/api-regression-validation.spec.js:33:3 › API Regression Validation › Roster Calculation Logic - Never Negative
[1A[2K[chromium] › tests/e2e/api-regression-validation.spec.js:33:3 › API Regression Validation › Roster Calculation Logic - Never Negative
✅ Roster Calculation - remaining = max(0, clubSlots - ownedCount) validated

[1A[2K[3/14] [chromium] › tests/e2e/api-regression-validation.sp...

```

## Critical Regression Prevention

This test suite prevents the following regressions:

1. **Min=2 Gate**: Start Auction button disabled at 1 member, enabled at 2+
2. **Slots=5 Display**: Lobby/Auction/Roster consistently show 5 club slots
3. **Calculation Logic**: `remaining = max(0, clubSlots - ownedCount)` never negative
4. **API Contracts**: Server responses always include correct settings
5. **Structure Validation**: Settings maintain expected data structures

