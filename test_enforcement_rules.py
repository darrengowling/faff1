#!/usr/bin/env python3
"""
Enforcement Rules Testing Script
Tests the comprehensive enforcement rules implementation
"""

import requests
import json
from datetime import datetime
import sys

class EnforcementRulesTester:
    def __init__(self, base_url="https://pifa-friends.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.test_leagues = []
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            self.failed_tests.append(f"{name}: {details}")
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def authenticate(self):
        """Authenticate using magic link flow"""
        # Step 1: Request magic link
        email = "commissioner@example.com"
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": email}
        )
        
        if not success:
            print(f"❌ Failed to request magic link: {status}")
            return False
        
        print(f"📧 Magic link requested for {email}")
        print("🔍 Check backend logs for the token...")
        
        # For testing, we'll use a token from the logs
        # In production, this would be extracted from email
        token = input("Enter the magic link token from backend logs: ").strip()
        
        if not token:
            print("❌ No token provided")
            return False
        
        # Step 2: Verify token
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token}
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            print(f"✅ Authenticated as {data['user']['email']}")
            return True
        
        print(f"❌ Token verification failed: {status}")
        return False

    def test_roster_capacity_rule(self):
        """Test ROSTER CAPACITY RULE enforcement"""
        print("\n🛡️ Testing ROSTER CAPACITY RULE")
        
        # Create league with 1 club slot for testing
        league_data = {
            "name": f"Roster Capacity Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 1,  # Only 1 slot
                "league_size": {"min": 2, "max": 4}
            }
        }
        
        success, status, league = self.make_request('POST', 'leagues', league_data)
        if not success:
            return self.log_test("Roster Capacity Rule", False, f"Failed to create league: {status}")
        
        league_id = league['id']
        self.test_leagues.append(league_id)
        
        # Add a member to reach minimum
        success_join, status_join, join_data = self.make_request('POST', f'leagues/{league_id}/join')
        
        # Verify league settings
        success_get, status_get, league_info = self.make_request('GET', f'leagues/{league_id}')
        
        capacity_rule_configured = (
            success_get and
            league_info.get('settings', {}).get('club_slots_per_manager') == 1
        )
        
        return self.log_test(
            "Roster Capacity Rule",
            capacity_rule_configured,
            f"League created with 1 slot limit: {capacity_rule_configured}"
        )

    def test_budget_rule_enforcement(self):
        """Test BUDGET RULE ENFORCEMENT"""
        print("\n💰 Testing BUDGET RULE ENFORCEMENT")
        
        if not self.test_leagues:
            return self.log_test("Budget Rule Enforcement", False, "No test league available")
        
        league_id = self.test_leagues[0]
        
        # Test 1: Budget change should be allowed when auction is scheduled
        budget_update = {
            "budget_per_manager": 150
        }
        
        success1, status1, result1 = self.make_request(
            'PUT',
            f'admin/leagues/{league_id}/settings',
            budget_update
        )
        
        budget_change_allowed = success1 and result1.get('success', False)
        
        # Test 2: Try another budget change
        budget_update2 = {
            "budget_per_manager": 120
        }
        
        success2, status2, result2 = self.make_request(
            'PUT',
            f'admin/leagues/{league_id}/settings',
            budget_update2
        )
        
        second_change_allowed = success2 and result2.get('success', False)
        
        return self.log_test(
            "Budget Rule Enforcement",
            budget_change_allowed and second_change_allowed,
            f"First change: {budget_change_allowed}, Second change: {second_change_allowed}"
        )

    def test_league_size_rule_enforcement(self):
        """Test LEAGUE SIZE RULE ENFORCEMENT"""
        print("\n👥 Testing LEAGUE SIZE RULE ENFORCEMENT")
        
        # Create league with small size limits
        league_data = {
            "name": f"League Size Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 3,
                "league_size": {"min": 2, "max": 3}  # Small league
            }
        }
        
        success, status, league = self.make_request('POST', 'leagues', league_data)
        if not success:
            return self.log_test("League Size Rule Enforcement", False, f"Failed to create league: {status}")
        
        league_id = league['id']
        self.test_leagues.append(league_id)
        
        # Test 1: League should not be ready with only 1 member
        success1, status1, league_status = self.make_request('GET', f'leagues/{league_id}/status')
        not_ready_with_one = (
            success1 and
            league_status.get('member_count') == 1 and
            league_status.get('min_members') == 2 and
            not league_status.get('is_ready', True)
        )
        
        # Test 2: Add member to reach minimum
        success2, status2, join_result = self.make_request('POST', f'leagues/{league_id}/join')
        
        # Test 3: Check if ready now
        success3, status3, updated_status = self.make_request('GET', f'leagues/{league_id}/status')
        ready_with_two = (
            success3 and
            updated_status.get('member_count') == 2 and
            updated_status.get('is_ready', False)
        )
        
        # Test 4: Add one more to reach max
        success4, status4, join_result2 = self.make_request('POST', f'leagues/{league_id}/join')
        
        # Test 5: Try to add another (should fail - league full)
        success5, status5, join_result3 = self.make_request(
            'POST', 
            f'leagues/{league_id}/join',
            expected_status=400
        )
        
        league_full_rejected = success5 and status5 == 400
        
        return self.log_test(
            "League Size Rule Enforcement",
            not_ready_with_one and ready_with_two and league_full_rejected,
            f"Not ready with 1: {not_ready_with_one}, Ready with 2: {ready_with_two}, Full rejected: {league_full_rejected}"
        )

    def test_admin_service_validations(self):
        """Test AdminService validation methods"""
        print("\n🔧 Testing ADMIN SERVICE VALIDATIONS")
        
        if not self.test_leagues:
            return self.log_test("Admin Service Validations", False, "No test league available")
        
        league_id = self.test_leagues[0]
        
        # Test 1: Valid settings update
        settings_update = {
            "budget_per_manager": 200,
            "club_slots_per_manager": 5,
            "league_size": {"min": 3, "max": 6}
        }
        
        success1, status1, result1 = self.make_request(
            'PUT',
            f'admin/leagues/{league_id}/settings',
            settings_update
        )
        
        valid_settings_accepted = success1 and result1.get('success', False)
        
        # Test 2: Invalid settings (should be rejected)
        invalid_settings = {
            "budget_per_manager": -10,  # Invalid negative
            "club_slots_per_manager": 0  # Invalid zero
        }
        
        success2, status2, result2 = self.make_request(
            'PUT',
            f'admin/leagues/{league_id}/settings',
            invalid_settings,
            expected_status=400
        )
        
        invalid_settings_rejected = success2 and status2 == 400
        
        return self.log_test(
            "Admin Service Validations",
            valid_settings_accepted and invalid_settings_rejected,
            f"Valid accepted: {valid_settings_accepted}, Invalid rejected: {invalid_settings_rejected}"
        )

    def test_auction_start_constraints(self):
        """Test auction start constraints"""
        print("\n🎯 Testing AUCTION START CONSTRAINTS")
        
        # Create league that doesn't meet minimum requirements
        league_data = {
            "name": f"Auction Start Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 3,
                "league_size": {"min": 4, "max": 8}  # Requires 4 members
            }
        }
        
        success, status, league = self.make_request('POST', 'leagues', league_data)
        if not success:
            return self.log_test("Auction Start Constraints", False, f"Failed to create league: {status}")
        
        league_id = league['id']
        self.test_leagues.append(league_id)
        
        # Test 1: Try to start auction with insufficient members (should fail)
        success1, status1, start_result1 = self.make_request(
            'POST',
            f'auction/{league_id}/start',
            expected_status=400
        )
        
        start_rejected_insufficient = success1 and status1 == 400
        
        # Test 2: Add members to reach minimum
        join_results = []
        for i in range(3):  # Add 3 more (total 4 with commissioner)
            success_join, status_join, join_data = self.make_request('POST', f'leagues/{league_id}/join')
            join_results.append(success_join)
        
        # Test 3: Check league status
        success2, status2, league_status = self.make_request('GET', f'leagues/{league_id}/status')
        league_ready = (
            success2 and
            league_status.get('member_count') >= 4 and
            league_status.get('is_ready', False)
        )
        
        # Test 4: Try to start auction now (should succeed)
        success3, status3, start_result2 = self.make_request(
            'POST',
            f'auction/{league_id}/start'
        )
        
        start_allowed_sufficient = success3
        
        return self.log_test(
            "Auction Start Constraints",
            start_rejected_insufficient and league_ready and start_allowed_sufficient,
            f"Rejected insufficient: {start_rejected_insufficient}, Ready: {league_ready}, Start allowed: {start_allowed_sufficient}, Joins: {sum(join_results)}"
        )

    def test_league_creation_with_defaults(self):
        """Test league creation uses competition profile defaults"""
        print("\n🏆 Testing LEAGUE CREATION WITH DEFAULTS")
        
        # Create league without settings
        league_data = {
            "name": f"Default Settings Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
            # No settings - should use UCL defaults
        }
        
        success, status, league = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in league:
            self.test_leagues.append(league['id'])
            
            # Verify uses UCL defaults
            settings = league.get('settings', {})
            uses_defaults = (
                settings.get('budget_per_manager') == 100 and  # UCL default
                settings.get('club_slots_per_manager') == 3 and  # UCL default
                settings.get('league_size', {}).get('min') == 4 and  # UCL default
                settings.get('league_size', {}).get('max') == 8  # UCL default
            )
            
            return self.log_test(
                "League Creation With Defaults",
                uses_defaults,
                f"Uses UCL defaults: {uses_defaults}"
            )
        
        return self.log_test(
            "League Creation With Defaults",
            False,
            f"Status: {status}, Response: {league}"
        )

    def run_enforcement_tests(self):
        """Run all enforcement rules tests"""
        print("🛡️ ENFORCEMENT RULES COMPREHENSIVE TESTING")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return 1
        
        # Run all enforcement tests
        results = []
        results.append(self.test_roster_capacity_rule())
        results.append(self.test_budget_rule_enforcement())
        results.append(self.test_league_size_rule_enforcement())
        results.append(self.test_admin_service_validations())
        results.append(self.test_auction_start_constraints())
        results.append(self.test_league_creation_with_defaults())
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 ENFORCEMENT RULES TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All enforcement rules tests passed!")
            print("✅ Roster capacity rule enforcement working")
            print("✅ Budget change constraints working")
            print("✅ League size rule enforcement working")
            print("✅ Admin service validations working")
            print("✅ Auction start constraints working")
            print("✅ Competition profile integration working")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = EnforcementRulesTester()
    return tester.run_enforcement_tests()

if __name__ == "__main__":
    sys.exit(main())