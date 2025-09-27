#!/usr/bin/env python3
"""
Fix Verification Test Suite
Tests the specific fixes implemented:
1. League Invitation Fix (InvitationEmailRequest model)
2. Auction Engine Fix (proper error handling)
3. Health Endpoint Fix (detailed health information)
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class FixVerificationTester:
    def __init__(self, base_url="https://pifa-friends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.test_email = "fix_test@example.com"
        self.manager_email = "manager_fix_test@example.com"
        
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
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=15)
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

    def setup_authentication(self):
        """Setup authentication for testing"""
        print("🔐 Setting up authentication...")
        
        # Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success or 'dev_magic_link' not in data:
            print(f"❌ Failed to get magic link: {status}")
            return False
        
        # Extract token
        magic_link = data['dev_magic_link']
        token = magic_link.split('token=')[1]
        
        # Verify token
        success, status, auth_data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if success and 'access_token' in auth_data:
            self.token = auth_data['access_token']
            self.user_data = auth_data['user']
            print(f"✅ Authentication successful for {self.test_email}")
            return True
        else:
            print(f"❌ Token verification failed: {status}")
            return False

    def setup_test_league(self):
        """Create a test league for testing"""
        print("🏟️ Creating test league...")
        
        league_data = {
            "name": f"Fix Test League {datetime.now().strftime('%H%M%S')}",
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
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            self.test_league_id = data['id']
            print(f"✅ Test league created: {self.test_league_id}")
            return True
        else:
            print(f"❌ League creation failed: {status}")
            return False

    # ==================== FIX 1: LEAGUE INVITATION SYSTEM ====================
    
    def test_league_invitation_fix(self):
        """Test Fix 1: League invitation system should work with only email in request body"""
        if not self.test_league_id:
            return self.log_test("League Invitation Fix", False, "No test league ID")
        
        print("\n🔧 Testing League Invitation Fix...")
        
        # Test 1: Send invitation with only email (should work now)
        success, status, data = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"email": self.manager_email},
            expected_status=200
        )
        
        invitation_success = success and status == 200
        
        # Test 2: Verify invitation was created
        if invitation_success:
            success2, status2, invitations = self.make_request('GET', f'leagues/{self.test_league_id}/invitations')
            invitation_created = success2 and isinstance(invitations, list) and len(invitations) > 0
        else:
            invitation_created = False
        
        # Test 3: Test duplicate prevention (should return 400)
        success3, status3, data3 = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"email": self.manager_email},
            expected_status=400
        )
        duplicate_prevented = success3 and status3 == 400
        
        overall_success = invitation_success and invitation_created and duplicate_prevented
        
        return self.log_test(
            "League Invitation Fix",
            overall_success,
            f"Invite: {status}, Created: {invitation_created}, Duplicate prevented: {status3}"
        )

    def test_invitation_model_validation(self):
        """Test that invitation endpoint only requires email field"""
        if not self.test_league_id:
            return self.log_test("Invitation Model Validation", False, "No test league ID")
        
        print("🔧 Testing Invitation Model Validation...")
        
        # Test with minimal payload (only email)
        test_email = f"model_test_{int(time.time())}@example.com"
        success, status, data = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"email": test_email},
            expected_status=200
        )
        
        minimal_payload_works = success and status == 200
        
        # Test with extra fields (should still work)
        test_email2 = f"model_test2_{int(time.time())}@example.com"
        success2, status2, data2 = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {
                "email": test_email2,
                "extra_field": "should_be_ignored"
            },
            expected_status=200
        )
        
        extra_fields_ignored = success2 and status2 == 200
        
        return self.log_test(
            "Invitation Model Validation",
            minimal_payload_works and extra_fields_ignored,
            f"Minimal: {status}, Extra fields: {status2}"
        )

    # ==================== FIX 2: AUCTION ENGINE ERROR HANDLING ====================
    
    def test_auction_engine_error_handling(self):
        """Test Fix 2: Auction engine should return proper 400 errors, not 500"""
        if not self.test_league_id:
            return self.log_test("Auction Engine Error Handling", False, "No test league ID")
        
        print("\n🔧 Testing Auction Engine Error Handling...")
        
        # Try to start auction on league that's not ready (should return 400, not 500)
        success, status, data = self.make_request(
            'POST',
            f'auction/{self.test_league_id}/start',
            expected_status=400
        )
        
        proper_error_code = success and status == 400
        
        # Check error message is clear
        error_message_clear = (
            isinstance(data, dict) and 
            'detail' in data and 
            isinstance(data['detail'], str) and
            len(data['detail']) > 0
        )
        
        # Verify it's not a 500 error
        success_500, status_500, data_500 = self.make_request(
            'POST',
            f'auction/{self.test_league_id}/start',
            expected_status=500
        )
        
        not_500_error = not success_500 or status_500 != 500
        
        return self.log_test(
            "Auction Engine Error Handling",
            proper_error_code and error_message_clear and not_500_error,
            f"Status: {status}, Clear message: {error_message_clear}, Not 500: {not_500_error}"
        )

    def test_auction_business_logic_errors(self):
        """Test that business logic errors return appropriate status codes"""
        if not self.test_league_id:
            return self.log_test("Auction Business Logic Errors", False, "No test league ID")
        
        print("🔧 Testing Auction Business Logic Errors...")
        
        # Test various auction operations that should fail with proper error codes
        test_results = []
        
        # Test 1: Start auction on non-ready league (should be 400)
        success, status, data = self.make_request('POST', f'auction/{self.test_league_id}/start')
        test_results.append(status == 400)
        
        # Test 2: Get state of non-existent auction (should be 404)
        fake_auction_id = str(uuid.uuid4())
        success2, status2, data2 = self.make_request('GET', f'auction/{fake_auction_id}/state')
        test_results.append(status2 == 404)
        
        # Test 3: Place bid on non-existent auction (should be 400 or 404)
        success3, status3, data3 = self.make_request(
            'POST',
            f'auction/{fake_auction_id}/bid',
            {"lot_id": "fake_lot", "amount": 10}
        )
        test_results.append(status3 in [400, 404])
        
        # Test 4: Pause non-existent auction (should be 400 or 404)
        success4, status4, data4 = self.make_request('POST', f'auction/{fake_auction_id}/pause')
        test_results.append(status4 in [400, 404])
        
        all_proper_errors = all(test_results)
        
        return self.log_test(
            "Auction Business Logic Errors",
            all_proper_errors,
            f"Start: {status}, State: {status2}, Bid: {status3}, Pause: {status4}"
        )

    # ==================== FIX 3: HEALTH ENDPOINT ====================
    
    def test_health_endpoint_fix(self):
        """Test Fix 3: /api/health should return detailed health information"""
        print("\n🔧 Testing Health Endpoint Fix...")
        
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Health Endpoint Fix", False, f"Health endpoint failed: {status}")
        
        # Check for detailed health information (not just {ok: true})
        required_fields = ['status', 'timestamp', 'database', 'services', 'system']
        has_required_fields = all(field in data for field in required_fields)
        
        # Check database info
        database_info = data.get('database', {})
        has_db_info = (
            'connected' in database_info and
            'collections_count' in database_info
        )
        
        # Check services info
        services_info = data.get('services', {})
        has_services_info = (
            'websocket' in services_info and
            'auth' in services_info
        )
        
        # Check system info
        system_info = data.get('system', {})
        has_system_info = (
            'cpu_percent' in system_info and
            'memory_percent' in system_info
        )
        
        # Verify it's not just {ok: true}
        not_simple_ok = not (len(data) == 1 and data.get('ok') is True)
        
        detailed_response = (
            has_required_fields and 
            has_db_info and 
            has_services_info and 
            has_system_info and 
            not_simple_ok
        )
        
        return self.log_test(
            "Health Endpoint Fix",
            detailed_response,
            f"Status: {status}, Fields: {has_required_fields}, DB: {has_db_info}, Services: {has_services_info}, System: {has_system_info}"
        )

    def test_health_endpoint_content(self):
        """Test that health endpoint returns comprehensive information"""
        print("🔧 Testing Health Endpoint Content...")
        
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Health Endpoint Content", False, f"Health endpoint failed: {status}")
        
        # Test specific content requirements
        content_checks = []
        
        # Check status field
        status_valid = data.get('status') in ['healthy', 'degraded', 'warning', 'critical', 'unhealthy']
        content_checks.append(status_valid)
        
        # Check timestamp format
        timestamp = data.get('timestamp', '')
        timestamp_valid = 'T' in timestamp and 'Z' in timestamp or '+' in timestamp
        content_checks.append(timestamp_valid)
        
        # Check database connectivity
        db_connected = data.get('database', {}).get('connected', False)
        content_checks.append(db_connected)
        
        # Check collections count is numeric
        collections_count = data.get('database', {}).get('collections_count', 0)
        collections_valid = isinstance(collections_count, int) and collections_count >= 0
        content_checks.append(collections_valid)
        
        # Check system metrics are numeric
        cpu_percent = data.get('system', {}).get('cpu_percent')
        memory_percent = data.get('system', {}).get('memory_percent')
        metrics_valid = (
            isinstance(cpu_percent, (int, float)) and 
            isinstance(memory_percent, (int, float))
        )
        content_checks.append(metrics_valid)
        
        all_content_valid = all(content_checks)
        
        return self.log_test(
            "Health Endpoint Content",
            all_content_valid,
            f"Status: {status_valid}, Timestamp: {timestamp_valid}, DB: {db_connected}, Collections: {collections_valid}, Metrics: {metrics_valid}"
        )

    # ==================== END-TO-END FLOW TEST ====================
    
    def test_end_to_end_flow(self):
        """Test complete end-to-end flow: auth → league creation → invitations → auction start"""
        print("\n🔧 Testing End-to-End Flow...")
        
        flow_steps = []
        
        # Step 1: Authentication (already done in setup)
        auth_working = self.token is not None
        flow_steps.append(auth_working)
        
        # Step 2: League creation (already done in setup)
        league_working = self.test_league_id is not None
        flow_steps.append(league_working)
        
        # Step 3: Send invitation
        if league_working:
            e2e_email = f"e2e_test_{int(time.time())}@example.com"
            success, status, data = self.make_request(
                'POST',
                f'leagues/{self.test_league_id}/invite',
                {"email": e2e_email}
            )
            invitation_working = success and status == 200
        else:
            invitation_working = False
        flow_steps.append(invitation_working)
        
        # Step 4: Try auction start (should fail with proper 400 error)
        if league_working:
            success, status, data = self.make_request(
                'POST',
                f'auction/{self.test_league_id}/start',
                expected_status=400
            )
            auction_error_proper = success and status == 400
        else:
            auction_error_proper = False
        flow_steps.append(auction_error_proper)
        
        # Step 5: Verify league status
        if league_working:
            success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/status')
            status_working = success and 'is_ready' in data
        else:
            status_working = False
        flow_steps.append(status_working)
        
        all_steps_working = all(flow_steps)
        
        return self.log_test(
            "End-to-End Flow",
            all_steps_working,
            f"Auth: {auth_working}, League: {league_working}, Invite: {invitation_working}, Auction: {auction_error_proper}, Status: {status_working}"
        )

    # ==================== MAIN TEST RUNNER ====================
    
    def run_fix_verification_tests(self):
        """Run all fix verification tests"""
        print("🔧 FIX VERIFICATION TEST SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed - cannot continue")
            return 0, 1, ["Authentication setup failed"]
        
        if not self.setup_test_league():
            print("❌ League setup failed - cannot continue")
            return 0, 1, ["League setup failed"]
        
        # Fix 1: League Invitation System
        print("\n🔧 FIX 1: LEAGUE INVITATION SYSTEM")
        self.test_league_invitation_fix()
        self.test_invitation_model_validation()
        
        # Fix 2: Auction Engine Error Handling
        print("\n🔧 FIX 2: AUCTION ENGINE ERROR HANDLING")
        self.test_auction_engine_error_handling()
        self.test_auction_business_logic_errors()
        
        # Fix 3: Health Endpoint
        print("\n🔧 FIX 3: HEALTH ENDPOINT")
        self.test_health_endpoint_fix()
        self.test_health_endpoint_content()
        
        # End-to-End Flow
        print("\n🔧 END-TO-END FLOW VERIFICATION")
        self.test_end_to_end_flow()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 FIX VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        print("\n✅ FIX STATUS:")
        fix_status = [
            ("League Invitation Fix", "League Invitation Fix" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Auction Engine Fix", "Auction Engine Error Handling" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Health Endpoint Fix", "Health Endpoint Fix" not in [t.split(':')[0] for t in self.failed_tests]),
            ("End-to-End Flow", "End-to-End Flow" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        for fix, status in fix_status:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {fix}: {'WORKING' if status else 'FAILED'}")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = FixVerificationTester()
    passed, total, failed = tester.run_fix_verification_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)