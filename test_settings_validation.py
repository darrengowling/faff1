#!/usr/bin/env python3
"""
Settings Validation Test
Test that fetched default settings are properly validated and applied to related documents
"""

import requests
import json
from datetime import datetime

class SettingsValidationTester:
    def __init__(self):
        self.base_url = "https://league-creator-1.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ODc4MzY3Zi05YmQzLTQ2NGQtODQ2YS1jZTQyYjYzZGI1MWYiLCJleHAiOjE3NTg2NzkyNjB9.ebAyqnx0FJ_sknhqY2sIB7FgD3tXHj6ZjSBTNfulBxY"
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
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_league_creation_and_validation(self):
        """Test league creation with default settings and validate all related documents"""
        league_data = {
            "name": f"Settings Validation Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
            # No settings - should use competition profile defaults
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if not success or 'id' not in data:
            return self.log_test(
                "League Creation and Validation",
                False,
                f"Failed to create league: {status}, {data}"
            )
        
        league_id = data['id']
        settings = data.get('settings', {})
        
        print(f"   Created league {league_id} with settings:")
        print(f"   - Budget per manager: {settings.get('budget_per_manager')}")
        print(f"   - Club slots per manager: {settings.get('club_slots_per_manager')}")
        print(f"   - League size: {settings.get('league_size', {}).get('min')}-{settings.get('league_size', {}).get('max')}")
        print(f"   - Scoring rules: {settings.get('scoring_rules')}")
        
        # Verify league settings structure
        settings_valid = (
            isinstance(settings.get('budget_per_manager'), int) and
            isinstance(settings.get('club_slots_per_manager'), int) and
            isinstance(settings.get('league_size'), dict) and
            isinstance(settings.get('scoring_rules'), dict) and
            settings.get('budget_per_manager') > 0 and
            settings.get('club_slots_per_manager') > 0 and
            settings.get('league_size', {}).get('min') > 0 and
            settings.get('league_size', {}).get('max') > 0
        )
        
        # Test league members (should have commissioner)
        success_members, status_members, members = self.make_request('GET', f'leagues/{league_id}/members')
        members_valid = success_members and len(members) == 1 and members[0]['role'] == 'commissioner'
        
        if members_valid:
            print(f"   ✓ League has {len(members)} member(s): {members[0]['display_name']} ({members[0]['role']})")
        
        # Test league status
        success_status, status_status, league_status = self.make_request('GET', f'leagues/{league_id}/status')
        status_valid = (
            success_status and 
            league_status.get('member_count') == 1 and
            league_status.get('min_members') == settings.get('league_size', {}).get('min') and
            league_status.get('max_members') == settings.get('league_size', {}).get('max')
        )
        
        if status_valid:
            print(f"   ✓ League status: {league_status.get('status')}, Members: {league_status.get('member_count')}/{league_status.get('max_members')}")
        
        return self.log_test(
            "League Creation and Validation",
            settings_valid and members_valid and status_valid,
            f"Settings valid: {settings_valid}, Members valid: {members_valid}, Status valid: {status_valid}"
        )

    def test_auction_setup_with_defaults(self):
        """Test that auction setup uses the correct default settings"""
        league_data = {
            "name": f"Auction Setup Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if not success or 'id' not in data:
            return self.log_test(
                "Auction Setup with Defaults",
                False,
                f"Failed to create league: {status}"
            )
        
        league_id = data['id']
        settings = data.get('settings', {})
        
        # Join additional members to make league ready for auction
        for i in range(3):  # Add 3 more members to reach minimum
            join_success, join_status, join_data = self.make_request('POST', f'leagues/{league_id}/join')
            if not join_success:
                print(f"   Warning: Failed to add member {i+1}: {join_status}")
        
        # Check if league is ready
        success_status, status_status, league_status = self.make_request('GET', f'leagues/{league_id}/status')
        
        if success_status and league_status.get('is_ready'):
            print(f"   ✓ League is ready with {league_status.get('member_count')} members")
            
            # Try to start auction to verify auction settings
            success_auction, status_auction, auction_data = self.make_request('POST', f'auction/{league_id}/start')
            
            if success_auction:
                print(f"   ✓ Auction started successfully")
                
                # Get auction state to verify settings
                success_state, status_state, state_data = self.make_request('GET', f'auction/{league_id}/state')
                
                if success_state and 'settings' in state_data:
                    auction_settings = state_data['settings']
                    settings_match = (
                        auction_settings.get('budget_per_manager') == settings.get('budget_per_manager') and
                        auction_settings.get('min_increment') == settings.get('min_increment') and
                        auction_settings.get('anti_snipe_seconds') == settings.get('anti_snipe_seconds') and
                        auction_settings.get('bid_timer_seconds') == settings.get('bid_timer_seconds')
                    )
                    
                    print(f"   ✓ Auction settings match league settings: {settings_match}")
                    
                    return self.log_test(
                        "Auction Setup with Defaults",
                        settings_match,
                        f"Auction settings properly applied from competition profile defaults"
                    )
                else:
                    return self.log_test(
                        "Auction Setup with Defaults",
                        False,
                        f"Failed to get auction state: {status_state}"
                    )
            else:
                return self.log_test(
                    "Auction Setup with Defaults",
                    False,
                    f"Failed to start auction: {status_auction}, {auction_data}"
                )
        else:
            return self.log_test(
                "Auction Setup with Defaults",
                False,
                f"League not ready for auction: {league_status.get('is_ready', False)}"
            )

    def test_scoring_rules_setup(self):
        """Test that scoring rules are properly set up from competition profile defaults"""
        league_data = {
            "name": f"Scoring Rules Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if not success or 'id' not in data:
            return self.log_test(
                "Scoring Rules Setup",
                False,
                f"Failed to create league: {status}"
            )
        
        league_id = data['id']
        settings = data.get('settings', {})
        scoring_rules = settings.get('scoring_rules', {})
        
        # Verify scoring rules match UCL competition profile defaults
        expected_scoring = {
            'club_goal': 1,
            'club_win': 3,
            'club_draw': 1
        }
        
        scoring_rules_valid = (
            scoring_rules.get('club_goal') == expected_scoring['club_goal'] and
            scoring_rules.get('club_win') == expected_scoring['club_win'] and
            scoring_rules.get('club_draw') == expected_scoring['club_draw']
        )
        
        print(f"   ✓ Scoring rules: {scoring_rules}")
        print(f"   ✓ Expected: {expected_scoring}")
        
        return self.log_test(
            "Scoring Rules Setup",
            scoring_rules_valid,
            f"Scoring rules properly applied from competition profile: {scoring_rules_valid}"
        )

    def run_tests(self):
        """Run all settings validation tests"""
        print("🔧 Settings Validation and Application Tests")
        print("=" * 60)
        
        self.test_league_creation_and_validation()
        self.test_auction_setup_with_defaults()
        self.test_scoring_rules_setup()
        
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All settings validation tests passed!")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed")
            return 1

if __name__ == "__main__":
    tester = SettingsValidationTester()
    exit_code = tester.run_tests()
    exit(exit_code)