#!/usr/bin/env python3
"""
Centralized League Settings Implementation Testing Suite
Tests the new centralized league settings features as specified in the review request
"""

import requests
import sys
import json
import os
import subprocess
from datetime import datetime, timezone
import time

class CentralizedLeagueSettingsTest:
    def __init__(self, base_url="https://league-creator-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.test_email = "league_settings_test@example.com"
        self.test_league_id = None
        
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

    def make_request(self, method, endpoint, data=None, expected_status=200, token=None, use_auth=True):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Handle authentication
        if use_auth:
            auth_token = token if token is not None else self.token
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

    def authenticate_test_user(self):
        """Authenticate test user using magic link flow"""
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            use_auth=False
        )
        
        if not success:
            return self.log_test("Authentication Setup", False, f"Failed to request magic link: {status}")
        
        # Extract dev magic link token from response
        if 'dev_magic_link' in data:
            magic_link = data['dev_magic_link']
            # Extract token from URL
            token = magic_link.split('token=')[1] if 'token=' in magic_link else None
            
            if token:
                # Step 2: Verify token
                success, status, auth_data = self.make_request(
                    'POST',
                    'auth/verify',
                    {"token": token},
                    use_auth=False
                )
                
                if success and 'access_token' in auth_data:
                    self.token = auth_data['access_token']
                    self.user_data = auth_data['user']
                    return self.log_test("Authentication Setup", True, f"Authenticated as {auth_data['user']['email']}")
        
        return self.log_test("Authentication Setup", False, "Failed to extract or verify token")

    def create_test_league(self):
        """Create a test league for settings testing"""
        league_data = {
            "name": f"League Settings Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 150,
                "min_increment": 1,
                "club_slots_per_manager": 4,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "max_managers": 6,
                "min_managers": 3,
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            self.test_league_id = data['id']
            return self.log_test(
                "Test League Creation",
                True,
                f"League ID: {data.get('id', 'None')}"
            )
        
        return self.log_test(
            "Test League Creation",
            False,
            f"Status: {status}, Response: {data}"
        )

    def test_league_settings_endpoint(self):
        """Test GET /leagues/:id/settings endpoint returns proper JSON structure"""
        if not self.test_league_id:
            return self.log_test("League Settings Endpoint", False, "No test league ID")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        
        # Verify response structure
        valid_structure = (
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
        valid_data = False
        if valid_structure:
            valid_data = (
                isinstance(data['clubSlots'], int) and
                isinstance(data['budgetPerManager'], int) and
                isinstance(data['leagueSize']['min'], int) and
                isinstance(data['leagueSize']['max'], int) and
                data['clubSlots'] > 0 and  # Should be positive
                data['budgetPerManager'] > 0 and  # Should be positive
                data['leagueSize']['min'] > 0 and  # Should be positive
                data['leagueSize']['max'] >= data['leagueSize']['min']  # Max should be >= min
            )
        
        return self.log_test(
            "League Settings Endpoint Structure",
            valid_structure and valid_data,
            f"Status: {status}, Structure: {valid_structure}, Data: {valid_data}, Response: {data if success else 'N/A'}"
        )

    def test_league_settings_authentication(self):
        """Test that endpoint requires authentication"""
        if not self.test_league_id:
            return self.log_test("League Settings Authentication", False, "No test league ID")
        
        # Test without token
        success, status, data = self.make_request(
            'GET', 
            f'leagues/{self.test_league_id}/settings',
            expected_status=403,
            use_auth=False
        )
        
        auth_required = success and status == 403
        
        # Test with invalid token
        success2, status2, data2 = self.make_request(
            'GET',
            f'leagues/{self.test_league_id}/settings',
            token="invalid_token",
            expected_status=401
        )
        
        invalid_token_rejected = success2 and status2 == 401
        
        return self.log_test(
            "League Settings Authentication Required",
            auth_required and invalid_token_rejected,
            f"No token: {status}, Invalid token: {status2}"
        )

    def test_useLeagueSettings_hook_exists(self):
        """Test that useLeagueSettings hook exists and is properly structured"""
        hook_path = "/app/frontend/src/hooks/useLeagueSettings.js"
        
        try:
            if not os.path.exists(hook_path):
                return self.log_test("useLeagueSettings Hook Exists", False, "Hook file not found")
            
            with open(hook_path, 'r') as f:
                hook_content = f.read()
            
            # Check for required hook structure
            has_export = 'export const useLeagueSettings' in hook_content
            has_useState = 'useState' in hook_content
            has_useEffect = 'useEffect' in hook_content
            has_loading_state = 'loading' in hook_content
            has_settings_state = 'settings' in hook_content
            has_api_call = 'leagues/${leagueId}/settings' in hook_content
            has_subscription = 'league_settings_updated' in hook_content
            
            hook_structure_valid = (
                has_export and has_useState and has_useEffect and 
                has_loading_state and has_settings_state and has_api_call
            )
            
            return self.log_test(
                "useLeagueSettings Hook Structure",
                hook_structure_valid,
                f"Export: {has_export}, States: {has_useState and has_loading_state}, API: {has_api_call}, Subscription: {has_subscription}"
            )
        except Exception as e:
            return self.log_test("useLeagueSettings Hook Exists", False, f"Exception: {str(e)}")

    def test_myclubs_component_integration(self):
        """Test that MyClubs component imports and uses useLeagueSettings hook"""
        myclubs_path = "/app/frontend/src/components/MyClubs.js"
        
        try:
            if not os.path.exists(myclubs_path):
                return self.log_test("MyClubs Hook Integration", False, "MyClubs component not found")
            
            with open(myclubs_path, 'r') as f:
                component_content = f.read()
            
            # Check for hook import
            has_hook_import = 'useLeagueSettings' in component_content and 'from' in component_content
            
            # Check for hook usage
            has_hook_usage = 'useLeagueSettings(leagueId)' in component_content
            
            # Check for settings destructuring
            has_settings_destructure = 'settings: leagueSettings' in component_content
            
            # Check for loading state usage
            has_loading_usage = 'settingsLoading' in component_content
            
            # Check that BudgetStatus uses league settings instead of hardcoded values
            has_budget_status_integration = (
                'leagueSettings ? leagueSettings.budgetPerManager' in component_content and
                'leagueSettings ? leagueSettings.clubSlots' in component_content
            )
            
            integration_complete = (
                has_hook_import and has_hook_usage and has_settings_destructure and
                has_loading_usage and has_budget_status_integration
            )
            
            return self.log_test(
                "MyClubs useLeagueSettings Integration",
                integration_complete,
                f"Import: {has_hook_import}, Usage: {has_hook_usage}, BudgetStatus: {has_budget_status_integration}"
            )
        except Exception as e:
            return self.log_test("MyClubs Hook Integration", False, f"Exception: {str(e)}")

    def test_eslint_configuration(self):
        """Test that ESLint is configured to forbid magic numbers for club slots"""
        eslint_path = "/app/frontend/.eslintrc.js"
        
        try:
            if not os.path.exists(eslint_path):
                return self.log_test("ESLint Configuration", False, ".eslintrc.js not found")
            
            with open(eslint_path, 'r') as f:
                eslint_content = f.read()
            
            # Check for no-magic-numbers rule
            has_magic_numbers_rule = 'no-magic-numbers' in eslint_content
            
            # Check for component-specific override
            has_component_override = 'src/components/**/*.js' in eslint_content
            
            # Check for error level on components
            has_error_level = "'error'" in eslint_content
            
            # Check for test file exception
            has_test_exception = '**/*.test.js' in eslint_content and "'off'" in eslint_content
            
            # Check for custom message about useLeagueSettings
            has_custom_message = 'useLeagueSettings' in eslint_content
            
            eslint_configured = (
                has_magic_numbers_rule and has_component_override and 
                has_error_level and has_test_exception
            )
            
            return self.log_test(
                "ESLint Magic Numbers Configuration",
                eslint_configured,
                f"Rule: {has_magic_numbers_rule}, Override: {has_component_override}, Custom message: {has_custom_message}"
            )
        except Exception as e:
            return self.log_test("ESLint Configuration", False, f"Exception: {str(e)}")

    def test_no_hardcoded_club_slots(self):
        """Test that no hardcoded '3 club slot(s)' references exist in UI code"""
        try:
            # Search for hardcoded club slot references
            frontend_src = "/app/frontend/src"
            hardcoded_references = []
            
            # Patterns to search for
            patterns = [
                "3 club slot",
                "3 club slots", 
                "club_slots_per_manager: 3",
                "clubSlots: 3",
                "slots: 3"
            ]
            
            for root, dirs, files in os.walk(frontend_src):
                # Skip test directories
                if any(test_dir in root for test_dir in ['__tests__', '__mocks__', '.test.', '.spec.']):
                    continue
                    
                for file in files:
                    if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                for pattern in patterns:
                                    if pattern in content:
                                        hardcoded_references.append(f"{file_path}: {pattern}")
                        except:
                            pass  # Skip files that can't be read
            
            no_hardcoded_values = len(hardcoded_references) == 0
            
            return self.log_test(
                "No Hardcoded Club Slots",
                no_hardcoded_values,
                f"Hardcoded references found: {len(hardcoded_references)} - {hardcoded_references[:3] if hardcoded_references else 'None'}"
            )
        except Exception as e:
            return self.log_test("No Hardcoded Club Slots", False, f"Exception: {str(e)}")

    def test_budget_status_component_integration(self):
        """Test that BudgetStatus component receives league settings instead of hardcoded values"""
        try:
            # Check BudgetStatus usage in MyClubs
            myclubs_path = "/app/frontend/src/components/MyClubs.js"
            
            if not os.path.exists(myclubs_path):
                return self.log_test("BudgetStatus Integration", False, "MyClubs component not found")
            
            with open(myclubs_path, 'r') as f:
                content = f.read()
            
            # Look for BudgetStatus component usage
            has_budget_status = '<BudgetStatus' in content
            
            # Check that it uses leagueSettings for budgetPerManager
            uses_league_budget = 'leagueSettings ? leagueSettings.budgetPerManager' in content
            
            # Check that it uses leagueSettings for clubSlots
            uses_league_slots = 'leagueSettings ? leagueSettings.clubSlots' in content
            
            # Check for fallback values
            has_fallbacks = 'budget_info.budget_start' in content and 'budget_info.clubs_owned + budget_info.slots_available' in content
            
            integration_correct = (
                has_budget_status and uses_league_budget and 
                uses_league_slots and has_fallbacks
            )
            
            return self.log_test(
                "BudgetStatus League Settings Integration",
                integration_correct,
                f"Component: {has_budget_status}, Budget: {uses_league_budget}, Slots: {uses_league_slots}, Fallbacks: {has_fallbacks}"
            )
        except Exception as e:
            return self.log_test("BudgetStatus Integration", False, f"Exception: {str(e)}")

    def test_eslint_rule_enforcement(self):
        """Test that ESLint rule catches magic number 3 in UI components"""
        try:
            # Create a temporary test file with magic number 3
            test_file_path = "/app/frontend/src/components/test_magic_number.js"
            test_content = """
import React from 'react';

const TestComponent = () => {
  const clubSlots = 3; // This should trigger ESLint error
  return <div>Club slots: {clubSlots}</div>;
};

export default TestComponent;
"""
            
            # Write test file
            with open(test_file_path, 'w') as f:
                f.write(test_content)
            
            # Run ESLint on the test file
            result = subprocess.run(
                ['npx', 'eslint', test_file_path],
                cwd='/app/frontend',
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up test file
            os.remove(test_file_path)
            
            # Check if ESLint caught the magic number
            eslint_output = result.stdout + result.stderr
            caught_magic_number = 'no-magic-numbers' in eslint_output and '3' in eslint_output
            
            return self.log_test(
                "ESLint Magic Number Detection",
                caught_magic_number,
                f"ESLint detected magic number: {caught_magic_number}, Exit code: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return self.log_test("ESLint Magic Number Detection", False, "ESLint command timed out")
        except Exception as e:
            return self.log_test("ESLint Magic Number Detection", False, f"Exception: {str(e)}")

    def test_league_settings_endpoint_error_handling(self):
        """Test error handling for league settings endpoint"""
        # Test with non-existent league
        success, status, data = self.make_request(
            'GET',
            'leagues/00000000-0000-0000-0000-000000000000/settings',
            expected_status=403  # Will be 403 because user is not a member, not 404
        )
        
        handles_not_found = success and status == 403
        
        return self.log_test(
            "League Settings Error Handling",
            handles_not_found,
            f"Non-member access denied: {handles_not_found}"
        )

    def run_all_tests(self):
        """Run all centralized league settings tests"""
        print("🧪 CENTRALIZED LEAGUE SETTINGS TESTING SUITE")
        print("=" * 60)
        
        # Authentication and setup
        if not self.authenticate_test_user():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        if not self.create_test_league():
            print("❌ Test league creation failed - cannot proceed with tests")
            return False
        
        # Backend API tests
        print("\n📡 BACKEND API TESTS")
        print("-" * 30)
        self.test_league_settings_endpoint()
        self.test_league_settings_authentication()
        self.test_league_settings_endpoint_error_handling()
        
        # Frontend hook tests
        print("\n🎣 FRONTEND HOOK TESTS")
        print("-" * 30)
        self.test_useLeagueSettings_hook_exists()
        
        # Component integration tests
        print("\n🧩 COMPONENT INTEGRATION TESTS")
        print("-" * 30)
        self.test_myclubs_component_integration()
        self.test_budget_status_component_integration()
        
        # ESLint configuration tests
        print("\n📏 ESLINT CONFIGURATION TESTS")
        print("-" * 30)
        self.test_eslint_configuration()
        self.test_eslint_rule_enforcement()
        
        # Code quality tests
        print("\n🔍 CODE QUALITY TESTS")
        print("-" * 30)
        self.test_no_hardcoded_club_slots()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failed_test in self.failed_tests:
                print(f"  • {failed_test}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = CentralizedLeagueSettingsTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)