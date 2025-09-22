#!/usr/bin/env python3
"""
UCL Auction Backend API Testing Suite - Enhanced League Management
Tests comprehensive league creation, invitation management, and commissioner controls
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class UCLAuctionAPITester:
    def __init__(self, base_url="https://champbid-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.commissioner_token = None
        self.manager_tokens = {}
        self.user_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.commissioner_email = "commissioner@example.com"
        self.manager_emails = [
            "manager1@example.com",
            "manager2@example.com", 
            "manager3@example.com",
            "manager4@example.com",
            "manager5@example.com"
        ]
        self.test_league_id = None
        self.test_invitations = []
        
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
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
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
            f"Status: {status}, Response: {data}"
        )

    def test_magic_link_request(self):
        """Test magic link request endpoint"""
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email}
        )
        return self.log_test(
            "Magic Link Request",
            success and 'message' in data,
            f"Status: {status}, Message: {data.get('message', 'No message')}"
        )

    def test_invalid_magic_link_verify(self):
        """Test magic link verification with invalid token"""
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": "invalid_token"},
            expected_status=400
        )
        return self.log_test(
            "Invalid Magic Link Verify",
            success and status == 400,
            f"Status: {status}, Response: {data}"
        )

    def test_auth_me_without_token(self):
        """Test /auth/me without authentication token"""
        # Temporarily remove token
        temp_token = self.token
        self.token = None
        
        success, status, data = self.make_request(
            'GET',
            'auth/me',
            expected_status=401
        )
        
        # Restore token
        self.token = temp_token
        
        return self.log_test(
            "Auth Me Without Token",
            success and status == 401,
            f"Status: {status}, Response: {data}"
        )

    def test_clubs_seed(self):
        """Test clubs seeding endpoint"""
        success, status, data = self.make_request('POST', 'clubs/seed')
        return self.log_test(
            "Clubs Seed",
            success and 'message' in data,
            f"Status: {status}, Message: {data.get('message', 'No message')}"
        )

    def test_get_clubs(self):
        """Test get all clubs endpoint"""
        success, status, data = self.make_request('GET', 'clubs')
        clubs_count = len(data) if isinstance(data, list) else 0
        return self.log_test(
            "Get Clubs",
            success and isinstance(data, list) and clubs_count > 0,
            f"Status: {status}, Clubs found: {clubs_count}"
        )

    def test_create_league(self):
        """Test league creation"""
        league_data = {
            "name": f"Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2024-25"
        }
        
        success, status, data = self.make_request(
            'POST',
            'leagues',
            league_data,
            expected_status=201
        )
        
        if success and 'id' in data:
            self.test_league_id = data['id']
            
        return self.log_test(
            "Create League",
            success and 'id' in data and 'name' in data,
            f"Status: {status}, League ID: {data.get('id', 'None')}"
        )

    def test_get_my_leagues(self):
        """Test get user's leagues"""
        success, status, data = self.make_request('GET', 'leagues')
        leagues_count = len(data) if isinstance(data, list) else 0
        return self.log_test(
            "Get My Leagues",
            success and isinstance(data, list),
            f"Status: {status}, Leagues found: {leagues_count}"
        )

    def test_get_league_details(self):
        """Test get specific league details"""
        if not hasattr(self, 'test_league_id'):
            return self.log_test("Get League Details", False, "No test league ID available")
            
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}')
        return self.log_test(
            "Get League Details",
            success and 'id' in data and data['id'] == self.test_league_id,
            f"Status: {status}, League: {data.get('name', 'Unknown')}"
        )

    def test_get_league_members(self):
        """Test get league members"""
        if not hasattr(self, 'test_league_id'):
            return self.log_test("Get League Members", False, "No test league ID available")
            
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        members_count = len(data) if isinstance(data, list) else 0
        return self.log_test(
            "Get League Members",
            success and isinstance(data, list),
            f"Status: {status}, Members found: {members_count}"
        )

    def test_unauthorized_league_access(self):
        """Test accessing non-existent league (should fail)"""
        fake_league_id = "00000000-0000-0000-0000-000000000000"
        success, status, data = self.make_request(
            'GET',
            f'leagues/{fake_league_id}',
            expected_status=404
        )
        return self.log_test(
            "Unauthorized League Access",
            success and status == 404,
            f"Status: {status}, Response: {data}"
        )

    def test_update_profile(self):
        """Test profile update"""
        new_display_name = f"Test User {datetime.now().strftime('%H%M%S')}"
        success, status, data = self.make_request(
            'PUT',
            'users/me',
            {"display_name": new_display_name}
        )
        return self.log_test(
            "Update Profile",
            success and 'display_name' in data and data['display_name'] == new_display_name,
            f"Status: {status}, New name: {data.get('display_name', 'None')}"
        )

    def simulate_magic_link_auth(self):
        """Simulate successful magic link authentication"""
        print("\n🔗 Simulating Magic Link Authentication...")
        print("Note: In development, magic links are logged to console")
        print("For testing, we'll simulate a successful verification")
        
        # Create a mock token (in real scenario, this would come from email link)
        # For testing purposes, we'll create a user and simulate the auth flow
        
        # First, request magic link
        if not self.test_magic_link_request():
            return False
            
        # In a real scenario, user would click email link
        # For testing, we'll simulate having a valid token
        print("⚠️  Cannot fully test magic link verification without actual token from email")
        print("   This would require email integration or mock token generation")
        
        return True

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting UCL Auction API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        print("\n📡 CONNECTIVITY TESTS")
        self.test_health_check()
        
        # Authentication tests
        print("\n🔐 AUTHENTICATION TESTS")
        self.simulate_magic_link_auth()
        self.test_invalid_magic_link_verify()
        self.test_auth_me_without_token()
        
        # Club tests (these don't require auth)
        print("\n🏆 CLUB MANAGEMENT TESTS")
        self.test_clubs_seed()
        self.test_get_clubs()
        
        # Note: League and user tests require valid authentication
        print("\n⚠️  LEAGUE & USER TESTS SKIPPED")
        print("   These require valid JWT token from magic link verification")
        print("   In a real test scenario, you would:")
        print("   1. Request magic link")
        print("   2. Extract token from email/console")
        print("   3. Verify token to get JWT")
        print("   4. Run authenticated tests")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1

def main():
    """Main test runner"""
    tester = UCLAuctionAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())