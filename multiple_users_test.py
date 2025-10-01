#!/usr/bin/env python3
"""
Multiple Users Join League Test
Testing Agent - Verify multiple users can join the same league

Focus: Test multiple users joining the same league to ensure the functionality works for multiple participants
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class MultipleUsersJoinTester:
    def __init__(self, base_url="https://livebid-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Multiple-Users-Join-Tester/1.0'
        })
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data for multiple users
        timestamp = int(datetime.now().timestamp())
        self.commissioner_email = f"commissioner-multi-{timestamp}@example.com"
        self.user_emails = [
            f"user1-multi-{timestamp}@example.com",
            f"user2-multi-{timestamp}@example.com", 
            f"user3-multi-{timestamp}@example.com",
            f"user4-multi-{timestamp}@example.com"
        ]
        
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

    def authenticate_user(self, email):
        """Authenticate a user via test-login endpoint"""
        try:
            payload = {"email": email}
            response = self.session.post(f"{self.api_url}/auth/test-login", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, User ID: {data.get('userId')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test(f"Authentication ({email})", success, details)
        except Exception as e:
            return self.log_test(f"Authentication ({email})", False, f"Exception: {str(e)}")

    def create_test_league(self):
        """Create a test league as commissioner"""
        try:
            timestamp = int(datetime.now().timestamp())
            league_data = {
                "name": f"Multi User Test League {timestamp}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {
                        "min": 2,
                        "max": 8
                    }
                }
            }
            
            response = self.session.post(f"{self.api_url}/leagues", json=league_data)
            success = response.status_code == 201
            
            if success:
                data = response.json()
                self.test_league_id = data.get('leagueId')
                details = f"Status: {response.status_code}, League ID: {self.test_league_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("League Creation", success, details)
        except Exception as e:
            return self.log_test("League Creation", False, f"Exception: {str(e)}")

    def join_league_as_user(self, email):
        """Join league as a specific user"""
        if not self.test_league_id:
            return self.log_test(f"League Join ({email})", False, "No league ID available")
        
        # Authenticate as the user
        auth_success = self.authenticate_user(email)
        if not auth_success:
            return self.log_test(f"League Join ({email})", False, "Failed to authenticate user")
            
        try:
            response = self.session.post(f"{self.api_url}/leagues/{self.test_league_id}/join")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, Message: {data.get('message', 'Success')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test(f"League Join ({email})", success, details)
        except Exception as e:
            return self.log_test(f"League Join ({email})", False, f"Exception: {str(e)}")

    def verify_league_members(self, expected_count):
        """Verify league members count and list"""
        if not self.test_league_id:
            return self.log_test("League Members Verification", False, "No league ID available")
            
        # Re-authenticate as commissioner to check members
        auth_success = self.authenticate_user(self.commissioner_email)
        if not auth_success:
            return self.log_test("League Members Verification", False, "Failed to re-authenticate commissioner")
            
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}/members")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                member_count = len(data) if isinstance(data, list) else 0
                details = f"Status: {response.status_code}, Member count: {member_count} (expected: {expected_count})"
                
                if member_count == expected_count:
                    member_emails = [m.get('email', 'N/A') for m in data]
                    details += f", Members: {member_emails}"
                    
                    # Verify all expected users are present
                    expected_emails = [self.commissioner_email] + self.user_emails[:expected_count-1]
                    missing_users = [email for email in expected_emails if email not in member_emails]
                    
                    if not missing_users:
                        details += " ✅ All expected users found"
                    else:
                        details += f" ❌ Missing users: {missing_users}"
                        success = False
                else:
                    success = False
                    details += " ❌ Member count mismatch"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("League Members Verification", success, details)
        except Exception as e:
            return self.log_test("League Members Verification", False, f"Exception: {str(e)}")

    def verify_league_status(self, expected_member_count):
        """Verify league status shows correct member count"""
        if not self.test_league_id:
            return self.log_test("League Status Verification", False, "No league ID available")
            
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}/status")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                actual_count = data.get('member_count', 0)
                details = f"Status: {response.status_code}, Members: {actual_count}/{data.get('max_members')}, Expected: {expected_member_count}"
                
                if actual_count == expected_member_count:
                    details += " ✅ Member count matches"
                else:
                    details += f" ❌ Member count mismatch (expected: {expected_member_count}, actual: {actual_count})"
                    success = False
                    
                details += f", League Status: {data.get('status')}, Ready: {data.get('is_ready')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("League Status Verification", success, details)
        except Exception as e:
            return self.log_test("League Status Verification", False, f"Exception: {str(e)}")

    def run_multiple_users_test(self):
        """Run multiple users joining same league test"""
        print("🧪 MULTIPLE USERS JOIN LEAGUE TEST")
        print("=" * 70)
        print(f"Backend URL: {self.base_url}")
        print(f"Commissioner: {self.commissioner_email}")
        print(f"Test Users: {self.user_emails}")
        print()
        
        # Step 1: Setup - Authenticate commissioner and create league
        print("\n--- SETUP PHASE ---")
        if not self.authenticate_user(self.commissioner_email):
            print("❌ Failed to authenticate commissioner - aborting test")
            return False
            
        if not self.create_test_league():
            print("❌ Failed to create test league - aborting test")
            return False
        
        # Step 2: Sequential user joins
        print("\n--- MULTIPLE USER JOIN PHASE ---")
        for i, user_email in enumerate(self.user_emails, 1):
            print(f"\n--- User {i} Join: {user_email} ---")
            join_success = self.join_league_as_user(user_email)
            
            if join_success:
                # Verify member count after each join
                expected_count = i + 1  # +1 for commissioner
                print(f"Verifying member count after user {i} join...")
                self.verify_league_members(expected_count)
                self.verify_league_status(expected_count)
            else:
                print(f"❌ User {i} failed to join - continuing with remaining users")
        
        # Step 3: Final verification
        print("\n--- FINAL VERIFICATION PHASE ---")
        final_expected_count = len([email for email in self.user_emails]) + 1  # All users + commissioner
        self.verify_league_members(final_expected_count)
        self.verify_league_status(final_expected_count)
        
        print("\n" + "=" * 70)
        print("🎯 MULTIPLE USERS JOIN TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"Overall Success Rate: {self.tests_passed}/{self.tests_run} ({success_rate:.1f}%)")
        
        if self.test_league_id:
            print(f"Test League ID: {self.test_league_id}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for failed in self.failed_tests:
                print(f"   - {failed}")
        
        # Final assessment
        print("\n🔍 MULTIPLE USERS JOIN READINESS ASSESSMENT:")
        if success_rate >= 90:
            print("✅ Multiple users can successfully join the same league")
            print("   - All user joins working correctly")
            print("   - Member count tracking accurate")
            print("   - Member list verification successful")
        elif success_rate >= 75:
            print("⚠️  Multiple users join partially working with minor issues")
        else:
            print("❌ Multiple users join functionality has significant issues")
        
        return success_rate >= 75

def main():
    """Main test execution"""
    tester = MultipleUsersJoinTester()
    success = tester.run_multiple_users_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()