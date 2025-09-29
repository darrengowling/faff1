#!/usr/bin/env python3
"""
Authentication Backend API Testing Suite
Tests specific authentication endpoints as requested in review:
1. POST /api/auth/test-login - Test login functionality with TEST_MODE enabled
2. GET /api/auth/me - Session verification after login  
3. POST /api/leagues - League creation with authentication
4. GET /api/leagues/{id} - League retrieval
5. GET /api/test/league/{id}/ready - Test mode readiness endpoint
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class AuthBackendTester:
    def __init__(self, base_url="https://e2e-stability.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()  # Use session for cookie persistence
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data with realistic values
        self.test_email = "league_creator@example.com"
        
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
        """Make HTTP request with session for cookie persistence"""
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

    def test_test_login_endpoint(self):
        """Test POST /api/auth/test-login endpoint with TEST_MODE enabled"""
        print(f"\n🧪 Testing POST /api/auth/test-login with email: {self.test_email}")
        
        success, status, data = self.make_request(
            'POST', 
            'auth/test-login', 
            {"email": self.test_email}
        )
        
        if not success:
            return self.log_test(
                "POST /api/auth/test-login", 
                False, 
                f"Status: {status}, Response: {data}"
            )
        
        # Validate response structure
        response_valid = (
            'ok' in data and
            data['ok'] is True and
            'userId' in data and
            'email' in data and
            'message' in data and
            data['email'] == self.test_email
        )
        
        if response_valid:
            self.user_data = {
                'id': data['userId'],
                'email': data['email']
            }
        
        return self.log_test(
            "POST /api/auth/test-login",
            response_valid,
            f"Status: {status}, User ID: {data.get('userId', 'None')}, Email: {data.get('email', 'None')}"
        )

    def test_auth_me_endpoint(self):
        """Test GET /api/auth/me endpoint for session verification"""
        print(f"\n🔐 Testing GET /api/auth/me for session verification")
        
        success, status, data = self.make_request('GET', 'auth/me')
        
        if not success:
            return self.log_test(
                "GET /api/auth/me", 
                False, 
                f"Status: {status}, Response: {data}"
            )
        
        # Validate response structure and data consistency
        me_valid = (
            'id' in data and
            'email' in data and
            'verified' in data and
            data['email'] == self.test_email and
            data['verified'] is True
        )
        
        return self.log_test(
            "GET /api/auth/me",
            me_valid,
            f"Status: {status}, Email: {data.get('email', 'None')}, Verified: {data.get('verified', 'None')}"
        )

    def test_league_creation_with_auth(self):
        """Test POST /api/leagues endpoint with authentication"""
        print(f"\n🏟️ Testing POST /api/leagues with authentication")
        
        # Create realistic league data
        league_data = {
            "name": f"Auth Test League {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 8,
                "bid_timer_seconds": 60,
                "anti_snipe_seconds": 30,
                "league_size": {
                    "min": 2,
                    "max": 8
                }
            }
        }
        
        success, status, data = self.make_request(
            'POST', 
            'leagues', 
            league_data,
            expected_status=201  # Expecting 201 Created
        )
        
        if not success:
            return self.log_test(
                "POST /api/leagues", 
                False, 
                f"Status: {status}, Response: {data}"
            )
        
        # Validate league creation response
        league_valid = (
            'leagueId' in data and
            data['leagueId'] is not None
        )
        
        if league_valid:
            self.test_league_id = data['leagueId']
        
        return self.log_test(
            "POST /api/leagues",
            league_valid,
            f"Status: {status}, League ID: {data.get('leagueId', 'None')}"
        )

    def test_league_retrieval(self):
        """Test GET /api/leagues/{id} endpoint"""
        if not self.test_league_id:
            return self.log_test(
                "GET /api/leagues/{id}", 
                False, 
                "No test league ID available"
            )
        
        print(f"\n📋 Testing GET /api/leagues/{self.test_league_id}")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}')
        
        if not success:
            return self.log_test(
                "GET /api/leagues/{id}", 
                False, 
                f"Status: {status}, Response: {data}"
            )
        
        # Validate league retrieval response
        league_data_valid = (
            'id' in data and
            'name' in data and
            'settings' in data and
            'status' in data and
            data['id'] == self.test_league_id
        )
        
        return self.log_test(
            "GET /api/leagues/{id}",
            league_data_valid,
            f"Status: {status}, Name: {data.get('name', 'None')}, Status: {data.get('status', 'None')}"
        )

    def test_league_ready_endpoint(self):
        """Test GET /api/test/league/{id}/ready endpoint"""
        if not self.test_league_id:
            return self.log_test(
                "GET /api/test/league/{id}/ready", 
                False, 
                "No test league ID available"
            )
        
        print(f"\n🎯 Testing GET /api/test/league/{self.test_league_id}/ready")
        
        success, status, data = self.make_request('GET', f'test/league/{self.test_league_id}/ready')
        
        if not success:
            return self.log_test(
                "GET /api/test/league/{id}/ready", 
                False, 
                f"Status: {status}, Response: {data}"
            )
        
        # Validate readiness response
        ready_valid = (
            'ready' in data and
            isinstance(data['ready'], bool)
        )
        
        return self.log_test(
            "GET /api/test/league/{id}/ready",
            ready_valid,
            f"Status: {status}, Ready: {data.get('ready', 'None')}, Reason: {data.get('reason', 'N/A')}"
        )

    def test_authentication_flow_complete(self):
        """Test complete authentication flow end-to-end"""
        print(f"\n🔄 Testing complete authentication flow")
        
        # Test session persistence by making multiple authenticated requests
        endpoints_to_test = [
            ('GET', 'auth/me'),
            ('GET', 'leagues'),
        ]
        
        all_success = True
        results = []
        
        for method, endpoint in endpoints_to_test:
            success, status, data = self.make_request(method, endpoint)
            results.append(f"{method} {endpoint}: {status}")
            if not success:
                all_success = False
        
        return self.log_test(
            "Authentication Flow Complete",
            all_success,
            f"Results: {', '.join(results)}"
        )

    def run_auth_tests(self):
        """Run all authentication-focused backend tests"""
        print("🚀 AUTHENTICATION BACKEND API TESTING SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print(f"Test Email: {self.test_email}")
        print("=" * 60)
        
        # Test the specific endpoints requested in review
        print("\n🔐 AUTHENTICATION ENDPOINTS TESTING")
        
        # 1. Test login functionality
        if not self.test_test_login_endpoint():
            print("❌ Authentication failed - skipping dependent tests")
            return self.tests_passed, self.tests_run, self.failed_tests
        
        # 2. Test session verification
        self.test_auth_me_endpoint()
        
        # 3. Test league creation with authentication
        self.test_league_creation_with_auth()
        
        # 4. Test league retrieval
        self.test_league_retrieval()
        
        # 5. Test readiness endpoint
        self.test_league_ready_endpoint()
        
        # 6. Test complete authentication flow
        self.test_authentication_flow_complete()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 AUTHENTICATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        else:
            print(f"\n✅ ALL AUTHENTICATION TESTS PASSED!")
        
        print("\n✅ CRITICAL AUTHENTICATION STATUS:")
        critical_tests = [
            ("Test Login Endpoint", "POST /api/auth/test-login" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Session Verification", "GET /api/auth/me" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Authenticated League Creation", "POST /api/leagues" not in [t.split(':')[0] for t in self.failed_tests]),
            ("League Retrieval", "GET /api/leagues/{id}" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Readiness Endpoint", "GET /api/test/league/{id}/ready" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        for test_name, status in critical_tests:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {test_name}: {'WORKING' if status else 'FAILED'}")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = AuthBackendTester()
    passed, total, failed = tester.run_auth_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)