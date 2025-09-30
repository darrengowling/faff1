#!/usr/bin/env python3
"""
Email Validation Fix Testing Suite
Tests the specific email validation fixes for auth endpoints
"""

import requests
import sys
import json
import os
import subprocess
from datetime import datetime, timezone

class EmailValidationTester:
    def __init__(self, base_url="https://test-harmony.preview.emergentagent.com"):
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

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def check_backend_logs(self):
        """Check backend logs for email validation startup messages"""
        try:
            result = subprocess.run(
                ["grep", "-i", "email.validation\\|email-validator", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            logs = result.stdout
            
            # Check for email validation startup messages
            has_email_validator_check = "Email validation status:" in logs
            has_version_info = "version: 2.1.1" in logs or "version 2.1.1" in logs
            has_self_test = "Email validation self-test passed" in logs
            
            return self.log_test(
                "Backend Email Validation Startup",
                has_email_validator_check and has_version_info and has_self_test,
                f"Startup check: {has_email_validator_check}, Version: {has_version_info}, Self-test: {has_self_test}"
            )
            
        except Exception as e:
            return self.log_test(
                "Backend Email Validation Startup",
                False,
                f"Could not check logs: {str(e)}"
            )

    def test_test_login_endpoint_valid_email(self):
        """Test /auth/test-login endpoint with valid email"""
        success, status, data = self.make_request(
            'POST', 
            'auth/test-login', 
            {"email": "test@example.com"},
            expected_status=200
        )
        
        valid_response = (
            success and
            data.get('ok') is True and
            'userId' in data and
            'email' in data and
            data['email'] == "test@example.com"
        )
        
        return self.log_test(
            "Test Login - Valid Email",
            valid_response,
            f"Status: {status}, Response: {data.get('message', 'No message')}"
        )

    def test_test_login_endpoint_invalid_email(self):
        """Test /auth/test-login endpoint with invalid email"""
        success, status, data = self.make_request(
            'POST', 
            'auth/test-login', 
            {"email": "bad@@example.com"},
            expected_status=400
        )
        
        valid_error_response = (
            success and
            status == 400 and
            isinstance(data.get('detail'), dict) and
            data['detail'].get('code') == 'INVALID_EMAIL' and
            'message' in data['detail']
        )
        
        return self.log_test(
            "Test Login - Invalid Email",
            valid_error_response,
            f"Status: {status}, Error code: {data.get('detail', {}).get('code', 'None')}"
        )

    def test_test_login_endpoint_empty_email(self):
        """Test /auth/test-login endpoint with empty email"""
        success, status, data = self.make_request(
            'POST', 
            'auth/test-login', 
            {"email": ""},
            expected_status=400
        )
        
        valid_error_response = (
            success and
            status == 400 and
            isinstance(data.get('detail'), dict) and
            data['detail'].get('code') == 'INVALID_EMAIL'
        )
        
        return self.log_test(
            "Test Login - Empty Email",
            valid_error_response,
            f"Status: {status}, Error code: {data.get('detail', {}).get('code', 'None')}"
        )

    def test_magic_link_endpoint_valid_email(self):
        """Test /auth/magic-link endpoint with valid email"""
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": "user@domain.com"},
            expected_status=200
        )
        
        valid_response = (
            success and
            'message' in data and
            ('dev_magic_link' in data or 'Magic link sent' in data['message'])
        )
        
        return self.log_test(
            "Magic Link - Valid Email",
            valid_response,
            f"Status: {status}, Has dev link: {'dev_magic_link' in data}"
        )

    def test_magic_link_endpoint_invalid_email(self):
        """Test /auth/magic-link endpoint with invalid email"""
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": "invalid@@domain"},
            expected_status=422  # Pydantic validation returns 422, not 400
        )
        
        # Pydantic returns 422 with validation error details
        # The key is that no 500 AttributeError occurs
        valid_error_response = (
            success and
            status == 422 and
            'detail' in data and
            isinstance(data['detail'], list) and
            len(data['detail']) > 0 and
            'type' in data['detail'][0] and
            data['detail'][0]['type'] == 'value_error'
        )
        
        return self.log_test(
            "Magic Link - Invalid Email (No AttributeError)",
            valid_error_response,
            f"Status: {status}, Pydantic validation working, No 500 error"
        )

    def test_magic_link_endpoint_no_email(self):
        """Test /auth/magic-link endpoint with no email"""
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {},
            expected_status=422  # Pydantic validation returns 422 for missing fields
        )
        
        # Pydantic returns 422 with validation error details
        # The key is that no 500 AttributeError occurs
        valid_error_response = (
            success and
            status == 422 and
            'detail' in data and
            isinstance(data['detail'], list) and
            len(data['detail']) > 0 and
            'type' in data['detail'][0] and
            data['detail'][0]['type'] == 'missing'
        )
        
        return self.log_test(
            "Magic Link - No Email (No AttributeError)",
            valid_error_response,
            f"Status: {status}, Pydantic validation working, No 500 error"
        )

    def test_no_500_errors_on_invalid_input(self):
        """Test that no 500 errors occur for invalid email inputs"""
        test_cases = [
            {"email": "bad@@example.com"},
            {"email": ""},
            {"email": "invalid.email"},
            {"email": "@domain.com"},
            {"email": "user@"},
            {"email": "user@domain@com"},
        ]
        
        no_500_errors = True
        error_details = []
        
        for test_case in test_cases:
            # Test magic-link endpoint (expects 422 from Pydantic or 400 from custom validation)
            success, status, data = self.make_request(
                'POST', 
                'auth/magic-link', 
                test_case
            )
            
            if status == 500:
                no_500_errors = False
                error_details.append(f"Magic link 500 error for {test_case['email']}")
            
            # Test test-login endpoint (expects 400 from custom validation)
            success2, status2, data2 = self.make_request(
                'POST', 
                'auth/test-login', 
                test_case
            )
            
            if status2 == 500:
                no_500_errors = False
                error_details.append(f"Test login 500 error for {test_case['email']}")
        
        return self.log_test(
            "No 500 Errors on Invalid Input",
            no_500_errors,
            f"Tested {len(test_cases)} invalid inputs. Errors: {'; '.join(error_details) if error_details else 'None'}"
        )

    def test_structured_error_responses(self):
        """Test that error responses have proper structure"""
        # Test with invalid email - magic-link uses Pydantic validation (422)
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": "bad@@example.com"},
            expected_status=422
        )
        
        # Pydantic returns 422 with validation error details
        pydantic_structure = (
            success and
            status == 422 and
            'detail' in data and
            isinstance(data['detail'], list) and
            len(data['detail']) > 0
        )
        
        # Test with test-login endpoint - uses custom validation (400)
        success2, status2, data2 = self.make_request(
            'POST', 
            'auth/test-login', 
            {"email": "bad@@example.com"},
            expected_status=400
        )
        
        # Custom validation returns 400 with structured error
        detail2 = data2.get('detail', {})
        custom_structure = (
            success2 and
            status2 == 400 and
            isinstance(detail2, dict) and
            'code' in detail2 and
            'message' in detail2 and
            detail2['code'] == 'INVALID_EMAIL'
        )
        
        return self.log_test(
            "Error Response Structure",
            pydantic_structure and custom_structure,
            f"Pydantic (422): {pydantic_structure}, Custom (400): {custom_structure}"
        )

    def test_email_validator_version(self):
        """Test that email-validator version 2.1.1 is being used"""
        try:
            result = subprocess.run(
                ["grep", "-i", "email.validation\\|email-validator", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            logs = result.stdout
            
            # Look for version information
            has_version_211 = "version: 2.1.1" in logs or "version 2.1.1" in logs
            has_email_validator = "email-validator" in logs
            
            return self.log_test(
                "Email Validator Version 2.1.1",
                has_version_211 and has_email_validator,
                f"Version 2.1.1 found: {has_version_211}, Email validator mentioned: {has_email_validator}"
            )
            
        except Exception as e:
            return self.log_test(
                "Email Validator Version 2.1.1",
                False,
                f"Could not check version: {str(e)}"
            )

    def run_email_validation_tests(self):
        """Run all email validation tests"""
        print("🔍 EMAIL VALIDATION FIX TESTING SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 60)
        
        # Check backend startup logs
        print("\n📋 BACKEND STARTUP VALIDATION")
        self.check_backend_logs()
        self.test_email_validator_version()
        
        # Test /auth/test-login endpoint
        print("\n🧪 /AUTH/TEST-LOGIN ENDPOINT TESTS")
        self.test_test_login_endpoint_valid_email()
        self.test_test_login_endpoint_invalid_email()
        self.test_test_login_endpoint_empty_email()
        
        # Test /auth/magic-link endpoint
        print("\n✨ /AUTH/MAGIC-LINK ENDPOINT TESTS")
        self.test_magic_link_endpoint_valid_email()
        self.test_magic_link_endpoint_invalid_email()
        self.test_magic_link_endpoint_no_email()
        
        # Test error handling
        print("\n🛡️ ERROR HANDLING TESTS")
        self.test_no_500_errors_on_invalid_input()
        self.test_structured_error_responses()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 EMAIL VALIDATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        print("\n✅ EMAIL VALIDATION FIX STATUS:")
        critical_fixes = [
            ("No AttributeError", "AttributeError" not in str(self.failed_tests)),
            ("Structured Error Responses", "Structured Error Responses" not in [t.split(':')[0] for t in self.failed_tests]),
            ("No 500 Errors", "No 500 Errors on Invalid Input" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Email Validator Working", "Email Validator Version 2.1.1" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        for fix, status in critical_fixes:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {fix}: {'WORKING' if status else 'FAILED'}")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = EmailValidationTester()
    passed, total, failed = tester.run_email_validation_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)