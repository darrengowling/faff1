/**
 * Temporary failing test to verify fail-fast behavior
 */

describe('Fail Test Contract', () => {
  test('should fail to test fail-fast behavior', () => {
    // This test intentionally fails to verify CI fail-fast
    expect(true).toBe(false);
  });
});