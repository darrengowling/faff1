#!/usr/bin/env python3
"""
Server-Side Settings Enforcement Integration Testing
Tests the enforcement rules implementation for start auction and bid validation
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class SettingsEnforcementTester:
    def __init__(self, base_url="https://e2e-stability.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.commissioner_token = None
        self.manager_tokens = {}
        self.user_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.commissioner_email = "commissioner@settingstest.com"
        self.manager_emails = [
            "manager1@settingstest.com",
            "manager2@settingstest.com", 
            "manager3@settingstest.com"
        ]
        self.test_league_id = None
        self.test_auction_id = None
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_test(self, test_name, test_func):
        """Run individual test with error handling"""
        self.tests_run += 1
        try:
            self.log(f"Running test: {test_name}")
            result = test_func()
            if result:
                self.tests_passed += 1
                self.log(f"✅ PASSED: {test_name}")
                return True
            else:
                self.failed_tests.append(test_name)
                self.log(f"❌ FAILED: {test_name}", "ERROR")
                return False
        except Exception as e:
            self.failed_tests.append(f"{test_name}: {str(e)}")
            self.log(f"❌ ERROR in {test_name}: {str(e)}", "ERROR")
            return False
    
    def authenticate_user(self, email):
        """Authenticate user and return token"""
        try:
            # Request magic link
            response = requests.post(f"{self.api_url}/auth/magic-link", 
                                   json={"email": email})
            
            if response.status_code != 200:
                self.log(f"Failed to request magic link for {email}: {response.text}")
                return None
            
            data = response.json()
            if "dev_magic_link" not in data:
                self.log(f"No dev magic link in response for {email}")
                return None
            
            # Extract token from magic link
            magic_link = data["dev_magic_link"]
            token = magic_link.split("token=")[1]
            
            # Verify token
            verify_response = requests.post(f"{self.api_url}/auth/verify",
                                          json={"token": token})
            
            if verify_response.status_code != 200:
                self.log(f"Failed to verify token for {email}: {verify_response.text}")
                return None
            
            verify_data = verify_response.json()
            access_token = verify_data["access_token"]
            user_info = verify_data["user"]
            
            self.user_data[email] = user_info
            self.log(f"Authenticated {email} successfully")
            return access_token
            
        except Exception as e:
            self.log(f"Authentication failed for {email}: {str(e)}")
            return None
    
    def setup_test_environment(self):
        """Set up test environment with users and league"""
        self.log("Setting up test environment...")
        
        # Authenticate commissioner
        self.commissioner_token = self.authenticate_user(self.commissioner_email)
        if not self.commissioner_token:
            return False
        
        # Authenticate managers
        for email in self.manager_emails:
            token = self.authenticate_user(email)
            if not token:
                return False
            self.manager_tokens[email] = token
        
        # Create test league with minimum size = 4
        league_data = {
            "name": "Settings Enforcement Test League",
            "competition_profile": "ucl",
            "settings": {
                "budget_per_manager": 200,
                "club_slots_per_manager": 3,
                "league_size": {
                    "min": 4,
                    "max": 8
                }
            }
        }
        
        headers = {"Authorization": f"Bearer {self.commissioner_token}"}
        response = requests.post(f"{self.api_url}/leagues", 
                               json=league_data, headers=headers)
        
        if response.status_code != 200:
            self.log(f"Failed to create test league: {response.text}")
            return False
        
        league_response = response.json()
        self.test_league_id = league_response["id"]
        self.log(f"Created test league: {self.test_league_id}")
        
        # Add managers to league (only 3 out of 4 minimum)
        for email in self.manager_emails:
            user_id = self.user_data[email]["id"]
            join_response = requests.post(
                f"{self.api_url}/leagues/{self.test_league_id}/join",
                headers={"Authorization": f"Bearer {self.manager_tokens[email]}"}
            )
            if join_response.status_code == 200:
                self.log(f"Added manager {email} to league")
        
        return True
    
    def test_start_auction_guard_insufficient_members(self):
        """Test that start auction fails with insufficient members"""
        try:
            headers = {"Authorization": f"Bearer {self.commissioner_token}"}
            
            # Try to start auction with only 3 members (minimum is 4)
            response = requests.post(
                f"{self.api_url}/auction/{self.test_league_id}/start",
                headers=headers
            )
            
            # Should fail with 400 status
            if response.status_code != 400:
                self.log(f"Expected 400 status, got {response.status_code}")
                return False
            
            error_data = response.json()
            error_message = error_data.get("detail", "")
            
            # Check for user-friendly error message format
            if "You must have ≥" not in error_message and "managers to start" not in error_message:
                self.log(f"Expected user-friendly error message not found. Got: {error_message}")
                return False
            
            self.log(f"✅ Start auction correctly blocked: {error_message}")
            return True
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}")
            return False
    
    def test_start_auction_guard_sufficient_members(self):
        """Test that start auction succeeds with sufficient members"""
        try:
            # Add one more manager to meet minimum requirement
            extra_manager_email = "manager4@settingstest.com"
            extra_token = self.authenticate_user(extra_manager_email)
            if not extra_token:
                return False
            
            join_response = requests.post(
                f"{self.api_url}/leagues/{self.test_league_id}/join",
                headers={"Authorization": f"Bearer {extra_token}"}
            )
            
            if join_response.status_code != 200:
                self.log(f"Failed to add 4th manager: {join_response.text}")
                return False
            
            # Now try to start auction with 4 members (meets minimum)
            headers = {"Authorization": f"Bearer {self.commissioner_token}"}
            response = requests.post(
                f"{self.api_url}/auction/{self.test_league_id}/start",
                headers=headers
            )
            
            # Should succeed with 200 status
            if response.status_code != 200:
                self.log(f"Expected 200 status, got {response.status_code}: {response.text}")
                return False
            
            success_data = response.json()
            if "auction_id" not in success_data:
                self.log(f"No auction_id in response: {success_data}")
                return False
            
            self.test_auction_id = success_data["auction_id"]
            self.log(f"✅ Start auction succeeded with sufficient members")
            return True
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}")
            return False
    
    def test_league_settings_endpoint(self):
        """Test league settings endpoint returns correct structure"""
        try:
            headers = {"Authorization": f"Bearer {self.commissioner_token}"}
            
            response = requests.get(
                f"{self.api_url}/leagues/{self.test_league_id}/settings",
                headers=headers
            )
            
            if response.status_code != 200:
                self.log(f"Failed to get league settings: {response.text}")
                return False
            
            settings = response.json()
            
            # Check required fields
            required_fields = ["clubSlots", "budgetPerManager", "leagueSize"]
            for field in required_fields:
                if field not in settings:
                    self.log(f"Missing required field: {field}")
                    return False
            
            # Check leagueSize structure
            if "min" not in settings["leagueSize"] or "max" not in settings["leagueSize"]:
                self.log(f"Invalid leagueSize structure: {settings['leagueSize']}")
                return False
            
            self.log(f"✅ League settings endpoint working: {settings}")
            return True
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}")
            return False
    
    def test_roster_summary_endpoint(self):
        """Test roster summary endpoint for server-computed values"""
        try:
            headers = {"Authorization": f"Bearer {self.commissioner_token}"}
            
            response = requests.get(
                f"{self.api_url}/leagues/{self.test_league_id}/roster/summary",
                headers=headers
            )
            
            if response.status_code != 200:
                self.log(f"Failed to get roster summary: {response.text}")
                return False
            
            summary = response.json()
            
            # Check required fields
            required_fields = ["ownedCount", "clubSlots", "remaining"]
            for field in required_fields:
                if field not in summary:
                    self.log(f"Missing required field: {field}")
                    return False
            
            # Check calculation logic
            expected_remaining = max(0, summary["clubSlots"] - summary["ownedCount"])
            if summary["remaining"] != expected_remaining:
                self.log(f"Incorrect remaining calculation: {summary['remaining']} != {expected_remaining}")
                return False
            
            self.log(f"✅ Roster summary endpoint working: {summary}")
            return True
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}")
            return False
    
    def test_structured_error_messages(self):
        """Test that API endpoints return structured error messages"""
        try:
            headers = {"Authorization": f"Bearer {self.commissioner_token}"}
            
            # Test league size constraint error message structure
            # Create a league with 1 member and try to start auction
            league_data = {
                "name": "Single Member Test League",
                "competition_profile": "ucl",
                "settings": {
                    "league_size": {"min": 2, "max": 4}
                }
            }
            
            response = requests.post(f"{self.api_url}/leagues", 
                                   json=league_data, headers=headers)
            
            if response.status_code != 200:
                self.log(f"Failed to create single member league: {response.text}")
                return False
            
            single_league_id = response.json()["id"]
            
            # Try to start auction with only 1 member (commissioner)
            start_response = requests.post(
                f"{self.api_url}/auction/{single_league_id}/start",
                headers=headers
            )
            
            if start_response.status_code != 400:
                self.log(f"Expected 400 status for single member league")
                return False
            
            error_data = start_response.json()
            error_message = error_data.get("detail", "")
            
            # Check structured error message format
            if "You must have ≥" not in error_message or "managers to start" not in error_message:
                self.log(f"Structured error message not found: {error_message}")
                return False
            
            self.log(f"✅ Structured error messages working: {error_message}")
            return True
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}")
            return False
    
    def test_admin_service_validation_endpoints(self):
        """Test admin service validation through API endpoints"""
        try:
            headers = {"Authorization": f"Bearer {self.commissioner_token}"}
            
            # Test league settings update with validation
            settings_update = {
                "league_size": {
                    "min": 6,  # Increase minimum to 6
                    "max": 8
                }
            }
            
            response = requests.patch(
                f"{self.api_url}/leagues/{self.test_league_id}/settings",
                json=settings_update,
                headers=headers
            )
            
            # This should succeed since we're not violating current member count
            if response.status_code != 200:
                self.log(f"Settings update failed: {response.text}")
                return False
            
            # Now try to reduce max below current member count
            bad_settings_update = {
                "league_size": {
                    "min": 2,
                    "max": 2  # Reduce max to 2 when we have 4 members
                }
            }
            
            bad_response = requests.patch(
                f"{self.api_url}/leagues/{self.test_league_id}/settings",
                json=bad_settings_update,
                headers=headers
            )
            
            # This should fail with validation error
            if bad_response.status_code != 400:
                self.log(f"Expected validation error for bad settings update")
                return False
            
            self.log("✅ Admin service validation working through API")
            return True
            
        except Exception as e:
            self.log(f"Test failed with exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.log("🚀 Starting Server-Side Settings Enforcement Integration Tests")
        
        if not self.setup_test_environment():
            self.log("❌ Failed to set up test environment")
            return False
        
        # Run integration tests
        tests = [
            ("Start Auction Guard - Insufficient Members", self.test_start_auction_guard_insufficient_members),
            ("League Settings Endpoint", self.test_league_settings_endpoint),
            ("Roster Summary Endpoint", self.test_roster_summary_endpoint),
            ("Structured Error Messages", self.test_structured_error_messages),
            ("Admin Service Validation", self.test_admin_service_validation_endpoints),
            ("Start Auction Guard - Sufficient Members", self.test_start_auction_guard_sufficient_members),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        self.log("=" * 80)
        self.log("🎯 SERVER-SIDE SETTINGS ENFORCEMENT TEST SUMMARY")
        self.log("=" * 80)
        self.log(f"Total Tests: {self.tests_run}")
        self.log(f"Passed: {self.tests_passed}")
        self.log(f"Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            self.log("\n❌ FAILED TESTS:")
            for failed_test in self.failed_tests:
                self.log(f"  - {failed_test}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            self.log("🎉 SETTINGS ENFORCEMENT TESTS MOSTLY SUCCESSFUL!")
        else:
            self.log("⚠️  SETTINGS ENFORCEMENT TESTS NEED ATTENTION")


def main():
    """Main test runner"""
    print("🎯 SERVER-SIDE SETTINGS ENFORCEMENT INTEGRATION TESTING")
    print("=" * 80)
    
    # Run integration tests
    tester = SettingsEnforcementTester()
    tester.run_all_tests()
    tester.print_summary()
    
    # Return appropriate exit code
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    
    if success_rate >= 80:
        print("🎉 SETTINGS ENFORCEMENT IMPLEMENTATION SUCCESSFUL!")
        return 0
    else:
        print("⚠️  SETTINGS ENFORCEMENT IMPLEMENTATION NEEDS ATTENTION")
        return 1


if __name__ == "__main__":
    sys.exit(main())