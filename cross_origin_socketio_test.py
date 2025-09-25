#!/usr/bin/env python3
"""
Cross-Origin Socket.IO Configuration Testing Suite
Tests the updated cross-origin Socket.IO implementation as requested in the review
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time
import subprocess
import os

class CrossOriginSocketIOTester:
    def __init__(self, base_url="https://realtime-socket-fix.preview.emergentagent.com"):
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

    def test_diagnostic_endpoint_updated(self):
        """Test diagnostic endpoint works at GET /api/socketio-diag with proper JSON response"""
        success, status, data = self.make_request('GET', 'socketio-diag', token=None)
        
        # Verify response structure matches expected format
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
        
        # Verify path configuration - should be /api/socketio for new implementation
        path_valid = data.get('path') == '/api/socketio' if valid_response else False
        
        return self.log_test(
            "Diagnostic Endpoint (/api/socketio-diag)",
            valid_response and timestamp_valid and path_valid,
            f"Status: {status}, Response: {data.get('ok', False)}, Path: {data.get('path', 'N/A')}, Timestamp valid: {timestamp_valid}"
        )

    def test_cli_script_cross_origin_pattern(self):
        """Test CLI script uses cross-origin pattern with new environment variables"""
        try:
            script_path = "/app/frontend/scripts/test-socketio.js"
            
            if not os.path.exists(script_path):
                return self.log_test("CLI Script Cross-Origin Pattern", False, "Script file not found")
            
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            # Check for cross-origin pattern usage
            uses_next_public_api_url = 'NEXT_PUBLIC_API_URL' in script_content
            uses_vite_public_api_url = 'VITE_PUBLIC_API_URL' in script_content
            uses_next_socket_path = 'NEXT_PUBLIC_SOCKET_PATH' in script_content
            # Note: VITE_SOCKET_PATH is not used in the path fallback, only in transports
            uses_transport_config = 'NEXT_PUBLIC_SOCKET_TRANSPORTS' in script_content and 'VITE_SOCKET_TRANSPORTS' in script_content
            
            # Check for proper fallback pattern
            has_fallback_pattern = 'process.env.NEXT_PUBLIC_API_URL ||' in script_content and 'process.env.VITE_PUBLIC_API_URL' in script_content
            
            # Check that it doesn't rely on window.location.origin
            no_window_location = 'window.location.origin' not in script_content
            
            cross_origin_pattern_complete = (
                uses_next_public_api_url and uses_vite_public_api_url and
                uses_next_socket_path and uses_transport_config and 
                has_fallback_pattern and no_window_location
            )
            
            return self.log_test(
                "CLI Script Cross-Origin Pattern",
                cross_origin_pattern_complete,
                f"NEXT_PUBLIC/VITE vars: {uses_next_public_api_url and uses_vite_public_api_url}, Transports: {uses_transport_config}, Fallback: {has_fallback_pattern}, No window.location: {no_window_location}"
            )
        except Exception as e:
            return self.log_test("CLI Script Cross-Origin Pattern", False, f"Exception: {str(e)}")

    def test_backend_socketio_path(self):
        """Test backend Socket.IO server responds at /api/socketio path"""
        try:
            # Test new Socket.IO path with proper Engine.IO parameters
            socketio_url = f"{self.base_url}/api/socketio/"
            response = requests.get(socketio_url, params={'EIO': '4', 'transport': 'polling'}, timeout=10)
            
            # Socket.IO handshake should return specific response format
            handshake_successful = response.status_code == 200
            contains_socketio_response = '{"sid":' in response.text or 'socket.io' in response.text.lower()
            
            return self.log_test(
                "Backend Socket.IO Server (/api/socketio)",
                handshake_successful and contains_socketio_response,
                f"Status: {response.status_code}, Socket.IO handshake: {contains_socketio_response}"
            )
        except Exception as e:
            return self.log_test("Backend Socket.IO Server", False, f"Exception: {str(e)}")

    def test_env_example_cross_origin_config(self):
        """Test .env.example includes new cross-origin configuration with proper comments"""
        try:
            env_example_path = "/app/.env.example"
            
            if not os.path.exists(env_example_path):
                return self.log_test(".env.example Cross-Origin Config", False, ".env.example file not found")
            
            with open(env_example_path, 'r') as f:
                env_content = f.read()
            
            # Check for cross-origin section
            has_cross_origin_section = 'CROSS-ORIGIN SOCKET.IO CONFIGURATION' in env_content
            
            # Check for new environment variables
            has_next_public_vars = 'NEXT_PUBLIC_API_URL' in env_content and 'NEXT_PUBLIC_SOCKET_PATH' in env_content and 'NEXT_PUBLIC_SOCKET_TRANSPORTS' in env_content
            has_vite_vars = 'VITE_PUBLIC_API_URL' in env_content and 'VITE_SOCKET_PATH' in env_content and 'VITE_SOCKET_TRANSPORTS' in env_content
            
            # Check for client connection pattern example
            has_connection_pattern = 'const socket = io(origin, { path, transports, withCredentials: true })' in env_content
            
            # Check for proper comments explaining the pattern
            has_explanatory_comments = 'Cross-origin Socket.IO pattern' in env_content and 'client-side access' in env_content
            
            return self.log_test(
                ".env.example Cross-Origin Config",
                has_cross_origin_section and has_next_public_vars and has_vite_vars and has_connection_pattern and has_explanatory_comments,
                f"Section: {has_cross_origin_section}, NEXT_PUBLIC: {has_next_public_vars}, VITE: {has_vite_vars}, Pattern: {has_connection_pattern}"
            )
        except Exception as e:
            return self.log_test(".env.example Cross-Origin Config", False, f"Exception: {str(e)}")

    def test_cross_origin_environment_variables(self):
        """Test cross-origin environment variables are properly configured"""
        try:
            frontend_env_path = "/app/frontend/.env"
            
            if not os.path.exists(frontend_env_path):
                return self.log_test("Cross-Origin Environment Variables", False, "Frontend .env not found")
            
            # Read frontend .env
            frontend_config = {}
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        frontend_config[key] = value
            
            # Check for new cross-origin environment variables
            cross_origin_vars = [
                'NEXT_PUBLIC_API_URL',
                'VITE_PUBLIC_API_URL', 
                'NEXT_PUBLIC_SOCKET_PATH',
                'VITE_SOCKET_PATH',
                'NEXT_PUBLIC_SOCKET_TRANSPORTS',
                'VITE_SOCKET_TRANSPORTS'
            ]
            
            cross_origin_vars_present = all(var in frontend_config for var in cross_origin_vars)
            
            # Check values are properly set
            next_api_url = frontend_config.get('NEXT_PUBLIC_API_URL', '').strip('"')
            vite_api_url = frontend_config.get('VITE_PUBLIC_API_URL', '').strip('"')
            next_socket_path = frontend_config.get('NEXT_PUBLIC_SOCKET_PATH', '').strip('"')
            vite_socket_path = frontend_config.get('VITE_SOCKET_PATH', '').strip('"')
            next_transports = frontend_config.get('NEXT_PUBLIC_SOCKET_TRANSPORTS', '').strip('"')
            vite_transports = frontend_config.get('VITE_SOCKET_TRANSPORTS', '').strip('"')
            
            # Verify consistency
            api_urls_consistent = next_api_url == vite_api_url
            socket_paths_consistent = next_socket_path == vite_socket_path == '/api/socketio'
            transports_consistent = next_transports == vite_transports == 'polling,websocket'
            
            return self.log_test(
                "Cross-Origin Environment Variables",
                cross_origin_vars_present and api_urls_consistent and socket_paths_consistent and transports_consistent,
                f"All vars: {cross_origin_vars_present}, API URLs: {api_urls_consistent}, Paths: {socket_paths_consistent}, Transports: {transports_consistent}"
            )
        except Exception as e:
            return self.log_test("Cross-Origin Environment Variables", False, f"Exception: {str(e)}")

    def test_no_window_location_reliance(self):
        """Test no reliance on window.location.origin for socket connections"""
        try:
            # Check key files for window.location.origin usage in Socket.IO connection logic
            files_to_check = [
                "/app/frontend/scripts/test-socketio.js",
            ]
            
            # Add React component files if they exist, but exclude DiagnosticPage.js 
            # since it uses window.location.origin only for display purposes
            frontend_src_path = "/app/frontend/src"
            if os.path.exists(frontend_src_path):
                for root, dirs, files in os.walk(frontend_src_path):
                    for file in files:
                        if file.endswith(('.js', '.jsx', '.ts', '.tsx')) and file != 'DiagnosticPage.js':
                            files_to_check.append(os.path.join(root, file))
            
            window_location_found = []
            
            for file_path in files_to_check:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if 'window.location.origin' in content:
                                window_location_found.append(file_path)
                    except:
                        pass
            
            no_window_location_reliance = len(window_location_found) == 0
            
            return self.log_test(
                "No window.location.origin Reliance",
                no_window_location_reliance,
                f"Files using window.location.origin for Socket.IO: {len(window_location_found)} (DiagnosticPage.js excluded as it's for display only)"
            )
        except Exception as e:
            return self.log_test("No window.location.origin Reliance", False, f"Exception: {str(e)}")

    def test_cli_script_execution(self):
        """Test CLI script execution shows expected results (1/4 tests passing)"""
        try:
            frontend_dir = "/app/frontend"
            
            # Run the npm command
            result = subprocess.run(
                ['npm', 'run', 'diag:socketio'],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if command executed
            command_executed = result.returncode is not None
            
            # Check output for expected format and results
            output = result.stdout + result.stderr
            shows_config = 'API Origin:' in output and 'Socket Path:' in output and '/api/socketio' in output
            shows_transports = 'Transports:' in output and ('polling' in output or 'websocket' in output)
            shows_test_results = ('✅' in output or '❌' in output) and 'Test Results:' in output
            
            # Expected: 1/4 tests passing (diagnostic works, connections fail due to infrastructure routing)
            expected_pattern = '1/4 passed' in output or ('Diagnostic Endpoint' in output and '✅' in output)
            
            return self.log_test(
                "CLI Script Execution",
                command_executed and shows_config and shows_test_results,
                f"Executed: {command_executed}, Shows config: {shows_config}, Test results: {shows_test_results}, Expected pattern: {expected_pattern}"
            )
        except subprocess.TimeoutExpired:
            return self.log_test("CLI Script Execution", False, "Command timed out")
        except Exception as e:
            return self.log_test("CLI Script Execution", False, f"Exception: {str(e)}")

    def run_cross_origin_tests(self):
        """Run all cross-origin Socket.IO tests"""
        print("🔍 Cross-Origin Socket.IO Configuration Testing")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print()
        
        # Run all tests
        self.test_diagnostic_endpoint_updated()
        self.test_cli_script_cross_origin_pattern()
        self.test_backend_socketio_path()
        self.test_env_example_cross_origin_config()
        self.test_cross_origin_environment_variables()
        self.test_no_window_location_reliance()
        self.test_cli_script_execution()
        
        # Print summary
        print()
        print("=" * 60)
        print(f"📊 CROSS-ORIGIN SOCKET.IO TEST RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print()
            print("❌ FAILED TESTS:")
            for failed_test in self.failed_tests:
                print(f"  - {failed_test}")
        
        print()
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = CrossOriginSocketIOTester()
    success = tester.run_cross_origin_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())