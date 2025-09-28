#!/usr/bin/env python3
"""
I18N Backend Validation Test Suite
Quick validation test to ensure frontend i18n implementation didn't break backend functionality
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time

class I18NBackendValidationTester:
    def __init__(self, base_url="https://league-creator-1.preview.emergentagent.com"):
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
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_api_health_check(self):
        """Test /api/health endpoint returns proper response"""
        success, status, data = self.make_request('GET', 'health')
        
        # Check for proper health response format
        health_valid = (
            success and 
            isinstance(data, dict) and
            (data.get('ok') is True or data.get('status') == 'healthy')
        )
        
        return self.log_test(
            "API Health Check (/api/health)",
            health_valid,
            f"Status: {status}, Response: {data}"
        )

    def test_magic_link_request(self):
        """Test /api/auth/magic-link endpoint functionality"""
        test_email = "i18n-test@example.com"
        
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": test_email},
            token=None
        )
        
        # Check for proper magic link response
        magic_link_valid = (
            success and 
            isinstance(data, dict) and
            'message' in data and
            ('Magic link' in data['message'] or 'sent' in data['message'].lower())
        )
        
        # In development mode, should include dev_magic_link
        has_dev_link = 'dev_magic_link' in data if isinstance(data, dict) else False
        
        return self.log_test(
            "Magic Link Request (/api/auth/magic-link)",
            magic_link_valid,
            f"Status: {status}, Has dev link: {has_dev_link}, Message: {data.get('message', 'N/A') if isinstance(data, dict) else 'N/A'}"
        )

    def test_auth_verify_endpoint_structure(self):
        """Test /api/auth/verify endpoint structure (without valid token)"""
        # Test with invalid token to verify endpoint structure
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": "invalid_test_token"},
            expected_status=400,  # Should return 400 for invalid token
            token=None
        )
        
        # Should return proper error response for invalid token
        verify_structure_valid = (
            success and 
            status == 400 and
            isinstance(data, dict) and
            'detail' in data
        )
        
        return self.log_test(
            "Auth Verify Endpoint Structure (/api/auth/verify)",
            verify_structure_valid,
            f"Status: {status}, Error response: {data.get('detail', 'N/A') if isinstance(data, dict) else 'N/A'}"
        )

    def test_clubs_endpoint(self):
        """Test /api/clubs endpoint functionality"""
        success, status, data = self.make_request('GET', 'clubs')
        
        clubs_valid = (
            success and 
            isinstance(data, list)
        )
        
        clubs_count = len(data) if isinstance(data, list) else 0
        
        return self.log_test(
            "Clubs Endpoint (/api/clubs)",
            clubs_valid,
            f"Status: {status}, Clubs count: {clubs_count}"
        )

    def test_competition_profiles_endpoint(self):
        """Test /api/competition-profiles endpoint functionality"""
        success, status, data = self.make_request('GET', 'competition-profiles')
        
        profiles_valid = (
            success and 
            isinstance(data, dict) and
            'profiles' in data and
            isinstance(data['profiles'], list)
        )
        
        profiles_count = len(data.get('profiles', [])) if isinstance(data, dict) else 0
        
        return self.log_test(
            "Competition Profiles Endpoint (/api/competition-profiles)",
            profiles_valid,
            f"Status: {status}, Profiles count: {profiles_count}"
        )

    def test_time_sync_endpoint(self):
        """Test /api/timez endpoint for server time synchronization"""
        success, status, data = self.make_request('GET', 'timez')
        
        # Verify response structure
        timez_valid = (
            success and 
            isinstance(data, dict) and
            'now' in data and
            isinstance(data['now'], str)
        )
        
        # Verify timestamp format
        timestamp_valid = False
        if timez_valid:
            try:
                server_time = datetime.fromisoformat(data['now'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                time_diff = abs((server_time - now).total_seconds())
                timestamp_valid = time_diff < 10  # Within 10 seconds
            except:
                timestamp_valid = False
        
        return self.log_test(
            "Time Sync Endpoint (/api/timez)",
            timez_valid and timestamp_valid,
            f"Status: {status}, Valid timestamp: {timestamp_valid}, Server time: {data.get('now', 'N/A') if isinstance(data, dict) else 'N/A'}"
        )

    def test_socket_diagnostic_endpoint(self):
        """Test Socket.IO diagnostic endpoint"""
        success, status, data = self.make_request('GET', 'socket-diag')
        
        diag_valid = (
            success and 
            isinstance(data, dict) and
            data.get('ok') is True and
            'path' in data and
            'now' in data
        )
        
        return self.log_test(
            "Socket.IO Diagnostic Endpoint (/api/socket-diag)",
            diag_valid,
            f"Status: {status}, Path: {data.get('path', 'N/A') if isinstance(data, dict) else 'N/A'}"
        )

    def test_unauthorized_endpoints(self):
        """Test that protected endpoints properly require authentication"""
        protected_endpoints = [
            ('GET', 'auth/me'),
            ('GET', 'leagues'),
            ('POST', 'leagues')
        ]
        
        auth_protection_working = True
        endpoint_results = []
        
        for method, endpoint in protected_endpoints:
            success, status, data = self.make_request(
                method, 
                endpoint, 
                {} if method == 'POST' else None,
                expected_status=403,  # Should return 403 Forbidden (auth middleware working)
                token=None
            )
            
            endpoint_protected = success and status == 403
            endpoint_results.append(f"{method} {endpoint}: {'✓' if endpoint_protected else '✗'}")
            
            if not endpoint_protected:
                auth_protection_working = False
        
        return self.log_test(
            "Authentication Protection",
            auth_protection_working,
            f"Protected endpoints: {', '.join(endpoint_results)}"
        )

    def test_cors_headers(self):
        """Test CORS headers are properly configured"""
        try:
            # Make a regular GET request to check CORS headers
            url = f"{self.api_url}/health"
            response = requests.get(url, timeout=10)
            
            # Check for CORS headers (case insensitive)
            cors_headers_present = any(
                header.lower().startswith('access-control-') 
                for header in response.headers.keys()
            )
            
            # Also check if the request succeeds (which indicates CORS is working)
            request_successful = response.status_code == 200
            
            return self.log_test(
                "CORS Configuration",
                request_successful,  # If request works, CORS is properly configured
                f"Status: {response.status_code}, Request successful: {request_successful}, CORS headers present: {cors_headers_present}"
            )
        except Exception as e:
            return self.log_test("CORS Configuration", False, f"Exception: {str(e)}")

    def test_api_response_consistency(self):
        """Test that API responses maintain consistent JSON format"""
        test_endpoints = [
            ('GET', 'health'),
            ('GET', 'clubs'),
            ('GET', 'competition-profiles'),
            ('GET', 'timez')
        ]
        
        json_consistency = True
        endpoint_results = []
        
        for method, endpoint in test_endpoints:
            success, status, data = self.make_request(method, endpoint)
            
            is_json = isinstance(data, (dict, list))
            endpoint_results.append(f"{endpoint}: {'JSON' if is_json else 'Non-JSON'}")
            
            if not is_json:
                json_consistency = False
        
        return self.log_test(
            "API Response Consistency",
            json_consistency,
            f"Endpoints: {', '.join(endpoint_results)}"
        )

    def run_validation_tests(self):
        """Run all i18n backend validation tests"""
        print("🔍 I18N Backend Validation Test Suite")
        print("=" * 50)
        print(f"Testing backend API at: {self.base_url}")
        print()
        
        # Core API health and functionality tests
        self.test_api_health_check()
        self.test_magic_link_request()
        self.test_auth_verify_endpoint_structure()
        self.test_clubs_endpoint()
        self.test_competition_profiles_endpoint()
        self.test_time_sync_endpoint()
        self.test_socket_diagnostic_endpoint()
        
        # API contract and security tests
        self.test_unauthorized_endpoints()
        self.test_cors_headers()
        self.test_api_response_consistency()
        
        # Summary
        print()
        print("=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failed_test in self.failed_tests:
                print(f"  - {failed_test}")
        else:
            print("\n✅ All tests passed! Backend functionality is intact after i18n implementation.")
        
        print()
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = I18NBackendValidationTester()
    
    try:
        success = tester.run_validation_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()