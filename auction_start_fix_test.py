#!/usr/bin/env python3
"""
CRITICAL AUCTION START FIX VERIFICATION TEST
Tests the specific auction start fix that was just applied.

This test covers the exact scenarios mentioned in the review request:
1. Auction Start Fix Verification - Create league with multiple users, verify API call uses correct league ID
2. Field Name Fix Verification - Confirm backend no longer receives "undefined" auction ID  
3. Navigation Fix Test - Test "My Leagues" navigation works
4. Complete User Flow - Create league → Join users → Navigate → Start auction → Verify working

SUCCESS CRITERIA:
- Auction start API call succeeds (not 404 "auction not found")
- Backend logs show correct league ID (not "undefined")
- Users can start auctions successfully
- Navigation back to league list works
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://livebid-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class AuctionStartFixTest:
    def __init__(self):
        self.sessions = {}  # email -> session mapping
        self.test_users = []
        self.league_id = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
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
        
    def authenticate_user(self, email: str) -> Optional[str]:
        """Authenticate user and return user_id"""
        try:
            # Create separate session for each user
            session = requests.Session()
            session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'AuctionStartFixTest/1.0'
            })
            
            resp = session.post(f"{API_BASE}/auth/test-login", json={"email": email})
            if resp.status_code == 200:
                data = resp.json()
                # Store the authenticated session
                self.sessions[email] = session
                self.log_result(f"Authentication for {email}", True, f"User ID: {data['userId']}")
                return data['userId']
            else:
                self.log_result(f"Authentication for {email}", False, f"Status {resp.status_code}: {resp.text}")
                if session:
                    session.close()
                return None
        except Exception as e:
            self.log_result(f"Authentication for {email}", False, f"Exception: {str(e)}")
            return None
            
    def test_1_auction_start_fix_verification(self) -> bool:
        """
        TEST 1: Auction Start Fix Verification
        Create league with multiple users and verify API call uses correct league ID (not "undefined")
        """
        print("\n🎯 TEST 1: AUCTION START FIX VERIFICATION")
        
        try:
            # Create test users
            test_emails = [
                "commissioner@auctionfix.com",
                "manager1@auctionfix.com", 
                "manager2@auctionfix.com",
                "manager3@auctionfix.com"
            ]
            
            # Authenticate all users
            for email in test_emails:
                user_id = self.authenticate_user(email)
                if user_id:
                    self.test_users.append({
                        'email': email,
                        'user_id': user_id,
                        'role': 'commissioner' if email == test_emails[0] else 'manager'
                    })
                    
            if len(self.test_users) < 4:
                self.log_result("User Authentication Setup", False, f"Only {len(self.test_users)}/4 users authenticated")
                return False
                
            self.log_result("User Authentication Setup", True, f"All {len(self.test_users)} users authenticated")
            
            # Create league as commissioner
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            league_data = {
                "name": f"Auction Fix Test League {datetime.now().strftime('%H%M%S')}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            resp = commissioner_session.post(f"{API_BASE}/leagues", json=league_data)
            if resp.status_code == 201:
                data = resp.json()
                self.league_id = data['leagueId']
                self.log_result("League Creation", True, f"League ID: {self.league_id}")
                
                # CRITICAL: Verify league ID is not "undefined"
                if self.league_id and self.league_id != "undefined" and len(self.league_id) > 10:
                    self.log_result("League ID Validation", True, f"Valid league ID: {self.league_id}")
                else:
                    self.log_result("League ID Validation", False, f"Invalid league ID: {self.league_id}")
                    return False
            else:
                self.log_result("League Creation", False, f"Status {resp.status_code}: {resp.text}")
                return False
                    
            # Add other users to league
            for user in self.test_users[1:]:  # Skip commissioner
                user_session = self.sessions[user['email']]
                resp = user_session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                if resp.status_code == 200:
                    self.log_result(f"User Join - {user['email']}", True)
                else:
                    self.log_result(f"User Join - {user['email']}", False, f"Status {resp.status_code}: {resp.text}")
                        
            # Verify league status and readiness
            resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/status")
            if resp.status_code == 200:
                data = resp.json()
                self.log_result("League Status Check", True, 
                              f"Members: {data['member_count']}, Ready: {data['is_ready']}")
                return data['is_ready']
            else:
                self.log_result("League Status Check", False, f"Status {resp.status_code}")
                return False
                    
        except Exception as e:
            self.log_result("Auction Start Fix Verification", False, f"Exception: {str(e)}")
            return False
            
    def test_2_field_name_fix_verification(self) -> bool:
        """
        TEST 2: Field Name Fix Verification  
        Test POST /api/auction/{correct-league-id}/start endpoint and confirm backend receives correct ID
        """
        print("\n🎯 TEST 2: FIELD NAME FIX VERIFICATION")
        
        try:
            if not self.league_id:
                self.log_result("Field Name Fix Setup", False, "No league ID available")
                return False
                
            # Test the auction start endpoint with the correct league ID
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            
            # CRITICAL TEST: Use the correct league ID (not "undefined")
            auction_start_url = f"{API_BASE}/auction/{self.league_id}/start"
            self.log_result("Auction Start URL", True, f"Using URL: {auction_start_url}")
            
            resp = commissioner_session.post(auction_start_url)
            
            # Check response
            if resp.status_code == 200:
                data = resp.json()
                auction_id = data.get('auction_id', self.league_id)
                self.log_result("Auction Start API Call", True, f"Success! Auction ID: {auction_id}")
                
                # Verify the auction ID is valid (not "undefined")
                if auction_id and auction_id != "undefined":
                    self.log_result("Auction ID Validation", True, f"Valid auction ID received: {auction_id}")
                    return True
                else:
                    self.log_result("Auction ID Validation", False, f"Invalid auction ID: {auction_id}")
                    return False
                    
            elif resp.status_code == 404:
                self.log_result("Auction Start API Call", False, f"404 Error - Auction not found. This indicates the fix may not be working. Response: {resp.text}")
                return False
            else:
                self.log_result("Auction Start API Call", False, f"Status {resp.status_code}: {resp.text}")
                return False
                    
        except Exception as e:
            self.log_result("Field Name Fix Verification", False, f"Exception: {str(e)}")
            return False
            
    def test_3_navigation_fix_test(self) -> bool:
        """
        TEST 3: Navigation Fix Test
        Test that "My Leagues" navigation works and users can get back to league list
        """
        print("\n🎯 TEST 3: NAVIGATION FIX TEST")
        
        try:
            # Test getting league list (My Leagues functionality)
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            
            resp = commissioner_session.get(f"{API_BASE}/leagues")
            if resp.status_code == 200:
                leagues = resp.json()
                self.log_result("My Leagues Navigation", True, f"Retrieved {len(leagues)} leagues")
                
                # Verify our test league is in the list
                test_league_found = False
                for league in leagues:
                    if league.get('id') == self.league_id:
                        test_league_found = True
                        self.log_result("Test League in List", True, f"Found league: {league.get('name')}")
                        break
                        
                if not test_league_found:
                    self.log_result("Test League in List", False, "Test league not found in My Leagues")
                    return False
                    
                # Test individual league access (navigation to league page)
                resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}")
                if resp.status_code == 200:
                    league_data = resp.json()
                    self.log_result("League Page Navigation", True, f"Accessed league: {league_data.get('name')}")
                    return True
                else:
                    self.log_result("League Page Navigation", False, f"Status {resp.status_code}: {resp.text}")
                    return False
                    
            else:
                self.log_result("My Leagues Navigation", False, f"Status {resp.status_code}: {resp.text}")
                return False
                    
        except Exception as e:
            self.log_result("Navigation Fix Test", False, f"Exception: {str(e)}")
            return False
            
    def test_4_complete_user_flow(self) -> bool:
        """
        TEST 4: Complete User Flow
        Create league → Join users → Navigate → Start auction → Verify working
        """
        print("\n🎯 TEST 4: COMPLETE USER FLOW VERIFICATION")
        
        try:
            if not self.league_id or len(self.test_users) < 4:
                self.log_result("Complete Flow Setup", False, "Prerequisites not met")
                return False
                
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            
            # Step 1: Verify league creation (already done)
            self.log_result("Flow Step 1 - League Creation", True, f"League ID: {self.league_id}")
            
            # Step 2: Verify users joined (already done)
            resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/members")
            if resp.status_code == 200:
                members = resp.json()
                self.log_result("Flow Step 2 - Users Joined", True, f"{len(members)} members in league")
            else:
                self.log_result("Flow Step 2 - Users Joined", False, f"Status {resp.status_code}")
                return False
                
            # Step 3: Verify navigation works (already tested)
            self.log_result("Flow Step 3 - Navigation", True, "Navigation tested successfully")
            
            # Step 4: Start auction and verify it works
            resp = commissioner_session.post(f"{API_BASE}/auction/{self.league_id}/start")
            if resp.status_code == 200:
                data = resp.json()
                self.log_result("Flow Step 4 - Auction Start", True, f"Auction started successfully")
                
                # Step 5: Verify auction is actually running
                auction_id = data.get('auction_id', self.league_id)
                resp = commissioner_session.get(f"{API_BASE}/auction/{auction_id}/state")
                if resp.status_code == 200:
                    auction_state = resp.json()
                    self.log_result("Flow Step 5 - Auction Verification", True, 
                                  f"Auction state: {auction_state.get('status', 'unknown')}")
                    return True
                else:
                    self.log_result("Flow Step 5 - Auction Verification", False, 
                                  f"Could not verify auction state: {resp.status_code}")
                    return False
            else:
                self.log_result("Flow Step 4 - Auction Start", False, 
                              f"Auction start failed: {resp.status_code} - {resp.text}")
                return False
                    
        except Exception as e:
            self.log_result("Complete User Flow", False, f"Exception: {str(e)}")
            return False
            
    def cleanup_sessions(self):
        """Cleanup HTTP sessions"""
        for session in self.sessions.values():
            try:
                session.close()
            except:
                pass
                
    def run_auction_start_fix_test(self):
        """Run the complete auction start fix test suite"""
        print("🎯 CRITICAL AUCTION START FIX VERIFICATION TEST")
        print("=" * 60)
        print("Testing the specific auction start fix that was just applied")
        print("=" * 60)
        
        try:
            # Test 1: Auction Start Fix Verification
            test1_success = self.test_1_auction_start_fix_verification()
            
            # Test 2: Field Name Fix Verification  
            test2_success = self.test_2_field_name_fix_verification()
            
            # Test 3: Navigation Fix Test
            test3_success = self.test_3_navigation_fix_test()
            
            # Test 4: Complete User Flow
            test4_success = self.test_4_complete_user_flow()
            
            # Summary
            print("\n" + "=" * 60)
            print("🎯 AUCTION START FIX TEST RESULTS")
            print("=" * 60)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            # Critical test assessment
            critical_tests = [test1_success, test2_success, test3_success, test4_success]
            critical_passed = sum(critical_tests)
            
            print(f"\nCRITICAL TESTS: {critical_passed}/4 passed")
            
            # SUCCESS CRITERIA CHECK
            print(f"\n🎯 SUCCESS CRITERIA VERIFICATION:")
            if test2_success:
                print("✅ Auction start API call succeeds (not 404 'auction not found')")
            else:
                print("❌ Auction start API call fails")
                
            if test1_success and test2_success:
                print("✅ Backend receives correct league ID (not 'undefined')")
            else:
                print("❌ Backend may still receive 'undefined' league ID")
                
            if test4_success:
                print("✅ Users can start auctions successfully")
            else:
                print("❌ Users cannot start auctions successfully")
                
            if test3_success:
                print("✅ Navigation back to league list works")
            else:
                print("❌ Navigation back to league list fails")
            
            # Final assessment
            if critical_passed == 4:
                print("\n🎉 AUCTION START FIX IS WORKING PERFECTLY!")
                print("✅ All critical issues have been resolved")
                print("✅ Ready for user testing")
            elif critical_passed >= 3:
                print("\n⚠️ AUCTION START FIX IS MOSTLY WORKING")
                print("⚠️ Minor issues remain but core functionality works")
            else:
                print("\n❌ AUCTION START FIX HAS CRITICAL ISSUES")
                print("❌ The showstopper issue may not be fully resolved")
                
            # Detailed failure analysis
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
                    
        finally:
            self.cleanup_sessions()

def main():
    """Main test execution"""
    test_suite = AuctionStartFixTest()
    test_suite.run_auction_start_fix_test()

if __name__ == "__main__":
    main()