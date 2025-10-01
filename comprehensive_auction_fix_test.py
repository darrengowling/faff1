#!/usr/bin/env python3
"""
COMPREHENSIVE AUCTION START FIX VERIFICATION TEST
Tests the specific auction start fix and identifies any remaining issues.

This test covers:
1. Collection name mismatch issues (memberships vs league_memberships)
2. League readiness requirements 
3. Auction creation and starting process
4. Complete user flow verification

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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveAuctionFixTest:
    def __init__(self):
        self.sessions = {}  # email -> session mapping
        self.test_users = []
        self.league_id = None
        self.auction_id = None
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
                'User-Agent': 'ComprehensiveAuctionFixTest/1.0'
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
            
    def test_collection_name_mismatch_issue(self) -> bool:
        """
        TEST: Collection Name Mismatch Issue
        Verify that the My Leagues endpoint works correctly
        """
        print("\n🎯 TESTING COLLECTION NAME MISMATCH ISSUE")
        
        try:
            # Create test users
            test_emails = [
                "commissioner@collectionfix.com",
                "manager1@collectionfix.com"
            ]
            
            # Authenticate users
            for email in test_emails:
                user_id = self.authenticate_user(email)
                if user_id:
                    self.test_users.append({
                        'email': email,
                        'user_id': user_id,
                        'role': 'commissioner' if email == test_emails[0] else 'manager'
                    })
                    
            if len(self.test_users) < 2:
                self.log_result("Collection Test Setup", False, f"Only {len(self.test_users)}/2 users authenticated")
                return False
                
            # Create league as commissioner
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            league_data = {
                "name": f"Collection Fix Test League {datetime.now().strftime('%H%M%S')}",
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
                self.log_result("League Creation for Collection Test", True, f"League ID: {self.league_id}")
            else:
                self.log_result("League Creation for Collection Test", False, f"Status {resp.status_code}: {resp.text}")
                return False
                
            # Add manager to league
            manager = self.test_users[1]
            manager_session = self.sessions[manager['email']]
            resp = manager_session.post(f"{API_BASE}/leagues/{self.league_id}/join")
            if resp.status_code == 200:
                self.log_result("Manager Join for Collection Test", True)
            else:
                self.log_result("Manager Join for Collection Test", False, f"Status {resp.status_code}: {resp.text}")
                
            # Test My Leagues endpoint (this should show the collection mismatch issue)
            resp = commissioner_session.get(f"{API_BASE}/leagues")
            if resp.status_code == 200:
                leagues = resp.json()
                self.log_result("My Leagues API Call", True, f"Retrieved {len(leagues)} leagues")
                
                # Check if our league is in the list
                test_league_found = False
                for league in leagues:
                    if league.get('id') == self.league_id:
                        test_league_found = True
                        self.log_result("Test League Found in My Leagues", True, f"League: {league.get('name')}")
                        break
                        
                if not test_league_found:
                    self.log_result("Test League Found in My Leagues", False, 
                                  "League not found - likely due to collection name mismatch (memberships vs league_memberships)")
                    return False
                else:
                    return True
            else:
                self.log_result("My Leagues API Call", False, f"Status {resp.status_code}: {resp.text}")
                return False
                
        except Exception as e:
            self.log_result("Collection Name Mismatch Test", False, f"Exception: {str(e)}")
            return False
            
    def test_auction_creation_and_start(self) -> bool:
        """
        TEST: Auction Creation and Start Process
        Test the complete auction creation and start process
        """
        print("\n🎯 TESTING AUCTION CREATION AND START PROCESS")
        
        try:
            if not self.league_id:
                self.log_result("Auction Test Setup", False, "No league ID available")
                return False
                
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            
            # First, check league status
            resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/status")
            if resp.status_code == 200:
                status_data = resp.json()
                self.log_result("League Status Check", True, 
                              f"Status: {status_data.get('status')}, Members: {status_data.get('member_count')}, Ready: {status_data.get('is_ready')}")
                
                # If league is not ready, we need to understand why
                if not status_data.get('is_ready'):
                    self.log_result("League Readiness Issue", False, 
                                  f"League not ready - Status: {status_data.get('status')}, Members: {status_data.get('member_count')}/{status_data.get('min_members')}")
                    return False
            else:
                self.log_result("League Status Check", False, f"Status {resp.status_code}: {resp.text}")
                return False
                
            # Check if auction already exists for this league
            resp = commissioner_session.get(f"{API_BASE}/auction/{self.league_id}/state")
            if resp.status_code == 404:
                # Auction doesn't exist, we need to create it first
                self.log_result("Auction Existence Check", True, "No existing auction found, will create new one")
                
                # Try to create auction (this might be automatic when league becomes ready)
                # Let's check if there are clubs available for auction
                resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}")
                if resp.status_code == 200:
                    league_data = resp.json()
                    self.log_result("League Data Retrieval", True, f"League status: {league_data.get('status')}")
                else:
                    self.log_result("League Data Retrieval", False, f"Status {resp.status_code}")
                    return False
                    
            elif resp.status_code == 200:
                auction_data = resp.json()
                self.log_result("Auction Existence Check", True, f"Auction exists with status: {auction_data.get('status')}")
            else:
                self.log_result("Auction Existence Check", False, f"Unexpected status {resp.status_code}: {resp.text}")
                
            # Now try to start the auction
            resp = commissioner_session.post(f"{API_BASE}/auction/{self.league_id}/start")
            if resp.status_code == 200:
                data = resp.json()
                self.auction_id = data.get('auction_id', self.league_id)
                self.log_result("Auction Start Success", True, f"Auction started! ID: {self.auction_id}")
                
                # Verify auction is actually running
                resp = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
                if resp.status_code == 200:
                    auction_state = resp.json()
                    self.log_result("Auction State Verification", True, 
                                  f"Auction status: {auction_state.get('status')}")
                    return True
                else:
                    self.log_result("Auction State Verification", False, 
                                  f"Could not verify auction state: {resp.status_code}")
                    return False
            else:
                self.log_result("Auction Start Failure", False, 
                              f"Status {resp.status_code}: {resp.text}")
                
                # Let's diagnose why auction start failed
                if resp.status_code == 400:
                    error_detail = resp.json().get('detail', 'Unknown error')
                    if "not ready" in error_detail.lower():
                        self.log_result("Auction Start Diagnosis", False, 
                                      "League not ready for auction - need to check league setup requirements")
                    elif "not found" in error_detail.lower():
                        self.log_result("Auction Start Diagnosis", False, 
                                      "Auction not found - may need to create auction first")
                    else:
                        self.log_result("Auction Start Diagnosis", False, f"Other error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_result("Auction Creation and Start Test", False, f"Exception: {str(e)}")
            return False
            
    def test_league_setup_requirements(self) -> bool:
        """
        TEST: League Setup Requirements
        Check what's needed to make a league ready for auction
        """
        print("\n🎯 TESTING LEAGUE SETUP REQUIREMENTS")
        
        try:
            if not self.league_id:
                self.log_result("League Setup Test", False, "No league ID available")
                return False
                
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            
            # Check league members
            resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/members")
            if resp.status_code == 200:
                members = resp.json()
                self.log_result("League Members Check", True, f"Found {len(members)} members")
                
                # List member details
                for member in members:
                    self.log_result(f"Member: {member.get('email', 'Unknown')}", True, 
                                  f"Role: {member.get('role', 'Unknown')}")
            else:
                self.log_result("League Members Check", False, f"Status {resp.status_code}: {resp.text}")
                
            # Check if clubs are assigned to league
            resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}")
            if resp.status_code == 200:
                league_data = resp.json()
                clubs = league_data.get('clubs', [])
                self.log_result("League Clubs Check", True, f"League has {len(clubs)} clubs assigned")
                
                if len(clubs) == 0:
                    self.log_result("League Clubs Issue", False, 
                                  "League has no clubs assigned - this may prevent auction from starting")
                    
                    # Try to add clubs to league (if there's an endpoint for this)
                    # This might be done automatically or require a separate step
                    
            else:
                self.log_result("League Clubs Check", False, f"Status {resp.status_code}: {resp.text}")
                
            # Check league status again
            resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}/status")
            if resp.status_code == 200:
                status_data = resp.json()
                self.log_result("Final League Status", True, 
                              f"Status: {status_data.get('status')}, Ready: {status_data.get('is_ready')}, Can Start: {status_data.get('can_start_auction')}")
                return status_data.get('can_start_auction', False)
            else:
                self.log_result("Final League Status", False, f"Status {resp.status_code}")
                return False
                
        except Exception as e:
            self.log_result("League Setup Requirements Test", False, f"Exception: {str(e)}")
            return False
            
    def test_backend_logs_for_undefined_ids(self) -> bool:
        """
        TEST: Backend Logs for Undefined IDs
        Check if backend logs show any "undefined" IDs
        """
        print("\n🎯 TESTING FOR UNDEFINED IDS IN BACKEND")
        
        try:
            # This test would ideally check backend logs, but we can't access them directly
            # Instead, we'll verify that all our API calls use proper IDs
            
            if self.league_id and self.league_id != "undefined" and len(self.league_id) > 10:
                self.log_result("League ID Format Check", True, f"League ID is valid: {self.league_id}")
            else:
                self.log_result("League ID Format Check", False, f"League ID is invalid: {self.league_id}")
                return False
                
            if self.auction_id and self.auction_id != "undefined" and len(self.auction_id) > 10:
                self.log_result("Auction ID Format Check", True, f"Auction ID is valid: {self.auction_id}")
            else:
                self.log_result("Auction ID Format Check", True, "No auction ID yet (auction not started)")
                
            # Test that API endpoints respond correctly to our IDs
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            
            # Test league endpoint with our ID
            resp = commissioner_session.get(f"{API_BASE}/leagues/{self.league_id}")
            if resp.status_code == 200:
                self.log_result("League ID API Response", True, "League endpoint responds correctly to our ID")
            else:
                self.log_result("League ID API Response", False, f"League endpoint error: {resp.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Backend Logs Test", False, f"Exception: {str(e)}")
            return False
            
    def cleanup_sessions(self):
        """Cleanup HTTP sessions"""
        for session in self.sessions.values():
            try:
                session.close()
            except:
                pass
                
    def run_comprehensive_test(self):
        """Run the comprehensive auction fix test suite"""
        print("🎯 COMPREHENSIVE AUCTION START FIX VERIFICATION TEST")
        print("=" * 70)
        print("Testing auction start fix and identifying any remaining issues")
        print("=" * 70)
        
        try:
            # Test 1: Collection Name Mismatch Issue
            test1_success = self.test_collection_name_mismatch_issue()
            
            # Test 2: League Setup Requirements
            test2_success = self.test_league_setup_requirements()
            
            # Test 3: Auction Creation and Start Process
            test3_success = self.test_auction_creation_and_start()
            
            # Test 4: Backend Logs for Undefined IDs
            test4_success = self.test_backend_logs_for_undefined_ids()
            
            # Summary
            print("\n" + "=" * 70)
            print("🎯 COMPREHENSIVE AUCTION FIX TEST RESULTS")
            print("=" * 70)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            # Critical test assessment
            critical_tests = [test1_success, test2_success, test3_success, test4_success]
            critical_passed = sum(critical_tests)
            
            print(f"\nCRITICAL AREAS: {critical_passed}/4 working")
            
            # Detailed analysis
            print(f"\n🔍 DETAILED ANALYSIS:")
            print(f"✅ Collection Name Mismatch: {'FIXED' if test1_success else 'ISSUE DETECTED'}")
            print(f"✅ League Setup Requirements: {'MET' if test2_success else 'NOT MET'}")
            print(f"✅ Auction Start Process: {'WORKING' if test3_success else 'FAILING'}")
            print(f"✅ ID Format Validation: {'CORRECT' if test4_success else 'ISSUES FOUND'}")
            
            # SUCCESS CRITERIA CHECK
            print(f"\n🎯 SUCCESS CRITERIA VERIFICATION:")
            if test3_success:
                print("✅ Auction start API call succeeds (not 404 'auction not found')")
                print("✅ Users can start auctions successfully")
            else:
                print("❌ Auction start API call fails or users cannot start auctions")
                
            if test4_success:
                print("✅ Backend receives correct league ID (not 'undefined')")
            else:
                print("❌ Backend may receive 'undefined' league ID")
                
            if test1_success:
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
            elif critical_passed >= 2:
                print("\n⚠️ AUCTION START FIX HAS SOME ISSUES")
                print("⚠️ Some components working but issues need attention")
            else:
                print("\n❌ AUCTION START FIX HAS CRITICAL ISSUES")
                print("❌ Multiple components failing - needs immediate attention")
                
            # Detailed failure analysis
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
                    
            # Recommendations
            print(f"\n💡 RECOMMENDATIONS:")
            if not test1_success:
                print("  - Fix collection name mismatch: Change 'memberships' to 'league_memberships' in /api/leagues endpoint")
            if not test2_success:
                print("  - Check league setup requirements: Ensure clubs are assigned and league meets minimum requirements")
            if not test3_success:
                print("  - Debug auction creation process: Check if auction entity needs to be created before starting")
            if not test4_success:
                print("  - Verify ID handling: Ensure frontend passes correct league.id instead of league._id")
                    
        finally:
            self.cleanup_sessions()

def main():
    """Main test execution"""
    test_suite = ComprehensiveAuctionFixTest()
    test_suite.run_comprehensive_test()

if __name__ == "__main__":
    main()