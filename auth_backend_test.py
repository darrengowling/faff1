#!/usr/bin/env python3
"""
Authentication Backend Testing Suite
Focused testing for authentication endpoints and backend routing issues
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class AuthBackendTester:
    def __init__(self, base_url="https://testid-enforcer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.test_email = "auth_test@example.com"
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

    def make_request(self, method, endpoint, data=None, expected_status=200, use_session=True):
        """Make HTTP request with proper headers and session handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if use_session:
                if method == 'GET':
                    response = self.session.get(url, headers=headers, timeout=15)
                elif method == 'POST':
                    response = self.session.post(url, json=data, headers=headers, timeout=15)
                elif method == 'PUT':
                    response = self.session.put(url, json=data, headers=headers, timeout=15)
                elif method == 'DELETE':
                    response = self.session.delete(url, headers=headers, timeout=15)
            else:
                if method == 'GET':
                    response = requests.get(url, headers=headers, timeout=15)
                elif method == 'POST':
                    response = requests.post(url, json=data, headers=headers, timeout=15)
                elif method == 'PUT':
                    response = requests.put(url, json=data, headers=headers, timeout=15)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data, response
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}, None

    def test_environment_variables(self):
        """Test that required environment variables are properly configured"""
        print("🔧 Testing Environment Variables Configuration...")
        
        # Test health endpoint to verify basic connectivity
        success, status, data, _ = self.make_request('GET', 'health', use_session=False)
        
        if not success:
            return self.log_test("Environment Variables", False, f"Health check failed: {status}")
        
        # Check if TEST_MODE and ALLOW_TEST_LOGIN are working by testing test-login endpoint availability
        success, status, data, _ = self.make_request('POST', 'auth/test-login', 
                                                   {"email": "test@example.com"}, 
                                                   expected_status=200, use_session=False)
        
        test_mode_enabled = success and status == 200
        
        return self.log_test(
            "Environment Variables", 
            test_mode_enabled,
            f"TEST_MODE and ALLOW_TEST_LOGIN configured: {test_mode_enabled}"
        )

    def test_auth_me_unauthenticated(self):
        """Test GET /api/auth/me endpoint without authentication"""
        print("🔐 Testing /api/auth/me endpoint (unauthenticated)...")
        
        # Clear any existing session
        self.session.cookies.clear()
        
        success, status, data, response = self.make_request('GET', 'auth/me', expected_status=401)
        
        # Should return 401 or 403 for unauthenticated requests
        auth_properly_protected = status in [401, 403]
        
        return self.log_test(
            "Auth Me Unauthenticated",
            auth_properly_protected,
            f"Status: {status}, Expected 401/403 for unauthenticated request"
        )

    def test_test_login_endpoint(self):
        """Test POST /api/auth/test-login endpoint"""
        print("🧪 Testing /api/auth/test-login endpoint...")
        
        # Clear any existing session
        self.session.cookies.clear()
        
        # Test with valid email
        success, status, data, response = self.make_request('POST', 'auth/test-login', 
                                                          {"email": self.test_email})
        
        if not success:
            return self.log_test("Test Login Endpoint", False, 
                               f"Test login failed: Status {status}, Response: {data}")
        
        # Check response structure
        test_login_valid = (
            'ok' in data and
            data['ok'] is True and
            'userId' in data and
            'email' in data and
            data['email'] == self.test_email
        )
        
        # Check if session cookie was set
        session_cookie_set = any('access_token' in cookie.name for cookie in self.session.cookies)
        
        return self.log_test(
            "Test Login Endpoint",
            test_login_valid and session_cookie_set,
            f"Login successful: {test_login_valid}, Session cookie set: {session_cookie_set}"
        )

    def test_auth_me_authenticated(self):
        """Test GET /api/auth/me endpoint after authentication"""
        print("🔐 Testing /api/auth/me endpoint (authenticated)...")
        
        # This test depends on test_test_login_endpoint being run first
        success, status, data, response = self.make_request('GET', 'auth/me')
        
        if not success:
            return self.log_test("Auth Me Authenticated", False, 
                               f"Auth me failed: Status {status}, Response: {data}")
        
        # Check response structure
        auth_me_valid = (
            'id' in data and
            'email' in data and
            'verified' in data and
            data['email'] == self.test_email and
            data['verified'] is True
        )
        
        return self.log_test(
            "Auth Me Authenticated",
            auth_me_valid,
            f"User data retrieved: {auth_me_valid}, Email: {data.get('email', 'Unknown')}"
        )

    def test_session_persistence(self):
        """Test that session persists across multiple requests"""
        print("🔄 Testing Session Persistence...")
        
        # Make multiple requests to auth/me to verify session persistence
        results = []
        for i in range(3):
            success, status, data, response = self.make_request('GET', 'auth/me')
            results.append(success and status == 200)
            time.sleep(0.5)  # Small delay between requests
        
        session_persistent = all(results)
        
        return self.log_test(
            "Session Persistence",
            session_persistent,
            f"Session maintained across {len(results)} requests: {session_persistent}"
        )

    def test_token_validation(self):
        """Test token validation and error handling"""
        print("🔍 Testing Token Validation...")
        
        # Test with invalid token by clearing session and making request
        temp_session = requests.Session()
        temp_session.cookies.set('access_token', 'invalid_token_12345')
        
        url = f"{self.api_url}/auth/me"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = temp_session.get(url, headers=headers, timeout=15)
            invalid_token_handled = response.status_code in [401, 403]
        except:
            invalid_token_handled = False
        
        return self.log_test(
            "Token Validation",
            invalid_token_handled,
            f"Invalid token properly rejected: {invalid_token_handled}"
        )

    def test_magic_link_flow(self):
        """Test magic link authentication flow"""
        print("✨ Testing Magic Link Flow...")
        
        # Clear session for fresh test
        self.session.cookies.clear()
        
        # Step 1: Request magic link
        success, status, data, response = self.make_request('POST', 'auth/magic-link', 
                                                          {"email": "magiclink_test@example.com"})
        
        if not success:
            return self.log_test("Magic Link Flow", False, 
                               f"Magic link request failed: Status {status}")
        
        # Check if dev magic link is provided
        has_dev_link = 'dev_magic_link' in data
        if not has_dev_link:
            return self.log_test("Magic Link Flow", False, "No dev magic link in response")
        
        # Extract token from magic link
        magic_link = data['dev_magic_link']
        if 'token=' not in magic_link:
            return self.log_test("Magic Link Flow", False, "Invalid magic link format")
        
        token = magic_link.split('token=')[1]
        
        # Step 2: Verify magic link token
        success, status, auth_data, response = self.make_request('POST', 'auth/verify', 
                                                               {"token": token})
        
        if not success:
            return self.log_test("Magic Link Flow", False, 
                               f"Token verification failed: Status {status}")
        
        # Check auth response structure
        magic_link_valid = (
            'access_token' in auth_data and
            'user' in auth_data and
            'email' in auth_data['user'] and
            auth_data['user']['verified'] is True
        )
        
        return self.log_test(
            "Magic Link Flow",
            magic_link_valid,
            f"Magic link flow completed: {magic_link_valid}"
        )

    def test_authentication_error_handling(self):
        """Test authentication error handling"""
        print("⚠️ Testing Authentication Error Handling...")
        
        results = []
        
        # Test invalid email format
        success, status, data, response = self.make_request('POST', 'auth/test-login', 
                                                          {"email": "invalid-email"}, 
                                                          expected_status=400)
        invalid_email_handled = success and status == 400
        results.append(invalid_email_handled)
        
        # Test missing email
        success, status, data, response = self.make_request('POST', 'auth/test-login', 
                                                          {}, expected_status=400)
        missing_email_handled = success and status == 400
        results.append(missing_email_handled)
        
        # Test invalid magic link token
        success, status, data, response = self.make_request('POST', 'auth/verify', 
                                                          {"token": "invalid_token"}, 
                                                          expected_status=400)
        invalid_token_handled = success and status == 400
        results.append(invalid_token_handled)
        
        error_handling_works = all(results)
        
        return self.log_test(
            "Authentication Error Handling",
            error_handling_works,
            f"Error cases handled properly: {sum(results)}/3"
        )

    def test_cors_and_headers(self):
        """Test CORS configuration and response headers"""
        print("🌐 Testing CORS and Headers...")
        
        # Test preflight request
        url = f"{self.api_url}/auth/me"
        headers = {
            'Origin': 'https://testid-enforcer.preview.emergentagent.com',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        try:
            response = requests.options(url, headers=headers, timeout=15)
            cors_configured = response.status_code in [200, 204]
            
            # Check CORS headers
            cors_headers_present = (
                'Access-Control-Allow-Origin' in response.headers or
                'access-control-allow-origin' in response.headers
            )
        except:
            cors_configured = False
            cors_headers_present = False
        
        return self.log_test(
            "CORS and Headers",
            cors_configured,
            f"CORS configured: {cors_configured}, Headers present: {cors_headers_present}"
        )

    def run_authentication_tests(self):
        """Run all authentication-focused tests"""
        print("🚀 AUTHENTICATION BACKEND TESTING SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 60)
        
        # Run tests in sequence (order matters for session-based tests)
        self.test_environment_variables()
        self.test_auth_me_unauthenticated()
        self.test_test_login_endpoint()
        self.test_auth_me_authenticated()
        self.test_session_persistence()
        self.test_token_validation()
        self.test_magic_link_flow()
        self.test_authentication_error_handling()
        self.test_cors_and_headers()
        
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
        
        print("\n✅ AUTHENTICATION SYSTEMS STATUS:")
        critical_auth_systems = [
            ("Test Login Endpoint", "Test Login Endpoint" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Auth Me Endpoint", "Auth Me Authenticated" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Session Persistence", "Session Persistence" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Environment Config", "Environment Variables" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        for system, status in critical_auth_systems:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {system}: {'WORKING' if status else 'FAILED'}")
        
        # Specific findings for the review request
        print("\n🔍 SPECIFIC FINDINGS FOR REVIEW REQUEST:")
        
        auth_me_working = "Auth Me Authenticated" not in [t.split(':')[0] for t in self.failed_tests]
        test_login_working = "Test Login Endpoint" not in [t.split(':')[0] for t in self.failed_tests]
        env_vars_working = "Environment Variables" not in [t.split(':')[0] for t in self.failed_tests]
        
        print(f"   • GET /api/auth/me endpoint: {'✅ WORKING' if auth_me_working else '❌ FAILING'}")
        print(f"   • POST /api/auth/test-login endpoint: {'✅ WORKING' if test_login_working else '❌ FAILING'}")
        print(f"   • Environment variables (TEST_MODE, ALLOW_TEST_LOGIN): {'✅ CONFIGURED' if env_vars_working else '❌ MISCONFIGURED'}")
        
        if not auth_me_working:
            print("   ⚠️  403 errors on /api/auth/me likely due to authentication issues")
        
        if not test_login_working:
            print("   ⚠️  Test login not working - may affect frontend authentication flow")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = AuthBackendTester()
    passed, total, failed = tester.run_authentication_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)