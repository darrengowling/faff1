#!/usr/bin/env python3
"""
Test AdminService no longer has hardcoded fallbacks
"""

import requests
import sys
import json
from datetime import datetime

class AdminServiceFallbackTester:
    def __init__(self, base_url="https://pifa-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.commissioner_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.commissioner_email = "commissioner@example.com"
        self.test_league_id = None
        
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
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

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

    def test_league_creation_uses_profile_defaults(self):
        """Test that new leagues use profile defaults, not hardcoded values"""
        if not self.commissioner_token:
            return self.log_test("League Creation Uses Profile Defaults", False, "Not authenticated")
        
        # Create league with UCL profile
        league_data = {
            "name": f"Admin Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "competition_profile": "ucl"
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if not success:
            return self.log_test("League Creation Uses Profile Defaults", False, f"Failed to create league: {status} - {data}")
        
        self.test_league_id = data.get('id')
        settings = data.get('settings', {})
        
        # Verify no hardcoded fallbacks (should be 5, not 3 for club_slots)
        club_slots = settings.get('club_slots_per_manager')
        league_size = settings.get('league_size', {})
        min_managers = league_size.get('min')
        
        no_hardcoded_fallbacks = (
            club_slots == 5 and  # Not hardcoded 3
            min_managers == 2    # Not hardcoded 4
        )
        
        return self.log_test(
            "League Creation Uses Profile Defaults",
            no_hardcoded_fallbacks,
            f"Club slots: {club_slots} (expected 5, not 3), Min managers: {min_managers} (expected 2, not 4)"
        )

    def test_admin_dashboard_minimum_size_calculation(self):
        """Test that AdminDashboard uses dynamic minimum size (not hardcoded 4)"""
        if not self.commissioner_token or not self.test_league_id:
            return self.log_test("Admin Dashboard Minimum Size", False, "Not authenticated or no test league")
        
        # Get league status to verify minimum size calculation
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        
        if not success:
            return self.log_test("Admin Dashboard Minimum Size", False, f"Failed to get league status: {status}")
        
        # Verify minimum size is from profile (2), not hardcoded (4)
        min_members = data.get('min_members')
        member_count = data.get('member_count', 0)
        is_ready = data.get('is_ready', False)
        
        # With 1 member and min=2, should not be ready
        correct_minimum = min_members == 2
        correct_ready_status = not is_ready if member_count < 2 else True
        
        return self.log_test(
            "Admin Dashboard Minimum Size",
            correct_minimum and correct_ready_status,
            f"Min members: {min_members} (expected 2, not 4), Ready with {member_count} members: {is_ready}"
        )

    def test_league_settings_endpoint_no_fallbacks(self):
        """Test that league settings endpoint returns profile values, not fallbacks"""
        if not self.commissioner_token or not self.test_league_id:
            return self.log_test("League Settings No Fallbacks", False, "Not authenticated or no test league")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        
        if not success:
            return self.log_test("League Settings No Fallbacks", False, f"Failed to get settings: {status}")
        
        # Verify values are from profile, not hardcoded fallbacks
        club_slots = data.get('clubSlots')
        league_size = data.get('leagueSize', {})
        min_size = league_size.get('min')
        
        no_fallbacks = (
            club_slots == 5 and  # Not fallback 3
            min_size == 2        # Not fallback 4
        )
        
        return self.log_test(
            "League Settings No Fallbacks",
            no_fallbacks,
            f"Club slots: {club_slots} (expected 5), Min size: {min_size} (expected 2)"
        )

    def test_admin_settings_update_validation(self):
        """Test that admin settings updates work with new minimum values"""
        if not self.commissioner_token or not self.test_league_id:
            return self.log_test("Admin Settings Update Validation", False, "Not authenticated or no test league")
        
        # Try to update league settings - should work with new minimums
        settings_update = {
            "club_slots_per_manager": 6,  # Increase from 5
            "league_size": {
                "min": 2,  # Keep minimum at 2 (new default)
                "max": 8   # Keep maximum at 8 (constraint limit)
            }
        }
        
        success, status, data = self.make_request('PATCH', f'leagues/{self.test_league_id}/settings', settings_update)
        
        if not success:
            return self.log_test("Admin Settings Update Validation", False, f"Failed to update settings: {status} - {data}")
        
        # Verify the update worked
        success_verify, status_verify, verify_data = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        
        if not success_verify:
            return self.log_test("Admin Settings Update Validation", False, f"Failed to verify update: {status_verify}")
        
        updated_correctly = (
            verify_data.get('clubSlots') == 6 and
            verify_data.get('leagueSize', {}).get('min') == 2 and
            verify_data.get('leagueSize', {}).get('max') == 8
        )
        
        return self.log_test(
            "Admin Settings Update Validation",
            updated_correctly,
            f"Settings updated correctly: {updated_correctly}"
        )

    def run_tests(self):
        """Run all admin service fallback tests"""
        print("🔐 Starting Admin Service Fallback Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Authenticate
        print("\n🔐 AUTHENTICATION")
        if not self.authenticate_with_dev_token():
            print("⚠️ Skipping tests - authentication failed")
            return 1
        
        print("\n🏟️ ADMIN SERVICE FALLBACK TESTS")
        self.test_league_creation_uses_profile_defaults()
        self.test_admin_dashboard_minimum_size_calculation()
        self.test_league_settings_endpoint_no_fallbacks()
        self.test_admin_settings_update_validation()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 ADMIN SERVICE FALLBACK TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All admin service fallback tests passed!")
            print("✅ No hardcoded fallbacks detected")
            print("✅ Profile defaults are being used correctly")
            return 0
        else:
            print(f"\n⚠️ {len(self.failed_tests)} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = AdminServiceFallbackTester()
    return tester.run_tests()

if __name__ == "__main__":
    sys.exit(main())