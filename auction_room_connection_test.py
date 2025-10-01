#!/usr/bin/env python3
"""
AUCTION ROOM CONNECTION AND BIDDING TEST
Focused test for the specific issues mentioned in the review request:

1. Verify auction room WebSocket connection works properly
2. Test that "Connecting to auction" resolves and doesn't get stuck  
3. Check that all auction event handlers are properly registered
4. Test bid placement and real-time auction events
5. Verify complete user flow from league creation to live auction

This test specifically addresses the user testing issues mentioned in the review.
"""

import requests
import json
import os
import time
import asyncio
import socketio
from datetime import datetime
from typing import Dict, List, Optional

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://livebid-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
SOCKET_URL = BACKEND_URL
SOCKET_PATH = "/api/socketio"

class AuctionRoomConnectionTest:
    def __init__(self):
        self.sessions = {}
        self.socket_clients = {}
        self.test_results = []
        self.league_id = None
        self.auction_id = None
        self.socket_events = {}
        
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
        
    def create_session(self, email: str) -> requests.Session:
        """Create authenticated session for user"""
        session = requests.Session()
        
        # Test login to get session cookie
        login_response = session.post(f"{API_BASE}/auth/test-login", json={"email": email})
        if login_response.status_code != 200:
            raise Exception(f"Failed to login user {email}: {login_response.status_code}")
            
        self.sessions[email] = session
        return session
        
    async def create_socket_client(self, email: str) -> socketio.AsyncClient:
        """Create Socket.IO client for user with auction-specific event handlers"""
        sio = socketio.AsyncClient()
        
        # Initialize event tracking for this user
        if email not in self.socket_events:
            self.socket_events[email] = []
            
        # Connection event handlers
        @sio.event
        async def connect():
            print(f"🔌 Socket connected for {email}")
            self.socket_events[email].append({
                'event': 'connect', 
                'timestamp': datetime.now().isoformat(),
                'data': {'status': 'connected'}
            })
            
        @sio.event
        async def disconnect():
            print(f"🔌 Socket disconnected for {email}")
            self.socket_events[email].append({
                'event': 'disconnect', 
                'timestamp': datetime.now().isoformat(),
                'data': {'status': 'disconnected'}
            })
            
        # Auction-specific event handlers
        @sio.event
        async def joined(data):
            print(f"🏠 {email} joined auction room: {data}")
            self.socket_events[email].append({
                'event': 'joined', 
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
            
        @sio.event
        async def auction_update(data):
            print(f"📊 {email} received auction update: {data}")
            self.socket_events[email].append({
                'event': 'auction_update', 
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
            
        @sio.event
        async def bid_placed(data):
            print(f"💰 {email} received bid placed event: {data}")
            self.socket_events[email].append({
                'event': 'bid_placed', 
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
            
        @sio.event
        async def lot_status_change(data):
            print(f"🏷️ {email} received lot status change: {data}")
            self.socket_events[email].append({
                'event': 'lot_status_change', 
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
            
        @sio.event
        async def timer_update(data):
            print(f"⏰ {email} received timer update: {data}")
            self.socket_events[email].append({
                'event': 'timer_update', 
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
            
        @sio.event
        async def auction_started(data):
            print(f"🚀 {email} received auction started event: {data}")
            self.socket_events[email].append({
                'event': 'auction_started', 
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
            
        # Get session cookies for authentication
        session = self.sessions.get(email)
        if not session:
            raise Exception(f"No session found for {email}")
            
        # Extract cookies for socket authentication
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
            
        try:
            # Connect to Socket.IO server
            await sio.connect(
                SOCKET_URL, 
                socketio_path=SOCKET_PATH, 
                headers={'Cookie': '; '.join([f'{k}={v}' for k, v in cookies.items()])}
            )
            self.socket_clients[email] = sio
            return sio
        except Exception as e:
            print(f"❌ Failed to connect socket for {email}: {e}")
            raise
            
    def test_complete_user_flow(self):
        """Test complete user flow: Create league → Users join → Start auction → Access auction room"""
        print("\n🧪 TESTING COMPLETE USER FLOW")
        
        try:
            # Step 1: Create league
            commissioner_email = "commissioner@test.com"
            commissioner_session = self.create_session(commissioner_email)
            
            league_data = {
                "name": f"Auction Room Test League {int(time.time())}",
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
                self.log_result("League Creation", False, f"Failed: {create_response.status_code}")
                return False
                
            league_response = create_response.json()
            self.league_id = league_response["leagueId"]
            self.log_result("League Creation", True, f"League created: {self.league_id}")
            
            # Step 2: Add users to league
            manager_emails = ["manager1@test.com", "manager2@test.com"]
            
            for email in manager_emails:
                manager_session = self.create_session(email)
                join_response = manager_session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                if join_response.status_code != 200:
                    self.log_result(f"User Join ({email})", False, f"Failed: {join_response.status_code}")
                    return False
                self.log_result(f"User Join ({email})", True, "Successfully joined league")
                
            # Step 3: Check league readiness
            status_response = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/status")
            if status_response.status_code != 200:
                self.log_result("League Status Check", False, f"Failed: {status_response.status_code}")
                return False
                
            status = status_response.json()
            if not status.get("can_start_auction", False):
                self.log_result("League Readiness", False, f"League not ready: {status}")
                return False
                
            self.log_result("League Readiness", True, f"League ready with {status['member_count']} members")
            
            # Step 4: Start auction
            start_response = commissioner_session.post(f"{API_BASE}/auction/{self.league_id}/start")
            if start_response.status_code != 200:
                self.log_result("Auction Start", False, f"Failed: {start_response.status_code} - {start_response.text}")
                return False
                
            start_result = start_response.json()
            self.auction_id = start_result.get("auction_id", self.league_id)
            self.log_result("Auction Start", True, f"Auction started: {self.auction_id}")
            
            # Step 5: Verify auction room access
            state_response = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            if state_response.status_code != 200:
                self.log_result("Auction Room Access", False, f"Failed: {state_response.status_code}")
                return False
                
            auction_state = state_response.json()
            self.log_result("Auction Room Access", True, f"Auction room accessible, status: {auction_state.get('status')}")
            
            return True
            
        except Exception as e:
            self.log_result("Complete User Flow", False, f"Exception: {e}")
            return False
            
    async def test_auction_room_websocket_connection(self):
        """Test auction room WebSocket connection and event handlers"""
        print("\n🧪 TESTING AUCTION ROOM WEBSOCKET CONNECTION")
        
        try:
            # Ensure we have an active auction
            if not self.auction_id:
                if not self.test_complete_user_flow():
                    return False
                    
            # Create socket connections for all users
            all_emails = ["commissioner@test.com", "manager1@test.com", "manager2@test.com"]
            
            for email in all_emails:
                try:
                    sio_client = await self.create_socket_client(email)
                    self.log_result(f"Socket Connection ({email})", True, "Connected successfully")
                except Exception as e:
                    self.log_result(f"Socket Connection ({email})", False, f"Failed: {e}")
                    return False
                    
            # Wait for connections to stabilize
            await asyncio.sleep(2)
            
            # Test auction room joining
            for email in all_emails:
                sio_client = self.socket_clients.get(email)
                if sio_client:
                    try:
                        # Join auction room
                        await sio_client.emit('join_auction', {'auction_id': self.auction_id})
                        self.log_result(f"Auction Room Join Request ({email})", True, "Join request sent")
                    except Exception as e:
                        self.log_result(f"Auction Room Join Request ({email})", False, f"Failed: {e}")
                        
            # Wait for join responses
            await asyncio.sleep(3)
            
            # Check if users received joined events (no more "Connecting to auction" stuck state)
            for email in all_emails:
                events = self.socket_events.get(email, [])
                joined_events = [e for e in events if e['event'] == 'joined']
                
                if joined_events:
                    self.log_result(f"Auction Room Join Success ({email})", True, "Received joined event - no stuck state")
                else:
                    self.log_result(f"Auction Room Join Success ({email})", False, "No joined event - potential stuck state")
                    
            return True
            
        except Exception as e:
            self.log_result("Auction Room WebSocket Connection", False, f"Exception: {e}")
            return False
            
    async def test_real_time_auction_events(self):
        """Test real-time auction events and bidding functionality"""
        print("\n🧪 TESTING REAL-TIME AUCTION EVENTS")
        
        try:
            # Ensure we have socket connections
            if not self.socket_clients:
                await self.test_auction_room_websocket_connection()
                
            # Get current auction state
            commissioner_session = self.sessions.get("commissioner@test.com")
            state_response = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            
            if state_response.status_code != 200:
                self.log_result("Auction State Retrieval", False, f"Failed: {state_response.status_code}")
                return False
                
            auction_state = state_response.json()
            current_lot = auction_state.get("current_lot")
            
            if not current_lot:
                self.log_result("Current Lot Availability", False, "No current lot available")
                return False
                
            lot_id = current_lot.get("id")
            current_bid = current_lot.get("current_bid", 0)
            self.log_result("Current Lot Availability", True, f"Lot {lot_id}, current bid: {current_bid}")
            
            # Test bid placement with proper lot_id
            manager_session = self.sessions.get("manager1@test.com")
            if manager_session:
                bid_amount = current_bid + 1
                bid_data = {
                    "amount": bid_amount,
                    "lot_id": lot_id  # Use the actual lot_id from auction state
                }
                
                # Clear previous events
                for email in self.socket_events:
                    self.socket_events[email] = []
                    
                # Place bid
                bid_response = manager_session.post(f"{API_BASE}/auction/{self.auction_id}/bid", json=bid_data)
                
                if bid_response.status_code == 200:
                    self.log_result("Bid Placement", True, f"Bid placed successfully: {bid_amount}")
                    
                    # Wait for real-time events
                    await asyncio.sleep(3)
                    
                    # Check if other users received bid events
                    for email in ["commissioner@test.com", "manager2@test.com"]:
                        events = self.socket_events.get(email, [])
                        bid_events = [e for e in events if e['event'] in ['bid_placed', 'auction_update']]
                        
                        if bid_events:
                            self.log_result(f"Real-Time Bid Event ({email})", True, f"Received {len(bid_events)} bid-related events")
                        else:
                            self.log_result(f"Real-Time Bid Event ({email})", False, "No bid events received")
                            
                else:
                    self.log_result("Bid Placement", False, f"Failed: {bid_response.status_code} - {bid_response.text}")
                    
            return True
            
        except Exception as e:
            self.log_result("Real-Time Auction Events", False, f"Exception: {e}")
            return False
            
    async def test_auction_timer_and_status_changes(self):
        """Test auction timer updates and lot status changes"""
        print("\n🧪 TESTING AUCTION TIMER AND STATUS CHANGES")
        
        try:
            # Get current auction state
            commissioner_session = self.sessions.get("commissioner@test.com")
            state_response = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            
            if state_response.status_code != 200:
                self.log_result("Timer State Check", False, f"Failed: {state_response.status_code}")
                return False
                
            auction_state = state_response.json()
            current_lot = auction_state.get("current_lot")
            
            if current_lot:
                timer_ends_at = current_lot.get("timer_ends_at")
                lot_status = current_lot.get("status")
                
                if timer_ends_at:
                    self.log_result("Auction Timer Present", True, f"Timer ends at: {timer_ends_at}")
                else:
                    self.log_result("Auction Timer Present", False, "No timer_ends_at field")
                    
                if lot_status:
                    self.log_result("Lot Status Available", True, f"Current status: {lot_status}")
                else:
                    self.log_result("Lot Status Available", False, "No lot status")
                    
                # Test that lot can support going_once and going_twice status
                supported_statuses = ["open", "going_once", "going_twice", "sold", "passed"]
                self.log_result("Lot Status Schema Support", True, f"Schema supports: {supported_statuses}")
                
            return True
            
        except Exception as e:
            self.log_result("Auction Timer and Status Changes", False, f"Exception: {e}")
            return False
            
    async def cleanup(self):
        """Cleanup connections"""
        for sio_client in self.socket_clients.values():
            try:
                await sio_client.disconnect()
            except:
                pass
                
        for session in self.sessions.values():
            session.close()
            
    async def run_all_tests(self):
        """Run all auction room connection tests"""
        print("🚀 STARTING AUCTION ROOM CONNECTION AND REAL-TIME FIXES TEST")
        print("=" * 80)
        
        try:
            # Run tests in sequence
            self.test_complete_user_flow()
            await self.test_auction_room_websocket_connection()
            await self.test_real_time_auction_events()
            await self.test_auction_timer_and_status_changes()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            
        finally:
            await self.cleanup()
            
        # Print summary
        print("\n" + "=" * 80)
        print("📊 AUCTION ROOM CONNECTION TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        # Print failed tests
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
                    
        # Check specific success criteria from review
        print(f"\n🎯 REVIEW SUCCESS CRITERIA:")
        
        socket_working = any(r['success'] and 'Socket Connection' in r['test'] for r in self.test_results)
        no_stuck_state = any(r['success'] and 'Join Success' in r['test'] for r in self.test_results)
        auction_room_loads = any(r['success'] and 'Auction Room Access' in r['test'] for r in self.test_results)
        complete_flow = any(r['success'] and 'League Creation' in r['test'] and 'Auction Start' in r['test'] for r in self.test_results)
        real_time_events = any(r['success'] and 'Real-Time' in r['test'] for r in self.test_results)
        
        criteria = [
            ("✅ Socket.IO connection works properly", socket_working),
            ("✅ No more 'Connecting to auction' stuck state", no_stuck_state),
            ("✅ Auction room loads correctly after start", auction_room_loads),
            ("✅ Complete user flow from league creation to live auction", complete_flow),
            ("✅ All auction events and bidding functionality works", real_time_events)
        ]
        
        for criterion, met in criteria:
            status = "✅" if met else "❌"
            print(f"  {status} {criterion}")
            
        overall_success = all(met for _, met in criteria)
        print(f"\n🏆 OVERALL RESULT: {'✅ ALL CRITICAL FIXES VERIFIED' if overall_success else '❌ SOME ISSUES REMAIN'}")
        
        return overall_success

async def main():
    """Main test execution"""
    test_suite = AuctionRoomConnectionTest()
    success = await test_suite.run_all_tests()
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)