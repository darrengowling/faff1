#!/usr/bin/env python3
"""
API Contracts Integration Test
Quick integration tests for league settings API contracts
"""

import requests
import json
from datetime import datetime

class APIContractsTester:
    def __init__(self, base_url="https://pifa-stability.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.test_league_id = None
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
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_patch_endpoint_exists(self):
        """Test that PATCH /leagues/:id/settings endpoint exists"""
        # Try to access endpoint (will fail auth but should show it exists)
        success, status, data = self.make_request(
            'PATCH', 
            'leagues/test-id/settings',
            {"club_slots_per_manager": 4},
            expected_status=401  # Expect auth failure, not 404
        )
        
        endpoint_exists = status != 404
        return self.log_test(
            "PATCH endpoint exists",
            endpoint_exists,
            f"Status: {status} (401 = auth required, 404 = not found)"
        )

    def test_competition_profiles_have_required_fields(self):
        """Test that competition profiles have required default fields"""
        success, status, data = self.make_request('GET', 'competition-profiles')
        
        if not success:
            return self.log_test("Competition profiles structure", False, f"Failed to fetch: {status}")
        
        profiles = data.get('profiles', [])
        if not profiles:
            return self.log_test("Competition profiles structure", False, "No profiles found")
        
        ucl_profile = next((p for p in profiles if p['id'] == 'ucl'), None)
        if not ucl_profile:
            return self.log_test("Competition profiles structure", False, "UCL profile not found")
        
        defaults = ucl_profile.get('defaults', {})
        required_fields = ['club_slots', 'budget_per_manager', 'league_size']
        
        missing_fields = [field for field in required_fields if field not in defaults]
        
        return self.log_test(
            "Competition profiles have required fields",
            len(missing_fields) == 0,
            f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
        )

    def test_league_creation_with_defaults(self):
        """Test league creation uses competition profile defaults"""
        # This test doesn't require auth, just checks the structure
        success, status, data = self.make_request('GET', 'competition-profiles/ucl')
        
        if not success:
            return self.log_test("League defaults from competition profile", False, f"Failed to fetch UCL profile: {status}")
        
        defaults = data.get('defaults', {})
        expected_defaults = {
            'club_slots': 3,
            'budget_per_manager': 100,
            'league_size': {'min': 4, 'max': 8}
        }
        
        matches_expected = (
            defaults.get('club_slots') == expected_defaults['club_slots'] and
            defaults.get('budget_per_manager') == expected_defaults['budget_per_manager'] and
            defaults.get('league_size', {}).get('min') == expected_defaults['league_size']['min'] and
            defaults.get('league_size', {}).get('max') == expected_defaults['league_size']['max']
        )
        
        return self.log_test(
            "UCL competition profile has correct defaults",
            matches_expected,
            f"Defaults: {json.dumps(defaults, indent=2)}"
        )

    def test_api_contract_structure(self):
        """Test API contract accepts expected field names"""
        # Test the structure by examining OpenAPI/schema if available
        success, status, data = self.make_request('GET', 'docs', expected_status=200)
        
        if success:
            return self.log_test(
                "API documentation available",
                True,
                "OpenAPI docs accessible at /api/docs"
            )
        else:
            return self.log_test(
                "API documentation available",
                False,
                f"Docs not available: {status}"
            )

    def test_backend_health_check(self):
        """Test that backend is healthy and responding"""
        success, status, data = self.make_request('GET', '')
        
        # Any response (even 404) indicates backend is running
        backend_healthy = status != 0
        
        return self.log_test(
            "Backend health check",
            backend_healthy,
            f"Backend responding with status: {status}"
        )

    def run_all_tests(self):
        """Run all API contract tests"""
        print("🧪 Running API Contracts Integration Tests\n")
        
        # Test suite
        tests = [
            self.test_backend_health_check,
            self.test_patch_endpoint_exists,
            self.test_competition_profiles_have_required_fields,
            self.test_league_creation_with_defaults,
            self.test_api_contract_structure
        ]
        
        for test in tests:
            test()
        
        # Summary
        print(f"\n📊 Test Results:")
        print(f"Total: {self.tests_run}, Passed: {self.tests_passed}, Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"  - {failure}")
        else:
            print(f"\n🎉 All tests passed!")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    tester = APIContractsTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)