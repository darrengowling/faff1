#!/usr/bin/env python3
"""
Rules Badge Integration Testing Suite
Tests the complete integration between backend API and frontend Rules badge components
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time

class RulesBadgeIntegrationTester:
    def __init__(self, base_url="https://pifa-league.preview.emergentagent.com"):
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
        
    def test_existing_leagues_rules_badge_data(self):
        """Test that existing leagues provide correct Rules badge data"""
        token = self.authenticate_user("integration_test@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get leagues
        response = requests.get(f"{self.api_url}/leagues", headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get leagues: {response.status_code}")
            
        leagues = response.json()
        if not leagues:
            self.log("No leagues found - creating test league")
            # Create a test league
            league_data = {
                "name": "Integration Test League",
                "competition_profile": "ucl",
                "settings": {
                    "club_slots_per_manager": 4,
                    "budget_per_manager": 150,
                    "league_size": {"min": 3, "max": 7}
                }
            }
            
            create_response = requests.post(f"{self.api_url}/leagues", 
                                          json=league_data, headers=headers)
            if create_response.status_code != 200:
                raise Exception(f"Failed to create test league: {create_response.status_code}")
                
            league = create_response.json()
            leagues = [league]
        
        # Test Rules badge data for each accessible league
        tested_leagues = 0
        for league in leagues[:3]:  # Test first 3 leagues
            league_id = league["id"]
            league_name = league["name"]
            
            settings_response = requests.get(f"{self.api_url}/leagues/{league_id}/settings", 
                                           headers=headers)
            
            if settings_response.status_code == 200:
                settings = settings_response.json()
                tested_leagues += 1
                
                # Verify Rules badge format can be generated
                rules_text = f"Slots: {settings['clubSlots']} · Budget: {settings['budgetPerManager']} · Min: {settings['leagueSize']['min']} · Max: {settings['leagueSize']['max']}"
                
                # Verify tooltip data structure
                tooltip_data = {
                    "clubSlots": settings['clubSlots'],
                    "budgetPerManager": settings['budgetPerManager'],
                    "minManagers": settings['leagueSize']['min'],
                    "maxManagers": settings['leagueSize']['max']
                }
                
                self.log(f"League '{league_name}': {rules_text}")
                self.log(f"  Tooltip data: {tooltip_data}")
                
                # Verify no hardcoded values (should not be exactly 3, 100, 4, 8 for all leagues)
                if (settings['clubSlots'] == 3 and settings['budgetPerManager'] == 100 and 
                    settings['leagueSize']['min'] == 4 and settings['leagueSize']['max'] == 8):
                    self.log(f"  ⚠️  League has default values - this is OK if intentional")
                else:
                    self.log(f"  ✅ League has custom values - no hardcoding detected")
                    
            elif settings_response.status_code == 403:
                self.log(f"League '{league_name}': Access denied (not a member)")
            else:
                self.log(f"League '{league_name}': Settings error {settings_response.status_code}")
        
        if tested_leagues == 0:
            raise Exception("No leagues were accessible for testing")
            
        self.log(f"✅ Successfully tested Rules badge data for {tested_leagues} leagues")
        
    def test_rules_badge_format_consistency(self):
        """Test that Rules badge format is consistent across different league configurations"""
        token = self.authenticate_user("format_test@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create leagues with different configurations
        test_configs = [
            {
                "name": "Small League Test",
                "settings": {
                    "club_slots_per_manager": 2,
                    "budget_per_manager": 50,
                    "league_size": {"min": 2, "max": 4}
                }
            },
            {
                "name": "Large League Test", 
                "settings": {
                    "club_slots_per_manager": 8,
                    "budget_per_manager": 300,
                    "league_size": {"min": 6, "max": 12}
                }
            }
        ]
        
        created_leagues = []
        
        for config in test_configs:
            league_data = {
                "name": config["name"],
                "competition_profile": "custom",
                **config
            }
            
            response = requests.post(f"{self.api_url}/leagues", 
                                   json=league_data, headers=headers)
            
            if response.status_code == 200:
                league = response.json()
                created_leagues.append(league)
                
                # Test settings endpoint
                settings_response = requests.get(f"{self.api_url}/leagues/{league['id']}/settings",
                                               headers=headers)
                
                if settings_response.status_code == 200:
                    settings = settings_response.json()
                    
                    # Generate Rules badge text
                    rules_text = f"Slots: {settings['clubSlots']} · Budget: {settings['budgetPerManager']} · Min: {settings['leagueSize']['min']} · Max: {settings['leagueSize']['max']}"
                    
                    # Verify format matches specification
                    import re
                    pattern = r"Slots: \d+ · Budget: \d+ · Min: \d+ · Max: \d+"
                    if not re.match(pattern, rules_text):
                        raise Exception(f"Rules badge format incorrect for {config['name']}: {rules_text}")
                        
                    self.log(f"✅ {config['name']}: {rules_text}")
                else:
                    raise Exception(f"Failed to get settings for {config['name']}: {settings_response.status_code}")
            else:
                self.log(f"⚠️  Failed to create {config['name']}: {response.status_code}")
        
        if not created_leagues:
            raise Exception("No test leagues were created successfully")
            
        self.log(f"✅ Rules badge format consistent across {len(created_leagues)} different configurations")
        
    def test_useLeagueSettings_hook_data_structure(self):
        """Test that the backend provides data in the exact structure expected by useLeagueSettings hook"""
        token = self.authenticate_user("hook_test@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test league
        league_data = {
            "name": "Hook Test League",
            "competition_profile": "ucl",
            "settings": {
                "club_slots_per_manager": 6,
                "budget_per_manager": 250,
                "league_size": {"min": 4, "max": 10}
            }
        }
        
        response = requests.post(f"{self.api_url}/leagues", 
                               json=league_data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create test league: {response.status_code}")
            
        league = response.json()
        league_id = league["id"]
        
        # Test settings endpoint response structure
        settings_response = requests.get(f"{self.api_url}/leagues/{league_id}/settings",
                                       headers=headers)
        
        if settings_response.status_code != 200:
            raise Exception(f"Failed to get league settings: {settings_response.status_code}")
            
        settings = settings_response.json()
        
        # Verify exact structure expected by useLeagueSettings hook
        expected_structure = {
            "clubSlots": int,
            "budgetPerManager": int,
            "leagueSize": {
                "min": int,
                "max": int
            }
        }
        
        # Check top-level fields
        for field, expected_type in expected_structure.items():
            if field not in settings:
                raise Exception(f"Missing required field: {field}")
                
            if field == "leagueSize":
                # Check nested structure
                if not isinstance(settings[field], dict):
                    raise Exception(f"leagueSize should be dict, got {type(settings[field])}")
                    
                for subfield in ["min", "max"]:
                    if subfield not in settings[field]:
                        raise Exception(f"Missing leagueSize.{subfield}")
                    if not isinstance(settings[field][subfield], int):
                        raise Exception(f"leagueSize.{subfield} should be int, got {type(settings[field][subfield])}")
            else:
                if not isinstance(settings[field], expected_type):
                    raise Exception(f"{field} should be {expected_type.__name__}, got {type(settings[field])}")
        
        # Verify the hook can generate both Rules badge formats
        # 1. Compact format (used in CompactRules component)
        compact_text = f"Slots: {settings['clubSlots']} · Budget: {settings['budgetPerManager']} · Min: {settings['leagueSize']['min']} · Max: {settings['leagueSize']['max']}"
        
        # 2. Tooltip format (used in RulesBadge component)
        tooltip_lines = [
            f"• Club Slots per Manager: {settings['clubSlots']}",
            f"• Budget per Manager: ${settings['budgetPerManager']}M",
            f"• Min Managers: {settings['leagueSize']['min']}",
            f"• Max Managers: {settings['leagueSize']['max']}"
        ]
        
        self.log(f"✅ useLeagueSettings data structure verified")
        self.log(f"  Compact format: {compact_text}")
        self.log(f"  Tooltip format: {' | '.join(tooltip_lines)}")
        
    def test_config_drift_prevention_backend(self):
        """Test that backend doesn't return hardcoded values"""
        token = self.authenticate_user("drift_test@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create leagues with different settings to ensure no hardcoding
        test_cases = [
            {"slots": 1, "budget": 25, "min": 2, "max": 3},
            {"slots": 10, "budget": 500, "min": 8, "max": 16},
            {"slots": 7, "budget": 175, "min": 5, "max": 9}
        ]
        
        for i, case in enumerate(test_cases):
            league_data = {
                "name": f"Drift Test League {i+1}",
                "competition_profile": "custom",
                "settings": {
                    "club_slots_per_manager": case["slots"],
                    "budget_per_manager": case["budget"],
                    "league_size": {"min": case["min"], "max": case["max"]}
                }
            }
            
            response = requests.post(f"{self.api_url}/leagues", 
                                   json=league_data, headers=headers)
            
            if response.status_code == 200:
                league = response.json()
                
                # Verify settings endpoint returns configured values
                settings_response = requests.get(f"{self.api_url}/leagues/{league['id']}/settings",
                                               headers=headers)
                
                if settings_response.status_code == 200:
                    settings = settings_response.json()
                    
                    # Verify no hardcoding - values should match what we configured
                    if settings["clubSlots"] != case["slots"]:
                        raise Exception(f"clubSlots hardcoded: expected {case['slots']}, got {settings['clubSlots']}")
                    if settings["budgetPerManager"] != case["budget"]:
                        raise Exception(f"budgetPerManager hardcoded: expected {case['budget']}, got {settings['budgetPerManager']}")
                    if settings["leagueSize"]["min"] != case["min"]:
                        raise Exception(f"leagueSize.min hardcoded: expected {case['min']}, got {settings['leagueSize']['min']}")
                    if settings["leagueSize"]["max"] != case["max"]:
                        raise Exception(f"leagueSize.max hardcoded: expected {case['max']}, got {settings['leagueSize']['max']}")
                        
                    self.log(f"✅ Test case {i+1}: No hardcoding detected - Slots:{case['slots']}, Budget:{case['budget']}, Min:{case['min']}, Max:{case['max']}")
                else:
                    raise Exception(f"Failed to get settings for test case {i+1}: {settings_response.status_code}")
            else:
                raise Exception(f"Failed to create league for test case {i+1}: {response.status_code}")
        
        self.log("✅ Config drift prevention verified - backend returns configured values, not hardcoded defaults")
        
    def run_all_tests(self):
        """Run all Rules badge integration tests"""
        self.log("🚀 Starting Rules Badge Integration Testing Suite")
        
        tests = [
            ("Existing Leagues Rules Badge Data", self.test_existing_leagues_rules_badge_data),
            ("Rules Badge Format Consistency", self.test_rules_badge_format_consistency),
            ("useLeagueSettings Hook Data Structure", self.test_useLeagueSettings_hook_data_structure),
            ("Config Drift Prevention Backend", self.test_config_drift_prevention_backend),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            
        # Summary
        self.log("\n" + "="*70)
        self.log("🎯 RULES BADGE INTEGRATION TESTING SUMMARY")
        self.log("="*70)
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
            self.log("🎉 ALL RULES BADGE INTEGRATION TESTS PASSED!")
            return True
        else:
            self.log("⚠️  Some Rules badge integration tests failed")
            return False

if __name__ == "__main__":
    tester = RulesBadgeIntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)