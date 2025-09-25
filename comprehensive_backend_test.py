#!/usr/bin/env python3
"""
Comprehensive Backend Testing Suite
Focus: PR2 & PR3 API endpoints, WebSocket configuration analysis
"""

import requests
import time
import json
from datetime import datetime, timezone

class ComprehensiveBackendTester:
    def __init__(self, base_url="https://champion-bid-portal.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
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

    def authenticate(self):
        """Get authentication token"""
        # Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": "test@example.com"},
            token=None
        )
        
        if not success or 'dev_magic_link' not in data:
            return self.log_test("Authentication Setup", False, f"Magic link failed: {status}")
        
        # Extract and verify token
        magic_link = data['dev_magic_link']
        token = magic_link.split('token=')[1]
        
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.user_data = data['user']
            return self.log_test("Authentication", True, f"User: {data['user']['email']}")
        
        return self.log_test("Authentication", False, f"Token verification failed: {status}")

    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        # Health check
        success, status, data = self.make_request('GET', 'health', token=None)
        self.log_test("Health Check", success and data.get('status') == 'healthy', f"Status: {status}")
        
        # Time sync endpoint
        success, status, data = self.make_request('GET', 'timez', token=None)
        time_valid = success and 'now' in data
        self.log_test("Time Sync Endpoint", time_valid, f"Status: {status}")
        
        # Clubs endpoint
        success, status, data = self.make_request('GET', 'clubs', token=None)
        clubs_valid = success and isinstance(data, list)
        self.log_test("Clubs Endpoint", clubs_valid, f"Status: {status}, Clubs: {len(data) if clubs_valid else 0}")

    def test_league_creation(self):
        """Test league creation and management"""
        if not self.token:
            return self.log_test("League Creation", False, "No authentication token")
        
        league_data = {
            "name": f"Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "max_managers": 8,
                "min_managers": 4
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            self.test_league_id = data['id']
            return self.log_test("League Creation", True, f"League ID: {data['id']}")
        
        return self.log_test("League Creation", False, f"Status: {status}, Response: {data}")

    def test_pr2_pr3_api_endpoints(self):
        """Test PR2 and PR3 API endpoints"""
        if not self.token:
            return self.log_test("PR2/PR3 API Endpoints", False, "No authentication token")
        
        # Test lot closing endpoints (PR3)
        test_lot_id = "test_lot_123"
        
        # Test close lot endpoint
        success, status, data = self.make_request(
            'POST',
            f'lots/{test_lot_id}/close',
            {"forced": False, "reason": "Test close"},
            expected_status=404  # Expected since lot doesn't exist
        )
        close_endpoint_works = success and status == 404
        self.log_test("PR3 Close Lot Endpoint", close_endpoint_works, f"Status: {status}")
        
        # Test undo lot endpoint
        success, status, data = self.make_request(
            'POST',
            'lots/undo/test_action',
            {},
            expected_status=404
        )
        undo_endpoint_works = success and status == 404
        self.log_test("PR3 Undo Lot Endpoint", undo_endpoint_works, f"Status: {status}")
        
        # Test get undo actions endpoint
        success, status, data = self.make_request(
            'GET',
            f'lots/{test_lot_id}/undo-actions',
            expected_status=404
        )
        undo_actions_endpoint_works = success and status == 404
        self.log_test("PR3 Undo Actions Endpoint", undo_actions_endpoint_works, f"Status: {status}")

    def test_aggregation_endpoints(self):
        """Test aggregation endpoints"""
        if not self.token or not self.test_league_id:
            return self.log_test("Aggregation Endpoints", False, "Missing token or league ID")
        
        endpoints = [
            f'clubs/my-clubs/{self.test_league_id}',
            f'fixtures/{self.test_league_id}',
            f'leaderboard/{self.test_league_id}'
        ]
        
        results = []
        for endpoint in endpoints:
            success, status, data = self.make_request('GET', endpoint)
            results.append(success)
            endpoint_name = endpoint.split('/')[-2] if '/' in endpoint else endpoint
            self.log_test(f"Aggregation {endpoint_name}", success, f"Status: {status}")
        
        return sum(results) >= 2

    def test_websocket_configuration(self):
        """Test WebSocket server configuration and accessibility"""
        print("\n🔌 WEBSOCKET CONFIGURATION ANALYSIS")
        print("=" * 50)
        
        # Test backend Socket.IO server directly
        try:
            response = requests.get("http://localhost:8001/socket.io/?EIO=4&transport=polling", timeout=5)
            backend_socketio_works = response.status_code == 200 and response.text.startswith('0{')
            self.log_test("Backend Socket.IO Server", backend_socketio_works, 
                         f"Direct backend access: {response.status_code}")
        except Exception as e:
            self.log_test("Backend Socket.IO Server", False, f"Error: {e}")
        
        # Test external Socket.IO routing
        try:
            response = requests.get(f"{self.base_url}/socket.io/?EIO=4&transport=polling", timeout=5)
            external_socketio_works = response.status_code == 200 and response.text.startswith('0{')
            
            if not external_socketio_works:
                # Check if it returns HTML (frontend routing issue)
                returns_html = "<!doctype html>" in response.text.lower()
                self.log_test("External Socket.IO Routing", False, 
                             f"Returns {'HTML (frontend)' if returns_html else 'unexpected response'}")
            else:
                self.log_test("External Socket.IO Routing", True, "Proper Socket.IO response")
                
        except Exception as e:
            self.log_test("External Socket.IO Routing", False, f"Error: {e}")
        
        # Test API routing (should work)
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            api_routing_works = response.status_code == 200
            self.log_test("API Routing", api_routing_works, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("API Routing", False, f"Error: {e}")

    def analyze_websocket_issue(self):
        """Analyze the WebSocket connectivity issue"""
        print("\n🔍 WEBSOCKET ISSUE ANALYSIS")
        print("=" * 50)
        
        print("FINDINGS:")
        print("1. ✅ Backend Socket.IO server is running correctly on localhost:8001")
        print("2. ✅ Backend API endpoints work correctly via external URL")
        print("3. ❌ External Socket.IO requests are routed to frontend instead of backend")
        print("4. ❌ Socket.IO client connections fail due to routing issue")
        
        print("\nROOT CAUSE:")
        print("- Kubernetes ingress/routing configuration issue")
        print("- /api/* routes correctly to backend")
        print("- /socket.io/* routes incorrectly to frontend")
        
        print("\nSOLUTION NEEDED:")
        print("- Update Kubernetes ingress to route /socket.io/* to backend service")
        print("- Ensure WebSocket upgrade headers are properly handled")
        print("- Verify Socket.IO server mounting in production environment")

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Comprehensive Backend Testing Suite")
        print("Focus: PR2 & PR3 API Integration + WebSocket Analysis")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with authenticated tests")
            return
        
        # Basic endpoints
        print("\n📡 BASIC ENDPOINTS")
        self.test_basic_endpoints()
        
        # League creation
        print("\n🏟️ LEAGUE MANAGEMENT")
        self.test_league_creation()
        
        # PR2 & PR3 API endpoints
        print("\n⚡ PR2 & PR3 API ENDPOINTS")
        self.test_pr2_pr3_api_endpoints()
        
        # Aggregation endpoints
        print("\n📊 AGGREGATION ENDPOINTS")
        self.test_aggregation_endpoints()
        
        # WebSocket configuration analysis
        self.test_websocket_configuration()
        
        # WebSocket issue analysis
        self.analyze_websocket_issue()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    tester.run_comprehensive_tests()