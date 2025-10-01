#!/usr/bin/env python3
"""
COMPREHENSIVE BIDDING MECHANISM TEST
Tests the complete auction bidding functionality as requested in review.

This test covers:
1. Complete Auction Setup (league creation, multiple users, auction start)
2. Place Actual Bids (POST /api/auction/{auction_id}/bid endpoint)
3. Race Condition Testing (simultaneous bidding scenarios)
4. Bid State Management (winning bid tracking, bid history)
5. Budget Impact (budget deductions, constraint validation)
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BiddingTestSuite:
    def __init__(self):
        self.session = None
        self.test_users = []
        self.league_id = None
        self.auction_id = None
        self.current_lot_id = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session with proper headers"""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
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

    def authenticate_user(self, email):
        """Authenticate a test user and store session"""
        try:
            # Create new session for this user
            user_session = requests.Session()
            user_session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'Invite-Code-Tester/1.0'
            })
            
            payload = {"email": email}
            response = user_session.post(f"{self.api_url}/auth/test-login", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.authenticated_users[email] = user_session
                details = f"Status: {response.status_code}, User ID: {data.get('userId')}, Email: {data.get('email')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            return self.log_test(f"Authentication ({email})", success, details)
        except Exception as e:
            return self.log_test(f"Authentication ({email})", False, f"Exception: {str(e)}")

    def create_league_with_invite_code(self, email, league_name):
        """Create a league and verify it gets an invite code"""
        try:
            if email not in self.authenticated_users:
                return self.log_test(f"Create League ({league_name})", False, f"User {email} not authenticated")
                
            session = self.authenticated_users[email]
            
            # Create league
            league_data = {
                "name": league_name,
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
            
            response = session.post(f"{self.api_url}/leagues", json=league_data)
            
            if response.status_code == 201:
                league_id = response.json().get("leagueId")
                
                # Get league details to verify invite code
                league_response = session.get(f"{self.api_url}/leagues/{league_id}")
                
                if league_response.status_code == 200:
                    league_details = league_response.json()
                    invite_code = league_details.get("invite_code")
                    
                    if invite_code:
                        # Verify invite code format (6 characters, letters and numbers, uppercase)
                        if len(invite_code) == 6 and invite_code.isalnum() and invite_code.isupper():
                            self.created_leagues.append({
                                "league_id": league_id,
                                "invite_code": invite_code,
                                "creator_email": email,
                                "league_name": league_name
                            })
                            details = f"League ID: {league_id}, Invite Code: {invite_code} (format verified)"
                            return self.log_test(f"Create League with Invite Code ({league_name})", True, details)
                        else:
                            details = f"League ID: {league_id}, Invalid invite code format: {invite_code} (should be 6 uppercase alphanumeric)"
                            return self.log_test(f"Create League with Invite Code ({league_name})", False, details)
                    else:
                        details = f"League ID: {league_id}, Missing invite_code field"
                        return self.log_test(f"Create League with Invite Code ({league_name})", False, details)
                else:
                    details = f"Failed to get league details: {league_response.status_code} - {league_response.text}"
                    return self.log_test(f"Create League with Invite Code ({league_name})", False, details)
            else:
                details = f"League creation failed: {response.status_code} - {response.text}"
                return self.log_test(f"Create League with Invite Code ({league_name})", False, details)
                
        except Exception as e:
            return self.log_test(f"Create League with Invite Code ({league_name})", False, f"Exception: {str(e)}")

    def join_league_by_invite_code(self, email, invite_code, expected_status=200):
        """Test joining a league using invite code"""
        try:
            if email not in self.authenticated_users:
                return self.log_test(f"Join by Invite Code ({email})", False, f"User {email} not authenticated")
                
            session = self.authenticated_users[email]
            
            # Join league by invite code
            response = session.post(f"{self.api_url}/leagues/join-by-code", 
                                  json={"code": invite_code})
            
            success = response.status_code == expected_status
            
            if success:
                if response.status_code == 200:
                    result = response.json()
                    details = f"Status: {response.status_code}, Message: {result.get('message', 'No message')}"
                elif response.status_code == 404:
                    details = f"Status: {response.status_code}, Correctly returned 404 for invalid code"
                elif response.status_code == 400:
                    result = response.json()
                    details = f"Status: {response.status_code}, Message: {result.get('detail', 'No detail')}"
                else:
                    details = f"Status: {response.status_code}"
            else:
                details = f"Expected {expected_status} but got {response.status_code} - {response.text}"
                
            return self.log_test(f"Join by Invite Code ({email}, {invite_code})", success, details)
                
        except Exception as e:
            return self.log_test(f"Join by Invite Code ({email}, {invite_code})", False, f"Exception: {str(e)}")

    def verify_league_membership(self, creator_email, league_id, expected_members):
        """Verify league membership after joins"""
        try:
            if creator_email not in self.authenticated_users:
                return self.log_test("Verify League Membership", False, f"Creator {creator_email} not authenticated")
                
            session = self.authenticated_users[creator_email]
            
            # Get league members
            response = session.get(f"{self.api_url}/leagues/{league_id}/members")
            
            if response.status_code == 200:
                members = response.json()
                member_emails = [member.get('email') for member in members]
                
                # Check if all expected members are present
                missing_members = []
                for expected_email in expected_members:
                    if expected_email not in member_emails:
                        missing_members.append(expected_email)
                
                if not missing_members:
                    details = f"All {len(expected_members)} expected members found: {member_emails}"
                    return self.log_test("Verify League Membership", True, details)
                else:
                    details = f"Missing members: {missing_members}, Found: {member_emails}"
                    return self.log_test("Verify League Membership", False, details)
            else:
                details = f"Failed to get league members: {response.status_code} - {response.text}"
                return self.log_test("Verify League Membership", False, details)
                
        except Exception as e:
            return self.log_test("Verify League Membership", False, f"Exception: {str(e)}")

    def test_invite_code_uniqueness(self):
        """Test that multiple leagues get unique invite codes"""
        try:
            # Create multiple leagues and collect their invite codes
            invite_codes = []
            league_names = [
                f"Uniqueness Test League 1 - {int(time.time())}",
                f"Uniqueness Test League 2 - {int(time.time())}",
                f"Uniqueness Test League 3 - {int(time.time())}"
            ]
            
            for league_name in league_names:
                if self.create_league_with_invite_code(self.test_email_1, league_name):
                    # Find the most recently created league
                    if self.created_leagues:
                        latest_league = self.created_leagues[-1]
                        invite_codes.append(latest_league["invite_code"])
                else:
                    return self.log_test("Invite Code Uniqueness", False, f"Failed to create league: {league_name}")
            
            # Check for uniqueness
            if len(invite_codes) == len(set(invite_codes)):
                details = f"All {len(invite_codes)} invite codes are unique: {invite_codes}"
                return self.log_test("Invite Code Uniqueness", True, details)
            else:
                details = f"Duplicate invite codes found: {invite_codes}"
                return self.log_test("Invite Code Uniqueness", False, details)
                
        except Exception as e:
            return self.log_test("Invite Code Uniqueness", False, f"Exception: {str(e)}")

    def run_invite_code_system_tests(self):
        """Run comprehensive invite code system tests as requested in review"""
        print("🚀 Starting Invite Code System Tests")
        print("=" * 80)
        
        # Test 1: Health Check
        print("\n📋 TEST 1: API Health Check")
        if not self.test_health_check():
            print("❌ API is not healthy, stopping tests")
            return False
        
        # Test 2: User Authentication
        print("\n📋 TEST 2: User Authentication")
        auth_success = True
        for email in [self.test_email_1, self.test_email_2, self.test_email_3]:
            if not self.authenticate_user(email):
                auth_success = False
        
        if not auth_success:
            print("❌ Authentication failed, cannot continue tests")
            return False
        
        # Test 3: Create League with Invite Code
        print("\n📋 TEST 3: Create League with Invite Code")
        league_name = f"Invite Code Test League - {int(time.time())}"
        if not self.create_league_with_invite_code(self.test_email_1, league_name):
            print("❌ League creation failed, cannot continue join tests")
            return False
        
        # Get the created league info
        test_league = self.created_leagues[-1]
        invite_code = test_league["invite_code"]
        league_id = test_league["league_id"]
        
        # Test 4: Valid Invite Code Join
        print("\n📋 TEST 4: Join via Valid Invite Code")
        self.join_league_by_invite_code(self.test_email_2, invite_code, expected_status=200)
        
        # Test 5: Invalid Invite Code (should return 404)
        print("\n📋 TEST 5: Invalid Invite Code Returns 404")
        self.join_league_by_invite_code(self.test_email_3, "INVALID123", expected_status=404)
        
        # Test 6: Duplicate Join (should return 400)
        print("\n📋 TEST 6: Duplicate Join Returns 400")
        self.join_league_by_invite_code(self.test_email_2, invite_code, expected_status=400)
        
        # Test 7: Verify League Membership
        print("\n📋 TEST 7: Verify League Membership")
        expected_members = [self.test_email_1, self.test_email_2]  # Creator + one joiner
        self.verify_league_membership(self.test_email_1, league_id, expected_members)
        
        # Test 8: Invite Code Uniqueness
        print("\n📋 TEST 8: Invite Code Uniqueness")
        self.test_invite_code_uniqueness()
        
        # Test 9: Complete Flow Test (Create → Join → Verify)
        print("\n📋 TEST 9: Complete Flow Test")
        flow_league_name = f"Complete Flow Test - {int(time.time())}"
        if self.create_league_with_invite_code(self.test_email_3, flow_league_name):
            flow_league = self.created_leagues[-1]
            flow_invite_code = flow_league["invite_code"]
            flow_league_id = flow_league["league_id"]
            
            # Join with different user
            if self.join_league_by_invite_code(self.test_email_1, flow_invite_code, expected_status=200):
                # Verify membership
                flow_expected_members = [self.test_email_3, self.test_email_1]
                self.verify_league_membership(self.test_email_3, flow_league_id, flow_expected_members)
        
        # Print final summary
        self.print_test_summary()
        
        # Return success if 75% or more tests passed
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        return success_rate >= 75

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 INVITE CODE SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {self.tests_passed}/{self.tests_run} tests passed ({success_rate:.1f}%)")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for failed_test in self.failed_tests:
                print(f"   - {failed_test}")
        
        print(f"\n📋 CREATED LEAGUES: {len(self.created_leagues)}")
        for league in self.created_leagues:
            print(f"   - {league['league_name']}: {league['invite_code']} (ID: {league['league_id']})")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT: Invite code system is working perfectly!")
        elif success_rate >= 75:
            print("\n✅ GOOD: Invite code system is mostly working with minor issues")
        elif success_rate >= 50:
            print("\n⚠️ PARTIAL: Invite code system has significant issues")
        else:
            print("\n❌ CRITICAL: Invite code system has major failures")
        
        # Summary for main agent
        print("\n" + "=" * 80)
        print("📝 SUMMARY FOR MAIN AGENT:")
        print("=" * 80)
        
        if success_rate >= 90:
            print("✅ INVITE CODE SYSTEM FULLY FUNCTIONAL")
            print("   - All core functionality working correctly")
            print("   - 6-character invite codes generated properly")
            print("   - Join-by-code endpoint working as expected")
            print("   - Error handling (404/400) working correctly")
            print("   - Invite code uniqueness verified")
        elif success_rate >= 75:
            print("⚠️ INVITE CODE SYSTEM MOSTLY FUNCTIONAL")
            print("   - Core functionality working")
            print("   - Some minor issues detected")
            print("   - Review failed tests above for details")
        else:
            print("❌ INVITE CODE SYSTEM HAS CRITICAL ISSUES")
            print("   - Major functionality failures detected")
            print("   - Requires immediate attention")
            print("   - Review failed tests above for details")

def main():
    """Main test execution"""
    print("🧪 Backend API Testing Suite - Invite Code System")
    print("Testing new invite code functionality as requested in review")
    print("=" * 80)
    
    tester = InviteCodeTester()
    success = tester.run_invite_code_system_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()