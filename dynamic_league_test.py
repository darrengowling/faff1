#!/usr/bin/env python3
"""
Dynamic League Minimum Size Implementation Testing Suite
Tests the centralized league settings and dynamic minimum member requirements
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time

class DynamicLeagueSizeAPITester:
    def __init__(self, base_url="https://pifa-friends-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.commissioner_token = None
        self.user_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.commissioner_email = "commissioner@example.com"
        self.test_league_id = None
        self.test_league_id_min_2 = None
        self.test_league_id_min_6 = None
        
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
        
        # Use provided token or default commissioner token
        auth_token = token or self.commissioner_token
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
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def authenticate_with_dev_token(self):
        """Authenticate using development magic link flow"""
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.commissioner_email},
            token=None
        )
        
        if not success or 'dev_magic_link' not in data:
            return self.log_test("Authentication Setup", False, f"Failed to get dev magic link: {status}")
        
        # Extract token from dev magic link
        magic_link = data['dev_magic_link']
        token = magic_link.split('token=')[1] if 'token=' in magic_link else None
        
        if not token:
            return self.log_test("Authentication Setup", False, "Failed to extract token from magic link")
        
        # Step 2: Verify token
        success, status, auth_data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if success and 'access_token' in auth_data:
            self.commissioner_token = auth_data['access_token']
            self.user_data = auth_data['user']
            return self.log_test("Authentication Setup", True, f"Authenticated as {auth_data['user']['email']}")
        
        return self.log_test("Authentication Setup", False, f"Token verification failed: {status}")

    def test_league_settings_endpoint(self):
        """Test GET /api/leagues/{league_id}/settings endpoint returns centralized settings"""
        if not self.test_league_id:
            return self.log_test("League Settings Endpoint", False, "No test league ID")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        
        # Verify response structure matches expected centralized format
        valid_response = (
            success and
            isinstance(data, dict) and
            'clubSlots' in data and
            'budgetPerManager' in data and
            'leagueSize' in data and
            isinstance(data['leagueSize'], dict) and
            'min' in data['leagueSize'] and
            'max' in data['leagueSize']
        )
        
        # Verify data types and reasonable values
        data_valid = False
        if valid_response:
            data_valid = (
                isinstance(data['clubSlots'], int) and data['clubSlots'] > 0 and
                isinstance(data['budgetPerManager'], int) and data['budgetPerManager'] > 0 and
                isinstance(data['leagueSize']['min'], int) and data['leagueSize']['min'] >= 2 and
                isinstance(data['leagueSize']['max'], int) and data['leagueSize']['max'] >= data['leagueSize']['min']
            )
        
        return self.log_test(
            "League Settings Endpoint",
            valid_response and data_valid,
            f"Status: {status}, Valid structure: {valid_response}, Valid data: {data_valid}, Settings: {data if valid_response else 'N/A'}"
        )

    def test_create_leagues_with_different_minimums(self):
        """Create test leagues with different minimum member requirements"""
        results = []
        
        # League with min=4 (default)
        league_data_default = {
            "name": f"Test League Default Min {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "league_size": {"min": 4, "max": 8},
                "scoring_rules": {"club_goal": 1, "club_win": 3, "club_draw": 1}
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data_default)
        if success and 'id' in data:
            self.test_league_id = data['id']
            results.append(f"✓ Created league with min=4: {data['id']}")
        else:
            results.append(f"✗ Failed to create default league: {status}")
        
        # League with min=2
        league_data_min_2 = {
            "name": f"Test League Min 2 {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "league_size": {"min": 2, "max": 6},
                "scoring_rules": {"club_goal": 1, "club_win": 3, "club_draw": 1}
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data_min_2)
        if success and 'id' in data:
            self.test_league_id_min_2 = data['id']
            results.append(f"✓ Created league with min=2: {data['id']}")
        else:
            results.append(f"✗ Failed to create min=2 league: {status}")
        
        # League with min=6
        league_data_min_6 = {
            "name": f"Test League Min 6 {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "league_size": {"min": 6, "max": 8},
                "scoring_rules": {"club_goal": 1, "club_win": 3, "club_draw": 1}
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data_min_6)
        if success and 'id' in data:
            self.test_league_id_min_6 = data['id']
            results.append(f"✓ Created league with min=6: {data['id']}")
        else:
            results.append(f"✗ Failed to create min=6 league: {status}")
        
        success_count = len([r for r in results if r.startswith('✓')])
        return self.log_test(
            "Create Test Leagues with Different Minimums",
            success_count >= 2,
            f"Created {success_count}/3 leagues: {', '.join(results)}"
        )

    def test_league_status_dynamic_minimum_validation(self):
        """Test league status endpoint reflects dynamic minimum requirements"""
        test_cases = [
            (self.test_league_id, 4, "Default Min 4"),
            (self.test_league_id_min_2, 2, "Min 2"),
            (self.test_league_id_min_6, 6, "Min 6")
        ]
        
        results = []
        for league_id, expected_min, description in test_cases:
            if not league_id:
                results.append(f"✗ {description}: No league ID")
                continue
            
            success, status, data = self.make_request('GET', f'leagues/{league_id}/status')
            
            if success and 'min_members' in data:
                if data['min_members'] == expected_min:
                    # Check if is_ready reflects the minimum requirement
                    member_count = data.get('member_count', 0)
                    expected_ready = member_count >= expected_min
                    actual_ready = data.get('is_ready', False)
                    
                    if expected_ready == actual_ready:
                        results.append(f"✓ {description}: min={data['min_members']}, members={member_count}, ready={actual_ready}")
                    else:
                        results.append(f"✗ {description}: Ready status mismatch - expected {expected_ready}, got {actual_ready}")
                else:
                    results.append(f"✗ {description}: Expected min={expected_min}, got {data['min_members']}")
            else:
                results.append(f"✗ {description}: Failed to get status or missing min_members: {status}")
        
        success_count = len([r for r in results if r.startswith('✓')])
        return self.log_test(
            "League Status Dynamic Minimum Validation",
            success_count >= 2,
            f"Validated {success_count}/{len(test_cases)} leagues: {'; '.join(results)}"
        )

    def test_league_settings_centralized_response(self):
        """Test that league settings endpoint returns consistent centralized format"""
        test_cases = [
            (self.test_league_id, {"min": 4, "max": 8}, "Default League"),
            (self.test_league_id_min_2, {"min": 2, "max": 6}, "Min 2 League"),
            (self.test_league_id_min_6, {"min": 6, "max": 8}, "Min 6 League")
        ]
        
        results = []
        for league_id, expected_size, description in test_cases:
            if not league_id:
                results.append(f"✗ {description}: No league ID")
                continue
            
            success, status, data = self.make_request('GET', f'leagues/{league_id}/settings')
            
            if success and 'leagueSize' in data:
                actual_size = data['leagueSize']
                if actual_size == expected_size:
                    # Verify other required fields are present
                    has_all_fields = (
                        'clubSlots' in data and
                        'budgetPerManager' in data and
                        isinstance(data['clubSlots'], int) and
                        isinstance(data['budgetPerManager'], int)
                    )
                    
                    if has_all_fields:
                        results.append(f"✓ {description}: {actual_size}, clubSlots={data['clubSlots']}, budget={data['budgetPerManager']}")
                    else:
                        results.append(f"✗ {description}: Missing required fields")
                else:
                    results.append(f"✗ {description}: Expected {expected_size}, got {actual_size}")
            else:
                results.append(f"✗ {description}: Failed to get settings: {status}")
        
        success_count = len([r for r in results if r.startswith('✓')])
        return self.log_test(
            "League Settings Centralized Response Format",
            success_count >= 2,
            f"Validated {success_count}/{len(test_cases)} settings: {'; '.join(results)}"
        )

    def test_auction_start_minimum_validation(self):
        """Test that auction start is blocked when members < minimum from settings"""
        if not self.test_league_id_min_6:
            return self.log_test("Auction Start Minimum Validation", False, "No min=6 league ID")
        
        # Get current league status
        success, status, league_status = self.make_request('GET', f'leagues/{self.test_league_id_min_6}/status')
        
        if not success:
            return self.log_test("Auction Start Minimum Validation", False, f"Failed to get league status: {status}")
        
        member_count = league_status.get('member_count', 0)
        min_members = league_status.get('min_members', 0)
        is_ready = league_status.get('is_ready', False)
        can_start_auction = league_status.get('can_start_auction', False)
        
        # With only 1 member (commissioner) and min=6, auction should not be startable
        validation_correct = (
            member_count < min_members and
            not is_ready and
            not can_start_auction
        )
        
        # Try to start auction (should fail)
        success_start, status_start, start_data = self.make_request(
            'POST',
            f'auction/{self.test_league_id_min_6}/start',
            expected_status=400  # Should fail
        )
        
        auction_start_blocked = success_start and status_start == 400
        
        return self.log_test(
            "Auction Start Minimum Validation",
            validation_correct and auction_start_blocked,
            f"Members: {member_count}/{min_members}, Ready: {is_ready}, Can start: {can_start_auction}, Start blocked: {auction_start_blocked}"
        )

    def test_dynamic_settings_update(self):
        """Test updating league minimum and verifying dynamic behavior"""
        if not self.test_league_id:
            return self.log_test("Dynamic Settings Update", False, "No test league ID")
        
        # Update league minimum from 4 to 3
        settings_update = {
            "league_size": {"min": 3, "max": 8}
        }
        
        success, status, update_data = self.make_request(
            'PATCH',
            f'leagues/{self.test_league_id}/settings',
            settings_update
        )
        
        if not success:
            return self.log_test("Dynamic Settings Update", False, f"Failed to update settings: {status}")
        
        # Verify settings were updated
        success_get, status_get, settings_data = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        
        if not success_get:
            return self.log_test("Dynamic Settings Update", False, f"Failed to get updated settings: {status_get}")
        
        settings_updated = (
            settings_data.get('leagueSize', {}).get('min') == 3 and
            settings_data.get('leagueSize', {}).get('max') == 8
        )
        
        # Verify league status reflects new minimum
        success_status, status_status, league_status = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        
        status_updated = False
        if success_status:
            status_updated = league_status.get('min_members') == 3
        
        return self.log_test(
            "Dynamic Settings Update",
            settings_updated and status_updated,
            f"Settings updated: {settings_updated}, Status updated: {status_updated}, New min: {settings_data.get('leagueSize', {}).get('min', 'N/A')}"
        )

    def test_member_count_calculations(self):
        """Test that member count calculations use dynamic minimums"""
        test_cases = [
            (self.test_league_id, 3, "Updated to Min 3"),  # Updated in previous test
            (self.test_league_id_min_2, 2, "Min 2 League"),
            (self.test_league_id_min_6, 6, "Min 6 League")
        ]
        
        results = []
        for league_id, expected_min, description in test_cases:
            if not league_id:
                results.append(f"✗ {description}: No league ID")
                continue
            
            success, status, league_status = self.make_request('GET', f'leagues/{league_id}/status')
            
            if success:
                member_count = league_status.get('member_count', 0)
                min_members = league_status.get('min_members', 0)
                is_ready = league_status.get('is_ready', False)
                
                # Calculate expected readiness
                expected_ready = member_count >= expected_min
                
                # Verify calculations
                calculations_correct = (
                    min_members == expected_min and
                    is_ready == expected_ready
                )
                
                if calculations_correct:
                    needed = max(0, expected_min - member_count)
                    results.append(f"✓ {description}: {member_count}/{expected_min} members, ready={is_ready}, need {needed} more")
                else:
                    results.append(f"✗ {description}: Calculation error - min={min_members} (expected {expected_min}), ready={is_ready} (expected {expected_ready})")
            else:
                results.append(f"✗ {description}: Failed to get status: {status}")
        
        success_count = len([r for r in results if r.startswith('✓')])
        return self.log_test(
            "Member Count Calculations",
            success_count >= 2,
            f"Validated {success_count}/{len(test_cases)} calculations: {'; '.join(results)}"
        )

    def test_backend_integration_consistency(self):
        """Test backend integration consistency across different endpoints"""
        if not self.test_league_id_min_2:
            return self.log_test("Backend Integration Consistency", False, "No min=2 league ID")
        
        # Get data from multiple endpoints
        endpoints_data = {}
        
        # League details
        success, status, league_data = self.make_request('GET', f'leagues/{self.test_league_id_min_2}')
        if success:
            endpoints_data['league'] = league_data
        
        # League settings
        success, status, settings_data = self.make_request('GET', f'leagues/{self.test_league_id_min_2}/settings')
        if success:
            endpoints_data['settings'] = settings_data
        
        # League status
        success, status, status_data = self.make_request('GET', f'leagues/{self.test_league_id_min_2}/status')
        if success:
            endpoints_data['status'] = status_data
        
        # League members
        success, status, members_data = self.make_request('GET', f'leagues/{self.test_league_id_min_2}/members')
        if success:
            endpoints_data['members'] = members_data
        
        # Verify consistency across endpoints
        consistency_checks = []
        
        # Check minimum members consistency
        league_min = endpoints_data.get('league', {}).get('settings', {}).get('league_size', {}).get('min')
        settings_min = endpoints_data.get('settings', {}).get('leagueSize', {}).get('min')
        status_min = endpoints_data.get('status', {}).get('min_members')
        
        min_consistent = league_min == settings_min == status_min == 2
        consistency_checks.append(f"Min members consistent: {min_consistent} (league={league_min}, settings={settings_min}, status={status_min})")
        
        # Check member count consistency
        league_count = endpoints_data.get('league', {}).get('member_count')
        status_count = endpoints_data.get('status', {}).get('member_count')
        members_count = len(endpoints_data.get('members', []))
        
        count_consistent = league_count == status_count == members_count
        consistency_checks.append(f"Member count consistent: {count_consistent} (league={league_count}, status={status_count}, members={members_count})")
        
        # Check readiness calculation consistency
        expected_ready = members_count >= 2
        status_ready = endpoints_data.get('status', {}).get('is_ready', False)
        
        ready_consistent = expected_ready == status_ready
        consistency_checks.append(f"Readiness consistent: {ready_consistent} (expected={expected_ready}, status={status_ready})")
        
        all_consistent = min_consistent and count_consistent and ready_consistent
        
        return self.log_test(
            "Backend Integration Consistency",
            all_consistent,
            f"All endpoints consistent: {all_consistent}. Checks: {'; '.join(consistency_checks)}"
        )

    def run_all_tests(self):
        """Run all dynamic league minimum size tests"""
        print("🧪 DYNAMIC LEAGUE MINIMUM SIZE IMPLEMENTATION TESTING")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate_with_dev_token():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Core functionality tests
        self.test_create_leagues_with_different_minimums()
        self.test_league_settings_endpoint()
        self.test_league_settings_centralized_response()
        self.test_league_status_dynamic_minimum_validation()
        self.test_member_count_calculations()
        self.test_auction_start_minimum_validation()
        self.test_dynamic_settings_update()
        self.test_backend_integration_consistency()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 DYNAMIC LEAGUE SIZE TESTING SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                print(f"  • {failure}")
        
        print(f"\n🎯 TESTING COMPLETE")
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = DynamicLeagueSizeAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)