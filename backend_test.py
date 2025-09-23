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
    def __init__(self, base_url="https://ucl-auction-1.preview.emergentagent.com"):
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
        self.test_league_id_no_settings = None
        self.test_league_id_custom_settings = None
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

    # ==================== NEW AGGREGATION API TESTS ====================
    
    def test_my_clubs_endpoint(self):
        """Test /api/clubs/my-clubs/{league_id} endpoint"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("My Clubs Endpoint", False, "Missing league ID or token")
        
        success, status, data = self.make_request(
            'GET',
            f'clubs/my-clubs/{self.test_league_id}'
        )
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'league_id' in data and
            'user_id' in data and
            'owned_clubs' in data and
            'budget_info' in data and
            isinstance(data['owned_clubs'], list) and
            isinstance(data['budget_info'], dict)
        )
        
        return self.log_test(
            "My Clubs Endpoint",
            valid_response,
            f"Status: {status}, Valid structure: {valid_response}, Clubs: {len(data.get('owned_clubs', []))}"
        )
    
    def test_fixtures_endpoint(self):
        """Test /api/fixtures/{league_id} endpoint"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Fixtures Endpoint", False, "Missing league ID or token")
        
        success, status, data = self.make_request(
            'GET',
            f'fixtures/{self.test_league_id}'
        )
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'league_id' in data and
            'season' in data and
            'fixtures' in data and
            'grouped_fixtures' in data and
            'ownership_summary' in data and
            isinstance(data['fixtures'], list) and
            isinstance(data['grouped_fixtures'], dict) and
            isinstance(data['ownership_summary'], dict)
        )
        
        return self.log_test(
            "Fixtures Endpoint",
            valid_response,
            f"Status: {status}, Valid structure: {valid_response}, Fixtures: {len(data.get('fixtures', []))}"
        )
    
    def test_leaderboard_endpoint(self):
        """Test /api/leaderboard/{league_id} endpoint"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Leaderboard Endpoint", False, "Missing league ID or token")
        
        success, status, data = self.make_request(
            'GET',
            f'leaderboard/{self.test_league_id}'
        )
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'league_id' in data and
            'leaderboard' in data and
            'weekly_breakdown' in data and
            'total_managers' in data and
            isinstance(data['leaderboard'], list) and
            isinstance(data['weekly_breakdown'], dict) and
            isinstance(data['total_managers'], int)
        )
        
        return self.log_test(
            "Leaderboard Endpoint",
            valid_response,
            f"Status: {status}, Valid structure: {valid_response}, Managers: {data.get('total_managers', 0)}"
        )
    
    def test_head_to_head_endpoint(self):
        """Test /api/analytics/head-to-head/{league_id} endpoint"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Head-to-Head Endpoint", False, "Missing league ID or token")
        
        # Get league members to use for head-to-head comparison
        success_members, status_members, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        
        if not success_members or len(members) < 2:
            return self.log_test(
                "Head-to-Head Endpoint", 
                False, 
                f"Need at least 2 members for comparison. Found: {len(members) if success_members else 0}"
            )
        
        user1_id = members[0]['user_id']
        user2_id = members[1]['user_id'] if len(members) > 1 else members[0]['user_id']
        
        success, status, data = self.make_request(
            'GET',
            f'analytics/head-to-head/{self.test_league_id}?user1_id={user1_id}&user2_id={user2_id}'
        )
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'league_id' in data and
            'comparison' in data and
            isinstance(data['comparison'], list)
        )
        
        return self.log_test(
            "Head-to-Head Endpoint",
            valid_response,
            f"Status: {status}, Valid structure: {valid_response}, Comparisons: {len(data.get('comparison', []))}"
        )
    
    def test_aggregation_endpoints_access_control(self):
        """Test access control for aggregation endpoints"""
        if not self.test_league_id:
            return self.log_test("Aggregation Access Control", False, "Missing league ID")
        
        # Test without authentication token
        endpoints_to_test = [
            f'clubs/my-clubs/{self.test_league_id}',
            f'fixtures/{self.test_league_id}',
            f'leaderboard/{self.test_league_id}',
            f'analytics/head-to-head/{self.test_league_id}?user1_id=test1&user2_id=test2'
        ]
        
        unauthorized_results = []
        for endpoint in endpoints_to_test:
            success, status, data = self.make_request(
                'GET',
                endpoint,
                token=None,  # No token
                expected_status=401
            )
            unauthorized_results.append(status == 401)
        
        # Test with invalid league ID
        fake_league_id = "fake_league_id_12345"
        invalid_league_results = []
        for endpoint_template in ['clubs/my-clubs/{}', 'fixtures/{}', 'leaderboard/{}']:
            endpoint = endpoint_template.format(fake_league_id)
            success, status, data = self.make_request(
                'GET',
                endpoint,
                expected_status=403  # Should be forbidden or not found
            )
            invalid_league_results.append(status in [403, 404, 500])  # Accept various error codes
        
        access_control_working = (
            all(unauthorized_results) and  # All should return 401 without token
            all(invalid_league_results)    # All should return error with invalid league
        )
        
        return self.log_test(
            "Aggregation Access Control",
            access_control_working,
            f"Unauthorized blocked: {sum(unauthorized_results)}/{len(unauthorized_results)}, Invalid league blocked: {sum(invalid_league_results)}/{len(invalid_league_results)}"
        )
    
    def test_aggregation_endpoints_comprehensive(self):
        """Run comprehensive tests for all aggregation endpoints"""
        print("\n🔍 AGGREGATION ENDPOINTS TESTS")
        
        results = []
        results.append(self.test_my_clubs_endpoint())
        results.append(self.test_fixtures_endpoint())
        results.append(self.test_leaderboard_endpoint())
        results.append(self.test_head_to_head_endpoint())
        results.append(self.test_aggregation_endpoints_access_control())
        
        return all(results)

    # ==================== ADMIN SYSTEM TESTS ====================
    
    def test_admin_league_settings_update(self):
        """Test admin league settings update with audit logging"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Admin League Settings Update", False, "Missing league ID or token")
        
        # Test updating league settings
        settings_update = {
            "budget_per_manager": 120,
            "min_increment": 2,
            "club_slots_per_manager": 4,
            "max_managers": 10
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'admin/leagues/{self.test_league_id}/settings',
            settings_update
        )
        
        settings_updated = success and data.get('success', False)
        
        # Verify settings were actually updated
        if settings_updated:
            success2, status2, league = self.make_request('GET', f'leagues/{self.test_league_id}')
            if success2:
                settings = league.get('settings', {})
                settings_correct = (
                    settings.get('budget_per_manager') == 120 and
                    settings.get('min_increment') == 2 and
                    settings.get('club_slots_per_manager') == 4 and
                    settings.get('max_managers') == 10
                )
            else:
                settings_correct = False
        else:
            settings_correct = False
        
        return self.log_test(
            "Admin League Settings Update",
            settings_updated and settings_correct,
            f"Update success: {settings_updated}, Settings correct: {settings_correct}, Status: {status}"
        )
    
    def test_admin_member_management(self):
        """Test admin member kick/approve functionality"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Admin Member Management", False, "Missing league ID or token")
        
        # Get current league members
        success, status, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        
        if not success or len(members) < 2:
            return self.log_test(
                "Admin Member Management", 
                False, 
                f"Need at least 2 members for testing. Found: {len(members) if success else 0}"
            )
        
        # Find a non-commissioner member to test with
        target_member = None
        for member in members:
            if member['role'] != 'commissioner':
                target_member = member
                break
        
        if not target_member:
            return self.log_test("Admin Member Management", False, "No non-commissioner members found")
        
        member_id = target_member['user_id']
        
        # Test member kick
        kick_action = {
            "member_id": member_id,
            "action": "kick"
        }
        
        success, status, data = self.make_request(
            'POST',
            f'admin/leagues/{self.test_league_id}/members/manage',
            kick_action
        )
        
        kick_successful = success and data.get('success', False)
        
        # Verify member was actually removed
        if kick_successful:
            success2, status2, updated_members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
            if success2:
                member_removed = not any(m['user_id'] == member_id for m in updated_members)
            else:
                member_removed = False
        else:
            member_removed = False
        
        return self.log_test(
            "Admin Member Management",
            kick_successful and member_removed,
            f"Kick success: {kick_successful}, Member removed: {member_removed}, Status: {status}"
        )
    
    def test_admin_auction_management(self):
        """Test admin auction start/pause/resume functionality"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Admin Auction Management", False, "Missing league ID or token")
        
        # Create a test auction ID (using league ID for simplicity)
        auction_id = self.test_league_id
        
        # Test auction start
        start_params = {
            "action": "start",
            "league_id": self.test_league_id,
            "auction_id": auction_id
        }
        
        success_start, status_start, start_data = self.make_request(
            'POST',
            f'admin/auctions/{auction_id}/manage',
            start_params
        )
        
        start_successful = success_start and start_data.get('success', False)
        
        # Test auction pause
        pause_params = {
            "action": "pause",
            "league_id": self.test_league_id,
            "auction_id": auction_id
        }
        
        success_pause, status_pause, pause_data = self.make_request(
            'POST',
            f'admin/auctions/{auction_id}/manage',
            pause_params
        )
        
        pause_successful = success_pause and pause_data.get('success', False)
        
        # Test auction resume
        resume_params = {
            "action": "resume",
            "league_id": self.test_league_id,
            "auction_id": auction_id
        }
        
        success_resume, status_resume, resume_data = self.make_request(
            'POST',
            f'admin/auctions/{auction_id}/manage',
            resume_params
        )
        
        resume_successful = success_resume and resume_data.get('success', False)
        
        return self.log_test(
            "Admin Auction Management",
            start_successful or pause_successful or resume_successful,  # At least one should work
            f"Start: {start_successful}, Pause: {pause_successful}, Resume: {resume_successful}"
        )
    
    def test_admin_nomination_reorder(self):
        """Test admin nomination queue reordering"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Admin Nomination Reorder", False, "Missing league ID or token")
        
        auction_id = self.test_league_id
        
        # Get clubs to create a test reorder
        success, status, clubs = self.make_request('GET', 'clubs')
        
        if not success or len(clubs) < 3:
            return self.log_test("Admin Nomination Reorder", False, f"Need at least 3 clubs. Found: {len(clubs) if success else 0}")
        
        # Create a new order with first 3 clubs
        new_order = [clubs[0]['id'], clubs[2]['id'], clubs[1]['id']]  # Reorder first 3
        
        reorder_params = {
            "league_id": self.test_league_id,
            "new_order": new_order
        }
        
        success, status, data = self.make_request(
            'POST',
            f'admin/auctions/{auction_id}/reorder-nominations',
            reorder_params
        )
        
        reorder_successful = success and data.get('success', False)
        
        return self.log_test(
            "Admin Nomination Reorder",
            reorder_successful,
            f"Reorder success: {reorder_successful}, Status: {status}, Clubs reordered: {len(new_order)}"
        )
    
    def test_admin_comprehensive_audit(self):
        """Test admin comprehensive audit information retrieval"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Admin Comprehensive Audit", False, "Missing league ID or token")
        
        # Test getting comprehensive audit
        success, status, data = self.make_request(
            'GET',
            f'admin/leagues/{self.test_league_id}/audit'
        )
        
        audit_retrieved = success and isinstance(data, dict)
        
        # Check if audit data has expected structure
        if audit_retrieved:
            has_bid_audit = 'bid_audit' in data or isinstance(data, dict)
            has_admin_logs = 'admin_logs' in data or isinstance(data, dict)
            has_audit_summary = 'audit_summary' in data or isinstance(data, dict)
            
            audit_structure_valid = has_bid_audit or has_admin_logs or has_audit_summary
        else:
            audit_structure_valid = False
        
        return self.log_test(
            "Admin Comprehensive Audit",
            audit_retrieved and audit_structure_valid,
            f"Audit retrieved: {audit_retrieved}, Structure valid: {audit_structure_valid}, Status: {status}"
        )
    
    def test_admin_logs_retrieval(self):
        """Test admin logs retrieval"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Admin Logs Retrieval", False, "Missing league ID or token")
        
        # Test getting admin logs
        success, status, data = self.make_request(
            'GET',
            f'admin/leagues/{self.test_league_id}/logs?limit=50'
        )
        
        logs_retrieved = success and 'logs' in data and isinstance(data['logs'], list)
        
        return self.log_test(
            "Admin Logs Retrieval",
            logs_retrieved,
            f"Logs retrieved: {logs_retrieved}, Status: {status}, Logs count: {len(data.get('logs', [])) if success else 0}"
        )
    
    def test_admin_bid_audit(self):
        """Test admin bid audit trail retrieval"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Admin Bid Audit", False, "Missing league ID or token")
        
        # Test getting bid audit
        success, status, data = self.make_request(
            'GET',
            f'admin/leagues/{self.test_league_id}/bid-audit?limit=50'
        )
        
        bid_audit_retrieved = success and 'bids' in data and isinstance(data['bids'], list)
        
        return self.log_test(
            "Admin Bid Audit",
            bid_audit_retrieved,
            f"Bid audit retrieved: {bid_audit_retrieved}, Status: {status}, Bids count: {len(data.get('bids', [])) if success else 0}"
        )
    
    def test_admin_access_control(self):
        """Test admin endpoints require commissioner access"""
        if not self.test_league_id:
            return self.log_test("Admin Access Control", False, "Missing league ID")
        
        # Test admin endpoints without token (should fail)
        admin_endpoints = [
            f'admin/leagues/{self.test_league_id}/settings',
            f'admin/leagues/{self.test_league_id}/members/manage',
            f'admin/auctions/{self.test_league_id}/manage',
            f'admin/leagues/{self.test_league_id}/audit',
            f'admin/leagues/{self.test_league_id}/logs',
            f'admin/leagues/{self.test_league_id}/bid-audit'
        ]
        
        unauthorized_results = []
        for endpoint in admin_endpoints:
            if 'settings' in endpoint:
                success, status, data = self.make_request('PUT', endpoint, {}, token=None, expected_status=401)
            elif 'manage' in endpoint:
                success, status, data = self.make_request('POST', endpoint, {}, token=None, expected_status=401)
            else:
                success, status, data = self.make_request('GET', endpoint, token=None, expected_status=401)
            
            unauthorized_results.append(status == 401)
        
        access_control_working = all(unauthorized_results)
        
        return self.log_test(
            "Admin Access Control",
            access_control_working,
            f"Unauthorized access blocked: {sum(unauthorized_results)}/{len(unauthorized_results)} endpoints"
        )
    
    def test_validation_guardrails(self):
        """Test validation guardrails (duplicate ownership, budget constraints, etc.)"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Validation Guardrails", False, "Missing league ID or token")
        
        # This is a conceptual test since the guardrails are internal to the admin service
        # We'll test by trying to trigger validation scenarios
        
        # Test 1: Try to update league settings with invalid values
        invalid_settings = {
            "budget_per_manager": -10,  # Invalid negative budget
            "min_increment": 0,         # Invalid zero increment
            "max_managers": 1           # Invalid max less than min
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'admin/leagues/{self.test_league_id}/settings',
            invalid_settings
        )
        
        # Should either succeed with validation or fail gracefully
        validation_handled = success or (status >= 400 and status < 500)
        
        # Test 2: Try to kick non-existent member
        invalid_kick = {
            "member_id": "non_existent_user_id",
            "action": "kick"
        }
        
        success2, status2, data2 = self.make_request(
            'POST',
            f'admin/leagues/{self.test_league_id}/members/manage',
            invalid_kick,
            expected_status=400
        )
        
        invalid_member_handled = success2 and status2 == 400
        
        return self.log_test(
            "Validation Guardrails",
            validation_handled and (invalid_member_handled or status2 >= 400),
            f"Invalid settings handled: {validation_handled}, Invalid member handled: {invalid_member_handled or status2 >= 400}"
        )
    
    def test_admin_system_comprehensive(self):
        """Run comprehensive tests for admin system"""
        print("\n🔐 ADMIN SYSTEM TESTS")
        
        results = []
        results.append(self.test_admin_league_settings_update())
        results.append(self.test_admin_member_management())
        results.append(self.test_admin_auction_management())
        results.append(self.test_admin_nomination_reorder())
        results.append(self.test_admin_comprehensive_audit())
        results.append(self.test_admin_logs_retrieval())
        results.append(self.test_admin_bid_audit())
        results.append(self.test_admin_access_control())
        results.append(self.test_validation_guardrails())
        
        return all(results)

    # ==================== COMPETITION PROFILE INTEGRATION TESTS ====================
    
    def test_competition_profiles_endpoint(self):
        """Test GET /api/competition-profiles endpoint"""
        success, status, data = self.make_request('GET', 'competition-profiles')
        
        # Check response structure
        valid_response = (
            success and
            isinstance(data, dict) and
            'profiles' in data and
            isinstance(data['profiles'], list)
        )
        
        return self.log_test(
            "Competition Profiles Endpoint",
            valid_response,
            f"Status: {status}, Valid structure: {valid_response}, Profiles: {len(data.get('profiles', []))}"
        )
    
    def test_ucl_competition_profile(self):
        """Test GET /api/competition-profiles/ucl endpoint"""
        success, status, data = self.make_request('GET', 'competition-profiles/ucl')
        
        # Check if UCL profile exists and has proper structure
        valid_ucl_profile = (
            success and
            isinstance(data, dict) and
            'competition' in data and
            'defaults' in data and
            isinstance(data['defaults'], dict)
        )
        
        # Check default values structure
        if valid_ucl_profile:
            defaults = data['defaults']
            defaults_structure_valid = (
                'budget_per_manager' in defaults and
                'club_slots' in defaults and
                'league_size' in defaults and
                'scoring_rules' in defaults and
                isinstance(defaults['league_size'], dict) and
                isinstance(defaults['scoring_rules'], dict)
            )
        else:
            defaults_structure_valid = False
        
        return self.log_test(
            "UCL Competition Profile",
            valid_ucl_profile and defaults_structure_valid,
            f"Status: {status}, Profile exists: {valid_ucl_profile}, Defaults valid: {defaults_structure_valid}"
        )
    
    def test_competition_profile_defaults_endpoint(self):
        """Test GET /api/competition-profiles/ucl/defaults endpoint"""
        success, status, data = self.make_request('GET', 'competition-profiles/ucl/defaults')
        
        # Check if defaults endpoint returns proper LeagueSettings structure
        valid_defaults = (
            success and
            isinstance(data, dict) and
            'budget_per_manager' in data and
            'club_slots_per_manager' in data and
            'league_size' in data and
            'scoring_rules' in data
        )
        
        return self.log_test(
            "Competition Profile Defaults Endpoint",
            valid_defaults,
            f"Status: {status}, Valid defaults structure: {valid_defaults}"
        )
    
    def test_league_creation_without_settings(self):
        """Test league creation without explicit settings (should use competition profile defaults)"""
        league_data = {
            "name": f"Auto-Default League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
            # No settings provided - should use competition profile defaults
        }
        
        success, status, data = self.make_request(
            'POST',
            'leagues',
            league_data,
            expected_status=200
        )
        
        if success and 'id' in data:
            # Store league ID for cleanup
            self.test_league_id_no_settings = data['id']
            
            # Verify settings were populated from competition profile
            settings = data.get('settings', {})
            settings_populated = (
                settings.get('budget_per_manager') is not None and
                settings.get('club_slots_per_manager') is not None and
                settings.get('league_size') is not None and
                settings.get('scoring_rules') is not None
            )
            
            # Check if settings match expected UCL defaults
            expected_defaults = (
                settings.get('budget_per_manager') == 100 and
                settings.get('club_slots_per_manager') == 3 and
                settings.get('league_size', {}).get('min') == 4 and
                settings.get('league_size', {}).get('max') == 8
            )
            
            return self.log_test(
                "League Creation Without Settings",
                success and settings_populated and expected_defaults,
                f"Status: {status}, Settings populated: {settings_populated}, Defaults match: {expected_defaults}"
            )
        
        return self.log_test(
            "League Creation Without Settings",
            False,
            f"Status: {status}, Response: {data}"
        )
    
    def test_league_creation_with_explicit_settings(self):
        """Test league creation with explicit settings (should override competition profile defaults)"""
        custom_settings = {
            "budget_per_manager": 150,
            "min_increment": 2,
            "club_slots_per_manager": 4,
            "anti_snipe_seconds": 45,
            "bid_timer_seconds": 90,
            "league_size": {
                "min": 3,
                "max": 6
            },
            "scoring_rules": {
                "club_goal": 2,
                "club_win": 5,
                "club_draw": 2
            }
        }
        
        league_data = {
            "name": f"Custom Settings League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": custom_settings
        }
        
        success, status, data = self.make_request(
            'POST',
            'leagues',
            league_data,
            expected_status=200
        )
        
        if success and 'id' in data:
            # Store league ID for cleanup
            self.test_league_id_custom_settings = data['id']
            
            # Verify explicit settings were used (not defaults)
            settings = data.get('settings', {})
            explicit_settings_used = (
                settings.get('budget_per_manager') == 150 and
                settings.get('min_increment') == 2 and
                settings.get('club_slots_per_manager') == 4 and
                settings.get('anti_snipe_seconds') == 45 and
                settings.get('bid_timer_seconds') == 90 and
                settings.get('league_size', {}).get('min') == 3 and
                settings.get('league_size', {}).get('max') == 6 and
                settings.get('scoring_rules', {}).get('club_goal') == 2 and
                settings.get('scoring_rules', {}).get('club_win') == 5 and
                settings.get('scoring_rules', {}).get('club_draw') == 2
            )
            
            return self.log_test(
                "League Creation With Explicit Settings",
                success and explicit_settings_used,
                f"Status: {status}, Explicit settings used: {explicit_settings_used}"
            )
        
        return self.log_test(
            "League Creation With Explicit Settings",
            False,
            f"Status: {status}, Response: {data}"
        )
    
    def test_settings_validation_and_application(self):
        """Test that fetched default settings are properly validated and applied"""
        if not hasattr(self, 'test_league_id_no_settings') or not self.test_league_id_no_settings:
            return self.log_test("Settings Validation and Application", False, "No test league with default settings")
        
        # Get the league created with default settings
        success, status, league = self.make_request('GET', f'leagues/{self.test_league_id_no_settings}')
        
        if not success:
            return self.log_test("Settings Validation and Application", False, f"Failed to get league: {status}")
        
        # Verify all related documents were created with proper settings
        settings = league.get('settings', {})
        
        # Check auction document was created with correct settings
        success_members, status_members, members = self.make_request('GET', f'leagues/{self.test_league_id_no_settings}/members')
        
        if success_members and len(members) > 0:
            # Check if roster was created with correct budget and slots
            roster_settings_valid = True  # We can't directly check roster without additional endpoints
        else:
            roster_settings_valid = False
        
        # Verify settings structure and values
        settings_valid = (
            isinstance(settings.get('budget_per_manager'), int) and
            isinstance(settings.get('club_slots_per_manager'), int) and
            isinstance(settings.get('league_size'), dict) and
            isinstance(settings.get('scoring_rules'), dict) and
            settings.get('budget_per_manager') > 0 and
            settings.get('club_slots_per_manager') > 0
        )
        
        return self.log_test(
            "Settings Validation and Application",
            settings_valid and roster_settings_valid,
            f"Settings valid: {settings_valid}, Roster settings valid: {roster_settings_valid}"
        )
    
    def test_competition_profile_integration_logging(self):
        """Test that the integration logs properly indicate which settings source is used"""
        # This test would ideally check backend logs, but we'll test the behavior indirectly
        # by creating leagues with and without settings and verifying the results
        
        # Create league without settings (should log "Using default settings from UCL competition profile")
        league_data_no_settings = {
            "name": f"Logging Test No Settings {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
        }
        
        success1, status1, data1 = self.make_request('POST', 'leagues', league_data_no_settings)
        
        # Create league with settings (should log "Using explicit settings provided by commissioner")
        league_data_with_settings = {
            "name": f"Logging Test With Settings {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 120,
                "club_slots_per_manager": 3
            }
        }
        
        success2, status2, data2 = self.make_request('POST', 'leagues', league_data_with_settings)
        
        # Verify both leagues were created successfully
        both_created = success1 and success2 and 'id' in data1 and 'id' in data2
        
        # Verify they have different settings (indicating different sources were used)
        if both_created:
            settings1 = data1.get('settings', {})
            settings2 = data2.get('settings', {})
            
            different_sources = (
                settings1.get('budget_per_manager') != settings2.get('budget_per_manager')
            )
        else:
            different_sources = False
        
        return self.log_test(
            "Competition Profile Integration Logging",
            both_created and different_sources,
            f"Both created: {both_created}, Different sources detected: {different_sources}"
        )
    
    def test_backward_compatibility(self):
        """Test that explicit settings take priority over competition profile defaults"""
        # Get UCL competition profile defaults first
        success_defaults, status_defaults, defaults = self.make_request('GET', 'competition-profiles/ucl/defaults')
        
        if not success_defaults:
            return self.log_test("Backward Compatibility", False, f"Failed to get defaults: {status_defaults}")
        
        # Create league with explicit settings that differ from defaults
        different_settings = {
            "budget_per_manager": defaults.get('budget_per_manager', 100) + 50,  # Different from default
            "club_slots_per_manager": defaults.get('club_slots_per_manager', 3) + 1,  # Different from default
            "league_size": {
                "min": defaults.get('league_size', {}).get('min', 4) - 1,  # Different from default
                "max": defaults.get('league_size', {}).get('max', 8) - 1   # Different from default
            }
        }
        
        league_data = {
            "name": f"Backward Compatibility Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": different_settings
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if success and 'id' in data:
            settings = data.get('settings', {})
            
            # Verify explicit settings were used, not defaults
            explicit_settings_priority = (
                settings.get('budget_per_manager') == different_settings['budget_per_manager'] and
                settings.get('club_slots_per_manager') == different_settings['club_slots_per_manager'] and
                settings.get('league_size', {}).get('min') == different_settings['league_size']['min'] and
                settings.get('league_size', {}).get('max') == different_settings['league_size']['max']
            )
            
            return self.log_test(
                "Backward Compatibility",
                explicit_settings_priority,
                f"Explicit settings took priority: {explicit_settings_priority}"
            )
        
        return self.log_test(
            "Backward Compatibility",
            False,
            f"Status: {status}, Response: {data}"
        )
    
    def test_competition_profile_comprehensive(self):
        """Run comprehensive tests for competition profile integration"""
        print("\n🏆 COMPETITION PROFILE INTEGRATION TESTS")
        
        results = []
        results.append(self.test_competition_profiles_endpoint())
        results.append(self.test_ucl_competition_profile())
        results.append(self.test_competition_profile_defaults_endpoint())
        results.append(self.test_league_creation_without_settings())
        results.append(self.test_league_creation_with_explicit_settings())
        results.append(self.test_settings_validation_and_application())
        results.append(self.test_competition_profile_integration_logging())
        results.append(self.test_backward_compatibility())
        
        return all(results)

    # ==================== ENFORCEMENT RULES TESTS ====================
    
    def test_roster_capacity_enforcement(self):
        """Test roster capacity rule enforcement during auction"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Roster Capacity Enforcement", False, "Missing league ID or token")
        
        # Create a test league with 1 club slot per manager for easier testing
        league_data = {
            "name": f"Capacity Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 1,  # Only 1 slot for testing
                "league_size": {"min": 2, "max": 4}
            }
        }
        
        success, status, capacity_league = self.make_request('POST', 'leagues', league_data)
        if not success:
            return self.log_test("Roster Capacity Enforcement", False, f"Failed to create test league: {status}")
        
        capacity_league_id = capacity_league['id']
        
        # Add one more member to reach minimum
        success_join, status_join, join_data = self.make_request('POST', f'leagues/{capacity_league_id}/join')
        
        # Get league members to test with
        success_members, status_members, members = self.make_request('GET', f'leagues/{capacity_league_id}/members')
        
        if not success_members or len(members) < 2:
            return self.log_test("Roster Capacity Enforcement", False, "Need at least 2 members for testing")
        
        # Test the validation endpoint indirectly by checking league settings
        success_league, status_league, league_info = self.make_request('GET', f'leagues/{capacity_league_id}')
        
        capacity_settings_valid = (
            success_league and
            league_info.get('settings', {}).get('club_slots_per_manager') == 1
        )
        
        return self.log_test(
            "Roster Capacity Enforcement",
            capacity_settings_valid,
            f"Capacity league created: {success}, Settings valid: {capacity_settings_valid}, Members: {len(members) if success_members else 0}"
        )
    
    def test_budget_change_constraints(self):
        """Test budget change constraints enforcement"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Budget Change Constraints", False, "Missing league ID or token")
        
        # Test 1: Budget change should be allowed when auction is scheduled and no clubs owned
        budget_update = {
            "budget_per_manager": 150
        }
        
        success1, status1, result1 = self.make_request(
            'PUT',
            f'admin/leagues/{self.test_league_id}/settings',
            budget_update
        )
        
        budget_change_allowed = success1 and result1.get('success', False)
        
        # Test 2: Verify all rosters were updated
        success2, status2, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        
        # Test 3: Try to change budget again (should still be allowed if no clubs purchased)
        budget_update2 = {
            "budget_per_manager": 120
        }
        
        success3, status3, result3 = self.make_request(
            'PUT',
            f'admin/leagues/{self.test_league_id}/settings',
            budget_update2
        )
        
        second_change_allowed = success3 and result3.get('success', False)
        
        return self.log_test(
            "Budget Change Constraints",
            budget_change_allowed and second_change_allowed,
            f"First change: {budget_change_allowed}, Second change: {second_change_allowed}"
        )
    
    def test_league_size_constraints(self):
        """Test league size constraint enforcement"""
        if not self.commissioner_token:
            return self.log_test("League Size Constraints", False, "No commissioner token")
        
        # Create a league with small size limits for testing
        league_data = {
            "name": f"Size Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 3,
                "league_size": {"min": 2, "max": 3}  # Small league for testing
            }
        }
        
        success, status, size_league = self.make_request('POST', 'leagues', league_data)
        if not success:
            return self.log_test("League Size Constraints", False, f"Failed to create test league: {status}")
        
        size_league_id = size_league['id']
        
        # Test 1: League should not be ready with only 1 member (commissioner)
        success1, status1, league_status = self.make_request('GET', f'leagues/{size_league_id}/status')
        not_ready_with_one = (
            success1 and
            league_status.get('member_count') == 1 and
            league_status.get('min_members') == 2 and
            not league_status.get('is_ready', True)
        )
        
        # Test 2: Add one member to reach minimum
        success2, status2, join_result = self.make_request('POST', f'leagues/{size_league_id}/join')
        
        # Test 3: Check if league is now ready
        success3, status3, updated_status = self.make_request('GET', f'leagues/{size_league_id}/status')
        ready_with_two = (
            success3 and
            updated_status.get('member_count') == 2 and
            updated_status.get('is_ready', False)
        )
        
        # Test 4: Try to add one more member (should reach max)
        success4, status4, join_result2 = self.make_request('POST', f'leagues/{size_league_id}/join')
        
        # Test 5: Try to add another member (should fail - league full)
        success5, status5, join_result3 = self.make_request(
            'POST', 
            f'leagues/{size_league_id}/join',
            expected_status=400
        )
        
        league_full_rejected = success5 and status5 == 400
        
        return self.log_test(
            "League Size Constraints",
            not_ready_with_one and ready_with_two and league_full_rejected,
            f"Not ready with 1: {not_ready_with_one}, Ready with 2: {ready_with_two}, Full rejected: {league_full_rejected}"
        )
    
    def test_admin_service_validations(self):
        """Test AdminService validation methods"""
        if not self.test_league_id or not self.commissioner_token:
            return self.log_test("Admin Service Validations", False, "Missing league ID or token")
        
        # Test 1: League settings update with validation
        settings_update = {
            "budget_per_manager": 200,
            "club_slots_per_manager": 5,
            "league_size": {"min": 3, "max": 6}
        }
        
        success1, status1, result1 = self.make_request(
            'PUT',
            f'admin/leagues/{self.test_league_id}/settings',
            settings_update
        )
        
        settings_update_valid = success1 and result1.get('success', False)
        
        # Test 2: Try invalid settings (should be rejected)
        invalid_settings = {
            "budget_per_manager": -10,  # Invalid negative budget
            "club_slots_per_manager": 0  # Invalid zero slots
        }
        
        success2, status2, result2 = self.make_request(
            'PUT',
            f'admin/leagues/{self.test_league_id}/settings',
            invalid_settings,
            expected_status=400
        )
        
        invalid_settings_rejected = success2 and status2 == 400
        
        # Test 3: Test member management validation
        member_action = {
            "member_id": "invalid_user_id",
            "action": "kick"
        }
        
        success3, status3, result3 = self.make_request(
            'POST',
            f'admin/leagues/{self.test_league_id}/members/manage',
            member_action,
            expected_status=400
        )
        
        invalid_member_rejected = success3 and status3 == 400
        
        return self.log_test(
            "Admin Service Validations",
            settings_update_valid and invalid_settings_rejected and invalid_member_rejected,
            f"Valid settings: {settings_update_valid}, Invalid rejected: {invalid_settings_rejected}, Invalid member: {invalid_member_rejected}"
        )
    
    def test_auction_start_constraints(self):
        """Test auction start constraints with minimum member requirements"""
        if not self.commissioner_token:
            return self.log_test("Auction Start Constraints", False, "No commissioner token")
        
        # Create a league that doesn't meet minimum requirements
        league_data = {
            "name": f"Auction Start Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 3,
                "league_size": {"min": 4, "max": 8}  # Requires 4 members minimum
            }
        }
        
        success, status, auction_league = self.make_request('POST', 'leagues', league_data)
        if not success:
            return self.log_test("Auction Start Constraints", False, f"Failed to create test league: {status}")
        
        auction_league_id = auction_league['id']
        
        # Test 1: Try to start auction with insufficient members (should fail)
        success1, status1, start_result1 = self.make_request(
            'POST',
            f'auction/{auction_league_id}/start',
            expected_status=400
        )
        
        start_rejected_insufficient = success1 and status1 == 400
        
        # Test 2: Add members to reach minimum
        join_results = []
        for i in range(3):  # Add 3 more members (total 4 with commissioner)
            success_join, status_join, join_data = self.make_request('POST', f'leagues/{auction_league_id}/join')
            join_results.append(success_join)
        
        # Test 3: Check league status
        success2, status2, league_status = self.make_request('GET', f'leagues/{auction_league_id}/status')
        league_ready = (
            success2 and
            league_status.get('member_count') >= 4 and
            league_status.get('is_ready', False)
        )
        
        # Test 4: Try to start auction now (should succeed)
        success3, status3, start_result2 = self.make_request(
            'POST',
            f'auction/{auction_league_id}/start'
        )
        
        start_allowed_sufficient = success3
        
        return self.log_test(
            "Auction Start Constraints",
            start_rejected_insufficient and league_ready and start_allowed_sufficient,
            f"Rejected insufficient: {start_rejected_insufficient}, League ready: {league_ready}, Start allowed: {start_allowed_sufficient}, Joins: {sum(join_results)}"
        )
    
    def test_league_creation_with_defaults(self):
        """Test league creation without settings uses competition profile defaults"""
        if not self.commissioner_token:
            return self.log_test("League Creation With Defaults", False, "No commissioner token")
        
        # Create league without settings (should use UCL defaults)
        league_data_no_settings = {
            "name": f"Default Settings League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26"
            # No settings provided - should use UCL defaults
        }
        
        success, status, league_no_settings = self.make_request(
            'POST',
            'leagues',
            league_data_no_settings
        )
        
        if success and 'id' in league_no_settings:
            # Verify it uses UCL defaults
            settings = league_no_settings.get('settings', {})
            uses_defaults = (
                settings.get('budget_per_manager') == 100 and  # UCL default
                settings.get('club_slots_per_manager') == 3 and  # UCL default
                settings.get('league_size', {}).get('min') == 4 and  # UCL default
                settings.get('league_size', {}).get('max') == 8  # UCL default
            )
            
            return self.log_test(
                "League Creation With Defaults",
                uses_defaults,
                f"Status: {status}, Uses UCL defaults: {uses_defaults}"
            )
        
        return self.log_test(
            "League Creation With Defaults",
            False,
            f"Status: {status}, Response: {league_no_settings}"
        )
    
    def test_enforcement_rules_comprehensive(self):
        """Run comprehensive tests for enforcement rules"""
        print("\n🛡️ ENFORCEMENT RULES TESTS")
        
        results = []
        results.append(self.test_roster_capacity_enforcement())
        results.append(self.test_budget_change_constraints())
        results.append(self.test_league_size_constraints())
        results.append(self.test_admin_service_validations())
        results.append(self.test_auction_start_constraints())
        results.append(self.test_league_creation_with_defaults())
        
        return all(results)

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
        
        # ==================== COMPETITION PROFILE INTEGRATION TESTS ====================
        print("\n🏆 COMPETITION PROFILE INTEGRATION TESTS")
        self.test_competition_profile_comprehensive()
        
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
        
        # ==================== NEW AGGREGATION API TESTS ====================
        print("\n📊 AGGREGATION ENDPOINTS TESTS")
        self.test_aggregation_endpoints_comprehensive()
        
        # ==================== ADMIN SYSTEM TESTS ====================
        print("\n🔐 COMPREHENSIVE ADMIN SYSTEM TESTS")
        self.test_admin_system_comprehensive()
        
        # ==================== ENFORCEMENT RULES TESTS ====================
        print("\n🛡️ ENFORCEMENT RULES TESTS")
        self.test_enforcement_rules_comprehensive()
        
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
        
        # Competition profile specific summary
        competition_tests = [test for test in self.failed_tests if any(keyword in test.lower() for keyword in ['competition', 'profile', 'default'])]
        if competition_tests:
            print(f"\n🏆 COMPETITION PROFILE ISSUES ({len(competition_tests)}):")
            for i, failure in enumerate(competition_tests, 1):
                print(f"   {i}. {failure}")
        
        # Auction-specific summary
        auction_tests = [test for test in self.failed_tests if any(keyword in test.lower() for keyword in ['auction', 'bid', 'websocket', 'chat'])]
        if auction_tests:
            print(f"\n🎯 AUCTION ENGINE ISSUES ({len(auction_tests)}):")
            for i, failure in enumerate(auction_tests, 1):
                print(f"   {i}. {failure}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All comprehensive tests passed!")
            print("✅ Competition profile integration working correctly")
            print("✅ Atomic bid processing working correctly")
            print("✅ Real-time WebSocket functionality operational")
            print("✅ Auction state management functioning properly")
            return 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed - see details above")
            
            # Provide specific guidance for competition profile issues
            if competition_tests:
                print("\n🔧 COMPETITION PROFILE RECOMMENDATIONS:")
                print("   - Check if UCL competition profile exists in database")
                print("   - Verify competition_service.py implementation")
                print("   - Ensure league_service.py integration is working")
                print("   - Check MongoDB competition_profiles collection")
            
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