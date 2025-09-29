#!/usr/bin/env python3
"""
Authentication Session Persistence Test
Tests the specific authentication session persistence fix for the atomic post-create flow.
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class AuthSessionTester:
    def __init__(self, base_url="https://magic-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()  # Use session to maintain cookies
        self.test_email = f"auth_test_{int(time.time())}@example.com"
        self.test_league_id = None
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
        """Make HTTP request using session to maintain cookies"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
            
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_test_login_flow(self):
        """Test 1: Call POST /api/auth/test-login with a test email and verify it returns 200 with {ok: true}"""
        print(f"\n🧪 Testing test-login flow with email: {self.test_email}")
        
        success, status, data = self.make_request(
            'POST', 
            'auth/test-login', 
            {"email": self.test_email},
            expected_status=200
        )
        
        if not success:
            return self.log_test("Test-Login Flow", False, f"Status: {status}, Response: {data}")
        
        # Verify response structure
        login_valid = (
            data.get('ok') is True and
            'userId' in data and
            'email' in data and
            data['email'] == self.test_email
        )
        
        return self.log_test(
            "Test-Login Flow",
            login_valid,
            f"Status: {status}, OK: {data.get('ok')}, Email: {data.get('email')}"
        )

    def test_session_verification(self):
        """Test 2: After test-login, call GET /api/auth/me to verify the session cookie is working"""
        print(f"\n🔐 Testing session verification via /auth/me")
        
        success, status, data = self.make_request('GET', 'auth/me', expected_status=200)
        
        if not success:
            return self.log_test("Session Verification", False, f"Status: {status}, Response: {data}")
        
        # Verify user data matches test login
        session_valid = (
            'id' in data and
            'email' in data and
            'verified' in data and
            data['email'] == self.test_email and
            data['verified'] is True
        )
        
        return self.log_test(
            "Session Verification",
            session_valid,
            f"Status: {status}, Email: {data.get('email')}, Verified: {data.get('verified')}"
        )

    def test_league_creation_flow(self):
        """Test 3: Test the complete league creation flow to see if authentication persists through the API calls"""
        print(f"\n🏟️ Testing league creation with persistent authentication")
        
        league_data = {
            "name": f"Auth Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 3,
                "bid_timer_seconds": 60,
                "anti_snipe_seconds": 30,
                "league_size": {
                    "min": 2,
                    "max": 8
                }
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data, expected_status=201)
        
        if not success:
            return self.log_test("League Creation Flow", False, f"Status: {status}, Response: {data}")
        
        # Verify league creation response
        league_valid = 'leagueId' in data
        
        if league_valid:
            self.test_league_id = data['leagueId']
        
        return self.log_test(
            "League Creation Flow",
            league_valid,
            f"Status: {status}, League ID: {data.get('leagueId', 'None')}"
        )

    def test_league_access(self):
        """Test 4: Test GET /api/leagues/{id} to ensure the user can access the league they created"""
        if not self.test_league_id:
            return self.log_test("League Access", False, "No test league ID available")
        
        print(f"\n🔍 Testing league access for league: {self.test_league_id}")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}', expected_status=200)
        
        if not success:
            return self.log_test("League Access", False, f"Status: {status}, Response: {data}")
        
        # Verify league data access
        access_valid = (
            'id' in data and
            'name' in data and
            'settings' in data and
            data['id'] == self.test_league_id
        )
        
        return self.log_test(
            "League Access",
            access_valid,
            f"Status: {status}, League Name: {data.get('name', 'Unknown')}"
        )

    def test_additional_authenticated_endpoints(self):
        """Test additional authenticated endpoints to verify session persistence"""
        print(f"\n🔄 Testing additional authenticated endpoints")
        
        results = []
        
        # Test user profile endpoint
        success, status, data = self.make_request('GET', 'auth/me')
        results.append(success and status == 200)
        
        # Test leagues list endpoint
        success2, status2, data2 = self.make_request('GET', 'leagues')
        results.append(success2 and status2 == 200)
        
        # Test league members endpoint (if we have a league)
        if self.test_league_id:
            success3, status3, data3 = self.make_request('GET', f'leagues/{self.test_league_id}/members')
            results.append(success3 and status3 == 200)
        else:
            results.append(True)  # Skip if no league
        
        # Test league status endpoint (if we have a league)
        if self.test_league_id:
            success4, status4, data4 = self.make_request('GET', f'leagues/{self.test_league_id}/status')
            results.append(success4 and status4 == 200)
        else:
            results.append(True)  # Skip if no league
        
        all_endpoints_work = all(results)
        
        return self.log_test(
            "Additional Authenticated Endpoints",
            all_endpoints_work,
            f"Working endpoints: {sum(results)}/{len(results)}"
        )

    def test_session_cookie_details(self):
        """Test session cookie details and configuration"""
        print(f"\n🍪 Testing session cookie configuration")
        
        # Make a request and check cookies
        success, status, data = self.make_request('GET', 'auth/me')
        
        if not success:
            return self.log_test("Session Cookie Details", False, f"Auth/me failed: {status}")
        
        # Check if we have cookies set
        cookies = self.session.cookies
        has_access_token = 'access_token' in cookies
        
        cookie_details = []
        if has_access_token:
            access_token_cookie = cookies['access_token']
            # Simple cookie details check
            cookie_details.append(f"Value present: {bool(access_token_cookie)}")
            cookie_details.append(f"Cookie name: access_token")
        
        return self.log_test(
            "Session Cookie Details",
            has_access_token,
            f"Has access_token cookie: {has_access_token}, Details: {', '.join(cookie_details)}"
        )

    def run_auth_session_tests(self):
        """Run all authentication session persistence tests"""
        print("🔐 AUTHENTICATION SESSION PERSISTENCE TEST SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print(f"Test Email: {self.test_email}")
        print("=" * 60)
        
        # Environment check
        print("\n🔧 Environment Configuration Check")
        success, status, data = self.make_request('GET', 'health')
        if success:
            print(f"✅ Backend health check passed")
        else:
            print(f"❌ Backend health check failed: {status}")
            return False
        
        # Run the specific tests requested in the review
        print("\n🧪 CORE AUTHENTICATION SESSION TESTS")
        
        # Test 1: Test-Login Flow
        if not self.test_test_login_flow():
            print("❌ Test-login failed - cannot proceed with session tests")
            return False
        
        # Test 2: Session Verification
        if not self.test_session_verification():
            print("❌ Session verification failed - authentication session not working")
            return False
        
        # Test 3: League Creation Flow
        if not self.test_league_creation_flow():
            print("❌ League creation failed - authentication not persisting for API calls")
            return False
        
        # Test 4: League Access
        if not self.test_league_access():
            print("❌ League access failed - user cannot access created league")
            return False
        
        # Additional tests
        print("\n🔄 ADDITIONAL SESSION PERSISTENCE TESTS")
        self.test_additional_authenticated_endpoints()
        self.test_session_cookie_details()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 AUTHENTICATION SESSION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        # Critical assessment
        core_tests_passed = (
            "Test-Login Flow" not in [t.split(':')[0] for t in self.failed_tests] and
            "Session Verification" not in [t.split(':')[0] for t in self.failed_tests] and
            "League Creation Flow" not in [t.split(':')[0] for t in self.failed_tests] and
            "League Access" not in [t.split(':')[0] for t in self.failed_tests]
        )
        
        print(f"\n🎯 CORE AUTHENTICATION SESSION PERSISTENCE: {'✅ WORKING' if core_tests_passed else '❌ FAILED'}")
        
        if core_tests_passed:
            print("✅ Authentication session persistence is working correctly!")
            print("✅ Test-login → session cookie → API access flow is functional")
            print("✅ Atomic post-create flow should work without 403 errors")
        else:
            print("❌ Authentication session persistence has issues!")
            print("❌ This will cause 403 errors in the atomic post-create flow")
            print("❌ Lobby loading will fail due to authentication problems")
        
        return core_tests_passed

if __name__ == "__main__":
    tester = AuthSessionTester()
    success = tester.run_auth_session_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)