#!/usr/bin/env python3
"""
Atomic Post-Create Flow Test
Tests the complete atomic post-create flow that was failing due to authentication issues.
This simulates the exact flow that was causing 403 errors in the lobby.
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class AtomicFlowTester:
    def __init__(self, base_url="https://testid-enforcer.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()  # Use session to maintain cookies
        self.test_email = f"atomic_test_{int(time.time())}@example.com"
        self.test_league_id = None
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
        """Make HTTP request using session to maintain cookies"""
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

    def test_atomic_post_create_flow(self):
        """Test the complete atomic post-create flow that was failing"""
        print(f"\n🚀 ATOMIC POST-CREATE FLOW TEST")
        print(f"Testing email: {self.test_email}")
        print("=" * 50)
        
        # Step 1: Test Login (simulates user authentication)
        print("Step 1: Test Login")
        success, status, data = self.make_request(
            'POST', 
            'auth/test-login', 
            {"email": self.test_email},
            expected_status=200
        )
        
        if not success:
            return self.log_test("Atomic Flow - Test Login", False, f"Status: {status}, Response: {data}")
        
        print(f"   ✅ Test login successful: {data.get('email')}")
        
        # Step 2: Verify session immediately after login
        print("Step 2: Session Verification")
        success, status, data = self.make_request('GET', 'auth/me', expected_status=200)
        
        if not success:
            return self.log_test("Atomic Flow - Session Verification", False, f"Status: {status}, Response: {data}")
        
        print(f"   ✅ Session verified: {data.get('email')}")
        
        # Step 3: Create League (the atomic operation)
        print("Step 3: League Creation (Atomic Operation)")
        league_data = {
            "name": f"Atomic Flow Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 3,
                "bid_timer_seconds": 60,
                "anti_snipe_seconds": 30,
                "league_size": {
                    "min": 2,
                    "max": 8
                }
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data, expected_status=201)
        
        if not success:
            return self.log_test("Atomic Flow - League Creation", False, f"Status: {status}, Response: {data}")
        
        self.test_league_id = data.get('leagueId')
        print(f"   ✅ League created: {self.test_league_id}")
        
        # Step 4: Immediate League Access (this was failing with 403)
        print("Step 4: Immediate League Access")
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}', expected_status=200)
        
        if not success:
            return self.log_test("Atomic Flow - League Access", False, f"Status: {status}, Response: {data}")
        
        print(f"   ✅ League accessed: {data.get('name')}")
        
        # Step 5: League Members (commissioner should be there)
        print("Step 5: League Members Check")
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/members', expected_status=200)
        
        if not success:
            return self.log_test("Atomic Flow - League Members", False, f"Status: {status}, Response: {data}")
        
        commissioner_found = any(member.get('role') == 'commissioner' for member in data)
        print(f"   ✅ League members retrieved: {len(data)} members, Commissioner: {commissioner_found}")
        
        # Step 6: League Status (readiness check)
        print("Step 6: League Status Check")
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/status', expected_status=200)
        
        if not success:
            return self.log_test("Atomic Flow - League Status", False, f"Status: {status}, Response: {data}")
        
        print(f"   ✅ League status: {data.get('status')}, Members: {data.get('member_count')}")
        
        # Step 7: Test League Readiness Endpoint (TEST_MODE specific)
        print("Step 7: League Readiness Check (TEST_MODE)")
        success, status, data = self.make_request('GET', f'test/league/{self.test_league_id}/ready', expected_status=200)
        
        if not success:
            return self.log_test("Atomic Flow - League Readiness", False, f"Status: {status}, Response: {data}")
        
        print(f"   ✅ League readiness: {data.get('ready')}")
        
        # Step 8: Multiple consecutive API calls (stress test session persistence)
        print("Step 8: Session Persistence Stress Test")
        consecutive_calls = []
        
        for i in range(5):
            success, status, data = self.make_request('GET', 'auth/me', expected_status=200)
            consecutive_calls.append(success)
            if success:
                print(f"   ✅ Call {i+1}: Session valid")
            else:
                print(f"   ❌ Call {i+1}: Session failed - {status}")
        
        all_calls_successful = all(consecutive_calls)
        
        return self.log_test(
            "Atomic Post-Create Flow",
            all_calls_successful,
            f"All 8 steps completed successfully, Session persistence: {sum(consecutive_calls)}/5"
        )

    def test_lobby_simulation(self):
        """Simulate the lobby loading that was failing with 403 errors"""
        if not self.test_league_id:
            return self.log_test("Lobby Simulation", False, "No test league ID")
        
        print(f"\n🏟️ LOBBY LOADING SIMULATION")
        print("=" * 30)
        
        # These are the API calls that would happen when loading the lobby
        lobby_calls = [
            ('GET', f'leagues/{self.test_league_id}', 'League Details'),
            ('GET', f'leagues/{self.test_league_id}/members', 'League Members'),
            ('GET', f'leagues/{self.test_league_id}/status', 'League Status'),
            ('GET', 'auth/me', 'User Authentication'),
            ('GET', f'test/league/{self.test_league_id}/ready', 'League Readiness')
        ]
        
        results = []
        for method, endpoint, description in lobby_calls:
            success, status, data = self.make_request(method, endpoint, expected_status=200)
            results.append(success)
            
            if success:
                print(f"   ✅ {description}: Success")
            else:
                print(f"   ❌ {description}: Failed ({status})")
        
        all_lobby_calls_work = all(results)
        
        return self.log_test(
            "Lobby Loading Simulation",
            all_lobby_calls_work,
            f"Lobby API calls: {sum(results)}/{len(results)} successful"
        )

    def run_atomic_flow_tests(self):
        """Run all atomic flow tests"""
        print("🚀 ATOMIC POST-CREATE FLOW TEST SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print(f"Test Email: {self.test_email}")
        print("=" * 60)
        
        # Environment check
        print("\n🔧 Environment Configuration Check")
        success, status, data = self.make_request('GET', 'health')
        if success:
            print(f"✅ Backend health check passed")
            print(f"✅ TEST_MODE: {os.getenv('TEST_MODE', 'Not set')}")
            print(f"✅ ALLOW_TEST_LOGIN: {os.getenv('ALLOW_TEST_LOGIN', 'Not set')}")
        else:
            print(f"❌ Backend health check failed: {status}")
            return False
        
        # Run the atomic flow test
        if not self.test_atomic_post_create_flow():
            print("❌ Atomic post-create flow failed")
            return False
        
        # Run lobby simulation
        if not self.test_lobby_simulation():
            print("❌ Lobby simulation failed")
            return False
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 ATOMIC FLOW TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        # Critical assessment
        atomic_flow_works = "Atomic Post-Create Flow" not in [t.split(':')[0] for t in self.failed_tests]
        lobby_works = "Lobby Loading Simulation" not in [t.split(':')[0] for t in self.failed_tests]
        
        print(f"\n🎯 ATOMIC POST-CREATE FLOW: {'✅ WORKING' if atomic_flow_works else '❌ FAILED'}")
        print(f"🎯 LOBBY LOADING: {'✅ WORKING' if lobby_works else '❌ FAILED'}")
        
        if atomic_flow_works and lobby_works:
            print("\n🎉 SUCCESS: Authentication session persistence fix is working!")
            print("✅ Test-login creates persistent session cookies")
            print("✅ League creation works with authenticated session")
            print("✅ Immediate league access works (no 403 errors)")
            print("✅ Lobby loading should work without authentication issues")
            print("✅ The atomic post-create flow is now functional")
        else:
            print("\n❌ FAILURE: Authentication session persistence still has issues")
            print("❌ The atomic post-create flow will still fail")
            print("❌ Lobby loading will continue to show 403 errors")
        
        return atomic_flow_works and lobby_works

if __name__ == "__main__":
    tester = AtomicFlowTester()
    success = tester.run_atomic_flow_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)