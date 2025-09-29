#!/usr/bin/env python3
"""
Rules Badge Final Testing Suite
Comprehensive test of Rules badge backend integration and config drift prevention
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time

class RulesBadgeFinalTester:
    def __init__(self, base_url="https://e2e-stability.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
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
        response = requests.post(f"{self.api_url}/auth/magic-link", 
                               json={"email": email})
        
        if response.status_code != 200:
            raise Exception(f"Failed to request magic link: {response.status_code}")
            
        data = response.json()
        if "dev_magic_link" not in data:
            raise Exception("Development magic link not provided")
            
        magic_link = data["dev_magic_link"]
        token = magic_link.split("token=")[1]
        
        verify_response = requests.post(f"{self.api_url}/auth/verify",
                                      json={"token": token})
        
        if verify_response.status_code != 200:
            raise Exception(f"Failed to verify token: {verify_response.status_code}")
            
        auth_data = verify_response.json()
        return auth_data["access_token"]
        
    def test_rules_badge_backend_api_comprehensive(self):
        """Comprehensive test of Rules badge backend API functionality"""
        token = self.authenticate_user("comprehensive_test@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test league with specific settings
        league_data = {
            "name": "Rules Badge Comprehensive Test",
            "competition_profile": "ucl",
            "settings": {
                "club_slots_per_manager": 6,
                "budget_per_manager": 175,
                "league_size": {"min": 2, "max": 8}
            }
        }
        
        response = requests.post(f"{self.api_url}/leagues", 
                               json=league_data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create test league: {response.status_code} - {response.text}")
            
        league = response.json()
        league_id = league["id"]
        
        # Test 1: Settings endpoint accessibility
        settings_response = requests.get(f"{self.api_url}/leagues/{league_id}/settings",
                                       headers=headers)
        
        if settings_response.status_code != 200:
            raise Exception(f"Settings endpoint failed: {settings_response.status_code}")
            
        settings = settings_response.json()
        
        # Test 2: Verify response structure for Rules badge
        required_fields = ["clubSlots", "budgetPerManager", "leagueSize"]
        for field in required_fields:
            if field not in settings:
                raise Exception(f"Missing required field: {field}")
                
        if "min" not in settings["leagueSize"] or "max" not in settings["leagueSize"]:
            raise Exception("leagueSize missing min/max fields")
            
        # Test 3: Verify data types
        if not isinstance(settings["clubSlots"], int):
            raise Exception(f"clubSlots should be int, got {type(settings['clubSlots'])}")
        if not isinstance(settings["budgetPerManager"], int):
            raise Exception(f"budgetPerManager should be int, got {type(settings['budgetPerManager'])}")
        if not isinstance(settings["leagueSize"]["min"], int):
            raise Exception(f"leagueSize.min should be int, got {type(settings['leagueSize']['min'])}")
        if not isinstance(settings["leagueSize"]["max"], int):
            raise Exception(f"leagueSize.max should be int, got {type(settings['leagueSize']['max'])}")
            
        # Test 4: Verify values match configuration (no hardcoding)
        if settings["clubSlots"] != 6:
            raise Exception(f"clubSlots hardcoded: expected 6, got {settings['clubSlots']}")
        if settings["budgetPerManager"] != 175:
            raise Exception(f"budgetPerManager hardcoded: expected 175, got {settings['budgetPerManager']}")
        if settings["leagueSize"]["min"] != 2:
            raise Exception(f"leagueSize.min hardcoded: expected 2, got {settings['leagueSize']['min']}")
        if settings["leagueSize"]["max"] != 8:
            raise Exception(f"leagueSize.max hardcoded: expected 8, got {settings['leagueSize']['max']}")
            
        # Test 5: Generate Rules badge format
        rules_text = f"Slots: {settings['clubSlots']} · Budget: {settings['budgetPerManager']} · Min: {settings['leagueSize']['min']} · Max: {settings['leagueSize']['max']}"
        expected_text = "Slots: 6 · Budget: 175 · Min: 2 · Max: 8"
        
        if rules_text != expected_text:
            raise Exception(f"Rules badge format incorrect: expected '{expected_text}', got '{rules_text}'")
            
        # Test 6: Generate tooltip format
        tooltip_data = {
            "clubSlots": settings['clubSlots'],
            "budgetPerManager": settings['budgetPerManager'],
            "minManagers": settings['leagueSize']['min'],
            "maxManagers": settings['leagueSize']['max']
        }
        
        self.log(f"✅ League settings verified: {settings}")
        self.log(f"✅ Rules badge text: {rules_text}")
        self.log(f"✅ Tooltip data: {tooltip_data}")
        
    def test_existing_leagues_rules_badge_integration(self):
        """Test Rules badge integration with existing leagues in the system"""
        token = self.authenticate_user("existing_leagues_test@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all leagues
        response = requests.get(f"{self.api_url}/leagues", headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get leagues: {response.status_code}")
            
        leagues = response.json()
        
        tested_leagues = 0
        rules_badge_data = []
        
        for league in leagues:
            league_id = league["id"]
            league_name = league["name"]
            
            # Try to get settings for this league
            settings_response = requests.get(f"{self.api_url}/leagues/{league_id}/settings",
                                           headers=headers)
            
            if settings_response.status_code == 200:
                settings = settings_response.json()
                tested_leagues += 1
                
                # Generate Rules badge text
                rules_text = f"Slots: {settings['clubSlots']} · Budget: {settings['budgetPerManager']} · Min: {settings['leagueSize']['min']} · Max: {settings['leagueSize']['max']}"
                
                rules_badge_data.append({
                    "league": league_name,
                    "rules_text": rules_text,
                    "settings": settings
                })
                
                # Verify format matches specification
                import re
                pattern = r"Slots: \d+ · Budget: \d+ · Min: \d+ · Max: \d+"
                if not re.match(pattern, rules_text):
                    raise Exception(f"Rules badge format incorrect for {league_name}: {rules_text}")
                    
                self.log(f"✅ {league_name}: {rules_text}")
                
            elif settings_response.status_code == 403:
                self.log(f"ℹ️  {league_name}: Access denied (not a member)")
            else:
                self.log(f"⚠️  {league_name}: Settings error {settings_response.status_code}")
        
        if tested_leagues == 0:
            raise Exception("No leagues were accessible for Rules badge testing")
            
        # Verify diversity in settings (no universal hardcoding)
        unique_club_slots = set(data["settings"]["clubSlots"] for data in rules_badge_data)
        unique_budgets = set(data["settings"]["budgetPerManager"] for data in rules_badge_data)
        
        if len(unique_club_slots) > 1 or len(unique_budgets) > 1:
            self.log("✅ Settings diversity detected - no universal hardcoding")
        else:
            self.log("ℹ️  All tested leagues have same settings - this may be intentional")
            
        self.log(f"✅ Rules badge integration tested on {tested_leagues} leagues")
        
    def test_rules_badge_format_specification_compliance(self):
        """Test that Rules badge format exactly matches the specification"""
        token = self.authenticate_user("format_spec_test@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a league with known values
        league_data = {
            "name": "Format Specification Test",
            "competition_profile": "ucl",
            "settings": {
                "club_slots_per_manager": 5,
                "budget_per_manager": 200,
                "league_size": {"min": 4, "max": 8}
            }
        }
        
        response = requests.post(f"{self.api_url}/leagues", 
                               json=league_data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create test league: {response.status_code}")
            
        league = response.json()
        league_id = league["id"]
        
        # Get settings
        settings_response = requests.get(f"{self.api_url}/leagues/{league_id}/settings",
                                       headers=headers)
        
        if settings_response.status_code != 200:
            raise Exception(f"Failed to get settings: {settings_response.status_code}")
            
        settings = settings_response.json()
        
        # Test exact format specification: "Slots: {clubSlots} · Budget: {budget} · Min: {min} · Max: {max}"
        rules_text = f"Slots: {settings['clubSlots']} · Budget: {settings['budgetPerManager']} · Min: {settings['leagueSize']['min']} · Max: {settings['leagueSize']['max']}"
        expected_format = "Slots: 5 · Budget: 200 · Min: 4 · Max: 8"
        
        if rules_text != expected_format:
            raise Exception(f"Format specification mismatch: expected '{expected_format}', got '{rules_text}'")
            
        # Test tooltip format specification
        tooltip_lines = [
            f"• Club Slots per Manager: {settings['clubSlots']}",
            f"• Budget per Manager: ${settings['budgetPerManager']}M",
            f"• Min Managers: {settings['leagueSize']['min']}",
            f"• Max Managers: {settings['leagueSize']['max']}"
        ]
        
        expected_tooltip_content = [
            "• Club Slots per Manager: 5",
            "• Budget per Manager: $200M",
            "• Min Managers: 4",
            "• Max Managers: 8"
        ]
        
        if tooltip_lines != expected_tooltip_content:
            raise Exception(f"Tooltip format mismatch: expected {expected_tooltip_content}, got {tooltip_lines}")
            
        self.log(f"✅ Rules badge format specification compliance verified")
        self.log(f"  Badge text: {rules_text}")
        self.log(f"  Tooltip lines: {tooltip_lines}")
        
    def test_config_drift_prevention_verification(self):
        """Verify that config drift prevention is working - no hardcoded values"""
        token = self.authenticate_user("config_drift_test@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with extreme values to ensure no hardcoding
        test_league_data = {
            "name": "Config Drift Prevention Test",
            "competition_profile": "custom",
            "settings": {
                "club_slots_per_manager": 1,  # Minimum possible
                "budget_per_manager": 25,     # Low budget
                "league_size": {"min": 2, "max": 3}  # Small league
            }
        }
        
        response = requests.post(f"{self.api_url}/leagues", 
                               json=test_league_data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create config drift test league: {response.status_code}")
            
        league = response.json()
        league_id = league["id"]
        
        # Verify settings endpoint returns configured values, not defaults
        settings_response = requests.get(f"{self.api_url}/leagues/{league_id}/settings",
                                       headers=headers)
        
        if settings_response.status_code != 200:
            raise Exception(f"Failed to get settings: {settings_response.status_code}")
            
        settings = settings_response.json()
        
        # Verify no hardcoded defaults
        if settings["clubSlots"] != 1:
            raise Exception(f"clubSlots hardcoded: expected 1, got {settings['clubSlots']}")
        if settings["budgetPerManager"] != 25:
            raise Exception(f"budgetPerManager hardcoded: expected 25, got {settings['budgetPerManager']}")
        if settings["leagueSize"]["min"] != 2:
            raise Exception(f"leagueSize.min hardcoded: expected 2, got {settings['leagueSize']['min']}")
        if settings["leagueSize"]["max"] != 3:
            raise Exception(f"leagueSize.max hardcoded: expected 3, got {settings['leagueSize']['max']}")
            
        # Generate Rules badge with extreme values
        rules_text = f"Slots: {settings['clubSlots']} · Budget: {settings['budgetPerManager']} · Min: {settings['leagueSize']['min']} · Max: {settings['leagueSize']['max']}"
        expected_text = "Slots: 1 · Budget: 25 · Min: 2 · Max: 3"
        
        if rules_text != expected_text:
            raise Exception(f"Config drift detected: expected '{expected_text}', got '{rules_text}'")
            
        self.log(f"✅ Config drift prevention verified with extreme values: {rules_text}")
        
    def run_all_tests(self):
        """Run all Rules badge final tests"""
        self.log("🚀 Starting Rules Badge Final Testing Suite")
        self.log("Testing Rules badge backend integration and config drift prevention")
        
        tests = [
            ("Rules Badge Backend API Comprehensive", self.test_rules_badge_backend_api_comprehensive),
            ("Existing Leagues Rules Badge Integration", self.test_existing_leagues_rules_badge_integration),
            ("Rules Badge Format Specification Compliance", self.test_rules_badge_format_specification_compliance),
            ("Config Drift Prevention Verification", self.test_config_drift_prevention_verification),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            
        # Summary
        self.log("\n" + "="*80)
        self.log("🎯 RULES BADGE FINAL TESTING SUMMARY")
        self.log("="*80)
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
            self.log("🎉 ALL RULES BADGE TESTS PASSED!")
            self.log("✅ Rules badge backend integration working correctly")
            self.log("✅ Config drift prevention implemented successfully")
            self.log("✅ Format specification compliance verified")
            return True
        else:
            self.log("⚠️  Some Rules badge tests failed")
            return False

if __name__ == "__main__":
    tester = RulesBadgeFinalTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)