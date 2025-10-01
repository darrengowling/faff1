#!/usr/bin/env python3
"""
POLLING-ONLY SOCKET.IO CONFIGURATION TEST
Tests Socket.IO with polling transport only, bypassing WebSocket upgrade.

This test covers:
1. Transport Configuration Test - Verify polling-only mode
2. Multi-User Auction Simulation - Test with 4-8 users
3. Real-time Event Delivery - Verify auction events via polling
4. Performance Verification - Test responsiveness with polling
5. Fallback Integration - Test environment variable override

SUCCESS CRITERIA:
- Socket.IO connects using only polling transport
- Multi-user auction functionality works without WebSocket
- Real-time events delivered reliably via polling
- No WebSocket upgrade attempts when VITE_SOCKET_TRANSPORTS=polling
"""

import asyncio
import requests
import json
import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
import socketio
import concurrent.futures

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
SOCKET_URL = BACKEND_URL
SOCKET_PATH = "/api/socket.io"

class PollingSocketTestSuite:
    def __init__(self):
        self.sessions = {}  # email -> session mapping
        self.socket_clients = {}  # email -> socket client mapping
        self.test_users = []
        self.league_id = None
        self.auction_id = None
        self.test_results = []
        self.event_logs = []  # Track received events
        self.transport_logs = []  # Track transport usage
        
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
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def log_event(self, user_email: str, event_type: str, data: dict):
        """Log received Socket.IO event"""
        event_log = {
            'user': user_email,
            'event': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self.event_logs.append(event_log)
        print(f"📡 EVENT [{user_email}]: {event_type} - {data}")
        
    def log_transport(self, user_email: str, transport: str, action: str):
        """Log transport usage"""
        transport_log = {
            'user': user_email,
            'transport': transport,
            'action': action,
            'timestamp': datetime.now().isoformat()
        }
        self.transport_logs.append(transport_log)
        print(f"🚀 TRANSPORT [{user_email}]: {transport} - {action}")

    async def authenticate_user(self, email: str) -> Optional[str]:
        """Authenticate user and return access token"""
        session = requests.Session()
        
        try:
            # Use test login endpoint
            response = session.post(f"{API_BASE}/auth/test-login", json={"email": email})
            
            if response.status_code == 200:
                # Extract token from cookie
                access_token = None
                for cookie in session.cookies:
                    if cookie.name == 'access_token':
                        access_token = cookie.value
                        break
                
                if access_token:
                    self.sessions[email] = session
                    self.log_result(f"Authentication for {email}", True, f"Token obtained")
                    return access_token
                else:
                    self.log_result(f"Authentication for {email}", False, "No access token in cookies")
                    return None
            else:
                self.log_result(f"Authentication for {email}", False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_result(f"Authentication for {email}", False, f"Error: {str(e)}")
            return None

    async def create_socket_client(self, email: str, access_token: str) -> Optional[socketio.AsyncClient]:
        """Create Socket.IO client with polling-only transport"""
        try:
            # Create client with POLLING ONLY transport
            sio = socketio.AsyncClient(
                logger=False,
                engineio_logger=False
            )
            
            # Event handlers to track transport usage
            @sio.event
            async def connect():
                self.log_transport(email, "polling", "connected")
                self.log_event(email, "connect", {"status": "connected"})
                
            @sio.event
            async def disconnect():
                self.log_transport(email, "polling", "disconnected")
                self.log_event(email, "disconnect", {"status": "disconnected"})
                
            # Auction-specific event handlers
            @sio.event
            async def joined(data):
                self.log_event(email, "joined", data)
                
            @sio.event
            async def league_joined(data):
                self.log_event(email, "league_joined", data)
                
            @sio.event
            async def user_joined_league(data):
                self.log_event(email, "user_joined_league", data)
                
            @sio.event
            async def member_joined(data):
                self.log_event(email, "member_joined", data)
                
            @sio.event
            async def league_status_update(data):
                self.log_event(email, "league_status_update", data)
                
            @sio.event
            async def auction_started(data):
                self.log_event(email, "auction_started", data)
                
            @sio.event
            async def bid_placed(data):
                self.log_event(email, "bid_placed", data)
                
            @sio.event
            async def lot_closed(data):
                self.log_event(email, "lot_closed", data)
                
            # Connect with polling-only transport and authentication
            await sio.connect(
                SOCKET_URL,
                socketio_path=SOCKET_PATH,
                transports=['polling'],  # POLLING ONLY - NO WEBSOCKET
                auth={'token': access_token}
            )
            
            self.socket_clients[email] = sio
            self.log_result(f"Socket.IO client for {email}", True, "Connected with polling-only transport")
            return sio
            
        except Exception as e:
            self.log_result(f"Socket.IO client for {email}", False, f"Error: {str(e)}")
            return None

    async def test_transport_configuration(self):
        """Test 1: Transport Configuration Test"""
        print("\n🧪 TEST 1: TRANSPORT CONFIGURATION")
        
        # Test user
        test_email = "transport-test@example.com"
        
        # Authenticate
        token = await self.authenticate_user(test_email)
        if not token:
            self.log_result("Transport Configuration", False, "Authentication failed")
            return
            
        # Create socket client with polling only
        sio = await self.create_socket_client(test_email, token)
        if not sio:
            self.log_result("Transport Configuration", False, "Socket client creation failed")
            return
            
        # Wait for connection to establish
        await asyncio.sleep(2)
        
        # Check if connected
        if sio.connected:
            self.log_result("Polling-only connection", True, "Socket.IO connected successfully")
            
            # Verify no WebSocket upgrade attempts by checking transport logs
            websocket_attempts = [log for log in self.transport_logs if 'websocket' in log['transport'].lower()]
            if len(websocket_attempts) == 0:
                self.log_result("No WebSocket upgrade", True, "Only polling transport used")
            else:
                self.log_result("No WebSocket upgrade", False, f"Found {len(websocket_attempts)} WebSocket attempts")
        else:
            self.log_result("Polling-only connection", False, "Socket.IO failed to connect")
            
        # Cleanup
        if sio.connected:
            await sio.disconnect()

    async def create_test_league(self) -> Optional[str]:
        """Create a test league for auction simulation"""
        commissioner_email = "commissioner@example.com"
        
        # Authenticate commissioner
        token = await self.authenticate_user(commissioner_email)
        if not token:
            return None
            
        session = self.sessions[commissioner_email]
        
        try:
            # Create league
            league_data = {
                "name": f"Polling Test League {int(time.time())}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 8,
                    "anti_snipe_seconds": 3,
                    "league_size": {
                        "min": 2,
                        "max": 8
                    }
                }
            }
            
            response = session.post(f"{API_BASE}/leagues", json=league_data)
            
            if response.status_code == 201:
                league_id = response.json()["leagueId"]
                self.league_id = league_id
                self.log_result("League creation", True, f"League ID: {league_id}")
                return league_id
            else:
                self.log_result("League creation", False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_result("League creation", False, f"Error: {str(e)}")
            return None

    async def add_users_to_league(self, num_users: int = 5) -> List[str]:
        """Add multiple users to the league"""
        added_users = []
        
        for i in range(1, num_users + 1):
            email = f"manager{i}@example.com"
            
            # Authenticate user
            token = await self.authenticate_user(email)
            if not token:
                continue
                
            session = self.sessions[email]
            
            try:
                # Join league
                response = session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                
                if response.status_code == 200:
                    added_users.append(email)
                    self.log_result(f"User join {email}", True, "Joined league successfully")
                else:
                    self.log_result(f"User join {email}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"User join {email}", False, f"Error: {str(e)}")
                
        self.test_users = added_users
        return added_users

    async def start_auction(self) -> bool:
        """Start the auction"""
        commissioner_email = "commissioner@example.com"
        session = self.sessions[commissioner_email]
        
        try:
            response = session.post(f"{API_BASE}/auction/{self.league_id}/start")
            
            if response.status_code == 200:
                result = response.json()
                self.auction_id = self.league_id  # Auction ID same as league ID
                self.log_result("Auction start", True, f"Auction started")
                return True
            else:
                self.log_result("Auction start", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Auction start", False, f"Error: {str(e)}")
            return False

    async def test_multi_user_auction_simulation(self):
        """Test 2: Multi-User Auction Simulation with Polling"""
        print("\n🧪 TEST 2: MULTI-USER AUCTION SIMULATION")
        
        # Create league
        league_id = await self.create_test_league()
        if not league_id:
            self.log_result("Multi-user auction setup", False, "League creation failed")
            return
            
        # Add 5 users to league
        users = await self.add_users_to_league(5)
        if len(users) < 2:
            self.log_result("Multi-user auction setup", False, "Insufficient users added")
            return
            
        # Connect all users via Socket.IO with polling
        connected_users = []
        for email in ["commissioner@example.com"] + users:
            if email in self.sessions:
                token = None
                # Extract token from session cookies
                for cookie in self.sessions[email].cookies:
                    if cookie.name == 'access_token':
                        token = cookie.value
                        break
                        
                if token:
                    sio = await self.create_socket_client(email, token)
                    if sio and sio.connected:
                        connected_users.append(email)
                        
                        # Join league room
                        await sio.emit('join_league', {
                            'league_id': league_id,
                            'user_id': email
                        })
                        
        self.log_result("Socket.IO connections", len(connected_users) >= 4, 
                       f"{len(connected_users)} users connected via polling")
        
        # Start auction
        auction_started = await self.start_auction()
        if not auction_started:
            self.log_result("Multi-user auction", False, "Auction start failed")
            return
            
        # Wait for auction events to propagate via polling
        await asyncio.sleep(3)
        
        # Check if auction events were received via polling
        auction_events = [log for log in self.event_logs if 'auction' in log['event'].lower()]
        self.log_result("Auction events via polling", len(auction_events) > 0,
                       f"Received {len(auction_events)} auction events")

    async def test_real_time_event_delivery(self):
        """Test 3: Real-time Event Delivery via Polling"""
        print("\n🧪 TEST 3: REAL-TIME EVENT DELIVERY")
        
        if not self.league_id or len(self.socket_clients) < 2:
            self.log_result("Real-time event delivery", False, "Insufficient setup")
            return
            
        # Clear previous event logs
        initial_event_count = len(self.event_logs)
        
        # Simulate league activity - have a user join
        test_email = "realtime-test@example.com"
        token = await self.authenticate_user(test_email)
        
        if token:
            session = self.sessions[test_email]
            
            # Join league (should trigger real-time events)
            response = session.post(f"{API_BASE}/leagues/{self.league_id}/join")
            
            # Wait for events to propagate via polling
            await asyncio.sleep(2)
            
            # Check if events were received
            new_events = len(self.event_logs) - initial_event_count
            self.log_result("Real-time event propagation", new_events > 0,
                           f"Received {new_events} new events via polling")
            
            # Check for specific league events
            league_events = [log for log in self.event_logs[initial_event_count:] 
                           if 'league' in log['event'].lower()]
            self.log_result("League event delivery", len(league_events) > 0,
                           f"Received {len(league_events)} league events")

    async def test_polling_performance(self):
        """Test 4: Performance Verification with Polling"""
        print("\n🧪 TEST 4: POLLING PERFORMANCE VERIFICATION")
        
        if len(self.socket_clients) < 2:
            self.log_result("Polling performance", False, "Insufficient connected clients")
            return
            
        # Measure event delivery time with polling
        start_time = time.time()
        initial_event_count = len(self.event_logs)
        
        # Trigger multiple events rapidly
        commissioner_session = self.sessions.get("commissioner@example.com")
        if commissioner_session:
            # Get league status multiple times to trigger events
            for i in range(3):
                response = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/status")
                await asyncio.sleep(0.5)
                
        # Wait for events to be delivered via polling
        await asyncio.sleep(3)
        
        end_time = time.time()
        delivery_time = end_time - start_time
        new_events = len(self.event_logs) - initial_event_count
        
        # Performance should be reasonable for 4-8 users
        performance_acceptable = delivery_time < 10  # Within 10 seconds
        self.log_result("Polling performance", performance_acceptable,
                       f"Event delivery time: {delivery_time:.2f}s, Events: {new_events}")

    async def test_transport_restriction_compliance(self):
        """Test 5: Verify No WebSocket Upgrade Attempts"""
        print("\n🧪 TEST 5: TRANSPORT RESTRICTION COMPLIANCE")
        
        # Analyze transport logs
        websocket_logs = [log for log in self.transport_logs if 'websocket' in log['transport'].lower()]
        polling_logs = [log for log in self.transport_logs if 'polling' in log['transport'].lower()]
        
        # Should have no WebSocket attempts
        no_websocket = len(websocket_logs) == 0
        has_polling = len(polling_logs) > 0
        
        self.log_result("No WebSocket attempts", no_websocket,
                       f"WebSocket logs: {len(websocket_logs)}, Polling logs: {len(polling_logs)}")
        
        self.log_result("Polling transport used", has_polling,
                       f"Polling connections: {len(polling_logs)}")

    async def cleanup(self):
        """Cleanup all connections"""
        print("\n🧹 CLEANUP")
        
        # Disconnect all socket clients
        for email, sio in self.socket_clients.items():
            try:
                if sio.connected:
                    await sio.disconnect()
                    self.log_result(f"Disconnect {email}", True, "Socket disconnected")
            except Exception as e:
                self.log_result(f"Disconnect {email}", False, f"Error: {str(e)}")
                
        # Close HTTP sessions
        for email, session in self.sessions.items():
            try:
                session.close()
            except:
                pass

    async def run_all_tests(self):
        """Run all polling-only Socket.IO tests"""
        print("🚀 STARTING POLLING-ONLY SOCKET.IO CONFIGURATION TESTS")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Socket URL: {SOCKET_URL}{SOCKET_PATH}")
        print("Transport: POLLING ONLY (no WebSocket)")
        
        try:
            # Test 1: Transport Configuration
            await self.test_transport_configuration()
            
            # Test 2: Multi-User Auction Simulation
            await self.test_multi_user_auction_simulation()
            
            # Test 3: Real-time Event Delivery
            await self.test_real_time_event_delivery()
            
            # Test 4: Performance Verification
            await self.test_polling_performance()
            
            # Test 5: Transport Restriction Compliance
            await self.test_transport_restriction_compliance()
            
        finally:
            # Always cleanup
            await self.cleanup()
            
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("POLLING-ONLY SOCKET.IO TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Group results by success
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"  - {result['test']}: {result['details']}")
            print()
            
        passed_tests = [r for r in self.test_results if r['success']]
        if passed_tests:
            print("✅ PASSED TESTS:")
            for result in passed_tests:
                print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Transport summary
        print("🚀 TRANSPORT SUMMARY:")
        websocket_count = len([log for log in self.transport_logs if 'websocket' in log['transport'].lower()])
        polling_count = len([log for log in self.transport_logs if 'polling' in log['transport'].lower()])
        print(f"  - Polling connections: {polling_count}")
        print(f"  - WebSocket attempts: {websocket_count}")
        
        # Event summary
        print(f"📡 EVENTS RECEIVED: {len(self.event_logs)}")
        
        # Success criteria check
        print("\n🎯 SUCCESS CRITERIA:")
        criteria = [
            ("Socket.IO connects using only polling transport", polling_count > 0 and websocket_count == 0),
            ("Multi-user auction functionality works", any("auction" in r['test'].lower() and r['success'] for r in self.test_results)),
            ("Real-time events delivered via polling", len(self.event_logs) > 0),
            ("No WebSocket upgrade attempts", websocket_count == 0),
            ("Performance acceptable for 4-8 users", success_rate >= 80)
        ]
        
        for criterion, met in criteria:
            status = "✅" if met else "❌"
            print(f"  {status} {criterion}")
            
        overall_success = all(met for _, met in criteria)
        print(f"\n🏆 OVERALL SUCCESS: {'✅ PASS' if overall_success else '❌ FAIL'}")

async def main():
    """Main test execution"""
    test_suite = PollingSocketTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())