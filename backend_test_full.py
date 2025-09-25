#!/usr/bin/env python3
"""
UCL Auction Backend API Full Testing Suite
Tests complete authentication flow and all endpoints
"""

import requests
import sys
import json
import re
from datetime import datetime
import time

class UCLAuctionFullTester:
    def __init__(self, base_url="https://pifa-friends.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_email = "test@example.com"
        self.test_league_id = None
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
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

    def extract_magic_link_token(self):
        """Extract magic link token from backend logs"""
        try:
            # Read recent backend logs
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "100", "/var/log/supervisor/backend.out.log"],
                capture_output=True, text=True
            )
            
            # Look for magic link token in logs
            pattern = r'token=([A-Za-z0-9\-_\.]+)'
            matches = re.findall(pattern, result.stdout)
            
            if matches:
                return matches[-1]  # Return the most recent token
            return None
            
        except Exception as e:
            print(f"Failed to extract token from logs: {e}")
            return None

    def test_complete_auth_flow(self):
        """Test complete authentication flow"""
        print("\n🔐 COMPLETE AUTHENTICATION FLOW")
        
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email}
        )
        
        if not self.log_test(
            "Magic Link Request",
            success and 'message' in data,
            f"Status: {status}"
        ):
            return False
        
        # Step 2: Extract token from logs
        print("🔍 Extracting magic link token from backend logs...")
        time.sleep(1)  # Wait for log to be written
        token = self.extract_magic_link_token()
        
        if not token:
            print("❌ Could not extract magic link token from logs")
            return False
        
        print(f"✅ Extracted token: {token[:20]}...")
        
        # Step 3: Verify magic link token
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token}
        )
        
        if not self.log_test(
            "Magic Link Verification",
            success and 'access_token' in data and 'user' in data,
            f"Status: {status}"
        ):
            return False
        
        # Store access token and user data
        self.token = data['access_token']
        self.user_data = data['user']
        
        print(f"✅ Authenticated as: {self.user_data['display_name']} ({self.user_data['email']})")
        
        # Step 4: Test /auth/me with valid token
        success, status, data = self.make_request('GET', 'auth/me')
        return self.log_test(
            "Auth Me With Token",
            success and 'id' in data and data['email'] == self.test_email,
            f"Status: {status}, User: {data.get('display_name', 'Unknown')}"
        )

    def test_authenticated_endpoints(self):
        """Test endpoints that require authentication"""
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        print("\n🏆 AUTHENTICATED ENDPOINTS")
        
        # Test clubs seed
        success, status, data = self.make_request('POST', 'clubs/seed')
        self.log_test(
            "Clubs Seed",
            success and 'message' in data,
            f"Status: {status}, Message: {data.get('message', 'No message')}"
        )
        
        # Test get clubs
        success, status, data = self.make_request('GET', 'clubs')
        clubs_count = len(data) if isinstance(data, list) else 0
        self.log_test(
            "Get Clubs",
            success and isinstance(data, list) and clubs_count > 0,
            f"Status: {status}, Clubs found: {clubs_count}"
        )
        
        # Test create league
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
            
        self.log_test(
            "Create League",
            success and 'id' in data and 'name' in data,
            f"Status: {status}, League: {data.get('name', 'Unknown')}"
        )
        
        # Test get my leagues
        success, status, data = self.make_request('GET', 'leagues')
        leagues_count = len(data) if isinstance(data, list) else 0
        self.log_test(
            "Get My Leagues",
            success and isinstance(data, list) and leagues_count > 0,
            f"Status: {status}, Leagues found: {leagues_count}"
        )
        
        # Test get league details
        if self.test_league_id:
            success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}')
            self.log_test(
                "Get League Details",
                success and 'id' in data and data['id'] == self.test_league_id,
                f"Status: {status}, League: {data.get('name', 'Unknown')}"
            )
            
            # Test get league members
            success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/members')
            members_count = len(data) if isinstance(data, list) else 0
            self.log_test(
                "Get League Members",
                success and isinstance(data, list) and members_count > 0,
                f"Status: {status}, Members found: {members_count}"
            )
        
        # Test update profile
        new_display_name = f"Test User {datetime.now().strftime('%H%M%S')}"
        success, status, data = self.make_request(
            'PUT',
            'users/me',
            {"display_name": new_display_name}
        )
        self.log_test(
            "Update Profile",
            success and 'display_name' in data and data['display_name'] == new_display_name,
            f"Status: {status}, New name: {data.get('display_name', 'None')}"
        )

    def test_access_control(self):
        """Test access control and security"""
        if not self.token:
            return
            
        print("\n🔒 ACCESS CONTROL TESTS")
        
        # Test accessing non-existent league
        fake_league_id = "00000000-0000-0000-0000-000000000000"
        success, status, data = self.make_request(
            'GET',
            f'leagues/{fake_league_id}',
            expected_status=404
        )
        self.log_test(
            "Non-existent League Access",
            success and status == 404,
            f"Status: {status}, Response: {data.get('detail', 'No detail')}"
        )
        
        # Test accessing another user's data (should fail)
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        success, status, data = self.make_request(
            'GET',
            f'users/{fake_user_id}',
            expected_status=404
        )
        self.log_test(
            "Non-existent User Access",
            success and status == 404,
            f"Status: {status}, Response: {data.get('detail', 'No detail')}"
        )

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting UCL Auction Full API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity test
        print("\n📡 CONNECTIVITY TESTS")
        success, status, data = self.make_request('GET', 'health')
        self.log_test(
            "Health Check", 
            success and 'status' in data and data['status'] == 'healthy',
            f"Status: {status}"
        )
        
        # Complete authentication flow
        if not self.test_complete_auth_flow():
            print("\n❌ Authentication failed - cannot test protected endpoints")
            return 1
        
        # Test authenticated endpoints
        self.test_authenticated_endpoints()
        
        # Test access control
        self.test_access_control()
        
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
    tester = UCLAuctionFullTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())