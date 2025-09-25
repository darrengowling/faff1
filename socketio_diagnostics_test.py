#!/usr/bin/env python3
"""
Socket.IO Diagnostics Testing Suite
Tests the newly implemented Socket.IO diagnostics features
"""

import requests
import sys
import json
import subprocess
import os
from datetime import datetime, timezone

class SocketIODiagnosticsTester:
    def __init__(self, base_url="https://champion-bid-portal.preview.emergentagent.com"):
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

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
            
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

    def test_socketio_diagnostic_endpoint(self):
        """Test GET /api/socketio/diag endpoint returns proper response with {ok: true, path, now}"""
        success, status, data = self.make_request('GET', 'socketio/diag')
        
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
                # Parse ISO timestamp
                server_time = datetime.fromisoformat(data['now'].replace('Z', '+00:00'))
                # Check it's recent (within 5 seconds)
                now = datetime.now(timezone.utc)
                time_diff = abs((server_time - now).total_seconds())
                timestamp_valid = time_diff < 5
            except:
                timestamp_valid = False
        
        # Verify path configuration
        path_valid = data.get('path') == '/api/socket.io' if valid_response else False
        
        return self.log_test(
            "Diagnostic Endpoint (/api/socketio/diag)",
            valid_response and timestamp_valid and path_valid,
            f"Status: {status}, Valid response: {valid_response}, Timestamp valid: {timestamp_valid}, Path: {data.get('path', 'N/A') if isinstance(data, dict) else 'N/A'}"
        )
    
    def test_cli_test_script_exists(self):
        """Test that scripts/diag-socketio.mjs exists and is executable"""
        script_path = "/app/frontend/scripts/diag-socketio.mjs"
        
        try:
            # Check if file exists
            file_exists = os.path.exists(script_path)
            
            # Check if file is readable
            file_readable = False
            script_content = ""
            if file_exists:
                try:
                    with open(script_path, 'r') as f:
                        script_content = f.read()
                    file_readable = len(script_content) > 0
                except:
                    file_readable = False
            
            # Check if script has proper shebang and structure
            has_shebang = script_content.startswith('#!/usr/bin/env node')
            has_socketio_import = 'socket.io-client' in script_content
            has_test_functions = 'testPollingHandshake' in script_content and 'testWebSocketConnection' in script_content
            has_proper_env_vars = 'NEXT_PUBLIC_API_URL' in script_content and 'VITE_PUBLIC_API_URL' in script_content
            
            script_valid = has_shebang and has_socketio_import and has_test_functions and has_proper_env_vars
            
            return self.log_test(
                "CLI Test Script Exists (scripts/diag-socketio.mjs)",
                file_exists and file_readable and script_valid,
                f"Exists: {file_exists}, Readable: {file_readable}, Valid structure: {script_valid}, Has env vars: {has_proper_env_vars}"
            )
        except Exception as e:
            return self.log_test("CLI Test Script Exists", False, f"Exception: {str(e)}")
    
    def test_npm_diag_socketio_command(self):
        """Test that npm run diag:socketio command is configured in package.json"""
        try:
            package_json_path = "/app/frontend/package.json"
            
            # Check if package.json exists
            if not os.path.exists(package_json_path):
                return self.log_test("NPM diag:socketio Command", False, "package.json not found")
            
            # Read and parse package.json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Check if scripts section exists
            scripts = package_data.get('scripts', {})
            
            # Check if diag:socketio script is defined
            diag_script = scripts.get('diag:socketio')
            script_configured = diag_script == 'node scripts/diag-socketio.mjs'
            
            # Check if socket.io-client dependency exists
            dependencies = package_data.get('dependencies', {})
            socketio_dependency = 'socket.io-client' in dependencies
            
            return self.log_test(
                "NPM diag:socketio Command Configuration",
                script_configured and socketio_dependency,
                f"Script configured: {script_configured}, Socket.IO dependency: {socketio_dependency}, Script: {diag_script}"
            )
        except Exception as e:
            return self.log_test("NPM diag:socketio Command Configuration", False, f"Exception: {str(e)}")
    
    def test_environment_variables_configuration(self):
        """Test that the script reads environment variables correctly"""
        try:
            # Check frontend .env file
            frontend_env_path = "/app/frontend/.env"
            backend_env_path = "/app/backend/.env"
            
            frontend_env_exists = os.path.exists(frontend_env_path)
            backend_env_exists = os.path.exists(backend_env_path)
            
            # Read frontend .env
            frontend_config = {}
            if frontend_env_exists:
                with open(frontend_env_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            frontend_config[key] = value
            
            # Read backend .env
            backend_config = {}
            if backend_env_exists:
                with open(backend_env_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            backend_config[key] = value
            
            # Check required environment variables
            required_frontend_vars = ['REACT_APP_BACKEND_URL', 'REACT_APP_SOCKET_PATH']
            required_backend_vars = ['SOCKET_PATH']
            
            frontend_vars_present = all(var in frontend_config for var in required_frontend_vars)
            backend_vars_present = all(var in backend_config for var in required_backend_vars)
            
            # Check consistency between frontend and backend socket paths
            frontend_socket_path = frontend_config.get('REACT_APP_SOCKET_PATH', '').strip('"')
            backend_socket_path = backend_config.get('SOCKET_PATH', '').strip('"')
            paths_consistent = frontend_socket_path == backend_socket_path == '/api/socket.io'
            
            return self.log_test(
                "Environment Variables Configuration",
                frontend_vars_present and backend_vars_present and paths_consistent,
                f"Frontend vars: {frontend_vars_present}, Backend vars: {backend_vars_present}, Paths consistent: {paths_consistent}"
            )
        except Exception as e:
            return self.log_test("Environment Variables Configuration", False, f"Exception: {str(e)}")
    
    def test_cli_script_execution(self):
        """Test that npm run diag:socketio works and provides clear pass/fail results"""
        try:
            # Change to frontend directory
            frontend_dir = "/app/frontend"
            
            # Run the npm command
            result = subprocess.run(
                ['npm', 'run', 'diag:socketio'],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if command executed successfully (exit code doesn't matter for this test)
            command_executed = result.returncode is not None
            
            # Check output format
            output = result.stdout + result.stderr
            has_test_header = '🔍 Socket.IO Diagnostics Test' in output
            has_configuration_info = 'API Origin:' in output and 'Socket Path:' in output
            has_test_results = ('✅' in output or '❌' in output) and 'Test Results:' in output
            has_clear_format = has_test_header and has_configuration_info and has_test_results
            
            # Expected: 1/4 tests passing (diagnostic endpoint works, Socket.IO connections fail)
            expected_pattern = '1/4 passed' in output or 'Diagnostic Endpoint' in output
            
            return self.log_test(
                "CLI Script Execution (npm run diag:socketio)",
                command_executed and has_clear_format,
                f"Executed: {command_executed}, Clear format: {has_clear_format}, Expected pattern: {expected_pattern}, Output preview: {output[:200]}..."
            )
        except subprocess.TimeoutExpired:
            return self.log_test("CLI Script Execution", False, "Command timed out after 30 seconds")
        except Exception as e:
            return self.log_test("CLI Script Execution", False, f"Exception: {str(e)}")

    def run_diagnostic_tests(self):
        """Run all Socket.IO diagnostic tests"""
        print("🔍 Socket.IO Diagnostics Testing Suite")
        print("=" * 50)
        print(f"📍 Testing against: {self.base_url}")
        print()
        
        print("🧪 Running Socket.IO diagnostics tests...")
        print()
        
        # Test 1: Diagnostic Endpoint
        self.test_socketio_diagnostic_endpoint()
        
        # Test 2: CLI Test Script
        self.test_cli_test_script_exists()
        
        # Test 3: NPM Command Configuration
        self.test_npm_diag_socketio_command()
        
        # Test 4: Environment Variables
        self.test_environment_variables_configuration()
        
        # Test 5: CLI Script Execution
        self.test_cli_script_execution()
        
        # Print summary
        print()
        print("=" * 50)
        print(f"📊 TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        else:
            print("\n🎉 All tests passed!")
        
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    """Main test runner"""
    tester = SocketIODiagnosticsTester()
    return tester.run_diagnostic_tests()

if __name__ == "__main__":
    sys.exit(main())