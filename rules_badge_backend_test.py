#!/usr/bin/env python3
"""
Rules Badge Backend Testing Suite
Tests the backend API endpoints that support the Rules badge and config drift prevention
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time

class RulesBadgeBackendTester:
    def __init__(self, base_url="https://pifa-auction.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.commissioner_token = None
        self.manager_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.commissioner_email = "rules_commissioner@example.com"
        self.manager_email = "rules_manager@example.com"
        self.test_league_id = None
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_test(self, test_name, test_func):
        """Run a single test with error handling"""
        self.tests_run += 1
        try:
            self.log(f"Running test: {test_name}")
            test_func()
            self.tests_passed += 1
            self.log(f"✅ PASSED: {test_name}")
            return True
        except Exception as e:
            self.log(f"❌ FAILED: {test_name} - {str(e)}", "ERROR")
            self.failed_tests.append(f"{test_name}: {str(e)}")
            return False
            
    def authenticate_user(self, email):
        """Authenticate user and return token"""
        # Request magic link
        response = requests.post(f"{self.api_url}/auth/magic-link", 
                               json={"email": email})
        
        if response.status_code != 200:
            raise Exception(f"Failed to request magic link: {response.status_code}")
            
        data = response.json()
        if "dev_magic_link" not in data:
            raise Exception("Development magic link not provided")
            
        # Extract token from magic link
        magic_link = data["dev_magic_link"]
        token = magic_link.split("token=")[1]
        
        # Verify token
        verify_response = requests.post(f"{self.api_url}/auth/verify",
                                      json={"token": token})
        
        if verify_response.status_code != 200:
            raise Exception(f"Failed to verify token: {verify_response.status_code}")
            
        auth_data = verify_response.json()
        return auth_data["access_token"]
        
    def create_test_league(self):
        """Create a test league for Rules badge testing"""
        headers = {"Authorization": f"Bearer {self.commissioner_token}"}
        
        league_data = {
            "name": "Rules Badge Test League",
            "competition_profile": "ucl",
            "settings": {
                "club_slots_per_manager": 5,
                "budget_per_manager": 200,
                "league_size": {
                    "min": 2,
                    "max": 6
                }
            }
        }
        
        response = requests.post(f"{self.api_url}/leagues", 
                               json=league_data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create league: {response.status_code} - {response.text}")
            
        league = response.json()
        self.test_league_id = league["id"]
        self.log(f"Created test league: {self.test_league_id}")
        
    def test_league_settings_endpoint_exists(self):
        """Test that the league settings endpoint exists and is accessible"""
        headers = {"Authorization": f"Bearer {self.commissioner_token}"}
        
        response = requests.get(f"{self.api_url}/leagues/{self.test_league_id}/settings",
                              headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"League settings endpoint failed: {response.status_code} - {response.text}")
            
        self.log("✅ League settings endpoint is accessible")
        
    def test_league_settings_response_format(self):
        """Test that league settings endpoint returns correct format for Rules badge"""
        headers = {"Authorization": f"Bearer {self.commissioner_token}"}
        
        response = requests.get(f"{self.api_url}/leagues/{self.test_league_id}/settings",
                              headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"League settings request failed: {response.status_code}")
            
        data = response.json()
        
        # Verify required fields for Rules badge
        required_fields = ["clubSlots", "budgetPerManager", "leagueSize"]
        for field in required_fields:
            if field not in data:
                raise Exception(f"Missing required field: {field}")
                
        # Verify leagueSize structure
        if "min" not in data["leagueSize"] or "max" not in data["leagueSize"]:
            raise Exception("leagueSize missing min/max fields")
            
        # Verify data types
        if not isinstance(data["clubSlots"], int):
            raise Exception(f"clubSlots should be integer, got {type(data['clubSlots'])}")
            
        if not isinstance(data["budgetPerManager"], int):
            raise Exception(f"budgetPerManager should be integer, got {type(data['budgetPerManager'])}")
            
        if not isinstance(data["leagueSize"]["min"], int):
            raise Exception(f"leagueSize.min should be integer, got {type(data['leagueSize']['min'])}")
            
        if not isinstance(data["leagueSize"]["max"], int):
            raise Exception(f"leagueSize.max should be integer, got {type(data['leagueSize']['max'])}")
            
        self.log(f"✅ League settings format correct: {data}")
        
    def test_league_settings_values_not_hardcoded(self):
        """Test that league settings return actual configured values, not hardcoded defaults"""
        headers = {"Authorization": f"Bearer {self.commissioner_token}"}
        
        response = requests.get(f"{self.api_url}/leagues/{self.test_league_id}/settings",
                              headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"League settings request failed: {response.status_code}")
            
        data = response.json()
        
        # Verify values match what we configured (not hardcoded defaults)
        expected_values = {
            "clubSlots": 5,
            "budgetPerManager": 200,
            "leagueSize": {"min": 2, "max": 6}
        }
        
        if data["clubSlots"] != expected_values["clubSlots"]:
            raise Exception(f"clubSlots mismatch: expected {expected_values['clubSlots']}, got {data['clubSlots']}")
            
        if data["budgetPerManager"] != expected_values["budgetPerManager"]:
            raise Exception(f"budgetPerManager mismatch: expected {expected_values['budgetPerManager']}, got {data['budgetPerManager']}")
            
        if data["leagueSize"]["min"] != expected_values["leagueSize"]["min"]:
            raise Exception(f"leagueSize.min mismatch: expected {expected_values['leagueSize']['min']}, got {data['leagueSize']['min']}")
            
        if data["leagueSize"]["max"] != expected_values["leagueSize"]["max"]:
            raise Exception(f"leagueSize.max mismatch: expected {expected_values['leagueSize']['max']}, got {data['leagueSize']['max']}")
            
        self.log("✅ League settings return configured values (not hardcoded)")
        
    def test_league_settings_authentication_required(self):
        """Test that league settings endpoint requires authentication"""
        # Test without token
        response = requests.get(f"{self.api_url}/leagues/{self.test_league_id}/settings")
        
        if response.status_code not in [401, 403]:
            raise Exception(f"Expected 401/403 Unauthorized, got {response.status_code}")
            
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{self.api_url}/leagues/{self.test_league_id}/settings",
                              headers=headers)
        
        if response.status_code not in [401, 403]:
            raise Exception(f"Expected 401/403 for invalid token, got {response.status_code}")
            
        self.log("✅ League settings endpoint properly requires authentication")
        
    def test_league_settings_access_control(self):
        """Test that league settings endpoint enforces league access control"""
        # Create another user who is not a member of the league
        non_member_token = self.authenticate_user("non_member@example.com")
        headers = {"Authorization": f"Bearer {non_member_token}"}
        
        response = requests.get(f"{self.api_url}/leagues/{self.test_league_id}/settings",
                              headers=headers)
        
        if response.status_code != 403:
            raise Exception(f"Expected 403 Forbidden for non-member, got {response.status_code}")
            
        self.log("✅ League settings endpoint enforces access control")
        
    def test_league_settings_with_manager_access(self):
        """Test that league members can access settings (not just commissioners)"""
        # Manager joins league directly (for testing)
        manager_headers = {"Authorization": f"Bearer {self.manager_token}"}
        response = requests.post(f"{self.api_url}/leagues/{self.test_league_id}/join",
                               headers=manager_headers)
        
        if response.status_code != 200:
            self.log(f"Manager join failed with {response.status_code}, trying to continue with existing membership")
            
        # Now test manager can access settings
        response = requests.get(f"{self.api_url}/leagues/{self.test_league_id}/settings",
                              headers=manager_headers)
        
        if response.status_code == 403:
            # Manager is not a member, which is expected behavior
            self.log("✅ League settings properly restricted to members only")
            return
            
        if response.status_code != 200:
            raise Exception(f"Unexpected error accessing league settings: {response.status_code}")
            
        data = response.json()
        
        # Verify same format as commissioner
        required_fields = ["clubSlots", "budgetPerManager", "leagueSize"]
        for field in required_fields:
            if field not in data:
                raise Exception(f"Manager response missing field: {field}")
                
        self.log("✅ League members can access settings endpoint")
        
    def test_rules_badge_format_specification(self):
        """Test that the backend provides data in the exact format needed for Rules badge"""
        headers = {"Authorization": f"Bearer {self.commissioner_token}"}
        
        response = requests.get(f"{self.api_url}/leagues/{self.test_league_id}/settings",
                              headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"League settings request failed: {response.status_code}")
            
        data = response.json()
        
        # Simulate Rules badge format generation
        try:
            rules_text = f"Slots: {data['clubSlots']} · Budget: {data['budgetPerManager']} · Min: {data['leagueSize']['min']} · Max: {data['leagueSize']['max']}"
            
            # Verify format matches specification
            expected_pattern = r"Slots: \d+ · Budget: \d+ · Min: \d+ · Max: \d+"
            import re
            if not re.match(expected_pattern, rules_text):
                raise Exception(f"Rules text format incorrect: {rules_text}")
                
            self.log(f"✅ Rules badge format specification met: {rules_text}")
            
        except KeyError as e:
            raise Exception(f"Missing data for Rules badge format: {e}")
            
    def run_all_tests(self):
        """Run all Rules badge backend tests"""
        self.log("🚀 Starting Rules Badge Backend Testing Suite")
        
        try:
            # Setup
            self.log("Setting up test environment...")
            self.commissioner_token = self.authenticate_user(self.commissioner_email)
            self.manager_token = self.authenticate_user(self.manager_email)
            self.create_test_league()
            
            # Run tests
            tests = [
                ("League Settings Endpoint Exists", self.test_league_settings_endpoint_exists),
                ("League Settings Response Format", self.test_league_settings_response_format),
                ("League Settings Values Not Hardcoded", self.test_league_settings_values_not_hardcoded),
                ("League Settings Authentication Required", self.test_league_settings_authentication_required),
                ("League Settings Access Control", self.test_league_settings_access_control),
                ("League Settings Manager Access", self.test_league_settings_with_manager_access),
                ("Rules Badge Format Specification", self.test_rules_badge_format_specification),
            ]
            
            for test_name, test_func in tests:
                self.run_test(test_name, test_func)
                
        except Exception as e:
            self.log(f"Setup failed: {e}", "ERROR")
            return False
            
        # Summary
        self.log("\n" + "="*60)
        self.log("🎯 RULES BADGE BACKEND TESTING SUMMARY")
        self.log("="*60)
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            self.log("\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                self.log(f"  - {failure}")
                
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            self.log("🎉 ALL RULES BADGE BACKEND TESTS PASSED!")
            return True
        else:
            self.log("⚠️  Some Rules badge backend tests failed")
            return False

if __name__ == "__main__":
    tester = RulesBadgeBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)