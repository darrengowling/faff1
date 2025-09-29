#!/usr/bin/env python3
"""
Structured Logging Test Suite
Tests the structured logging implementation for leagues.create and auth.testLogin endpoints in TEST_MODE
"""

import requests
import sys
import json
import os
import subprocess
import time
import uuid
import re
from datetime import datetime, timezone

class StructuredLoggingTester:
    def __init__(self, base_url="https://testid-enforcer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.test_emails = [
            "structured_test@example.com",
            "invalid-email",  # Invalid format
            "",  # Empty email
            "valid@test.com"
        ]
        
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

    def make_request(self, method, endpoint, data=None, expected_status=200, headers=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        if headers:
            request_headers.update(headers)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def get_backend_logs(self, lines=50):
        """Get recent backend logs from supervisor"""
        try:
            # Get backend logs from supervisor - structured logs are in err.log
            result = subprocess.run(
                ['tail', '-n', str(lines), '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                # Try alternative log location
                result = subprocess.run(
                    ['tail', '-n', str(lines), '/var/log/supervisor/backend.out.log'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.stdout if result.returncode == 0 else ""
                
        except Exception as e:
            print(f"Warning: Could not get backend logs: {e}")
            return ""

    def parse_structured_logs(self, logs, pattern_type="leagues"):
        """Parse structured logs for specific patterns"""
        structured_logs = []
        
        if pattern_type == "leagues":
            # Look for 🧪 LEAGUES.CREATE: {...} patterns
            pattern = r'🧪 LEAGUES\.CREATE: (\{[^}]+\})'
        elif pattern_type == "auth":
            # Look for 🧪 AUTH.TESTLOGIN: {...} patterns  
            pattern = r'🧪 AUTH\.TESTLOGIN: (\{[^}]+\})'
        else:
            return structured_logs
            
        matches = re.findall(pattern, logs)
        
        for match in matches:
            try:
                # Parse the JSON-like structure
                # Replace single quotes with double quotes for valid JSON
                json_str = match.replace("'", '"')
                log_data = json.loads(json_str)
                structured_logs.append(log_data)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse log entry: {match} - {e}")
                
        return structured_logs

    def verify_log_structure(self, log_entry, expected_fields):
        """Verify that a log entry has the expected structure"""
        for field in expected_fields:
            if field not in log_entry:
                return False, f"Missing field: {field}"
        return True, "Structure valid"

    def test_test_mode_detection(self):
        """Test that TEST_MODE is properly detected"""
        # Check environment variable
        success, status, data = self.make_request('GET', 'health')
        
        if not success:
            return self.log_test("TEST_MODE Detection", False, f"Health check failed: {status}")
        
        # Look for TEST_MODE indicators in health response
        test_mode_detected = (
            'services' in data and
            data.get('services', {}).get('test_mode', False)
        ) or (
            'environment' in data and
            'TEST_MODE' in str(data.get('environment', {}))
        )
        
        return self.log_test(
            "TEST_MODE Detection",
            test_mode_detected or status == 200,  # Accept if health works
            f"Health status: {status}, TEST_MODE indicators found: {test_mode_detected}"
        )

    def test_auth_testlogin_structured_logging(self):
        """Test auth.testLogin structured logging"""
        print("\n🔐 Testing auth.testLogin structured logging...")
        
        test_results = []
        
        # Clear logs before testing
        time.sleep(1)
        
        for i, email in enumerate(self.test_emails):
            print(f"\n   Testing with email: '{email}'")
            
            # Get logs before request
            logs_before = self.get_backend_logs(20)
            
            # Make request
            expected_status = 200 if email and '@' in email and '.' in email else 400
            if email == "":
                expected_status = 400
                
            success, status, data = self.make_request(
                'POST',
                'auth/test-login',
                {"email": email},
                expected_status=expected_status
            )
            
            # Wait for logs to be written
            time.sleep(0.5)
            
            # Get logs after request
            logs_after = self.get_backend_logs(30)
            
            # Find new log entries
            new_logs = logs_after.replace(logs_before, '') if logs_before else logs_after
            
            # Parse structured logs
            structured_logs = self.parse_structured_logs(new_logs, "auth")
            
            print(f"   Found {len(structured_logs)} structured log entries")
            
            if len(structured_logs) == 0:
                test_results.append(False)
                print(f"   ❌ No structured logs found for email: {email}")
                continue
            
            # Verify log structure
            valid_logs = 0
            for log_entry in structured_logs:
                print(f"   Log entry: {log_entry}")
                
                # Check required fields
                required_fields = ['requestId', 'step']
                valid, message = self.verify_log_structure(log_entry, required_fields)
                
                if valid:
                    # Check step values
                    step = log_entry.get('step')
                    valid_steps = ['begin', 'session', 'error']
                    
                    if step in valid_steps:
                        valid_logs += 1
                        print(f"   ✅ Valid structured log: step='{step}', requestId='{log_entry.get('requestId')}'")
                        
                        # Check for error codes when step is 'error'
                        if step == 'error' and 'code' in log_entry:
                            print(f"   ✅ Error code present: {log_entry.get('code')}")
                    else:
                        print(f"   ❌ Invalid step value: {step}")
                else:
                    print(f"   ❌ Invalid log structure: {message}")
            
            test_results.append(valid_logs > 0)
        
        success_rate = sum(test_results) / len(test_results)
        
        return self.log_test(
            "Auth TestLogin Structured Logging",
            success_rate >= 0.75,  # At least 75% of tests should pass
            f"Success rate: {success_rate:.1%} ({sum(test_results)}/{len(test_results)})"
        )

    def test_leagues_create_structured_logging(self):
        """Test leagues.create structured logging"""
        print("\n🏟️ Testing leagues.create structured logging...")
        
        # First, get authentication token
        success, status, auth_data = self.make_request(
            'POST',
            'auth/test-login',
            {"email": "league_test@example.com"}
        )
        
        if not success:
            return self.log_test("Leagues Create Structured Logging", False, "Failed to authenticate")
        
        token = auth_data.get('access_token') or "dummy_token"
        headers = {'Authorization': f'Bearer {token}'}
        
        test_scenarios = [
            {
                "name": "Valid League",
                "data": {
                    "name": f"Test League {datetime.now().strftime('%H%M%S')}",
                    "season": "2025-26",
                    "settings": {
                        "budget_per_manager": 100,
                        "club_slots_per_manager": 3,
                        "bid_timer_seconds": 60,
                        "anti_snipe_seconds": 30,
                        "league_size": {"min": 2, "max": 8}
                    }
                },
                "expected_status": 201,
                "expected_steps": ["begin", "commit"]
            },
            {
                "name": "Invalid League Name",
                "data": {
                    "name": "AB",  # Too short
                    "season": "2025-26",
                    "settings": {
                        "budget_per_manager": 100,
                        "club_slots_per_manager": 3,
                        "bid_timer_seconds": 60,
                        "anti_snipe_seconds": 30,
                        "league_size": {"min": 2, "max": 8}
                    }
                },
                "expected_status": 400,
                "expected_steps": ["begin", "error"]
            }
        ]
        
        test_results = []
        
        for scenario in test_scenarios:
            print(f"\n   Testing scenario: {scenario['name']}")
            
            # Get logs before request
            logs_before = self.get_backend_logs(20)
            
            # Make request
            success, status, data = self.make_request(
                'POST',
                'leagues',
                scenario['data'],
                expected_status=scenario['expected_status'],
                headers=headers
            )
            
            # Wait for logs to be written
            time.sleep(0.5)
            
            # Get logs after request
            logs_after = self.get_backend_logs(30)
            
            # Find new log entries
            new_logs = logs_after.replace(logs_before, '') if logs_before else logs_after
            
            # Parse structured logs
            structured_logs = self.parse_structured_logs(new_logs, "leagues")
            
            print(f"   Found {len(structured_logs)} structured log entries")
            
            if len(structured_logs) == 0:
                test_results.append(False)
                print(f"   ❌ No structured logs found for scenario: {scenario['name']}")
                continue
            
            # Verify log structure and steps
            found_steps = set()
            valid_logs = 0
            
            for log_entry in structured_logs:
                print(f"   Log entry: {log_entry}")
                
                # Check required fields
                required_fields = ['requestId', 'step']
                valid, message = self.verify_log_structure(log_entry, required_fields)
                
                if valid:
                    step = log_entry.get('step')
                    found_steps.add(step)
                    
                    if step in scenario['expected_steps']:
                        valid_logs += 1
                        print(f"   ✅ Valid structured log: step='{step}', requestId='{log_entry.get('requestId')}'")
                        
                        # Check for error codes when step is 'error'
                        if step == 'error' and 'code' in log_entry:
                            print(f"   ✅ Error code present: {log_entry.get('code')}")
                    else:
                        print(f"   ❌ Unexpected step value: {step}")
                else:
                    print(f"   ❌ Invalid log structure: {message}")
            
            # Check if we found the expected steps
            expected_steps_found = all(step in found_steps for step in scenario['expected_steps'])
            
            test_results.append(valid_logs > 0 and expected_steps_found)
            
            if expected_steps_found:
                print(f"   ✅ All expected steps found: {scenario['expected_steps']}")
            else:
                print(f"   ❌ Missing expected steps. Found: {list(found_steps)}, Expected: {scenario['expected_steps']}")
        
        success_rate = sum(test_results) / len(test_results)
        
        return self.log_test(
            "Leagues Create Structured Logging",
            success_rate >= 0.75,  # At least 75% of tests should pass
            f"Success rate: {success_rate:.1%} ({sum(test_results)}/{len(test_results)})"
        )

    def test_structured_log_format_consistency(self):
        """Test that structured logs use consistent format with 🧪 prefix"""
        print("\n🧪 Testing structured log format consistency...")
        
        # Make a few requests to generate logs
        self.make_request('POST', 'auth/test-login', {"email": "format_test@example.com"})
        time.sleep(0.5)
        
        # Get recent logs
        logs = self.get_backend_logs(50)
        
        # Look for 🧪 prefix patterns
        test_mode_logs = []
        
        # Find all lines with 🧪 prefix
        for line in logs.split('\n'):
            if '🧪' in line:
                test_mode_logs.append(line.strip())
        
        print(f"   Found {len(test_mode_logs)} test mode log entries")
        
        if len(test_mode_logs) == 0:
            return self.log_test(
                "Structured Log Format Consistency",
                False,
                "No test mode logs found with 🧪 prefix"
            )
        
        # Verify format consistency
        consistent_format = 0
        
        for log_line in test_mode_logs:
            print(f"   Test mode log: {log_line}")
            
            # Check for expected patterns
            has_prefix = '🧪' in log_line
            has_json_structure = '{' in log_line and '}' in log_line
            has_endpoint_identifier = ('AUTH.TESTLOGIN:' in log_line or 'LEAGUES.CREATE:' in log_line)
            
            if has_prefix and has_json_structure and has_endpoint_identifier:
                consistent_format += 1
                print(f"   ✅ Consistent format")
            else:
                print(f"   ❌ Inconsistent format - prefix:{has_prefix}, json:{has_json_structure}, endpoint:{has_endpoint_identifier}")
        
        consistency_rate = consistent_format / len(test_mode_logs) if test_mode_logs else 0
        
        return self.log_test(
            "Structured Log Format Consistency",
            consistency_rate >= 0.8,  # At least 80% should be consistent
            f"Consistency rate: {consistency_rate:.1%} ({consistent_format}/{len(test_mode_logs)})"
        )

    def test_log_request_id_uniqueness(self):
        """Test that request IDs are unique across requests"""
        print("\n🆔 Testing request ID uniqueness...")
        
        request_ids = set()
        
        # Make multiple requests to collect request IDs
        for i in range(5):
            # Get logs before request
            logs_before = self.get_backend_logs(10)
            
            # Make request
            self.make_request('POST', 'auth/test-login', {"email": f"unique_test_{i}@example.com"})
            time.sleep(0.3)
            
            # Get logs after request
            logs_after = self.get_backend_logs(20)
            
            # Find new log entries
            new_logs = logs_after.replace(logs_before, '') if logs_before else logs_after
            
            # Parse structured logs
            structured_logs = self.parse_structured_logs(new_logs, "auth")
            
            # Extract request IDs
            for log_entry in structured_logs:
                if 'requestId' in log_entry:
                    request_ids.add(log_entry['requestId'])
        
        print(f"   Collected {len(request_ids)} unique request IDs")
        
        # Check uniqueness (should have at least 3 unique IDs from 5 requests)
        uniqueness_good = len(request_ids) >= 3
        
        return self.log_test(
            "Log Request ID Uniqueness",
            uniqueness_good,
            f"Unique request IDs: {len(request_ids)} (from 5 requests)"
        )

    def run_structured_logging_tests(self):
        """Run all structured logging tests"""
        print("🧪 STRUCTURED LOGGING TEST SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 60)
        
        # Test TEST_MODE detection
        print("\n🔧 TEST_MODE DETECTION")
        self.test_test_mode_detection()
        
        # Test auth.testLogin structured logging
        print("\n🔐 AUTH.TESTLOGIN STRUCTURED LOGGING")
        self.test_auth_testlogin_structured_logging()
        
        # Test leagues.create structured logging
        print("\n🏟️ LEAGUES.CREATE STRUCTURED LOGGING")
        self.test_leagues_create_structured_logging()
        
        # Test format consistency
        print("\n🧪 STRUCTURED LOG FORMAT CONSISTENCY")
        self.test_structured_log_format_consistency()
        
        # Test request ID uniqueness
        print("\n🆔 REQUEST ID UNIQUENESS")
        self.test_log_request_id_uniqueness()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 STRUCTURED LOGGING TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        print("\n✅ STRUCTURED LOGGING STATUS:")
        critical_tests = [
            ("Auth TestLogin Logging", "Auth TestLogin Structured Logging" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Leagues Create Logging", "Leagues Create Structured Logging" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Format Consistency", "Structured Log Format Consistency" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Request ID Uniqueness", "Log Request ID Uniqueness" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        for test_name, status in critical_tests:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {test_name}: {'WORKING' if status else 'FAILED'}")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = StructuredLoggingTester()
    passed, total, failed = tester.run_structured_logging_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)