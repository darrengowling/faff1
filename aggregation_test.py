#!/usr/bin/env python3
"""
UCL Auction Aggregation API Testing Suite
Tests the 4 new aggregation endpoints added to server.py
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class AggregationAPITester:
    def __init__(self, base_url="https://livebid-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.access_token = None
        self.user_data = {}
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test user data
        self.test_email = f"aggregation_test_{int(time.time())}@example.com"
        
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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_health_check(self):
        """Test health check endpoint"""
        success, status, data = self.make_request('GET', 'health')
        return self.log_test(
            "Health Check", 
            success and 'status' in data and data['status'] == 'healthy',
            f"Status: {status}"
        )

    def authenticate_and_setup(self):
        """Authenticate user and set up test league"""
        print("🔐 Setting up authentication and test league...")
        
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success:
            print(f"❌ Failed to request magic link: {status}")
            return False
        
        print(f"📧 Magic link requested for {self.test_email}")
        print("⚠️  MANUAL STEP REQUIRED:")
        print("   1. Check backend logs for the magic link token")
        print("   2. Extract the token from the logs")
        print("   3. Enter the token when prompted")
        
        # Get token from user input
        token = input("\n🔑 Enter the magic link token from backend logs: ").strip()
        
        if not token:
            print("❌ No token provided")
            return False
        
        # Step 2: Verify token
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if not success or 'access_token' not in data:
            print(f"❌ Token verification failed: {status}")
            return False
        
        self.access_token = data['access_token']
        self.user_data = data['user']
        print(f"✅ Authenticated as {data['user']['email']}")
        
        # Step 3: Seed clubs
        success, status, data = self.make_request('POST', 'clubs/seed')
        if success:
            print("✅ Clubs seeded successfully")
        
        # Step 4: Create test league
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
            print(f"❌ Failed to create test league: {status}")
            return False

    def test_my_clubs_endpoint(self):
        """Test /api/clubs/my-clubs/{league_id} endpoint"""
        if not self.test_league_id or not self.access_token:
            return self.log_test("My Clubs Endpoint", False, "Missing league ID or token")
        
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
        if not self.test_league_id or not self.access_token:
            return self.log_test("Fixtures Endpoint", False, "Missing league ID or token")
        
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
        if not self.test_league_id or not self.access_token:
            return self.log_test("Leaderboard Endpoint", False, "Missing league ID or token")
        
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
        
        # Check leaderboard entry structure (if any entries exist)
        leaderboard_valid = True
        if valid_response and data['leaderboard']:
            first_entry = data['leaderboard'][0]
            leaderboard_valid = (
                'user_id' in first_entry and
                'display_name' in first_entry and
                'total_points' in first_entry and
                'position' in first_entry and
                'budget_remaining' in first_entry
            )
        
        return self.log_test(
            "Leaderboard Endpoint",
            valid_response and leaderboard_valid,
            f"Status: {status}, Valid structure: {valid_response}, Leaderboard valid: {leaderboard_valid}, Managers: {data.get('total_managers', 0)}"
        )
    
    def test_head_to_head_endpoint(self):
        """Test /api/analytics/head-to-head/{league_id} endpoint"""
        if not self.test_league_id or not self.access_token:
            return self.log_test("Head-to-Head Endpoint", False, "Missing league ID or token")
        
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
        
        # Check comparison entry structure (if any entries exist)
        comparison_valid = True
        if valid_response and data['comparison']:
            first_comparison = data['comparison'][0]
            comparison_valid = (
                'user_id' in first_comparison and
                'display_name' in first_comparison and
                'total_points' in first_comparison and
                'matches_played' in first_comparison
            )
        
        return self.log_test(
            "Head-to-Head Endpoint",
            valid_response and comparison_valid,
            f"Status: {status}, Valid structure: {valid_response}, Comparison valid: {comparison_valid}, Comparisons: {len(data.get('comparison', []))}"
        )
    
    def test_access_control(self):
        """Test access control for aggregation endpoints"""
        if not self.test_league_id:
            return self.log_test("Access Control", False, "Missing league ID")
        
        # Test without authentication token
        endpoints_to_test = [
            f'clubs/my-clubs/{self.test_league_id}',
            f'fixtures/{self.test_league_id}',
            f'leaderboard/{self.test_league_id}',
            f'analytics/head-to-head/{self.test_league_id}?user1_id=test1&user2_id=test2'
        ]
        
        unauthorized_results = []
        for endpoint in endpoints_to_test:
            success, status, data = self.make_request(
                'GET',
                endpoint,
                token=None,  # No token
                expected_status=401
            )
            unauthorized_results.append(status == 401)
        
        # Test with invalid league ID
        fake_league_id = "fake_league_id_12345"
        invalid_league_results = []
        for endpoint_template in ['clubs/my-clubs/{}', 'fixtures/{}', 'leaderboard/{}']:
            endpoint = endpoint_template.format(fake_league_id)
            success, status, data = self.make_request(
                'GET',
                endpoint,
                expected_status=403  # Should be forbidden or not found
            )
            invalid_league_results.append(status in [403, 404, 500])  # Accept various error codes
        
        access_control_working = (
            all(unauthorized_results) and  # All should return 401 without token
            all(invalid_league_results)    # All should return error with invalid league
        )
        
        return self.log_test(
            "Access Control",
            access_control_working,
            f"Unauthorized blocked: {sum(unauthorized_results)}/{len(unauthorized_results)}, Invalid league blocked: {sum(invalid_league_results)}/{len(invalid_league_results)}"
        )
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        if not self.access_token:
            return self.log_test("Error Handling", False, "Missing access token")
        
        error_tests = []
        
        # Test with non-existent league ID
        success, status, data = self.make_request(
            'GET',
            'clubs/my-clubs/nonexistent_league_id',
            expected_status=403
        )
        error_tests.append(status in [403, 404, 500])
        
        # Test head-to-head with missing parameters
        success, status, data = self.make_request(
            'GET',
            f'analytics/head-to-head/{self.test_league_id}',  # Missing user IDs
            expected_status=400
        )
        error_tests.append(status in [400, 422, 500])  # Various error codes acceptable
        
        # Test with malformed league ID
        success, status, data = self.make_request(
            'GET',
            'leaderboard/invalid-league-format',
            expected_status=403
        )
        error_tests.append(status in [403, 404, 500])
        
        error_handling_working = all(error_tests)
        
        return self.log_test(
            "Error Handling",
            error_handling_working,
            f"Error scenarios handled: {sum(error_tests)}/{len(error_tests)}"
        )

    def run_aggregation_tests(self):
        """Run comprehensive aggregation API tests"""
        print("🚀 Starting UCL Auction Aggregation API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Basic connectivity
        print("\n📡 CONNECTIVITY TESTS")
        if not self.test_health_check():
            print("❌ Health check failed - aborting tests")
            return 1
        
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
        
        # Security and error handling tests
        print("\n🔒 SECURITY AND ERROR HANDLING TESTS")
        self.test_access_control()
        self.test_error_handling()
        
        # Print detailed summary
        print("\n" + "=" * 80)
        print(f"📊 AGGREGATION API TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All aggregation API tests passed!")
            print("✅ My Clubs endpoint working correctly")
            print("✅ Fixtures endpoint working correctly")
            print("✅ Leaderboard endpoint working correctly")
            print("✅ Head-to-Head endpoint working correctly")
            print("✅ Access control functioning properly")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed - see details above")
            return 1

def main():
    """Main test runner"""
    tester = AggregationAPITester()
    return tester.run_aggregation_tests()

if __name__ == "__main__":
    sys.exit(main())