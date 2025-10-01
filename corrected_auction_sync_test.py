#!/usr/bin/env python3
"""
CORRECTED AUCTION STATE SYNCHRONIZATION TEST
Tests the Socket.IO auction state sync functionality with correct endpoints.
"""

import requests
import json
import os
import sys
from datetime import datetime
import uuid
import time

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CorrectedAuctionSyncTest:
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
        
    def test_1_setup_and_start_auction(self):
        """Test 1: Setup league and start auction"""
        try:
            print("\n=== TEST 1: SETUP AND START AUCTION ===")
            
            # Create test users
            self.test_users = [
                f"corrected-commissioner-{uuid.uuid4().hex[:8]}@test.com",
                f"corrected-manager1-{uuid.uuid4().hex[:8]}@test.com", 
                f"corrected-manager2-{uuid.uuid4().hex[:8]}@test.com",
                f"corrected-manager3-{uuid.uuid4().hex[:8]}@test.com"
            ]
            
            # Create sessions for all users
            for email in self.test_users:
                self.create_session(email)
                
            # Create league with commissioner
            commissioner_session = self.sessions[self.test_users[0]]
            league_data = {
                "name": f"Corrected Auction Sync Test {uuid.uuid4().hex[:8]}",
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
                    
            self.log_result("All Users Joined", True, f"{len(self.test_users)} users in league")
            
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
                
            return True
            
        except Exception as e:
            self.log_result("Setup and Start Auction", False, f"Exception: {str(e)}")
            return False
            
    def test_2_auction_state_endpoint(self):
        """Test 2: Test correct auction state endpoint"""
        try:
            print("\n=== TEST 2: AUCTION STATE ENDPOINT ===")
            
            commissioner_session = self.sessions[self.test_users[0]]
            
            # Test the correct auction state endpoint
            auction_state_response = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            
            if auction_state_response.status_code == 200:
                auction_data = auction_state_response.json()
                self.log_result("Auction State Endpoint", True, f"Status: {auction_data.get('status', 'unknown')}")
                
                # Verify essential auction state fields for sync
                required_fields = ['status', 'league_id']
                missing_fields = [field for field in required_fields if field not in auction_data]
                
                if not missing_fields:
                    self.log_result("Auction State Fields", True, f"Contains required fields: {required_fields}")
                else:
                    self.log_result("Auction State Fields", False, f"Missing fields: {missing_fields}")
                    return False
                    
                # Check for auction-specific data
                auction_fields = []
                if 'current_lot' in auction_data:
                    auction_fields.append('current_lot')
                if 'lots' in auction_data:
                    auction_fields.append('lots')
                if 'auction_id' in auction_data:
                    auction_fields.append('auction_id')
                if 'timer_ends_at' in auction_data:
                    auction_fields.append('timer_ends_at')
                    
                if auction_fields:
                    self.log_result("Auction Specific Data", True, f"Contains: {auction_fields}")
                else:
                    self.log_result("Auction Specific Data", True, "Basic auction state available")
                    
                return True
                
            else:
                self.log_result("Auction State Endpoint", False, f"Status: {auction_state_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Auction State Endpoint", False, f"Exception: {str(e)}")
            return False
            
    def test_3_multi_user_auction_state_access(self):
        """Test 3: Verify all users can access auction state"""
        try:
            print("\n=== TEST 3: MULTI-USER AUCTION STATE ACCESS ===")
            
            # Test that all users can access auction state
            for email in self.test_users:
                session = self.sessions[email]
                
                # Each user should be able to get auction state
                auction_response = session.get(f"{API_BASE}/auction/{self.auction_id}/state")
                if auction_response.status_code != 200:
                    self.log_result(f"Multi-User Auction Access ({email})", False, f"Status: {auction_response.status_code}")
                    return False
                    
                auction_data = auction_response.json()
                self.log_result(f"Multi-User Auction Access ({email})", True, f"Status: {auction_data.get('status', 'unknown')}")
                
            # Verify auction state consistency across users
            auction_states = []
            for email in self.test_users:
                session = self.sessions[email]
                response = session.get(f"{API_BASE}/auction/{self.auction_id}/state")
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
            self.log_result("Multi-User Auction State Access", False, f"Exception: {str(e)}")
            return False
            
    def test_4_complete_sync_data_with_auction(self):
        """Test 4: Verify complete sync data structure with auction"""
        try:
            print("\n=== TEST 4: COMPLETE SYNC DATA WITH AUCTION ===")
            
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
                
            # 4. Auction state (using correct endpoint)
            auction_response = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
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
                self.log_result("Complete Sync Serializable", True, "Full sync data with auction can be serialized")
            except (TypeError, ValueError) as e:
                self.log_result("Complete Sync Serializable", False, f"Serialization error: {e}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Complete Sync Data with Auction", False, f"Exception: {str(e)}")
            return False
            
    def test_5_auction_state_fields_for_reconnection(self):
        """Test 5: Verify auction state contains fields needed for reconnection"""
        try:
            print("\n=== TEST 5: AUCTION STATE FIELDS FOR RECONNECTION ===")
            
            commissioner_session = self.sessions[self.test_users[0]]
            
            # Get auction state
            auction_response = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            if auction_response.status_code != 200:
                self.log_result("Auction State Retrieval", False, f"Status: {auction_response.status_code}")
                return False
                
            auction_data = auction_response.json()
            
            # Check for fields that would be essential for client reconnection
            reconnection_fields = {
                'status': 'Auction status (active/paused/completed)',
                'league_id': 'League identifier for room joining',
                'current_lot': 'Current lot being auctioned',
                'timer_ends_at': 'Timer information for UI sync',
                'lots': 'Available lots for auction progression'
            }
            
            present_fields = []
            missing_fields = []
            
            for field, description in reconnection_fields.items():
                if field in auction_data:
                    present_fields.append(field)
                    self.log_result(f"Reconnection Field: {field}", True, description)
                else:
                    missing_fields.append(field)
                    self.log_result(f"Reconnection Field: {field}", False, f"Missing: {description}")
                    
            # At minimum, we need status and league_id for basic reconnection
            critical_fields = ['status', 'league_id']
            missing_critical = [field for field in critical_fields if field not in auction_data]
            
            if not missing_critical:
                self.log_result("Critical Reconnection Fields", True, f"Present: {critical_fields}")
            else:
                self.log_result("Critical Reconnection Fields", False, f"Missing critical: {missing_critical}")
                return False
                
            # Check if auction state provides enough info for UI restoration
            if len(present_fields) >= 3:  # At least 3 out of 5 fields
                self.log_result("Auction Reconnection Capability", True, f"Sufficient fields for reconnection: {present_fields}")
            else:
                self.log_result("Auction Reconnection Capability", False, f"Insufficient fields: {present_fields}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Auction State Fields for Reconnection", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all corrected auction sync tests"""
        print("🔄 STARTING CORRECTED AUCTION STATE SYNCHRONIZATION TESTS")
        print(f"Backend URL: {BACKEND_URL}")
        
        try:
            # Run tests in sequence
            tests = [
                self.test_1_setup_and_start_auction,
                self.test_2_auction_state_endpoint,
                self.test_3_multi_user_auction_state_access,
                self.test_4_complete_sync_data_with_auction,
                self.test_5_auction_state_fields_for_reconnection
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
            print(f"\n🎯 CORRECTED AUCTION STATE SYNCHRONIZATION TEST SUMMARY")
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
    test_suite = CorrectedAuctionSyncTest()
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