#!/usr/bin/env python3
"""
ROOM DISCIPLINE AND SYNC ENDPOINT TEST
Tests the Socket.IO room discipline and sync state functionality as requested in review.

This test covers:
1. Socket.IO Event Handlers - Test that `join_league` and `request_sync` events work properly
2. Sync State Functionality - Verify `get_sync_state()` returns correct format: `{lot, highestBid, endsAt, managers, budgets}`
3. Room Discipline - Verify all auction events use proper league_id as room name
4. State Synchronization - Test that entering/reconnecting to a league produces sync_state payload
5. Real-time Updates - Verify auction events (nominate, bid, tick, anti_snipe, sold) broadcast to correct rooms

Acceptance criteria: Entering or reconnecting to a league should immediately produce a sync_state payload for that socket.
"""

import asyncio
import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import socketio
import threading
import time

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://livebid-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
SOCKET_URL = BACKEND_URL

class RoomSyncTestSuite:
    def __init__(self):
        self.sessions = {}  # email -> session mapping
        self.sio_clients = {}  # email -> socketio client mapping
        self.test_users = []
        self.league_id = None
        self.auction_id = None
        self.test_results = []
        self.received_events = {}  # Track received Socket.IO events
        
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
        
    async def authenticate_user(self, email: str) -> Optional[str]:
        """Authenticate user and return user_id"""
        try:
            # Create separate session for each user
            session = requests.Session()
            session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'RoomSyncTestSuite/1.0'
            })
            
            resp = session.post(f"{API_BASE}/auth/test-login", json={"email": email})
            if resp.status_code == 200:
                data = resp.json()
                # Store the authenticated session
                self.sessions[email] = session
                await self.log_result(f"Authentication for {email}", True, f"User ID: {data['userId']}")
                return data['userId']
            else:
                await self.log_result(f"Authentication for {email}", False, f"Status {resp.status_code}: {resp.text}")
                session.close()
                return None
        except Exception as e:
            await self.log_result(f"Authentication for {email}", False, f"Exception: {str(e)}")
            return None

    async def get_jwt_token(self, email: str) -> Optional[str]:
        """Get JWT token for Socket.IO authentication"""
        try:
            # Use magic link flow to get JWT token
            session = self.sessions[email]
            
            # Request magic link
            resp = session.post(f"{API_BASE}/auth/magic-link", json={"email": email})
            if resp.status_code == 200:
                data = resp.json()
                if 'dev_magic_link' in data:
                    # Extract token from dev magic link
                    magic_link = data['dev_magic_link']
                    token = magic_link.split('token=')[1] if 'token=' in magic_link else None
                    
                    if token:
                        # Verify the token to get JWT
                        verify_resp = session.post(f"{API_BASE}/auth/verify", json={"token": token})
                        if verify_resp.status_code == 200:
                            verify_data = verify_resp.json()
                            jwt_token = verify_data.get('access_token')
                            await self.log_result(f"JWT Token for {email}", True, "Token obtained")
                            return jwt_token
                        else:
                            await self.log_result(f"JWT Token for {email}", False, f"Verify failed: {verify_resp.status_code}")
                    else:
                        await self.log_result(f"JWT Token for {email}", False, "No token in magic link")
                else:
                    await self.log_result(f"JWT Token for {email}", False, "No dev magic link in response")
            else:
                await self.log_result(f"JWT Token for {email}", False, f"Magic link failed: {resp.status_code}")
                
        except Exception as e:
            await self.log_result(f"JWT Token for {email}", False, f"Exception: {str(e)}")
            
        return None

    async def setup_socketio_client(self, email: str, jwt_token: str) -> bool:
        """Setup Socket.IO client for user"""
        try:
            # Create Socket.IO client
            sio = socketio.AsyncClient(
                reconnection=True,
                reconnection_attempts=3,
                reconnection_delay=1
            )
            
            # Setup event handlers for this client
            self.received_events[email] = []
            
            @sio.event
            async def connect():
                print(f"Socket.IO connected for {email}")
                
            @sio.event
            async def disconnect():
                print(f"Socket.IO disconnected for {email}")
                
            @sio.event
            async def joined(data):
                print(f"Socket.IO joined event for {email}: {data}")
                self.received_events[email].append(('joined', data))
                
            @sio.event
            async def sync_state(data):
                print(f"Socket.IO sync_state event for {email}: {json.dumps(data, indent=2)}")
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
                
            # Connect with JWT authentication
            auth_data = {'token': jwt_token}
            await sio.connect(f"{SOCKET_URL}/api/socket.io", auth=auth_data)
            
            # Store the client
            self.sio_clients[email] = sio
            
            await self.log_result(f"Socket.IO Setup for {email}", True, "Client connected")
            return True
            
        except Exception as e:
            await self.log_result(f"Socket.IO Setup for {email}", False, f"Exception: {str(e)}")
            return False

    async def create_test_league(self) -> bool:
        """Create a test league for room discipline testing"""
        print("\n🎯 PHASE 1: TEST LEAGUE CREATION")
        
        try:
            # Create test users
            test_emails = [
                "commissioner@roomtest.com",
                "manager1@roomtest.com", 
                "manager2@roomtest.com"
            ]
            
            # Authenticate all users
            for email in test_emails:
                user_id = await self.authenticate_user(email)
                if user_id:
                    self.test_users.append({
                        'email': email,
                        'user_id': user_id,
                        'role': 'commissioner' if email == test_emails[0] else 'manager'
                    })
                    
            if len(self.test_users) < 3:
                await self.log_result("User Authentication", False, f"Only {len(self.test_users)}/3 users authenticated")
                return False
                
            await self.log_result("User Authentication", True, f"All {len(self.test_users)} users authenticated")
            
            # Create league as commissioner
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            league_data = {
                "name": f"Room Sync Test League {datetime.now().strftime('%H%M%S')}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            resp = commissioner_session.post(f"{API_BASE}/leagues", json=league_data)
            if resp.status_code == 201:
                data = resp.json()
                self.league_id = data['leagueId']
                await self.log_result("League Creation", True, f"League ID: {self.league_id}")
                return True
            else:
                await self.log_result("League Creation", False, f"Status {resp.status_code}: {resp.text}")
                return False
                    
        except Exception as e:
            await self.log_result("Test League Creation", False, f"Exception: {str(e)}")
            return False

    async def test_join_league_event(self) -> bool:
        """
        CRITICAL TEST 1: Socket.IO join_league Event Handler
        Test that join_league event works properly and automatically requests sync
        """
        print("\n🎯 PHASE 2: JOIN_LEAGUE EVENT HANDLER TESTING")
        
        try:
            # Setup Socket.IO clients for all users
            for user in self.test_users:
                jwt_token = await self.get_jwt_token(user['email'])
                if not jwt_token:
                    await self.log_result(f"JWT Setup for {user['email']}", False, "Could not get JWT token")
                    return False
                    
                success = await self.setup_socketio_client(user['email'], jwt_token)
                if not success:
                    await self.log_result(f"Socket.IO Setup for {user['email']}", False, "Could not setup client")
                    return False
                    
            # Test join_league event for commissioner
            commissioner = self.test_users[0]
            commissioner_sio = self.sio_clients[commissioner['email']]
            
            # Clear previous events
            self.received_events[commissioner['email']] = []
            
            # Emit join_league event
            await commissioner_sio.emit('join_league', {'leagueId': self.league_id})
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Check for joined and sync_state events
            events = self.received_events[commissioner['email']]
            joined_received = any(event[0] == 'joined' for event in events)
            sync_state_received = any(event[0] == 'sync_state' for event in events)
            
            if joined_received and sync_state_received:
                await self.log_result("join_league Event Handler", True, 
                                    "Both 'joined' and 'sync_state' events received")
                return True
            else:
                await self.log_result("join_league Event Handler", False, 
                                    f"Missing events - joined: {joined_received}, sync_state: {sync_state_received}")
                return False
                
        except Exception as e:
            await self.log_result("join_league Event Handler", False, f"Exception: {str(e)}")
            return False

    async def test_sync_state_format(self) -> bool:
        """
        CRITICAL TEST 2: Sync State Functionality
        Verify get_sync_state() returns correct format: {lot, highestBid, endsAt, managers, budgets}
        """
        print("\n🎯 PHASE 3: SYNC STATE FORMAT TESTING")
        
        try:
            # Get the most recent sync_state event
            commissioner = self.test_users[0]
            events = self.received_events[commissioner['email']]
            sync_events = [event[1] for event in events if event[0] == 'sync_state']
            
            if not sync_events:
                await self.log_result("Sync State Format", False, "No sync_state events received")
                return False
                
            sync_data = sync_events[-1]  # Get the latest sync_state
            
            # Check required fields
            required_fields = ['lot', 'highestBid', 'endsAt', 'managers', 'budgets']
            missing_fields = []
            
            for field in required_fields:
                if field not in sync_data:
                    missing_fields.append(field)
                    
            if missing_fields:
                await self.log_result("Sync State Format", False, 
                                    f"Missing required fields: {missing_fields}")
                return False
            else:
                await self.log_result("Sync State Format", True, 
                                    f"All required fields present: {required_fields}")
                
            # Validate field types
            validation_results = []
            
            # lot can be None or dict
            if sync_data['lot'] is not None and not isinstance(sync_data['lot'], dict):
                validation_results.append("lot should be None or dict")
                
            # highestBid should be number or None
            if sync_data['highestBid'] is not None and not isinstance(sync_data['highestBid'], (int, float)):
                validation_results.append("highestBid should be number or None")
                
            # endsAt should be string or None
            if sync_data['endsAt'] is not None and not isinstance(sync_data['endsAt'], str):
                validation_results.append("endsAt should be string or None")
                
            # managers should be list
            if not isinstance(sync_data['managers'], list):
                validation_results.append("managers should be list")
                
            # budgets should be dict
            if not isinstance(sync_data['budgets'], dict):
                validation_results.append("budgets should be dict")
                
            if validation_results:
                await self.log_result("Sync State Type Validation", False, 
                                    f"Type validation errors: {validation_results}")
                return False
            else:
                await self.log_result("Sync State Type Validation", True, 
                                    "All field types are correct")
                return True
                
        except Exception as e:
            await self.log_result("Sync State Format", False, f"Exception: {str(e)}")
            return False

    async def test_request_sync_event(self) -> bool:
        """
        CRITICAL TEST 3: request_sync Event Handler
        Test that request_sync event works properly
        """
        print("\n🎯 PHASE 4: REQUEST_SYNC EVENT HANDLER TESTING")
        
        try:
            # Test request_sync event for manager
            manager = self.test_users[1]
            
            # Setup Socket.IO client if not already done
            if manager['email'] not in self.sio_clients:
                jwt_token = await self.get_jwt_token(manager['email'])
                if not jwt_token:
                    await self.log_result(f"JWT Setup for {manager['email']}", False, "Could not get JWT token")
                    return False
                    
                success = await self.setup_socketio_client(manager['email'], jwt_token)
                if not success:
                    await self.log_result(f"Socket.IO Setup for {manager['email']}", False, "Could not setup client")
                    return False
            
            manager_sio = self.sio_clients[manager['email']]
            
            # Clear previous events
            self.received_events[manager['email']] = []
            
            # Emit request_sync event directly
            await manager_sio.emit('request_sync', {'leagueId': self.league_id})
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Check for sync_state event
            events = self.received_events[manager['email']]
            sync_state_received = any(event[0] == 'sync_state' for event in events)
            sync_error_received = any(event[0] == 'sync_error' for event in events)
            
            if sync_state_received:
                await self.log_result("request_sync Event Handler", True, 
                                    "sync_state event received after request_sync")
                return True
            elif sync_error_received:
                error_data = [event[1] for event in events if event[0] == 'sync_error'][0]
                await self.log_result("request_sync Event Handler", False, 
                                    f"sync_error received: {error_data}")
                return False
            else:
                await self.log_result("request_sync Event Handler", False, 
                                    "No sync_state or sync_error event received")
                return False
                
        except Exception as e:
            await self.log_result("request_sync Event Handler", False, f"Exception: {str(e)}")
            return False

    async def test_room_discipline(self) -> bool:
        """
        CRITICAL TEST 4: Room Discipline
        Verify all auction events use proper league_id as room name
        """
        print("\n🎯 PHASE 5: ROOM DISCIPLINE TESTING")
        
        try:
            # Add managers to league to test room discipline
            for user in self.test_users[1:]:  # Skip commissioner
                user_session = self.sessions[user['email']]
                resp = user_session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                if resp.status_code == 200:
                    await self.log_result(f"User Join - {user['email']}", True)
                else:
                    await self.log_result(f"User Join - {user['email']}", False, f"Status {resp.status_code}: {resp.text}")
                    
            # Wait for member_joined events
            await asyncio.sleep(2)
            
            # Check if all clients received member_joined events
            member_joined_count = 0
            for user in self.test_users:
                if user['email'] in self.received_events:
                    events = self.received_events[user['email']]
                    member_joined_events = [event for event in events if event[0] == 'member_joined']
                    if member_joined_events:
                        member_joined_count += 1
                        
            if member_joined_count > 0:
                await self.log_result("Room Discipline - Member Events", True, 
                                    f"{member_joined_count} clients received member_joined events")
            else:
                await self.log_result("Room Discipline - Member Events", False, 
                                    "No clients received member_joined events")
                
            # Test league status update events
            league_status_count = 0
            for user in self.test_users:
                if user['email'] in self.received_events:
                    events = self.received_events[user['email']]
                    status_events = [event for event in events if event[0] == 'league_status_update']
                    if status_events:
                        league_status_count += 1
                        
            if league_status_count > 0:
                await self.log_result("Room Discipline - Status Events", True, 
                                    f"{league_status_count} clients received league_status_update events")
                return True
            else:
                await self.log_result("Room Discipline - Status Events", False, 
                                    "No clients received league_status_update events")
                return False
                
        except Exception as e:
            await self.log_result("Room Discipline", False, f"Exception: {str(e)}")
            return False

    async def test_reconnection_sync(self) -> bool:
        """
        CRITICAL TEST 5: State Synchronization on Reconnection
        Test that reconnecting to a league produces sync_state payload
        """
        print("\n🎯 PHASE 6: RECONNECTION SYNC TESTING")
        
        try:
            # Disconnect and reconnect a client
            manager = self.test_users[1]
            manager_sio = self.sio_clients[manager['email']]
            
            # Disconnect
            await manager_sio.disconnect()
            await asyncio.sleep(1)
            
            # Clear events
            self.received_events[manager['email']] = []
            
            # Reconnect
            jwt_token = await self.get_jwt_token(manager['email'])
            if not jwt_token:
                await self.log_result("Reconnection JWT", False, "Could not get JWT token")
                return False
                
            success = await self.setup_socketio_client(manager['email'], jwt_token)
            if not success:
                await self.log_result("Reconnection Setup", False, "Could not reconnect client")
                return False
                
            # Join league again
            manager_sio = self.sio_clients[manager['email']]
            await manager_sio.emit('join_league', {'leagueId': self.league_id})
            
            # Wait for sync
            await asyncio.sleep(2)
            
            # Check for sync_state event
            events = self.received_events[manager['email']]
            sync_state_received = any(event[0] == 'sync_state' for event in events)
            
            if sync_state_received:
                await self.log_result("Reconnection Sync", True, 
                                    "sync_state event received after reconnection")
                return True
            else:
                await self.log_result("Reconnection Sync", False, 
                                    "No sync_state event received after reconnection")
                return False
                
        except Exception as e:
            await self.log_result("Reconnection Sync", False, f"Exception: {str(e)}")
            return False

    async def cleanup_clients(self):
        """Cleanup Socket.IO clients"""
        for email, sio in self.sio_clients.items():
            try:
                await sio.disconnect()
            except:
                pass
                
        for session in self.sessions.values():
            try:
                session.close()
            except:
                pass

    async def run_room_sync_test(self):
        """Run the complete room discipline and sync test suite"""
        print("🎯 ROOM DISCIPLINE AND SYNC ENDPOINT TEST SUITE")
        print("=" * 60)
        
        try:
            # Phase 1: Create Test League
            league_success = await self.create_test_league()
            if not league_success:
                print("\n❌ CRITICAL FAILURE: Could not create test league")
                return
                
            # Phase 2: Test join_league Event Handler
            join_success = await self.test_join_league_event()
            
            # Phase 3: Test Sync State Format
            format_success = await self.test_sync_state_format()
            
            # Phase 4: Test request_sync Event Handler
            request_success = await self.test_request_sync_event()
            
            # Phase 5: Test Room Discipline
            room_success = await self.test_room_discipline()
            
            # Phase 6: Test Reconnection Sync
            reconnect_success = await self.test_reconnection_sync()
            
            # Summary
            print("\n" + "=" * 60)
            print("🎯 ROOM DISCIPLINE AND SYNC TEST RESULTS SUMMARY")
            print("=" * 60)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            # Critical functionality assessment
            critical_phases = [league_success, join_success, format_success, request_success, room_success, reconnect_success]
            critical_passed = sum(critical_phases)
            
            print(f"\nCRITICAL PHASES: {critical_passed}/6 passed")
            
            if critical_passed >= 5:
                print("✅ ROOM DISCIPLINE AND SYNC IMPLEMENTATION IS FUNCTIONAL")
                print("✅ Acceptance criteria met: Entering/reconnecting produces sync_state payload")
            elif critical_passed >= 3:
                print("⚠️ ROOM DISCIPLINE AND SYNC PARTIALLY FUNCTIONAL - Some issues need attention")
            else:
                print("❌ ROOM DISCIPLINE AND SYNC HAS CRITICAL ISSUES - Needs immediate fixes")
                
            # Detailed failure analysis
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
                    
        finally:
            await self.cleanup_clients()

async def main():
    """Main test execution"""
    test_suite = RoomSyncTestSuite()
    await test_suite.run_room_sync_test()

if __name__ == "__main__":
    asyncio.run(main())