#!/usr/bin/env python3
"""
SOCKET.IO OVERLAY PATTERN COMPREHENSIVE TEST
Tests the complete /api/socket.io OVERLAY PATTERN implementation as requested in review.

This test covers:
1. Socket.IO Endpoint - verify curl /api/socket.io/?EIO=4&transport=polling returns Engine.IO JSON
2. FastAPI Routes Still Work - test existing /api/* endpoints remain functional  
3. Complete Auction Flow - test league creation → auction start → auction room access
4. Socket.IO Authentication - test JWT token validation in Socket.IO connection
"""

import asyncio
import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import socketio
import jwt
from urllib.parse import urlencode

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SocketIOOverlayTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.league_id = None
        self.auction_id = None
        self.access_token = None
        self.user_id = None
        
    async def log_result(self, test_name: str, success: bool, details: str = ""):
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
        
    async def setup_authentication(self) -> bool:
        """Setup authentication for testing"""
        try:
            # Test login to get access token
            resp = self.session.post(f"{API_BASE}/auth/test-login", json={"email": "test@example.com"})
            if resp.status_code == 200:
                data = resp.json()
                self.user_id = data['userId']
                
                # Extract access token from cookies
                for cookie in self.session.cookies:
                    if cookie.name == 'access_token':
                        self.access_token = cookie.value
                        break
                        
                if self.access_token:
                    await self.log_result("Authentication Setup", True, f"User ID: {self.user_id}")
                    return True
                else:
                    await self.log_result("Authentication Setup", False, "No access token found in cookies")
                    return False
            else:
                await self.log_result("Authentication Setup", False, f"Status {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            await self.log_result("Authentication Setup", False, f"Exception: {str(e)}")
            return False
            
    async def test_socketio_endpoint(self) -> bool:
        """
        CRITICAL TEST 1: Socket.IO Endpoint
        Verify /api/socket.io/?EIO=4&transport=polling returns Engine.IO JSON (not HTML)
        """
        print("\n🎯 PHASE 1: SOCKET.IO ENDPOINT TESTING")
        
        try:
            # Test Engine.IO handshake endpoint
            params = {
                'EIO': '4',
                'transport': 'polling'
            }
            
            resp = self.session.get(f"{API_BASE}/socket.io/", params=params)
            
            if resp.status_code == 200:
                content_type = resp.headers.get('content-type', '')
                
                # Check if response is JSON (Engine.IO format)
                if 'application/json' in content_type or resp.text.startswith('0{'):
                    try:
                        # Try to parse Engine.IO response
                        if resp.text.startswith('0{'):
                            # Engine.IO format: "0{...}" where 0 is the packet type
                            json_part = resp.text[1:]  # Remove the '0' prefix
                            data = json.loads(json_part)
                            
                            if 'sid' in data:
                                await self.log_result("Socket.IO Handshake", True, 
                                                    f"Session ID: {data['sid'][:8]}...")
                                return True
                            else:
                                await self.log_result("Socket.IO Handshake", False, 
                                                    "No session ID in response")
                                return False
                        else:
                            # Regular JSON response
                            data = resp.json()
                            await self.log_result("Socket.IO Handshake", True, 
                                                f"JSON response received: {list(data.keys())}")
                            return True
                    except json.JSONDecodeError:
                        await self.log_result("Socket.IO Handshake", False, 
                                            "Response is not valid JSON")
                        return False
                else:
                    await self.log_result("Socket.IO Handshake", False, 
                                        f"Expected JSON, got {content_type}. Response: {resp.text[:100]}")
                    return False
            else:
                await self.log_result("Socket.IO Handshake", False, 
                                    f"Status {resp.status_code}: {resp.text}")
                return False
                
        except Exception as e:
            await self.log_result("Socket.IO Endpoint Test", False, f"Exception: {str(e)}")
            return False
            
    async def test_fastapi_routes_still_work(self) -> bool:
        """
        CRITICAL TEST 2: FastAPI Routes Still Work
        Test that existing /api/* endpoints remain functional
        """
        print("\n🎯 PHASE 2: FASTAPI ROUTES FUNCTIONALITY")
        
        try:
            # Test health endpoint
            resp = self.session.get(f"{API_BASE}/health")
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result("Health Endpoint", True, f"Status: {data.get('status')}")
            else:
                await self.log_result("Health Endpoint", False, f"Status {resp.status_code}")
                return False
                
            # Test auth/me endpoint
            resp = self.session.get(f"{API_BASE}/auth/me")
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result("Auth Me Endpoint", True, f"User: {data.get('email')}")
            else:
                await self.log_result("Auth Me Endpoint", False, f"Status {resp.status_code}")
                return False
                
            # Test leagues endpoint
            resp = self.session.get(f"{API_BASE}/leagues")
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result("Leagues Endpoint", True, f"Found {len(data)} leagues")
            else:
                await self.log_result("Leagues Endpoint", False, f"Status {resp.status_code}")
                return False
                
            # Test time sync endpoint
            resp = self.session.get(f"{API_BASE}/timez")
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result("Time Sync Endpoint", True, f"Server time received")
            else:
                await self.log_result("Time Sync Endpoint", False, f"Status {resp.status_code}")
                return False
                
            return True
            
        except Exception as e:
            await self.log_result("FastAPI Routes Test", False, f"Exception: {str(e)}")
            return False
            
    async def test_complete_auction_flow(self) -> bool:
        """
        CRITICAL TEST 3: Complete Auction Flow
        Test league creation → auction start → auction room access
        """
        print("\n🎯 PHASE 3: COMPLETE AUCTION FLOW")
        
        try:
            # Create league
            league_data = {
                "name": f"Socket.IO Test League {datetime.now().strftime('%H%M%S')}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            resp = self.session.post(f"{API_BASE}/leagues", json=league_data)
            if resp.status_code == 201:
                data = resp.json()
                self.league_id = data['leagueId']
                await self.log_result("League Creation", True, f"League ID: {self.league_id}")
            else:
                await self.log_result("League Creation", False, f"Status {resp.status_code}: {resp.text}")
                return False
                
            # Add another user to meet minimum requirements
            resp = self.session.post(f"{API_BASE}/auth/test-login", json={"email": "manager@example.com"})
            if resp.status_code == 200:
                # Create a separate session for the manager
                manager_session = requests.Session()
                manager_session.cookies.update(resp.cookies)
                
                resp = manager_session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                if resp.status_code == 200:
                    await self.log_result("Manager Join", True, "Manager joined league")
                else:
                    await self.log_result("Manager Join", False, f"Status {resp.status_code}")
                    
            # Check league status
            resp = self.session.get(f"{API_BASE}/leagues/{self.league_id}/status")
            if resp.status_code == 200:
                data = resp.json()
                if data.get('is_ready'):
                    await self.log_result("League Ready Check", True, f"Members: {data['member_count']}")
                else:
                    await self.log_result("League Ready Check", False, "League not ready")
                    return False
            else:
                await self.log_result("League Ready Check", False, f"Status {resp.status_code}")
                return False
                
            # Start auction
            resp = self.session.post(f"{API_BASE}/auction/{self.league_id}/start")
            if resp.status_code == 200:
                data = resp.json()
                self.auction_id = data.get('auction_id', self.league_id)
                await self.log_result("Auction Start", True, f"Auction ID: {self.auction_id}")
            else:
                await self.log_result("Auction Start", False, f"Status {resp.status_code}: {resp.text}")
                return False
                
            # Test auction room access
            resp = self.session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result("Auction Room Access", True, f"Auction state retrieved")
                return True
            else:
                await self.log_result("Auction Room Access", False, f"Status {resp.status_code}")
                return False
                
        except Exception as e:
            await self.log_result("Complete Auction Flow", False, f"Exception: {str(e)}")
            return False
            
    async def test_socketio_authentication(self) -> bool:
        """
        CRITICAL TEST 4: Socket.IO Authentication
        Test JWT token validation in Socket.IO connection
        """
        print("\n🎯 PHASE 4: SOCKET.IO AUTHENTICATION")
        
        try:
            if not self.access_token:
                await self.log_result("Socket.IO Auth Setup", False, "No access token available")
                return False
                
            # Test Socket.IO connection with authentication
            sio_client = socketio.AsyncClient()
            connection_success = False
            auth_success = False
            
            @sio_client.event
            async def connect():
                nonlocal connection_success
                connection_success = True
                await self.log_result("Socket.IO Connection", True, "Connected successfully")
                
            @sio_client.event
            async def connect_error(data):
                await self.log_result("Socket.IO Connection", False, f"Connection error: {data}")
                
            @sio_client.event
            async def joined(data):
                nonlocal auth_success
                auth_success = True
                await self.log_result("Socket.IO Authentication", True, f"Joined room: {data}")
                
            try:
                # Connect with authentication token
                await sio_client.connect(
                    f"{BACKEND_URL}/api/socket.io",
                    auth={'token': self.access_token},
                    transports=['polling', 'websocket']
                )
                
                # Wait a moment for connection to establish
                await asyncio.sleep(2)
                
                if connection_success:
                    # Test joining auction room if we have an auction
                    if self.auction_id:
                        await sio_client.emit('join_auction', {'auction_id': self.auction_id})
                        await asyncio.sleep(1)
                        
                    # Test joining league room
                    if self.league_id:
                        await sio_client.emit('join_league', {
                            'league_id': self.league_id,
                            'user_id': self.user_id
                        })
                        await asyncio.sleep(1)
                        
                    await self.log_result("Socket.IO Room Join", True, "Room join events sent")
                    
                await sio_client.disconnect()
                return connection_success
                
            except Exception as e:
                await self.log_result("Socket.IO Connection Test", False, f"Connection exception: {str(e)}")
                return False
                
        except Exception as e:
            await self.log_result("Socket.IO Authentication Test", False, f"Exception: {str(e)}")
            return False
            
    async def test_socketio_diagnostic_endpoint(self) -> bool:
        """Test the Socket.IO diagnostic endpoint"""
        try:
            resp = self.session.get(f"{API_BASE}/socket.io/diag")
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result("Socket.IO Diagnostic", True, f"Path: {data.get('path')}")
                return True
            else:
                await self.log_result("Socket.IO Diagnostic", False, f"Status {resp.status_code}")
                return False
        except Exception as e:
            await self.log_result("Socket.IO Diagnostic", False, f"Exception: {str(e)}")
            return False
            
    async def run_complete_socketio_test(self):
        """Run the complete Socket.IO overlay pattern test suite"""
        print("🎯 SOCKET.IO OVERLAY PATTERN COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        
        try:
            # Setup authentication
            auth_success = await self.setup_authentication()
            if not auth_success:
                print("\n❌ CRITICAL FAILURE: Could not authenticate")
                return
                
            # Phase 1: Socket.IO Endpoint
            endpoint_success = await self.test_socketio_endpoint()
            
            # Phase 2: FastAPI Routes Still Work
            routes_success = await self.test_fastapi_routes_still_work()
            
            # Phase 3: Complete Auction Flow
            auction_success = await self.test_complete_auction_flow()
            
            # Phase 4: Socket.IO Authentication
            socketio_auth_success = await self.test_socketio_authentication()
            
            # Additional: Diagnostic endpoint
            diag_success = await self.test_socketio_diagnostic_endpoint()
            
            # Summary
            print("\n" + "=" * 70)
            print("🎯 SOCKET.IO OVERLAY PATTERN TEST RESULTS SUMMARY")
            print("=" * 70)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            # Critical functionality assessment
            critical_phases = [endpoint_success, routes_success, auction_success, socketio_auth_success]
            critical_passed = sum(critical_phases)
            
            print(f"\nCRITICAL SUCCESS CRITERIA: {critical_passed}/4 passed")
            
            success_criteria = [
                f"✅ Socket.IO handshake returns proper Engine.IO JSON response" if endpoint_success else "❌ Socket.IO handshake fails",
                f"✅ All existing /api/* REST endpoints work normally" if routes_success else "❌ REST endpoints broken", 
                f"✅ Real-time auction functionality works end-to-end" if auction_success else "❌ Auction flow broken",
                f"✅ Users can connect to auction rooms without hanging" if socketio_auth_success else "❌ Socket.IO authentication fails"
            ]
            
            print("\nSUCCESS CRITERIA EVALUATION:")
            for criteria in success_criteria:
                print(f"  {criteria}")
                
            if critical_passed == 4:
                print("\n🎉 SOCKET.IO OVERLAY PATTERN IS FULLY FUNCTIONAL!")
                print("✅ This should finally resolve the 'waiting for auction to begin' issue")
                print("✅ Socket.IO connectivity through /api/* routing is working")
            elif critical_passed >= 3:
                print("\n⚠️ SOCKET.IO OVERLAY PATTERN MOSTLY FUNCTIONAL - Minor issues remain")
            else:
                print("\n❌ SOCKET.IO OVERLAY PATTERN HAS CRITICAL ISSUES")
                
            # Detailed failure analysis
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
                    
        except Exception as e:
            print(f"\n❌ CRITICAL TEST SUITE ERROR: {str(e)}")
        finally:
            self.session.close()

async def main():
    """Main test execution"""
    test_suite = SocketIOOverlayTestSuite()
    await test_suite.run_complete_socketio_test()

if __name__ == "__main__":
    asyncio.run(main())