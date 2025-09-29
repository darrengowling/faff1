#!/usr/bin/env python3
"""
Frontend Authentication Simulation Test
Simulates the exact frontend authentication behavior to identify routing issues
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class FrontendAuthSimulator:
    def __init__(self, base_url="https://testid-enforcer.preview.emergentagent.com"):
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

    def simulate_frontend_auth_check(self):
        """Simulate how frontend checks authentication status"""
        print("🔍 Simulating Frontend Authentication Check...")
        
        # Simulate a fresh browser session (no cookies)
        session = requests.Session()
        
        # Make request to /api/auth/me without any authentication
        url = f"{self.api_url}/auth/me"
        headers = {
            'Content-Type': 'application/json',
            'Origin': self.base_url,
            'Referer': f"{self.base_url}/login"
        }
        
        try:
            response = session.get(url, headers=headers, timeout=15)
            status_code = response.status_code
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            # Frontend expects 401/403 for unauthenticated users
            expected_behavior = status_code in [401, 403]
            
            return self.log_test(
                "Frontend Auth Check Simulation",
                expected_behavior,
                f"Status: {status_code}, Response: {response_data}"
            )
            
        except requests.exceptions.RequestException as e:
            return self.log_test(
                "Frontend Auth Check Simulation",
                False,
                f"Request failed: {str(e)}"
            )

    def simulate_login_page_access(self):
        """Simulate accessing the login page"""
        print("🔍 Simulating Login Page Access...")
        
        session = requests.Session()
        
        # First, check auth status (what frontend does on page load)
        auth_url = f"{self.api_url}/auth/me"
        headers = {
            'Content-Type': 'application/json',
            'Origin': self.base_url,
            'Referer': f"{self.base_url}/login"
        }
        
        try:
            auth_response = session.get(auth_url, headers=headers, timeout=15)
            auth_status = auth_response.status_code
            
            # If user is already authenticated, frontend might redirect
            if auth_status == 200:
                return self.log_test(
                    "Login Page Access Simulation",
                    False,
                    f"User appears to be already authenticated (Status: {auth_status})"
                )
            
            # If 403/401, user should see login form
            if auth_status in [401, 403]:
                return self.log_test(
                    "Login Page Access Simulation",
                    True,
                    f"Unauthenticated user should see login form (Status: {auth_status})"
                )
            
            return self.log_test(
                "Login Page Access Simulation",
                False,
                f"Unexpected auth status: {auth_status}"
            )
            
        except requests.exceptions.RequestException as e:
            return self.log_test(
                "Login Page Access Simulation",
                False,
                f"Auth check failed: {str(e)}"
            )

    def simulate_test_login_flow(self):
        """Simulate the complete test login flow as frontend would do it"""
        print("🔍 Simulating Complete Test Login Flow...")
        
        session = requests.Session()
        test_email = "frontend_sim@example.com"
        
        # Step 1: Frontend calls test-login endpoint
        login_url = f"{self.api_url}/auth/test-login"
        login_data = {"email": test_email}
        headers = {
            'Content-Type': 'application/json',
            'Origin': self.base_url,
            'Referer': f"{self.base_url}/login"
        }
        
        try:
            login_response = session.post(login_url, json=login_data, headers=headers, timeout=15)
            login_status = login_response.status_code
            
            if login_status != 200:
                return self.log_test(
                    "Test Login Flow Simulation",
                    False,
                    f"Test login failed: Status {login_status}"
                )
            
            login_data_response = login_response.json()
            
            # Step 2: Frontend should now be able to call /auth/me successfully
            auth_url = f"{self.api_url}/auth/me"
            auth_response = session.get(auth_url, headers=headers, timeout=15)
            auth_status = auth_response.status_code
            
            if auth_status != 200:
                return self.log_test(
                    "Test Login Flow Simulation",
                    False,
                    f"Auth check after login failed: Status {auth_status}"
                )
            
            auth_data = auth_response.json()
            
            # Verify the auth data matches login
            auth_valid = (
                'email' in auth_data and
                auth_data['email'] == test_email and
                'verified' in auth_data and
                auth_data['verified'] is True
            )
            
            return self.log_test(
                "Test Login Flow Simulation",
                auth_valid,
                f"Login successful, auth data valid: {auth_valid}"
            )
            
        except requests.exceptions.RequestException as e:
            return self.log_test(
                "Test Login Flow Simulation",
                False,
                f"Request failed: {str(e)}"
            )

    def simulate_cross_origin_requests(self):
        """Simulate cross-origin requests that might cause issues"""
        print("🔍 Simulating Cross-Origin Authentication Requests...")
        
        session = requests.Session()
        
        # Simulate request from different origins
        origins_to_test = [
            self.base_url,
            "http://localhost:3000",
            "https://localhost:3000"
        ]
        
        results = []
        
        for origin in origins_to_test:
            headers = {
                'Content-Type': 'application/json',
                'Origin': origin,
                'Referer': f"{origin}/login"
            }
            
            try:
                response = session.get(f"{self.api_url}/auth/me", headers=headers, timeout=15)
                # Should get 403/401 for unauthenticated, but not CORS errors
                cors_working = response.status_code in [401, 403, 200]
                results.append(cors_working)
                
            except requests.exceptions.RequestException:
                results.append(False)
        
        cors_success = all(results)
        
        return self.log_test(
            "Cross-Origin Requests Simulation",
            cors_success,
            f"CORS working for {sum(results)}/{len(results)} origins"
        )

    def simulate_session_cookie_issues(self):
        """Simulate potential session cookie issues"""
        print("🔍 Simulating Session Cookie Issues...")
        
        # Test 1: Login and check if cookies are set properly
        session = requests.Session()
        test_email = "cookie_test@example.com"
        
        # Login
        login_response = session.post(
            f"{self.api_url}/auth/test-login",
            json={"email": test_email},
            timeout=15
        )
        
        if login_response.status_code != 200:
            return self.log_test(
                "Session Cookie Issues Simulation",
                False,
                f"Login failed: {login_response.status_code}"
            )
        
        # Check if cookies were set
        cookies_set = len(session.cookies) > 0
        has_access_token = any('access_token' in cookie.name for cookie in session.cookies)
        
        # Test auth/me with cookies
        auth_response = session.get(f"{self.api_url}/auth/me", timeout=15)
        auth_working = auth_response.status_code == 200
        
        # Test 2: Simulate cookie issues by clearing cookies and trying auth
        session.cookies.clear()
        auth_response_no_cookies = session.get(f"{self.api_url}/auth/me", timeout=15)
        properly_rejected = auth_response_no_cookies.status_code in [401, 403]
        
        cookie_system_working = cookies_set and has_access_token and auth_working and properly_rejected
        
        return self.log_test(
            "Session Cookie Issues Simulation",
            cookie_system_working,
            f"Cookies set: {cookies_set}, Has token: {has_access_token}, Auth works: {auth_working}, Properly rejected: {properly_rejected}"
        )

    def simulate_token_expiry_handling(self):
        """Simulate token expiry scenarios"""
        print("🔍 Simulating Token Expiry Handling...")
        
        session = requests.Session()
        
        # Set an invalid/expired token manually
        session.cookies.set('access_token', 'expired_token_12345')
        
        # Try to access auth/me
        try:
            response = session.get(f"{self.api_url}/auth/me", timeout=15)
            expired_token_handled = response.status_code in [401, 403]
            
            return self.log_test(
                "Token Expiry Handling Simulation",
                expired_token_handled,
                f"Expired token properly rejected: Status {response.status_code}"
            )
            
        except requests.exceptions.RequestException as e:
            return self.log_test(
                "Token Expiry Handling Simulation",
                False,
                f"Request failed: {str(e)}"
            )

    def run_frontend_simulation_tests(self):
        """Run all frontend simulation tests"""
        print("🚀 FRONTEND AUTHENTICATION SIMULATION SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 60)
        
        # Run simulation tests
        self.simulate_frontend_auth_check()
        self.simulate_login_page_access()
        self.simulate_test_login_flow()
        self.simulate_cross_origin_requests()
        self.simulate_session_cookie_issues()
        self.simulate_token_expiry_handling()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 FRONTEND SIMULATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        print("\n🔍 ANALYSIS FOR FRONTEND ROUTING ISSUES:")
        
        auth_check_working = "Frontend Auth Check Simulation" not in [t.split(':')[0] for t in self.failed_tests]
        login_flow_working = "Test Login Flow Simulation" not in [t.split(':')[0] for t in self.failed_tests]
        cookie_system_working = "Session Cookie Issues Simulation" not in [t.split(':')[0] for t in self.failed_tests]
        
        print(f"   • Frontend auth check behavior: {'✅ CORRECT' if auth_check_working else '❌ PROBLEMATIC'}")
        print(f"   • Test login flow: {'✅ WORKING' if login_flow_working else '❌ BROKEN'}")
        print(f"   • Session cookie system: {'✅ WORKING' if cookie_system_working else '❌ BROKEN'}")
        
        if not auth_check_working:
            print("   ⚠️  Frontend auth check not behaving as expected - may cause routing issues")
        
        if not login_flow_working:
            print("   ⚠️  Test login flow broken - frontend cannot authenticate users")
        
        if not cookie_system_working:
            print("   ⚠️  Session cookie system issues - authentication state not persisting")
        
        # Specific diagnosis for the review request issue
        print("\n🎯 DIAGNOSIS FOR REVIEW REQUEST:")
        print("   Issue: /login redirects to landing page instead of showing login form")
        print("   Issue: 403 errors on /api/auth/me")
        
        if auth_check_working and login_flow_working:
            print("   ✅ Backend authentication is working correctly")
            print("   🔍 Issue is likely in frontend routing logic, not backend")
            print("   💡 Frontend may be incorrectly interpreting 403 responses")
        else:
            print("   ❌ Backend authentication has issues that could cause frontend problems")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    simulator = FrontendAuthSimulator()
    passed, total, failed = simulator.run_frontend_simulation_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)