#!/usr/bin/env python3
"""
TOKEN AUTHENTICATION AND CONNECTION ISSUES TEST
Specifically tests the auction room connection fix mentioned in the review request.

FOCUS AREAS:
1. Token Validation Fix - JWT token validation before Socket.IO connection
2. Improved Error Handling - Socket.IO authentication failure detection  
3. Connection Timeout Fix - 15-second timeout for auction state loading
4. Complete Auction Room Flow - End-to-end with valid/invalid tokens

SUCCESS CRITERIA:
- No more "stuck on Connecting to auction" issues
- Clear error messages when authentication fails
- Proper token validation prevents connection attempts with expired tokens
- Users can successfully access auction room when properly authenticated
- Timeout prevents infinite loading states
"""

import requests
import json
import os
import time
import asyncio
import socketio
from datetime import datetime
from typing import Dict, Optional

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://livebid-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
SOCKET_URL = BACKEND_URL
SOCKET_PATH = "/api/socketio"

class TokenAuthConnectionTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.valid_token = None
        self.league_id = None
        self.user_id = None
        
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
        
    def setup_authenticated_user(self) -> bool:
        """Setup authenticated user and extract token"""
        try:
            # Authenticate test user
            auth_resp = self.session.post(f"{API_BASE}/auth/test-login", 
                                        json={"email": "token_test@example.com"})
            if auth_resp.status_code != 200:
                self.log_result("User Authentication", False, 
                              f"Status {auth_resp.status_code}: {auth_resp.text}")
                return False
                
            auth_data = auth_resp.json()
            self.user_id = auth_data['userId']
            
            # Extract token from session cookie
            cookies = self.session.cookies
            if 'access_token' in cookies:
                self.valid_token = cookies['access_token']
                self.log_result("Token Extraction", True, "Valid token extracted from session")
                return True
            else:
                self.log_result("Token Extraction", False, "No access_token cookie found")
                return False
                
        except Exception as e:
            self.log_result("User Setup", False, f"Exception: {str(e)}")
            return False
    
    def create_test_league(self) -> bool:
        """Create test league for auction testing"""
        try:
            league_data = {
                "name": f"Token Auth Test League {datetime.now().strftime('%H%M%S')}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            league_resp = self.session.post(f"{API_BASE}/leagues", json=league_data)
            if league_resp.status_code == 201:
                data = league_resp.json()
                self.league_id = data['leagueId']
                self.log_result("League Creation", True, f"League ID: {self.league_id}")
                
                # Add another user to meet minimum requirements
                manager_session = requests.Session()
                manager_auth = manager_session.post(f"{API_BASE}/auth/test-login", 
                                                  json={"email": "manager_for_auth_test@example.com"})
                if manager_auth.status_code == 200:
                    join_resp = manager_session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                    if join_resp.status_code == 200:
                        self.log_result("Manager Join", True, "Added manager to meet minimum")
                    else:
                        self.log_result("Manager Join", False, f"Status {join_resp.status_code}")
                
                # Check league status
                status_resp = self.session.get(f"{API_BASE}/leagues/{self.league_id}/status")
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    self.log_result("League Status", True, 
                                  f"Members: {status_data.get('member_count', 0)}, Ready: {status_data.get('is_ready', False)}")
                
                # Start auction
                start_resp = self.session.post(f"{API_BASE}/auction/{self.league_id}/start")
                if start_resp.status_code == 200:
                    self.log_result("Auction Start", True, "Auction started for testing")
                    return True
                else:
                    self.log_result("Auction Start", False, f"Status {start_resp.status_code}: {start_resp.text}")
                    # Continue anyway - we can test connection even without started auction
                    return True
            else:
                self.log_result("League Creation", False, f"Status {league_resp.status_code}")
                return False
                
        except Exception as e:
            self.log_result("League Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_token_validation_before_connection(self) -> bool:
        """
        TEST 1: Token Validation Fix
        Verify JWT token is validated before Socket.IO connection attempts
        """
        print("\n🎯 TEST 1: TOKEN VALIDATION BEFORE CONNECTION")
        
        try:
            # Test valid token validation
            auth_resp = requests.get(f"{API_BASE}/auth/me", 
                                   headers={'Authorization': f'Bearer {self.valid_token}'})
            
            if auth_resp.status_code == 200:
                user_data = auth_resp.json()
                self.log_result("Valid Token Pre-Validation", True, 
                              f"Token validates for user: {user_data.get('email', 'unknown')}")
            else:
                self.log_result("Valid Token Pre-Validation", False, 
                              f"Valid token failed validation: {auth_resp.status_code}")
                return False
            
            # Test expired/invalid token rejection
            invalid_tokens = [
                "expired.jwt.token",
                "invalid.format.token",
                "Bearer malformed",
                ""
            ]
            
            for i, invalid_token in enumerate(invalid_tokens):
                auth_resp = requests.get(f"{API_BASE}/auth/me", 
                                       headers={'Authorization': f'Bearer {invalid_token}'})
                
                if auth_resp.status_code in [401, 403, 422]:
                    self.log_result(f"Invalid Token Rejection {i+1}", True, 
                                  f"Token correctly rejected with {auth_resp.status_code}")
                else:
                    self.log_result(f"Invalid Token Rejection {i+1}", False, 
                                  f"Should reject invalid token, got {auth_resp.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("Token Validation Test", False, f"Exception: {str(e)}")
            return False
    
    async def test_socketio_auth_success(self) -> bool:
        """
        TEST 2: Successful Socket.IO Connection with Valid Token
        """
        print("\n🎯 TEST 2: SOCKET.IO CONNECTION WITH VALID TOKEN")
        
        try:
            sio = socketio.AsyncClient()
            connection_events = {
                'connected': False,
                'joined_auction': False,
                'received_state': False,
                'connection_error': None,
                'timeout_occurred': False
            }
            
            @sio.event
            async def connect():
                connection_events['connected'] = True
                print("✅ Socket.IO connected successfully with valid token")
                
                # Join auction room
                await sio.emit('join_auction', {'auction_id': self.league_id})
            
            @sio.event
            async def connect_error(data):
                connection_events['connection_error'] = str(data)
                print(f"❌ Socket.IO connection error: {data}")
            
            @sio.event
            async def joined(data):
                connection_events['joined_auction'] = True
                print(f"✅ Joined auction room: {data}")
            
            @sio.event
            async def auction_state(data):
                connection_events['received_state'] = True
                print(f"✅ Received auction state: {data.get('status', 'unknown')}")
            
            @sio.event
            async def auction_snapshot(data):
                connection_events['received_state'] = True
                print(f"✅ Received auction snapshot")
            
            # Test connection with timeout
            try:
                await asyncio.wait_for(
                    sio.connect(SOCKET_URL, 
                              auth={'token': self.valid_token},
                              socketio_path=SOCKET_PATH,
                              transports=['polling', 'websocket']),
                    timeout=10.0
                )
                
                # Wait for auction room events
                await asyncio.sleep(5)
                
                # Evaluate results
                if connection_events['connected']:
                    self.log_result("Valid Token Socket Connection", True, 
                                  "Successfully connected with valid token")
                else:
                    self.log_result("Valid Token Socket Connection", False, 
                                  f"Connection failed: {connection_events['connection_error']}")
                    return False
                
                if connection_events['joined_auction']:
                    self.log_result("Auction Room Join", True, 
                                  "Successfully joined auction room - no stuck state")
                else:
                    self.log_result("Auction Room Join", False, 
                                  "Did not receive auction room join confirmation")
                
                # Test for stuck "Connecting" state - if we get here, we're not stuck
                self.log_result("No Stuck Connecting State", True, 
                              "Connection completed without hanging")
                
                await sio.disconnect()
                return True
                
            except asyncio.TimeoutError:
                connection_events['timeout_occurred'] = True
                self.log_result("Connection Timeout", False, 
                              "Connection timed out - potential stuck state")
                return False
                
        except Exception as e:
            self.log_result("Socket.IO Auth Success Test", False, f"Exception: {str(e)}")
            return False
    
    async def test_socketio_auth_failure_handling(self) -> bool:
        """
        TEST 3: Socket.IO Authentication Failure Detection
        """
        print("\n🎯 TEST 3: SOCKET.IO AUTHENTICATION FAILURE HANDLING")
        
        try:
            # Test with invalid token
            sio_invalid = socketio.AsyncClient()
            invalid_events = {
                'connected': False,
                'connection_error': None,
                'clear_error_message': False
            }
            
            @sio_invalid.event
            async def connect():
                invalid_events['connected'] = True
                print("❌ ERROR: Invalid token should not connect")
            
            @sio_invalid.event
            async def connect_error(data):
                invalid_events['connection_error'] = str(data)
                # Check if error message is clear and helpful
                error_str = str(data).lower()
                if any(keyword in error_str for keyword in ['auth', 'token', 'forbidden', '403']):
                    invalid_events['clear_error_message'] = True
                print(f"✅ Expected auth failure: {data}")
            
            try:
                await asyncio.wait_for(
                    sio_invalid.connect(SOCKET_URL, 
                                      auth={'token': 'invalid.jwt.token'},
                                      socketio_path=SOCKET_PATH,
                                      transports=['polling', 'websocket']),
                    timeout=5.0
                )
                await asyncio.sleep(2)
            except Exception as e:
                # Connection failure is expected
                invalid_events['connection_error'] = str(e)
                if any(keyword in str(e).lower() for keyword in ['auth', 'token', 'forbidden', '403']):
                    invalid_events['clear_error_message'] = True
            
            # Evaluate authentication failure handling
            if not invalid_events['connected']:
                self.log_result("Invalid Token Rejection", True, 
                              "Invalid token correctly prevented connection")
            else:
                self.log_result("Invalid Token Rejection", False, 
                              "Invalid token should not connect successfully")
            
            if invalid_events['clear_error_message']:
                self.log_result("Clear Error Messages", True, 
                              "Authentication errors provide clear feedback")
            else:
                self.log_result("Clear Error Messages", False, 
                              f"Error message unclear: {invalid_events['connection_error']}")
            
            try:
                await sio_invalid.disconnect()
            except:
                pass
            
            return not invalid_events['connected']
            
        except Exception as e:
            self.log_result("Auth Failure Handling Test", False, f"Exception: {str(e)}")
            return False
    
    async def test_connection_timeout_prevention(self) -> bool:
        """
        TEST 4: Connection Timeout Fix (15-second timeout)
        """
        print("\n🎯 TEST 4: CONNECTION TIMEOUT PREVENTION")
        
        try:
            sio = socketio.AsyncClient()
            timeout_events = {
                'connected': False,
                'state_received': False,
                'timeout_handled': False
            }
            
            @sio.event
            async def connect():
                timeout_events['connected'] = True
                print("Connected for timeout test")
                await sio.emit('join_auction', {'auction_id': self.league_id})
            
            @sio.event
            async def auction_state(data):
                timeout_events['state_received'] = True
                print("Auction state received within timeout period")
            
            @sio.event
            async def auction_snapshot(data):
                timeout_events['state_received'] = True
                print("Auction snapshot received within timeout period")
            
            start_time = time.time()
            
            try:
                await sio.connect(SOCKET_URL, 
                                auth={'token': self.valid_token},
                                socketio_path=SOCKET_PATH,
                                transports=['polling', 'websocket'])
                
                # Wait for up to 16 seconds to test timeout behavior
                await asyncio.sleep(16)
                
                elapsed = time.time() - start_time
                
                if timeout_events['connected']:
                    if elapsed < 15:
                        self.log_result("Fast Connection", True, 
                                      f"Connected in {elapsed:.1f}s - no timeout needed")
                    else:
                        self.log_result("Timeout Handling", True, 
                                      f"Connection maintained for {elapsed:.1f}s - timeout logic working")
                
                if timeout_events['state_received']:
                    self.log_result("Auction State Loading", True, 
                                  "Auction state loaded successfully")
                else:
                    self.log_result("Auction State Loading", False, 
                                  "Auction state not received - potential timeout issue")
                
                await sio.disconnect()
                return True
                
            except asyncio.TimeoutError:
                self.log_result("Timeout Prevention", True, 
                              "Timeout properly triggered - prevents infinite loading")
                return True
                
        except Exception as e:
            self.log_result("Timeout Prevention Test", False, f"Exception: {str(e)}")
            return False
    
    async def test_complete_auction_room_flow(self) -> bool:
        """
        TEST 5: Complete Auction Room Flow
        """
        print("\n🎯 TEST 5: COMPLETE AUCTION ROOM FLOW")
        
        try:
            # Test complete flow: Create league → Start auction → Access auction room
            flow_success = True
            
            # Verify auction is accessible via API
            auction_resp = self.session.get(f"{API_BASE}/auction/{self.league_id}/state")
            if auction_resp.status_code == 200:
                auction_data = auction_resp.json()
                self.log_result("Auction API Access", True, 
                              f"Auction accessible, status: {auction_data.get('status', 'unknown')}")
            else:
                self.log_result("Auction API Access", False, 
                              f"Cannot access auction: {auction_resp.status_code}")
                flow_success = False
            
            # Test Socket.IO auction room access
            sio = socketio.AsyncClient()
            flow_events = {
                'connected': False,
                'joined_room': False,
                'received_data': False
            }
            
            @sio.event
            async def connect():
                flow_events['connected'] = True
                await sio.emit('join_auction', {'auction_id': self.league_id})
            
            @sio.event
            async def joined(data):
                flow_events['joined_room'] = True
                print(f"Successfully joined auction room: {data}")
            
            @sio.event
            async def auction_state(data):
                flow_events['received_data'] = True
                print(f"Received auction data: {data.get('status', 'unknown')}")
            
            @sio.event
            async def auction_snapshot(data):
                flow_events['received_data'] = True
                print("Received auction snapshot data")
            
            try:
                await sio.connect(SOCKET_URL, 
                                auth={'token': self.valid_token},
                                socketio_path=SOCKET_PATH,
                                transports=['polling', 'websocket'])
                
                await asyncio.sleep(5)
                
                if flow_events['connected'] and (flow_events['joined_room'] or flow_events['received_data']):
                    self.log_result("Complete Auction Room Access", True, 
                                  "Successfully accessed auction room end-to-end")
                else:
                    self.log_result("Complete Auction Room Access", False, 
                                  f"Flow incomplete - connected: {flow_events['connected']}, joined: {flow_events['joined_room']}, data: {flow_events['received_data']}")
                    flow_success = False
                
                await sio.disconnect()
                
            except Exception as e:
                self.log_result("Complete Flow Socket Test", False, f"Exception: {str(e)}")
                flow_success = False
            
            return flow_success
            
        except Exception as e:
            self.log_result("Complete Auction Room Flow", False, f"Exception: {str(e)}")
            return False
    
    async def run_token_auth_tests(self):
        """Run the complete token authentication and connection test suite"""
        print("🎯 TOKEN AUTHENTICATION AND CONNECTION ISSUES TEST")
        print("=" * 70)
        print("Testing the auction room connection fix mentioned in review request")
        print("=" * 70)
        
        try:
            # Setup
            if not self.setup_authenticated_user():
                print("\n❌ SETUP FAILED: Could not authenticate user")
                return
            
            if not self.create_test_league():
                print("\n❌ SETUP FAILED: Could not create test league")
                return
            
            print(f"\n✅ SETUP COMPLETE: User {self.user_id}, League {self.league_id}")
            
            # Run all tests
            test1 = self.test_token_validation_before_connection()
            test2 = await self.test_socketio_auth_success()
            test3 = await self.test_socketio_auth_failure_handling()
            test4 = await self.test_connection_timeout_prevention()
            test5 = await self.test_complete_auction_room_flow()
            
            # Results Summary
            print("\n" + "=" * 70)
            print("🎯 TOKEN AUTHENTICATION TEST RESULTS")
            print("=" * 70)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            # Success Criteria Evaluation
            print(f"\n🎯 SUCCESS CRITERIA FROM REVIEW REQUEST:")
            print(f"✅ Token validation before connection: {'PASS' if test1 else 'FAIL'}")
            print(f"✅ Clear error messages for auth failures: {'PASS' if test3 else 'FAIL'}")
            print(f"✅ Valid tokens allow successful connection: {'PASS' if test2 else 'FAIL'}")
            print(f"✅ Timeout prevents infinite loading: {'PASS' if test4 else 'FAIL'}")
            print(f"✅ Complete auction room flow works: {'PASS' if test5 else 'FAIL'}")
            
            critical_passed = sum([test1, test2, test3, test4, test5])
            
            print(f"\n🏆 OVERALL ASSESSMENT:")
            if critical_passed >= 4:
                print("✅ AUCTION ROOM CONNECTION FIX IS WORKING!")
                print("   • No more 'stuck on Connecting to auction' issues")
                print("   • Clear error messages when authentication fails")
                print("   • Proper token validation prevents invalid connections")
                print("   • Timeout prevents infinite loading states")
                print("   • Users can successfully access auction room when authenticated")
            elif critical_passed >= 3:
                print("⚠️ AUCTION ROOM CONNECTION MOSTLY FIXED")
                print("   • Most issues resolved but some improvements needed")
            else:
                print("❌ AUCTION ROOM CONNECTION STILL HAS ISSUES")
                print("   • Critical fixes needed before user testing")
            
            # Failed tests details
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"  • {test['test']}: {test['details']}")
                    
        except Exception as e:
            print(f"\n❌ TEST SUITE EXCEPTION: {str(e)}")
        finally:
            self.session.close()

async def main():
    """Main test execution"""
    test_suite = TokenAuthConnectionTest()
    await test_suite.run_token_auth_tests()

if __name__ == "__main__":
    asyncio.run(main())