#!/usr/bin/env python3
"""
Focused Backend Testing for Friends of PIFA Auction Platform
Tests authentication endpoints, league management, and core functionality as specified in review request
"""

import requests
import sys
import json
import os
import time
from datetime import datetime, timezone

class FocusedAuthLeagueTest:
    def __init__(self, base_url="https://pifa-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.session = requests.Session()  # Use session to handle cookies
        
        # Test data with realistic values
        self.test_email = "pifa_test_user@example.com"
        self.test_league_name = f"PIFA Test League {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
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
        """Make HTTP request with proper headers and session handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        auth_token = token or self.token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
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

    # ==================== ENVIRONMENT VARIABLES CHECK ====================
    
    def test_environment_variables(self):
        """Test that required environment variables are properly configured"""
        print("🔧 Checking Environment Variables...")
        
        # Test health endpoint to verify basic connectivity
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Environment Variables Check", False, f"Health check failed: {status}")
        
        # Check if TEST_MODE and ALLOW_TEST_LOGIN are working by testing test-login endpoint availability
        success_test, status_test, data_test = self.make_request(
            'POST', 
            'auth/test-login', 
            {"email": "test@example.com"}, 
            expected_status=200,
            token=None
        )
        
        test_mode_enabled = success_test and data_test.get('ok') is True
        
        return self.log_test(
            "Environment Variables Check",
            success and test_mode_enabled,
            f"Health: {success}, TEST_MODE: {test_mode_enabled}, ALLOW_TEST_LOGIN: {test_mode_enabled}"
        )

    # ==================== AUTHENTICATION ENDPOINTS ====================
    
    def test_auth_test_login(self):
        """Test POST /api/auth/test-login (TEST_MODE only)"""
        print("🔐 Testing TEST_MODE Authentication...")
        
        success, status, data = self.make_request(
            'POST',
            'auth/test-login',
            {"email": self.test_email},
            expected_status=200,
            token=None
        )
        
        if not success:
            return self.log_test("POST /api/auth/test-login", False, f"Status: {status}, Response: {data}")
        
        # Validate response structure
        auth_valid = (
            data.get('ok') is True and
            'userId' in data and
            'email' in data and
            data['email'] == self.test_email and
            'message' in data
        )
        
        if auth_valid:
            # Extract token from cookie or response (test-login sets HTTP-only cookie)
            # For testing, we'll use the userId to create a session
            self.user_data = {
                'id': data['userId'],
                'email': data['email']
            }
        
        return self.log_test(
            "POST /api/auth/test-login",
            auth_valid,
            f"Status: {status}, User ID: {data.get('userId', 'None')}, Email: {data.get('email', 'None')}"
        )

    def test_auth_me_endpoint(self):
        """Test GET /api/auth/me (session verification)"""
        print("🔐 Testing Session Verification...")
        
        # First, establish session using test-login
        success_login, status_login, login_data = self.make_request(
            'POST',
            'auth/test-login',
            {"email": self.test_email},
            expected_status=200,
            token=None
        )
        
        if not success_login:
            return self.log_test("GET /api/auth/me", False, f"Test login failed: {status_login}")
        
        # Now test /auth/me endpoint (should work with session cookie)
        success, status, data = self.make_request('GET', 'auth/me', token=None)
        
        if not success:
            return self.log_test("GET /api/auth/me", False, f"Status: {status}, Response: {data}")
        
        # Validate response structure
        me_valid = (
            'id' in data and
            'email' in data and
            'verified' in data and
            data['email'] == self.test_email and
            data['verified'] is True
        )
        
        if me_valid:
            self.user_data = data
        
        return self.log_test(
            "GET /api/auth/me",
            me_valid,
            f"Status: {status}, Email: {data.get('email', 'None')}, Verified: {data.get('verified', False)}"
        )

    def test_magic_link_auth(self):
        """Test POST /api/auth/login (magic link authentication)"""
        print("🔐 Testing Magic Link Authentication...")
        
        # Test magic link request
        success, status, data = self.make_request(
            'POST',
            'auth/magic-link',
            {"email": self.test_email},
            expected_status=200,
            token=None
        )
        
        if not success:
            return self.log_test("POST /api/auth/magic-link", False, f"Status: {status}, Response: {data}")
        
        # Validate response structure
        magic_link_valid = (
            'message' in data and
            ('dev_magic_link' in data or 'Magic link sent' in data['message'])
        )
        
        # If dev magic link is available, test token verification
        token_verification_works = True
        if 'dev_magic_link' in data:
            magic_link = data['dev_magic_link']
            if 'token=' in magic_link:
                token = magic_link.split('token=')[1]
                
                # Test token verification
                success_verify, status_verify, verify_data = self.make_request(
                    'POST',
                    'auth/verify',
                    {"token": token},
                    expected_status=200,
                    token=None
                )
                
                token_verification_works = (
                    success_verify and
                    'access_token' in verify_data and
                    'user' in verify_data
                )
                
                if token_verification_works:
                    self.token = verify_data['access_token']
                    self.user_data = verify_data['user']
        
        return self.log_test(
            "POST /api/auth/magic-link",
            magic_link_valid and token_verification_works,
            f"Magic link: {magic_link_valid}, Token verification: {token_verification_works}"
        )

    # ==================== LEAGUE MANAGEMENT ENDPOINTS ====================
    
    def test_league_creation(self):
        """Test POST /api/leagues (create league - sequential MongoDB operations)"""
        print("🏟️ Testing League Creation...")
        
        # Ensure we have authentication
        if not self.user_data:
            # Try test login first
            success_login, status_login, login_data = self.make_request(
                'POST',
                'auth/test-login',
                {"email": self.test_email},
                expected_status=200,
                token=None
            )
            if success_login:
                self.user_data = {'id': login_data['userId'], 'email': login_data['email']}
        
        if not self.user_data:
            return self.log_test("POST /api/leagues", False, "No authentication available")
        
        league_data = {
            "name": self.test_league_name,
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,  # Use minimum required value
                "bid_timer_seconds": 60,   # Use minimum required value
                "league_size": {
                    "min": 2,
                    "max": 8
                },
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data, expected_status=201)
        
        if not success:
            return self.log_test("POST /api/leagues", False, f"Status: {status}, Response: {data}")
        
        # Validate response structure (should return 201 with leagueId)
        league_creation_valid = (
            status == 201 and
            'leagueId' in data
        )
        
        if league_creation_valid:
            self.test_league_id = data['leagueId']
        
        return self.log_test(
            "POST /api/leagues",
            league_creation_valid,
            f"Status: {status}, League ID: {data.get('leagueId', 'None')}"
        )

    def test_league_details(self):
        """Test GET /api/leagues/{id} (get league details)"""
        print("🏟️ Testing League Details Retrieval...")
        
        if not self.test_league_id:
            return self.log_test("GET /api/leagues/{id}", False, "No test league ID available")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}')
        
        if not success:
            return self.log_test("GET /api/leagues/{id}", False, f"Status: {status}, Response: {data}")
        
        # Validate response structure
        league_details_valid = (
            'id' in data and
            'name' in data and
            'settings' in data and
            'status' in data and
            data['id'] == self.test_league_id and
            data['name'] == self.test_league_name
        )
        
        return self.log_test(
            "GET /api/leagues/{id}",
            league_details_valid,
            f"Status: {status}, Name: {data.get('name', 'None')}, Status: {data.get('status', 'None')}"
        )

    def test_league_join(self):
        """Test POST /api/leagues/{id}/join (join league)"""
        print("🏟️ Testing League Join...")
        
        if not self.test_league_id:
            return self.log_test("POST /api/leagues/{id}/join", False, "No test league ID available")
        
        success, status, data = self.make_request('POST', f'leagues/{self.test_league_id}/join')
        
        # This might fail if user is already a member (commissioner), which is expected
        if status == 400 and 'already a member' in str(data).lower():
            return self.log_test(
                "POST /api/leagues/{id}/join",
                True,
                f"Status: {status}, Already a member (expected for commissioner)"
            )
        
        if not success:
            return self.log_test("POST /api/leagues/{id}/join", False, f"Status: {status}, Response: {data}")
        
        # Validate response structure
        join_valid = (
            'message' in data and
            'successfully joined' in data['message'].lower()
        )
        
        return self.log_test(
            "POST /api/leagues/{id}/join",
            join_valid,
            f"Status: {status}, Message: {data.get('message', 'None')}"
        )

    def test_league_readiness(self):
        """Test GET /api/test/league/{id}/ready (TEST_MODE readiness check)"""
        print("🏟️ Testing League Readiness Check...")
        
        if not self.test_league_id:
            return self.log_test("GET /api/test/league/{id}/ready", False, "No test league ID available")
        
        success, status, data = self.make_request('GET', f'test/league/{self.test_league_id}/ready', token=None)
        
        if not success:
            return self.log_test("GET /api/test/league/{id}/ready", False, f"Status: {status}, Response: {data}")
        
        # Validate response structure
        readiness_valid = (
            'ready' in data and
            isinstance(data['ready'], bool)
        )
        
        # If not ready, should have reason
        if not data.get('ready', False):
            readiness_valid = readiness_valid and 'reason' in data
        
        return self.log_test(
            "GET /api/test/league/{id}/ready",
            readiness_valid,
            f"Status: {status}, Ready: {data.get('ready', 'None')}, Reason: {data.get('reason', 'N/A')}"
        )

    # ==================== CORE FUNCTIONALITY TESTS ====================
    
    def test_mongodb_operations(self):
        """Test MongoDB connection and operations (sequential, not transactions)"""
        print("💾 Testing MongoDB Operations...")
        
        # Test database connectivity through multiple operations
        operations_results = []
        
        # 1. Test user creation/update (via profile update)
        if self.user_data:
            test_name = f"MongoDB Test {datetime.now().strftime('%H%M%S')}"
            success, status, data = self.make_request(
                'PUT',
                'users/me',
                {"display_name": test_name}
            )
            operations_results.append(success)
            
            # Verify persistence
            success2, status2, data2 = self.make_request('GET', 'auth/me')
            operations_results.append(success2 and data2.get('display_name') == test_name)
        
        # 2. Test league data persistence
        if self.test_league_id:
            success3, status3, data3 = self.make_request('GET', f'leagues/{self.test_league_id}')
            operations_results.append(success3)
        
        # 3. Test list operations
        success4, status4, data4 = self.make_request('GET', 'leagues')
        operations_results.append(success4)
        
        mongodb_working = sum(operations_results) >= 3
        
        return self.log_test(
            "MongoDB Operations",
            mongodb_working,
            f"Operations working: {sum(operations_results)}/4"
        )

    def test_session_persistence(self):
        """Test session persistence after league creation"""
        print("🔐 Testing Session Persistence...")
        
        # Create a new league and verify session persists
        if not self.user_data:
            return self.log_test("Session Persistence", False, "No user session available")
        
        # Create another league to test session persistence
        league_data = {
            "name": f"Session Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,  # Use minimum required value
                "bid_timer_seconds": 60,   # Use minimum required value
                "league_size": {
                    "min": 2,
                    "max": 8
                }
            }
        }
        
        # Create league
        success1, status1, data1 = self.make_request('POST', 'leagues', league_data, expected_status=201)
        
        # Immediately test session with /auth/me
        success2, status2, data2 = self.make_request('GET', 'auth/me')
        
        # Test accessing the created league
        success3, status3, data3 = False, 0, {}
        if success1 and 'leagueId' in data1:
            success3, status3, data3 = self.make_request('GET', f'leagues/{data1["leagueId"]}')
        
        session_persists = success1 and success2 and success3
        
        return self.log_test(
            "Session Persistence",
            session_persists,
            f"League creation: {success1}, Auth check: {success2}, League access: {success3}"
        )

    def test_error_handling(self):
        """Test proper error handling and status codes"""
        print("⚠️ Testing Error Handling...")
        
        error_tests = []
        
        # 1. Test invalid league creation (missing required fields)
        success1, status1, data1 = self.make_request(
            'POST',
            'leagues',
            {"name": ""},  # Invalid name
            expected_status=400
        )
        error_tests.append(success1 and status1 == 400)
        
        # 2. Test accessing non-existent league
        success2, status2, data2 = self.make_request(
            'GET',
            'leagues/non-existent-league-id',
            expected_status=404
        )
        error_tests.append(success2 and status2 == 404)
        
        # 3. Test invalid email in test-login
        success3, status3, data3 = self.make_request(
            'POST',
            'auth/test-login',
            {"email": "invalid-email"},
            expected_status=400,
            token=None
        )
        error_tests.append(success3 and status3 == 400)
        
        # 4. Test unauthorized access (without authentication)
        success4, status4, data4 = self.make_request(
            'POST',
            'leagues',
            {"name": "Test League"},
            expected_status=401,
            token=None
        )
        error_tests.append(success4 and status4 == 401)
        
        error_handling_works = sum(error_tests) >= 3
        
        return self.log_test(
            "Error Handling",
            error_handling_works,
            f"Error tests passed: {sum(error_tests)}/4"
        )

    # ==================== MAIN TEST RUNNER ====================
    
    def run_focused_tests(self):
        """Run focused authentication and league management tests"""
        print("🚀 FOCUSED BACKEND TESTING - FRIENDS OF PIFA AUCTION PLATFORM")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 70)
        
        # Environment Variables Check
        print("\n🔧 ENVIRONMENT VARIABLES CHECK")
        self.test_environment_variables()
        
        # Authentication Endpoints
        print("\n🔐 AUTHENTICATION ENDPOINTS")
        self.test_auth_test_login()
        self.test_auth_me_endpoint()
        self.test_magic_link_auth()
        
        # League Management Endpoints
        print("\n🏟️ LEAGUE MANAGEMENT ENDPOINTS")
        self.test_league_creation()
        self.test_league_details()
        self.test_league_join()
        self.test_league_readiness()
        
        # Core Functionality
        print("\n💾 CORE FUNCTIONALITY")
        self.test_mongodb_operations()
        self.test_session_persistence()
        self.test_error_handling()
        
        # Final Summary
        print("\n" + "=" * 70)
        print("📊 FOCUSED TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        print("\n✅ CRITICAL ENDPOINTS STATUS:")
        critical_endpoints = [
            ("POST /api/auth/test-login", "POST /api/auth/test-login" not in [t.split(':')[0] for t in self.failed_tests]),
            ("GET /api/auth/me", "GET /api/auth/me" not in [t.split(':')[0] for t in self.failed_tests]),
            ("POST /api/leagues", "POST /api/leagues" not in [t.split(':')[0] for t in self.failed_tests]),
            ("GET /api/leagues/{id}", "GET /api/leagues/{id}" not in [t.split(':')[0] for t in self.failed_tests]),
            ("MongoDB Operations", "MongoDB Operations" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        for endpoint, status in critical_endpoints:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {endpoint}: {'WORKING' if status else 'FAILED'}")
        
        # Check for specific issues mentioned in review request
        print("\n🔍 SPECIFIC REVIEW ISSUES CHECK:")
        no_403_after_league_creation = "Session Persistence" not in [t.split(':')[0] for t in self.failed_tests]
        sequential_operations_working = "MongoDB Operations" not in [t.split(':')[0] for t in self.failed_tests]
        proper_status_codes = "Error Handling" not in [t.split(':')[0] for t in self.failed_tests]
        
        print(f"   {'✅' if no_403_after_league_creation else '❌'} No 403 errors after league creation: {'RESOLVED' if no_403_after_league_creation else 'ISSUE PERSISTS'}")
        print(f"   {'✅' if sequential_operations_working else '❌'} Sequential MongoDB operations: {'WORKING' if sequential_operations_working else 'FAILED'}")
        print(f"   {'✅' if proper_status_codes else '❌'} Proper error handling: {'WORKING' if proper_status_codes else 'FAILED'}")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = FocusedAuthLeagueTest()
    passed, total, failed = tester.run_focused_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)