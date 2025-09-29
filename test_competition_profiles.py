#!/usr/bin/env python3
"""
Competition Profile Integration Testing
Tests the updated league creation defaults and competitionProfile integration
"""

import requests
import sys
import json
from datetime import datetime, timezone

class CompetitionProfileTester:
    def __init__(self, base_url="https://pifa-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.commissioner_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.commissioner_email = "commissioner@example.com"
        self.test_league_id_profile = None
        
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

    def make_request(self, method, endpoint, data=None, expected_status=200, token=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use provided token or default commissioner token
        auth_token = token or self.commissioner_token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_competition_profiles_endpoint(self):
        """Test GET /api/competition-profiles returns updated defaults"""
        success, status, data = self.make_request('GET', 'competition-profiles', token=None)
        
        if not success:
            return self.log_test("Competition Profiles Endpoint", False, f"Failed to get profiles: {status}")
        
        profiles = data.get('profiles', [])
        if not profiles:
            return self.log_test("Competition Profiles Endpoint", False, "No profiles returned")
        
        # Find UCL profile and verify updated defaults
        ucl_profile = None
        for profile in profiles:
            if profile.get('id') == 'ucl' or profile.get('short_name') == 'UCL':
                ucl_profile = profile
                break
        
        if not ucl_profile:
            return self.log_test("Competition Profiles Endpoint", False, "UCL profile not found")
        
        defaults = ucl_profile.get('defaults', {})
        
        # Verify updated defaults: clubSlots: 5, leagueSize: {min: 2, max: 8}
        club_slots_correct = defaults.get('club_slots') == 5
        league_size = defaults.get('league_size', {})
        league_size_correct = league_size.get('min') == 2 and league_size.get('max') == 8
        
        # Check UEL profile as well
        uel_profile = None
        for profile in profiles:
            if profile.get('id') == 'uel' or profile.get('short_name') == 'UEL':
                uel_profile = profile
                break
        
        uel_correct = True
        if uel_profile:
            uel_defaults = uel_profile.get('defaults', {})
            uel_club_slots = uel_defaults.get('club_slots') == 5
            uel_league_size = uel_defaults.get('league_size', {})
            uel_size_correct = uel_league_size.get('min') == 2 and uel_league_size.get('max') == 6
            uel_correct = uel_club_slots and uel_size_correct
        
        return self.log_test(
            "Competition Profiles Endpoint",
            club_slots_correct and league_size_correct and uel_correct,
            f"UCL - Club slots: {defaults.get('club_slots')} (expected 5), League size: {league_size.get('min')}-{league_size.get('max')} (expected 2-8), UEL correct: {uel_correct}"
        )
    
    def test_custom_profile_settings(self):
        """Test Custom competition profile has updated defaults"""
        success, status, data = self.make_request('GET', 'competition-profiles', token=None)
        
        if not success:
            return self.log_test("Custom Profile Settings", False, f"Failed to get profiles: {status}")
        
        profiles = data.get('profiles', [])
        custom_profile = None
        
        for profile in profiles:
            if profile.get('id') == 'custom' or profile.get('short_name') == 'Custom':
                custom_profile = profile
                break
        
        if not custom_profile:
            return self.log_test("Custom Profile Settings", False, "Custom profile not found")
        
        defaults = custom_profile.get('defaults', {})
        
        # Verify Custom profile: club_slots: 5, league_size: {min: 2, max: 8}
        club_slots_correct = defaults.get('club_slots') == 5
        league_size = defaults.get('league_size', {})
        league_size_correct = league_size.get('min') == 2 and league_size.get('max') == 8
        
        return self.log_test(
            "Custom Profile Settings",
            club_slots_correct and league_size_correct,
            f"Club slots: {defaults.get('club_slots')} (expected 5), League size: {league_size.get('min')}-{league_size.get('max')} (expected 2-8)"
        )

    def authenticate_with_dev_token(self):
        """Get authentication token using development magic link"""
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.commissioner_email},
            token=None
        )
        
        if not success:
            print(f"❌ Failed to request magic link: {status}")
            return False
        
        # Step 2: Use dev magic link if available
        if 'dev_magic_link' in data:
            magic_link = data['dev_magic_link']
            # Extract token from magic link
            token = magic_link.split('token=')[1] if 'token=' in magic_link else None
            
            if token:
                # Verify the token
                success, status, auth_data = self.make_request(
                    'POST',
                    'auth/verify',
                    {"token": token},
                    token=None
                )
                
                if success and 'access_token' in auth_data:
                    self.commissioner_token = auth_data['access_token']
                    print(f"✅ Authenticated as {auth_data['user']['email']}")
                    return True
        
        print("❌ Authentication failed - no dev token available")
        return False

    def test_league_creation_with_profile_defaults(self):
        """Test Create League uses competition profile defaults (not hardcoded 3)"""
        if not self.commissioner_token:
            return self.log_test("League Creation with Profile Defaults", False, "Not authenticated")
        
        # Create league without explicit settings to test profile integration
        league_data = {
            "name": f"Profile Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "competition_profile": "ucl"  # Explicitly use UCL profile
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if not success:
            return self.log_test("League Creation with Profile Defaults", False, f"Failed to create league: {status} - {data}")
        
        self.test_league_id_profile = data.get('id')
        settings = data.get('settings', {})
        
        # Verify league uses profile defaults (5 slots, min 2 managers)
        club_slots = settings.get('club_slots_per_manager')
        league_size = settings.get('league_size', {})
        min_managers = league_size.get('min')
        max_managers = league_size.get('max')
        
        profile_defaults_used = (
            club_slots == 5 and  # Updated from hardcoded 3
            min_managers == 2 and  # Updated from hardcoded 4
            max_managers == 8
        )
        
        return self.log_test(
            "League Creation with Profile Defaults",
            profile_defaults_used,
            f"Club slots: {club_slots} (expected 5), Min managers: {min_managers} (expected 2), Max managers: {max_managers} (expected 8)"
        )
    
    def test_league_creation_without_profile(self):
        """Test league creation without explicit profile uses UCL defaults"""
        if not self.commissioner_token:
            return self.log_test("League Creation without Profile", False, "Not authenticated")
        
        league_data = {
            "name": f"Default Profile League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
            # No competition_profile specified - should default to UCL
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if not success:
            return self.log_test("League Creation without Profile", False, f"Failed to create league: {status} - {data}")
        
        settings = data.get('settings', {})
        
        # Should still use UCL profile defaults
        club_slots = settings.get('club_slots_per_manager')
        league_size = settings.get('league_size', {})
        min_managers = league_size.get('min')
        
        ucl_defaults_used = club_slots == 5 and min_managers == 2
        
        return self.log_test(
            "League Creation without Profile",
            ucl_defaults_used,
            f"Uses UCL defaults - Club slots: {club_slots} (expected 5), Min managers: {min_managers} (expected 2)"
        )
    
    def test_frontend_league_settings_endpoint(self):
        """Test GET /api/leagues/{id}/settings returns centralized settings for frontend"""
        if not self.commissioner_token or not self.test_league_id_profile:
            return self.log_test("Frontend League Settings Endpoint", False, "Not authenticated or no test league")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id_profile}/settings')
        
        if not success:
            return self.log_test("Frontend League Settings Endpoint", False, f"Failed to get settings: {status} - {data}")
        
        # Verify response structure for frontend consumption
        has_club_slots = 'clubSlots' in data
        has_budget = 'budgetPerManager' in data
        has_league_size = 'leagueSize' in data and isinstance(data['leagueSize'], dict)
        
        if has_league_size:
            league_size = data['leagueSize']
            has_min_max = 'min' in league_size and 'max' in league_size
        else:
            has_min_max = False
        
        # Verify values match profile defaults
        club_slots_correct = data.get('clubSlots') == 5
        min_correct = data.get('leagueSize', {}).get('min') == 2
        
        frontend_ready = has_club_slots and has_budget and has_league_size and has_min_max and club_slots_correct and min_correct
        
        return self.log_test(
            "Frontend League Settings Endpoint",
            frontend_ready,
            f"Structure complete: {has_club_slots and has_budget and has_league_size and has_min_max}, Values correct: {club_slots_correct and min_correct}"
        )

    def run_tests(self):
        """Run all competition profile tests"""
        print("🏅 Starting Competition Profile Integration Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Test endpoints that don't require authentication first
        print("\n📊 COMPETITION PROFILE ENDPOINTS")
        self.test_competition_profiles_endpoint()
        self.test_custom_profile_settings()
        
        # Authenticate for league creation tests
        print("\n🔐 AUTHENTICATION")
        if self.authenticate_with_dev_token():
            print("\n🏟️ LEAGUE CREATION WITH PROFILES")
            self.test_league_creation_with_profile_defaults()
            self.test_league_creation_without_profile()
            self.test_frontend_league_settings_endpoint()
        else:
            print("⚠️ Skipping authenticated tests - authentication failed")
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 COMPETITION PROFILE TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All competition profile tests passed!")
            return 0
        else:
            print(f"\n⚠️ {len(self.failed_tests)} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = CompetitionProfileTester()
    return tester.run_tests()

if __name__ == "__main__":
    sys.exit(main())