#!/usr/bin/env python3
"""
SOCKET FACTORY REFACTOR BACKEND VERIFICATION TEST
Tests backend functionality after AuctionRoom frontend socket factory refactor.

This test focuses on the specific areas mentioned in the review request:
1. Basic API Health Check - /api/health endpoint
2. Authentication Endpoints - /api/auth/test-login and /api/auth/me endpoints  
3. League Management - Test league creation and basic league operations
4. Socket.IO Connectivity - Test that /api/socket.io endpoint is accessible and working
5. Auction System - Test auction start functionality if possible

The frontend refactor involved:
- Replacing manual socket connection logic with unified createSocket() factory
- Using joinAndSync(auctionId) method from the factory
- Removing complex manual reconnection logic
- But keeping all existing auction event handlers

This test verifies that backend systems remain stable after the frontend changes.
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import time

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://livebid-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SocketFactoryRefactorTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SocketFactoryRefactorTest/1.0'
        })
        self.test_results = []
        self.test_user_id = None
        self.test_league_id = None
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def test_health_endpoint(self) -> bool:
        """
        TEST 1: Basic API Health Check
        Verify /api/health endpoint is working
        """
        print("\n🔍 TEST 1: BASIC API HEALTH CHECK")
        
        try:
            resp = self.session.get(f"{API_BASE}/health")
            if resp.status_code == 200:
                data = resp.json()
                if 'status' in data and data['status'] == 'healthy':
                    self.log_result("Health Endpoint", True, f"Status: {data['status']}")
                    return True
                else:
                    self.log_result("Health Endpoint", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("Health Endpoint", False, f"Status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Exception: {str(e)}")
            return False
            
    def test_authentication_endpoints(self) -> bool:
        """
        TEST 2: Authentication Endpoints
        Test /api/auth/test-login and /api/auth/me endpoints
        """
        print("\n🔍 TEST 2: AUTHENTICATION ENDPOINTS")
        
        try:
            # Test login endpoint
            test_email = f"socket-test-{int(time.time())}@test.com"
            login_resp = self.session.post(f"{API_BASE}/auth/test-login", json={"email": test_email})
            
            if login_resp.status_code == 200:
                login_data = login_resp.json()
                if login_data.get('ok') and login_data.get('userId'):
                    self.test_user_id = login_data['userId']
                    self.log_result("Test Login Endpoint", True, f"User ID: {self.test_user_id}")
                else:
                    self.log_result("Test Login Endpoint", False, f"Invalid response: {login_data}")
                    return False
            else:
                self.log_result("Test Login Endpoint", False, f"Status {login_resp.status_code}: {login_resp.text}")
                return False
                
            # Test /api/auth/me endpoint
            me_resp = self.session.get(f"{API_BASE}/auth/me")
            if me_resp.status_code == 200:
                me_data = me_resp.json()
                if me_data.get('id') == self.test_user_id:
                    self.log_result("Auth Me Endpoint", True, f"Verified user: {me_data.get('email')}")
                    return True
                else:
                    self.log_result("Auth Me Endpoint", False, f"User ID mismatch: {me_data}")
                    return False
            else:
                self.log_result("Auth Me Endpoint", False, f"Status {me_resp.status_code}: {me_resp.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication Endpoints", False, f"Exception: {str(e)}")
            return False
            
    def test_league_management(self) -> bool:
        """
        TEST 3: League Management
        Test league creation and basic league operations
        """
        print("\n🔍 TEST 3: LEAGUE MANAGEMENT")
        
        try:
            # Create league
            league_data = {
                "name": f"Socket Refactor Test League {datetime.now().strftime('%H%M%S')}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            create_resp = self.session.post(f"{API_BASE}/leagues", json=league_data)
            if create_resp.status_code == 201:
                create_data = create_resp.json()
                self.test_league_id = create_data.get('leagueId')
                if self.test_league_id:
                    self.log_result("League Creation", True, f"League ID: {self.test_league_id}")
                else:
                    self.log_result("League Creation", False, f"No league ID in response: {create_data}")
                    return False
            else:
                self.log_result("League Creation", False, f"Status {create_resp.status_code}: {create_resp.text}")
                return False
                
            # Get league details
            get_resp = self.session.get(f"{API_BASE}/leagues/{self.test_league_id}")
            if get_resp.status_code == 200:
                league_details = get_resp.json()
                if league_details.get('id') == self.test_league_id:
                    self.log_result("League Retrieval", True, f"Name: {league_details.get('name')}")
                else:
                    self.log_result("League Retrieval", False, f"League ID mismatch: {league_details}")
                    return False
            else:
                self.log_result("League Retrieval", False, f"Status {get_resp.status_code}: {get_resp.text}")
                return False
                
            # Get league status
            status_resp = self.session.get(f"{API_BASE}/leagues/{self.test_league_id}/status")
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                self.log_result("League Status", True, f"Members: {status_data.get('member_count', 0)}, Ready: {status_data.get('is_ready', False)}")
                return True
            else:
                self.log_result("League Status", False, f"Status {status_resp.status_code}: {status_resp.text}")
                return False
                
        except Exception as e:
            self.log_result("League Management", False, f"Exception: {str(e)}")
            return False
            
    def test_socket_io_connectivity(self) -> bool:
        """
        TEST 4: Socket.IO Connectivity
        Test that /api/socket.io endpoint is accessible and working
        """
        print("\n🔍 TEST 4: SOCKET.IO CONNECTIVITY")
        
        try:
            # Test Socket.IO handshake endpoint
            socket_url = f"{API_BASE}/socket.io/?EIO=4&transport=polling"
            socket_resp = self.session.get(socket_url)
            
            if socket_resp.status_code == 200:
                response_text = socket_resp.text
                # Check if it's a proper Engine.IO response (starts with a number and contains JSON)
                if response_text.startswith('0{') and 'sid' in response_text:
                    self.log_result("Socket.IO Handshake", True, "Engine.IO handshake successful")
                    
                    # Parse the JSON part to verify structure
                    try:
                        json_part = response_text[1:]  # Remove the '0' prefix
                        handshake_data = json.loads(json_part)
                        if 'sid' in handshake_data and 'upgrades' in handshake_data:
                            self.log_result("Socket.IO Response Format", True, f"SID: {handshake_data['sid'][:8]}...")
                            return True
                        else:
                            self.log_result("Socket.IO Response Format", False, f"Missing required fields: {handshake_data}")
                            return False
                    except json.JSONDecodeError as e:
                        self.log_result("Socket.IO Response Format", False, f"JSON parse error: {str(e)}")
                        return False
                else:
                    self.log_result("Socket.IO Handshake", False, f"Unexpected response format: {response_text[:100]}")
                    return False
            else:
                self.log_result("Socket.IO Handshake", False, f"Status {socket_resp.status_code}: {socket_resp.text}")
                return False
                
        except Exception as e:
            self.log_result("Socket.IO Connectivity", False, f"Exception: {str(e)}")
            return False
            
    def test_auction_system(self) -> bool:
        """
        TEST 5: Auction System
        Test auction start functionality if possible
        """
        print("\n🔍 TEST 5: AUCTION SYSTEM")
        
        try:
            if not self.test_league_id:
                self.log_result("Auction System Setup", False, "No test league available")
                return False
                
            # Try to start auction (may fail if league not ready, but endpoint should be accessible)
            start_resp = self.session.post(f"{API_BASE}/auction/{self.test_league_id}/start")
            
            if start_resp.status_code == 200:
                start_data = start_resp.json()
                if start_data.get('success'):
                    auction_id = start_data.get('auction_id', self.test_league_id)
                    self.log_result("Auction Start", True, f"Auction ID: {auction_id}")
                    
                    # Try to get auction state
                    state_resp = self.session.get(f"{API_BASE}/auction/{auction_id}/state")
                    if state_resp.status_code == 200:
                        state_data = state_resp.json()
                        self.log_result("Auction State", True, f"Status: {state_data.get('status', 'unknown')}")
                        return True
                    else:
                        self.log_result("Auction State", False, f"Status {state_resp.status_code}: {state_resp.text}")
                        return False
                else:
                    self.log_result("Auction Start", False, f"Start failed: {start_data}")
                    return False
            elif start_resp.status_code == 400:
                # Expected if league not ready - check the error message
                error_data = start_resp.json() if start_resp.headers.get('content-type', '').startswith('application/json') else {}
                if 'not ready' in str(error_data).lower() or 'minimum' in str(error_data).lower():
                    self.log_result("Auction Start", True, "Correctly rejected unready league")
                    return True
                else:
                    self.log_result("Auction Start", False, f"Unexpected 400 error: {error_data}")
                    return False
            else:
                self.log_result("Auction Start", False, f"Status {start_resp.status_code}: {start_resp.text}")
                return False
                
        except Exception as e:
            self.log_result("Auction System", False, f"Exception: {str(e)}")
            return False
            
    def run_socket_factory_verification(self):
        """Run the complete socket factory refactor verification test"""
        print("🔍 SOCKET FACTORY REFACTOR BACKEND VERIFICATION")
        print("=" * 60)
        print("Testing backend stability after AuctionRoom frontend socket factory refactor")
        print("=" * 60)
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_health_endpoint())
        test_results.append(self.test_authentication_endpoints())
        test_results.append(self.test_league_management())
        test_results.append(self.test_socket_io_connectivity())
        test_results.append(self.test_auction_system())
        
        # Summary
        print("\n" + "=" * 60)
        print("🔍 SOCKET FACTORY REFACTOR VERIFICATION RESULTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Core functionality assessment
        core_tests_passed = sum(test_results)
        
        print(f"\nCORE BACKEND SYSTEMS: {core_tests_passed}/5 working")
        
        if core_tests_passed == 5:
            print("✅ ALL BACKEND SYSTEMS STABLE - Socket factory refactor did not break backend functionality!")
        elif core_tests_passed >= 4:
            print("⚠️ MOSTLY STABLE - Minor issues detected but core functionality intact")
        else:
            print("❌ BACKEND ISSUES DETECTED - Socket factory refactor may have affected backend systems")
            
        # Detailed failure analysis
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED - Backend is fully functional after frontend refactor")
            
        return core_tests_passed >= 4

def main():
    """Main test execution"""
    test_suite = SocketFactoryRefactorTest()
    success = test_suite.run_socket_factory_verification()
    
    if success:
        print("\n🎉 VERIFICATION COMPLETE: Backend systems are stable after socket factory refactor")
        sys.exit(0)
    else:
        print("\n⚠️ VERIFICATION ISSUES: Some backend systems may need attention")
        sys.exit(1)

if __name__ == "__main__":
    main()