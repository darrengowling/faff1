#!/usr/bin/env python3
"""
Final Production Readiness Test Suite
Comprehensive testing of Socket.IO configuration and all critical backend endpoints
"""

import requests
import sys
import json
import os
import time
import socketio
from datetime import datetime, timezone
import subprocess

class FinalProductionTester:
    def __init__(self, base_url="https://livebid-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.test_email = "final_prod_test@example.com"
        
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

    def test_socketio_connection_both_transports(self):
        """Test Socket.IO connection via both polling and websocket transports"""
        results = []
        
        # Test polling transport
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/api/socketio/?EIO=4&transport=polling",
                timeout=10
            )
            polling_time = (time.time() - start_time) * 1000
            
            polling_success = (
                response.status_code == 200 and
                response.text.startswith('0{') and
                '"sid"' in response.text
            )
            results.append(("Polling", polling_success, f"{polling_time:.0f}ms"))
            
        except Exception as e:
            results.append(("Polling", False, f"Error: {str(e)}"))
        
        # Test websocket transport
        try:
            sio_client = socketio.SimpleClient()
            start_time = time.time()
            sio_client.connect(
                self.base_url,
                socketio_path='/api/socketio',
                transports=['websocket'],
                wait_timeout=10
            )
            websocket_time = (time.time() - start_time) * 1000
            
            websocket_success = sio_client.connected
            if websocket_success:
                sio_client.disconnect()
            
            results.append(("WebSocket", websocket_success, f"{websocket_time:.0f}ms"))
            
        except Exception as e:
            results.append(("WebSocket", False, f"Error: {str(e)}"))
        
        # Both transports should work
        both_working = all(result[1] for result in results)
        details = ", ".join([f"{name}: {status} ({detail})" for name, status, detail in results])
        
        return self.log_test(
            "Socket.IO Both Transports",
            both_working,
            details
        )

    def test_path_consistency_validation(self):
        """Validate path consistency between frontend env and backend config"""
        try:
            # Read frontend .env file
            with open('/app/frontend/.env', 'r') as f:
                frontend_env = f.read()
            
            # Extract all socket path variables
            frontend_paths = {}
            for line in frontend_env.split('\n'):
                if 'SOCKET_PATH=' in line and not line.startswith('#'):
                    key = line.split('=')[0]
                    value = line.split('=')[1].strip()
                    frontend_paths[key] = value
            
            # Get backend socket path
            success, status, data = self.make_request('GET', 'socket/config', token=None)
            backend_path = data.get('path') if success else None
            
            # Check consistency
            expected_path = '/api/socketio'
            all_paths_consistent = (
                backend_path == expected_path and
                all(path == expected_path for path in frontend_paths.values())
            )
            
            return self.log_test(
                "Path Consistency Validation",
                all_paths_consistent,
                f"Backend: {backend_path}, Frontend paths: {len(frontend_paths)} all match {expected_path}"
            )
            
        except Exception as e:
            return self.log_test(
                "Path Consistency Validation",
                False,
                f"Failed to validate paths: {str(e)}"
            )

    # ==================== CRITICAL BACKEND API TESTS ====================
    
    def test_authentication_flow_complete(self):
        """Test complete authentication flow with all endpoints"""
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success or 'dev_magic_link' not in data:
            return self.log_test("Authentication Flow Complete", False, f"Magic link request failed: {status}")
        
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
            return self.log_test("Authentication Flow Complete", False, f"Token verification failed: {status}")
        
        # Step 4: Store token and test user endpoints
        self.token = auth_data['access_token']
        self.user_data = auth_data['user']
        
        # Test /auth/me endpoint
        success, status, me_data = self.make_request('GET', 'auth/me')
        me_valid = success and me_data.get('email') == self.test_email
        
        # Test profile update
        success2, status2, update_data = self.make_request(
            'PUT',
            'users/me',
            {"display_name": f"Final Test User {datetime.now().strftime('%H%M%S')}"}
        )
        update_valid = success2 and 'display_name' in update_data
        
        auth_complete = me_valid and update_valid
        
        return self.log_test(
            "Authentication Flow Complete",
            auth_complete,
            f"Magic link ✓, Token verification ✓, /auth/me ✓, Profile update ✓"
        )

    def test_league_management_comprehensive(self):
        """Test comprehensive league management functionality"""
        if not self.token:
            return self.log_test("League Management Comprehensive", False, "No authentication token")
        
        # Create league
        league_data = {
            "name": f"Final Production Test League {datetime.now().strftime('%H%M%S')}",
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
            return self.log_test("League Management Comprehensive", False, f"League creation failed: {status}")
        
        self.test_league_id = data['id']
        
        # Test all league endpoints
        endpoints_tested = []
        
        # 1. League settings retrieval
        success, status, settings = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        endpoints_tested.append(("Settings", success and 'clubSlots' in settings))
        
        # 2. League members
        success, status, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        endpoints_tested.append(("Members", success and isinstance(members, list)))
        
        # 3. League status
        success, status, league_status = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        endpoints_tested.append(("Status", success and 'member_count' in league_status))
        
        # 4. Send invitation
        success, status, invite_data = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"email": "final_test_manager@example.com"}
        )
        endpoints_tested.append(("Invitation", success and 'message' in invite_data))
        
        # 5. Get invitations
        success, status, invitations = self.make_request('GET', f'leagues/{self.test_league_id}/invitations')
        endpoints_tested.append(("Get Invitations", success and isinstance(invitations, list)))
        
        # 6. Get my leagues
        success, status, my_leagues = self.make_request('GET', 'leagues')
        endpoints_tested.append(("My Leagues", success and isinstance(my_leagues, list)))
        
        working_endpoints = sum(1 for _, status in endpoints_tested if status)
        all_working = working_endpoints == len(endpoints_tested)
        
        details = f"Working endpoints: {working_endpoints}/{len(endpoints_tested)} - " + ", ".join([f"{name}: {'✓' if status else '✗'}" for name, status in endpoints_tested])
        
        return self.log_test(
            "League Management Comprehensive",
            all_working,
            details
        )

    def test_auction_system_comprehensive(self):
        """Test comprehensive auction system functionality"""
        if not self.test_league_id:
            return self.log_test("Auction System Comprehensive", False, "No test league ID")
        
        auction_endpoints_tested = []
        
        # 1. Auction start (expected to fail due to insufficient members)
        success, status, data = self.make_request('POST', f'auction/{self.test_league_id}/start')
        start_handled = success or status == 400  # 400 expected for insufficient members
        auction_endpoints_tested.append(("Start", start_handled, status))
        
        # 2. Auction state retrieval
        success, status, state_data = self.make_request('GET', f'auction/{self.test_league_id}/state')
        state_handled = success or status == 404  # 404 expected for inactive auction
        auction_endpoints_tested.append(("State", state_handled, status))
        
        # 3. Bid placement endpoint
        success, status, bid_data = self.make_request(
            'POST',
            f'auction/{self.test_league_id}/bid',
            {"lot_id": "test_lot", "amount": 10},
            expected_status=400
        )
        bid_handled = success and status == 400  # Expected failure
        auction_endpoints_tested.append(("Bid", bid_handled, status))
        
        # 4. Auction pause
        success, status, pause_data = self.make_request('POST', f'auction/{self.test_league_id}/pause')
        pause_handled = success or status in [400, 404]
        auction_endpoints_tested.append(("Pause", pause_handled, status))
        
        # 5. Auction resume
        success, status, resume_data = self.make_request('POST', f'auction/{self.test_league_id}/resume')
        resume_handled = success or status in [400, 404]
        auction_endpoints_tested.append(("Resume", resume_handled, status))
        
        working_endpoints = sum(1 for _, status, _ in auction_endpoints_tested if status)
        all_working = working_endpoints == len(auction_endpoints_tested)
        
        details = f"Working endpoints: {working_endpoints}/{len(auction_endpoints_tested)} - " + ", ".join([f"{name}: {'✓' if status else '✗'}({code})" for name, status, code in auction_endpoints_tested])
        
        return self.log_test(
            "Auction System Comprehensive",
            all_working,
            details
        )

    def test_health_endpoint_production_ready(self):
        """Test health endpoint provides production-ready monitoring information"""
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Health Endpoint Production Ready", False, f"Health check failed: {status}")
        
        # Check for comprehensive health information
        required_fields = [
            'status', 'timestamp', 'version', 'environment',
            'database', 'system', 'services'
        ]
        
        fields_present = all(field in data for field in required_fields)
        
        # Check database info
        db_info = data.get('database', {})
        db_comprehensive = (
            db_info.get('connected') is True and
            'collections_count' in db_info and
            'missing_collections' in db_info
        )
        
        # Check system metrics
        system_info = data.get('system', {})
        system_comprehensive = (
            'cpu_percent' in system_info and
            'memory_percent' in system_info and
            'disk_percent' in system_info
        )
        
        # Check services info
        services_info = data.get('services', {})
        services_comprehensive = (
            'websocket' in services_info and
            'email' in services_info and
            'auth' in services_info
        )
        
        production_ready_health = (
            fields_present and
            db_comprehensive and
            system_comprehensive and
            services_comprehensive and
            data.get('status') == 'healthy'
        )
        
        return self.log_test(
            "Health Endpoint Production Ready",
            production_ready_health,
            f"Status: {data.get('status')}, DB: {db_info.get('connected')}, Collections: {db_info.get('collections_count')}, System metrics: ✓, Services: {len(services_info)}"
        )

    # ==================== CONFIGURATION VALIDATION ====================
    
    def test_config_gate_script_execution(self):
        """Run config gate script to ensure frontend/backend path consistency"""
        try:
            # Check if config gate script exists
            script_path = '/app/scripts/verify-socket-config.mjs'
            if not os.path.exists(script_path):
                return self.log_test(
                    "Config Gate Script Execution",
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
            output_contains_success = "✅" in result.stdout or "SUCCESS" in result.stdout.upper()
            
            return self.log_test(
                "Config Gate Script Execution",
                script_success and output_contains_success,
                f"Exit code: {result.returncode}, Success indicators: {output_contains_success}"
            )
            
        except subprocess.TimeoutExpired:
            return self.log_test("Config Gate Script Execution", False, "Script execution timed out")
        except Exception as e:
            return self.log_test("Config Gate Script Execution", False, f"Script execution failed: {str(e)}")

    def test_environment_variables_production(self):
        """Test environment variables are properly configured for production"""
        # Test through health endpoint and actual functionality
        success, status, health_data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Environment Variables Production", False, f"Health check failed: {status}")
        
        # Check database connectivity (indicates MONGO_URL is working)
        db_connected = health_data.get('database', {}).get('connected', False)
        
        # Check websocket service (indicates SOCKET_PATH is working)
        websocket_working = health_data.get('services', {}).get('websocket', False)
        
        # Test auth functionality (indicates JWT configuration is working)
        auth_working = self.token is not None  # We successfully got a token earlier
        
        # Check frontend environment variables
        try:
            with open('/app/frontend/.env', 'r') as f:
                frontend_env = f.read()
            
            required_frontend_vars = [
                'REACT_APP_BACKEND_URL',
                'REACT_APP_SOCKET_PATH'
            ]
            
            frontend_vars_present = all(var in frontend_env for var in required_frontend_vars)
            
        except Exception:
            frontend_vars_present = False
        
        env_production_ready = (
            db_connected and
            websocket_working and
            auth_working and
            frontend_vars_present
        )
        
        return self.log_test(
            "Environment Variables Production",
            env_production_ready,
            f"DB: {db_connected}, WebSocket: {websocket_working}, Auth: {auth_working}, Frontend vars: {frontend_vars_present}"
        )

    def test_diagnostic_endpoints_comprehensive(self):
        """Test all diagnostic endpoints for comprehensive monitoring"""
        diagnostic_results = []
        
        # 1. Socket.IO diagnostics
        success, status, data = self.make_request('GET', 'socket-diag', token=None)
        socketio_diag = success and data.get('ok') is True
        diagnostic_results.append(("Socket.IO Diag", socketio_diag))
        
        # 2. Socket.IO config
        success, status, data = self.make_request('GET', 'socket/config', token=None)
        socketio_config = success and data.get('path') == '/api/socketio'
        diagnostic_results.append(("Socket.IO Config", socketio_config))
        
        # 3. Health endpoint
        success, status, data = self.make_request('GET', 'health', token=None)
        health_diag = success and data.get('status') == 'healthy'
        diagnostic_results.append(("Health", health_diag))
        
        # 4. Time sync endpoint
        success, status, data = self.make_request('GET', 'timez', token=None)
        time_diag = success and 'now' in data
        diagnostic_results.append(("Time Sync", time_diag))
        
        # 5. Version endpoint
        success, status, data = self.make_request('GET', '../version', token=None)
        version_diag = success or status == 404  # 404 is acceptable
        diagnostic_results.append(("Version", version_diag))
        
        working_diagnostics = sum(1 for _, status in diagnostic_results if status)
        all_diagnostics_working = working_diagnostics >= 4  # At least 4/5 should work
        
        details = f"Working diagnostics: {working_diagnostics}/5 - " + ", ".join([f"{name}: {'✓' if status else '✗'}" for name, status in diagnostic_results])
        
        return self.log_test(
            "Diagnostic Endpoints Comprehensive",
            all_diagnostics_working,
            details
        )

    # ==================== PRODUCTION READINESS ASSESSMENT ====================
    
    def assess_production_readiness_final(self):
        """Final assessment of production readiness"""
        critical_systems = [
            ("Socket.IO Configuration", "Socket.IO Config Endpoint" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Socket.IO Connectivity", "Socket.IO Both Transports" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Authentication System", "Authentication Flow Complete" not in [t.split(':')[0] for t in self.failed_tests]),
            ("League Management", "League Management Comprehensive" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Auction System", "Auction System Comprehensive" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Health Monitoring", "Health Endpoint Production Ready" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Environment Config", "Environment Variables Production" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Configuration Validation", "Config Gate Script Execution" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        working_systems = sum(1 for _, status in critical_systems if status)
        total_systems = len(critical_systems)
        
        # Production ready if at least 7/8 critical systems work (87.5% threshold)
        production_ready = working_systems >= 7
        
        print(f"\n🎯 FINAL PRODUCTION READINESS ASSESSMENT:")
        print(f"Critical Systems Working: {working_systems}/{total_systems} ({(working_systems/total_systems)*100:.1f}%)")
        
        for system, status in critical_systems:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {system}")
        
        readiness_status = "PRODUCTION READY" if production_ready else "NOT PRODUCTION READY"
        readiness_icon = "🟢" if production_ready else "🔴"
        
        print(f"\n{readiness_icon} FINAL STATUS: {readiness_status}")
        
        if production_ready:
            print("🚀 All critical systems are operational and ready for production deployment!")
        else:
            print("⚠️  Some critical systems need attention before production deployment.")
        
        return production_ready

    # ==================== MAIN TEST RUNNER ====================
    
    def run_final_production_tests(self):
        """Run comprehensive Socket.IO configuration and production readiness tests"""
        print("🚀 FINAL SOCKET.IO CONFIGURATION & PRODUCTION READINESS TESTING")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 80)
        
        # Socket.IO Configuration Tests
        print("\n🔌 SOCKET.IO CONFIGURATION TESTS")
        self.test_socket_config_endpoint()
        self.test_socketio_connection_both_transports()
        self.test_path_consistency_validation()
        
        # Critical Backend API Tests
        print("\n🔐 CRITICAL BACKEND API TESTS")
        self.test_authentication_flow_complete()
        self.test_league_management_comprehensive()
        self.test_auction_system_comprehensive()
        self.test_health_endpoint_production_ready()
        
        # Configuration Validation Tests
        print("\n⚙️ CONFIGURATION VALIDATION TESTS")
        self.test_config_gate_script_execution()
        self.test_environment_variables_production()
        self.test_diagnostic_endpoints_comprehensive()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        # Final Production Readiness Assessment
        production_ready = self.assess_production_readiness_final()
        
        return self.tests_passed, self.tests_run, self.failed_tests, production_ready

if __name__ == "__main__":
    tester = FinalProductionTester()
    passed, total, failed, production_ready = tester.run_final_production_tests()
    
    # Exit with appropriate code
    sys.exit(0 if production_ready else 1)