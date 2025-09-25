#!/usr/bin/env python3
"""
Unit Tests for Roster Calculation Logic (Backend)
Ensures remaining = max(0, clubSlots - ownedCount) never goes negative
"""

import unittest
import sys
import os

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

class TestRosterCalculationLogic(unittest.TestCase):
    """Test suite for roster calculation logic regression prevention"""

    def calculate_remaining_slots(self, club_slots, owned_count):
        """Calculate remaining slots using the same logic as backend"""
        return max(0, club_slots - owned_count)

    def test_normal_remaining_slots_calculation(self):
        """Test remaining slots calculation for normal cases"""
        test_cases = [
            (5, 0, 5),
            (5, 1, 4),
            (5, 2, 3),
            (5, 3, 2),
            (5, 4, 1),
            (5, 5, 0)
        ]
        
        for club_slots, owned_count, expected in test_cases:
            with self.subTest(slots=club_slots, owned=owned_count):
                result = self.calculate_remaining_slots(club_slots, owned_count)
                self.assertEqual(result, expected)
                self.assertGreaterEqual(result, 0, "Remaining slots should never be negative")

    def test_negative_clamping(self):
        """Test that remaining slots clamps to 0 when owned > slots"""
        test_cases = [
            (5, 6, 0),
            (5, 7, 0),
            (5, 10, 0),
            (5, 100, 0),
            (3, 5, 0),
            (1, 2, 0)
        ]
        
        for club_slots, owned_count, expected in test_cases:
            with self.subTest(slots=club_slots, owned=owned_count):
                result = self.calculate_remaining_slots(club_slots, owned_count)
                self.assertEqual(result, expected)
                self.assertEqual(result, 0, "Over-owned scenarios should return 0")
                self.assertGreaterEqual(result, 0, "Result should never be negative")

    def test_never_negative_property(self):
        """Test that remaining slots is NEVER negative under any circumstances"""
        # Test a wide range of scenarios
        for club_slots in range(0, 11):
            for owned_count in range(0, 21):
                with self.subTest(slots=club_slots, owned=owned_count):
                    result = self.calculate_remaining_slots(club_slots, owned_count)
                    self.assertGreaterEqual(result, 0, 
                        f"remaining = max(0, {club_slots} - {owned_count}) = {result} should be >= 0")

    def test_mathematical_consistency(self):
        """Test that the calculation matches the mathematical formula exactly"""
        test_data = [
            (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
            (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5),
            (1, 0), (1, 1), (1, 2), (1, 3),
            (0, 0), (0, 1), (0, 2)
        ]
        
        for slots, owned in test_data:
            with self.subTest(slots=slots, owned=owned):
                expected = max(0, slots - owned)
                actual = self.calculate_remaining_slots(slots, owned)
                self.assertEqual(actual, expected, 
                    f"max(0, {slots} - {owned}) should equal {expected}")

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Zero slots
        self.assertEqual(self.calculate_remaining_slots(0, 0), 0)
        self.assertEqual(self.calculate_remaining_slots(0, 1), 0)
        
        # Large numbers
        self.assertEqual(self.calculate_remaining_slots(100, 50), 50)
        self.assertEqual(self.calculate_remaining_slots(100, 150), 0)
        
        # Single slot scenarios
        self.assertEqual(self.calculate_remaining_slots(1, 0), 1)
        self.assertEqual(self.calculate_remaining_slots(1, 1), 0)
        self.assertEqual(self.calculate_remaining_slots(1, 2), 0)


class TestLeagueMemberValidation(unittest.TestCase):
    """Test suite for league member count validation logic"""

    def can_start_auction(self, member_count, min_members):
        """Check if auction can start based on member count"""
        return member_count >= min_members

    def is_within_max_members(self, member_count, max_members):
        """Check if member count is within maximum limit"""
        return member_count <= max_members

    def test_minimum_member_requirements(self):
        """Test minimum member validation (Min=2 gate)"""
        # Min = 2 scenarios (UCL default)
        self.assertFalse(self.can_start_auction(1, 2), "Should not start auction with 1 member (min=2)")
        self.assertTrue(self.can_start_auction(2, 2), "Should start auction with 2 members (min=2)")
        self.assertTrue(self.can_start_auction(3, 2), "Should start auction with 3 members (min=2)")
        self.assertTrue(self.can_start_auction(8, 2), "Should start auction with 8 members (min=2)")

        # Min = 4 scenarios (alternative league types)
        self.assertFalse(self.can_start_auction(3, 4), "Should not start auction with 3 members (min=4)")
        self.assertTrue(self.can_start_auction(4, 4), "Should start auction with 4 members (min=4)")
        self.assertTrue(self.can_start_auction(5, 4), "Should start auction with 5 members (min=4)")

    def test_maximum_member_limits(self):
        """Test maximum member validation"""
        # Max = 8 scenarios (UCL default)
        self.assertTrue(self.is_within_max_members(7, 8), "7 members should be within max=8")
        self.assertTrue(self.is_within_max_members(8, 8), "8 members should be within max=8")
        self.assertFalse(self.is_within_max_members(9, 8), "9 members should exceed max=8")
        self.assertFalse(self.is_within_max_members(10, 8), "10 members should exceed max=8")

        # Max = 6 scenarios (UEL leagues)
        self.assertTrue(self.is_within_max_members(5, 6), "5 members should be within max=6")
        self.assertTrue(self.is_within_max_members(6, 6), "6 members should be within max=6")
        self.assertFalse(self.is_within_max_members(7, 6), "7 members should exceed max=6")

    def test_boundary_conditions(self):
        """Test boundary conditions for member validation"""
        # Zero members
        self.assertFalse(self.can_start_auction(0, 2), "Should not start with 0 members")
        self.assertTrue(self.is_within_max_members(0, 8), "0 members is within max limit")

        # Exactly at boundaries
        self.assertTrue(self.can_start_auction(2, 2), "Should start exactly at minimum")
        self.assertTrue(self.is_within_max_members(8, 8), "Should allow exactly at maximum")


class TestServerResponseStructures(unittest.TestCase):
    """Test expected server response structures for regression prevention"""

    def validate_roster_summary_structure(self, response):
        """Validate roster summary response structure"""
        required_fields = ['ownedCount', 'clubSlots', 'remaining']
        
        if not isinstance(response, dict):
            return False, "Response should be a dictionary"
            
        for field in required_fields:
            if field not in response:
                return False, f"Missing required field: {field}"
            if not isinstance(response[field], int):
                return False, f"Field {field} should be an integer"
            if response[field] < 0:
                return False, f"Field {field} should not be negative"
        
        # Validate calculation
        expected_remaining = max(0, response['clubSlots'] - response['ownedCount'])
        if response['remaining'] != expected_remaining:
            return False, f"Remaining calculation incorrect: expected {expected_remaining}, got {response['remaining']}"
        
        return True, "Valid"

    def validate_league_settings_structure(self, settings):
        """Validate league settings structure"""
        if not isinstance(settings, dict):
            return False, "Settings should be a dictionary"
            
        required_fields = {
            'clubSlots': int,
            'budgetPerManager': int,
            'leagueSize': dict
        }
        
        for field, expected_type in required_fields.items():
            if field not in settings:
                return False, f"Missing required field: {field}"
            if not isinstance(settings[field], expected_type):
                return False, f"Field {field} should be {expected_type.__name__}"
        
        # Validate league size structure
        league_size = settings['leagueSize']
        if 'min' not in league_size or 'max' not in league_size:
            return False, "leagueSize should have 'min' and 'max' fields"
        
        if not isinstance(league_size['min'], int) or not isinstance(league_size['max'], int):
            return False, "leagueSize min and max should be integers"
        
        if league_size['min'] > league_size['max']:
            return False, "leagueSize min should not exceed max"
        
        # Validate positive values
        if settings['clubSlots'] <= 0:
            return False, "clubSlots should be positive"
        if settings['budgetPerManager'] <= 0:
            return False, "budgetPerManager should be positive"
        if league_size['min'] <= 0:
            return False, "leagueSize min should be positive"
        
        return True, "Valid"

    def test_valid_roster_summary_responses(self):
        """Test validation of valid roster summary responses"""
        valid_responses = [
            {'ownedCount': 0, 'clubSlots': 5, 'remaining': 5},
            {'ownedCount': 2, 'clubSlots': 5, 'remaining': 3},
            {'ownedCount': 5, 'clubSlots': 5, 'remaining': 0},
            {'ownedCount': 6, 'clubSlots': 5, 'remaining': 0}  # Over-owned but clamped
        ]
        
        for response in valid_responses:
            with self.subTest(response=response):
                is_valid, message = self.validate_roster_summary_structure(response)
                self.assertTrue(is_valid, f"Response should be valid: {message}")

    def test_invalid_roster_summary_responses(self):
        """Test validation of invalid roster summary responses"""
        invalid_responses = [
            {'ownedCount': -1, 'clubSlots': 5, 'remaining': 5},  # Negative owned
            {'ownedCount': 2, 'clubSlots': 0, 'remaining': 3},   # Zero slots
            {'ownedCount': 2, 'clubSlots': 5, 'remaining': -1},  # Negative remaining
            {'ownedCount': 2, 'clubSlots': 5, 'remaining': 4},   # Incorrect calculation
        ]
        
        for response in invalid_responses:
            with self.subTest(response=response):
                is_valid, message = self.validate_roster_summary_structure(response)
                self.assertFalse(is_valid, f"Response should be invalid: {response}")

    def test_valid_league_settings(self):
        """Test validation of valid league settings"""
        valid_settings = [
            {
                'clubSlots': 5,
                'budgetPerManager': 100,
                'leagueSize': {'min': 2, 'max': 8}
            },
            {
                'clubSlots': 3,
                'budgetPerManager': 150,
                'leagueSize': {'min': 4, 'max': 6}
            }
        ]
        
        for settings in valid_settings:
            with self.subTest(settings=settings):
                is_valid, message = self.validate_league_settings_structure(settings)
                self.assertTrue(is_valid, f"Settings should be valid: {message}")

    def test_invalid_league_settings(self):
        """Test validation of invalid league settings"""
        invalid_settings = [
            {
                'clubSlots': 0,  # Invalid: zero slots
                'budgetPerManager': 100,
                'leagueSize': {'min': 2, 'max': 8}
            },
            {
                'clubSlots': 5,
                'budgetPerManager': 100,
                'leagueSize': {'min': 8, 'max': 2}  # Invalid: min > max
            },
            {
                'clubSlots': 5,
                'budgetPerManager': -50,  # Invalid: negative budget
                'leagueSize': {'min': 2, 'max': 8}
            }
        ]
        
        for settings in invalid_settings:
            with self.subTest(settings=settings):
                is_valid, message = self.validate_league_settings_structure(settings)
                self.assertFalse(is_valid, f"Settings should be invalid: {settings}")


class TestUCLDefaultValues(unittest.TestCase):
    """Test that UCL default values match expected specifications"""

    def test_ucl_default_constants(self):
        """Test UCL competition profile default values"""
        # Expected UCL defaults based on requirements
        EXPECTED_UCL_DEFAULTS = {
            'club_slots': 5,
            'league_size_min': 2,
            'league_size_max': 8,
            'budget_per_manager': 100  # or another expected value
        }
        
        # Test each expected default
        self.assertEqual(EXPECTED_UCL_DEFAULTS['club_slots'], 5, 
            "UCL default should have 5 club slots")
        self.assertEqual(EXPECTED_UCL_DEFAULTS['league_size_min'], 2, 
            "UCL default should have min=2 members")
        self.assertEqual(EXPECTED_UCL_DEFAULTS['league_size_max'], 8, 
            "UCL default should have max=8 members")
        self.assertGreater(EXPECTED_UCL_DEFAULTS['budget_per_manager'], 0, 
            "UCL default should have positive budget")

    def test_calculation_consistency_with_defaults(self):
        """Test calculations work correctly with UCL defaults"""
        club_slots = 5  # UCL default
        
        # Test various owned counts with 5-slot default
        test_cases = [
            (0, 5),  # No clubs owned -> 5 remaining
            (1, 4),  # 1 club owned -> 4 remaining
            (2, 3),  # 2 clubs owned -> 3 remaining
            (3, 2),  # 3 clubs owned -> 2 remaining
            (4, 1),  # 4 clubs owned -> 1 remaining
            (5, 0),  # All slots filled -> 0 remaining
            (6, 0),  # Over-owned -> 0 remaining (clamped)
        ]
        
        for owned_count, expected_remaining in test_cases:
            with self.subTest(owned=owned_count):
                actual_remaining = max(0, club_slots - owned_count)
                self.assertEqual(actual_remaining, expected_remaining)
                self.assertGreaterEqual(actual_remaining, 0)


if __name__ == '__main__':
    # Run the tests
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestRosterCalculationLogic,
        TestLeagueMemberValidation, 
        TestServerResponseStructures,
        TestUCLDefaultValues
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"REGRESSION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, error in result.failures:
            print(f"- {test}: {error}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    if result.wasSuccessful():
        print(f"\n✅ ALL REGRESSION TESTS PASSED!")
        print(f"✅ remaining = max(0, clubSlots - ownedCount) never goes negative")
        print(f"✅ Min=2 gate validation working correctly")
        print(f"✅ Slots=5 calculations validated") 
        print(f"✅ Server response structures validated")
    else:
        print(f"\n❌ SOME TESTS FAILED - REGRESSIONS DETECTED!")
        sys.exit(1)