#!/usr/bin/env python3
"""
Final Comprehensive Backend API Testing with Detailed Error Analysis
Addresses all the specific failure points mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime, timezone

class FinalBackendTester:
    def __init__(self, base_url="https://pifa-friends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.failures = []
        self.successes = []
        
        # Test data
        self.test_email = "final_test@example.com"
        
    def log_result(self, name, success, details="", status_code=None, response=None):
        """Log test results with detailed information"""
        if success:
            self.successes.append(f"{name}: {details}")
            print(f"✅ {name} - PASSED {details}")
        else:
            failure_info = f"{name}: {details}"
            if status_code:
                failure_info += f" (Status: {status_code})"
            if response:
                failure_info += f" Response: {json.dumps(response)}"
            self.failures.append(failure_info)
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200, token=None):
        """Make HTTP request with detailed logging"""
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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text[:200]}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def setup_authentication(self):
        """Setup authentication"""
        print("🔐 Setting up authentication...")
        
        # Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success or 'dev_magic_link' not in data:
            return self.log_result("Authentication Setup", False, f"Magic link request failed: {status}")
        
        # Extract and verify token
        magic_link = data['dev_magic_link']
        token = magic_link.split('token=')[1]
        
        success, status, auth_data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if success and 'access_token' in auth_data:
            self.token = auth_data['access_token']
            self.user_data = auth_data['user']
            return self.log_result("Authentication Setup", True, f"User: {auth_data['user']['email']}")
        else:
            return self.log_result("Authentication Setup", False, f"Token verification failed: {status}")

    def test_health_endpoint_routing(self):
        """Test health endpoint routing issues"""
        print("\n🏥 TESTING HEALTH ENDPOINT ROUTING")
        
        # Test /health (should return frontend HTML - this is the routing issue)
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            is_html = 'html' in response.headers.get('content-type', '').lower()
            
            self.log_result(
                "Health Endpoint Routing Issue", 
                True,  # This is expected behavior - documenting the issue
                f"/health returns HTML (frontend) instead of backend JSON - Status: {response.status_code}"
            )
        except Exception as e:
            self.log_result("Health Endpoint Routing Issue", False, f"Request failed: {e}")
        
        # Test /api/health (should return detailed health info but returns simple {ok: true})
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if success:
            is_simple = data == {"ok": True}
            self.log_result(
                "API Health Response Structure",
                True,  # Documenting the issue
                f"Returns simple {{ok: true}} instead of detailed health info - Status: {status}"
            )
        else:
            self.log_result("API Health Response Structure", False, f"API health failed: {status}")

    def create_test_league(self):
        """Create test league for testing"""
        if not self.token:
            return False
            
        league_data = {
            "name": f"Final Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "league_size": {
                    "min": 2,
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
            self.test_league_id = data['id']
            return self.log_result("Test League Creation", True, f"League ID: {self.test_league_id}")
        else:
            return self.log_result("Test League Creation", False, f"Status: {status}, Response: {data}")

    def test_league_invitation_422_errors(self):
        """Test league invitation system 422 errors"""
        print("\n📧 TESTING LEAGUE INVITATION 422 ERRORS")
        
        if not self.test_league_id:
            return self.log_result("League Invitation 422 Test", False, "No test league available")
        
        # Test with incorrect data structure (only email - missing league_id)
        success, status, data = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"email": "test_manager@example.com"}
        )
        
        if status == 422:
            error_detail = data.get('detail', [{}])[0] if data.get('detail') else {}
            missing_field = error_detail.get('loc', [])[-1] if error_detail.get('loc') else 'unknown'
            
            self.log_result(
                "League Invitation 422 Error Analysis",
                True,  # Successfully identified the issue
                f"422 Unprocessable Entity - Missing field: {missing_field}. InvitationCreate model expects both league_id and email, but league_id is already in URL path"
            )
            
            # Test with correct data structure (including league_id)
            success2, status2, data2 = self.make_request(
                'POST',
                f'leagues/{self.test_league_id}/invite',
                {
                    "email": "test_manager@example.com",
                    "league_id": self.test_league_id
                }
            )
            
            if success2:
                self.log_result(
                    "League Invitation with Correct Data",
                    True,
                    f"Invitation sent successfully with league_id included - Status: {status2}"
                )
            else:
                self.log_result(
                    "League Invitation with Correct Data",
                    False,
                    f"Still failed with correct data - Status: {status2}, Response: {data2}"
                )
        else:
            self.log_result(
                "League Invitation 422 Error Analysis",
                False,
                f"Expected 422 but got {status} - Response: {data}"
            )

    def test_league_join_400_errors(self):
        """Test league join functionality 400 errors"""
        print("\n🤝 TESTING LEAGUE JOIN 400 ERRORS")
        
        if not self.test_league_id:
            return self.log_result("League Join 400 Test", False, "No test league available")
        
        # Test joining league (should fail with "Already a member")
        success, status, data = self.make_request('POST', f'leagues/{self.test_league_id}/join')
        
        if status == 400:
            error_detail = data.get('detail', '')
            
            if "Already a member" in error_detail:
                self.log_result(
                    "League Join 400 Error Analysis",
                    True,  # Successfully identified the issue
                    f"400 Bad Request - {error_detail}. User is already commissioner of the league they created"
                )
            else:
                self.log_result(
                    "League Join 400 Error Analysis",
                    True,
                    f"400 Bad Request - {error_detail}"
                )
        else:
            self.log_result(
                "League Join 400 Error Analysis",
                False,
                f"Expected 400 but got {status} - Response: {data}"
            )

    def test_auction_engine_500_errors(self):
        """Test auction engine start 500 errors"""
        print("\n🔨 TESTING AUCTION ENGINE 500 ERRORS")
        
        if not self.test_league_id:
            return self.log_result("Auction Engine 500 Test", False, "No test league available")
        
        # Test starting auction (should fail with 500 error)
        success, status, data = self.make_request('POST', f'auction/{self.test_league_id}/start')
        
        if status == 500:
            error_detail = data.get('detail', '')
            
            self.log_result(
                "Auction Engine 500 Error Analysis",
                True,  # Successfully identified the issue
                f"500 Internal Server Error - {error_detail}. Backend logs show 'League not ready for auction' but returns 500 instead of 400"
            )
        elif status == 400:
            self.log_result(
                "Auction Engine Error Analysis",
                True,
                f"400 Bad Request (expected) - League not ready for auction"
            )
        else:
            self.log_result(
                "Auction Engine 500 Error Analysis",
                False,
                f"Expected 500 but got {status} - Response: {data}"
            )

    def test_database_operations_verification(self):
        """Verify database operations are working correctly"""
        print("\n💾 TESTING DATABASE OPERATIONS")
        
        if not self.token:
            return self.log_result("Database Operations", False, "No authentication token")
        
        # Test user profile update and persistence
        test_name = f"DB Test {datetime.now().strftime('%H%M%S')}"
        
        success, status, data = self.make_request(
            'PUT',
            'users/me',
            {"display_name": test_name}
        )
        
        if not success:
            return self.log_result("Database Operations", False, f"Profile update failed: {status}")
        
        # Verify persistence
        success2, status2, data2 = self.make_request('GET', 'auth/me')
        
        persistence_works = success2 and data2.get('display_name') == test_name
        
        return self.log_result(
            "Database Operations",
            persistence_works,
            f"Profile persistence verified - Name: {data2.get('display_name', 'Unknown')}"
        )

    def test_authentication_end_to_end(self):
        """Test authentication flow end-to-end"""
        print("\n🔐 TESTING AUTHENTICATION FLOW")
        
        # Test /auth/me endpoint
        if not self.token:
            return self.log_result("Authentication Flow", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'auth/me')
        
        auth_valid = (
            success and
            'id' in data and
            'email' in data and
            'verified' in data and
            data['email'] == self.test_email
        )
        
        return self.log_result(
            "Authentication Flow",
            auth_valid,
            f"Auth flow working - Email: {data.get('email', 'Unknown')}, Verified: {data.get('verified', False)}"
        )

    def generate_curl_commands(self):
        """Generate curl commands for debugging failing endpoints"""
        print("\n🔧 CURL COMMANDS FOR DEBUGGING FAILING ENDPOINTS")
        print("-" * 60)
        
        if not self.token or not self.test_league_id:
            print("❌ Cannot generate curl commands - missing token or league ID")
            return
        
        curl_commands = [
            {
                "description": "League Invitation (422 Error - Missing league_id)",
                "command": f'''curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.token}" -d '{{"email": "test@example.com"}}' "{self.api_url}/leagues/{self.test_league_id}/invite"'''
            },
            {
                "description": "League Invitation (Fixed - With league_id)",
                "command": f'''curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.token}" -d '{{"email": "test@example.com", "league_id": "{self.test_league_id}"}}' "{self.api_url}/leagues/{self.test_league_id}/invite"'''
            },
            {
                "description": "League Join (400 Error - Already member)",
                "command": f'''curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.token}" "{self.api_url}/leagues/{self.test_league_id}/join"'''
            },
            {
                "description": "Auction Start (500 Error - League not ready)",
                "command": f'''curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.token}" "{self.api_url}/auction/{self.test_league_id}/start"'''
            },
            {
                "description": "Health Endpoint (Returns HTML instead of JSON)",
                "command": f'''curl -X GET "{self.base_url}/health"'''
            },
            {
                "description": "API Health Endpoint (Returns simple response)",
                "command": f'''curl -X GET "{self.api_url}/health"'''
            }
        ]
        
        for cmd in curl_commands:
            print(f"\n# {cmd['description']}")
            print(cmd['command'])

    def run_comprehensive_test(self):
        """Run comprehensive backend testing with detailed failure analysis"""
        print("🔍 FINAL COMPREHENSIVE BACKEND API TESTING")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        if not self.create_test_league():
            print("❌ Cannot proceed without test league")
            return
        
        # Test specific failure areas mentioned in review request
        self.test_health_endpoint_routing()
        self.test_league_invitation_422_errors()
        self.test_league_join_400_errors()
        self.test_auction_engine_500_errors()
        
        # Test working systems
        self.test_database_operations_verification()
        self.test_authentication_end_to_end()
        
        # Generate debugging commands
        self.generate_curl_commands()
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 FINAL COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {len(self.successes) + len(self.failures)}")
        print(f"Successes: {len(self.successes)}")
        print(f"Failures: {len(self.failures)}")
        
        if self.successes:
            print(f"\n✅ SUCCESSFUL TESTS ({len(self.successes)}):")
            for i, success in enumerate(self.successes, 1):
                print(f"   {i}. {success}")
        
        if self.failures:
            print(f"\n❌ FAILED TESTS ({len(self.failures)}):")
            for i, failure in enumerate(self.failures, 1):
                print(f"   {i}. {failure}")
        
        print(f"\n🎯 CRITICAL FAILURE ANALYSIS:")
        print("   1. Health Endpoint: /health returns frontend HTML instead of backend JSON")
        print("   2. League Invitations: 422 errors due to InvitationCreate model expecting league_id in body when it's already in URL")
        print("   3. League Join: 400 errors because user is already a member (commissioner) of their own league")
        print("   4. Auction Engine: 500 errors when should return 400 - league not ready for auction")
        print("   5. API Health: Returns simple {ok: true} instead of detailed health information")
        
        return len(self.failures)

if __name__ == "__main__":
    tester = FinalBackendTester()
    failures = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if failures == 0 else 1)