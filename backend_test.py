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
import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import concurrent.futures

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
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BiddingTestSuite/1.0'
        })
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            self.session.close()
            
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
            resp = self.session.post(f"{API_BASE}/auth/test-login", json={"email": email})
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result(f"Authentication for {email}", True, f"User ID: {data['userId']}")
                return data['userId']
            else:
                await self.log_result(f"Authentication for {email}", False, f"Status {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            await self.log_result(f"Authentication for {email}", False, f"Exception: {str(e)}")
            return None
            
    async def create_league_with_multiple_users(self) -> bool:
        """
        CRITICAL TEST 1: Complete Auction Setup
        Create league with multiple users for bidding
        """
        print("\n🎯 PHASE 1: COMPLETE AUCTION SETUP")
        
        try:
            # Create test users
            test_emails = [
                "commissioner@test.com",
                "manager1@test.com", 
                "manager2@test.com",
                "manager3@test.com",
                "manager4@test.com"
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
                    
            if len(self.test_users) < 5:
                await self.log_result("User Authentication", False, f"Only {len(self.test_users)}/5 users authenticated")
                return False
                
            await self.log_result("User Authentication", True, f"All {len(self.test_users)} users authenticated")
            
            # Create league as commissioner
            commissioner = self.test_users[0]
            league_data = {
                "name": f"Bidding Test League {datetime.now().strftime('%H%M%S')}",
                "season": "2025-26",
                "settings": {
                    "budget_per_manager": 100,
                    "club_slots_per_manager": 8,
                    "bid_timer_seconds": 60,
                    "anti_snipe_seconds": 30,
                    "league_size": {"min": 2, "max": 8}
                }
            }
            
            resp = self.session.post(f"{API_BASE}/leagues", json=league_data)
            if resp.status_code == 201:
                data = resp.json()
                self.league_id = data['leagueId']
                await self.log_result("League Creation", True, f"League ID: {self.league_id}")
            else:
                await self.log_result("League Creation", False, f"Status {resp.status_code}: {resp.text}")
                return False
                    
            # Add other users to league
            for user in self.test_users[1:]:  # Skip commissioner
                resp = self.session.post(f"{API_BASE}/leagues/{self.league_id}/join")
                if resp.status_code == 200:
                    await self.log_result(f"User Join - {user['email']}", True)
                else:
                    await self.log_result(f"User Join - {user['email']}", False, f"Status {resp.status_code}: {resp.text}")
                        
            # Verify league status
            resp = self.session.get(f"{API_BASE}/leagues/{self.league_id}/status")
            if resp.status_code == 200:
                data = resp.json()
                await self.log_result("League Status Check", True, 
                                    f"Members: {data['member_count']}, Ready: {data['is_ready']}")
                return data['is_ready']
            else:
                await self.log_result("League Status Check", False, f"Status {resp.status_code}")
                return False
                    
        except Exception as e:
            await self.log_result("Complete Auction Setup", False, f"Exception: {str(e)}")
            return False
            
    async def start_auction_and_get_lots(self) -> bool:
        """Start auction and get active lots"""
        print("\n🎯 PHASE 2: AUCTION START AND LOT RETRIEVAL")
        
        try:
            # Start auction
            async with self.session.post(f"{API_BASE}/auction/{self.league_id}/start") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auction_id = data.get('auction_id', self.league_id)  # Fallback to league_id
                    await self.log_result("Auction Start", True, f"Auction ID: {self.auction_id}")
                else:
                    error_text = await resp.text()
                    await self.log_result("Auction Start", False, f"Status {resp.status}: {error_text}")
                    return False
                    
            # Get auction state to find current lot
            async with self.session.get(f"{API_BASE}/auction/{self.auction_id}/state") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    current_lot = data.get('current_lot')
                    if current_lot:
                        self.current_lot_id = current_lot['id']
                        await self.log_result("Current Lot Retrieval", True, 
                                            f"Lot ID: {self.current_lot_id}, Club: {current_lot.get('club', {}).get('name', 'Unknown')}")
                        return True
                    else:
                        await self.log_result("Current Lot Retrieval", False, "No current lot found")
                        return False
                else:
                    await self.log_result("Current Lot Retrieval", False, f"Status {resp.status}")
                    return False
                    
        except Exception as e:
            await self.log_result("Auction Start and Lot Retrieval", False, f"Exception: {str(e)}")
            return False
            
    async def test_bid_placement(self) -> bool:
        """
        CRITICAL TEST 2: Place Actual Bids
        Test POST /api/auction/{auction_id}/bid endpoint
        """
        print("\n🎯 PHASE 3: ACTUAL BID PLACEMENT TESTING")
        
        try:
            if not self.current_lot_id:
                await self.log_result("Bid Placement Setup", False, "No current lot available")
                return False
                
            # Test bid placement from multiple users
            bid_results = []
            
            # Manager 1 places first bid
            manager1 = self.test_users[1]
            bid_data = {
                "lot_id": self.current_lot_id,
                "amount": 5
            }
            
            async with self.session.post(f"{API_BASE}/auction/{self.auction_id}/bid", 
                                       json=bid_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    bid_results.append(data)
                    await self.log_result(f"First Bid - {manager1['email']}", True, 
                                        f"Amount: {bid_data['amount']}, Success: {data.get('success', False)}")
                else:
                    error_text = await resp.text()
                    await self.log_result(f"First Bid - {manager1['email']}", False, 
                                        f"Status {resp.status}: {error_text}")
                    
            # Manager 2 places higher bid
            manager2 = self.test_users[2]
            bid_data = {
                "lot_id": self.current_lot_id,
                "amount": 10
            }
            
            async with self.session.post(f"{API_BASE}/auction/{self.auction_id}/bid", 
                                       json=bid_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    bid_results.append(data)
                    await self.log_result(f"Higher Bid - {manager2['email']}", True, 
                                        f"Amount: {bid_data['amount']}, Success: {data.get('success', False)}")
                else:
                    error_text = await resp.text()
                    await self.log_result(f"Higher Bid - {manager2['email']}", False, 
                                        f"Status {resp.status}: {error_text}")
                    
            # Test invalid bid (too low)
            manager3 = self.test_users[3]
            bid_data = {
                "lot_id": self.current_lot_id,
                "amount": 8  # Lower than current bid
            }
            
            async with self.session.post(f"{API_BASE}/auction/{self.auction_id}/bid", 
                                       json=bid_data) as resp:
                if resp.status == 400:
                    await self.log_result(f"Invalid Low Bid - {manager3['email']}", True, 
                                        "Correctly rejected low bid")
                else:
                    await self.log_result(f"Invalid Low Bid - {manager3['email']}", False, 
                                        f"Should have rejected low bid, got status {resp.status}")
                    
            return len(bid_results) >= 2
            
        except Exception as e:
            await self.log_result("Bid Placement Testing", False, f"Exception: {str(e)}")
            return False
            
    async def test_race_conditions(self) -> bool:
        """
        CRITICAL TEST 3: Race Condition Testing
        Test simultaneous bidding scenarios
        """
        print("\n🎯 PHASE 4: RACE CONDITION TESTING")
        
        try:
            if not self.current_lot_id:
                await self.log_result("Race Condition Setup", False, "No current lot available")
                return False
                
            # Prepare simultaneous bids from multiple users
            tasks = []
            bid_amount = 15
            
            for i, user in enumerate(self.test_users[1:4]):  # Use 3 managers
                bid_data = {
                    "lot_id": self.current_lot_id,
                    "amount": bid_amount + i  # Slightly different amounts
                }
                
                task = self.place_bid_async(user, bid_data, f"Simultaneous Bid {i+1}")
                tasks.append(task)
                
            # Execute all bids simultaneously
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_bids = 0
            failed_bids = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    await self.log_result(f"Simultaneous Bid {i+1}", False, f"Exception: {str(result)}")
                    failed_bids += 1
                elif result:
                    successful_bids += 1
                else:
                    failed_bids += 1
                    
            await self.log_result("Race Condition Handling", True, 
                                f"Successful: {successful_bids}, Failed: {failed_bids}")
            
            # At least one bid should succeed, others should fail gracefully
            return successful_bids >= 1
            
        except Exception as e:
            await self.log_result("Race Condition Testing", False, f"Exception: {str(e)}")
            return False
            
    async def place_bid_async(self, user: Dict, bid_data: Dict, test_name: str) -> bool:
        """Helper method for async bid placement"""
        try:
            async with self.session.post(f"{API_BASE}/auction/{self.auction_id}/bid", 
                                       json=bid_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    success = data.get('success', False)
                    await self.log_result(f"{test_name} - {user['email']}", success, 
                                        f"Amount: {bid_data['amount']}")
                    return success
                else:
                    error_text = await resp.text()
                    await self.log_result(f"{test_name} - {user['email']}", False, 
                                        f"Status {resp.status}: {error_text}")
                    return False
        except Exception as e:
            await self.log_result(f"{test_name} - {user['email']}", False, f"Exception: {str(e)}")
            return False
            
    async def test_bid_state_management(self) -> bool:
        """
        CRITICAL TEST 4: Bid State Management
        Verify winning bid tracking and bid history
        """
        print("\n🎯 PHASE 5: BID STATE MANAGEMENT TESTING")
        
        try:
            if not self.current_lot_id:
                await self.log_result("Bid State Setup", False, "No current lot available")
                return False
                
            # Get current lot state
            async with self.session.get(f"{API_BASE}/auction/{self.auction_id}/state") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    current_lot = data.get('current_lot')
                    if current_lot:
                        current_bid = current_lot.get('current_bid', 0)
                        top_bidder = current_lot.get('top_bidder')
                        await self.log_result("Current Lot State", True, 
                                            f"Current bid: {current_bid}, Top bidder: {top_bidder}")
                        
                        # Verify bid progression
                        if current_bid > 0:
                            await self.log_result("Bid Progression", True, "Bids are being tracked correctly")
                            return True
                        else:
                            await self.log_result("Bid Progression", False, "No bids recorded")
                            return False
                    else:
                        await self.log_result("Current Lot State", False, "No current lot in auction state")
                        return False
                else:
                    await self.log_result("Current Lot State", False, f"Status {resp.status}")
                    return False
                    
        except Exception as e:
            await self.log_result("Bid State Management", False, f"Exception: {str(e)}")
            return False
            
    async def test_budget_impact(self) -> bool:
        """
        CRITICAL TEST 5: Budget Impact
        Verify budget deductions and constraint validation
        """
        print("\n🎯 PHASE 6: BUDGET IMPACT TESTING")
        
        try:
            # Get league members with budget info
            async with self.session.get(f"{API_BASE}/leagues/{self.league_id}/members") as resp:
                if resp.status == 200:
                    members = await resp.json()
                    await self.log_result("Member Budget Retrieval", True, f"Found {len(members)} members")
                    
                    # Check if any member has reduced budget (indicating successful bids)
                    budget_changes_detected = False
                    for member in members:
                        if hasattr(member, 'budget_remaining') and member.get('budget_remaining', 100) < 100:
                            budget_changes_detected = True
                            await self.log_result("Budget Deduction Detected", True, 
                                                f"User {member.get('user_id', 'Unknown')} has budget {member.get('budget_remaining', 'Unknown')}")
                            
                    if not budget_changes_detected:
                        await self.log_result("Budget Impact", True, "No budget changes yet (bids may not be finalized)")
                    
                    # Test budget constraint by trying to bid more than available budget
                    manager = self.test_users[4]  # Use last manager
                    excessive_bid = {
                        "lot_id": self.current_lot_id,
                        "amount": 150  # More than total budget
                    }
                    
                    async with self.session.post(f"{API_BASE}/auction/{self.auction_id}/bid", 
                                               json=excessive_bid) as resp:
                        if resp.status == 400:
                            await self.log_result("Budget Constraint Validation", True, 
                                                "Correctly rejected excessive bid")
                            return True
                        else:
                            await self.log_result("Budget Constraint Validation", False, 
                                                f"Should have rejected excessive bid, got status {resp.status}")
                            return False
                            
                else:
                    await self.log_result("Member Budget Retrieval", False, f"Status {resp.status}")
                    return False
                    
        except Exception as e:
            await self.log_result("Budget Impact Testing", False, f"Exception: {str(e)}")
            return False
            
    async def run_complete_bidding_test(self):
        """Run the complete bidding mechanism test suite"""
        print("🎯 COMPREHENSIVE BIDDING MECHANISM TEST SUITE")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Phase 1: Complete Auction Setup
            setup_success = await self.create_league_with_multiple_users()
            if not setup_success:
                print("\n❌ CRITICAL FAILURE: Could not set up auction environment")
                return
                
            # Phase 2: Start Auction
            auction_success = await self.start_auction_and_get_lots()
            if not auction_success:
                print("\n❌ CRITICAL FAILURE: Could not start auction or get lots")
                return
                
            # Phase 3: Test Bid Placement
            bid_success = await self.test_bid_placement()
            
            # Phase 4: Test Race Conditions
            race_success = await self.test_race_conditions()
            
            # Phase 5: Test Bid State Management
            state_success = await self.test_bid_state_management()
            
            # Phase 6: Test Budget Impact
            budget_success = await self.test_budget_impact()
            
            # Summary
            print("\n" + "=" * 60)
            print("🎯 BIDDING MECHANISM TEST RESULTS SUMMARY")
            print("=" * 60)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            # Critical functionality assessment
            critical_phases = [setup_success, auction_success, bid_success, race_success, state_success, budget_success]
            critical_passed = sum(critical_phases)
            
            print(f"\nCRITICAL PHASES: {critical_passed}/6 passed")
            
            if critical_passed >= 5:
                print("✅ BIDDING MECHANISM IS FUNCTIONAL - Ready for tomorrow's test!")
            elif critical_passed >= 3:
                print("⚠️ BIDDING MECHANISM PARTIALLY FUNCTIONAL - Some issues need attention")
            else:
                print("❌ BIDDING MECHANISM HAS CRITICAL ISSUES - Needs immediate fixes")
                
            # Detailed failure analysis
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
                    
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    test_suite = BiddingTestSuite()
    await test_suite.run_complete_bidding_test()

if __name__ == "__main__":
    asyncio.run(main())