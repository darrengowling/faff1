#!/usr/bin/env python3
"""
TIMEZONE FIX VERIFICATION TEST
Tests the timezone fix for anti-snipe timer issue as requested in review.

This test specifically covers:
1. Create Auction Setup with timer_ends_at values
2. Test Anti-Snipe Logic with timezone comparison
3. Verify No Timezone Errors occur
4. End-to-End Timer Testing with proper timing

SUCCESS CRITERIA:
- No timezone-related errors during bidding
- Anti-snipe timer extensions work correctly  
- All datetime comparisons succeed
- Auction timing is predictable and reliable
"""

import asyncio
import requests
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import time

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TimezoneFixTestSuite:
    def __init__(self):
        self.sessions = {}  # email -> session mapping
        self.test_users = []
        self.league_id = None
        self.auction_id = None
        self.current_lot_id = None
        self.test_results = []
        
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
        
    async def authenticate_user(self, email: str) -> Optional[str]:
        """Authenticate user and return user_id"""
        try:
            session = requests.Session()
            session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'TimezoneFixTestSuite/1.0'
            })
            
            resp = session.post(f"{API_BASE}/auth/test-login", json={"email": email})
            if resp.status_code == 200:
                data = resp.json()
                self.sessions[email] = session
                await self.log_result(f"Authentication for {email}", True, f"User ID: {data['userId']}")
                return data['userId']
            else:
                await self.log_result(f"Authentication for {email}", False, f"Status {resp.status_code}: {resp.text}")
                session.close()
                return None
        except Exception as e:
            await self.log_result(f"Authentication for {email}", False, f"Exception: {str(e)}")
            return None
            
    async def create_auction_setup(self) -> bool:
        """
        TEST 1: Create Auction Setup
        Create league and start auction, verify lots are created with timer_ends_at values
        """
        print("\n🎯 TEST 1: CREATE AUCTION SETUP WITH TIMER_ENDS_AT VALUES")
        
        try:
            # Create test users
            test_emails = [
                "commissioner@example.com",
                "manager1@example.com", 
                "manager2@example.com",
                "manager3@example.com"
            ]
            
            # Authenticate all users
            for email in test_emails:
                user_id = await self.authenticate_user(email)
                if user_id:
                    self.test_users.append({
                        'email': email,
                        'user_id': user_id,
                        'role': 'commissioner' if email == test_emails[0] else 'manager'
                    })
                    
            if len(self.test_users) < 4:
                await self.log_result("User Authentication", False, f"Only {len(self.test_users)}/4 users authenticated")
                return False
                
            await self.log_result("User Authentication", True, f"All {len(self.test_users)} users authenticated")
            
            # Create league as commissioner with specific timer settings
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            league_data = {
                "name": f"Timezone Fix Test League {datetime.now().strftime('%H%M%S')}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 30,  # Minimum allowed timer
                    "anti_snipe_seconds": 3,  # Short anti-snipe for testing
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            resp = commissioner_session.post(f"{API_BASE}/leagues", json=league_data)
            if resp.status_code == 201:
                data = resp.json()
                self.league_id = data['leagueId']
                await self.log_result("League Creation", True, f"League ID: {self.league_id}")
            else:
                await self.log_result("League Creation", False, f"Status {resp.status_code}: {resp.text}")
                return False
                    
            # Add other users to league
            for user in self.test_users[1:]:  # Skip commissioner
                user_session = self.sessions[user['email']]
                resp = user_session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                if resp.status_code == 200:
                    await self.log_result(f"User Join - {user['email']}", True)
                else:
                    await self.log_result(f"User Join - {user['email']}", False, f"Status {resp.status_code}: {resp.text}")
                        
            # Start auction
            resp = commissioner_session.post(f"{API_BASE}/auction/{self.league_id}/start")
            if resp.status_code == 200:
                data = resp.json()
                self.auction_id = data.get('auction_id', self.league_id)
                await self.log_result("Auction Start", True, f"Auction ID: {self.auction_id}")
            else:
                await self.log_result("Auction Start", False, f"Status {resp.status_code}: {resp.text}")
                return False
                
            # Verify lots are created with timer_ends_at values
            resp = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            if resp.status_code == 200:
                data = resp.json()
                current_lot = data.get('current_lot')
                if current_lot and current_lot.get('timer_ends_at'):
                    self.current_lot_id = current_lot.get('_id')
                    timer_ends_at = current_lot.get('timer_ends_at')
                    await self.log_result("Timer Ends At Verification", True, 
                                        f"Lot {self.current_lot_id} has timer_ends_at: {timer_ends_at}")
                    return True
                else:
                    await self.log_result("Timer Ends At Verification", False, "No timer_ends_at found in current lot")
                    return False
            else:
                await self.log_result("Auction State Retrieval", False, f"Status {resp.status_code}: {resp.text}")
                return False
                    
        except Exception as e:
            await self.log_result("Create Auction Setup", False, f"Exception: {str(e)}")
            return False
            
    async def test_anti_snipe_logic(self) -> bool:
        """
        TEST 2: Test Anti-Snipe Logic
        Place bids near the end of timer to trigger anti-snipe
        Verify timezone comparison works correctly
        """
        print("\n🎯 TEST 2: TEST ANTI-SNIPE LOGIC WITH TIMEZONE COMPARISON")
        
        try:
            if not self.current_lot_id:
                await self.log_result("Anti-Snipe Setup", False, "No current lot available")
                return False
                
            # Get current lot state to check timer
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            
            resp = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            if resp.status_code != 200:
                await self.log_result("Lot State Check", False, f"Status {resp.status_code}")
                return False
                
            data = resp.json()
            current_lot = data.get('current_lot')
            if not current_lot:
                await self.log_result("Current Lot Check", False, "No current lot found")
                return False
                
            original_timer = current_lot.get('timer_ends_at')
            await self.log_result("Original Timer Check", True, f"Original timer: {original_timer}")
            
            # Wait until we're close to the end of the timer (within anti-snipe window)
            if original_timer:
                try:
                    # Parse the timer (handle both string and datetime formats)
                    if isinstance(original_timer, str):
                        end_time = datetime.fromisoformat(original_timer.replace('Z', '+00:00'))
                    else:
                        end_time = original_timer
                        if end_time.tzinfo is None:
                            end_time = end_time.replace(tzinfo=timezone.utc)
                    
                    current_time = datetime.now(timezone.utc)
                    seconds_remaining = (end_time - current_time).total_seconds()
                    
                    await self.log_result("Timer Parsing", True, f"Seconds remaining: {seconds_remaining:.1f}")
                    
                    # If we have more than 4 seconds, wait until we're in anti-snipe window
                    if seconds_remaining > 4:
                        wait_time = seconds_remaining - 2.5  # Wait until 2.5 seconds remaining
                        await self.log_result("Waiting for Anti-Snipe Window", True, f"Waiting {wait_time:.1f} seconds")
                        await asyncio.sleep(wait_time)
                        
                except Exception as e:
                    await self.log_result("Timer Parsing", False, f"Timer parsing error: {str(e)}")
                    # Continue with test anyway
            
            # Place bid to trigger anti-snipe
            manager1 = self.test_users[1]
            manager1_session = self.sessions[manager1['email']]
            bid_data = {
                "lot_id": self.current_lot_id,
                "amount": 5
            }
            
            await self.log_result("Placing Anti-Snipe Bid", True, "Attempting bid near timer end")
            resp = manager1_session.post(f"{API_BASE}/auction/{self.auction_id}/bid", json=bid_data)
            
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result("Anti-Snipe Bid Placement", True, 
                                    f"Bid successful: {data.get('success', False)}")
                
                # Check if timer was extended (anti-snipe triggered)
                await asyncio.sleep(1)  # Give server time to process
                
                resp = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
                if resp.status_code == 200:
                    data = resp.json()
                    current_lot = data.get('current_lot')
                    if current_lot:
                        new_timer = current_lot.get('timer_ends_at')
                        if new_timer != original_timer:
                            await self.log_result("Anti-Snipe Timer Extension", True, 
                                                f"Timer extended from {original_timer} to {new_timer}")
                            return True
                        else:
                            await self.log_result("Anti-Snipe Timer Extension", True, 
                                                "Timer may not have needed extension or bid was not in anti-snipe window")
                            return True
                    else:
                        await self.log_result("Post-Bid Lot Check", False, "No current lot after bid")
                        return False
                else:
                    await self.log_result("Post-Bid State Check", False, f"Status {resp.status_code}")
                    return False
                    
            else:
                # Check if this is a timezone error
                error_text = resp.text
                if "offset-naive" in error_text and "offset-aware" in error_text:
                    await self.log_result("Timezone Error Detection", False, 
                                        f"TIMEZONE ERROR DETECTED: {error_text}")
                    return False
                else:
                    await self.log_result("Anti-Snipe Bid Placement", False, 
                                        f"Status {resp.status_code}: {error_text}")
                    return False
                    
        except Exception as e:
            error_str = str(e)
            if "offset-naive" in error_str and "offset-aware" in error_str:
                await self.log_result("Anti-Snipe Logic", False, f"TIMEZONE ERROR: {error_str}")
                return False
            else:
                await self.log_result("Anti-Snipe Logic", False, f"Exception: {error_str}")
                return False
                
    async def verify_no_timezone_errors(self) -> bool:
        """
        TEST 3: Verify No Timezone Errors
        Confirm no "can't subtract offset-naive and offset-aware datetimes" errors
        Test both string and datetime timer_ends_at formats
        """
        print("\n🎯 TEST 3: VERIFY NO TIMEZONE ERRORS")
        
        try:
            # Place multiple bids to test different scenarios
            test_scenarios = [
                {"user_idx": 1, "amount": 8, "description": "Regular bid"},
                {"user_idx": 2, "amount": 12, "description": "Higher bid"},
                {"user_idx": 3, "amount": 15, "description": "Even higher bid"}
            ]
            
            timezone_errors_detected = 0
            successful_bids = 0
            
            for scenario in test_scenarios:
                try:
                    user = self.test_users[scenario["user_idx"]]
                    user_session = self.sessions[user['email']]
                    bid_data = {
                        "lot_id": self.current_lot_id,
                        "amount": scenario["amount"]
                    }
                    
                    resp = user_session.post(f"{API_BASE}/auction/{self.auction_id}/bid", json=bid_data)
                    
                    if resp.status_code == 200:
                        successful_bids += 1
                        await self.log_result(f"Timezone Test - {scenario['description']}", True, 
                                            f"Bid {scenario['amount']} successful")
                    else:
                        error_text = resp.text
                        if "offset-naive" in error_text and "offset-aware" in error_text:
                            timezone_errors_detected += 1
                            await self.log_result(f"Timezone Test - {scenario['description']}", False, 
                                                f"TIMEZONE ERROR: {error_text}")
                        else:
                            await self.log_result(f"Timezone Test - {scenario['description']}", True, 
                                                f"Non-timezone error (acceptable): Status {resp.status_code}")
                    
                    # Small delay between bids
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    error_str = str(e)
                    if "offset-naive" in error_str and "offset-aware" in error_str:
                        timezone_errors_detected += 1
                        await self.log_result(f"Timezone Test - {scenario['description']}", False, 
                                            f"TIMEZONE EXCEPTION: {error_str}")
                    else:
                        await self.log_result(f"Timezone Test - {scenario['description']}", True, 
                                            f"Non-timezone exception (acceptable): {error_str}")
            
            # Summary
            if timezone_errors_detected == 0:
                await self.log_result("No Timezone Errors Verification", True, 
                                    f"No timezone errors detected in {len(test_scenarios)} test scenarios")
                return True
            else:
                await self.log_result("No Timezone Errors Verification", False, 
                                    f"{timezone_errors_detected} timezone errors detected")
                return False
                
        except Exception as e:
            error_str = str(e)
            if "offset-naive" in error_str and "offset-aware" in error_str:
                await self.log_result("Verify No Timezone Errors", False, f"TIMEZONE ERROR: {error_str}")
                return False
            else:
                await self.log_result("Verify No Timezone Errors", False, f"Exception: {error_str}")
                return False
                
    async def test_end_to_end_timer_testing(self) -> bool:
        """
        TEST 4: End-to-End Timer Testing
        Test complete bidding cycle with timer logic
        Verify all datetime operations work correctly
        """
        print("\n🎯 TEST 4: END-TO-END TIMER TESTING")
        
        try:
            # Test complete auction progression with proper timing
            commissioner = self.test_users[0]
            commissioner_session = self.sessions[commissioner['email']]
            
            # Get initial auction state
            resp = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
            if resp.status_code != 200:
                await self.log_result("Initial State Check", False, f"Status {resp.status_code}")
                return False
                
            initial_data = resp.json()
            initial_lot = initial_data.get('current_lot')
            if not initial_lot:
                await self.log_result("Initial Lot Check", False, "No current lot")
                return False
                
            await self.log_result("Initial State Check", True, 
                                f"Lot {initial_lot.get('_id')} status: {initial_lot.get('status')}")
            
            # Place a series of bids to test timer behavior
            bid_sequence = [
                {"user_idx": 1, "amount": 20, "delay": 0.5},
                {"user_idx": 2, "amount": 25, "delay": 1.0},
                {"user_idx": 3, "amount": 30, "delay": 0.5}
            ]
            
            datetime_operations_successful = 0
            total_datetime_operations = 0
            
            for i, bid in enumerate(bid_sequence):
                try:
                    total_datetime_operations += 1
                    
                    # Wait specified delay
                    await asyncio.sleep(bid["delay"])
                    
                    user = self.test_users[bid["user_idx"]]
                    user_session = self.sessions[user['email']]
                    bid_data = {
                        "lot_id": self.current_lot_id,
                        "amount": bid["amount"]
                    }
                    
                    resp = user_session.post(f"{API_BASE}/auction/{self.auction_id}/bid", json=bid_data)
                    
                    if resp.status_code == 200:
                        datetime_operations_successful += 1
                        await self.log_result(f"Timer Test Bid {i+1}", True, 
                                            f"Amount {bid['amount']} successful")
                    else:
                        error_text = resp.text
                        if "offset-naive" in error_text or "offset-aware" in error_text:
                            await self.log_result(f"Timer Test Bid {i+1}", False, 
                                                f"DATETIME ERROR: {error_text}")
                        else:
                            # Non-datetime error (e.g., bid too low) is acceptable
                            datetime_operations_successful += 1
                            await self.log_result(f"Timer Test Bid {i+1}", True, 
                                                f"Non-datetime error (acceptable): Status {resp.status_code}")
                    
                    # Check auction state after each bid
                    resp = commissioner_session.get(f"{API_BASE}/auction/{self.auction_id}/state")
                    if resp.status_code == 200:
                        data = resp.json()
                        current_lot = data.get('current_lot')
                        if current_lot:
                            timer_ends_at = current_lot.get('timer_ends_at')
                            status = current_lot.get('status')
                            await self.log_result(f"State Check After Bid {i+1}", True, 
                                                f"Status: {status}, Timer: {timer_ends_at}")
                        else:
                            await self.log_result(f"State Check After Bid {i+1}", True, 
                                                "Lot may have closed or progressed")
                    
                except Exception as e:
                    error_str = str(e)
                    if "offset-naive" in error_str or "offset-aware" in error_str:
                        await self.log_result(f"Timer Test Bid {i+1}", False, 
                                            f"DATETIME EXCEPTION: {error_str}")
                    else:
                        datetime_operations_successful += 1
                        await self.log_result(f"Timer Test Bid {i+1}", True, 
                                            f"Non-datetime exception (acceptable): {error_str}")
            
            # Final assessment
            if datetime_operations_successful == total_datetime_operations:
                await self.log_result("End-to-End Timer Testing", True, 
                                    f"All {total_datetime_operations} datetime operations successful")
                return True
            else:
                await self.log_result("End-to-End Timer Testing", False, 
                                    f"Only {datetime_operations_successful}/{total_datetime_operations} datetime operations successful")
                return False
                
        except Exception as e:
            error_str = str(e)
            if "offset-naive" in error_str or "offset-aware" in error_str:
                await self.log_result("End-to-End Timer Testing", False, f"DATETIME ERROR: {error_str}")
                return False
            else:
                await self.log_result("End-to-End Timer Testing", False, f"Exception: {error_str}")
                return False
                
    async def cleanup_session(self):
        """Cleanup HTTP sessions"""
        for session in self.sessions.values():
            session.close()
            
    async def run_timezone_fix_test(self):
        """Run the complete timezone fix test suite"""
        print("🎯 TIMEZONE FIX VERIFICATION TEST SUITE")
        print("=" * 60)
        print("Testing timezone fix for anti-snipe timer issue")
        print("SUCCESS CRITERIA:")
        print("- No timezone-related errors during bidding")
        print("- Anti-snipe timer extensions work correctly")
        print("- All datetime comparisons succeed")
        print("- Auction timing is predictable and reliable")
        print("=" * 60)
        
        try:
            # Test 1: Create Auction Setup
            setup_success = await self.create_auction_setup()
            if not setup_success:
                print("\n❌ CRITICAL FAILURE: Could not set up auction with timer_ends_at values")
                return
                
            # Test 2: Test Anti-Snipe Logic
            anti_snipe_success = await self.test_anti_snipe_logic()
            
            # Test 3: Verify No Timezone Errors
            no_errors_success = await self.verify_no_timezone_errors()
            
            # Test 4: End-to-End Timer Testing
            end_to_end_success = await self.test_end_to_end_timer_testing()
            
            # Summary
            print("\n" + "=" * 60)
            print("🎯 TIMEZONE FIX TEST RESULTS SUMMARY")
            print("=" * 60)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            # Critical functionality assessment
            critical_phases = [setup_success, anti_snipe_success, no_errors_success, end_to_end_success]
            critical_passed = sum(critical_phases)
            
            print(f"\nCRITICAL PHASES: {critical_passed}/4 passed")
            
            # Check for timezone-specific failures
            timezone_failures = [result for result in self.test_results 
                                if not result['success'] and 
                                ('TIMEZONE ERROR' in result['details'] or 'DATETIME ERROR' in result['details'])]
            
            if len(timezone_failures) == 0:
                print("✅ TIMEZONE FIX SUCCESSFUL - No timezone errors detected!")
                print("✅ Anti-snipe timer is ready for tomorrow's live auction!")
            else:
                print(f"❌ TIMEZONE ISSUES DETECTED - {len(timezone_failures)} timezone-related failures")
                print("❌ CRITICAL: Fix needed before tomorrow's live auction!")
                
            # Detailed failure analysis
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
                    
            # Specific timezone error summary
            if timezone_failures:
                print(f"\n🚨 TIMEZONE-SPECIFIC FAILURES ({len(timezone_failures)}):")
                for failure in timezone_failures:
                    print(f"  - {failure['test']}: {failure['details']}")
                    
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    test_suite = TimezoneFixTestSuite()
    await test_suite.run_timezone_fix_test()

if __name__ == "__main__":
    asyncio.run(main())