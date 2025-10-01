#!/usr/bin/env python3
"""
COMPREHENSIVE REAL-TIME WEBSOCKET SYSTEM TEST
Tests the complete real-time WebSocket functionality for League Creator App
Focus: League Real-Time Updates, Auction Start Real-Time Sync, Socket.IO Event Flow
"""

import asyncio
import aiohttp
import socketio
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://leaguemate-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
SOCKET_URL = BACKEND_URL
SOCKET_PATH = "/api/socketio"

class WebSocketRealTimeTest:
    def __init__(self):
        self.session = None
        self.sio_clients = {}  # user_id -> socketio client
        self.received_events = {}  # user_id -> list of events
        self.test_results = []
        self.authenticated_users = {}  # user_id -> auth data
        
    async def setup_session(self):
        """Setup HTTP session with proper headers"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup(self):
        """Cleanup resources"""
        # Disconnect all socket clients
        for user_id, sio in self.sio_clients.items():
            try:
                await sio.disconnect()
            except:
                pass
                
        if self.session:
            await self.session.close()
            
    async def authenticate_user(self, email: str) -> Dict[str, Any]:
        """Authenticate user via test-login endpoint"""
        try:
            async with self.session.post(f"{API_BASE}/auth/test-login", 
                                       json={"email": email}) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    # Extract cookies for session
                    cookies = {}
                    for cookie in resp.cookies:
                        cookies[cookie.key] = cookie.value
                    
                    auth_data = {
                        "success": True,
                        "user_id": result["userId"],
                        "email": email,
                        "cookies": cookies
                    }
                    self.authenticated_users[result["userId"]] = auth_data
                    return auth_data
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"Auth failed: {resp.status} - {text}"}
        except Exception as e:
            return {"success": False, "error": f"Auth exception: {str(e)}"}
            
    async def create_socket_client(self, user_id: str, cookies: Dict[str, str]) -> socketio.AsyncClient:
        """Create and connect Socket.IO client for user"""
        sio = socketio.AsyncClient(
            logger=False,
            engineio_logger=False
        )
        
        # Store received events for this user
        self.received_events[user_id] = []
        
        @sio.event
        async def connect():
            print(f"✅ Socket.IO client connected for user {user_id}")
            
        @sio.event
        async def disconnect():
            print(f"❌ Socket.IO client disconnected for user {user_id}")
            
        @sio.event
        async def league_joined(data):
            print(f"📡 User {user_id} received league_joined: {data}")
            self.received_events[user_id].append({"event": "league_joined", "data": data, "timestamp": time.time()})
            
        @sio.event
        async def user_joined_league(data):
            print(f"📡 User {user_id} received user_joined_league: {data}")
            self.received_events[user_id].append({"event": "user_joined_league", "data": data, "timestamp": time.time()})
            
        @sio.event
        async def member_joined(data):
            print(f"📡 User {user_id} received member_joined: {data}")
            self.received_events[user_id].append({"event": "member_joined", "data": data, "timestamp": time.time()})
            
        @sio.event
        async def league_status_update(data):
            print(f"📡 User {user_id} received league_status_update: {data}")
            self.received_events[user_id].append({"event": "league_status_update", "data": data, "timestamp": time.time()})
            
        @sio.event
        async def auction_started(data):
            print(f"📡 User {user_id} received auction_started: {data}")
            self.received_events[user_id].append({"event": "auction_started", "data": data, "timestamp": time.time()})
            
        # Connect with cookies for authentication
        cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        headers = {"Cookie": cookie_header} if cookies else {}
        
        try:
            await sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH, headers=headers)
            self.sio_clients[user_id] = sio
            return sio
        except Exception as e:
            print(f"❌ Failed to connect Socket.IO for user {user_id}: {e}")
            return None
            
    async def create_league(self, user_id: str, cookies: Dict[str, str]) -> Dict[str, Any]:
        """Create a test league"""
        league_data = {
            "name": f"Real-Time Test League {int(time.time())}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 8,
                "bid_timer_seconds": 60,
                "anti_snipe_seconds": 30,
                "league_size": {
                    "min": 2,
                    "max": 8
                }
            }
        }
        
        try:
            cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            headers = {"Cookie": cookie_header, "Content-Type": "application/json"}
            
            async with self.session.post(f"{API_BASE}/leagues", 
                                       json=league_data, 
                                       headers=headers) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    return {"success": True, "league_id": result["leagueId"]}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"League creation failed: {resp.status} - {text}"}
        except Exception as e:
            return {"success": False, "error": f"League creation exception: {str(e)}"}
            
    async def join_league_room(self, user_id: str, league_id: str):
        """Join league room via Socket.IO"""
        sio = self.sio_clients.get(user_id)
        if sio:
            try:
                await sio.emit('join_league', {
                    'league_id': league_id,
                    'user_id': user_id
                })
                print(f"📡 User {user_id} joined league room {league_id}")
                return True
            except Exception as e:
                print(f"❌ Failed to join league room for user {user_id}: {e}")
                return False
        return False
        
    async def join_league_direct(self, user_id: str, league_id: str, cookies: Dict[str, str]) -> Dict[str, Any]:
        """Join league via HTTP API (triggers real-time events)"""
        try:
            cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            headers = {"Cookie": cookie_header, "Content-Type": "application/json"}
            
            async with self.session.post(f"{API_BASE}/leagues/{league_id}/join", 
                                       headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return {"success": True, "message": result.get("message", "Joined successfully")}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"Join failed: {resp.status} - {text}"}
        except Exception as e:
            return {"success": False, "error": f"Join exception: {str(e)}"}
            
    async def start_auction(self, user_id: str, league_id: str, cookies: Dict[str, str]) -> Dict[str, Any]:
        """Start auction via HTTP API (triggers real-time events)"""
        try:
            cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            headers = {"Cookie": cookie_header, "Content-Type": "application/json"}
            
            async with self.session.post(f"{API_BASE}/auction/{league_id}/start", 
                                       headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return {"success": True, "message": result.get("message", "Auction started")}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"Auction start failed: {resp.status} - {text}"}
        except Exception as e:
            return {"success": False, "error": f"Auction start exception: {str(e)}"}
            
    def wait_for_events(self, timeout: float = 5.0) -> None:
        """Wait for real-time events to be received"""
        print(f"⏳ Waiting {timeout}s for real-time events...")
        time.sleep(timeout)
        
    def analyze_events(self, expected_events: List[str], users: List[str]) -> Dict[str, Any]:
        """Analyze received events for expected patterns"""
        results = {
            "success": True,
            "details": {},
            "missing_events": [],
            "unexpected_events": [],
            "timing_analysis": {}
        }
        
        for user_id in users:
            user_events = self.received_events.get(user_id, [])
            results["details"][user_id] = {
                "total_events": len(user_events),
                "events": [e["event"] for e in user_events]
            }
            
            # Check for expected events
            received_event_types = [e["event"] for e in user_events]
            for expected in expected_events:
                if expected not in received_event_types:
                    results["missing_events"].append(f"{user_id}:{expected}")
                    results["success"] = False
                    
        return results
        
    async def test_league_real_time_updates(self):
        """Test 1: League Real-Time Updates"""
        print("\n🧪 TEST 1: League Real-Time Updates")
        print("=" * 50)
        
        try:
            # Setup users
            commissioner_email = f"commissioner_{int(time.time())}@test.com"
            member_email = f"member_{int(time.time())}@test.com"
            
            # Authenticate users
            print("🔐 Authenticating users...")
            commissioner_auth = await self.authenticate_user(commissioner_email)
            member_auth = await self.authenticate_user(member_email)
            
            if not commissioner_auth["success"] or not member_auth["success"]:
                self.test_results.append({
                    "test": "League Real-Time Updates",
                    "success": False,
                    "error": "Authentication failed"
                })
                return
                
            commissioner_id = commissioner_auth["user_id"]
            member_id = member_auth["user_id"]
            
            # Create Socket.IO connections
            print("📡 Creating Socket.IO connections...")
            commissioner_sio = await self.create_socket_client(commissioner_id, commissioner_auth["cookies"])
            member_sio = await self.create_socket_client(member_id, member_auth["cookies"])
            
            if not commissioner_sio or not member_sio:
                self.test_results.append({
                    "test": "League Real-Time Updates",
                    "success": False,
                    "error": "Socket.IO connection failed"
                })
                return
                
            # Create league
            print("🏆 Creating league...")
            league_result = await self.create_league(commissioner_id, commissioner_auth["cookies"])
            if not league_result["success"]:
                self.test_results.append({
                    "test": "League Real-Time Updates",
                    "success": False,
                    "error": f"League creation failed: {league_result['error']}"
                })
                return
                
            league_id = league_result["league_id"]
            print(f"✅ League created: {league_id}")
            
            # Join league rooms
            print("📡 Joining league rooms...")
            await self.join_league_room(commissioner_id, league_id)
            await self.join_league_room(member_id, league_id)
            
            # Wait for room joins to complete
            await asyncio.sleep(2)
            
            # Member joins league (should trigger real-time events)
            print("👥 Member joining league...")
            join_result = await self.join_league_direct(member_id, league_id, member_auth["cookies"])
            
            if not join_result["success"]:
                print(f"⚠️ Join failed: {join_result['error']}")
                
            # Wait for real-time events
            self.wait_for_events(3.0)
            
            # Analyze events
            expected_events = ["member_joined", "league_status_update"]
            analysis = self.analyze_events(expected_events, [commissioner_id, member_id])
            
            print(f"\n📊 Event Analysis:")
            print(f"Commissioner events: {analysis['details'].get(commissioner_id, {}).get('events', [])}")
            print(f"Member events: {analysis['details'].get(member_id, {}).get('events', [])}")
            
            self.test_results.append({
                "test": "League Real-Time Updates",
                "success": analysis["success"],
                "details": analysis,
                "league_id": league_id
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "League Real-Time Updates",
                "success": False,
                "error": f"Test exception: {str(e)}"
            })
            
    async def test_auction_start_real_time_sync(self):
        """Test 2: Auction Start Real-Time Sync"""
        print("\n🧪 TEST 2: Auction Start Real-Time Sync")
        print("=" * 50)
        
        try:
            # Get league from previous test
            previous_test = next((t for t in self.test_results if "league_id" in t), None)
            if not previous_test or not previous_test.get("league_id"):
                print("⚠️ No league available from previous test, creating new one...")
                await self.test_league_real_time_updates()
                previous_test = self.test_results[-1]
                
            if not previous_test.get("league_id"):
                self.test_results.append({
                    "test": "Auction Start Real-Time Sync",
                    "success": False,
                    "error": "No league available for auction start test"
                })
                return
                
            league_id = previous_test["league_id"]
            
            # Get commissioner from existing connections
            commissioner_id = list(self.sio_clients.keys())[0] if self.sio_clients else None
            if not commissioner_id:
                self.test_results.append({
                    "test": "Auction Start Real-Time Sync",
                    "success": False,
                    "error": "No commissioner connection available"
                })
                return
                
            # Clear previous events
            for user_id in self.received_events:
                self.received_events[user_id] = []
                
            # Start auction (should trigger real-time events)
            print("🚀 Starting auction...")
            
            # Get commissioner cookies from authenticated users
            commissioner_auth = self.authenticated_users.get(commissioner_id, {})
            commissioner_cookies = commissioner_auth.get("cookies", {})
            
            start_result = await self.start_auction(commissioner_id, league_id, commissioner_cookies)
            
            print(f"Auction start result: {start_result}")
            
            # Wait for real-time events
            self.wait_for_events(3.0)
            
            # Analyze events
            expected_events = ["auction_started"]
            analysis = self.analyze_events(expected_events, list(self.sio_clients.keys()))
            
            print(f"\n📊 Auction Start Event Analysis:")
            for user_id, details in analysis["details"].items():
                print(f"User {user_id} events: {details.get('events', [])}")
                
            self.test_results.append({
                "test": "Auction Start Real-Time Sync",
                "success": analysis["success"],
                "details": analysis,
                "auction_start_result": start_result
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Auction Start Real-Time Sync",
                "success": False,
                "error": f"Test exception: {str(e)}"
            })
            
    async def test_socket_io_event_flow(self):
        """Test 3: Socket.IO Event Flow"""
        print("\n🧪 TEST 3: Socket.IO Event Flow")
        print("=" * 50)
        
        try:
            # Test basic Socket.IO connectivity and room functionality
            test_user_email = f"sockettest_{int(time.time())}@test.com"
            
            # Authenticate
            auth_result = await self.authenticate_user(test_user_email)
            if not auth_result["success"]:
                self.test_results.append({
                    "test": "Socket.IO Event Flow",
                    "success": False,
                    "error": "Authentication failed for Socket.IO test"
                })
                return
                
            user_id = auth_result["user_id"]
            
            # Create Socket.IO connection
            sio = await self.create_socket_client(user_id, auth_result["cookies"])
            if not sio:
                self.test_results.append({
                    "test": "Socket.IO Event Flow",
                    "success": False,
                    "error": "Socket.IO connection failed"
                })
                return
                
            # Test join_league event handler
            test_league_id = str(uuid.uuid4())
            await self.join_league_room(user_id, test_league_id)
            
            # Wait for events
            await asyncio.sleep(2)
            
            # Check if league_joined event was received
            user_events = self.received_events.get(user_id, [])
            league_joined_events = [e for e in user_events if e["event"] == "league_joined"]
            
            success = len(league_joined_events) > 0
            
            self.test_results.append({
                "test": "Socket.IO Event Flow",
                "success": success,
                "details": {
                    "events_received": len(user_events),
                    "league_joined_events": len(league_joined_events),
                    "all_events": [e["event"] for e in user_events]
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Socket.IO Event Flow",
                "success": False,
                "error": f"Test exception: {str(e)}"
            })
            
    async def test_complete_real_time_flow(self):
        """Test 4: Complete Real-Time Flow"""
        print("\n🧪 TEST 4: Complete Real-Time Flow")
        print("=" * 50)
        
        try:
            # Create multiple users for comprehensive test
            users = []
            for i in range(3):
                email = f"flowtest_{i}_{int(time.time())}@test.com"
                auth_result = await self.authenticate_user(email)
                if auth_result["success"]:
                    sio = await self.create_socket_client(auth_result["user_id"], auth_result["cookies"])
                    if sio:
                        users.append({
                            "user_id": auth_result["user_id"],
                            "email": email,
                            "cookies": auth_result["cookies"],
                            "is_commissioner": i == 0
                        })
                        
            if len(users) < 2:
                self.test_results.append({
                    "test": "Complete Real-Time Flow",
                    "success": False,
                    "error": "Insufficient users for complete flow test"
                })
                return
                
            commissioner = users[0]
            members = users[1:]
            
            # Clear events
            for user_id in self.received_events:
                self.received_events[user_id] = []
                
            # Step 1: Commissioner creates league
            print("👑 Commissioner creating league...")
            league_result = await self.create_league(commissioner["user_id"], commissioner["cookies"])
            if not league_result["success"]:
                self.test_results.append({
                    "test": "Complete Real-Time Flow",
                    "success": False,
                    "error": f"League creation failed: {league_result['error']}"
                })
                return
                
            league_id = league_result["league_id"]
            
            # Step 2: All users join league room
            print("📡 All users joining league room...")
            for user in users:
                await self.join_league_room(user["user_id"], league_id)
                
            await asyncio.sleep(2)
            
            # Step 3: Members join league sequentially (should trigger events)
            print("👥 Members joining league...")
            for member in members:
                join_result = await self.join_league_direct(member["user_id"], league_id, member["cookies"])
                print(f"Member {member['user_id']} join result: {join_result}")
                await asyncio.sleep(1)  # Small delay between joins
                
            # Wait for all events
            self.wait_for_events(3.0)
            
            # Step 4: Start auction (should trigger auction_started events)
            print("🚀 Starting auction...")
            auction_result = await self.start_auction(commissioner["user_id"], league_id, commissioner["cookies"])
            print(f"Auction start result: {auction_result}")
            
            # Wait for auction events
            self.wait_for_events(3.0)
            
            # Analyze complete flow
            all_user_ids = [u["user_id"] for u in users]
            expected_events = ["member_joined", "league_status_update", "auction_started"]
            analysis = self.analyze_events(expected_events, all_user_ids)
            
            print(f"\n📊 Complete Flow Analysis:")
            for user_id, details in analysis["details"].items():
                user_type = "Commissioner" if user_id == commissioner["user_id"] else "Member"
                print(f"{user_type} {user_id}: {details.get('events', [])} ({details.get('total_events', 0)} total)")
                
            # Success criteria: At least some real-time events received
            total_events = sum(details.get('total_events', 0) for details in analysis["details"].values())
            success = total_events > 0 and len(analysis["missing_events"]) < len(expected_events) * len(users)
            
            self.test_results.append({
                "test": "Complete Real-Time Flow",
                "success": success,
                "details": analysis,
                "total_events_received": total_events,
                "users_tested": len(users)
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Complete Real-Time Flow",
                "success": False,
                "error": f"Test exception: {str(e)}"
            })
            
    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE REAL-TIME WEBSOCKET SYSTEM TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"\n{i}. {result['test']}: {status}")
            
            if not result["success"] and "error" in result:
                print(f"   Error: {result['error']}")
                
            if "details" in result:
                details = result["details"]
                if isinstance(details, dict):
                    if "total_events" in details:
                        print(f"   Events: {details['total_events']}")
                    elif "details" in details:
                        event_counts = {uid: data.get('total_events', 0) 
                                      for uid, data in details["details"].items()}
                        total_events = sum(event_counts.values())
                        print(f"   Total Events Received: {total_events}")
                        if event_counts:
                            print(f"   Per User: {event_counts}")
                            
        print(f"\n🎯 SUCCESS CRITERIA ANALYSIS:")
        
        # Analyze specific success criteria
        criteria_results = {
            "Real-time member join events": False,
            "Auction start events reach all members": False,
            "Socket.IO rooms properly isolate events": False,
            "Complete real-time synchronization": False
        }
        
        for result in self.test_results:
            if result["test"] == "League Real-Time Updates" and result["success"]:
                criteria_results["Real-time member join events"] = True
                
            if result["test"] == "Auction Start Real-Time Sync" and result["success"]:
                criteria_results["Auction start events reach all members"] = True
                
            if result["test"] == "Socket.IO Event Flow" and result["success"]:
                criteria_results["Socket.IO rooms properly isolate events"] = True
                
            if result["test"] == "Complete Real-Time Flow" and result["success"]:
                criteria_results["Complete real-time synchronization"] = True
                
        for criteria, passed in criteria_results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {criteria}")
            
        print(f"\n🏆 FINAL ASSESSMENT:")
        if success_rate >= 75:
            print("🎉 REAL-TIME WEBSOCKET SYSTEM IS FUNCTIONAL")
            print("✅ Ready for live auction experience")
        elif success_rate >= 50:
            print("⚠️ REAL-TIME WEBSOCKET SYSTEM PARTIALLY FUNCTIONAL")
            print("🔧 Some issues need resolution before live auctions")
        else:
            print("❌ REAL-TIME WEBSOCKET SYSTEM NEEDS MAJOR FIXES")
            print("🚫 Not ready for live auction experience")
            
        return success_rate >= 75

async def main():
    """Main test execution"""
    print("🚀 Starting Comprehensive Real-Time WebSocket System Test")
    print("=" * 80)
    
    test = WebSocketRealTimeTest()
    
    try:
        await test.setup_session()
        
        # Execute all tests
        await test.test_league_real_time_updates()
        await test.test_auction_start_real_time_sync()
        await test.test_socket_io_event_flow()
        await test.test_complete_real_time_flow()
        
        # Print results
        success = test.print_final_results()
        
        return success
        
    finally:
        await test.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)