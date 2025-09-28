#!/usr/bin/env python3
"""
Focused Server-Authoritative Timer Testing
Tests the timer synchronization and anti-snipe functionality specifically
"""

import requests
import json
from datetime import datetime, timezone
import time
import socketio

class TimerTester:
    def __init__(self, base_url="https://auction-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.league_id = None
        self.auction_id = None
        
    def make_request(self, method, endpoint, data=None, expected_status=200, token=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        auth_token = token or self.token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}
    
    def authenticate_with_token(self, magic_token):
        """Authenticate using magic link token"""
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": magic_token},
            token=None
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.user_data = data['user']
            print(f"✅ Authenticated as {data['user']['email']}")
            return True
        
        print(f"❌ Authentication failed: {status}")
        return False
    
    def test_time_sync_endpoint(self):
        """Test GET /api/timez endpoint"""
        print("\n🕐 Testing Time Sync Endpoint...")
        
        success, status, data = self.make_request('GET', 'timez', token=None)
        
        if success and 'now' in data:
            try:
                server_time = datetime.fromisoformat(data['now'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                time_diff = abs((server_time - now).total_seconds())
                
                print(f"✅ Time sync endpoint working")
                print(f"   Server time: {data['now']}")
                print(f"   Time difference: {time_diff:.2f}s")
                return True
            except Exception as e:
                print(f"❌ Time parsing failed: {e}")
                return False
        else:
            print(f"❌ Time sync endpoint failed: {status}")
            return False
    
    def test_time_consistency(self):
        """Test time consistency across multiple calls"""
        print("\n🕑 Testing Time Consistency...")
        
        timestamps = []
        for i in range(3):
            success, status, data = self.make_request('GET', 'timez', token=None)
            if success and 'now' in data:
                try:
                    timestamp = datetime.fromisoformat(data['now'].replace('Z', '+00:00'))
                    timestamps.append(timestamp)
                except:
                    pass
            time.sleep(0.5)
        
        if len(timestamps) == 3:
            progression = timestamps[1] > timestamps[0] and timestamps[2] > timestamps[1]
            diff1 = (timestamps[1] - timestamps[0]).total_seconds()
            diff2 = (timestamps[2] - timestamps[1]).total_seconds()
            
            print(f"✅ Time progression: {progression}")
            print(f"   Intervals: {diff1:.2f}s, {diff2:.2f}s")
            return progression and 0.4 < diff1 < 0.7 and 0.4 < diff2 < 0.7
        else:
            print(f"❌ Failed to get consistent timestamps")
            return False
    
    def create_test_league(self):
        """Create a test league for auction testing"""
        print("\n🏟️ Creating Test League...")
        
        if not self.token:
            print("❌ No authentication token")
            return False
        
        league_data = {
            "name": f"Timer Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,  # 30 seconds for testing
                "bid_timer_seconds": 60,
                "league_size": {
                    "min": 2,  # Lower minimum for testing
                    "max": 8
                },
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            self.league_id = data['id']
            print(f"✅ League created: {self.league_id}")
            print(f"   Anti-snipe seconds: {data.get('settings', {}).get('anti_snipe_seconds', 'N/A')}")
            return True
        else:
            print(f"❌ League creation failed: {status} - {data}")
            return False
    
    def add_test_members(self):
        """Add members to reach minimum league size"""
        print("\n👥 Adding Test Members...")
        
        if not self.league_id:
            print("❌ No league ID")
            return False
        
        # Join league directly (simulating accepted invitations)
        for i in range(1):  # Add 1 more member to reach minimum of 2
            success, status, data = self.make_request('POST', f'leagues/{self.league_id}/join')
            if success:
                print(f"✅ Added member {i+1}")
            else:
                print(f"❌ Failed to add member {i+1}: {status}")
        
        # Check league status
        success, status, league_status = self.make_request('GET', f'leagues/{self.league_id}/status')
        if success:
            print(f"✅ League status: {league_status.get('status', 'unknown')}")
            print(f"   Members: {league_status.get('member_count', 0)}/{league_status.get('max_members', 0)}")
            print(f"   Ready: {league_status.get('is_ready', False)}")
            return league_status.get('is_ready', False)
        
        return False
    
    def start_test_auction(self):
        """Start auction for testing"""
        print("\n🎯 Starting Test Auction...")
        
        if not self.league_id:
            print("❌ No league ID")
            return False
        
        success, status, data = self.make_request('POST', f'auction/{self.league_id}/start')
        
        if success:
            self.auction_id = self.league_id
            print(f"✅ Auction started: {self.auction_id}")
            return True
        else:
            print(f"❌ Auction start failed: {status} - {data}")
            return False
    
    def test_websocket_time_sync(self):
        """Test WebSocket time sync broadcasting"""
        print("\n🔌 Testing WebSocket Time Sync...")
        
        if not self.token or not self.auction_id:
            print("❌ Missing token or auction ID")
            return False
        
        try:
            sio = socketio.Client()
            time_sync_messages = []
            connected = False
            
            @sio.event
            def connect():
                nonlocal connected
                connected = True
                print("   WebSocket connected")
            
            @sio.event
            def time_sync(data):
                time_sync_messages.append(data)
                print(f"   Time sync: {data.get('server_now', 'N/A')}")
            
            # Connect
            sio.connect(self.base_url, auth={'token': self.token}, transports=['websocket', 'polling'])
            time.sleep(1)
            
            if connected:
                # Join auction room
                join_result = sio.call('join_auction', {'auction_id': self.auction_id}, timeout=5)
                
                if join_result and join_result.get('success', False):
                    print("   Joined auction room")
                    
                    # Wait for time sync messages
                    time.sleep(6)  # Wait for at least 3 time sync messages (every 2 seconds)
                    
                    sio.disconnect()
                    
                    if len(time_sync_messages) >= 2:
                        print(f"✅ Received {len(time_sync_messages)} time sync messages")
                        
                        # Check message structure
                        first_msg = time_sync_messages[0]
                        structure_valid = (
                            'server_now' in first_msg and
                            'current_lot' in first_msg
                        )
                        print(f"   Message structure valid: {structure_valid}")
                        return structure_valid
                    else:
                        print(f"❌ Only received {len(time_sync_messages)} time sync messages")
                        return False
                else:
                    sio.disconnect()
                    print("❌ Failed to join auction room")
                    return False
            else:
                print("❌ WebSocket connection failed")
                return False
                
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False
    
    def test_auction_state_with_timing(self):
        """Test auction state includes timing information"""
        print("\n📊 Testing Auction State with Timing...")
        
        if not self.auction_id:
            print("❌ No auction ID")
            return False
        
        success, status, data = self.make_request('GET', f'auction/{self.auction_id}/state')
        
        if success:
            has_timing = (
                'auction_id' in data and
                'settings' in data and
                'anti_snipe_seconds' in data.get('settings', {})
            )
            
            anti_snipe_seconds = data.get('settings', {}).get('anti_snipe_seconds', 0)
            
            print(f"✅ Auction state retrieved")
            print(f"   Has timing info: {has_timing}")
            print(f"   Anti-snipe seconds: {anti_snipe_seconds}")
            print(f"   Current lot: {'Yes' if data.get('current_lot') else 'No'}")
            
            return has_timing and anti_snipe_seconds == 30  # Should match our league settings
        else:
            print(f"❌ Failed to get auction state: {status}")
            return False
    
    def run_timer_tests(self):
        """Run all timer-related tests"""
        print("🚀 Starting Server-Authoritative Timer Tests")
        print("=" * 60)
        
        results = []
        
        # Basic time sync tests (no auth required)
        results.append(self.test_time_sync_endpoint())
        results.append(self.test_time_consistency())
        
        # Use a fresh magic token
        magic_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRpbWVyLnRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjE3NTg3NTY5OTcsInR5cGUiOiJtYWdpY19saW5rIn0.rpNeShCacIxgcuVdeTGueeiXI4otaAwPYOy-sdyHbxs"
        
        if self.authenticate_with_token(magic_token):
            # Authenticated tests
            if self.create_test_league():
                if self.add_test_members():
                    if self.start_test_auction():
                        results.append(self.test_websocket_time_sync())
                        results.append(self.test_auction_state_with_timing())
                    else:
                        results.extend([False, False])  # WebSocket and auction state tests
                else:
                    results.extend([False, False, False])  # All remaining tests
            else:
                results.extend([False, False, False, False])  # All remaining tests
        else:
            results.extend([False, False, False, False])  # All remaining tests
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TIMER TEST SUMMARY")
        passed = sum(results)
        total = len(results)
        print(f"   Tests Passed: {passed}/{total}")
        print(f"   Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print("🎉 All timer tests passed!")
        else:
            print("⚠️  Some timer tests failed")
        
        return passed == total

if __name__ == "__main__":
    tester = TimerTester()
    tester.run_timer_tests()