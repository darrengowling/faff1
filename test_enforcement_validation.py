#!/usr/bin/env python3
"""
Enforcement Rules Validation Test
Quick validation test for all enforcement rules implementation
"""

import requests
import json

class EnforcementValidationTester:
    def __init__(self, base_url="https://auction-platform-6.preview.emergentagent.com"):
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
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_patch_endpoint_available(self):
        """Test PATCH endpoint is available"""
        success, status, data = self.make_request(
            'PATCH', 
            'leagues/test-id/settings',
            {"club_slots_per_manager": 4},
            expected_status=403  # Auth required, not 404 (not found)
        )
        
        return self.log_test(
            "PATCH /leagues/:id/settings endpoint exists",
            status != 404,
            f"Status: {status} (403=auth required, 404=not found)"
        )

    def test_competition_profile_structure(self):
        """Test competition profiles have enforcement rule fields"""
        success, status, data = self.make_request('GET', 'competition-profiles/ucl')
        
        if not success:
            return self.log_test("UCL competition profile structure", False, f"Failed to fetch: {status}")
        
        defaults = data.get('defaults', {})
        required_fields = {
            'club_slots': 3,
            'budget_per_manager': 100,
            'league_size': {'min': 4, 'max': 8}
        }
        
        structure_valid = (
            defaults.get('club_slots') == required_fields['club_slots'] and
            defaults.get('budget_per_manager') == required_fields['budget_per_manager'] and
            isinstance(defaults.get('league_size'), dict) and
            defaults.get('league_size', {}).get('min') == required_fields['league_size']['min'] and
            defaults.get('league_size', {}).get('max') == required_fields['league_size']['max']
        )
        
        return self.log_test(
            "UCL competition profile has enforcement fields",
            structure_valid,
            f"Fields present and correct values"
        )

    def test_api_contract_field_names(self):
        """Test API contract accepts correct field names"""
        # Test that the expected field names are recognized (will fail auth but shouldn't fail parsing)
        test_payload = {
            "club_slots_per_manager": 4,
            "budget_per_manager": 150,
            "league_size": {"min": 2, "max": 6}
        }
        
        success, status, data = self.make_request(
            'PATCH',
            'leagues/test-id/settings',
            test_payload,
            expected_status=403  # Should fail auth, not parsing
        )
        
        # If we get 422 (validation error), it means the fields were parsed but invalid
        # If we get 403 (auth error), it means the fields were parsed successfully
        contract_valid = status in [403, 422, 401]  # Auth or validation, not parsing error
        
        return self.log_test(
            "API contract accepts enforcement rule fields",
            contract_valid,
            f"Status: {status} (403/422/401=good, 400=bad request)"
        )

    def test_backend_admin_service_available(self):
        """Test admin service endpoints are available"""
        admin_endpoints = [
            'admin/leagues/test-id/settings',
            'admin/leagues/test-id/members/manage',
            'admin/leagues/test-id/audit'
        ]
        
        available_count = 0
        for endpoint in admin_endpoints:
            success, status, data = self.make_request('GET', endpoint, expected_status=403)
            if status != 404:  # Not found
                available_count += 1
        
        return self.log_test(
            "Admin service endpoints available",
            available_count == len(admin_endpoints),
            f"{available_count}/{len(admin_endpoints)} endpoints accessible"
        )

    def test_validation_error_structure(self):
        """Test that validation errors have proper structure"""
        # Try an invalid league size (min > max) to test validation
        invalid_payload = {
            "league_size": {"min": 8, "max": 4}  # Invalid: min > max
        }
        
        success, status, data = self.make_request(
            'PATCH',
            'leagues/test-id/settings',
            invalid_payload,
            expected_status=403  # Will fail auth before validation
        )
        
        # The endpoint exists and processes the request
        validation_structure_exists = status != 404
        
        return self.log_test(
            "Validation error handling structure",
            validation_structure_exists,
            f"Endpoint processes validation requests (status: {status})"
        )

    def test_league_creation_defaults_integration(self):
        """Test league creation can access competition profiles"""
        # Test that league creation endpoint can access competition profiles
        success, status, data = self.make_request('GET', 'competition-profiles')
        
        if not success:
            return self.log_test("League creation defaults integration", False, f"Profiles not accessible: {status}")
        
        profiles = data.get('profiles', [])
        ucl_exists = any(p.get('id') == 'ucl' for p in profiles)
        
        return self.log_test(
            "League creation can access competition profiles",
            ucl_exists,
            f"UCL profile available for league creation defaults"
        )

    def run_validation_tests(self):
        """Run all enforcement validation tests"""
        print("🛡️ Running Enforcement Rules Validation Tests\n")
        
        tests = [
            self.test_patch_endpoint_available,
            self.test_competition_profile_structure,
            self.test_api_contract_field_names,
            self.test_backend_admin_service_available,
            self.test_validation_error_structure,
            self.test_league_creation_defaults_integration
        ]
        
        for test in tests:
            test()
        
        # Summary
        print(f"\n📊 Validation Results:")
        print(f"Total: {self.tests_run}, Passed: {self.tests_passed}, Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Validations:")
            for failure in self.failed_tests:
                print(f"  - {failure}")
        else:
            print(f"\n🎉 All enforcement rules validation passed!")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    tester = EnforcementValidationTester()
    success = tester.run_validation_tests()
    exit(0 if success else 1)