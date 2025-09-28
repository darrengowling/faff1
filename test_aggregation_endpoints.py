#!/usr/bin/env python3
"""
UCL Auction Aggregation API Testing Suite - Automated Version
Tests the 4 new aggregation endpoints with extracted token
"""

import requests
import sys
import json
from datetime import datetime
import time

class AggregationEndpointTester:
    def __init__(self, base_url="https://auction-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.access_token = None
        self.user_data = {}
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Use the token from backend logs
        self.magic_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFnZ3JlZ2F0aW9uX3Rlc3RfMTc1ODU4Njk2NkBleGFtcGxlLmNvbSIsImV4cCI6MTc1ODU4Nzg2NiwidHlwZSI6Im1hZ2ljX2xpbmsifQ.DAvIyA0s7ny6TCARw8qFq80RBzcFtjb6s_ASTpXBjVo"
        
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
        
        auth_token = token or self.access_token
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

    def authenticate_and_setup(self):
        """Authenticate using extracted token and set up test league"""
        print("🔐 Authenticating with extracted token...")
        
        # Verify the magic link token
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": self.magic_token},
            token=None
        )
        
        if not success or 'access_token' not in data:
            print(f"❌ Token verification failed: {status} - {data}")
            return False
        
        self.access_token = data['access_token']
        self.user_data = data['user']
        print(f"✅ Authenticated as {data['user']['email']}")
        
        # Seed clubs
        success, status, data = self.make_request('POST', 'clubs/seed')
        if success:
            print("✅ Clubs seeded successfully")
        
        # Create test league
        league_data = {
            "name": f"Aggregation Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2024-25",
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
            print(f"✅ Test league created: {self.test_league_id}")
            return True
        else:
            print(f"❌ Failed to create test league: {status} - {data}")
            return False

    def test_my_clubs_endpoint(self):
        """Test /api/clubs/my-clubs/{league_id} endpoint"""
        success, status, data = self.make_request(
            'GET',
            f'clubs/my-clubs/{self.test_league_id}'
        )
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'league_id' in data and
            'user_id' in data and
            'owned_clubs' in data and
            'budget_info' in data and
            isinstance(data['owned_clubs'], list) and
            isinstance(data['budget_info'], dict)
        )
        
        # Check budget_info structure
        budget_valid = True
        if valid_response and data['budget_info']:
            budget_info = data['budget_info']
            budget_valid = (
                'budget_start' in budget_info and
                'budget_remaining' in budget_info and
                'total_spent' in budget_info and
                'clubs_owned' in budget_info and
                'slots_available' in budget_info
            )
        
        return self.log_test(
            "My Clubs Endpoint",
            valid_response and budget_valid,
            f"Status: {status}, Valid structure: {valid_response}, Budget valid: {budget_valid}, Clubs: {len(data.get('owned_clubs', []))}"
        )
    
    def test_fixtures_endpoint(self):
        """Test /api/fixtures/{league_id} endpoint"""
        success, status, data = self.make_request(
            'GET',
            f'fixtures/{self.test_league_id}'
        )
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'league_id' in data and
            'season' in data and
            'fixtures' in data and
            'grouped_fixtures' in data and
            'ownership_summary' in data and
            isinstance(data['fixtures'], list) and
            isinstance(data['grouped_fixtures'], dict) and
            isinstance(data['ownership_summary'], dict)
        )
        
        # Check grouped_fixtures structure
        grouped_valid = True
        if valid_response and data['grouped_fixtures']:
            expected_groups = ['group_stage', 'round_of_16', 'quarter_finals', 'semi_finals', 'final']
            grouped_fixtures = data['grouped_fixtures']
            grouped_valid = all(group in grouped_fixtures for group in expected_groups)
        
        return self.log_test(
            "Fixtures Endpoint",
            valid_response and grouped_valid,
            f"Status: {status}, Valid structure: {valid_response}, Grouped valid: {grouped_valid}, Fixtures: {len(data.get('fixtures', []))}"
        )
    
    def test_leaderboard_endpoint(self):
        """Test /api/leaderboard/{league_id} endpoint"""
        success, status, data = self.make_request(
            'GET',
            f'leaderboard/{self.test_league_id}'
        )
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'league_id' in data and
            'leaderboard' in data and
            'weekly_breakdown' in data and
            'total_managers' in data and
            isinstance(data['leaderboard'], list) and
            isinstance(data['weekly_breakdown'], dict) and
            isinstance(data['total_managers'], int)
        )
        
        return self.log_test(
            "Leaderboard Endpoint",
            valid_response,
            f"Status: {status}, Valid structure: {valid_response}, Managers: {data.get('total_managers', 0)}"
        )
    
    def test_head_to_head_endpoint(self):
        """Test /api/analytics/head-to-head/{league_id} endpoint"""
        # Get league members to use for head-to-head comparison
        success_members, status_members, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        
        if not success_members or len(members) < 1:
            return self.log_test(
                "Head-to-Head Endpoint", 
                False, 
                f"Need at least 1 member for testing. Found: {len(members) if success_members else 0}"
            )
        
        # Use the same user twice for testing (should still work)
        user1_id = members[0]['user_id']
        user2_id = members[1]['user_id'] if len(members) > 1 else members[0]['user_id']
        
        success, status, data = self.make_request(
            'GET',
            f'analytics/head-to-head/{self.test_league_id}?user1_id={user1_id}&user2_id={user2_id}'
        )
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'league_id' in data and
            'comparison' in data and
            isinstance(data['comparison'], list)
        )
        
        return self.log_test(
            "Head-to-Head Endpoint",
            valid_response,
            f"Status: {status}, Valid structure: {valid_response}, Comparisons: {len(data.get('comparison', []))}"
        )
    
    def test_access_control(self):
        """Test access control for aggregation endpoints"""
        # Test without authentication token
        endpoints_to_test = [
            f'clubs/my-clubs/{self.test_league_id}',
            f'fixtures/{self.test_league_id}',
            f'leaderboard/{self.test_league_id}',
            f'analytics/head-to-head/{self.test_league_id}?user1_id=test1&user2_id=test2'
        ]
        
        unauthorized_results = []
        status_codes = []
        for endpoint in endpoints_to_test:
            success, status, data = self.make_request(
                'GET',
                endpoint,
                token=None,  # No token
                expected_status=403  # FastAPI returns 403 for "Not authenticated"
            )
            status_codes.append(status)
            unauthorized_results.append(status in [401, 403])  # Accept both 401 and 403
        
        access_control_working = all(unauthorized_results)
        
        return self.log_test(
            "Access Control",
            access_control_working,
            f"Unauthorized blocked: {sum(unauthorized_results)}/{len(unauthorized_results)}, Status codes: {status_codes}"
        )

    def run_tests(self):
        """Run all aggregation endpoint tests"""
        print("🚀 Starting UCL Auction Aggregation API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Authentication and setup
        print("\n🔐 AUTHENTICATION AND SETUP")
        if not self.authenticate_and_setup():
            print("❌ Authentication/setup failed - aborting tests")
            return 1
        
        # Aggregation endpoint tests
        print("\n📊 AGGREGATION ENDPOINTS TESTS")
        self.test_my_clubs_endpoint()
        self.test_fixtures_endpoint()
        self.test_leaderboard_endpoint()
        self.test_head_to_head_endpoint()
        
        # Security tests
        print("\n🔒 SECURITY TESTS")
        self.test_access_control()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All aggregation API tests passed!")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = AggregationEndpointTester()
    return tester.run_tests()

if __name__ == "__main__":
    sys.exit(main())