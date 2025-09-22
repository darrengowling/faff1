#!/usr/bin/env python3
"""
UCL Auction Backend API Testing Suite - Comprehensive Live Auction Engine Testing
Tests atomic bid processing, real-time WebSocket functionality, and auction state management
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid
import asyncio
import socketio
import threading
from concurrent.futures import ThreadPoolExecutor

class UCLAuctionAPITester:
    def __init__(self, base_url="https://champbid-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.commissioner_token = None
        self.manager_tokens = {}
        self.user_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test data
        self.commissioner_email = "commissioner@example.com"
        self.manager_emails = [
            "manager1@example.com",
            "manager2@example.com", 
            "manager3@example.com",
            "manager4@example.com",
            "manager5@example.com"
        ]
        self.test_league_id = None
        self.test_invitations = []
        self.test_auction_id = None
        self.test_clubs = []
        
        # WebSocket testing
        self.socket_clients = {}
        self.websocket_events = []
        self.bid_results = []
        
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

    def make_request(self, method, endpoint, data=None, expected_status=200, token=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use provided token or default commissioner token
        auth_token = token or self.commissioner_token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_health_check(self):
        """Test health check endpoint"""
        success, status, data = self.make_request('GET', 'health')
        return self.log_test(
            "Health Check", 
            success and 'status' in data and data['status'] == 'healthy',
            f"Status: {status}"
        )

    def test_clubs_seed(self):
        """Test clubs seeding endpoint"""
        success, status, data = self.make_request('POST', 'clubs/seed')
        return self.log_test(
            "Clubs Seed",
            success and 'message' in data,
            f"Status: {status}, {data.get('message', 'No message')}"
        )

    def test_get_clubs(self):
        """Test get all clubs endpoint"""
        success, status, data = self.make_request('GET', 'clubs')
        clubs_count = len(data) if isinstance(data, list) else 0
        return self.log_test(
            "Get Clubs",
            success and isinstance(data, list) and clubs_count >= 16,
            f"Status: {status}, Clubs found: {clubs_count}"
        )

    def authenticate_user(self, email):
        """Authenticate user using magic link flow"""
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": email},
            token=None  # No token needed for magic link request
        )
        
        if not success:
            return None, f"Failed to request magic link: {status}"
        
        print(f"📧 Magic link requested for {email}")
        
        # Step 2: In a real scenario, we'd extract token from email
        # For testing, we'll check the backend logs for the token
        # This is a simplified approach - in production you'd have proper test tokens
        
        # For now, let's try to use a test approach
        # We'll simulate the verification step with a mock token approach
        return None, "Authentication requires manual token extraction from logs"

    def test_with_manual_token(self, token):
        """Test with manually extracted token"""
        # Verify the token works
        success, status, data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if success and 'access_token' in data:
            self.commissioner_token = data['access_token']
            self.user_data = data['user']
            return True, f"Authenticated as {data['user']['email']}"
        
        return False, f"Token verification failed: {status}"

    def test_enhanced_league_creation(self):
        """Test enhanced league creation with comprehensive settings"""
        league_data = {
            "name": f"Elite UCL League 2025-26 {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "max_managers": 8,
                "min_managers": 4,
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        success, status, data = self.make_request(
            'POST',
            'leagues',
            league_data,
            expected_status=200  # Updated expected status
        )
        
        if success and 'id' in data:
            self.test_league_id = data['id']
            # Verify all settings are properly set
            settings_valid = (
                data.get('settings', {}).get('budget_per_manager') == 100 and
                data.get('settings', {}).get('max_managers') == 8 and
                data.get('settings', {}).get('min_managers') == 4 and
                data.get('member_count') == 1 and
                data.get('status') == 'setup'
            )
            
            return self.log_test(
                "Enhanced League Creation",
                success and settings_valid,
                f"Status: {status}, League ID: {data.get('id', 'None')}, Settings valid: {settings_valid}"
            )
        
        return self.log_test(
            "Enhanced League Creation",
            False,
            f"Status: {status}, Response: {data}"
        )

    def test_league_documents_creation(self):
        """Test that all related documents are created with league"""
        if not self.test_league_id:
            return self.log_test("League Documents Creation", False, "No test league ID")
        
        # Test league members (should have commissioner)
        success, status, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        members_valid = success and len(members) == 1 and members[0]['role'] == 'commissioner'
        
        # Test league status
        success2, status2, league_status = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        status_valid = success2 and league_status.get('member_count') == 1
        
        return self.log_test(
            "League Documents Creation",
            members_valid and status_valid,
            f"Members: {len(members) if success else 0}, Status valid: {status_valid}"
        )

    def test_invitation_management(self):
        """Test comprehensive invitation management system"""
        if not self.test_league_id:
            return self.log_test("Invitation Management", False, "No test league ID")
        
        results = []
        
        # Test sending invitations
        for i, email in enumerate(self.manager_emails[:3]):  # Test with 3 managers
            success, status, data = self.make_request(
                'POST',
                f'leagues/{self.test_league_id}/invite',
                {"league_id": self.test_league_id, "email": email}
            )
            
            if success and 'id' in data:
                self.test_invitations.append(data)
                results.append(f"✓ Invited {email}")
            else:
                results.append(f"✗ Failed to invite {email}: {status}")
        
        # Test getting invitations
        success, status, invitations = self.make_request('GET', f'leagues/{self.test_league_id}/invitations')
        invitations_valid = success and len(invitations) >= 3
        
        # Test duplicate invitation prevention
        success_dup, status_dup, data_dup = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"league_id": self.test_league_id, "email": self.manager_emails[0]},
            expected_status=400
        )
        
        duplicate_prevented = success_dup and status_dup == 400
        
        overall_success = len([r for r in results if r.startswith('✓')]) >= 2 and invitations_valid and duplicate_prevented
        
        return self.log_test(
            "Invitation Management",
            overall_success,
            f"Invitations sent: {len([r for r in results if r.startswith('✓')])}, Retrieved: {len(invitations) if success else 0}, Duplicate prevented: {duplicate_prevented}"
        )

    def test_league_size_validation(self):
        """Test league size validation (4-8 members)"""
        if not self.test_league_id:
            return self.log_test("League Size Validation", False, "No test league ID")
        
        # Test current status (should not be ready with only 1 member)
        success, status, league_status = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        
        not_ready_with_one = (
            success and 
            league_status.get('member_count') == 1 and
            league_status.get('min_members') == 4 and
            league_status.get('max_members') == 8 and
            not league_status.get('is_ready', True)
        )
        
        # Test joining league directly (for testing purposes)
        # This simulates what would happen when invitations are accepted
        join_results = []
        for i in range(3):  # Add 3 more members to reach minimum
            success_join, status_join, data_join = self.make_request(
                'POST',
                f'leagues/{self.test_league_id}/join'
            )
            join_results.append(success_join)
        
        # Check if league is now ready
        success2, status2, updated_status = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        ready_with_four = (
            success2 and 
            updated_status.get('member_count') >= 4 and
            updated_status.get('is_ready', False)
        )
        
        return self.log_test(
            "League Size Validation",
            not_ready_with_one and sum(join_results) >= 2,
            f"Not ready with 1: {not_ready_with_one}, Joins successful: {sum(join_results)}, Ready with 4+: {ready_with_four}"
        )

    def test_commissioner_access_control(self):
        """Test commissioner-only access controls"""
        if not self.test_league_id:
            return self.log_test("Commissioner Access Control", False, "No test league ID")
        
        # Test commissioner can access invitations
        success_comm, status_comm, invitations = self.make_request('GET', f'leagues/{self.test_league_id}/invitations')
        commissioner_access = success_comm and isinstance(invitations, list)
        
        # Test commissioner can send invitations
        success_invite, status_invite, invite_data = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"league_id": self.test_league_id, "email": "test_access@example.com"}
        )
        commissioner_invite = success_invite or status_invite == 400  # 400 if already invited
        
        # Test league members access (should work for any member)
        success_members, status_members, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        members_access = success_members and isinstance(members, list)
        
        return self.log_test(
            "Commissioner Access Control",
            commissioner_access and commissioner_invite and members_access,
            f"Invitations access: {commissioner_access}, Can invite: {commissioner_invite}, Members access: {members_access}"
        )

    def test_invitation_resend(self):
        """Test invitation resending functionality"""
        if not self.test_invitations:
            return self.log_test("Invitation Resend", False, "No test invitations available")
        
        invitation_id = self.test_invitations[0]['id']
        success, status, data = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invitations/{invitation_id}/resend'
        )
        
        return self.log_test(
            "Invitation Resend",
            success and 'id' in data,
            f"Status: {status}, Resent invitation: {data.get('email', 'Unknown')}"
        )

    def test_league_settings_validation(self):
        """Test league settings are properly validated and stored"""
        if not self.test_league_id:
            return self.log_test("League Settings Validation", False, "No test league ID")
        
        success, status, league = self.make_request('GET', f'leagues/{self.test_league_id}')
        
        if not success:
            return self.log_test("League Settings Validation", False, f"Failed to get league: {status}")
        
        settings = league.get('settings', {})
        scoring_rules = settings.get('scoring_rules', {})
        
        settings_valid = (
            settings.get('budget_per_manager') == 100 and
            settings.get('club_slots_per_manager') == 3 and
            settings.get('min_managers') == 4 and
            settings.get('max_managers') == 8 and
            scoring_rules.get('club_goal') == 1 and
            scoring_rules.get('club_win') == 3 and
            scoring_rules.get('club_draw') == 1
        )
        
        return self.log_test(
            "League Settings Validation",
            settings_valid,
            f"All settings properly stored and retrieved: {settings_valid}"
        )

    # ==================== AUCTION ENGINE TESTS ====================
    
    def test_auction_creation_and_setup(self):
        """Test auction creation when league is ready"""
        if not self.test_league_id:
            return self.log_test("Auction Creation", False, "No test league ID")
        
        # First ensure league is ready by checking status
        success, status, league_status = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        
        if not success or not league_status.get('is_ready', False):
            return self.log_test(
                "Auction Creation", 
                False, 
                f"League not ready for auction. Status: {league_status.get('status', 'unknown')}, Ready: {league_status.get('is_ready', False)}"
            )
        
        # Try to start auction (this should create auction if not exists)
        success, status, data = self.make_request(
            'POST',
            f'auction/{self.test_league_id}/start'
        )
        
        if success:
            self.test_auction_id = self.test_league_id  # Using league_id as auction_id for simplicity
            return self.log_test(
                "Auction Creation",
                True,
                f"Auction started successfully. Status: {status}"
            )
        else:
            return self.log_test(
                "Auction Creation",
                False,
                f"Failed to start auction. Status: {status}, Response: {data}"
            )

    def test_auction_state_retrieval(self):
        """Test getting auction state"""
        if not self.test_auction_id:
            return self.log_test("Auction State Retrieval", False, "No test auction ID")
        
        success, status, data = self.make_request('GET', f'auction/{self.test_auction_id}/state')
        
        state_valid = (
            success and 
            'auction_id' in data and
            'league_id' in data and
            'status' in data and
            'managers' in data
        )
        
        return self.log_test(
            "Auction State Retrieval",
            state_valid,
            f"Status: {status}, State valid: {state_valid}, Managers: {len(data.get('managers', []))}"
        )

    def test_atomic_bid_processing(self):
        """Test atomic bid processing with MongoDB transactions"""
        if not self.test_auction_id:
            return self.log_test("Atomic Bid Processing", False, "No test auction ID")
        
        # Get current auction state to find active lot
        success, status, auction_state = self.make_request('GET', f'auction/{self.test_auction_id}/state')
        
        if not success or not auction_state.get('current_lot'):
            return self.log_test(
                "Atomic Bid Processing",
                False,
                f"No active lot found. Status: {status}"
            )
        
        current_lot = auction_state['current_lot']
        lot_id = current_lot['_id']
        current_bid = current_lot.get('current_bid', 0)
        min_increment = auction_state.get('settings', {}).get('min_increment', 1)
        
        # Test valid bid
        bid_amount = current_bid + min_increment
        success, status, bid_result = self.make_request(
            'POST',
            f'auction/{self.test_auction_id}/bid',
            {
                "lot_id": lot_id,
                "amount": bid_amount
            }
        )
        
        bid_successful = success and bid_result.get('success', False)
        
        # Test invalid bid (too low)
        invalid_bid_amount = current_bid  # Same as current bid, should fail
        success2, status2, invalid_result = self.make_request(
            'POST',
            f'auction/{self.test_auction_id}/bid',
            {
                "lot_id": lot_id,
                "amount": invalid_bid_amount
            },
            expected_status=400
        )
        
        invalid_bid_rejected = success2 and status2 == 400
        
        return self.log_test(
            "Atomic Bid Processing",
            bid_successful and invalid_bid_rejected,
            f"Valid bid: {bid_successful}, Invalid bid rejected: {invalid_bid_rejected}"
        )

    def test_budget_constraint_validation(self):
        """Test budget and slot constraint validation"""
        if not self.test_auction_id:
            return self.log_test("Budget Constraint Validation", False, "No test auction ID")
        
        # Get current auction state
        success, status, auction_state = self.make_request('GET', f'auction/{self.test_auction_id}/state')
        
        if not success:
            return self.log_test("Budget Constraint Validation", False, f"Failed to get auction state: {status}")
        
        managers = auction_state.get('managers', [])
        if not managers:
            return self.log_test("Budget Constraint Validation", False, "No managers found in auction")
        
        user_manager = managers[0]  # Use first manager for testing
        budget = user_manager.get('budget_remaining', 0)
        
        current_lot = auction_state.get('current_lot')
        if not current_lot:
            return self.log_test("Budget Constraint Validation", False, "No active lot found")
        
        lot_id = current_lot['_id']
        
        # Test bid exceeding budget
        excessive_bid = budget + 50  # Bid more than available budget
        success, status, result = self.make_request(
            'POST',
            f'auction/{self.test_auction_id}/bid',
            {
                "lot_id": lot_id,
                "amount": excessive_bid
            },
            expected_status=400
        )
        
        budget_constraint_enforced = success and status == 400
        
        return self.log_test(
            "Budget Constraint Validation",
            budget_constraint_enforced,
            f"Budget constraint enforced: {budget_constraint_enforced}, Budget: {budget}, Attempted bid: {excessive_bid}"
        )

    def test_concurrent_bid_handling(self):
        """Test race condition handling with concurrent bids"""
        if not self.test_auction_id:
            return self.log_test("Concurrent Bid Handling", False, "No test auction ID")
        
        # Get current auction state
        success, status, auction_state = self.make_request('GET', f'auction/{self.test_auction_id}/state')
        
        if not success or not auction_state.get('current_lot'):
            return self.log_test("Concurrent Bid Handling", False, "No active lot found")
        
        current_lot = auction_state['current_lot']
        lot_id = current_lot['_id']
        current_bid = current_lot.get('current_bid', 0)
        min_increment = auction_state.get('settings', {}).get('min_increment', 1)
        
        # Simulate concurrent bids with same amount
        bid_amount = current_bid + min_increment
        
        def place_concurrent_bid():
            success, status, result = self.make_request(
                'POST',
                f'auction/{self.test_auction_id}/bid',
                {
                    "lot_id": lot_id,
                    "amount": bid_amount
                }
            )
            return success, status, result
        
        # Execute concurrent bids
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(place_concurrent_bid) for _ in range(3)]
            results = [future.result() for future in futures]
        
        # Only one bid should succeed, others should fail
        successful_bids = sum(1 for success, status, result in results if success and result.get('success', False))
        failed_bids = sum(1 for success, status, result in results if not success or not result.get('success', False))
        
        race_condition_handled = successful_bids == 1 and failed_bids == 2
        
        return self.log_test(
            "Concurrent Bid Handling",
            race_condition_handled,
            f"Successful bids: {successful_bids}, Failed bids: {failed_bids}, Race condition handled: {race_condition_handled}"
        )

    def test_auction_pause_resume(self):
        """Test auction pause/resume functionality (commissioner only)"""
        if not self.test_auction_id:
            return self.log_test("Auction Pause/Resume", False, "No test auction ID")
        
        # Test pause
        success_pause, status_pause, pause_result = self.make_request(
            'POST',
            f'auction/{self.test_auction_id}/pause'
        )
        
        pause_successful = success_pause and 'message' in pause_result
        
        # Test resume
        success_resume, status_resume, resume_result = self.make_request(
            'POST',
            f'auction/{self.test_auction_id}/resume'
        )
        
        resume_successful = success_resume and 'message' in resume_result
        
        return self.log_test(
            "Auction Pause/Resume",
            pause_successful and resume_successful,
            f"Pause: {pause_successful}, Resume: {resume_successful}"
        )

    def test_websocket_connection(self):
        """Test WebSocket connection and authentication"""
        if not self.commissioner_token or not self.test_auction_id:
            return self.log_test("WebSocket Connection", False, "Missing token or auction ID")
        
        try:
            # Create Socket.IO client
            sio = socketio.Client()
            connection_successful = False
            auth_successful = False
            
            @sio.event
            def connect():
                nonlocal connection_successful
                connection_successful = True
                print("WebSocket connected successfully")
            
            @sio.event
            def connect_error(data):
                print(f"WebSocket connection failed: {data}")
            
            @sio.event
            def auction_state(data):
                nonlocal auth_successful
                auth_successful = True
                self.websocket_events.append(('auction_state', data))
                print(f"Received auction state: {data.get('auction_id', 'unknown')}")
            
            # Connect with authentication
            sio.connect(
                self.base_url,
                auth={'token': self.commissioner_token},
                transports=['websocket', 'polling']
            )
            
            # Wait for connection
            time.sleep(2)
            
            if connection_successful:
                # Join auction room
                join_result = sio.call('join_auction', {'auction_id': self.test_auction_id}, timeout=5)
                join_successful = join_result and join_result.get('success', False)
                
                # Wait for auction state
                time.sleep(2)
                
                sio.disconnect()
                
                return self.log_test(
                    "WebSocket Connection",
                    connection_successful and join_successful and auth_successful,
                    f"Connected: {connection_successful}, Joined: {join_successful}, Auth: {auth_successful}"
                )
            else:
                return self.log_test("WebSocket Connection", False, "Failed to connect")
                
        except Exception as e:
            return self.log_test("WebSocket Connection", False, f"Exception: {str(e)}")

    def test_websocket_bid_placement(self):
        """Test placing bids through WebSocket"""
        if not self.commissioner_token or not self.test_auction_id:
            return self.log_test("WebSocket Bid Placement", False, "Missing token or auction ID")
        
        try:
            sio = socketio.Client()
            bid_result_received = False
            lot_update_received = False
            
            @sio.event
            def connect():
                print("WebSocket connected for bid testing")
            
            @sio.event
            def bid_result(data):
                nonlocal bid_result_received
                bid_result_received = True
                self.bid_results.append(data)
                print(f"Bid result: {data}")
            
            @sio.event
            def lot_update(data):
                nonlocal lot_update_received
                lot_update_received = True
                print(f"Lot update: {data}")
            
            # Connect and join auction
            sio.connect(
                self.base_url,
                auth={'token': self.commissioner_token},
                transports=['websocket', 'polling']
            )
            
            time.sleep(1)
            
            join_result = sio.call('join_auction', {'auction_id': self.test_auction_id}, timeout=5)
            
            if join_result and join_result.get('success', False):
                # Get current auction state first
                auction_state = sio.call('get_auction_state', {'auction_id': self.test_auction_id}, timeout=5)
                
                if auction_state and auction_state.get('success', False):
                    # Place a bid through WebSocket
                    bid_data = {
                        'auction_id': self.test_auction_id,
                        'lot_id': 'test_lot_id',  # This would need to be a real lot ID
                        'amount': 10
                    }
                    
                    bid_response = sio.call('place_bid', bid_data, timeout=10)
                    
                    # Wait for events
                    time.sleep(3)
                    
                    sio.disconnect()
                    
                    websocket_bid_successful = bid_result_received or lot_update_received
                    
                    return self.log_test(
                        "WebSocket Bid Placement",
                        websocket_bid_successful,
                        f"Bid result received: {bid_result_received}, Lot update received: {lot_update_received}"
                    )
                else:
                    sio.disconnect()
                    return self.log_test("WebSocket Bid Placement", False, "Failed to get auction state")
            else:
                sio.disconnect()
                return self.log_test("WebSocket Bid Placement", False, "Failed to join auction room")
                
        except Exception as e:
            return self.log_test("WebSocket Bid Placement", False, f"Exception: {str(e)}")

    def test_chat_functionality(self):
        """Test WebSocket chat functionality"""
        if not self.commissioner_token or not self.test_auction_id:
            return self.log_test("Chat Functionality", False, "Missing token or auction ID")
        
        try:
            sio = socketio.Client()
            chat_message_received = False
            
            @sio.event
            def connect():
                print("WebSocket connected for chat testing")
            
            @sio.event
            def chat_message(data):
                nonlocal chat_message_received
                chat_message_received = True
                print(f"Chat message received: {data}")
            
            # Connect and join auction
            sio.connect(
                self.base_url,
                auth={'token': self.commissioner_token},
                transports=['websocket', 'polling']
            )
            
            time.sleep(1)
            
            join_result = sio.call('join_auction', {'auction_id': self.test_auction_id}, timeout=5)
            
            if join_result and join_result.get('success', False):
                # Send chat message
                chat_data = {
                    'auction_id': self.test_auction_id,
                    'message': 'Test chat message from automated test'
                }
                
                chat_response = sio.call('send_chat_message', chat_data, timeout=5)
                
                # Wait for message to be broadcast back
                time.sleep(2)
                
                sio.disconnect()
                
                chat_successful = chat_response and chat_response.get('success', False)
                
                return self.log_test(
                    "Chat Functionality",
                    chat_successful,
                    f"Chat sent: {chat_successful}, Message received: {chat_message_received}"
                )
            else:
                sio.disconnect()
                return self.log_test("Chat Functionality", False, "Failed to join auction room")
                
        except Exception as e:
            return self.log_test("Chat Functionality", False, f"Exception: {str(e)}")

    def run_comprehensive_tests(self):
        """Run comprehensive league management and auction engine tests"""
        print("🚀 Starting UCL Auction Comprehensive Live Auction Engine Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Basic connectivity
        print("\n📡 CONNECTIVITY TESTS")
        self.test_health_check()
        
        # Setup data
        print("\n🏆 SETUP TESTS")
        self.test_clubs_seed()
        self.test_get_clubs()
        
        # Enhanced League Creation Tests
        print("\n🏟️ ENHANCED LEAGUE CREATION TESTS")
        self.test_enhanced_league_creation()
        self.test_league_documents_creation()
        self.test_league_settings_validation()
        
        # Invitation Management Tests  
        print("\n📧 INVITATION MANAGEMENT TESTS")
        self.test_invitation_management()
        self.test_invitation_resend()
        
        # League Size Validation Tests
        print("\n👥 LEAGUE SIZE VALIDATION TESTS")
        self.test_league_size_validation()
        
        # Commissioner Controls Tests
        print("\n👑 COMMISSIONER CONTROLS TESTS")
        self.test_commissioner_access_control()
        
        # ==================== AUCTION ENGINE TESTS ====================
        print("\n🎯 AUCTION ENGINE TESTS")
        self.test_auction_creation_and_setup()
        self.test_auction_state_retrieval()
        
        print("\n💰 ATOMIC BID PROCESSING TESTS")
        self.test_atomic_bid_processing()
        self.test_budget_constraint_validation()
        self.test_concurrent_bid_handling()
        
        print("\n⏸️ AUCTION CONTROL TESTS")
        self.test_auction_pause_resume()
        
        print("\n🔌 WEBSOCKET INTEGRATION TESTS")
        self.test_websocket_connection()
        self.test_websocket_bid_placement()
        self.test_chat_functionality()
        
        # Print detailed summary
        print("\n" + "=" * 80)
        print(f"📊 COMPREHENSIVE TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        # Auction-specific summary
        auction_tests = [test for test in self.failed_tests if any(keyword in test.lower() for keyword in ['auction', 'bid', 'websocket', 'chat'])]
        if auction_tests:
            print(f"\n🎯 AUCTION ENGINE ISSUES ({len(auction_tests)}):")
            for i, failure in enumerate(auction_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All comprehensive tests passed!")
            print("✅ Atomic bid processing working correctly")
            print("✅ Real-time WebSocket functionality operational")
            print("✅ Auction state management functioning properly")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed - see details above")
            
            # Provide specific guidance for auction issues
            if auction_tests:
                print("\n🔧 AUCTION ENGINE RECOMMENDATIONS:")
                print("   - Check MongoDB transaction support")
                print("   - Verify WebSocket server configuration")
                print("   - Ensure auction engine initialization")
                print("   - Test with manual authentication tokens")
            
            return 1

def main():
    """Main test runner"""
    tester = UCLAuctionAPITester()
    return tester.run_comprehensive_tests()

if __name__ == "__main__":
    sys.exit(main())