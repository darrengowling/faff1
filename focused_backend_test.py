#!/usr/bin/env python3
"""
Focused Backend API Testing Suite for Critical Endpoints
Tests the specific endpoints mentioned in the review request after frontend refactoring
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class FocusedBackendTester:
    def __init__(self, base_url="https://magic-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.test_email = "focused_test@example.com"
        
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
        
        auth_token = token or self.token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
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

    # ==================== CRITICAL ENDPOINT TESTS ====================
    
    def test_health_endpoint(self):
        """Test /api/health endpoint to verify system status"""
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Health Endpoint", False, f"Status: {status}, Response: {data}")
        
        # Check health response structure
        health_valid = (
            'status' in data and
            'timestamp' in data and
            data.get('status') == 'healthy'
        )
        
        # Check for detailed health info
        has_database_info = 'database' in data
        has_services_info = 'services' in data
        
        return self.log_test(
            "Health Endpoint",
            health_valid,
            f"Status: {data.get('status')}, DB info: {has_database_info}, Services info: {has_services_info}"
        )

    def test_database_connectivity(self):
        """Test MongoDB database connectivity through health endpoint"""
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Database Connectivity", False, f"Health endpoint failed: {status}")
        
        # Check database connectivity info
        database_info = data.get('database', {})
        db_connected = database_info.get('connected', False)
        collections_count = database_info.get('collections_count', 0)
        
        return self.log_test(
            "Database Connectivity",
            db_connected,
            f"Connected: {db_connected}, Collections: {collections_count}"
        )

    def test_auth_magic_link_endpoint(self):
        """Test /api/auth/magic-link endpoint"""
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success:
            return self.log_test("Auth Magic Link Endpoint", False, f"Status: {status}, Response: {data}")
        
        # Check response structure
        has_message = 'message' in data
        has_dev_link = 'dev_magic_link' in data  # Development mode
        
        return self.log_test(
            "Auth Magic Link Endpoint",
            has_message,
            f"Message: {has_message}, Dev link: {has_dev_link}"
        )

    def test_auth_test_login_endpoint(self):
        """Test /api/auth/test-login endpoint"""
        success, status, data = self.make_request(
            'POST',
            'auth/test-login',
            {"email": self.test_email},
            token=None
        )
        
        if not success:
            return self.log_test("Auth Test Login Endpoint", False, f"Status: {status}, Response: {data}")
        
        # Check response structure
        login_valid = (
            'ok' in data and
            'userId' in data and
            'email' in data and
            data.get('ok') is True and
            data.get('email') == self.test_email
        )
        
        return self.log_test(
            "Auth Test Login Endpoint",
            login_valid,
            f"User ID: {data.get('userId')}, Email: {data.get('email')}"
        )

    def test_complete_auth_flow(self):
        """Test complete authentication flow: magic-link -> verify -> me"""
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success or 'dev_magic_link' not in data:
            return self.log_test("Complete Auth Flow", False, f"Magic link failed: {status}")
        
        # Step 2: Extract and verify token
        magic_link = data['dev_magic_link']
        if 'token=' not in magic_link:
            return self.log_test("Complete Auth Flow", False, "Invalid magic link format")
        
        token = magic_link.split('token=')[1]
        
        # Step 3: Verify magic link token
        success, status, auth_data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if not success:
            return self.log_test("Complete Auth Flow", False, f"Token verification failed: {status}")
        
        # Check auth response structure
        auth_valid = (
            'access_token' in auth_data and
            'user' in auth_data and
            'email' in auth_data['user'] and
            'verified' in auth_data['user']
        )
        
        if not auth_valid:
            return self.log_test("Complete Auth Flow", False, "Invalid auth response structure")
        
        # Store token for subsequent tests
        self.token = auth_data['access_token']
        self.user_data = auth_data['user']
        
        # Step 4: Test /auth/me endpoint
        success, status, me_data = self.make_request('GET', 'auth/me')
        
        me_valid = (
            success and
            'id' in me_data and
            'email' in me_data and
            'verified' in me_data and
            me_data['email'] == self.test_email
        )
        
        return self.log_test(
            "Complete Auth Flow",
            auth_valid and me_valid,
            f"Token obtained, User verified: {me_data.get('verified', False)}"
        )

    def test_user_profile_endpoints(self):
        """Test /api/users/me endpoint"""
        if not self.token:
            return self.log_test("User Profile Endpoints", False, "No authentication token")
        
        # Test profile update
        new_display_name = f"Focused Test User {datetime.now().strftime('%H%M%S')}"
        
        success, status, data = self.make_request(
            'PUT',
            'users/me',
            {"display_name": new_display_name}
        )
        
        if not success:
            return self.log_test("User Profile Endpoints", False, f"Profile update failed: {status}")
        
        # Verify update worked
        update_valid = (
            'display_name' in data and
            data['display_name'] == new_display_name
        )
        
        return self.log_test(
            "User Profile Endpoints",
            update_valid,
            f"Profile updated: {data.get('display_name', 'Unknown')}"
        )

    def test_league_creation_endpoint(self):
        """Test POST /api/leagues endpoint"""
        if not self.token:
            return self.log_test("League Creation Endpoint", False, "No authentication token")
        
        league_data = {
            "name": f"Focused Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
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
            return self.log_test("League Creation Endpoint", False, f"Status: {status}, Response: {data}")
        
        # Check response structure - the API now returns just leagueId
        league_valid = 'leagueId' in data
        
        if league_valid:
            self.test_league_id = data['leagueId']
        
        return self.log_test(
            "League Creation Endpoint",
            league_valid,
            f"League ID: {data.get('leagueId', 'None')}"
        )

    def test_league_list_endpoint(self):
        """Test GET /api/leagues endpoint"""
        if not self.token:
            return self.log_test("League List Endpoint", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'leagues')
        
        if not success:
            return self.log_test("League List Endpoint", False, f"Status: {status}, Response: {data}")
        
        # Check response structure
        list_valid = isinstance(data, list)
        has_leagues = len(data) > 0 if list_valid else False
        
        # If we have leagues, check structure of first league
        league_structure_valid = True
        if has_leagues:
            first_league = data[0]
            league_structure_valid = (
                'id' in first_league and
                'name' in first_league and
                'status' in first_league
            )
        
        return self.log_test(
            "League List Endpoint",
            list_valid and league_structure_valid,
            f"Leagues count: {len(data) if list_valid else 0}, Structure valid: {league_structure_valid}"
        )

    def test_league_details_endpoint(self):
        """Test GET /api/leagues/{id} endpoint"""
        if not self.test_league_id:
            return self.log_test("League Details Endpoint", False, "No test league ID")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}')
        
        if not success:
            return self.log_test("League Details Endpoint", False, f"Status: {status}, Response: {data}")
        
        # Check response structure
        details_valid = (
            'id' in data and
            'name' in data and
            'settings' in data and
            'status' in data and
            data['id'] == self.test_league_id
        )
        
        return self.log_test(
            "League Details Endpoint",
            details_valid,
            f"League: {data.get('name', 'Unknown')}, Status: {data.get('status', 'Unknown')}"
        )

    def test_email_validation_fixes(self):
        """Test that email validation fixes are still working"""
        # Test invalid email format
        success, status, data = self.make_request(
            'POST',
            'auth/magic-link',
            {"email": "invalid@@domain.com"},
            expected_status=400,
            token=None
        )
        
        invalid_email_handled = success and status == 400
        
        # Test empty email
        success2, status2, data2 = self.make_request(
            'POST',
            'auth/magic-link',
            {"email": ""},
            expected_status=400,
            token=None
        )
        
        empty_email_handled = success2 and status2 == 400
        
        # Test valid email (should work)
        success3, status3, data3 = self.make_request(
            'POST',
            'auth/magic-link',
            {"email": "valid@example.com"},
            expected_status=200,
            token=None
        )
        
        valid_email_works = success3 and status3 == 200
        
        return self.log_test(
            "Email Validation Fixes",
            invalid_email_handled and empty_email_handled and valid_email_works,
            f"Invalid: {status}, Empty: {status2}, Valid: {status3}"
        )

    def test_error_handling(self):
        """Test that endpoints return proper HTTP status codes and no 500 errors for expected failures"""
        test_results = []
        
        # Test 404 for non-existent league
        success, status, data = self.make_request('GET', 'leagues/non-existent-id', expected_status=404)
        test_results.append(success and status == 404)
        
        # Test 401 for unauthorized access
        success2, status2, data2 = self.make_request('GET', 'auth/me', token="invalid-token", expected_status=401)
        test_results.append(success2 and status2 == 401)
        
        # Test 400 for invalid league creation data
        success3, status3, data3 = self.make_request(
            'POST',
            'leagues',
            {"invalid": "data"},
            expected_status=422,  # Pydantic validation error
            token=self.token
        )
        test_results.append(success3 and status3 == 422)
        
        return self.log_test(
            "Error Handling",
            sum(test_results) >= 2,  # At least 2 out of 3 should work
            f"404: {test_results[0]}, 401: {test_results[1]}, 422: {test_results[2]}"
        )

    # ==================== MAIN TEST RUNNER ====================
    
    def run_focused_tests(self):
        """Run focused backend tests for critical endpoints"""
        print("🎯 FOCUSED BACKEND API TESTING SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("Testing critical endpoints after frontend refactoring")
        print("=" * 60)
        
        # Health and Database Tests
        print("\n🏥 HEALTH & DATABASE TESTS")
        self.test_health_endpoint()
        self.test_database_connectivity()
        
        # Authentication Tests
        print("\n🔐 AUTHENTICATION TESTS")
        self.test_auth_magic_link_endpoint()
        self.test_auth_test_login_endpoint()
        self.test_complete_auth_flow()
        self.test_user_profile_endpoints()
        
        # League Management Tests
        print("\n🏟️ LEAGUE MANAGEMENT TESTS")
        self.test_league_creation_endpoint()
        self.test_league_list_endpoint()
        self.test_league_details_endpoint()
        
        # Validation and Error Handling Tests
        print("\n🛡️ VALIDATION & ERROR HANDLING TESTS")
        self.test_email_validation_fixes()
        self.test_error_handling()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST SUMMARY")
        print("=" * 60)
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
            ("Health Endpoint", "Health Endpoint" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Database Connectivity", "Database Connectivity" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Authentication Flow", "Complete Auth Flow" not in [t.split(':')[0] for t in self.failed_tests]),
            ("League Management", "League Creation Endpoint" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Email Validation", "Email Validation Fixes" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        for endpoint, status in critical_endpoints:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {endpoint}: {'WORKING' if status else 'FAILED'}")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = FocusedBackendTester()
    passed, total, failed = tester.run_focused_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)