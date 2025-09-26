#!/usr/bin/env python3
"""
UCL Auction Backend API Testing Suite - With Authentication
Tests the complete league management system with proper authentication
"""

import requests
import sys
import json
from datetime import datetime

class AuthenticatedAPITester:
    def __init__(self, base_url="https://friends-of-pifa.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.access_token = None
        self.user_data = None
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

    def authenticate_with_magic_token(self, magic_token):
        """Authenticate using magic link token"""
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": magic_token}
        )
        
        if success and 'access_token' in data:
            self.access_token = data['access_token']
            self.user_data = data['user']
            return True, f"Authenticated as {data['user']['email']}"
        
        return False, f"Authentication failed: {status} - {data}"

    def test_comprehensive_league_management(self):
        """Test comprehensive league management features"""
        if not self.access_token:
            return self.log_test("League Management", False, "Not authenticated")
        
        print(f"\n👤 Testing as: {self.user_data['email']}")
        
        # Test 1: Enhanced League Creation
        league_data = {
            "name": f"Elite UCL League 2025-26 {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "max_managers": 8,
                "min_managers": 4,
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        success, status, league = self.make_request('POST', 'leagues', league_data)
        if not success:
            return self.log_test("Enhanced League Creation", False, f"Failed: {status}")
        
        league_id = league['id']
        self.log_test("Enhanced League Creation", True, f"Created: {league['name']}")
        
        # Test 2: Verify League Documents Creation
        success, status, members = self.make_request('GET', f'leagues/{league_id}/members')
        members_valid = success and len(members) == 1 and members[0]['role'] == 'commissioner'
        self.log_test("League Documents Creation", members_valid, f"Commissioner membership created")
        
        # Test 3: League Settings Validation
        success, status, league_details = self.make_request('GET', f'leagues/{league_id}')
        settings = league_details.get('settings', {}) if success else {}
        settings_valid = (
            settings.get('budget_per_manager') == 100 and
            settings.get('max_managers') == 8 and
            settings.get('min_managers') == 4 and
            settings.get('scoring_rules', {}).get('club_win') == 3
        )
        self.log_test("League Settings Validation", settings_valid, "All settings properly stored")
        
        # Test 4: League Status (should not be ready with 1 member)
        success, status, league_status = self.make_request('GET', f'leagues/{league_id}/status')
        status_valid = success and not league_status.get('is_ready', True) and league_status.get('member_count') == 1
        self.log_test("League Size Validation", status_valid, f"Not ready with 1 member: {league_status.get('is_ready', 'unknown')}")
        
        # Test 5: Invitation Management
        invitation_results = []
        manager_emails = ["manager1@example.com", "manager2@example.com", "manager3@example.com"]
        
        for email in manager_emails:
            success, status, invitation = self.make_request(
                'POST', f'leagues/{league_id}/invite',
                {"league_id": league_id, "email": email}
            )
            invitation_results.append(success)
            if success:
                print(f"   📧 Invited {email}")
        
        invitations_sent = sum(invitation_results)
        self.log_test("Invitation Management", invitations_sent >= 2, f"Sent {invitations_sent}/3 invitations")
        
        # Test 6: Get League Invitations (Commissioner only)
        success, status, invitations = self.make_request('GET', f'leagues/{league_id}/invitations')
        invitations_valid = success and len(invitations) >= 2
        self.log_test("Commissioner Access Control", invitations_valid, f"Retrieved {len(invitations) if success else 0} invitations")
        
        # Test 7: Duplicate Invitation Prevention
        success, status, data = self.make_request(
            'POST', f'leagues/{league_id}/invite',
            {"league_id": league_id, "email": manager_emails[0]},
            expected_status=400
        )
        duplicate_prevented = success and status == 400
        self.log_test("Duplicate Invitation Prevention", duplicate_prevented, "Correctly rejected duplicate")
        
        # Test 8: Join League (simulate invitation acceptance)
        join_results = []
        for i in range(3):  # Try to add 3 more members
            success, status, data = self.make_request('POST', f'leagues/{league_id}/join')
            join_results.append(success)
        
        joins_successful = sum(join_results)
        self.log_test("League Joining", joins_successful >= 2, f"Added {joins_successful} members")
        
        # Test 9: League Readiness Check
        success, status, updated_status = self.make_request('GET', f'leagues/{league_id}/status')
        if success:
            member_count = updated_status.get('member_count', 0)
            is_ready = updated_status.get('is_ready', False)
            ready_valid = member_count >= 4 and is_ready
            self.log_test("League Readiness", ready_valid, f"Members: {member_count}, Ready: {is_ready}")
        else:
            self.log_test("League Readiness", False, "Failed to get status")
        
        # Test 10: Resend Invitation
        if invitations_valid and len(invitations) > 0:
            invitation_id = invitations[0]['id']
            success, status, data = self.make_request(
                'POST', f'leagues/{league_id}/invitations/{invitation_id}/resend'
            )
            self.log_test("Invitation Resend", success, f"Status: {status}")
        else:
            self.log_test("Invitation Resend", False, "No invitations to resend")
        
        return True

    def run_comprehensive_tests(self, magic_token):
        """Run comprehensive tests with authentication"""
        print("🚀 Starting UCL Auction Comprehensive Tests with Authentication")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Authenticate
        print("\n🔐 AUTHENTICATION")
        auth_success, auth_msg = self.authenticate_with_magic_token(magic_token)
        if not auth_success:
            print(f"❌ Authentication failed: {auth_msg}")
            return 1
        
        print(f"✅ {auth_msg}")
        
        # Run comprehensive tests
        print("\n🏟️ COMPREHENSIVE LEAGUE MANAGEMENT TESTS")
        self.test_comprehensive_league_management()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 COMPREHENSIVE TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All comprehensive tests passed!")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed")
            return 1

def main():
    """Main test runner"""
    if len(sys.argv) < 2:
        print("Usage: python backend_test_auth.py <magic_link_token>")
        print("Extract magic link token from backend logs")
        return 1
    
    magic_token = sys.argv[1]
    tester = AuthenticatedAPITester()
    return tester.run_comprehensive_tests(magic_token)

if __name__ == "__main__":
    sys.exit(main())