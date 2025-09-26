#!/usr/bin/env python3
"""
Competition Profile Integration Test
Focused testing for competition profile integration in league creation
"""

import requests
import json
from datetime import datetime

class CompetitionProfileTester:
    def __init__(self):
        self.base_url = "https://friends-of-pifa.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ODc4MzY3Zi05YmQzLTQ2NGQtODQ2YS1jZTQyYjYzZGI1MWYiLCJleHAiOjE3NTg2NzkyNjB9.ebAyqnx0FJ_sknhqY2sIB7FgD3tXHj6ZjSBTNfulBxY"
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
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_competition_profiles_endpoint(self):
        """Test GET /api/competition-profiles endpoint"""
        success, status, data = self.make_request('GET', 'competition-profiles')
        
        valid_response = (
            success and
            isinstance(data, dict) and
            'profiles' in data and
            isinstance(data['profiles'], list)
        )
        
        return self.log_test(
            "Competition Profiles Endpoint",
            valid_response,
            f"Status: {status}, Profiles: {len(data.get('profiles', []))}"
        )
    
    def test_ucl_competition_profile(self):
        """Test GET /api/competition-profiles/ucl endpoint"""
        success, status, data = self.make_request('GET', 'competition-profiles/ucl')
        
        valid_ucl_profile = (
            success and
            isinstance(data, dict) and
            'competition' in data and
            'defaults' in data and
            isinstance(data['defaults'], dict)
        )
        
        if valid_ucl_profile:
            defaults = data['defaults']
            defaults_structure_valid = (
                'budget_per_manager' in defaults and
                'club_slots' in defaults and
                'league_size' in defaults and
                'scoring_rules' in defaults
            )
            print(f"   UCL Profile defaults: {json.dumps(defaults, indent=2)}")
        else:
            defaults_structure_valid = False
        
        return self.log_test(
            "UCL Competition Profile",
            valid_ucl_profile and defaults_structure_valid,
            f"Status: {status}, Profile exists: {valid_ucl_profile}, Defaults valid: {defaults_structure_valid}"
        )
    
    def test_league_creation_without_settings(self):
        """Test league creation without explicit settings (should use competition profile defaults)"""
        league_data = {
            "name": f"Auto-Default League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
            # No settings provided - should use competition profile defaults
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            settings = data.get('settings', {})
            print(f"   League created with settings: {json.dumps(settings, indent=2)}")
            
            # Verify settings were populated from competition profile
            settings_populated = (
                settings.get('budget_per_manager') is not None and
                settings.get('club_slots_per_manager') is not None and
                settings.get('league_size') is not None and
                settings.get('scoring_rules') is not None
            )
            
            # Check if settings match expected UCL defaults
            expected_defaults = (
                settings.get('budget_per_manager') == 100 and
                settings.get('club_slots_per_manager') == 3 and
                settings.get('league_size', {}).get('min') == 4 and
                settings.get('league_size', {}).get('max') == 8
            )
            
            return self.log_test(
                "League Creation Without Settings",
                success and settings_populated and expected_defaults,
                f"Settings populated: {settings_populated}, Defaults match: {expected_defaults}"
            )
        
        return self.log_test(
            "League Creation Without Settings",
            False,
            f"Status: {status}, Response: {data}"
        )
    
    def test_league_creation_with_explicit_settings(self):
        """Test league creation with explicit settings (should override competition profile defaults)"""
        custom_settings = {
            "budget_per_manager": 150,
            "min_increment": 2,
            "club_slots_per_manager": 4,
            "anti_snipe_seconds": 45,
            "bid_timer_seconds": 90,
            "league_size": {
                "min": 3,
                "max": 6
            },
            "scoring_rules": {
                "club_goal": 2,
                "club_win": 5,
                "club_draw": 2
            }
        }
        
        league_data = {
            "name": f"Custom Settings League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": custom_settings
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            settings = data.get('settings', {})
            print(f"   League created with custom settings: {json.dumps(settings, indent=2)}")
            
            # Verify explicit settings were used (not defaults)
            explicit_settings_used = (
                settings.get('budget_per_manager') == 150 and
                settings.get('min_increment') == 2 and
                settings.get('club_slots_per_manager') == 4 and
                settings.get('anti_snipe_seconds') == 45 and
                settings.get('bid_timer_seconds') == 90 and
                settings.get('league_size', {}).get('min') == 3 and
                settings.get('league_size', {}).get('max') == 6 and
                settings.get('scoring_rules', {}).get('club_goal') == 2 and
                settings.get('scoring_rules', {}).get('club_win') == 5 and
                settings.get('scoring_rules', {}).get('club_draw') == 2
            )
            
            return self.log_test(
                "League Creation With Explicit Settings",
                success and explicit_settings_used,
                f"Explicit settings used: {explicit_settings_used}"
            )
        
        return self.log_test(
            "League Creation With Explicit Settings",
            False,
            f"Status: {status}, Response: {data}"
        )
    
    def test_backward_compatibility(self):
        """Test that explicit settings take priority over competition profile defaults"""
        # Get UCL competition profile defaults first
        success_defaults, status_defaults, defaults = self.make_request('GET', 'competition-profiles/ucl/defaults')
        
        if not success_defaults:
            return self.log_test("Backward Compatibility", False, f"Failed to get defaults: {status_defaults}")
        
        print(f"   UCL defaults: {json.dumps(defaults, indent=2)}")
        
        # Create league with explicit settings that differ from defaults
        different_settings = {
            "budget_per_manager": defaults.get('budget_per_manager', 100) + 50,  # Different from default
            "club_slots_per_manager": defaults.get('club_slots_per_manager', 3) + 1,  # Different from default
            "league_size": {
                "min": max(2, defaults.get('league_size', {}).get('min', 4) - 1),  # Different from default
                "max": defaults.get('league_size', {}).get('max', 8) - 1   # Different from default
            }
        }
        
        league_data = {
            "name": f"Backward Compatibility Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": different_settings
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            settings = data.get('settings', {})
            print(f"   League created with different settings: {json.dumps(settings, indent=2)}")
            
            # Verify explicit settings were used, not defaults
            explicit_settings_priority = (
                settings.get('budget_per_manager') == different_settings['budget_per_manager'] and
                settings.get('club_slots_per_manager') == different_settings['club_slots_per_manager'] and
                settings.get('league_size', {}).get('min') == different_settings['league_size']['min'] and
                settings.get('league_size', {}).get('max') == different_settings['league_size']['max']
            )
            
            return self.log_test(
                "Backward Compatibility",
                explicit_settings_priority,
                f"Explicit settings took priority: {explicit_settings_priority}"
            )
        
        return self.log_test(
            "Backward Compatibility",
            False,
            f"Status: {status}, Response: {data}"
        )

    def run_tests(self):
        """Run all competition profile integration tests"""
        print("🏆 Competition Profile Integration Tests")
        print("=" * 60)
        
        self.test_competition_profiles_endpoint()
        self.test_ucl_competition_profile()
        self.test_league_creation_without_settings()
        self.test_league_creation_with_explicit_settings()
        self.test_backward_compatibility()
        
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All competition profile integration tests passed!")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed")
            return 1

if __name__ == "__main__":
    tester = CompetitionProfileTester()
    exit_code = tester.run_tests()
    exit(exit_code)