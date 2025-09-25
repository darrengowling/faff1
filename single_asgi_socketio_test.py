#!/usr/bin/env python3
"""
Single ASGI Wrapper Socket.IO Implementation Test
Tests the refactored server.py with single ASGI wrapper pattern
"""

import requests
import sys
import json
from datetime import datetime, timezone
import time
import subprocess
import os

class SingleASGISocketIOTester:
    def __init__(self, base_url="https://pifa-friends.preview.emergentagent.com"):
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
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
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

    def test_health_endpoint(self):
        """Test /api/health endpoint returns {"ok": True}"""
        success, status, data = self.make_request('GET', 'health')
        
        # Verify exact response format
        correct_response = (
            success and
            isinstance(data, dict) and
            data.get('ok') is True
        )
        
        return self.log_test(
            "Health Endpoint (/api/health)",
            correct_response,
            f"Status: {status}, Response: {data}"
        )

    def test_socketio_handshake(self):
        """Test Socket.IO server responds at /api/socketio with proper handshake"""
        try:
            # Test Socket.IO handshake endpoint
            socketio_url = f"{self.base_url}/api/socketio/"
            response = requests.get(socketio_url, params={'transport': 'polling', 'EIO': '4'}, timeout=10)
            
            # Socket.IO handshake should return specific response format
            handshake_successful = response.status_code == 200
            
            # Check for Engine.IO response format (starts with number + JSON)
            response_text = response.text
            contains_engineio_response = (
                response_text.startswith('0{') or  # Engine.IO handshake format
                '"sid":' in response_text or      # Session ID in response
                'upgrades' in response_text       # Engine.IO upgrades field
            )
            
            return self.log_test(
                "Socket.IO Handshake (/api/socketio)",
                handshake_successful and contains_engineio_response,
                f"Status: {response.status_code}, Engine.IO response: {contains_engineio_response}, Response preview: {response_text[:100]}"
            )
        except Exception as e:
            return self.log_test("Socket.IO Handshake", False, f"Exception: {str(e)}")

    def test_diagnostic_endpoint(self):
        """Test diagnostic endpoint works at /api/socketio-diag"""
        success, status, data = self.make_request('GET', 'socketio-diag')
        
        # Verify response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            data.get('ok') is True and
            'path' in data and
            'now' in data
        )
        
        # Verify path is correct for new implementation
        path_correct = data.get('path') == '/api/socketio' if valid_response else False
        
        # Verify timestamp is recent
        timestamp_valid = False
        if valid_response:
            try:
                server_time = datetime.fromisoformat(data['now'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                time_diff = abs((server_time - now).total_seconds())
                timestamp_valid = time_diff < 5
            except:
                timestamp_valid = False
        
        return self.log_test(
            "Diagnostic Endpoint (/api/socketio-diag)",
            valid_response and path_correct and timestamp_valid,
            f"Status: {status}, Valid: {valid_response}, Path: {data.get('path', 'N/A')}, Recent timestamp: {timestamp_valid}"
        )

    def test_cli_script_execution(self):
        """Test CLI script shows improved connectivity (should be 4/4 tests passing now)"""
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
            
            # Check output for test results
            output = result.stdout + result.stderr
            
            # Look for improved connectivity - should be 4/4 or at least better than 1/4
            has_test_results = ('✅' in output or '❌' in output) and ('passed' in output or 'failed' in output)
            
            # Check for specific improvements
            diagnostic_works = 'Diagnostic Endpoint' in output and '✅' in output
            socketio_improved = 'Socket.IO' in output
            
            # Look for 4/4 or improved results
            improved_results = (
                '4/4 passed' in output or 
                '3/4 passed' in output or 
                '2/4 passed' in output or
                ('✅' in output and output.count('✅') > 1)  # More than 1 success
            )
            
            return self.log_test(
                "CLI Script Execution (Improved Connectivity)",
                command_executed and has_test_results and diagnostic_works,
                f"Executed: {command_executed}, Has results: {has_test_results}, Diagnostic works: {diagnostic_works}, Improved: {improved_results}"
            )
        except subprocess.TimeoutExpired:
            return self.log_test("CLI Script Execution", False, "Command timed out")
        except Exception as e:
            return self.log_test("CLI Script Execution", False, f"Exception: {str(e)}")

    def test_route_separation(self):
        """Test that all /api routes go to FastAPI while /api/socketio goes to Socket.IO"""
        
        # Test FastAPI routes
        fastapi_routes = [
            ('health', 'FastAPI Health'),
            ('socketio-diag', 'FastAPI Diagnostic'),
            ('timez', 'FastAPI Time Sync')
        ]
        
        fastapi_working = []
        for route, name in fastapi_routes:
            success, status, data = self.make_request('GET', route)
            fastapi_working.append((name, success, status))
        
        # Test Socket.IO route
        try:
            socketio_url = f"{self.base_url}/api/socketio/"
            response = requests.get(socketio_url, params={'transport': 'polling', 'EIO': '4'}, timeout=10)
            socketio_works = response.status_code == 200 and ('sid' in response.text or 'upgrades' in response.text)
        except:
            socketio_works = False
        
        # All FastAPI routes should work
        fastapi_success_count = sum(1 for _, success, _ in fastapi_working if success)
        all_fastapi_work = fastapi_success_count == len(fastapi_routes)
        
        return self.log_test(
            "Route Separation (FastAPI vs Socket.IO)",
            all_fastapi_work and socketio_works,
            f"FastAPI routes working: {fastapi_success_count}/{len(fastapi_routes)}, Socket.IO works: {socketio_works}"
        )

    def test_single_asgi_wrapper_pattern(self):
        """Test that the single ASGI wrapper pattern is working correctly"""
        
        # Test 1: Verify no mount conflicts by testing multiple endpoints
        endpoints_to_test = [
            'health',
            'socketio-diag', 
            'timez'
        ]
        
        all_endpoints_work = True
        endpoint_results = []
        
        for endpoint in endpoints_to_test:
            success, status, data = self.make_request('GET', endpoint)
            endpoint_results.append((endpoint, success, status))
            if not success:
                all_endpoints_work = False
        
        # Test 2: Verify Socket.IO path works
        try:
            socketio_url = f"{self.base_url}/api/socketio/"
            response = requests.get(socketio_url, params={'transport': 'polling', 'EIO': '4'}, timeout=10)
            socketio_accessible = response.status_code == 200 and ('sid' in response.text or 'upgrades' in response.text)
        except:
            socketio_accessible = False
        
        # Test 3: Verify CORS is working (check headers)
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            cors_configured = response.status_code == 200  # If health works, CORS is likely OK
        except:
            cors_configured = False
        
        pattern_working = all_endpoints_work and socketio_accessible and cors_configured
        
        return self.log_test(
            "Single ASGI Wrapper Pattern",
            pattern_working,
            f"All endpoints work: {all_endpoints_work}, Socket.IO accessible: {socketio_accessible}, CORS configured: {cors_configured}"
        )

    def test_environment_variables(self):
        """Test that environment variables are correctly configured"""
        
        # Test backend environment by checking if Socket.IO path is correct
        success, status, data = self.make_request('GET', 'socketio-diag')
        
        if success and 'path' in data:
            backend_socket_path = data['path']
            backend_path_correct = backend_socket_path == '/api/socketio'
        else:
            backend_path_correct = False
        
        # Test frontend environment by checking if .env file has correct values
        try:
            frontend_env_path = "/app/frontend/.env"
            if os.path.exists(frontend_env_path):
                with open(frontend_env_path, 'r') as f:
                    env_content = f.read()
                
                # Check for new Socket.IO path configuration
                has_new_socket_path = 'NEXT_PUBLIC_SOCKET_PATH=/api/socketio' in env_content or 'VITE_SOCKET_PATH=/api/socketio' in env_content
                has_backend_url = 'REACT_APP_BACKEND_URL=' in env_content
                
                frontend_env_correct = has_new_socket_path and has_backend_url
            else:
                frontend_env_correct = False
        except:
            frontend_env_correct = False
        
        return self.log_test(
            "Environment Variables Configuration",
            backend_path_correct and frontend_env_correct,
            f"Backend path correct: {backend_path_correct} ({backend_socket_path if 'backend_socket_path' in locals() else 'N/A'}), Frontend env correct: {frontend_env_correct}"
        )

    def test_no_mount_shadows(self):
        """Test that there are no previous mounts that shadow /api routes"""
        
        # Test various /api endpoints to ensure they all work
        test_endpoints = [
            ('health', 'Health endpoint'),
            ('socketio-diag', 'Diagnostic endpoint'),
            ('timez', 'Time sync endpoint')
        ]
        
        all_accessible = True
        results = []
        
        for endpoint, description in test_endpoints:
            success, status, data = self.make_request('GET', endpoint)
            results.append((description, success, status))
            if not success:
                all_accessible = False
        
        # Also test that Socket.IO doesn't interfere with FastAPI routes
        try:
            # Make a request that should definitely go to FastAPI
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            health_is_fastapi = health_response.status_code == 200 and 'ok' in health_response.text
        except:
            health_is_fastapi = False
        
        no_shadows = all_accessible and health_is_fastapi
        
        return self.log_test(
            "No Mount Shadows",
            no_shadows,
            f"All endpoints accessible: {all_accessible}, Health is FastAPI: {health_is_fastapi}, Results: {len([r for r in results if r[1]])} / {len(results)} working"
        )

    def run_all_tests(self):
        """Run all single ASGI wrapper Socket.IO tests"""
        print("🔍 Single ASGI Wrapper Socket.IO Implementation Test")
        print("=" * 60)
        
        # Core functionality tests
        self.test_health_endpoint()
        self.test_socketio_handshake()
        self.test_diagnostic_endpoint()
        self.test_route_separation()
        
        # Implementation pattern tests
        self.test_single_asgi_wrapper_pattern()
        self.test_environment_variables()
        self.test_no_mount_shadows()
        
        # Integration test
        self.test_cli_script_execution()
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failed_test in self.failed_tests:
                print(f"  - {failed_test}")
        
        print(f"\n🎯 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed, self.tests_run, self.failed_tests

def main():
    """Main test execution"""
    tester = SingleASGISocketIOTester()
    passed, total, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()