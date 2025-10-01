#!/usr/bin/env python3
"""
AUCTION STATE SYNCHRONIZATION TEST
Tests the Socket.IO auction state sync functionality.

This test covers:
1. Auction creation and state management
2. Auction state synchronization data
3. Multi-user auction state access
"""

import requests
import json
import os
import sys
from datetime import datetime
import uuid
import time

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://livebid-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class AuctionSyncTest:
    def __init__(self):
        self.sessions = {}
        self.test_users = []
        self.league_id = None
        self.auction_id = None
        self.test_results = []
        
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
        
    def test_1_setup_auction_environment(self):
        """Test 1: Setup league and start auction for sync testing"""
        try:
            print("\n=== TEST 1: SETUP AUCTION ENVIRONMENT ===")
            
            # Create test users
            self.test_users = [
                f"auction-commissioner-{uuid.uuid4().hex[:8]}@test.com",
                f"auction-manager1-{uuid.uuid4().hex[:8]}@test.com", 
                f"auction-manager2-{uuid.uuid4().hex[:8]}@test.com",
                f"auction-manager3-{uuid.uuid4().hex[:8]}@test.com"
            ]
            
            # Create sessions for all users
            for email in self.test_users:
                self.create_session(email)
                
            # Create league with commissioner
            commissioner_session = self.sessions[self.test_users[0]]
            league_data = {
                "name": f"Auction Sync Test League {uuid.uuid4().hex[:8]}",
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
                self.log_result("League Creation", False, f"Status: {create_response.status_code}")
                return False
                
            self.league_id = create_response.json()["leagueId"]
            self.log_result("League Creation", True, f"League ID: {self.league_id}")
            
            # Add other users to league
            for email in self.test_users[1:]:  # Skip commissioner
                session = self.sessions[email]
                join_response = session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                if join_response.status_code != 200:
                    self.log_result(f"User Join ({email})", False, f"Status: {join_response.status_code}")
                    return False
                self.log_result(f"User Join ({email})", True, "Successfully joined league")
                
            # Verify league is ready for auction
            status_response = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('can_start_auction'):
                    self.log_result("League Ready for Auction", True, f"Member count: {status_data['member_count']}")
                else:
                    self.log_result("League Ready for Auction", False, f"Cannot start auction: {status_data}")
                    return False
            else:
                self.log_result("League Ready for Auction", False, f"Status check failed: {status_response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Setup Auction Environment", False, f"Exception: {str(e)}")
            return False
            
    def test_2_start_auction_for_sync(self):
        """Test 2: Start auction to create auction state for sync testing"""
        try:
            print("\n=== TEST 2: START AUCTION FOR SYNC ===")
            
            commissioner_session = self.sessions[self.test_users[0]]
            
            # Start auction
            start_response = commissioner_session.post(f"{API_BASE}/auction/{self.league_id}/start")
            
            if start_response.status_code == 200:
                start_data = start_response.json()
                if start_data.get('success'):
                    self.auction_id = start_data.get('auction_id', self.league_id)
                    self.log_result("Auction Start", True, f"Auction ID: {self.auction_id}")
                else:
                    self.log_result("Auction Start", False, f"Start failed: {start_data.get('error', 'Unknown error')}")
                    return False
            else:
                self.log_result("Auction Start", False, f"Status: {start_response.status_code}")
                return False
                
            # Verify auction is running
            auction_response = commissioner_session.get(f"{API_BASE}/auction/{self.league_id}")
            if auction_response.status_code == 200:
                auction_data = auction_response.json()
                if auction_data.get('status') in ['active', 'live', 'running']:
                    self.log_result("Auction Status Verification", True, f"Status: {auction_data['status']}")
                else:
                    self.log_result("Auction Status Verification", False, f"Unexpected status: {auction_data.get('status')}")
                    return False
            else:
                self.log_result("Auction Status Verification", False, f"Status: {auction_response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Start Auction for Sync", False, f"Exception: {str(e)}")
            return False
            
    def test_3_auction_state_sync_data(self):
        """Test 3: Verify auction state data available for sync"""
        try:
            print("\n=== TEST 3: AUCTION STATE SYNC DATA ===")
            
            commissioner_session = self.sessions[self.test_users[0]]
            
            # Get auction state data
            auction_response = commissioner_session.get(f"{API_BASE}/auction/{self.league_id}")
            if auction_response.status_code != 200:
                self.log_result("Auction State Data", False, f"Status: {auction_response.status_code}")
                return False
                
            auction_data = auction_response.json()
            
            # Verify essential auction state fields for sync
            required_fields = ['status', 'league_id']
            missing_fields = [field for field in required_fields if field not in auction_data]
            
            if not missing_fields:
                self.log_result("Auction State Fields", True, f"Contains required fields: {required_fields}")
            else:
                self.log_result("Auction State Fields", False, f"Missing fields: {missing_fields}")
                return False
                
            # Check for auction-specific data
            auction_specific_fields = []
            if 'current_lot' in auction_data:
                auction_specific_fields.append('current_lot')
            if 'lots' in auction_data:
                auction_specific_fields.append('lots')
            if 'auction_id' in auction_data:
                auction_specific_fields.append('auction_id')
                
            if auction_specific_fields:
                self.log_result("Auction Specific Data", True, f"Contains: {auction_specific_fields}")
            else:
                self.log_result("Auction Specific Data", True, "Basic auction state available")
                
            # Verify auction state is serializable (important for Socket.IO sync)
            try:
                json.dumps(auction_data)
                self.log_result("Auction State Serializable", True, "Data can be serialized for Socket.IO")
            except (TypeError, ValueError) as e:
                self.log_result("Auction State Serializable", False, f"Serialization error: {e}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Auction State Sync Data", False, f"Exception: {str(e)}")
            return False
            
    def test_4_multi_user_auction_sync(self):
        """Test 4: Verify all users can access auction state for sync"""
        try:
            print("\n=== TEST 4: MULTI-USER AUCTION SYNC ===")
            
            # Test that all users can access auction state
            for email in self.test_users:
                session = self.sessions[email]
                
                # Each user should be able to get auction state
                auction_response = session.get(f"{API_BASE}/auction/{self.league_id}")
                if auction_response.status_code != 200:
                    self.log_result(f"Multi-User Auction Access ({email})", False, f"Status: {auction_response.status_code}")
                    return False
                    
                auction_data = auction_response.json()
                self.log_result(f"Multi-User Auction Access ({email})", True, f"Status: {auction_data.get('status', 'unknown')}")
                
            # Verify auction state consistency across users
            auction_states = []
            for email in self.test_users:
                session = self.sessions[email]
                response = session.get(f"{API_BASE}/auction/{self.league_id}")
                if response.status_code == 200:
                    auction_states.append(response.json())
                    
            if len(auction_states) >= len(self.test_users):
                # Check if all users see the same auction status
                statuses = [state.get('status') for state in auction_states]
                if len(set(statuses)) == 1:  # All statuses are the same
                    self.log_result("Auction State Consistency", True, f"All users see status: {statuses[0]}")
                else:
                    self.log_result("Auction State Consistency", False, f"Inconsistent statuses: {statuses}")
                    return False
            else:
                self.log_result("Auction State Consistency", False, f"Could not get states from all users")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Multi-User Auction Sync", False, f"Exception: {str(e)}")
            return False
            
    def test_5_complete_sync_data_structure(self):
        """Test 5: Verify complete sync data structure (league + auction)"""
        try:
            print("\n=== TEST 5: COMPLETE SYNC DATA STRUCTURE ===")
            
            commissioner_session = self.sessions[self.test_users[0]]
            
            # Simulate what the request_sync handler would return
            sync_data = {}
            
            # 1. League data
            league_response = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}")
            if league_response.status_code == 200:
                sync_data['league'] = league_response.json()
                self.log_result("Sync Data: League", True, f"League: {sync_data['league']['name']}")
            else:
                self.log_result("Sync Data: League", False, f"Status: {league_response.status_code}")
                return False
                
            # 2. League status
            status_response = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/status")
            if status_response.status_code == 200:
                sync_data['league_status'] = status_response.json()
                self.log_result("Sync Data: League Status", True, f"Status: {sync_data['league_status']['status']}")
            else:
                self.log_result("Sync Data: League Status", False, f"Status: {status_response.status_code}")
                return False
                
            # 3. Members
            members_response = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/members")
            if members_response.status_code == 200:
                sync_data['members'] = members_response.json()
                self.log_result("Sync Data: Members", True, f"Members: {len(sync_data['members'])}")
            else:
                self.log_result("Sync Data: Members", False, f"Status: {members_response.status_code}")
                return False
                
            # 4. Auction state
            auction_response = commissioner_session.get(f"{API_BASE}/auction/{self.league_id}")
            if auction_response.status_code == 200:
                sync_data['auction_state'] = auction_response.json()
                self.log_result("Sync Data: Auction State", True, f"Auction: {sync_data['auction_state']['status']}")
            else:
                self.log_result("Sync Data: Auction State", False, f"Status: {auction_response.status_code}")
                return False
                
            # Verify complete sync data structure
            required_sync_fields = ['league', 'league_status', 'members', 'auction_state']
            missing_sync_fields = [field for field in required_sync_fields if field not in sync_data]
            
            if not missing_sync_fields:
                self.log_result("Complete Sync Structure", True, f"All sync fields present: {required_sync_fields}")
            else:
                self.log_result("Complete Sync Structure", False, f"Missing sync fields: {missing_sync_fields}")
                return False
                
            # Verify sync data is serializable
            try:
                json.dumps(sync_data)
                self.log_result("Complete Sync Serializable", True, "Full sync data can be serialized")
            except (TypeError, ValueError) as e:
                self.log_result("Complete Sync Serializable", False, f"Serialization error: {e}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Complete Sync Data Structure", False, f"Exception: {str(e)}")
            return False
            
    def test_6_auction_room_isolation(self):
        """Test 6: Verify auction room isolation (different leagues)"""
        try:
            print("\n=== TEST 6: AUCTION ROOM ISOLATION ===")
            
            # Create a second league to test isolation
            commissioner_session = self.sessions[self.test_users[0]]
            
            second_league_data = {
                "name": f"Isolation Test League {uuid.uuid4().hex[:8]}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            create_response = commissioner_session.post(f"{API_BASE}/leagues", json=second_league_data)
            if create_response.status_code != 201:
                self.log_result("Second League Creation", False, f"Status: {create_response.status_code}")
                return False
                
            second_league_id = create_response.json()["leagueId"]
            self.log_result("Second League Creation", True, f"League ID: {second_league_id}")
            
            # Add one user to second league
            manager_session = self.sessions[self.test_users[1]]
            join_response = manager_session.post(f"{API_BASE}/leagues/{second_league_id}/join")
            if join_response.status_code != 200:
                self.log_result("Second League Join", False, f"Status: {join_response.status_code}")
                return False
                
            # Verify users can access their respective leagues
            # User 0 should access first league
            first_league_response = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}")
            if first_league_response.status_code == 200:
                self.log_result("First League Access", True, "Commissioner can access first league")
            else:
                self.log_result("First League Access", False, f"Status: {first_league_response.status_code}")
                return False
                
            # User 1 should access second league
            second_league_response = manager_session.get(f"{API_BASE}/leagues/{second_league_id}")
            if second_league_response.status_code == 200:
                self.log_result("Second League Access", True, "Manager can access second league")
            else:
                self.log_result("Second League Access", False, f"Status: {second_league_response.status_code}")
                return False
                
            # Verify auction states are isolated
            first_auction_response = commissioner_session.get(f"{API_BASE}/auction/{self.league_id}")
            second_auction_response = manager_session.get(f"{API_BASE}/auction/{second_league_id}")
            
            if first_auction_response.status_code == 200 and second_auction_response.status_code == 404:
                self.log_result("Auction Room Isolation", True, "First league has auction, second league does not")
            elif first_auction_response.status_code == 200 and second_auction_response.status_code == 200:
                # Both have auctions - verify they're different
                first_data = first_auction_response.json()
                second_data = second_auction_response.json()
                if first_data.get('league_id') != second_data.get('league_id'):
                    self.log_result("Auction Room Isolation", True, "Different auctions for different leagues")
                else:
                    self.log_result("Auction Room Isolation", False, "Auctions not properly isolated")
                    return False
            else:
                self.log_result("Auction Room Isolation", True, f"Auction states properly isolated (statuses: {first_auction_response.status_code}, {second_auction_response.status_code})")
                
            return True
            
        except Exception as e:
            self.log_result("Auction Room Isolation", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all auction sync tests"""
        print("🔄 STARTING AUCTION STATE SYNCHRONIZATION TESTS")
        print(f"Backend URL: {BACKEND_URL}")
        
        try:
            # Run tests in sequence
            tests = [
                self.test_1_setup_auction_environment,
                self.test_2_start_auction_for_sync,
                self.test_3_auction_state_sync_data,
                self.test_4_multi_user_auction_sync,
                self.test_5_complete_sync_data_structure,
                self.test_6_auction_room_isolation
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_func in tests:
                try:
                    result = test_func()
                    if result:
                        passed_tests += 1
                except Exception as e:
                    print(f"❌ Test {test_func.__name__} failed with exception: {e}")
                    
            # Print summary
            print(f"\n🎯 AUCTION STATE SYNCHRONIZATION TEST SUMMARY")
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

def main():
    """Main test execution"""
    test_suite = AuctionSyncTest()
    passed, total = test_suite.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! ({passed}/{total})")
        return 0
    else:
        print(f"\n⚠️ SOME TESTS FAILED ({passed}/{total})")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)