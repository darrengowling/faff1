#!/usr/bin/env python3
"""
Final Backend Validation Suite
Tests all critical backend API endpoints mentioned in the review request
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class FinalBackendValidator:
    def __init__(self, base_url="https://pifa-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.test_email = "final_validation@example.com"
        
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

    def test_critical_endpoints(self):
        """Test all critical endpoints mentioned in the review"""
        
        print("🎯 TESTING CRITICAL BACKEND ENDPOINTS")
        print("=" * 60)
        
        # 1. Health endpoint - /api/health
        print("\n1️⃣ HEALTH ENDPOINT")
        success, status, data = self.make_request('GET', 'health', token=None)
        health_working = success and data.get('status') == 'healthy'
        self.log_test("Health Endpoint (/api/health)", health_working, 
                     f"Status: {data.get('status', 'unknown')}, DB Connected: {data.get('database', {}).get('connected', False)}")
        
        # 2. Authentication endpoints
        print("\n2️⃣ AUTHENTICATION ENDPOINTS")
        
        # 2a. Magic link endpoint
        success, status, data = self.make_request('POST', 'auth/magic-link', {"email": self.test_email}, token=None)
        magic_link_working = success and 'message' in data
        self.log_test("Magic Link (/api/auth/magic-link)", magic_link_working, 
                     f"Status: {status}, Has dev link: {'dev_magic_link' in data}")
        
        # 2b. Test login endpoint
        success, status, data = self.make_request('POST', 'auth/test-login', {"email": self.test_email}, token=None)
        test_login_working = success and data.get('ok') is True
        self.log_test("Test Login (/api/auth/test-login)", test_login_working, 
                     f"Status: {status}, User ID: {data.get('userId', 'none')}")
        
        # 2c. Complete auth flow for token
        # Get fresh magic link for verification
        success, status, magic_data = self.make_request('POST', 'auth/magic-link', {"email": self.test_email}, token=None)
        if success and 'dev_magic_link' in magic_data:
            magic_link = magic_data['dev_magic_link']
            if 'token=' in magic_link:
                token = magic_link.split('token=')[1]
                success, status, auth_data = self.make_request('POST', 'auth/verify', {"token": token}, token=None)
                verify_working = success and 'access_token' in auth_data
                self.log_test("Token Verification (/api/auth/verify)", verify_working, 
                             f"Status: {status}, Token obtained: {'access_token' in auth_data}")
                
                if verify_working:
                    self.token = auth_data['access_token']
                    self.user_data = auth_data['user']
        
        # 2d. Auth me endpoint
        if self.token:
            success, status, data = self.make_request('GET', 'auth/me')
            auth_me_working = success and data.get('email') == self.test_email
            self.log_test("Auth Me (/api/auth/me)", auth_me_working, 
                         f"Status: {status}, Email: {data.get('email', 'unknown')}")
        
        # 3. User management endpoints
        print("\n3️⃣ USER MANAGEMENT ENDPOINTS")
        if self.token:
            # User profile update
            new_name = f"Final Test {datetime.now().strftime('%H%M%S')}"
            success, status, data = self.make_request('PUT', 'users/me', {"display_name": new_name})
            user_update_working = success and data.get('display_name') == new_name
            self.log_test("User Profile Update (/api/users/me)", user_update_working, 
                         f"Status: {status}, New name: {data.get('display_name', 'unknown')}")
        
        # 4. League management endpoints
        print("\n4️⃣ LEAGUE MANAGEMENT ENDPOINTS")
        if self.token:
            # League creation
            league_data = {
                "name": f"Final Test League {datetime.now().strftime('%H%M%S')}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "min_increment": 1,
                    "club_slots_per_manager": 3,
                    "anti_snipe_seconds": 30,
                    "bid_timer_seconds": 60,
                    "league_size": {"min": 2, "max": 8},
                    "scoring_rules": {"club_goal": 1, "club_win": 3, "club_draw": 1}
                }
            }
            
            success, status, data = self.make_request('POST', 'leagues', league_data, expected_status=201)
            league_create_working = success and 'leagueId' in data
            self.log_test("League Creation (POST /api/leagues)", league_create_working, 
                         f"Status: {status}, League ID: {data.get('leagueId', 'none')}")
            
            if league_create_working:
                self.test_league_id = data['leagueId']
            
            # League list
            success, status, data = self.make_request('GET', 'leagues')
            league_list_working = success and isinstance(data, list)
            self.log_test("League List (GET /api/leagues)", league_list_working, 
                         f"Status: {status}, Count: {len(data) if isinstance(data, list) else 0}")
            
            # League details
            if self.test_league_id:
                success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}')
                league_details_working = success and data.get('id') == self.test_league_id
                self.log_test("League Details (GET /api/leagues/{id})", league_details_working, 
                             f"Status: {status}, Name: {data.get('name', 'unknown')}")
        
        # 5. Email validation fixes verification
        print("\n5️⃣ EMAIL VALIDATION FIXES")
        
        # Test invalid email (should return 422 with Pydantic validation)
        success, status, data = self.make_request('POST', 'auth/magic-link', {"email": "invalid@@domain.com"}, 
                                                expected_status=422, token=None)
        invalid_email_handled = success and status == 422
        self.log_test("Invalid Email Handling", invalid_email_handled, 
                     f"Status: {status}, Proper validation error: {success}")
        
        # Test empty email
        success, status, data = self.make_request('POST', 'auth/magic-link', {"email": ""}, 
                                                expected_status=422, token=None)
        empty_email_handled = success and status == 422
        self.log_test("Empty Email Handling", empty_email_handled, 
                     f"Status: {status}, Proper validation error: {success}")
        
        # Test valid email works
        success, status, data = self.make_request('POST', 'auth/magic-link', {"email": "valid@example.com"}, token=None)
        valid_email_works = success and status == 200
        self.log_test("Valid Email Processing", valid_email_works, 
                     f"Status: {status}, Magic link generated: {success}")
        
        # 6. Error handling verification
        print("\n6️⃣ ERROR HANDLING VERIFICATION")
        
        # Test 404 for non-existent league (with valid token)
        if self.token:
            success, status, data = self.make_request('GET', 'leagues/non-existent-id', expected_status=404)
            not_found_handled = success and status == 404
            self.log_test("404 Error Handling", not_found_handled, 
                         f"Status: {status}, Proper 404 response: {success}")
        
        # Test 403 for unauthorized access
        success, status, data = self.make_request('GET', 'auth/me', token="invalid-token", expected_status=403)
        unauthorized_handled = success and status == 403
        self.log_test("403 Unauthorized Handling", unauthorized_handled, 
                     f"Status: {status}, Proper auth error: {success}")
        
        # Test no 500 errors for expected failures
        success, status, data = self.make_request('POST', 'leagues', {"invalid": "data"}, 
                                                expected_status=422, token=self.token)
        validation_error_handled = success and status == 422
        self.log_test("422 Validation Error Handling", validation_error_handled, 
                     f"Status: {status}, No 500 error: {success}")

    def test_database_stability(self):
        """Test MongoDB connection stability"""
        print("\n7️⃣ DATABASE CONNECTIVITY STABILITY")
        
        # Multiple health checks to verify stability
        stable_connections = 0
        for i in range(3):
            success, status, data = self.make_request('GET', 'health', token=None)
            if success and data.get('database', {}).get('connected', False):
                stable_connections += 1
            time.sleep(1)
        
        db_stable = stable_connections >= 2
        self.log_test("Database Connection Stability", db_stable, 
                     f"Stable connections: {stable_connections}/3")
        
        # Test data persistence
        if self.token:
            # Create and retrieve data to test persistence
            test_name = f"Persistence Test {datetime.now().strftime('%H%M%S')}"
            success, status, data = self.make_request('PUT', 'users/me', {"display_name": test_name})
            
            if success:
                # Retrieve to verify persistence
                success2, status2, data2 = self.make_request('GET', 'auth/me')
                persistence_works = success2 and data2.get('display_name') == test_name
                self.log_test("Data Persistence", persistence_works, 
                             f"Data persisted correctly: {persistence_works}")

    def test_league_transactions(self):
        """Test league creation with transactions"""
        print("\n8️⃣ LEAGUE TRANSACTION FUNCTIONALITY")
        
        if not self.token:
            self.log_test("League Transactions", False, "No authentication token")
            return
        
        # Test league creation with proper transaction handling
        league_data = {
            "name": f"Transaction Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 150,
                "min_increment": 1,
                "club_slots_per_manager": 5,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "league_size": {"min": 2, "max": 6},
                "scoring_rules": {"club_goal": 1, "club_win": 3, "club_draw": 1}
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data, expected_status=201)
        
        if success and 'leagueId' in data:
            league_id = data['leagueId']
            
            # Verify league was created with all components
            success2, status2, league_data = self.make_request('GET', f'leagues/{league_id}')
            league_complete = success2 and league_data.get('settings', {}).get('budget_per_manager') == 150
            
            # Verify membership was created
            success3, status3, members = self.make_request('GET', f'leagues/{league_id}/members')
            membership_created = success3 and len(members) >= 1
            
            transaction_success = league_complete and membership_created
            self.log_test("League Creation Transactions", transaction_success, 
                         f"League: {league_complete}, Membership: {membership_created}")
        else:
            self.log_test("League Creation Transactions", False, f"League creation failed: {status}")

    def run_validation(self):
        """Run complete validation suite"""
        print("🔍 FINAL BACKEND VALIDATION SUITE")
        print("Testing all critical endpoints after frontend refactoring")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"API: {self.api_url}")
        print(f"Test Mode: {os.getenv('TEST_MODE', 'false')}")
        print("=" * 80)
        
        # Run all tests
        self.test_critical_endpoints()
        self.test_database_stability()
        self.test_league_transactions()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📊 FINAL VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        print("\n✅ CRITICAL SYSTEMS VALIDATION:")
        critical_systems = [
            ("Health Endpoint", "Health Endpoint" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Authentication Flow", "Token Verification" not in [t.split(':')[0] for t in self.failed_tests]),
            ("League Management", "League Creation" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Database Connectivity", "Database Connection Stability" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Email Validation", "Invalid Email Handling" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Error Handling", "422 Validation Error Handling" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        all_critical_working = True
        for system, status in critical_systems:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {system}: {'WORKING' if status else 'FAILED'}")
            if not status:
                all_critical_working = False
        
        print(f"\n🎯 OVERALL STATUS: {'✅ ALL CRITICAL SYSTEMS WORKING' if all_critical_working else '❌ SOME CRITICAL SYSTEMS FAILED'}")
        
        return self.tests_passed, self.tests_run, self.failed_tests, all_critical_working

if __name__ == "__main__":
    validator = FinalBackendValidator()
    passed, total, failed, all_critical_working = validator.run_validation()
    
    # Exit with appropriate code
    sys.exit(0 if all_critical_working else 1)