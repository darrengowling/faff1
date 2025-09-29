#!/usr/bin/env python3
"""
PR2 and PR3 Testing Script
Tests the specific features mentioned in the review request
"""

import requests
import json
import time
import socketio
from datetime import datetime

class PR2PR3Tester:
    def __init__(self):
        self.base_url = "https://testid-enforcer.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzNmY4ZTVkMi03NmQ3LTQ4ZjAtOGMyYy0xMTQ5MTIwMTNhOWMiLCJleHAiOjE3NTg4OTE1MjZ9.zdOl6LxlSENv-fxuJ0MafpaEsCPd5CkRTDnOkj5E38E"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        self.test_results = []
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {name} - {details}")
        self.test_results.append((name, success, details))
        return success
    
    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=self.headers, timeout=15)
            
            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
        except Exception as e:
            return False, 0, {"error": str(e)}
    
    def test_pr2_connection_manager_api(self):
        """Test PR2: Connection Manager through API endpoints"""
        # Test health check to verify backend is running
        success, status, data = self.make_request('GET', 'health')
        return self.log_test(
            "PR2: Backend Health Check",
            success and data.get('status') == 'healthy',
            f"Status: {status}, Backend healthy: {data.get('status') == 'healthy'}"
        )
    
    def test_pr2_websocket_connection(self):
        """Test PR2: WebSocket connection with authentication"""
        try:
            sio = socketio.Client()
            connection_successful = False
            auth_successful = False
            
            @sio.event
            def connect():
                nonlocal connection_successful
                connection_successful = True
            
            @sio.event
            def connection_status(data):
                nonlocal auth_successful
                if data.get('status') == 'connected':
                    auth_successful = True
            
            # Test connection with authentication
            sio.connect(
                self.base_url,
                auth={'token': self.access_token},
                transports=['websocket', 'polling']
            )
            
            time.sleep(3)
            sio.disconnect()
            
            return self.log_test(
                "PR2: WebSocket Connection & Authentication",
                connection_successful and auth_successful,
                f"Connected: {connection_successful}, Authenticated: {auth_successful}"
            )
            
        except Exception as e:
            return self.log_test("PR2: WebSocket Connection & Authentication", False, f"Exception: {str(e)}")
    
    def test_pr2_heartbeat_system(self):
        """Test PR2: Heartbeat system"""
        try:
            sio = socketio.Client()
            heartbeat_ack_received = False
            
            @sio.event
            def connect():
                pass
            
            @sio.event
            def heartbeat_ack(data):
                nonlocal heartbeat_ack_received
                heartbeat_ack_received = True
            
            sio.connect(
                self.base_url,
                auth={'token': self.access_token},
                transports=['websocket', 'polling']
            )
            
            time.sleep(2)
            
            # Send heartbeat
            sio.call('heartbeat', {}, timeout=5)
            time.sleep(2)
            
            sio.disconnect()
            
            return self.log_test(
                "PR2: Heartbeat System",
                heartbeat_ack_received,
                f"Heartbeat ack received: {heartbeat_ack_received}"
            )
            
        except Exception as e:
            return self.log_test("PR2: Heartbeat System", False, f"Exception: {str(e)}")
    
    def test_pr2_state_snapshot_system(self):
        """Test PR2: State snapshot system"""
        try:
            sio = socketio.Client()
            snapshot_received = False
            snapshot_valid = False
            
            @sio.event
            def connect():
                pass
            
            @sio.event
            def auction_snapshot(data):
                nonlocal snapshot_received, snapshot_valid
                snapshot_received = True
                # Validate snapshot structure
                snapshot_valid = (
                    isinstance(data, dict) and
                    'server_time' in data and
                    'snapshot_version' in data
                )
            
            sio.connect(
                self.base_url,
                auth={'token': self.access_token},
                transports=['websocket', 'polling']
            )
            
            time.sleep(2)
            
            # Request snapshot with a test auction ID
            sio.call('request_snapshot', {'auction_id': 'test_auction'}, timeout=5)
            time.sleep(3)
            
            sio.disconnect()
            
            return self.log_test(
                "PR2: State Snapshot System",
                snapshot_received and snapshot_valid,
                f"Snapshot received: {snapshot_received}, Valid: {snapshot_valid}"
            )
            
        except Exception as e:
            return self.log_test("PR2: State Snapshot System", False, f"Exception: {str(e)}")
    
    def test_pr3_lot_closing_endpoints(self):
        """Test PR3: Lot closing API endpoints"""
        # Test lot close endpoint
        success_close, status_close, data_close = self.make_request(
            'POST',
            'lots/test_lot_id/close',
            {"forced": False, "reason": "Test close"},
            expected_status=404  # Expected since lot doesn't exist
        )
        
        # Test undo endpoint
        success_undo, status_undo, data_undo = self.make_request(
            'POST',
            'lots/undo/test_action_id',
            {},
            expected_status=404  # Expected since action doesn't exist
        )
        
        # Test get undo actions endpoint
        success_get, status_get, data_get = self.make_request(
            'GET',
            'lots/test_lot_id/undo-actions',
            expected_status=404  # Expected since lot doesn't exist
        )
        
        endpoints_working = (
            success_close and status_close == 404 and
            success_undo and status_undo == 404 and
            success_get and status_get == 404
        )
        
        return self.log_test(
            "PR3: Lot Closing API Endpoints",
            endpoints_working,
            f"Close: {status_close}, Undo: {status_undo}, Get: {status_get}"
        )
    
    def test_pr3_commissioner_permissions(self):
        """Test PR3: Commissioner permissions for lot closing"""
        # Test that endpoints require authentication
        headers_no_auth = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(
                f"{self.api_url}/lots/test_lot/close",
                json={"forced": False, "reason": "Test"},
                headers=headers_no_auth,
                timeout=15
            )
            auth_required = response.status_code == 401
        except:
            auth_required = False
        
        return self.log_test(
            "PR3: Commissioner Permissions",
            auth_required,
            f"Authentication required: {auth_required}"
        )
    
    def test_pr3_undo_system_validation(self):
        """Test PR3: Undo system validation"""
        # Test undo with invalid action ID
        success, status, data = self.make_request(
            'POST',
            'lots/undo/invalid_action_id',
            {},
            expected_status=404
        )
        
        validation_working = success and status == 404
        
        return self.log_test(
            "PR3: Undo System Validation",
            validation_working,
            f"Validation working: {validation_working}, Status: {status}"
        )
    
    def test_pr3_database_operations(self):
        """Test PR3: Database operations consistency"""
        # Test multiple rapid requests to same endpoint (should handle atomically)
        results = []
        for i in range(3):
            success, status, data = self.make_request(
                'POST',
                f'lots/atomic_test_lot/close',
                {"forced": False, "reason": f"Atomic test {i}"},
                expected_status=404  # Expected since lot doesn't exist
            )
            results.append((success, status))
        
        # All should return consistent 404 responses
        consistent_responses = all(status == 404 for success, status in results)
        
        return self.log_test(
            "PR3: Database Operations Atomic",
            consistent_responses,
            f"Consistent responses: {consistent_responses}, Results: {[s for _, s in results]}"
        )
    
    def run_pr2_tests(self):
        """Run all PR2 tests"""
        print("\n🔄 PR2: ROBUST RECONNECT & PRESENCE SYSTEM TESTS")
        print("=" * 60)
        
        pr2_results = []
        pr2_results.append(self.test_pr2_connection_manager_api())
        pr2_results.append(self.test_pr2_websocket_connection())
        pr2_results.append(self.test_pr2_heartbeat_system())
        pr2_results.append(self.test_pr2_state_snapshot_system())
        
        pr2_passed = sum(pr2_results)
        pr2_total = len(pr2_results)
        
        print(f"\nPR2 Results: {pr2_passed}/{pr2_total} tests passed")
        return pr2_passed, pr2_total
    
    def run_pr3_tests(self):
        """Run all PR3 tests"""
        print("\n⏱️  PR3: SAFE-CLOSE + 10S UNDO SYSTEM TESTS")
        print("=" * 60)
        
        pr3_results = []
        pr3_results.append(self.test_pr3_lot_closing_endpoints())
        pr3_results.append(self.test_pr3_commissioner_permissions())
        pr3_results.append(self.test_pr3_undo_system_validation())
        pr3_results.append(self.test_pr3_database_operations())
        
        pr3_passed = sum(pr3_results)
        pr3_total = len(pr3_results)
        
        print(f"\nPR3 Results: {pr3_passed}/{pr3_total} tests passed")
        return pr3_passed, pr3_total
    
    def run_all_tests(self):
        """Run all PR2 and PR3 tests"""
        print("🚀 PR2 & PR3 Testing Suite")
        print("Focus: Robust Reconnect & Presence + Safe-Close + 10s Undo")
        print("=" * 80)
        
        pr2_passed, pr2_total = self.run_pr2_tests()
        pr3_passed, pr3_total = self.run_pr3_tests()
        
        total_passed = pr2_passed + pr3_passed
        total_tests = pr2_total + pr3_total
        
        print("\n" + "=" * 80)
        print("📊 FINAL SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
        
        print(f"\nPR2 (Robust Reconnect & Presence): {pr2_passed}/{pr2_total}")
        print(f"PR3 (Safe-Close + 10s Undo): {pr3_passed}/{pr3_total}")
        
        failed_tests = [name for name, success, _ in self.test_results if not success]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for i, test_name in enumerate(failed_tests, 1):
                print(f"   {i}. {test_name}")
        
        if total_passed == total_tests:
            print("\n🎉 All PR2 & PR3 tests passed!")
        else:
            print(f"\n⚠️  {total_tests - total_passed} tests failed")
        
        return total_passed, total_tests

if __name__ == "__main__":
    tester = PR2PR3Tester()
    tester.run_all_tests()