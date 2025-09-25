#!/usr/bin/env python3
"""
Final UCL Auction Aggregation API Test
"""

import requests
import sys
import json
from datetime import datetime

class FinalAggregationTester:
    def __init__(self, base_url="https://realtime-socket-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.access_token = None
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

    def make_request(self, method, endpoint, data=None, token=None, expect_success=True):
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
            
            response_data = {}
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return 0, {"error": str(e)}

    def setup_test_environment(self):
        """Set up authentication and test league"""
        print("🔐 Setting up test environment...")
        
        # Verify the magic link token
        status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": self.magic_token},
            token=None
        )
        
        if status != 200 or 'access_token' not in data:
            print(f"❌ Token verification failed: {status} - {data}")
            return False
        
        self.access_token = data['access_token']
        print(f"✅ Authenticated as {data['user']['email']}")
        
        # Create test league
        league_data = {
            "name": f"Final Test League {datetime.now().strftime('%H%M%S')}",
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
        
        status, data = self.make_request('POST', 'leagues', league_data)
        
        if status == 200 and 'id' in data:
            self.test_league_id = data['id']
            print(f"✅ Test league created: {self.test_league_id}")
            return True
        else:
            print(f"❌ Failed to create test league: {status} - {data}")
            return False

    def test_aggregation_endpoints(self):
        """Test all 4 aggregation endpoints"""
        endpoints = [
            ('My Clubs', f'clubs/my-clubs/{self.test_league_id}'),
            ('Fixtures', f'fixtures/{self.test_league_id}'),
            ('Leaderboard', f'leaderboard/{self.test_league_id}'),
            ('Head-to-Head', f'analytics/head-to-head/{self.test_league_id}?user1_id=test1&user2_id=test2')
        ]
        
        print("\n📊 Testing aggregation endpoints with authentication:")
        for name, endpoint in endpoints:
            status, data = self.make_request('GET', endpoint)
            success = status == 200 and isinstance(data, dict)
            self.log_test(f"{name} Endpoint (Authenticated)", success, f"Status: {status}")
        
        print("\n🔒 Testing aggregation endpoints without authentication:")
        for name, endpoint in endpoints:
            status, data = self.make_request('GET', endpoint, token=None)
            success = status in [401, 403]  # Should be unauthorized
            self.log_test(f"{name} Endpoint (Unauthorized)", success, f"Status: {status}")

    def run_tests(self):
        """Run all tests"""
        print("🚀 Final UCL Auction Aggregation API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        if not self.setup_test_environment():
            return 1
        
        self.test_aggregation_endpoints()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 FINAL TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = FinalAggregationTester()
    return tester.run_tests()

if __name__ == "__main__":
    sys.exit(main())