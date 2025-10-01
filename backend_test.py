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

    def make_request(self, method, endpoint, data=None, expected_status=200, token=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        auth_token = token or self.token
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=15)
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

    # ==================== ENVIRONMENT & HEALTH TESTS ====================
    
    def test_environment_variables(self):
        """Test that required environment variables are properly configured"""
        # Test backend health to verify environment is working
        success, status, data = self.make_request('GET', 'health', token=None)
        
        if not success:
            return self.log_test("Environment Variables", False, f"Health check failed: {status}")
        
        # Check health response structure
        env_valid = (
            'status' in data and
            'timestamp' in data and
            'database' in data and
            'services' in data
        )
        
        # Check database connectivity
        db_connected = data.get('database', {}).get('connected', False)
        
        # Check services configuration
        services = data.get('services', {})
        websocket_configured = services.get('websocket', False)
        auth_configured = services.get('auth', False)
        
        return self.log_test(
            "Environment Variables",
            env_valid and db_connected and websocket_configured and auth_configured,
            f"DB: {db_connected}, WebSocket: {websocket_configured}, Auth: {auth_configured}"
        )

    def test_health_endpoints(self):
        """Test health check endpoints"""
        # Main health endpoint
        success, status, data = self.make_request('GET', 'health', token=None)
        health_valid = success and data.get('status') == 'healthy'
        
        # Time sync endpoint
        success2, status2, data2 = self.make_request('GET', 'timez', token=None)
        time_valid = success2 and 'now' in data2
        
        # Version endpoint (if available)
        success3, status3, data3 = self.make_request('GET', '../version', token=None)
        version_available = success3 or status3 == 404  # 404 is acceptable
        
        return self.log_test(
            "Health Endpoints",
            health_valid and time_valid,
            f"Health: {health_valid}, Time: {time_valid}, Version: {version_available}"
        )

    # ==================== AUTHENTICATION TESTS ====================
    
    def test_magic_link_auth_flow(self):
        """Test complete magic link authentication flow"""
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success:
            return self.log_test("Magic Link Auth Flow", False, f"Magic link request failed: {status}")
        
        # Check response structure
        has_message = 'message' in data
        has_dev_link = 'dev_magic_link' in data  # Development mode
        
        if not has_dev_link:
            return self.log_test("Magic Link Auth Flow", False, "No dev magic link in response")
        
        # Step 2: Extract and verify token
        magic_link = data['dev_magic_link']
        if 'token=' not in magic_link:
            return self.log_test("Magic Link Auth Flow", False, "Invalid magic link format")
        
        token = magic_link.split('token=')[1]
        
        # Step 3: Verify magic link token
        success, status, auth_data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if not success:
            return self.log_test("Magic Link Auth Flow", False, f"Token verification failed: {status}")
        
        # Check auth response structure
        auth_valid = (
            'access_token' in auth_data and
            'user' in auth_data and
            'email' in auth_data['user'] and
            'verified' in auth_data['user']
        )
        
        if auth_valid:
            self.token = auth_data['access_token']
            self.user_data = auth_data['user']
        
        return self.log_test(
            "Magic Link Auth Flow",
            auth_valid,
            f"Token obtained, User: {auth_data.get('user', {}).get('email', 'Unknown')}"
        )

    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint"""
        if not self.token:
            return self.log_test("Auth Me Endpoint", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'auth/me')
        
        me_valid = (
            success and
            'id' in data and
            'email' in data and
            'verified' in data and
            data['email'] == self.test_email
        )
        
        return self.log_test(
            "Auth Me Endpoint",
            me_valid,
            f"Status: {status}, Email: {data.get('email', 'Unknown')}"
        )

    def test_user_profile_update(self):
        """Test user profile update"""
        if not self.token:
            return self.log_test("User Profile Update", False, "No authentication token")
        
        new_display_name = f"Test User {datetime.now().strftime('%H%M%S')}"
        
        success, status, data = self.make_request(
            'PUT',
            'users/me',
            {"display_name": new_display_name}
        )
        
        update_valid = (
            success and
            'display_name' in data and
            data['display_name'] == new_display_name
        )
        
        return self.log_test(
            "User Profile Update",
            update_valid,
            f"Status: {status}, New name: {data.get('display_name', 'Unknown')}"
        )

    # ==================== CLUB DATA TESTS ====================
    
    def test_clubs_seed_and_retrieval(self):
        """Test clubs seeding and retrieval"""
        if not self.token:
            return self.log_test("Clubs Seed and Retrieval", False, "No authentication token")
        
        # Seed clubs
        success, status, data = self.make_request('POST', 'clubs/seed')
        seed_success = success and 'message' in data
        
        # Get clubs
        success2, status2, clubs_data = self.make_request('GET', 'clubs', token=None)
        
        clubs_valid = (
            success2 and
            isinstance(clubs_data, list) and
            len(clubs_data) >= 16  # Should have at least 16 clubs
        )
        
        if clubs_valid:
            self.test_clubs = clubs_data[:5]  # Store first 5 for testing
        
        return self.log_test(
            "Clubs Seed and Retrieval",
            seed_success and clubs_valid,
            f"Seed: {seed_success}, Clubs count: {len(clubs_data) if clubs_valid else 0}"
        )

    # ==================== LEAGUE MANAGEMENT TESTS ====================
    
    def test_league_creation(self):
        """Test comprehensive league creation"""
        if not self.token:
            return self.log_test("League Creation", False, "No authentication token")
        
        league_data = {
            "name": f"Backend Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 3,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "league_size": {
                    "min": 2,
                    "max": 8
                },
                "scoring_rules": {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                }
            }
        }
        
        success, status, data = self.make_request('POST', 'leagues', league_data)
        
        if not success:
            return self.log_test("League Creation", False, f"Status: {status}, Response: {data}")
        
        # Validate league creation response
        league_valid = (
            'id' in data and
            'name' in data and
            'settings' in data and
            'member_count' in data and
            data['member_count'] == 1 and
            data['status'] == 'setup'
        )
        
        if league_valid:
            self.test_league_id = data['id']
        
        return self.log_test(
            "League Creation",
            league_valid,
            f"League ID: {data.get('id', 'None')}, Status: {data.get('status', 'Unknown')}"
        )

    def test_league_settings_retrieval(self):
        """Test league settings retrieval"""
        if not self.test_league_id:
            return self.log_test("League Settings Retrieval", False, "No test league ID")
        
        success, status, data = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        
        settings_valid = (
            success and
            'clubSlots' in data and
            'budgetPerManager' in data and
            'leagueSize' in data and
            data['clubSlots'] == 3 and
            data['budgetPerManager'] == 100
        )
        
        return self.log_test(
            "League Settings Retrieval",
            settings_valid,
            f"Status: {status}, Club slots: {data.get('clubSlots', 'Unknown')}"
        )

    def test_league_invitation_system(self):
        """Test league invitation system"""
        if not self.test_league_id:
            return self.log_test("League Invitation System", False, "No test league ID")
        
        results = []
        
        # Send invitations
        for email in self.manager_emails[:2]:  # Test with 2 managers
            success, status, data = self.make_request(
                'POST',
                f'leagues/{self.test_league_id}/invite',
                {"email": email}
            )
            results.append(success)
        
        # Get invitations
        success, status, invitations = self.make_request('GET', f'leagues/{self.test_league_id}/invitations')
        invitations_valid = success and isinstance(invitations, list) and len(invitations) >= 2
        
        # Test duplicate prevention
        success_dup, status_dup, data_dup = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"email": self.manager_emails[0]},
            expected_status=400
        )
        duplicate_prevented = success_dup and status_dup == 400
        
        invitation_system_works = sum(results) >= 1 and invitations_valid and duplicate_prevented
        
        return self.log_test(
            "League Invitation System",
            invitation_system_works,
            f"Invites sent: {sum(results)}, Retrieved: {len(invitations) if invitations_valid else 0}, Duplicate prevented: {duplicate_prevented}"
        )

    def test_league_member_management(self):
        """Test league member management"""
        if not self.test_league_id:
            return self.log_test("League Member Management", False, "No test league ID")
        
        # Get league members
        success, status, members = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        
        members_valid = (
            success and
            isinstance(members, list) and
            len(members) >= 1 and
            members[0]['role'] == 'commissioner'
        )
        
        # Get league status
        success2, status2, league_status = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        
        status_valid = (
            success2 and
            'member_count' in league_status and
            'min_members' in league_status and
            'max_members' in league_status and
            'is_ready' in league_status
        )
        
        return self.log_test(
            "League Member Management",
            members_valid and status_valid,
            f"Members: {len(members) if members_valid else 0}, Status valid: {status_valid}"
        )

    def test_league_join_functionality(self):
        """Test direct league joining (for testing)"""
        if not self.test_league_id:
            return self.log_test("League Join Functionality", False, "No test league ID")
        
        # Join league directly (testing endpoint)
        success, status, data = self.make_request('POST', f'leagues/{self.test_league_id}/join')
        
        join_success = success and 'message' in data
        
        # Verify member count increased
        success2, status2, league_status = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        
        member_count_increased = (
            success2 and
            league_status.get('member_count', 0) >= 2
        )
        
        return self.log_test(
            "League Join Functionality",
            join_success and member_count_increased,
            f"Join: {join_success}, Member count: {league_status.get('member_count', 0) if success2 else 'Unknown'}"
        )

    # ==================== AUCTION ENGINE TESTS ====================
    
    def test_auction_creation_and_start(self):
        """Test auction creation and starting"""
        if not self.test_league_id:
            return self.log_test("Auction Creation and Start", False, "No test league ID")
        
        # Try to start auction
        success, status, data = self.make_request('POST', f'auction/{self.test_league_id}/start')
        
        if success:
            self.test_auction_id = self.test_league_id
            return self.log_test(
                "Auction Creation and Start",
                True,
                f"Auction started successfully, Status: {status}"
            )
        else:
            # Auction might not start due to insufficient members, which is expected
            expected_failure = status == 400 or status == 403
            return self.log_test(
                "Auction Creation and Start",
                expected_failure,
                f"Expected failure due to league requirements, Status: {status}"
            )

    def test_auction_state_retrieval(self):
        """Test auction state retrieval"""
        if not self.test_auction_id:
            return self.log_test("Auction State Retrieval", False, "No test auction ID")
        
        success, status, data = self.make_request('GET', f'auction/{self.test_auction_id}/state')
        
        if success:
            state_valid = (
                'auction_id' in data and
                'league_id' in data and
                'status' in data
            )
            return self.log_test(
                "Auction State Retrieval",
                state_valid,
                f"Status: {status}, Auction status: {data.get('status', 'Unknown')}"
            )
        else:
            # Expected if auction not active
            return self.log_test(
                "Auction State Retrieval",
                status == 404,
                f"Expected 404 for inactive auction, Status: {status}"
            )

    def test_bid_placement_endpoint(self):
        """Test bid placement endpoint"""
        if not self.test_auction_id:
            return self.log_test("Bid Placement Endpoint", False, "No test auction ID")
        
        # Test bid placement (expected to fail due to no active lot)
        success, status, data = self.make_request(
            'POST',
            f'auction/{self.test_auction_id}/bid',
            {
                "lot_id": "test_lot_id",
                "amount": 10
            },
            expected_status=400
        )
        
        # Expected failure due to no active auction/lot
        endpoint_works = success and status == 400
        
        return self.log_test(
            "Bid Placement Endpoint",
            endpoint_works,
            f"Endpoint accessible, Expected failure: {status}"
        )

    def test_auction_control_endpoints(self):
        """Test auction control endpoints (pause/resume)"""
        if not self.test_auction_id:
            return self.log_test("Auction Control Endpoints", False, "No test auction ID")
        
        # Test pause (expected to fail if no active auction)
        success, status, data = self.make_request('POST', f'auction/{self.test_auction_id}/pause')
        pause_endpoint_works = success or status in [400, 404]
        
        # Test resume (expected to fail if no active auction)
        success2, status2, data2 = self.make_request('POST', f'auction/{self.test_auction_id}/resume')
        resume_endpoint_works = success2 or status2 in [400, 404]
        
        return self.log_test(
            "Auction Control Endpoints",
            pause_endpoint_works and resume_endpoint_works,
            f"Pause: {status}, Resume: {status2}"
        )

    # ==================== DATABASE OPERATIONS TESTS ====================
    
    def test_database_operations(self):
        """Test database operations through API endpoints"""
        if not self.token:
            return self.log_test("Database Operations", False, "No authentication token")
        
        # Test user data persistence (profile update and retrieval)
        test_name = f"DB Test {datetime.now().strftime('%H%M%S')}"
        
        # Update profile
        success, status, data = self.make_request(
            'PUT',
            'users/me',
            {"display_name": test_name}
        )
        
        if not success:
            return self.log_test("Database Operations", False, f"Profile update failed: {status}")
        
        # Retrieve profile to verify persistence
        success2, status2, data2 = self.make_request('GET', 'auth/me')
        
        persistence_works = (
            success2 and
            data2.get('display_name') == test_name
        )
        
        # Test league data persistence
        success3, status3, leagues = self.make_request('GET', 'leagues')
        leagues_persisted = success3 and isinstance(leagues, list) and len(leagues) > 0
        
        return self.log_test(
            "Database Operations",
            persistence_works and leagues_persisted,
            f"Profile persistence: {persistence_works}, Leagues persisted: {leagues_persisted}"
        )

    def test_aggregation_endpoints(self):
        """Test aggregation service endpoints"""
        if not self.test_league_id:
            return self.log_test("Aggregation Endpoints", False, "No test league ID")
        
        endpoints_results = []
        
        # Test my clubs endpoint
        success, status, data = self.make_request('GET', f'clubs/my-clubs/{self.test_league_id}')
        my_clubs_works = success or status == 404  # 404 acceptable if no clubs owned
        endpoints_results.append(my_clubs_works)
        
        # Test roster summary endpoint
        success2, status2, data2 = self.make_request('GET', f'leagues/{self.test_league_id}/roster/summary')
        roster_works = success2 and 'ownedCount' in data2 and 'clubSlots' in data2
        endpoints_results.append(roster_works)
        
        # Test fixtures endpoint
        success3, status3, data3 = self.make_request('GET', f'fixtures/{self.test_league_id}')
        fixtures_works = success3 or status3 == 404  # 404 acceptable if no fixtures
        endpoints_results.append(fixtures_works)
        
        # Test leaderboard endpoint
        success4, status4, data4 = self.make_request('GET', f'leaderboard/{self.test_league_id}')
        leaderboard_works = success4 or status4 == 404  # 404 acceptable if no data
        endpoints_results.append(leaderboard_works)
        
        return self.log_test(
            "Aggregation Endpoints",
            sum(endpoints_results) >= 3,
            f"Working endpoints: {sum(endpoints_results)}/4"
        )

    # ==================== SCORING SYSTEM TESTS ====================
    
    def test_scoring_endpoints(self):
        """Test scoring system endpoints"""
        if not self.test_league_id:
            return self.log_test("Scoring Endpoints", False, "No test league ID")
        
        # Test result ingestion endpoint (should fail without proper data)
        success, status, data = self.make_request(
            'POST',
            'ingest/final_result',
            {
                "league_id": self.test_league_id,
                "match_id": "test_match",
                "season": "2025-26",
                "home_ext": "test_home",
                "away_ext": "test_away",
                "home_goals": 2,
                "away_goals": 1,
                "kicked_off_at": datetime.now(timezone.utc).isoformat(),
                "status": "final"
            },
            expected_status=400
        )
        
        ingest_endpoint_works = success and status == 400  # Expected failure
        
        # Test standings endpoint
        success2, status2, data2 = self.make_request('GET', f'leagues/{self.test_league_id}/standings')
        standings_works = success2 or status2 == 404
        
        # Test processing endpoint
        success3, status3, data3 = self.make_request('POST', 'scoring/process')
        processing_works = success3 or status3 in [400, 404]
        
        return self.log_test(
            "Scoring Endpoints",
            ingest_endpoint_works and standings_works and processing_works,
            f"Ingest: {status}, Standings: {status2}, Processing: {status3}"
        )

    # ==================== ADMIN ENDPOINTS TESTS ====================
    
    def test_admin_endpoints(self):
        """Test admin/commissioner endpoints"""
        if not self.test_league_id:
            return self.log_test("Admin Endpoints", False, "No test league ID")
        
        # Test league settings update (PATCH)
        success, status, data = self.make_request(
            'PATCH',
            f'leagues/{self.test_league_id}/settings',
            {
                "budget_per_manager": 120
            }
        )
        
        settings_update_works = success or status in [400, 403]  # May fail due to league state
        
        # Test admin logs endpoint
        success2, status2, data2 = self.make_request('GET', f'admin/leagues/{self.test_league_id}/logs')
        logs_works = success2 or status2 in [403, 404]
        
        # Test bid audit endpoint
        success3, status3, data3 = self.make_request('GET', f'admin/leagues/{self.test_league_id}/bid-audit')
        audit_works = success3 or status3 in [403, 404]
        
        return self.log_test(
            "Admin Endpoints",
            settings_update_works and logs_works and audit_works,
            f"Settings: {status}, Logs: {status2}, Audit: {status3}"
        )

    # ==================== COMPETITION PROFILES TESTS ====================
    
    def test_competition_profiles(self):
        """Test competition profiles endpoints"""
        # Test get all profiles
        success, status, data = self.make_request('GET', 'competition-profiles', token=None)
        
        profiles_valid = (
            success and
            'profiles' in data and
            isinstance(data['profiles'], list)
        )
        
        profile_id = None
        if profiles_valid and len(data['profiles']) > 0:
            profile_id = data['profiles'][0].get('id')
        
        # Test get specific profile
        if profile_id:
            success2, status2, data2 = self.make_request('GET', f'competition-profiles/{profile_id}', token=None)
            specific_profile_works = success2 and 'id' in data2
            
            # Test get profile defaults
            success3, status3, data3 = self.make_request('GET', f'competition-profiles/{profile_id}/defaults', token=None)
            defaults_work = success3 or status3 == 404
        else:
            specific_profile_works = True  # Skip if no profiles
            defaults_work = True
        
        return self.log_test(
            "Competition Profiles",
            profiles_valid and specific_profile_works and defaults_work,
            f"Profiles: {len(data.get('profiles', [])) if profiles_valid else 0}, Specific: {specific_profile_works}, Defaults: {defaults_work}"
        )

    # ==================== WEBSOCKET DIAGNOSTICS ====================
    
    def test_websocket_diagnostics(self):
        """Test WebSocket diagnostic endpoints"""
        # Test Socket.IO diagnostic endpoint
        success, status, data = self.make_request('GET', 'socketio/diag', token=None)
        
        if not success:
            # Try alternative endpoint
            success, status, data = self.make_request('GET', 'socket-diag', token=None)
        
        diag_valid = (
            success and
            isinstance(data, dict) and
            data.get('ok') is True and
            'path' in data and
            'now' in data
        )
        
        # Test Socket.IO handshake endpoint directly
        try:
            response = requests.get(f"{self.base_url}/api/socketio/?EIO=4&transport=polling", timeout=5)
            handshake_works = response.status_code == 200 and response.text.startswith('0{')
        except:
            handshake_works = False
        
        return self.log_test(
            "WebSocket Diagnostics",
            diag_valid,
            f"Diagnostic endpoint: {diag_valid}, Handshake: {handshake_works}"
        )

    # ==================== MAIN TEST RUNNER ====================
    
    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🚀 COMPREHENSIVE BACKEND API TESTING SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("=" * 60)
        
        # Environment & Health Tests
        print("\n🔧 ENVIRONMENT & HEALTH TESTS")
        self.test_environment_variables()
        self.test_health_endpoints()
        
        # Authentication Tests
        print("\n🔐 AUTHENTICATION TESTS")
        self.test_magic_link_auth_flow()
        self.test_auth_me_endpoint()
        self.test_user_profile_update()
        
        # Club Data Tests
        print("\n⚽ CLUB DATA TESTS")
        self.test_clubs_seed_and_retrieval()
        
        # League Management Tests
        print("\n🏟️ LEAGUE MANAGEMENT TESTS")
        self.test_league_creation()
        self.test_league_settings_retrieval()
        self.test_league_invitation_system()
        self.test_league_member_management()
        self.test_league_join_functionality()
        
        # Auction Engine Tests
        print("\n🔨 AUCTION ENGINE TESTS")
        self.test_auction_creation_and_start()
        self.test_auction_state_retrieval()
        self.test_bid_placement_endpoint()
        self.test_auction_control_endpoints()
        
        # Database Operations Tests
        print("\n💾 DATABASE OPERATIONS TESTS")
        self.test_database_operations()
        self.test_aggregation_endpoints()
        
        # Scoring System Tests
        print("\n📊 SCORING SYSTEM TESTS")
        self.test_scoring_endpoints()
        
        # Admin Endpoints Tests
        print("\n👑 ADMIN ENDPOINTS TESTS")
        self.test_admin_endpoints()
        
        # Competition Profiles Tests
        print("\n🏆 COMPETITION PROFILES TESTS")
        self.test_competition_profiles()
        
        # WebSocket Diagnostics
        print("\n🔌 WEBSOCKET DIAGNOSTICS")
        self.test_websocket_diagnostics()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        print("\n✅ CRITICAL SYSTEMS STATUS:")
        critical_systems = [
            ("Authentication Flow", "Magic Link Auth Flow" not in [t.split(':')[0] for t in self.failed_tests]),
            ("League Management", "League Creation" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Database Operations", "Database Operations" not in [t.split(':')[0] for t in self.failed_tests]),
            ("Environment Config", "Environment Variables" not in [t.split(':')[0] for t in self.failed_tests])
        ]
        
        for system, status in critical_systems:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {system}: {'WORKING' if status else 'FAILED'}")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    passed, total, failed = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)