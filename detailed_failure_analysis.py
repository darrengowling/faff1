#!/usr/bin/env python3
"""
Detailed Backend API Failure Analysis
Provides exact error messages, status codes, and curl commands for failing endpoints
"""

import requests
import json
import sys
from datetime import datetime, timezone

class DetailedFailureAnalyzer:
    def __init__(self, base_url="https://pifa-stability.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.failures = []
        
        # Test data
        self.test_email = "detailed_test@example.com"
        self.manager_emails = [
            "manager1_detailed@example.com",
            "manager2_detailed@example.com"
        ]
        
    def log_failure(self, endpoint, method, status_code, response_data, request_data=None, headers=None):
        """Log detailed failure information"""
        failure = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response": response_data,
            "request_data": request_data,
            "headers": headers,
            "curl_command": self.generate_curl_command(endpoint, method, request_data, headers)
        }
        self.failures.append(failure)
        return failure
        
    def generate_curl_command(self, endpoint, method, request_data=None, headers=None):
        """Generate curl command for reproducing the request"""
        url = f"{self.api_url}/{endpoint}"
        
        curl_parts = [f"curl -X {method}"]
        
        if headers:
            for key, value in headers.items():
                curl_parts.append(f'-H "{key}: {value}"')
        
        if request_data:
            curl_parts.append(f"-d '{json.dumps(request_data)}'")
            
        curl_parts.append(f'"{url}"')
        
        return " ".join(curl_parts)
        
    def make_detailed_request(self, method, endpoint, data=None, expected_status=200, token=None):
        """Make HTTP request with detailed error logging"""
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
                response_data = {"text": response.text[:500]}  # Truncate long responses
                
            if not success:
                self.log_failure(endpoint, method, response.status_code, response_data, data, headers)
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            error_data = {"error": str(e)}
            self.log_failure(endpoint, method, 0, error_data, data, headers)
            return False, 0, error_data

    def setup_authentication(self):
        """Setup authentication for detailed testing"""
        print("🔐 Setting up authentication...")
        
        # Request magic link
        success, status, data = self.make_detailed_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success or 'dev_magic_link' not in data:
            print(f"❌ Magic link request failed: {status}")
            return False
        
        # Extract token
        magic_link = data['dev_magic_link']
        token = magic_link.split('token=')[1]
        
        # Verify token
        success, status, auth_data = self.make_detailed_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if success and 'access_token' in auth_data:
            self.token = auth_data['access_token']
            self.user_data = auth_data['user']
            print(f"✅ Authentication successful: {auth_data['user']['email']}")
            return True
        else:
            print(f"❌ Token verification failed: {status}")
            return False

    def analyze_health_endpoint_failure(self):
        """Analyze health endpoint routing issues"""
        print("\n🏥 ANALYZING HEALTH ENDPOINT FAILURES")
        print("-" * 50)
        
        # Test /health endpoint (should return frontend HTML)
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            print(f"GET /health - Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"Response preview: {response.text[:200]}...")
            
            if 'html' in response.headers.get('content-type', '').lower():
                print("❌ ISSUE: /health returns HTML (frontend) instead of backend JSON")
                
        except Exception as e:
            print(f"❌ /health request failed: {e}")
        
        # Test /api/health endpoint
        success, status, data = self.make_detailed_request('GET', 'health', token=None)
        print(f"\nGET /api/health - Status: {status}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if not success:
            print("❌ ISSUE: /api/health endpoint failing")
        elif data.get('ok') is True and len(data) == 1:
            print("❌ ISSUE: /api/health returns simple {ok: true} instead of detailed health info")

    def analyze_league_invitation_failures(self):
        """Analyze league invitation system failures"""
        print("\n📧 ANALYZING LEAGUE INVITATION FAILURES")
        print("-" * 50)
        
        if not self.test_league_id:
            print("❌ No test league available for invitation testing")
            return
            
        # Test invitation sending
        for i, email in enumerate(self.manager_emails):
            print(f"\nTesting invitation {i+1}: {email}")
            success, status, data = self.make_detailed_request(
                'POST',
                f'leagues/{self.test_league_id}/invite',
                {"email": email}
            )
            
            print(f"Status: {status}")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if not success:
                if status == 422:
                    print("❌ CRITICAL: 422 Unprocessable Entity - Validation error in invitation data")
                elif status == 400:
                    print("❌ CRITICAL: 400 Bad Request - Invalid invitation request")
                elif status == 500:
                    print("❌ CRITICAL: 500 Internal Server Error - Server-side invitation processing error")
        
        # Test getting invitations
        print(f"\nTesting invitation retrieval:")
        success, status, data = self.make_detailed_request('GET', f'leagues/{self.test_league_id}/invitations')
        print(f"Status: {status}")
        print(f"Response: {json.dumps(data, indent=2)}")

    def analyze_league_join_failures(self):
        """Analyze league join functionality failures"""
        print("\n🤝 ANALYZING LEAGUE JOIN FAILURES")
        print("-" * 50)
        
        if not self.test_league_id:
            print("❌ No test league available for join testing")
            return
            
        print(f"Testing direct league join for league: {self.test_league_id}")
        success, status, data = self.make_detailed_request('POST', f'leagues/{self.test_league_id}/join')
        
        print(f"Status: {status}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if not success:
            if status == 400:
                print("❌ CRITICAL: 400 Bad Request - League join blocked")
                if 'detail' in data:
                    print(f"   Error detail: {data['detail']}")
            elif status == 403:
                print("❌ CRITICAL: 403 Forbidden - Permission denied for league join")
            elif status == 422:
                print("❌ CRITICAL: 422 Unprocessable Entity - Validation error in join request")

    def analyze_auction_engine_failures(self):
        """Analyze auction engine start failures"""
        print("\n🔨 ANALYZING AUCTION ENGINE FAILURES")
        print("-" * 50)
        
        if not self.test_league_id:
            print("❌ No test league available for auction testing")
            return
            
        print(f"Testing auction start for league: {self.test_league_id}")
        success, status, data = self.make_detailed_request('POST', f'auction/{self.test_league_id}/start')
        
        print(f"Status: {status}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if not success:
            if status == 500:
                print("❌ CRITICAL: 500 Internal Server Error - Auction engine initialization failure")
                if 'detail' in data:
                    print(f"   Error detail: {data['detail']}")
            elif status == 400:
                print("❌ ISSUE: 400 Bad Request - League not ready for auction")
            elif status == 403:
                print("❌ ISSUE: 403 Forbidden - Permission denied for auction start")

    def create_test_league(self):
        """Create a test league for failure analysis"""
        if not self.token:
            print("❌ No authentication token for league creation")
            return False
            
        league_data = {
            "name": f"Detailed Test League {datetime.now().strftime('%H%M%S')}",
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
        
        success, status, data = self.make_detailed_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            self.test_league_id = data['id']
            print(f"✅ Test league created: {self.test_league_id}")
            return True
        else:
            print(f"❌ League creation failed: {status}")
            return False

    def check_backend_logs(self):
        """Check backend logs for additional error information"""
        print("\n📋 CHECKING BACKEND LOGS")
        print("-" * 50)
        
        try:
            import subprocess
            result = subprocess.run(
                ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout:
                print("Recent backend error logs:")
                print(result.stdout)
            else:
                print("No recent backend error logs found")
                
        except Exception as e:
            print(f"Could not access backend logs: {e}")

    def run_detailed_analysis(self):
        """Run comprehensive failure analysis"""
        print("🔍 DETAILED BACKEND API FAILURE ANALYSIS")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
            
        # Create test league
        self.create_test_league()
        
        # Analyze specific failure areas
        self.analyze_health_endpoint_failure()
        self.analyze_league_invitation_failures()
        self.analyze_league_join_failures()
        self.analyze_auction_engine_failures()
        
        # Check backend logs
        self.check_backend_logs()
        
        # Generate failure summary
        print("\n" + "=" * 60)
        print("📊 DETAILED FAILURE ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total Failed Requests Analyzed: {len(self.failures)}")
        
        if self.failures:
            print(f"\n❌ DETAILED FAILURE BREAKDOWN:")
            for i, failure in enumerate(self.failures, 1):
                print(f"\n{i}. {failure['method']} /{failure['endpoint']}")
                print(f"   Status Code: {failure['status_code']}")
                print(f"   Response: {json.dumps(failure['response'], indent=6)}")
                print(f"   Curl Command: {failure['curl_command']}")
        
        print(f"\n🔧 CURL COMMANDS FOR DEBUGGING:")
        print("-" * 40)
        for failure in self.failures:
            print(f"# {failure['method']} /{failure['endpoint']} (Status: {failure['status_code']})")
            print(failure['curl_command'])
            print()
        
        return self.failures

if __name__ == "__main__":
    analyzer = DetailedFailureAnalyzer()
    failures = analyzer.run_detailed_analysis()
    
    # Exit with appropriate code
    sys.exit(0 if len(failures) == 0 else 1)