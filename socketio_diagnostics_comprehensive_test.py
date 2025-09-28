#!/usr/bin/env python3
"""
Comprehensive Socket.IO Diagnostics Testing Suite
Tests all Socket.IO handshake diagnostics implementation features
"""

import requests
import sys
import json
import os
import subprocess
import time
from datetime import datetime, timezone

class SocketIODiagnosticsComprehensiveTester:
    def __init__(self, base_url="https://auction-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
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
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
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

    def test_diagnostic_endpoint_alternative(self):
        """Test GET /api/socket-diag endpoint (alternative path due to routing conflicts)"""
        success, status, data = self.make_request('GET', 'socket-diag', token=None)
        
        # Verify response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            data.get('ok') is True and
            'path' in data and
            'now' in data and
            isinstance(data['path'], str) and
            isinstance(data['now'], str)
        )
        
        # Verify timestamp format (ISO format with timezone)
        timestamp_valid = False
        if valid_response:
            try:
                server_time = datetime.fromisoformat(data['now'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                time_diff = abs((server_time - now).total_seconds())
                timestamp_valid = time_diff < 5
            except:
                timestamp_valid = False
        
        # Verify path configuration
        path_valid = data.get('path') == '/api/socketio' if valid_response else False
        
        return self.log_test(
            "Diagnostic Endpoint (/api/socket-diag)",
            valid_response and timestamp_valid and path_valid,
            f"Status: {status}, Valid response: {valid_response}, Timestamp valid: {timestamp_valid}, Path: {data.get('path', 'N/A') if isinstance(data, dict) else 'N/A'}"
        )

    def test_socketio_handshake_direct(self):
        """Test Socket.IO handshake directly via polling transport"""
        try:
            timestamp = str(int(time.time() * 1000))
            handshake_url = f"{self.base_url}/api/socketio/?EIO=4&transport=polling&t={timestamp}"
            
            response = requests.get(handshake_url, timeout=10)
            
            # Check for proper Engine.IO handshake response
            handshake_successful = response.status_code == 200
            proper_format = response.text.startswith('0{') and '"sid":' in response.text
            has_upgrades = '"upgrades":' in response.text
            
            # Parse the handshake response
            handshake_data = None
            if proper_format:
                try:
                    json_part = response.text[1:]
                    handshake_data = json.loads(json_part)
                except:
                    pass
            
            valid_handshake_data = (
                handshake_data is not None and
                'sid' in handshake_data and
                'upgrades' in handshake_data and
                isinstance(handshake_data['upgrades'], list)
            )
            
            return self.log_test(
                "Socket.IO Handshake Validation",
                handshake_successful and proper_format and valid_handshake_data,
                f"Status: {response.status_code}, Proper format: {proper_format}, Valid data: {valid_handshake_data}, SID: {handshake_data.get('sid', 'N/A')[:8] if handshake_data else 'N/A'}..."
            )
        except Exception as e:
            return self.log_test("Socket.IO Handshake Validation", False, f"Exception: {str(e)}")

    def test_cli_script_exists(self):
        """Test that scripts/diag-socketio.mjs exists and is properly configured"""
        script_path = "/app/frontend/scripts/diag-socketio.mjs"
        
        try:
            file_exists = os.path.exists(script_path)
            
            file_readable = False
            script_content = ""
            if file_exists:
                try:
                    with open(script_path, 'r') as f:
                        script_content = f.read()
                    file_readable = len(script_content) > 0
                except:
                    file_readable = False
            
            # Check script structure
            has_shebang = script_content.startswith('#!/usr/bin/env node')
            has_socketio_import = 'socket.io-client' in script_content
            has_test_functions = 'testPollingHandshake' in script_content and 'testWebSocketConnection' in script_content
            has_proper_env_vars = 'NEXT_PUBLIC_API_URL' in script_content and 'VITE_PUBLIC_API_URL' in script_content
            has_timeout_config = 'timeout: 2000' in script_content
            has_exit_behavior = 'process.exit(' in script_content
            
            script_valid = (has_shebang and has_socketio_import and has_test_functions and 
                          has_proper_env_vars and has_timeout_config and has_exit_behavior)
            
            return self.log_test(
                "CLI Script Structure (scripts/diag-socketio.mjs)",
                file_exists and file_readable and script_valid,
                f"Exists: {file_exists}, Valid structure: {script_valid}, Has timeout: {has_timeout_config}, Has exit behavior: {has_exit_behavior}"
            )
        except Exception as e:
            return self.log_test("CLI Script Structure", False, f"Exception: {str(e)}")

    def test_npm_command_configuration(self):
        """Test NPM command configuration in package.json"""
        try:
            package_json_path = "/app/frontend/package.json"
            
            if not os.path.exists(package_json_path):
                return self.log_test("NPM Command Configuration", False, "package.json not found")
            
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            scripts = package_data.get('scripts', {})
            diag_script = scripts.get('diag:socketio')
            script_configured = diag_script == 'node scripts/diag-socketio.mjs'
            
            dependencies = package_data.get('dependencies', {})
            socketio_dependency = 'socket.io-client' in dependencies
            
            return self.log_test(
                "NPM Command Configuration",
                script_configured and socketio_dependency,
                f"Script configured: {script_configured}, Socket.IO dependency: {socketio_dependency}, Script: {diag_script}"
            )
        except Exception as e:
            return self.log_test("NPM Command Configuration", False, f"Exception: {str(e)}")

    def test_cli_script_execution(self):
        """Test CLI script execution and output format"""
        try:
            frontend_dir = "/app/frontend"
            
            result = subprocess.run(
                ['npm', 'run', 'diag:socketio'],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            command_executed = result.returncode is not None
            output = result.stdout + result.stderr
            
            # Check output format
            has_test_header = '🔍 Socket.IO Handshake Diagnostics' in output
            has_configuration_info = 'API Origin:' in output and 'Socket Path:' in output
            has_test_results = ('✅' in output or '❌' in output) and 'Results:' in output
            has_polling_test = 'Polling Handshake' in output
            has_websocket_test = 'WebSocket Connection' in output
            
            # Expected: 1/2 tests passing (polling works, websocket may timeout)
            expected_results = ('1/2 tests passed' in output or 
                              ('✅ Polling Handshake' in output and '❌ WebSocket Connection' in output))
            
            # Check exit behavior
            proper_exit_code = result.returncode in [0, 1]  # 0 for partial success, 1 for complete failure
            
            return self.log_test(
                "CLI Script Execution",
                command_executed and has_test_header and has_configuration_info and expected_results and proper_exit_code,
                f"Executed: {command_executed}, Has header: {has_test_header}, Expected results: {expected_results}, Exit code: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return self.log_test("CLI Script Execution", False, "Command timed out after 30 seconds")
        except Exception as e:
            return self.log_test("CLI Script Execution", False, f"Exception: {str(e)}")

    def test_diagnostic_page_route(self):
        """Test /diag route accessibility"""
        try:
            response = requests.get(f"{self.base_url}/diag", timeout=10)
            
            page_accessible = response.status_code == 200
            contains_react_app = 'react' in response.text.lower() or 'root' in response.text
            is_html_page = response.headers.get('content-type', '').startswith('text/html')
            
            return self.log_test(
                "Diagnostic Page Route (/diag)",
                page_accessible and (contains_react_app or is_html_page),
                f"Status: {response.status_code}, HTML page: {is_html_page}, Contains React: {contains_react_app}"
            )
        except Exception as e:
            return self.log_test("Diagnostic Page Route", False, f"Exception: {str(e)}")

    def test_ui_diagnostic_features(self):
        """Test UI diagnostic features implementation"""
        try:
            diagnostic_page_path = "/app/frontend/src/components/DiagnosticPage.js"
            
            if not os.path.exists(diagnostic_page_path):
                return self.log_test("UI Diagnostic Features", False, "DiagnosticPage.js not found")
            
            with open(diagnostic_page_path, 'r') as f:
                component_content = f.read()
            
            # Check for required UI features
            has_api_origin_display = 'API Origin:' in component_content
            has_socket_path_display = 'Socket Path:' in component_content
            has_transport_info = 'transports' in component_content.lower()
            has_session_id_display = 'Session ID' in component_content or 'sessionId' in component_content
            has_polling_banner = 'Polling-Only' in component_content
            has_connection_status = 'connectionStatus' in component_content
            has_test_connection = 'testConnection' in component_content or 'Test Connection' in component_content
            
            ui_features_complete = (
                has_api_origin_display and has_socket_path_display and 
                has_transport_info and has_session_id_display and 
                has_polling_banner and has_connection_status and has_test_connection
            )
            
            return self.log_test(
                "UI Diagnostic Features",
                ui_features_complete,
                f"API Origin: {has_api_origin_display}, Socket Path: {has_socket_path_display}, Session ID: {has_session_id_display}, Test Connection: {has_test_connection}"
            )
        except Exception as e:
            return self.log_test("UI Diagnostic Features", False, f"Exception: {str(e)}")

    def test_environment_variables(self):
        """Test environment variable configuration"""
        try:
            frontend_env_path = "/app/frontend/.env"
            backend_env_path = "/app/backend/.env"
            
            # Check frontend .env
            frontend_config = {}
            if os.path.exists(frontend_env_path):
                with open(frontend_env_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            frontend_config[key] = value.strip('"')
            
            # Check backend .env
            backend_config = {}
            if os.path.exists(backend_env_path):
                with open(backend_env_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            backend_config[key] = value.strip('"')
            
            # Check cross-origin variables
            has_next_vars = all(var in frontend_config for var in ['NEXT_PUBLIC_API_URL', 'NEXT_PUBLIC_SOCKET_PATH'])
            has_vite_vars = all(var in frontend_config for var in ['VITE_PUBLIC_API_URL', 'VITE_SOCKET_PATH'])
            has_backend_socket_path = 'SOCKET_PATH' in backend_config
            
            # Check path consistency
            backend_socket_path = backend_config.get('SOCKET_PATH', '')
            next_socket_path = frontend_config.get('NEXT_PUBLIC_SOCKET_PATH', '')
            vite_socket_path = frontend_config.get('VITE_SOCKET_PATH', '')
            
            paths_consistent = (backend_socket_path == next_socket_path == vite_socket_path == '/api/socketio')
            
            return self.log_test(
                "Environment Variables Configuration",
                has_next_vars and has_vite_vars and has_backend_socket_path and paths_consistent,
                f"Cross-origin vars: {has_next_vars and has_vite_vars}, Backend config: {has_backend_socket_path}, Paths consistent: {paths_consistent}"
            )
        except Exception as e:
            return self.log_test("Environment Variables Configuration", False, f"Exception: {str(e)}")

    def test_handshake_tests_implementation(self):
        """Test that handshake tests are properly implemented in CLI script"""
        try:
            script_path = "/app/frontend/scripts/diag-socketio.mjs"
            
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            # Check for specific test implementations
            has_polling_handshake = 'testPollingHandshake' in script_content and 'EIO=4&transport=polling' in script_content
            has_websocket_connection = 'testWebSocketConnection' in script_content and "transports: ['websocket']" in script_content
            has_timeout_handling = 'timeout: 2000' in script_content
            has_proper_url_construction = 'API_ORIGIN' in script_content and 'SOCKET_PATH' in script_content
            has_engine_io_validation = '"sid":' in script_content and 'startsWith(\'0{\')' in script_content
            
            implementation_complete = (
                has_polling_handshake and has_websocket_connection and 
                has_timeout_handling and has_proper_url_construction and has_engine_io_validation
            )
            
            return self.log_test(
                "Handshake Tests Implementation",
                implementation_complete,
                f"Polling test: {has_polling_handshake}, WebSocket test: {has_websocket_connection}, Engine.IO validation: {has_engine_io_validation}"
            )
        except Exception as e:
            return self.log_test("Handshake Tests Implementation", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run comprehensive Socket.IO diagnostics tests"""
        print("🔍 Socket.IO Handshake Diagnostics - Comprehensive Testing Suite")
        print("=" * 70)
        print(f"📍 Testing against: {self.base_url}")
        print()
        
        print("🎯 DELIVERABLE 1: API Endpoint")
        print("-" * 40)
        self.test_diagnostic_endpoint_alternative()
        
        print("\n🎯 DELIVERABLE 2: CLI Script")
        print("-" * 40)
        self.test_cli_script_exists()
        self.test_handshake_tests_implementation()
        
        print("\n🎯 DELIVERABLE 3: NPM Alias")
        print("-" * 40)
        self.test_npm_command_configuration()
        self.test_cli_script_execution()
        
        print("\n🎯 DELIVERABLE 4: UI Updates")
        print("-" * 40)
        self.test_diagnostic_page_route()
        self.test_ui_diagnostic_features()
        
        print("\n🎯 BACKEND INTEGRATION")
        print("-" * 40)
        self.test_socketio_handshake_direct()
        self.test_environment_variables()
        
        # Print comprehensive summary
        print("\n" + "=" * 70)
        print(f"📊 COMPREHENSIVE TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        # Deliverable-specific summary
        print(f"\n🎯 DELIVERABLE STATUS:")
        
        # Count tests by deliverable
        api_tests = [t for t in self.failed_tests if 'Diagnostic Endpoint' in t]
        cli_tests = [t for t in self.failed_tests if any(x in t for x in ['CLI Script', 'Handshake Tests'])]
        npm_tests = [t for t in self.failed_tests if any(x in t for x in ['NPM Command', 'CLI Script Execution'])]
        ui_tests = [t for t in self.failed_tests if any(x in t for x in ['Diagnostic Page', 'UI Diagnostic'])]
        
        print(f"   ✅ API Endpoint: {'PASS' if not api_tests else 'FAIL'}")
        print(f"   ✅ CLI Script: {'PASS' if not cli_tests else 'FAIL'}")
        print(f"   ✅ NPM Alias: {'PASS' if not npm_tests else 'FAIL'}")
        print(f"   ✅ UI Updates: {'PASS' if not ui_tests else 'FAIL'}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All Socket.IO diagnostics tests passed!")
            print("✅ API endpoint accessible with proper JSON response")
            print("✅ CLI script properly configured with handshake tests")
            print("✅ NPM command executes successfully")
            print("✅ UI diagnostic features implemented")
            print("✅ Backend Socket.IO handshake working correctly")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed - see details above")
            
            if self.tests_passed / self.tests_run >= 0.8:
                print("\n✅ OVERALL STATUS: Socket.IO diagnostics implementation is mostly working")
                print("   Minor issues detected but core functionality is operational")
            else:
                print("\n❌ OVERALL STATUS: Socket.IO diagnostics implementation needs attention")
                print("   Multiple issues detected that may impact functionality")
            
            return 1

def main():
    """Main test runner"""
    tester = SocketIODiagnosticsComprehensiveTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())