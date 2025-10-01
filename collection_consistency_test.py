#!/usr/bin/env python3
"""
Collection Consistency Test
Testing Agent - Verify collection name consistency between join and members endpoints

Focus: Test the specific collection mismatch issue mentioned in test_result.md
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class CollectionConsistencyTester:
    def __init__(self, base_url="https://livebid-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Collection-Consistency-Tester/1.0'
        })
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        timestamp = int(datetime.now().timestamp())
        self.commissioner_email = f"commissioner-consistency-{timestamp}@example.com"
        self.join_user_email = f"join-user-consistency-{timestamp}@example.com"
        
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
            return response.status_code == 200
        except Exception as e:
            print(f"Authentication failed for {email}: {e}")
            return False

    def create_test_league(self):
        """Create a test league as commissioner"""
        try:
            timestamp = int(datetime.now().timestamp())
            league_data = {
                "name": f"Collection Consistency Test League {timestamp}",
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

    def test_collection_consistency_issue(self):
        """Test the specific collection mismatch issue"""
        if not self.test_league_id:
            return self.log_test("Collection Consistency Test", False, "No league ID available")
        
        print("\n🔍 TESTING COLLECTION CONSISTENCY ISSUE")
        print("=" * 50)
        
        # Step 1: Get initial member count (should be 1 - commissioner only)
        print("Step 1: Check initial member count...")
        if not self.authenticate_user(self.commissioner_email):
            return self.log_test("Collection Consistency Test", False, "Failed to authenticate commissioner")
        
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}/members")
            if response.status_code != 200:
                return self.log_test("Collection Consistency Test", False, f"Failed to get initial members: {response.status_code}")
            
            initial_members = response.json()
            initial_count = len(initial_members) if isinstance(initial_members, list) else 0
            print(f"   Initial member count: {initial_count}")
            print(f"   Initial members: {[m.get('email', 'N/A') for m in initial_members]}")
            
            if initial_count != 1:
                return self.log_test("Collection Consistency Test", False, f"Expected 1 initial member, got {initial_count}")
                
        except Exception as e:
            return self.log_test("Collection Consistency Test", False, f"Exception getting initial members: {str(e)}")
        
        # Step 2: Join league as new user
        print("\nStep 2: Join league as new user...")
        if not self.authenticate_user(self.join_user_email):
            return self.log_test("Collection Consistency Test", False, "Failed to authenticate join user")
        
        try:
            response = self.session.post(f"{self.api_url}/leagues/{self.test_league_id}/join")
            if response.status_code != 200:
                return self.log_test("Collection Consistency Test", False, f"Failed to join league: {response.status_code} - {response.text}")
            
            join_data = response.json()
            print(f"   Join response: {join_data.get('message', 'Success')}")
            
        except Exception as e:
            return self.log_test("Collection Consistency Test", False, f"Exception joining league: {str(e)}")
        
        # Step 3: Check member count after join (should be 2)
        print("\nStep 3: Check member count after join...")
        if not self.authenticate_user(self.commissioner_email):
            return self.log_test("Collection Consistency Test", False, "Failed to re-authenticate commissioner")
        
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}/members")
            if response.status_code != 200:
                return self.log_test("Collection Consistency Test", False, f"Failed to get members after join: {response.status_code}")
            
            after_join_members = response.json()
            after_join_count = len(after_join_members) if isinstance(after_join_members, list) else 0
            member_emails = [m.get('email', 'N/A') for m in after_join_members]
            
            print(f"   Member count after join: {after_join_count}")
            print(f"   Members after join: {member_emails}")
            
            # Check if the join user is in the members list
            join_user_found = self.join_user_email in member_emails
            commissioner_found = self.commissioner_email in member_emails
            
            print(f"   Commissioner found: {commissioner_found}")
            print(f"   Join user found: {join_user_found}")
            
            # This is the critical test - if collection mismatch exists, join user won't be found
            if not join_user_found:
                return self.log_test("Collection Consistency Test", False, 
                    f"COLLECTION MISMATCH DETECTED: Join user {self.join_user_email} not found in members list. "
                    f"This indicates the join endpoint and members endpoint are using different collections.")
            
            if after_join_count != 2:
                return self.log_test("Collection Consistency Test", False, 
                    f"Expected 2 members after join, got {after_join_count}. This may indicate collection inconsistency.")
            
            if not commissioner_found:
                return self.log_test("Collection Consistency Test", False, 
                    f"Commissioner {self.commissioner_email} not found in members list.")
            
        except Exception as e:
            return self.log_test("Collection Consistency Test", False, f"Exception getting members after join: {str(e)}")
        
        # Step 4: Cross-verify with league status endpoint
        print("\nStep 4: Cross-verify with league status endpoint...")
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}/status")
            if response.status_code != 200:
                return self.log_test("Collection Consistency Test", False, f"Failed to get league status: {response.status_code}")
            
            status_data = response.json()
            status_member_count = status_data.get('member_count', 0)
            
            print(f"   Status endpoint member count: {status_member_count}")
            print(f"   Members endpoint member count: {after_join_count}")
            
            if status_member_count != after_join_count:
                return self.log_test("Collection Consistency Test", False, 
                    f"Member count mismatch between status ({status_member_count}) and members ({after_join_count}) endpoints. "
                    f"This indicates collection inconsistency.")
            
        except Exception as e:
            return self.log_test("Collection Consistency Test", False, f"Exception getting league status: {str(e)}")
        
        # If we reach here, all tests passed
        return self.log_test("Collection Consistency Test", True, 
            "✅ No collection mismatch detected. Join and members endpoints are consistent.")

    def run_collection_consistency_test(self):
        """Run collection consistency test"""
        print("🧪 COLLECTION CONSISTENCY TEST")
        print("=" * 70)
        print(f"Backend URL: {self.base_url}")
        print(f"Commissioner: {self.commissioner_email}")
        print(f"Join User: {self.join_user_email}")
        print()
        print("Testing for collection name mismatch between:")
        print("- Join endpoint: /api/leagues/{league_id}/join")
        print("- Members endpoint: /api/leagues/{league_id}/members")
        print()
        
        # Setup
        if not self.authenticate_user(self.commissioner_email):
            print("❌ Failed to authenticate commissioner - aborting test")
            return False
            
        if not self.create_test_league():
            print("❌ Failed to create test league - aborting test")
            return False
        
        # Main test
        success = self.test_collection_consistency_issue()
        
        print("\n" + "=" * 70)
        print("🎯 COLLECTION CONSISTENCY TEST RESULTS")
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
        print("\n🔍 COLLECTION CONSISTENCY ASSESSMENT:")
        if success:
            print("✅ Collection consistency VERIFIED - No mismatch detected")
            print("   - Join endpoint correctly adds users to the collection")
            print("   - Members endpoint correctly retrieves users from the same collection")
            print("   - Member count tracking is accurate across endpoints")
            print("   - Copy Invitation Link functionality is ready")
        else:
            print("❌ Collection consistency ISSUE DETECTED")
            print("   - There may be a mismatch between collections used by different endpoints")
            print("   - Copy Invitation Link functionality may not work correctly")
        
        return success

def main():
    """Main test execution"""
    tester = CollectionConsistencyTester()
    success = tester.run_collection_consistency_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()