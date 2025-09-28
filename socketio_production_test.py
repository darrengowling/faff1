#!/usr/bin/env python3
"""
Socket.IO Configuration and Production Readiness Testing Suite
Tests Socket.IO configuration, critical backend endpoints, and production readiness
"""

import requests
import sys
import json
import os
import time
import socketio
from datetime import datetime, timezone
import subprocess

class SocketIOProductionTester:
    def __init__(self, base_url="https://pifa-auction.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.test_email = "socketio_test@example.com"
        
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
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
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
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    # ==================== SOCKET.IO CONFIGURATION TESTS ====================
    
    def test_socket_config_endpoint(self):
        """Test /api/socket/config endpoint returns correct path"""
        success, status, data = self.make_request('GET', 'socket/config', token=None)
        
        config_valid = (
            success and
            'path' in data and
            data['path'] == '/api/socketio'
        )
        
        return self.log_test(
            "Socket.IO Config Endpoint",
            config_valid,
            f"Status: {status}, Path: {data.get('path', 'Unknown')}"
        )

    def test_socketio_diagnostics(self):
        """Test Socket.IO diagnostic endpoints"""
        # Test main diagnostic endpoint
        success, status, data = self.make_request('GET', 'socketio/diag', token=None)
        
        if not success:
            # Try alternative endpoint
            success, status, data = self.make_request('GET', 'socket-diag', token=None)
        
        diag_valid = (
            success and
            isinstance(data, dict) and
            data.get('ok') is True and
            'path' in data and
            'now' in data and
            data['path'] == '/api/socketio'
        )
        
        return self.log_test(
            "Socket.IO Diagnostics",
            diag_valid,
            f"Status: {status}, Path: {data.get('path', 'Unknown')}, OK: {data.get('ok', False)}"
        )

    def test_socketio_connection_polling(self):
        """Test Socket.IO connection via polling transport"""
        try:
            # Test Engine.IO handshake with polling
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/api/socketio/?EIO=4&transport=polling",
                timeout=10
            )
            polling_time = (time.time() - start_time) * 1000  # Convert to ms
            
            handshake_success = (
                response.status_code == 200 and
                response.text.startswith('0{') and
                '"sid"' in response.text
            )
            
            return self.log_test(
                "Socket.IO Polling Connection",
                handshake_success,
                f"Status: {response.status_code}, Time: {polling_time:.0f}ms, Response starts: {response.text[:20]}"
            )
            
        except Exception as e:
            return self.log_test(
                "Socket.IO Polling Connection",
                False,
                f"Connection failed: {str(e)}"
            )

    def test_socketio_connection_websocket(self):
        """Test Socket.IO connection via websocket transport"""
        try:
            # Create Socket.IO client
            sio_client = socketio.SimpleClient()
            
            start_time = time.time()
            # Connect with websocket transport
            sio_client.connect(
                self.base_url,
                socketio_path='/api/socketio',
                transports=['websocket'],
                wait_timeout=10
            )
            websocket_time = (time.time() - start_time) * 1000  # Convert to ms
            
            connected = sio_client.connected
            
            # Disconnect
            if connected:
                sio_client.disconnect()
            
            return self.log_test(
                "Socket.IO WebSocket Connection",
                connected,
                f"Connected: {connected}, Time: {websocket_time:.0f}ms"
            )
            
        except Exception as e:
            return self.log_test(
                "Socket.IO WebSocket Connection",
                False,
                f"WebSocket connection failed: {str(e)}"
            )

    def test_path_consistency(self):
        """Test path consistency between frontend env and backend config"""
        # Read frontend .env file
        try:
            with open('/app/frontend/.env', 'r') as f:
                frontend_env = f.read()
            
            # Extract socket path from frontend env
            frontend_socket_path = None
            for line in frontend_env.split('\n'):
                if 'REACT_APP_SOCKET_PATH=' in line:
                    frontend_socket_path = line.split('=')[1].strip()
                    break
            
            # Get backend socket path from config endpoint
            success, status, data = self.make_request('GET', 'socket/config', token=None)
            backend_socket_path = data.get('path') if success else None
            
            paths_consistent = (
                frontend_socket_path is not None and
                backend_socket_path is not None and
                frontend_socket_path == backend_socket_path == '/api/socketio'
            )
            
            return self.log_test(
                "Socket.IO Path Consistency",
                paths_consistent,
                f"Frontend: {frontend_socket_path}, Backend: {backend_socket_path}"
            )
            
        except Exception as e:
            return self.log_test(
                "Socket.IO Path Consistency",
                False,
                f"Failed to check path consistency: {str(e)}"
            )

    # ==================== CRITICAL BACKEND API TESTS ====================
    
    def test_authentication_flow(self):
        """Test complete authentication flow"""
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success or 'dev_magic_link' not in data:
            return self.log_test("Authentication Flow", False, f"Magic link request failed: {status}")
        
        # Step 2: Extract and verify token
        magic_link = data['dev_magic_link']
        token = magic_link.split('token=')[1]
        
        # Step 3: Verify magic link token
        success, status, auth_data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if not success:
            return self.log_test("Authentication Flow", False, f"Token verification failed: {status}")
        
        # Step 4: Test user profile endpoint
        self.token = auth_data['access_token']
        success, status, profile_data = self.make_request('GET', 'auth/me')
        
        auth_flow_complete = (
            success and
            'access_token' in auth_data and
            'user' in auth_data and
            profile_data.get('email') == self.test_email
        )
        
        return self.log_test(
            "Authentication Flow",
            auth_flow_complete,
            f"Magic link ✓, Token verification ✓, Profile access ✓"
        )

    def test_league_management(self):
        """Test league management functionality"""
        if not self.token:
            return self.log_test("League Management", False, "No authentication token")
        
        # Create league
        league_data = {
            "name": f"Production Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "league_size": {"min": 2, "max": 8},
                "scoring_rules": {"club_goal": 1, "club_win": 3, "club_draw": 1}
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if not success:
            return self.log_test("League Management", False, f"League creation failed: {status}")
        
        self.test_league_id = data['id']
        
        # Test league settings retrieval
        success2, status2, settings = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        
        # Test member management
        success3, status3, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        
        # Test invitation system
        success4, status4, invite_data = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"email": "test_manager@example.com"}
        )
        
        league_mgmt_working = (
            success and success2 and success3 and success4 and
            'clubSlots' in settings and
            isinstance(members, list) and
            'message' in invite_data
        )
        
        return self.log_test(
            "League Management",
            league_mgmt_working,
            f"Creation ✓, Settings ✓, Members ✓, Invitations ✓"
        )

    def test_auction_system(self):
        """Test auction system endpoints"""
        if not self.test_league_id:
            return self.log_test("Auction System", False, "No test league ID")
        
        # Test auction start (expected to fail due to insufficient members)
        success, status, data = self.make_request('POST', f'auction/{self.test_league_id}/start')
        auction_start_handled = success or status == 400  # 400 expected for insufficient members
        
        # Test auction state retrieval
        success2, status2, state_data = self.make_request('GET', f'auction/{self.test_league_id}/state')
        state_handled = success2 or status2 == 404  # 404 expected for inactive auction
        
        # Test bid placement endpoint
        success3, status3, bid_data = self.make_request(
            'POST',
            f'auction/{self.test_league_id}/bid',
            {"lot_id": "test_lot", "amount": 10},
            expected_status=400
        )
        bid_endpoint_works = success3 and status3 == 400  # Expected failure
        
        # Test auction control endpoints
        success4, status4, pause_data = self.make_request('POST', f'auction/{self.test_league_id}/pause')
        pause_handled = success4 or status4 in [400, 404]
        
        auction_system_working = (
            auction_start_handled and
            state_handled and
            bid_endpoint_works and
            pause_handled
        )
        
        return self.log_test(
            "Auction System",
            auction_system_working,
            f"Start: {status}, State: {status2}, Bid: {status3}, Pause: {status4}"
        )

    def test_health_endpoint_detailed(self):
        """Test health endpoint with detailed system information"""
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Health Endpoint Detailed", False, f"Health check failed: {status}")
        
        # Check for detailed health information
        detailed_health = (
            'status' in data and
            'timestamp' in data and
            'database' in data and
            'system' in data and
            'services' in data and
            data['database'].get('connected') is True and
            'cpu_percent' in data['system'] and
            'memory_percent' in data['system'] and
            'websocket' in data['services'] and
            'auth' in data['services']
        )
        
        return self.log_test(
            "Health Endpoint Detailed",
            detailed_health,
            f"Status: {data.get('status')}, DB: {data.get('database', {}).get('connected')}, Services: {len(data.get('services', {}))}"
        )

    # ==================== CONFIGURATION VALIDATION ====================
    
    def test_environment_variables(self):
        """Test that all required environment variables are properly set"""
        # Test backend environment variables through health endpoint
        success, status, health_data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Environment Variables", False, f"Health check failed: {status}")
        
        # Check critical services are configured
        services = health_data.get('services', {})
        env_properly_configured = (
            services.get('websocket') is True and
            services.get('auth') is True and
            health_data.get('database', {}).get('connected') is True
        )
        
        # Test frontend environment variables by checking if they're accessible
        try:
            with open('/app/frontend/.env', 'r') as f:
                frontend_env = f.read()
            
            required_vars = [
                'REACT_APP_BACKEND_URL',
                'REACT_APP_SOCKET_PATH'
            ]
            
            frontend_vars_present = all(var in frontend_env for var in required_vars)
            
        except Exception:
            frontend_vars_present = False
        
        return self.log_test(
            "Environment Variables",
            env_properly_configured and frontend_vars_present,
            f"Backend services configured: {env_properly_configured}, Frontend vars: {frontend_vars_present}"
        )

    def test_config_gate_script(self):
        """Run config gate script to ensure frontend/backend path consistency"""
        try:
            # Check if config gate script exists
            script_path = '/app/scripts/verify-socket-config.mjs'
            if not os.path.exists(script_path):
                return self.log_test(
                    "Config Gate Script",
                    False,
                    "Config gate script not found at /app/scripts/verify-socket-config.mjs"
                )
            
            # Run the config gate script
            result = subprocess.run(
                ['node', script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            script_success = result.returncode == 0
            
            return self.log_test(
                "Config Gate Script",
                script_success,
                f"Exit code: {result.returncode}, Output: {result.stdout[:100]}"
            )
            
        except subprocess.TimeoutExpired:
            return self.log_test("Config Gate Script", False, "Script execution timed out")
        except Exception as e:
            return self.log_test("Config Gate Script", False, f"Script execution failed: {str(e)}")

    def test_diagnostic_endpoints(self):
        """Test all diagnostic endpoints functionality"""
        diagnostic_results = []
        
        # Test Socket.IO diagnostics
        success, status, data = self.make_request('GET', 'socket-diag', token=None)
        socketio_diag = success and data.get('ok') is True
        diagnostic_results.append(socketio_diag)
        
        # Test health endpoint
        success2, status2, data2 = self.make_request('GET', 'health', token=None)
        health_diag = success2 and data2.get('status') == 'healthy'
        diagnostic_results.append(health_diag)
        
        # Test time sync endpoint
        success3, status3, data3 = self.make_request('GET', 'timez', token=None)
        time_diag = success3 and 'now' in data3
        diagnostic_results.append(time_diag)
        
        # Test version endpoint
        success4, status4, data4 = self.make_request('GET', '../version', token=None)
        version_diag = success4 or status4 == 404  # 404 is acceptable
        diagnostic_results.append(version_diag)
        
        all_diagnostics_working = sum(diagnostic_results) >= 3  # At least 3/4 should work
        
        return self.log_test(
            "Diagnostic Endpoints",
            all_diagnostics_working,
            f"Working diagnostics: {sum(diagnostic_results)}/4 (Socket.IO: {socketio_diag}, Health: {health_diag}, Time: {time_diag}, Version: {version_diag})"
        )

    # ==================== PRODUCTION READINESS ASSESSMENT ====================
    
    def assess_production_readiness(self):
        """Assess overall production readiness"""
        critical_systems = [
            ("Socket.IO Configuration", "Socket.IO Config Endpoint" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Socket.IO Connectivity", "Socket.IO Polling Connection" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Authentication System", "Authentication Flow" not in [t.split(':')[0] for t in self.failed_tests]),
            ("League Management", "League Management" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Health Monitoring", "Health Endpoint Detailed" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Environment Config", "Environment Variables" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        working_systems = sum(1 for _, status in critical_systems if status)
        total_systems = len(critical_systems)
        
        production_ready = working_systems >= 5  # At least 5/6 critical systems must work
        
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        print(f"Critical Systems Working: {working_systems}/{total_systems}")
        
        for system, status in critical_systems:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {system}")
        
        readiness_status = "PRODUCTION READY" if production_ready else "NOT PRODUCTION READY"
        readiness_icon = "🟢" if production_ready else "🔴"
        
        print(f"\n{readiness_icon} STATUS: {readiness_status}")
        
        return production_ready

    # ==================== MAIN TEST RUNNER ====================
    
    def run_production_tests(self):
        """Run Socket.IO configuration and production readiness tests"""
        print("🚀 SOCKET.IO CONFIGURATION & PRODUCTION READINESS TESTING")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 70)
        
        # Socket.IO Configuration Tests
        print("\n🔌 SOCKET.IO CONFIGURATION TESTS")
        self.test_socket_config_endpoint()
        self.test_socketio_diagnostics()
        self.test_socketio_connection_polling()
        self.test_socketio_connection_websocket()
        self.test_path_consistency()
        
        # Critical Backend API Tests
        print("\n🔐 CRITICAL BACKEND API TESTS")
        self.test_authentication_flow()
        self.test_league_management()
        self.test_auction_system()
        self.test_health_endpoint_detailed()
        
        # Configuration Validation Tests
        print("\n⚙️ CONFIGURATION VALIDATION TESTS")
        self.test_environment_variables()
        self.test_config_gate_script()
        self.test_diagnostic_endpoints()
        
        # Final Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        # Production Readiness Assessment
        production_ready = self.assess_production_readiness()
        
        return self.tests_passed, self.tests_run, self.failed_tests, production_ready

if __name__ == "__main__":
    tester = SocketIOProductionTester()
    passed, total, failed, production_ready = tester.run_production_tests()
    
    # Exit with appropriate code
    sys.exit(0 if production_ready else 1)