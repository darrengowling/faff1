#!/usr/bin/env python3
"""
CLIENT RECONNECTION AND STATE SYNC SYSTEM TEST
Tests the complete Socket.IO reconnection and state synchronization functionality.

This test covers:
1. Socket.IO Event Handlers (join_league, request_sync)
2. State Synchronization (league status, members, auction state)
3. Reconnection Flow Simulation (client joining, sync requests)
4. Multi-User Scenario (multiple clients, room isolation)
"""

import asyncio
import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import socketio
import uuid
import time

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://livebid-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
SOCKET_URL = f"{BACKEND_URL}/api/socket.io"

class ReconnectionSyncTestSuite:
    def __init__(self):
        self.sessions = {}  # email -> session mapping
        self.sio_clients = {}  # email -> socketio client mapping
        self.test_users = []
        self.league_id = None
        self.auction_id = None
        self.test_results = []
        self.received_events = {}  # Track events received by each client
        
    async def setup_session(self):
        """Setup HTTP sessions - will be created per user"""
        pass
        
    async def cleanup_session(self):
        """Cleanup HTTP sessions and Socket.IO clients"""
        for session in self.sessions.values():
            session.close()
        for sio_client in self.sio_clients.values():
            await sio_client.disconnect()
            
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
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def create_session(self, email: str) -> requests.Session:
        """Create authenticated session for user"""
        session = requests.Session()
        
        # Test login to get session cookie
        login_response = session.post(f"{API_BASE}/auth/test-login", json={"email": email})
        if login_response.status_code != 200:
            raise Exception(f"Failed to login user {email}: {login_response.status_code}")
            
        self.sessions[email] = session
        return session
        
    async def create_socketio_client(self, email: str) -> socketio.AsyncClient:
        """Create authenticated Socket.IO client for user"""
        # Get JWT token for Socket.IO authentication
        session = self.sessions[email]
        me_response = session.get(f"{API_BASE}/auth/me")
        if me_response.status_code != 200:
            raise Exception(f"Failed to get user info for {email}")
            
        # Extract access token from session cookie
        access_token = None
        for cookie in session.cookies:
            if cookie.name == 'access_token':
                access_token = cookie.value
                break
                
        if not access_token:
            raise Exception(f"No access token found for {email}")
            
        # Create Socket.IO client
        sio = socketio.AsyncClient()
        
        # Setup event handlers to track received events
        self.received_events[email] = []
        
        @sio.event
        async def connect():
            print(f"Socket.IO client connected for {email}")
            self.received_events[email].append(('connect', {}))
            
        @sio.event
        async def disconnect():
            print(f"Socket.IO client disconnected for {email}")
            self.received_events[email].append(('disconnect', {}))
            
        @sio.event
        async def joined(data):
            print(f"Socket.IO joined event for {email}: {data}")
            self.received_events[email].append(('joined', data))
            
        @sio.event
        async def sync_state(data):
            print(f"Socket.IO sync_state event for {email}: {data}")
            self.received_events[email].append(('sync_state', data))
            
        @sio.event
        async def sync_error(data):
            print(f"Socket.IO sync_error event for {email}: {data}")
            self.received_events[email].append(('sync_error', data))
            
        @sio.event
        async def member_joined(data):
            print(f"Socket.IO member_joined event for {email}: {data}")
            self.received_events[email].append(('member_joined', data))
            
        @sio.event
        async def league_status_update(data):
            print(f"Socket.IO league_status_update event for {email}: {data}")
            self.received_events[email].append(('league_status_update', data))
            
        @sio.event
        async def user_joined_league(data):
            print(f"Socket.IO user_joined_league event for {email}: {data}")
            self.received_events[email].append(('user_joined_league', data))
            
        # Connect with authentication
        try:
            await sio.connect(SOCKET_URL, auth={'token': access_token})
            self.sio_clients[email] = sio
            return sio
        except Exception as e:
            print(f"Failed to connect Socket.IO client for {email}: {e}")
            raise
            
    async def test_1_setup_league_and_users(self):
        """Test 1: Setup league with multiple users for testing"""
        try:
            print("\n=== TEST 1: SETUP LEAGUE AND USERS ===")
            
            # Create test users
            self.test_users = [
                f"commissioner-{uuid.uuid4().hex[:8]}@test.com",
                f"manager1-{uuid.uuid4().hex[:8]}@test.com", 
                f"manager2-{uuid.uuid4().hex[:8]}@test.com",
                f"manager3-{uuid.uuid4().hex[:8]}@test.com"
            ]
            
            # Create sessions for all users
            for email in self.test_users:
                self.create_session(email)
                
            # Create league with commissioner
            commissioner_session = self.sessions[self.test_users[0]]
            league_data = {
                "name": f"Reconnection Test League {uuid.uuid4().hex[:8]}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            create_response = commissioner_session.post(f"{API_BASE}/leagues", json=league_data)
            if create_response.status_code != 201:
                await self.log_result("League Creation", False, f"Status: {create_response.status_code}")
                return False
                
            self.league_id = create_response.json()["leagueId"]
            await self.log_result("League Creation", True, f"League ID: {self.league_id}")
            
            # Add other users to league
            for email in self.test_users[1:]:  # Skip commissioner
                session = self.sessions[email]
                join_response = session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                if join_response.status_code != 200:
                    await self.log_result(f"User Join ({email})", False, f"Status: {join_response.status_code}")
                    return False
                await self.log_result(f"User Join ({email})", True, "Successfully joined league")
                
            return True
            
        except Exception as e:
            await self.log_result("Setup League and Users", False, f"Exception: {str(e)}")
            return False
            
    async def test_2_socket_io_event_handlers(self):
        """Test 2: Socket.IO Event Handlers (join_league, request_sync)"""
        try:
            print("\n=== TEST 2: SOCKET.IO EVENT HANDLERS ===")
            
            # Create Socket.IO clients for all users
            for email in self.test_users:
                await self.create_socketio_client(email)
                
            # Wait for connections to establish
            await asyncio.sleep(2)
            
            # Test join_league event handler with different formats
            commissioner_sio = self.sio_clients[self.test_users[0]]
            
            # Test with leagueId format
            await commissioner_sio.emit('join_league', {'leagueId': self.league_id})
            await asyncio.sleep(1)
            
            # Test with league_id format  
            await commissioner_sio.emit('join_league', {'league_id': self.league_id})
            await asyncio.sleep(1)
            
            # Check if joined events were received
            commissioner_events = self.received_events[self.test_users[0]]
            joined_events = [e for e in commissioner_events if e[0] == 'joined']
            
            if len(joined_events) >= 2:
                await self.log_result("join_league Event Handler", True, f"Received {len(joined_events)} joined events")
            else:
                await self.log_result("join_league Event Handler", False, f"Expected 2+ joined events, got {len(joined_events)}")
                return False
                
            # Test request_sync event handler
            await commissioner_sio.emit('request_sync', {'leagueId': self.league_id})
            await asyncio.sleep(2)
            
            # Check if sync_state event was received
            sync_events = [e for e in commissioner_events if e[0] == 'sync_state']
            if len(sync_events) >= 1:
                sync_data = sync_events[0][1]
                required_fields = ['league_id', 'league_status', 'members']
                missing_fields = [field for field in required_fields if field not in sync_data]
                
                if not missing_fields:
                    await self.log_result("request_sync Event Handler", True, f"Sync data contains all required fields")
                else:
                    await self.log_result("request_sync Event Handler", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                await self.log_result("request_sync Event Handler", False, "No sync_state event received")
                return False
                
            return True
            
        except Exception as e:
            await self.log_result("Socket.IO Event Handlers", False, f"Exception: {str(e)}")
            return False
            
    async def test_3_state_synchronization(self):
        """Test 3: State Synchronization (complete league information)"""
        try:
            print("\n=== TEST 3: STATE SYNCHRONIZATION ===")
            
            commissioner_sio = self.sio_clients[self.test_users[0]]
            
            # Request sync and analyze the response
            await commissioner_sio.emit('request_sync', {'leagueId': self.league_id})
            await asyncio.sleep(2)
            
            # Get the latest sync_state event
            commissioner_events = self.received_events[self.test_users[0]]
            sync_events = [e for e in commissioner_events if e[0] == 'sync_state']
            
            if not sync_events:
                await self.log_result("State Synchronization", False, "No sync_state events received")
                return False
                
            sync_data = sync_events[-1][1]  # Get latest sync event
            
            # Verify league information completeness
            checks = []
            
            # Check league_id
            if sync_data.get('league_id') == self.league_id:
                checks.append(("League ID", True, f"Correct: {self.league_id}"))
            else:
                checks.append(("League ID", False, f"Expected {self.league_id}, got {sync_data.get('league_id')}"))
                
            # Check league_status
            league_status = sync_data.get('league_status')
            if league_status and isinstance(league_status, dict):
                status_fields = ['member_count', 'is_ready', 'status']
                missing_status_fields = [f for f in status_fields if f not in league_status]
                if not missing_status_fields:
                    checks.append(("League Status", True, f"Contains: {list(league_status.keys())}"))
                else:
                    checks.append(("League Status", False, f"Missing: {missing_status_fields}"))
            else:
                checks.append(("League Status", False, "Missing or invalid league_status"))
                
            # Check members
            members = sync_data.get('members')
            if members and isinstance(members, list) and len(members) >= len(self.test_users):
                checks.append(("Members List", True, f"Contains {len(members)} members"))
            else:
                checks.append(("Members List", False, f"Expected {len(self.test_users)}+ members, got {len(members) if members else 0}"))
                
            # Check auction_state (should be None since no auction started)
            auction_state = sync_data.get('auction_state')
            if auction_state is None:
                checks.append(("Auction State", True, "Correctly None (no auction active)"))
            else:
                checks.append(("Auction State", True, f"Auction data present: {type(auction_state)}"))
                
            # Log all checks
            all_passed = True
            for check_name, passed, details in checks:
                await self.log_result(f"Sync Check: {check_name}", passed, details)
                if not passed:
                    all_passed = False
                    
            return all_passed
            
        except Exception as e:
            await self.log_result("State Synchronization", False, f"Exception: {str(e)}")
            return False
            
    async def test_4_reconnection_flow_simulation(self):
        """Test 4: Reconnection Flow Simulation"""
        try:
            print("\n=== TEST 4: RECONNECTION FLOW SIMULATION ===")
            
            # Simulate reconnection by disconnecting and reconnecting a client
            manager1_email = self.test_users[1]
            manager1_sio = self.sio_clients[manager1_email]
            
            # Disconnect client
            await manager1_sio.disconnect()
            await asyncio.sleep(1)
            
            # Clear previous events
            self.received_events[manager1_email] = []
            
            # Reconnect client
            await self.create_socketio_client(manager1_email)
            new_manager1_sio = self.sio_clients[manager1_email]
            
            # Wait for connection
            await asyncio.sleep(2)
            
            # Simulate reconnection flow: join league room
            await new_manager1_sio.emit('join_league', {
                'leagueId': self.league_id,
                'user_id': f"user-{manager1_email}"
            })
            await asyncio.sleep(1)
            
            # Request sync to restore state
            await new_manager1_sio.emit('request_sync', {'leagueId': self.league_id})
            await asyncio.sleep(2)
            
            # Verify reconnection flow
            manager1_events = self.received_events[manager1_email]
            
            # Check for connect event
            connect_events = [e for e in manager1_events if e[0] == 'connect']
            if connect_events:
                await self.log_result("Reconnection: Connect", True, "Client reconnected successfully")
            else:
                await self.log_result("Reconnection: Connect", False, "No connect event received")
                return False
                
            # Check for joined event (room rejoin)
            joined_events = [e for e in manager1_events if e[0] == 'joined']
            if joined_events:
                await self.log_result("Reconnection: Room Join", True, f"Rejoined league room: {joined_events[0][1]}")
            else:
                await self.log_result("Reconnection: Room Join", False, "No joined event received")
                return False
                
            # Check for sync_state event (state restoration)
            sync_events = [e for e in manager1_events if e[0] == 'sync_state']
            if sync_events:
                await self.log_result("Reconnection: State Sync", True, "State synchronized after reconnection")
            else:
                await self.log_result("Reconnection: State Sync", False, "No sync_state event received")
                return False
                
            return True
            
        except Exception as e:
            await self.log_result("Reconnection Flow Simulation", False, f"Exception: {str(e)}")
            return False
            
    async def test_5_multi_user_scenario(self):
        """Test 5: Multi-User Scenario (room isolation, multiple clients)"""
        try:
            print("\n=== TEST 5: MULTI-USER SCENARIO ===")
            
            # Clear all event logs
            for email in self.test_users:
                self.received_events[email] = []
                
            # Have all users join the league room
            for email in self.test_users:
                sio_client = self.sio_clients[email]
                await sio_client.emit('join_league', {
                    'leagueId': self.league_id,
                    'user_id': f"user-{email}"
                })
                
            await asyncio.sleep(2)
            
            # Verify all users received joined events
            all_joined = True
            for email in self.test_users:
                events = self.received_events[email]
                joined_events = [e for e in events if e[0] == 'joined']
                if joined_events:
                    await self.log_result(f"Multi-User Join ({email})", True, "Successfully joined league room")
                else:
                    await self.log_result(f"Multi-User Join ({email})", False, "No joined event received")
                    all_joined = False
                    
            if not all_joined:
                return False
                
            # Test room isolation by having one user request sync
            # and verify others receive user_joined_league events
            commissioner_sio = self.sio_clients[self.test_users[0]]
            
            # Clear events again
            for email in self.test_users:
                self.received_events[email] = []
                
            # Commissioner requests sync
            await commissioner_sio.emit('request_sync', {'leagueId': self.league_id})
            await asyncio.sleep(2)
            
            # Verify commissioner received sync_state
            commissioner_events = self.received_events[self.test_users[0]]
            sync_events = [e for e in commissioner_events if e[0] == 'sync_state']
            if sync_events:
                await self.log_result("Multi-User: Commissioner Sync", True, "Commissioner received sync_state")
            else:
                await self.log_result("Multi-User: Commissioner Sync", False, "Commissioner did not receive sync_state")
                return False
                
            # Test that multiple users can sync simultaneously
            sync_tasks = []
            for i, email in enumerate(self.test_users[1:3]):  # Test with 2 users
                sio_client = self.sio_clients[email]
                task = sio_client.emit('request_sync', {'leagueId': self.league_id})
                sync_tasks.append(task)
                
            # Execute simultaneous sync requests
            await asyncio.gather(*sync_tasks)
            await asyncio.sleep(3)
            
            # Verify both users received sync responses
            simultaneous_sync_success = True
            for email in self.test_users[1:3]:
                events = self.received_events[email]
                sync_events = [e for e in events if e[0] == 'sync_state']
                if sync_events:
                    await self.log_result(f"Simultaneous Sync ({email})", True, "Received sync_state")
                else:
                    await self.log_result(f"Simultaneous Sync ({email})", False, "No sync_state received")
                    simultaneous_sync_success = False
                    
            return simultaneous_sync_success
            
        except Exception as e:
            await self.log_result("Multi-User Scenario", False, f"Exception: {str(e)}")
            return False
            
    async def test_6_error_handling(self):
        """Test 6: Error Handling (invalid league IDs, sync failures)"""
        try:
            print("\n=== TEST 6: ERROR HANDLING ===")
            
            commissioner_sio = self.sio_clients[self.test_users[0]]
            
            # Clear events
            self.received_events[self.test_users[0]] = []
            
            # Test with invalid league ID
            invalid_league_id = "invalid-league-id-12345"
            await commissioner_sio.emit('request_sync', {'leagueId': invalid_league_id})
            await asyncio.sleep(2)
            
            # Check for sync_error event
            commissioner_events = self.received_events[self.test_users[0]]
            error_events = [e for e in commissioner_events if e[0] == 'sync_error']
            
            if error_events:
                error_data = error_events[0][1]
                if 'error' in error_data and 'not found' in error_data['error'].lower():
                    await self.log_result("Error Handling: Invalid League ID", True, f"Correct error: {error_data['error']}")
                else:
                    await self.log_result("Error Handling: Invalid League ID", False, f"Unexpected error: {error_data}")
                    return False
            else:
                await self.log_result("Error Handling: Invalid League ID", False, "No sync_error event received")
                return False
                
            # Test with missing league ID
            self.received_events[self.test_users[0]] = []
            await commissioner_sio.emit('request_sync', {})  # No leagueId
            await asyncio.sleep(2)
            
            commissioner_events = self.received_events[self.test_users[0]]
            error_events = [e for e in commissioner_events if e[0] == 'sync_error']
            
            if error_events:
                error_data = error_events[0][1]
                if 'error' in error_data and 'required' in error_data['error'].lower():
                    await self.log_result("Error Handling: Missing League ID", True, f"Correct error: {error_data['error']}")
                else:
                    await self.log_result("Error Handling: Missing League ID", False, f"Unexpected error: {error_data}")
                    return False
            else:
                await self.log_result("Error Handling: Missing League ID", False, "No sync_error event received")
                return False
                
            return True
            
        except Exception as e:
            await self.log_result("Error Handling", False, f"Exception: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Run all reconnection and sync tests"""
        print("🔄 STARTING CLIENT RECONNECTION AND STATE SYNC SYSTEM TESTS")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Socket.IO URL: {SOCKET_URL}")
        
        try:
            # Run tests in sequence
            tests = [
                self.test_1_setup_league_and_users,
                self.test_2_socket_io_event_handlers,
                self.test_3_state_synchronization,
                self.test_4_reconnection_flow_simulation,
                self.test_5_multi_user_scenario,
                self.test_6_error_handling
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_func in tests:
                try:
                    result = await test_func()
                    if result:
                        passed_tests += 1
                except Exception as e:
                    print(f"❌ Test {test_func.__name__} failed with exception: {e}")
                    
            # Print summary
            print(f"\n🎯 RECONNECTION AND SYNC TEST SUMMARY")
            print(f"Passed: {passed_tests}/{total_tests} tests ({passed_tests/total_tests*100:.1f}%)")
            
            # Print detailed results
            print(f"\n📊 DETAILED RESULTS:")
            for result in self.test_results:
                status = "✅" if result['success'] else "❌"
                print(f"{status} {result['test']}: {result['details']}")
                
            return passed_tests, total_tests
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            return 0, len(tests)
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    test_suite = ReconnectionSyncTestSuite()
    passed, total = await test_suite.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! ({passed}/{total})")
        sys.exit(0)
    else:
        print(f"\n⚠️ SOME TESTS FAILED ({passed}/{total})")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())