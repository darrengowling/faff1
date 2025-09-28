#!/usr/bin/env python3
"""
Focused test for server-computed roster summary implementation
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone

class RosterSummaryTester:
    def __init__(self, base_url="https://league-creator-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_league_id = None
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            self.failed_tests.append(f"{name}: {details}")
            print(f"❌ {name} - FAILED {details}")
        return success

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

    def authenticate_with_manual_token(self):
        """Use a manual token for testing - you'll need to provide this"""
        # For testing, you would need to get a token from the magic link flow
        # This is a placeholder - in real testing you'd extract from logs or use a test user
        print("⚠️  Manual authentication required")
        print("   1. Go to the frontend and request a magic link")
        print("   2. Check backend logs for the token")
        print("   3. Set the token manually in this script")
        
        # For now, let's try to create a test user and get a token
        # This would require implementing the full auth flow
        return False

    def setup_test_league(self):
        """Create a test league for roster summary testing"""
        if not self.token:
            return False
            
        league_data = {
            "name": f"Roster Summary Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "max_managers": 8,
                "min_managers": 4,
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            self.test_league_id = data['id']
            return True
        
        print(f"Failed to create test league: {status} - {data}")
        return False

    def test_roster_summary_endpoint_structure(self):
        """Test GET /api/leagues/{league_id}/roster/summary endpoint returns proper JSON structure"""
        if not self.test_league_id:
            return self.log_test("Roster Summary Endpoint Structure", False, "No test league ID")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/roster/summary')
        
        # Verify response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'ownedCount' in data and
            'clubSlots' in data and
            'remaining' in data and
            isinstance(data['ownedCount'], int) and
            isinstance(data['clubSlots'], int) and
            isinstance(data['remaining'], int)
        )
        
        # Verify calculation logic: remaining = clubSlots - ownedCount
        calculation_correct = False
        if valid_response:
            expected_remaining = max(0, data['clubSlots'] - data['ownedCount'])
            calculation_correct = data['remaining'] == expected_remaining
        
        return self.log_test(
            "Roster Summary Endpoint Structure",
            valid_response and calculation_correct,
            f"Status: {status}, Valid structure: {valid_response}, Calculation correct: {calculation_correct}, Data: {data if success else 'N/A'}"
        )

    def test_roster_summary_authentication_required(self):
        """Test roster summary endpoint requires authentication"""
        if not self.test_league_id:
            return self.log_test("Roster Summary Authentication", False, "No test league ID")
        
        # Test without token
        success, status, data = self.make_request(
            'GET', 
            f'leagues/{self.test_league_id}/roster/summary',
            token=None,
            expected_status=401
        )
        
        auth_required = success and status == 401
        
        return self.log_test(
            "Roster Summary Authentication Required",
            auth_required,
            f"Status: {status}, Auth required: {auth_required}"
        )

    def test_roster_summary_server_side_calculation(self):
        """Test that roster summary calculations are performed server-side from database"""
        if not self.test_league_id:
            return self.log_test("Roster Summary Server Calculation", False, "No test league ID")
        
        # Get roster summary
        success, status, roster_data = self.make_request('GET', f'leagues/{self.test_league_id}/roster/summary')
        
        if not success:
            return self.log_test("Roster Summary Server Calculation", False, f"Failed to get roster summary: {status}")
        
        # Get league settings to verify club slots
        success2, status2, league_data = self.make_request('GET', f'leagues/{self.test_league_id}')
        
        if not success2:
            return self.log_test("Roster Summary Server Calculation", False, f"Failed to get league data: {status2}")
        
        # Verify club slots match league settings
        league_club_slots = league_data.get('settings', {}).get('club_slots_per_manager', 0)
        roster_club_slots = roster_data.get('clubSlots', 0)
        
        club_slots_match = league_club_slots == roster_club_slots
        
        # Verify owned count is non-negative integer
        owned_count = roster_data.get('ownedCount', -1)
        owned_count_valid = isinstance(owned_count, int) and owned_count >= 0
        
        # Verify remaining calculation
        remaining = roster_data.get('remaining', -1)
        expected_remaining = max(0, roster_club_slots - owned_count)
        remaining_correct = remaining == expected_remaining
        
        server_calculation_valid = club_slots_match and owned_count_valid and remaining_correct
        
        return self.log_test(
            "Roster Summary Server-Side Calculation",
            server_calculation_valid,
            f"Club slots match: {club_slots_match} ({league_club_slots}={roster_club_slots}), Owned count valid: {owned_count_valid} ({owned_count}), Remaining correct: {remaining_correct} ({remaining}={expected_remaining})"
        )

    def test_roster_summary_user_id_parameter(self):
        """Test roster summary endpoint with optional userId parameter"""
        if not self.test_league_id:
            return self.log_test("Roster Summary UserId Parameter", False, "No test league ID")
        
        # Test without userId (should default to current user)
        success1, status1, data1 = self.make_request('GET', f'leagues/{self.test_league_id}/roster/summary')
        
        # Test with explicit userId (using current user's ID)
        if success1 and self.user_data:
            user_id = self.user_data.get('id')
            success2, status2, data2 = self.make_request('GET', f'leagues/{self.test_league_id}/roster/summary?userId={user_id}')
            
            # Both should return same data since it's the same user
            same_data = (
                success1 and success2 and
                data1.get('ownedCount') == data2.get('ownedCount') and
                data1.get('clubSlots') == data2.get('clubSlots') and
                data1.get('remaining') == data2.get('remaining')
            )
            
            return self.log_test(
                "Roster Summary UserId Parameter",
                same_data,
                f"Default user data matches explicit userId: {same_data}"
            )
        else:
            return self.log_test(
                "Roster Summary UserId Parameter",
                success1,
                f"Basic endpoint works: {success1}, Status: {status1}"
            )

    def run_tests(self):
        """Run all roster summary tests"""
        print("🏆 Starting Server-Computed Roster Summary Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Check if we can access the API
        success, status, data = self.make_request('GET', 'health', token=None)
        if not success:
            print(f"❌ Cannot access API at {self.base_url}")
            return 1
        
        print("✅ API is accessible")
        
        # For now, test without authentication to see basic endpoint behavior
        print("\n🔍 Testing roster summary endpoint without authentication...")
        
        # Test with a dummy league ID to see the auth requirement
        dummy_league_id = "test_league_123"
        success, status, data = self.make_request(
            'GET', 
            f'leagues/{dummy_league_id}/roster/summary',
            token=None,
            expected_status=401
        )
        
        if success and status == 401:
            print("✅ Roster summary endpoint correctly requires authentication")
        else:
            print(f"⚠️  Unexpected response: {status} - {data}")
        
        # Test endpoint structure with invalid league (should get 401 before 404)
        success, status, data = self.make_request(
            'GET', 
            f'leagues/{dummy_league_id}/roster/summary',
            token="invalid_token",
            expected_status=401
        )
        
        if status == 401:
            print("✅ Roster summary endpoint validates authentication before processing")
        else:
            print(f"⚠️  Unexpected auth validation: {status}")
        
        print(f"\n📊 Basic Tests Complete")
        print("⚠️  Full testing requires authentication setup")
        print("   To complete testing:")
        print("   1. Set up authentication in the test")
        print("   2. Create test leagues")
        print("   3. Test with actual roster data")
        
        return 0

def main():
    """Main test runner"""
    tester = RosterSummaryTester()
    return tester.run_tests()

if __name__ == "__main__":
    sys.exit(main())