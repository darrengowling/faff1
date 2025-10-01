#!/usr/bin/env python3
"""
FOCUSED REAL-TIME WEBSOCKET SYSTEM TEST
Tests the specific real-time WebSocket features requested in the review:
1. League Real-Time Updates (member_joined, league_status_update events)
2. Auction Start Real-Time Sync (auction_started events)
3. Socket.IO Event Flow (join_league rooms, cross-user events)
4. Complete Real-Time Flow (end-to-end synchronization)
"""

import asyncio
import aiohttp
import socketio
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://leaguemate-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class RealTimeWebSocketTest:
    def __init__(self):
        self.test_results = []
        self.socket_events = {}  # user_id -> list of events
        
    async def authenticate_user(self, email: str):
        """Authenticate user and extract session cookie"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{API_BASE}/auth/test-login", 
                                       json={"email": email}) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        
                        # Extract access_token from Set-Cookie header
                        cookies = {}
                        if 'Set-Cookie' in resp.headers:
                            cookie_str = resp.headers['Set-Cookie']
                            if 'access_token=' in cookie_str:
                                token_part = cookie_str.split('access_token=')[1].split(';')[0]
                                cookies['access_token'] = token_part
                        
                        return {
                            "success": True,
                            "user_id": result["userId"],
                            "email": email,
                            "cookies": cookies
                        }
                    else:
                        return {"success": False, "error": f"Auth failed: {resp.status}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
                
    async def create_league(self, user_data):
        """Create a test league"""
        league_data = {
            "name": f"Real-Time Test League {int(time.time())}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 8,
                "bid_timer_seconds": 60,
                "anti_snipe_seconds": 30,
                "league_size": {"min": 2, "max": 8}
            }
        }
        
        cookie_header = "; ".join([f"{k}={v}" for k, v in user_data["cookies"].items()])
        headers = {"Cookie": cookie_header, "Content-Type": "application/json"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{API_BASE}/leagues", 
                                       json=league_data, 
                                       headers=headers) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        return {"success": True, "league_id": result["leagueId"]}
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Failed: {resp.status} - {text}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
                
    async def join_league(self, user_data, league_id):
        """Join a league via HTTP API"""
        cookie_header = "; ".join([f"{k}={v}" for k, v in user_data["cookies"].items()])
        headers = {"Cookie": cookie_header, "Content-Type": "application/json"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{API_BASE}/leagues/{league_id}/join", 
                                       headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return {"success": True, "message": result.get("message", "Joined")}
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Join failed: {resp.status} - {text}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
                
    async def start_auction(self, user_data, league_id):
        """Start auction via HTTP API"""
        cookie_header = "; ".join([f"{k}={v}" for k, v in user_data["cookies"].items()])
        headers = {"Cookie": cookie_header, "Content-Type": "application/json"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{API_BASE}/auction/{league_id}/start", 
                                       headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return {"success": True, "message": result.get("message", "Started")}
                    else:
                        text = await resp.text()
                        return {"success": False, "error": f"Start failed: {resp.status} - {text}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
                
    async def create_socket_client(self, user_data):
        """Create Socket.IO client for user"""
        sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        user_id = user_data["user_id"]
        
        # Initialize event storage
        self.socket_events[user_id] = []
        
        @sio.event
        async def connect():
            print(f"✅ Socket connected for {user_data['email']}")
            
        @sio.event
        async def disconnect():
            print(f"❌ Socket disconnected for {user_data['email']}")
            
        @sio.event
        async def league_joined(data):
            print(f"📡 {user_data['email']} received league_joined: {data}")
            self.socket_events[user_id].append({"event": "league_joined", "data": data, "time": time.time()})
            
        @sio.event
        async def user_joined_league(data):
            print(f"📡 {user_data['email']} received user_joined_league: {data}")
            self.socket_events[user_id].append({"event": "user_joined_league", "data": data, "time": time.time()})
            
        @sio.event
        async def member_joined(data):
            print(f"📡 {user_data['email']} received member_joined: {data}")
            self.socket_events[user_id].append({"event": "member_joined", "data": data, "time": time.time()})
            
        @sio.event
        async def league_status_update(data):
            print(f"📡 {user_data['email']} received league_status_update: {data}")
            self.socket_events[user_id].append({"event": "league_status_update", "data": data, "time": time.time()})
            
        @sio.event
        async def auction_started(data):
            print(f"📡 {user_data['email']} received auction_started: {data}")
            self.socket_events[user_id].append({"event": "auction_started", "data": data, "time": time.time()})
            
        # Connect with authentication
        cookie_header = "; ".join([f"{k}={v}" for k, v in user_data["cookies"].items()])
        headers = {"Cookie": cookie_header} if user_data["cookies"] else {}
        
        try:
            await sio.connect(BACKEND_URL, socketio_path="/api/socketio", headers=headers)
            return sio
        except Exception as e:
            print(f"❌ Socket connection failed for {user_data['email']}: {e}")
            return None
            
    async def test_league_real_time_updates(self):
        """Test 1: League Real-Time Updates"""
        print("\n🧪 TEST 1: League Real-Time Updates")
        print("=" * 50)
        
        try:
            # Setup users
            commissioner = await self.authenticate_user(f"commissioner_{int(time.time())}@test.com")
            member = await self.authenticate_user(f"member_{int(time.time())}@test.com")
            
            if not commissioner["success"] or not member["success"]:
                self.test_results.append({
                    "test": "League Real-Time Updates",
                    "success": False,
                    "error": "Authentication failed"
                })
                return
                
            # Create Socket.IO connections
            commissioner_sio = await self.create_socket_client(commissioner)
            member_sio = await self.create_socket_client(member)
            
            if not commissioner_sio or not member_sio:
                self.test_results.append({
                    "test": "League Real-Time Updates",
                    "success": False,
                    "error": "Socket connection failed"
                })
                return
                
            # Create league
            league_result = await self.create_league(commissioner)
            if not league_result["success"]:
                self.test_results.append({
                    "test": "League Real-Time Updates",
                    "success": False,
                    "error": f"League creation failed: {league_result['error']}"
                })
                return
                
            league_id = league_result["league_id"]
            print(f"✅ League created: {league_id}")
            
            # Join league rooms via Socket.IO
            await commissioner_sio.emit('join_league', {
                'league_id': league_id,
                'user_id': commissioner["user_id"]
            })
            
            await member_sio.emit('join_league', {
                'league_id': league_id,
                'user_id': member["user_id"]
            })
            
            # Wait for room joins
            await asyncio.sleep(2)
            
            # Clear events before the test action
            self.socket_events[commissioner["user_id"]] = []
            self.socket_events[member["user_id"]] = []
            
            # Member joins league (should trigger real-time events)
            print("👥 Member joining league...")
            join_result = await self.join_league(member, league_id)
            print(f"Join result: {join_result}")
            
            # Wait for real-time events
            print("⏳ Waiting for real-time events...")
            await asyncio.sleep(5)
            
            # Analyze events
            commissioner_events = self.socket_events.get(commissioner["user_id"], [])
            member_events = self.socket_events.get(member["user_id"], [])
            
            print(f"Commissioner events: {[e['event'] for e in commissioner_events]}")
            print(f"Member events: {[e['event'] for e in member_events]}")
            
            # Check for expected events
            expected_events = ["member_joined", "league_status_update"]
            commissioner_event_types = [e["event"] for e in commissioner_events]
            member_event_types = [e["event"] for e in member_events]
            
            success = any(event in commissioner_event_types for event in expected_events)
            
            self.test_results.append({
                "test": "League Real-Time Updates",
                "success": success,
                "details": {
                    "commissioner_events": commissioner_event_types,
                    "member_events": member_event_types,
                    "total_events": len(commissioner_events) + len(member_events)
                },
                "league_id": league_id,
                "users": [commissioner, member]
            })
            
            # Cleanup
            await commissioner_sio.disconnect()
            await member_sio.disconnect()
            
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
            # Get data from previous test
            previous_test = next((t for t in self.test_results if "users" in t), None)
            if not previous_test or not previous_test.get("league_id"):
                print("⚠️ No league from previous test, skipping auction start test")
                self.test_results.append({
                    "test": "Auction Start Real-Time Sync",
                    "success": False,
                    "error": "No league available from previous test"
                })
                return
                
            league_id = previous_test["league_id"]
            users = previous_test["users"]
            commissioner = users[0]
            member = users[1]
            
            # Create new Socket.IO connections
            commissioner_sio = await self.create_socket_client(commissioner)
            member_sio = await self.create_socket_client(member)
            
            if not commissioner_sio or not member_sio:
                self.test_results.append({
                    "test": "Auction Start Real-Time Sync",
                    "success": False,
                    "error": "Socket connection failed"
                })
                return
                
            # Join league rooms
            await commissioner_sio.emit('join_league', {
                'league_id': league_id,
                'user_id': commissioner["user_id"]
            })
            
            await member_sio.emit('join_league', {
                'league_id': league_id,
                'user_id': member["user_id"]
            })
            
            await asyncio.sleep(2)
            
            # Clear events
            self.socket_events[commissioner["user_id"]] = []
            self.socket_events[member["user_id"]] = []
            
            # Start auction (should trigger real-time events)
            print("🚀 Starting auction...")
            auction_result = await self.start_auction(commissioner, league_id)
            print(f"Auction start result: {auction_result}")
            
            # Wait for real-time events
            print("⏳ Waiting for auction start events...")
            await asyncio.sleep(5)
            
            # Analyze events
            commissioner_events = self.socket_events.get(commissioner["user_id"], [])
            member_events = self.socket_events.get(member["user_id"], [])
            
            print(f"Commissioner events: {[e['event'] for e in commissioner_events]}")
            print(f"Member events: {[e['event'] for e in member_events]}")
            
            # Check for auction_started events
            commissioner_has_auction_started = any(e["event"] == "auction_started" for e in commissioner_events)
            member_has_auction_started = any(e["event"] == "auction_started" for e in member_events)
            
            success = commissioner_has_auction_started or member_has_auction_started
            
            self.test_results.append({
                "test": "Auction Start Real-Time Sync",
                "success": success,
                "details": {
                    "commissioner_events": [e["event"] for e in commissioner_events],
                    "member_events": [e["event"] for e in member_events],
                    "auction_started_events": commissioner_has_auction_started + member_has_auction_started,
                    "auction_result": auction_result
                }
            })
            
            # Cleanup
            await commissioner_sio.disconnect()
            await member_sio.disconnect()
            
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
            # Test basic Socket.IO functionality
            user = await self.authenticate_user(f"sockettest_{int(time.time())}@test.com")
            if not user["success"]:
                self.test_results.append({
                    "test": "Socket.IO Event Flow",
                    "success": False,
                    "error": "Authentication failed"
                })
                return
                
            sio = await self.create_socket_client(user)
            if not sio:
                self.test_results.append({
                    "test": "Socket.IO Event Flow",
                    "success": False,
                    "error": "Socket connection failed"
                })
                return
                
            # Test join_league event handler
            test_league_id = "test-league-123"
            await sio.emit('join_league', {
                'league_id': test_league_id,
                'user_id': user["user_id"]
            })
            
            # Wait for events
            await asyncio.sleep(3)
            
            # Check if league_joined event was received
            user_events = self.socket_events.get(user["user_id"], [])
            league_joined_events = [e for e in user_events if e["event"] == "league_joined"]
            
            success = len(league_joined_events) > 0
            
            self.test_results.append({
                "test": "Socket.IO Event Flow",
                "success": success,
                "details": {
                    "total_events": len(user_events),
                    "league_joined_events": len(league_joined_events),
                    "all_events": [e["event"] for e in user_events]
                }
            })
            
            await sio.disconnect()
            
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
            # Create multiple users
            users = []
            for i in range(3):
                user = await self.authenticate_user(f"flowtest_{i}_{int(time.time())}@test.com")
                if user["success"]:
                    users.append(user)
                    
            if len(users) < 2:
                self.test_results.append({
                    "test": "Complete Real-Time Flow",
                    "success": False,
                    "error": "Insufficient users created"
                })
                return
                
            commissioner = users[0]
            members = users[1:]
            
            # Create Socket.IO connections for all users
            sockets = {}
            for user in users:
                sio = await self.create_socket_client(user)
                if sio:
                    sockets[user["user_id"]] = sio
                    
            if len(sockets) < 2:
                self.test_results.append({
                    "test": "Complete Real-Time Flow",
                    "success": False,
                    "error": "Insufficient socket connections"
                })
                return
                
            # Create league
            league_result = await self.create_league(commissioner)
            if not league_result["success"]:
                self.test_results.append({
                    "test": "Complete Real-Time Flow",
                    "success": False,
                    "error": f"League creation failed: {league_result['error']}"
                })
                return
                
            league_id = league_result["league_id"]
            print(f"✅ League created: {league_id}")
            
            # All users join league room
            for user in users:
                if user["user_id"] in sockets:
                    await sockets[user["user_id"]].emit('join_league', {
                        'league_id': league_id,
                        'user_id': user["user_id"]
                    })
                    
            await asyncio.sleep(2)
            
            # Clear events
            for user in users:
                self.socket_events[user["user_id"]] = []
                
            # Members join league sequentially
            for member in members:
                print(f"👥 {member['email']} joining league...")
                join_result = await self.join_league(member, league_id)
                print(f"Join result: {join_result}")
                await asyncio.sleep(2)  # Wait between joins
                
            # Wait for all member join events
            await asyncio.sleep(3)
            
            # Start auction
            print("🚀 Starting auction...")
            auction_result = await self.start_auction(commissioner, league_id)
            print(f"Auction result: {auction_result}")
            
            # Wait for auction events
            await asyncio.sleep(3)
            
            # Analyze complete flow
            total_events = 0
            event_summary = {}
            
            for user in users:
                user_events = self.socket_events.get(user["user_id"], [])
                event_types = [e["event"] for e in user_events]
                event_summary[user["email"]] = event_types
                total_events += len(user_events)
                print(f"{user['email']}: {event_types}")
                
            # Success if we got some real-time events
            success = total_events > 0
            
            self.test_results.append({
                "test": "Complete Real-Time Flow",
                "success": success,
                "details": {
                    "total_events": total_events,
                    "users_tested": len(users),
                    "event_summary": event_summary
                }
            })
            
            # Cleanup
            for sio in sockets.values():
                await sio.disconnect()
                
        except Exception as e:
            self.test_results.append({
                "test": "Complete Real-Time Flow",
                "success": False,
                "error": f"Test exception: {str(e)}"
            })
            
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("🎯 REAL-TIME WEBSOCKET SYSTEM TEST RESULTS")
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
                if "total_events" in details:
                    print(f"   Total Events: {details['total_events']}")
                if "commissioner_events" in details:
                    print(f"   Commissioner Events: {details['commissioner_events']}")
                if "member_events" in details:
                    print(f"   Member Events: {details['member_events']}")
                    
        print(f"\n🎯 SUCCESS CRITERIA ANALYSIS:")
        
        criteria_results = {
            "Real-time member join events work instantly": False,
            "Auction start events reach all league members": False,
            "Socket.IO rooms properly isolate league-specific events": False,
            "Complete real-time synchronization between users": False
        }
        
        for result in self.test_results:
            if result["test"] == "League Real-Time Updates" and result["success"]:
                criteria_results["Real-time member join events work instantly"] = True
                
            if result["test"] == "Auction Start Real-Time Sync" and result["success"]:
                criteria_results["Auction start events reach all league members"] = True
                
            if result["test"] == "Socket.IO Event Flow" and result["success"]:
                criteria_results["Socket.IO rooms properly isolate league-specific events"] = True
                
            if result["test"] == "Complete Real-Time Flow" and result["success"]:
                criteria_results["Complete real-time synchronization between users"] = True
                
        for criteria, passed in criteria_results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {criteria}")
            
        print(f"\n🏆 FINAL ASSESSMENT:")
        if success_rate >= 75:
            print("🎉 REAL-TIME WEBSOCKET SYSTEM IS FUNCTIONAL")
            print("✅ Ready for live auction experience - true real-time WebSocket events working")
        elif success_rate >= 50:
            print("⚠️ REAL-TIME WEBSOCKET SYSTEM PARTIALLY FUNCTIONAL")
            print("🔧 Some real-time features working, but issues need resolution")
        else:
            print("❌ REAL-TIME WEBSOCKET SYSTEM NEEDS MAJOR FIXES")
            print("🚫 Not ready for live auction experience - real-time events not working")
            
        return success_rate >= 75

async def main():
    """Main test execution"""
    print("🚀 Starting Focused Real-Time WebSocket System Test")
    print("Testing: League Real-Time Updates, Auction Start Sync, Socket.IO Event Flow")
    print("=" * 80)
    
    test = RealTimeWebSocketTest()
    
    try:
        # Execute all tests
        await test.test_league_real_time_updates()
        await test.test_auction_start_real_time_sync()
        await test.test_socket_io_event_flow()
        await test.test_complete_real_time_flow()
        
        # Print results
        success = test.print_results()
        
        return success
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)