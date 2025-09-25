#!/usr/bin/env python3
"""
UCL Auction Backend API Testing Suite - Simplified Version
Tests basic functionality and provides manual authentication guidance
"""

import requests
import sys
import json
from datetime import datetime

class SimpleAPITester:
    def __init__(self, base_url="https://champion-bid-portal.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
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

    def make_request(self, method, endpoint, data=None, expected_status=200, token=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
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

    def test_health_check(self):
        """Test health check endpoint"""
        success, status, data = self.make_request('GET', 'health')
        return self.log_test(
            "Health Check", 
            success and 'status' in data and data['status'] == 'healthy',
            f"Status: {status}"
        )

    def test_get_clubs(self):
        """Test get all clubs endpoint (no auth required)"""
        success, status, data = self.make_request('GET', 'clubs')
        clubs_count = len(data) if isinstance(data, list) else 0
        return self.log_test(
            "Get Clubs",
            success and isinstance(data, list) and clubs_count >= 16,
            f"Status: {status}, Clubs found: {clubs_count}"
        )

    def test_magic_link_request(self):
        """Test magic link request (no auth required)"""
        test_email = "test@example.com"
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": test_email}
        )
        return self.log_test(
            "Magic Link Request",
            success and 'message' in data,
            f"Status: {status}, Email: {test_email}"
        )

    def test_invalid_token_verify(self):
        """Test invalid token verification"""
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": "invalid_token"},
            expected_status=400
        )
        return self.log_test(
            "Invalid Token Verify",
            success and status == 400,
            f"Status: {status} (correctly rejected invalid token)"
        )

    def test_unauthorized_access(self):
        """Test that protected endpoints require authentication"""
        # Test league creation without auth
        success, status, data = self.make_request(
            'POST',
            'leagues',
            {"name": "Test League", "season": "2025-26"},
            expected_status=403
        )
        
        auth_required = success and status == 403
        
        # Test auth/me without token
        success2, status2, data2 = self.make_request(
            'GET',
            'auth/me',
            expected_status=403  # Updated to expect 403 instead of 401
        )
        
        auth_required2 = success2 and status2 == 403
        
        return self.log_test(
            "Unauthorized Access Protection",
            auth_required and auth_required2,
            f"League creation: {status}, Auth me: {status2} (both correctly protected)"
        )

    def test_with_token(self, token):
        """Test authenticated endpoints with provided token"""
        if not token:
            return self.log_test("Authenticated Tests", False, "No token provided")
        
        print(f"\n🔑 Testing with provided token...")
        
        # Test auth/me
        success, status, user_data = self.make_request('GET', 'auth/me', token=token)
        if not success:
            return self.log_test("Token Validation", False, f"Token invalid: {status}")
        
        print(f"✅ Authenticated as: {user_data.get('email', 'Unknown')}")
        
        # Test league creation
        league_data = {
            "name": f"Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 3,
                "max_managers": 8,
                "min_managers": 4,
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        success, status, league = self.make_request(
            'POST', 'leagues', league_data, token=token
        )
        
        if not success:
            return self.log_test("League Creation", False, f"Failed: {status}")
        
        league_id = league.get('id')
        print(f"✅ Created league: {league.get('name')} (ID: {league_id})")
        
        # Test league members
        success, status, members = self.make_request(
            'GET', f'leagues/{league_id}/members', token=token
        )
        
        members_valid = success and len(members) == 1 and members[0]['role'] == 'commissioner'
        
        # Test league status
        success, status, league_status = self.make_request(
            'GET', f'leagues/{league_id}/status', token=token
        )
        
        status_valid = success and not league_status.get('is_ready', True)  # Should not be ready with 1 member
        
        # Test invitation
        success, status, invitation = self.make_request(
            'POST', f'leagues/{league_id}/invite',
            {"league_id": league_id, "email": "manager@example.com"},
            token=token
        )
        
        invitation_valid = success and 'id' in invitation
        
        return self.log_test(
            "Authenticated League Tests",
            members_valid and status_valid and invitation_valid,
            f"Members: {len(members) if 'members' in locals() else 0}, Status valid: {status_valid}, Invitation: {invitation_valid}"
        )

    def run_basic_tests(self):
        """Run basic API tests"""
        print("🚀 Starting UCL Auction Basic API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Basic connectivity tests
        print("\n📡 CONNECTIVITY & PUBLIC ENDPOINT TESTS")
        self.test_health_check()
        self.test_get_clubs()
        
        # Authentication flow tests
        print("\n🔐 AUTHENTICATION FLOW TESTS")
        self.test_magic_link_request()
        self.test_invalid_token_verify()
        self.test_unauthorized_access()
        
        # Instructions for manual testing
        print("\n" + "=" * 70)
        print("🔑 MANUAL AUTHENTICATION TESTING")
        print("To test authenticated endpoints:")
        print("1. Check backend logs for magic link tokens")
        print("2. Extract a token from the logs")
        print("3. Run: python backend_test_simple.py <token>")
        print("4. Or use the test_with_token() method directly")
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 BASIC TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All basic tests passed!")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = SimpleAPITester()
    
    # Check if token provided as command line argument
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"🔑 Testing with provided token: {token[:20]}...")
        tester.run_basic_tests()
        tester.test_with_token(token)
    else:
        return tester.run_basic_tests()

if __name__ == "__main__":
    sys.exit(main())