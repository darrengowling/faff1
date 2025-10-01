#!/usr/bin/env python3
"""
Backend API Testing for Copy Invitation Link Functionality
Testing Agent - Comprehensive Backend API Verification

Focus: Copy Invitation Link functionality testing as requested in review
- Authentication endpoints
- League creation 
- Direct league join via /api/leagues/{league_id}/join
- League member verification
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class CopyInviteLinkTester:
    def __init__(self, base_url="https://leaguemate-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Copy-Invite-Link-Tester/1.0'
        })
        self.test_league_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data for Copy Invitation Link functionality
        timestamp = int(datetime.now().timestamp())
        self.commissioner_email = f"commissioner-{timestamp}@example.com"
        self.join_user_email = f"join-user-{timestamp}@example.com"
        
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

    def test_health_check(self):
        """Test API health endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/health")
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            return self.log_test("Health Check", success, details)
        except Exception as e:
            return self.log_test("Health Check", False, f"Exception: {str(e)}")

    def test_authentication_login(self, email):
        """Test authentication via test-login endpoint"""
        try:
            payload = {"email": email}
            response = self.session.post(f"{self.api_url}/auth/test-login", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, User ID: {data.get('userId')}, Email: {data.get('email')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test(f"Authentication Login ({email})", success, details)
        except Exception as e:
            return self.log_test(f"Authentication Login ({email})", False, f"Exception: {str(e)}")

    def test_auth_me(self):
        """Test /auth/me endpoint to verify session"""
        try:
            response = self.session.get(f"{self.api_url}/auth/me")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, User: {data.get('email')}, Verified: {data.get('verified')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("Auth Me Verification", success, details)
        except Exception as e:
            return self.log_test("Auth Me Verification", False, f"Exception: {str(e)}")

    def test_league_creation(self):
        """Test league creation to get a league ID"""
        try:
            timestamp = int(datetime.now().timestamp())
            league_data = {
                "name": f"Copy Invite Test League {timestamp}",
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

    def test_league_details(self):
        """Test getting league details"""
        if not self.test_league_id:
            return self.log_test("League Details", False, "No league ID available")
            
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, League: {data.get('name')}, Status: {data.get('status')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("League Details", success, details)
        except Exception as e:
            return self.log_test("League Details", False, f"Exception: {str(e)}")

    def test_league_members_before_join(self):
        """Test getting league members before join (should be 1 - commissioner)"""
        if not self.test_league_id:
            return self.log_test("League Members (Before Join)", False, "No league ID available")
            
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}/members")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                member_count = len(data) if isinstance(data, list) else 0
                details = f"Status: {response.status_code}, Member count: {member_count}"
                if member_count > 0:
                    details += f", Members: {[m.get('email', 'N/A') for m in data]}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("League Members (Before Join)", success, details)
        except Exception as e:
            return self.log_test("League Members (Before Join)", False, f"Exception: {str(e)}")

    def test_direct_league_join(self):
        """Test direct league join via /api/leagues/{league_id}/join - MAIN TEST"""
        if not self.test_league_id:
            return self.log_test("Direct League Join", False, "No league ID available")
        
        # First, authenticate as a different user who will join the league
        auth_success = self.test_authentication_login(self.join_user_email)
        if not auth_success:
            return self.log_test("Direct League Join", False, "Failed to authenticate join user")
            
        try:
            response = self.session.post(f"{self.api_url}/leagues/{self.test_league_id}/join")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, Message: {data.get('message', 'Success')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("Direct League Join", success, details)
        except Exception as e:
            return self.log_test("Direct League Join", False, f"Exception: {str(e)}")

    def test_league_members_after_join(self):
        """Test getting league members after join (should be 2 - commissioner + joined user)"""
        if not self.test_league_id:
            return self.log_test("League Members (After Join)", False, "No league ID available")
            
        # Re-authenticate as original user to check members
        auth_success = self.test_authentication_login(self.commissioner_email)
        if not auth_success:
            return self.log_test("League Members (After Join)", False, "Failed to re-authenticate commissioner")
            
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}/members")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                member_count = len(data) if isinstance(data, list) else 0
                details = f"Status: {response.status_code}, Member count: {member_count}"
                if member_count > 0:
                    member_emails = [m.get('email', 'N/A') for m in data]
                    details += f", Members: {member_emails}"
                    # Check if join user is in the list
                    if self.join_user_email in member_emails:
                        details += " ✅ Join user found in members"
                    else:
                        details += " ❌ Join user NOT found in members"
                        success = False
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("League Members (After Join)", success, details)
        except Exception as e:
            return self.log_test("League Members (After Join)", False, f"Exception: {str(e)}")

    def test_league_status(self):
        """Test league status endpoint"""
        if not self.test_league_id:
            return self.log_test("League Status", False, "No league ID available")
            
        try:
            response = self.session.get(f"{self.api_url}/leagues/{self.test_league_id}/status")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, League Status: {data.get('status')}, Members: {data.get('member_count')}/{data.get('max_members')}, Ready: {data.get('is_ready')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test("League Status", success, details)
        except Exception as e:
            return self.log_test("League Status", False, f"Exception: {str(e)}")

    def run_copy_invitation_link_tests(self):
        """Run comprehensive Copy Invitation Link functionality tests"""
        print("🧪 BACKEND API TESTING - Copy Invitation Link Functionality")
        print("=" * 70)
        print(f"Backend URL: {self.base_url}")
        print(f"Commissioner: {self.commissioner_email}")
        print(f"Join User: {self.join_user_email}")
        print()
        
        # Test sequence as requested in review
        tests = [
            ("1. Health Check", self.test_health_check),
            ("2. Authentication (Commissioner)", lambda: self.test_authentication_login(self.commissioner_email)),
            ("3. Auth Me Verification", self.test_auth_me),
            ("4. League Creation", self.test_league_creation),
            ("5. League Details", self.test_league_details),
            ("6. League Members (Before Join)", self.test_league_members_before_join),
            ("7. Direct League Join", self.test_direct_league_join),
            ("8. League Members (After Join)", self.test_league_members_after_join),
            ("9. League Status", self.test_league_status),
        ]
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            test_func()
        
        print("\n" + "=" * 70)
        print("🎯 COPY INVITATION LINK FUNCTIONALITY TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"Overall Success Rate: {self.tests_passed}/{self.tests_run} ({success_rate:.1f}%)")
        
        if self.test_league_id:
            print(f"Created League ID: {self.test_league_id}")
            print(f"Invitation Link Format: {self.base_url}/join/{self.test_league_id}")
        
        # Critical test analysis
        critical_tests = [
            "Authentication Login",
            "League Creation", 
            "Direct League Join",
            "League Members (After Join)"
        ]
        
        critical_passed = sum(1 for test in self.failed_tests if not any(critical in test for critical in critical_tests))
        critical_total = len(critical_tests)
        critical_rate = ((critical_total - len([t for t in self.failed_tests if any(c in t for c in critical_tests)])) / critical_total) * 100
        
        print(f"Critical Tests Success Rate: {critical_rate:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for failed in self.failed_tests:
                print(f"   - {failed}")
        
        # Final assessment
        print("\n🔍 COPY INVITATION LINK READINESS ASSESSMENT:")
        if critical_rate >= 100:
            print("✅ Backend is READY to support Copy Invitation Link feature")
            print("   - Authentication endpoints working")
            print("   - League creation successful")
            print("   - Direct league join functional")
            print("   - Member verification working")
        elif critical_rate >= 75:
            print("⚠️  Backend is PARTIALLY READY with minor issues")
            print("   - Core functionality working but some edge cases may fail")
        else:
            print("❌ Backend is NOT READY for Copy Invitation Link feature")
            print("   - Critical functionality failures detected")
        
        return success_rate >= 75

def main():
    """Main test execution"""
    tester = CopyInviteLinkTester()
    success = tester.run_copy_invitation_link_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
        """Test that required environment variables are properly configured"""
        # Test backend health to verify environment is working
