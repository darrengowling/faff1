#!/usr/bin/env python3
"""
Atomic League Creation Testing Suite
Focused testing for MongoDB transaction issues in league creation endpoint
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class AtomicLeagueCreationTester:
    def __init__(self, base_url="https://leaguemate-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data with unique timestamp
        timestamp = datetime.now().strftime('%H%M%S')
        self.test_email = f"atomic_test_{timestamp}@example.com"
        self.unique_league_name = f"Atomic Test League {timestamp}"
        
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

    def test_environment_setup(self):
        """Test environment configuration for TEST_MODE"""
        # Check health endpoint
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Environment Setup", False, f"Health check failed: {status}")
        
        # Verify TEST_MODE configuration
        env_valid = (
            'status' in data and
            'database' in data and
            data.get('database', {}).get('connected', False)
        )
        
        # Check if test endpoints are available
        success2, status2, data2 = self.make_request('GET', 'test/time/set', {"nowMs": int(time.time() * 1000)}, expected_status=403, token=None)
        test_mode_active = status2 == 403  # Should be forbidden without proper request
        
        return self.log_test(
            "Environment Setup",
            env_valid and test_mode_active,
            f"Health: {env_valid}, TEST_MODE: {test_mode_active}, DB Connected: {data.get('database', {}).get('connected', False)}"
        )

    def test_authentication_flow(self):
        """Test authentication using test login endpoint"""
        # Use test login endpoint for faster authentication
        success, status, data = self.make_request(
            'POST',
            'auth/test-login',
            {"email": self.test_email},
            token=None
        )
        
        if not success:
            return self.log_test("Authentication Flow", False, f"Test login failed: {status}, Response: {data}")
        
        # Verify response structure
        auth_valid = (
            'ok' in data and
            data['ok'] is True and
            'userId' in data and
            'email' in data and
            data['email'] == self.test_email
        )
        
        if auth_valid:
            # Get access token via auth/me endpoint
            success2, status2, me_data = self.make_request('GET', 'auth/me', token=None)
            if success2:
                # Extract token from cookie or use magic link flow
                # For now, let's use magic link flow to get proper token
                success3, status3, magic_data = self.make_request(
                    'POST',
                    'auth/magic-link',
                    {"email": self.test_email},
                    token=None
                )
                
                if success3 and 'dev_magic_link' in magic_data:
                    magic_link = magic_data['dev_magic_link']
                    token = magic_link.split('token=')[1]
                    
                    # Verify token
                    success4, status4, auth_data = self.make_request(
                        'POST',
                        'auth/verify',
                        {"token": token},
                        token=None
                    )
                    
                    if success4 and 'access_token' in auth_data:
                        self.token = auth_data['access_token']
                        self.user_data = auth_data['user']
                        return self.log_test("Authentication Flow", True, f"Token obtained for user: {self.test_email}")
        
        return self.log_test("Authentication Flow", False, f"Failed to obtain access token")

    def test_mongodb_configuration(self):
        """Test MongoDB configuration and transaction support"""
        # Check database health
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("MongoDB Configuration", False, f"Health check failed: {status}")
        
        db_info = data.get('database', {})
        db_connected = db_info.get('connected', False)
        collections_count = db_info.get('collections_count', 0)
        
        # Check if MongoDB is configured properly
        mongo_valid = (
            db_connected and
            collections_count >= 0  # Should have some collections
        )
        
        return self.log_test(
            "MongoDB Configuration",
            mongo_valid,
            f"Connected: {db_connected}, Collections: {collections_count}"
        )

    def test_league_creation_endpoint(self):
        """Test POST /leagues endpoint with unique league name"""
        if not self.token:
            return self.log_test("League Creation Endpoint", False, "No authentication token")
        
        # Create league with unique name to avoid duplicates
        league_data = {
            "name": self.unique_league_name,
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 5,
                "anti_snipe_seconds": 3,
                "bid_timer_seconds": 8,
                "league_size": {
                    "min": 2,
                    "max": 4
                },
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        print(f"🧪 Creating league with name: {self.unique_league_name}")
        
        # Make the league creation request
        success, status, data = self.make_request('POST', 'leagues', league_data, expected_status=201)
        
        if not success:
            error_details = f"Status: {status}, Response: {json.dumps(data, indent=2)}"
            
            # Check for specific MongoDB transaction errors
            if status == 500:
                error_msg = str(data)
                if "transaction" in error_msg.lower() or "replica set" in error_msg.lower():
                    error_details += " [MONGODB TRANSACTION ERROR DETECTED]"
                elif "duplicate" in error_msg.lower():
                    error_details += " [DUPLICATE NAME ERROR]"
            
            return self.log_test("League Creation Endpoint", False, error_details)
        
        # Validate 201 response with leagueId format
        response_valid = (
            status == 201 and
            'leagueId' in data and
            isinstance(data['leagueId'], str) and
            len(data['leagueId']) > 0
        )
        
        if response_valid:
            self.test_league_id = data['leagueId']
            return self.log_test(
                "League Creation Endpoint",
                True,
                f"✅ 201 response with leagueId: {data['leagueId']}"
            )
        else:
            return self.log_test(
                "League Creation Endpoint",
                False,
                f"Invalid response format: {json.dumps(data, indent=2)}"
            )

    def test_league_readiness_endpoint(self):
        """Test GET /test/league/:id/ready endpoint"""
        if not self.test_league_id:
            return self.log_test("League Readiness Endpoint", False, "No test league ID")
        
        # Test the readiness endpoint
        success, status, data = self.make_request('GET', f'test/league/{self.test_league_id}/ready', token=None)
        
        if not success:
            return self.log_test(
                "League Readiness Endpoint",
                False,
                f"Status: {status}, Response: {json.dumps(data, indent=2)}"
            )
        
        # Validate readiness response
        readiness_valid = (
            'ready' in data and
            isinstance(data['ready'], bool)
        )
        
        if readiness_valid:
            ready_status = data['ready']
            reason = data.get('reason', 'N/A')
            return self.log_test(
                "League Readiness Endpoint",
                True,
                f"Ready: {ready_status}, Reason: {reason}"
            )
        else:
            return self.log_test(
                "League Readiness Endpoint",
                False,
                f"Invalid response format: {json.dumps(data, indent=2)}"
            )

    def test_error_handling(self):
        """Test error handling for various scenarios"""
        if not self.token:
            return self.log_test("Error Handling", False, "No authentication token")
        
        error_tests = []
        
        # Test 1: Duplicate league name
        duplicate_data = {
            "name": self.unique_league_name,  # Same name as before
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 5,
                "anti_snipe_seconds": 3,
                "bid_timer_seconds": 8,
                "league_size": {"min": 2, "max": 4},
                "scoring_rules": {"club_goal": 1, "club_win": 3, "club_draw": 1}
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', duplicate_data, expected_status=400)
        duplicate_handled = success and status == 400
        error_tests.append(("Duplicate Name", duplicate_handled))
        
        # Test 2: Invalid league data
        invalid_data = {
            "name": "",  # Empty name
            "season": "2025-26",
            "settings": {}  # Empty settings
        }
        
        success2, status2, data2 = self.make_request('POST', 'leagues', invalid_data, expected_status=400)
        invalid_handled = success2 and status2 == 400
        error_tests.append(("Invalid Data", invalid_handled))
        
        # Test 3: Missing authentication
        success3, status3, data3 = self.make_request('POST', 'leagues', duplicate_data, expected_status=401, token="invalid_token")
        auth_handled = success3 and status3 == 401
        error_tests.append(("Invalid Auth", auth_handled))
        
        all_errors_handled = all(result for _, result in error_tests)
        
        return self.log_test(
            "Error Handling",
            all_errors_handled,
            f"Tests: {', '.join([f'{name}: {result}' for name, result in error_tests])}"
        )

    def test_backend_logs_analysis(self):
        """Analyze backend logs for transaction errors"""
        print("\n🔍 BACKEND LOGS ANALYSIS:")
        print("Checking supervisor backend logs for MongoDB transaction errors...")
        
        try:
            # Try to read backend logs
            import subprocess
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logs = result.stdout
                print("📋 Recent Backend Error Logs:")
                print("-" * 40)
                print(logs)
                print("-" * 40)
                
                # Check for specific MongoDB transaction errors
                transaction_errors = [
                    "Transaction numbers are only allowed on a replica set member or mongos",
                    "MongoServerError",
                    "TransactionError",
                    "replica set",
                    "transaction"
                ]
                
                found_errors = []
                for error in transaction_errors:
                    if error.lower() in logs.lower():
                        found_errors.append(error)
                
                if found_errors:
                    print(f"🚨 MONGODB TRANSACTION ERRORS DETECTED: {', '.join(found_errors)}")
                    return self.log_test("Backend Logs Analysis", False, f"Transaction errors found: {', '.join(found_errors)}")
                else:
                    print("✅ No MongoDB transaction errors found in recent logs")
                    return self.log_test("Backend Logs Analysis", True, "No transaction errors in logs")
            else:
                return self.log_test("Backend Logs Analysis", False, "Could not read backend logs")
                
        except Exception as e:
            return self.log_test("Backend Logs Analysis", False, f"Error reading logs: {str(e)}")

    def run_atomic_tests(self):
        """Run focused atomic league creation tests"""
        print("🧪 ATOMIC LEAGUE CREATION TESTING SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print(f"Test Email: {self.test_email}")
        print(f"Unique League Name: {self.unique_league_name}")
        print("=" * 60)
        
        # Environment Setup
        print("\n🔧 ENVIRONMENT SETUP")
        self.test_environment_setup()
        
        # Authentication
        print("\n🔐 AUTHENTICATION")
        self.test_authentication_flow()
        
        # MongoDB Configuration
        print("\n💾 MONGODB CONFIGURATION")
        self.test_mongodb_configuration()
        
        # Core League Creation Test
        print("\n🏟️ LEAGUE CREATION ENDPOINT")
        self.test_league_creation_endpoint()
        
        # Readiness Endpoint Test
        print("\n✅ LEAGUE READINESS ENDPOINT")
        self.test_league_readiness_endpoint()
        
        # Error Handling Tests
        print("\n🚨 ERROR HANDLING")
        self.test_error_handling()
        
        # Backend Logs Analysis
        print("\n📋 BACKEND LOGS ANALYSIS")
        self.test_backend_logs_analysis()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 ATOMIC TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        # Critical Analysis
        print("\n🔍 CRITICAL ANALYSIS:")
        league_creation_failed = any("League Creation Endpoint" in test for test in self.failed_tests)
        transaction_errors = any("transaction" in test.lower() or "replica set" in test.lower() for test in self.failed_tests)
        
        if league_creation_failed:
            print("❌ LEAGUE CREATION IS FAILING - This blocks the atomic navigation flow")
            if transaction_errors:
                print("🚨 MONGODB TRANSACTION CONFIGURATION ISSUE CONFIRMED")
                print("   - MongoDB is not configured as a replica set")
                print("   - Backend is trying to use transactions")
                print("   - Need to either configure MongoDB replica set or remove transaction usage")
            else:
                print("⚠️  League creation failing for other reasons - check error details above")
        else:
            print("✅ LEAGUE CREATION IS WORKING - Atomic navigation flow should work")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = AtomicLeagueCreationTester()
    passed, total, failed = tester.run_atomic_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)