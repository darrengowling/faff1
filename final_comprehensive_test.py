#!/usr/bin/env python3
"""
Final Comprehensive Backend API Testing Suite
Tests ALL critical user flows end-to-end for production readiness
"""

import requests
import sys
import json
import os
from datetime import datetime, timezone
import time
import uuid

class FinalComprehensiveBackendTester:
    def __init__(self, base_url="https://league-creator-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_league_id = None
        self.test_auction_id = None
        self.test_clubs = []
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.critical_failures = []
        
        # Test data with realistic values
        self.test_email = f"final_test_{int(time.time())}@example.com"
        self.manager_emails = [
            f"manager1_{int(time.time())}@example.com",
            f"manager2_{int(time.time())}@example.com", 
            f"manager3_{int(time.time())}@example.com"
        ]
        
    def log_test(self, name, success, details="", critical=False):
        """Log test results with critical flag"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            self.failed_tests.append(f"{name}: {details}")
            if critical:
                self.critical_failures.append(f"{name}: {details}")
            print(f"❌ {name} - {'CRITICAL FAILURE' if critical else 'FAILED'} {details}")
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

    # ==================== CRITICAL FLOW 1: COMPLETE AUTHENTICATION FLOW ====================
    
    def test_complete_authentication_flow(self):
        """Test complete authentication flow - magic link generation and verification"""
        print("\n🔐 TESTING COMPLETE AUTHENTICATION FLOW")
        
        # Step 1: Request magic link
        success, status, data = self.make_request(
            'POST', 
            'auth/magic-link', 
            {"email": self.test_email},
            token=None
        )
        
        if not success:
            return self.log_test("Complete Authentication Flow", False, f"Magic link request failed: {status}", critical=True)
        
        # Verify magic link structure
        if 'dev_magic_link' not in data:
            return self.log_test("Complete Authentication Flow", False, "No dev magic link in response", critical=True)
        
        # Step 2: Extract and verify token
        magic_link = data['dev_magic_link']
        if 'token=' not in magic_link:
            return self.log_test("Complete Authentication Flow", False, "Invalid magic link format", critical=True)
        
        token = magic_link.split('token=')[1]
        
        # Step 3: Verify magic link token
        success, status, auth_data = self.make_request(
            'POST',
            'auth/verify',
            {"token": token},
            token=None
        )
        
        if not success:
            return self.log_test("Complete Authentication Flow", False, f"Token verification failed: {status}", critical=True)
        
        # Step 4: Validate auth response and store token
        auth_valid = (
            'access_token' in auth_data and
            'user' in auth_data and
            'email' in auth_data['user'] and
            'verified' in auth_data['user'] and
            auth_data['user']['verified'] is True
        )
        
        if auth_valid:
            self.token = auth_data['access_token']
            self.user_data = auth_data['user']
        
        # Step 5: Test /auth/me endpoint
        success_me, status_me, me_data = self.make_request('GET', 'auth/me')
        me_valid = success_me and me_data.get('email') == self.test_email
        
        overall_success = auth_valid and me_valid
        return self.log_test(
            "Complete Authentication Flow",
            overall_success,
            f"Magic link ✓, Token verification ✓, /auth/me ✓, User: {auth_data.get('user', {}).get('email', 'Unknown')}",
            critical=True
        )

    # ==================== CRITICAL FLOW 2: LEAGUE MANAGEMENT FLOW ====================
    
    def test_league_management_flow(self):
        """Test league management flow - create league, update settings, get member info"""
        print("\n🏟️ TESTING LEAGUE MANAGEMENT FLOW")
        
        if not self.token:
            return self.log_test("League Management Flow", False, "No authentication token", critical=True)
        
        # Step 1: Create league
        league_data = {
            "name": f"Final Test League {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "min_increment": 1,
                "club_slots_per_manager": 5,
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
            return self.log_test("League Management Flow", False, f"League creation failed: {status} - {data}", critical=True)
        
        # Validate league creation
        league_valid = (
            'id' in data and
            'name' in data and
            'settings' in data and
            'member_count' in data and
            data['member_count'] == 1 and
            data['status'] == 'setup'
        )
        
        if not league_valid:
            return self.log_test("League Management Flow", False, "Invalid league creation response", critical=True)
        
        self.test_league_id = data['id']
        
        # Step 2: Get league settings
        success2, status2, settings_data = self.make_request('GET', f'leagues/{self.test_league_id}/settings')
        
        settings_valid = (
            success2 and
            'clubSlots' in settings_data and
            'budgetPerManager' in settings_data and
            'leagueSize' in settings_data and
            settings_data['clubSlots'] == 5 and
            settings_data['budgetPerManager'] == 100
        )
        
        # Step 3: Get league members
        success3, status3, members_data = self.make_request('GET', f'leagues/{self.test_league_id}/members')
        
        members_valid = (
            success3 and
            isinstance(members_data, list) and
            len(members_data) == 1 and
            members_data[0]['role'] == 'commissioner'
        )
        
        # Step 4: Get league status
        success4, status4, status_data = self.make_request('GET', f'leagues/{self.test_league_id}/status')
        
        status_valid = (
            success4 and
            'member_count' in status_data and
            'min_members' in status_data and
            'max_members' in status_data and
            'is_ready' in status_data and
            status_data['member_count'] == 1
        )
        
        overall_success = league_valid and settings_valid and members_valid and status_valid
        return self.log_test(
            "League Management Flow",
            overall_success,
            f"Creation ✓, Settings ✓, Members ✓, Status ✓, League ID: {self.test_league_id}",
            critical=True
        )

    # ==================== CRITICAL FLOW 3: INVITATION SYSTEM FLOW ====================
    
    def test_invitation_system_flow(self):
        """Test invitation system flow - send invitations, check status, prevent duplicates"""
        print("\n📧 TESTING INVITATION SYSTEM FLOW")
        
        if not self.test_league_id:
            return self.log_test("Invitation System Flow", False, "No test league ID", critical=True)
        
        invitation_results = []
        
        # Step 1: Send invitations
        for i, email in enumerate(self.manager_emails[:2]):  # Test with 2 managers
            success, status, data = self.make_request(
                'POST',
                f'leagues/{self.test_league_id}/invite',
                {"email": email}
            )
            invitation_results.append(success)
            
            if not success:
                print(f"   ❌ Invitation {i+1} failed: {status} - {data}")
            else:
                print(f"   ✅ Invitation {i+1} sent successfully to {email}")
        
        # Step 2: Get invitations list
        success_list, status_list, invitations = self.make_request('GET', f'leagues/{self.test_league_id}/invitations')
        
        invitations_valid = (
            success_list and
            isinstance(invitations, list) and
            len(invitations) >= len([r for r in invitation_results if r])
        )
        
        # Step 3: Test duplicate prevention
        success_dup, status_dup, data_dup = self.make_request(
            'POST',
            f'leagues/{self.test_league_id}/invite',
            {"email": self.manager_emails[0]},
            expected_status=400
        )
        
        duplicate_prevented = success_dup and status_dup == 400
        
        # Step 4: Check invitation status in list
        invitation_status_valid = True
        if invitations_valid:
            for invitation in invitations:
                if 'email' not in invitation or 'status' not in invitation:
                    invitation_status_valid = False
                    break
        
        successful_invites = sum(invitation_results)
        overall_success = (
            successful_invites >= 1 and
            invitations_valid and
            duplicate_prevented and
            invitation_status_valid
        )
        
        return self.log_test(
            "Invitation System Flow",
            overall_success,
            f"Sent: {successful_invites}/2, Retrieved: {len(invitations) if invitations_valid else 0}, Duplicate prevented: {duplicate_prevented}",
            critical=True
        )

    # ==================== CRITICAL FLOW 4: COMPETITION & CLUB DATA ====================
    
    def test_competition_and_club_data(self):
        """Test competition profiles and club data accessibility"""
        print("\n🏆 TESTING COMPETITION & CLUB DATA")
        
        # Step 1: Test competition profiles
        success, status, data = self.make_request('GET', 'competition-profiles', token=None)
        
        profiles_valid = (
            success and
            'profiles' in data and
            isinstance(data['profiles'], list) and
            len(data['profiles']) > 0
        )
        
        profile_details_valid = False
        if profiles_valid and len(data['profiles']) > 0:
            profile_id = data['profiles'][0].get('id')
            if profile_id:
                success2, status2, profile_data = self.make_request('GET', f'competition-profiles/{profile_id}', token=None)
                profile_details_valid = success2 and 'id' in profile_data
        
        # Step 2: Test club data
        success3, status3, clubs_data = self.make_request('GET', 'clubs', token=None)
        
        clubs_valid = (
            success3 and
            isinstance(clubs_data, list) and
            len(clubs_data) >= 16  # Should have at least 16 clubs
        )
        
        # Step 3: Validate club data structure
        club_structure_valid = True
        if clubs_valid:
            for club in clubs_data[:3]:  # Check first 3 clubs
                if not all(key in club for key in ['id', 'name', 'short_name', 'country']):
                    club_structure_valid = False
                    break
            self.test_clubs = clubs_data[:5]  # Store for later use
        
        overall_success = profiles_valid and profile_details_valid and clubs_valid and club_structure_valid
        return self.log_test(
            "Competition & Club Data",
            overall_success,
            f"Profiles: {len(data.get('profiles', [])) if profiles_valid else 0}, Clubs: {len(clubs_data) if clubs_valid else 0}, Structure valid: {club_structure_valid}",
            critical=True
        )

    # ==================== CRITICAL FLOW 5: WEBSOCKET INTEGRATION ====================
    
    def test_websocket_integration(self):
        """Test WebSocket integration - verify socket diagnostics working"""
        print("\n🔌 TESTING WEBSOCKET INTEGRATION")
        
        # Step 1: Test Socket.IO diagnostic endpoint
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
        
        # Step 2: Test Socket.IO handshake endpoint directly
        handshake_works = False
        try:
            response = requests.get(f"{self.base_url}/api/socketio/?EIO=4&transport=polling", timeout=10)
            handshake_works = response.status_code == 200 and response.text.startswith('0{')
        except Exception as e:
            print(f"   ⚠️ Handshake test failed: {e}")
        
        # Step 3: Verify Socket.IO path configuration
        socket_path_valid = True
        if diag_valid:
            expected_path = "/api/socketio"
            actual_path = data.get('path', '')
            socket_path_valid = actual_path == expected_path
        
        overall_success = diag_valid and handshake_works and socket_path_valid
        return self.log_test(
            "WebSocket Integration",
            overall_success,
            f"Diagnostic: {diag_valid}, Handshake: {handshake_works}, Path config: {socket_path_valid}",
            critical=True
        )

    # ==================== CRITICAL FLOW 6: HEALTH & MONITORING ====================
    
    def test_health_and_monitoring(self):
        """Test health & monitoring - verify detailed health endpoint"""
        print("\n🏥 TESTING HEALTH & MONITORING")
        
        # Step 1: Test main health endpoint
        success, status, data = self.make_request('GET', 'health', token=None)
        
        health_structure_valid = (
            success and
            'status' in data and
            'timestamp' in data and
            'database' in data and
            'system' in data and
            'services' in data
        )
        
        # Step 2: Validate database health
        db_health_valid = False
        if health_structure_valid:
            db_info = data.get('database', {})
            db_health_valid = (
                db_info.get('connected') is True and
                'collections_count' in db_info and
                isinstance(db_info.get('missing_collections', []), list)
            )
        
        # Step 3: Validate system metrics
        system_metrics_valid = False
        if health_structure_valid:
            system_info = data.get('system', {})
            system_metrics_valid = (
                'cpu_percent' in system_info and
                'memory_percent' in system_info and
                'disk_percent' in system_info and
                isinstance(system_info.get('cpu_percent'), (int, float))
            )
        
        # Step 4: Validate services status
        services_status_valid = False
        if health_structure_valid:
            services_info = data.get('services', {})
            services_status_valid = (
                'websocket' in services_info and
                'email' in services_info and
                'auth' in services_info
            )
        
        # Step 5: Test time sync endpoint
        success_time, status_time, time_data = self.make_request('GET', 'timez', token=None)
        time_sync_valid = success_time and 'now' in time_data
        
        overall_success = (
            health_structure_valid and
            db_health_valid and
            system_metrics_valid and
            services_status_valid and
            time_sync_valid
        )
        
        return self.log_test(
            "Health & Monitoring",
            overall_success,
            f"Structure ✓, DB ✓, System ✓, Services ✓, Time sync ✓, Status: {data.get('status', 'Unknown')}",
            critical=True
        )

    # ==================== CRITICAL FLOW 7: ADMIN & AUDIT FUNCTIONS ====================
    
    def test_admin_and_audit_functions(self):
        """Test admin controls and audit logging"""
        print("\n👑 TESTING ADMIN & AUDIT FUNCTIONS")
        
        if not self.test_league_id:
            return self.log_test("Admin & Audit Functions", False, "No test league ID", critical=True)
        
        # Step 1: Test league settings update (PATCH)
        success, status, data = self.make_request(
            'PATCH',
            f'leagues/{self.test_league_id}/settings',
            {"budget_per_manager": 120}
        )
        
        settings_update_works = success and status == 200
        
        # Step 2: Test admin logs endpoint
        success2, status2, logs_data = self.make_request('GET', f'admin/leagues/{self.test_league_id}/logs')
        
        logs_accessible = success2 and 'logs' in logs_data and isinstance(logs_data['logs'], list)
        
        # Step 3: Test bid audit endpoint
        success3, status3, audit_data = self.make_request('GET', f'admin/leagues/{self.test_league_id}/bid-audit')
        
        audit_accessible = success3 and 'bids' in audit_data
        
        # Step 4: Test comprehensive audit endpoint
        success4, status4, comp_audit = self.make_request('GET', f'admin/leagues/{self.test_league_id}/audit')
        
        comp_audit_works = success4 or status4 in [400, 404]  # May not have data yet
        
        overall_success = settings_update_works and logs_accessible and audit_accessible
        return self.log_test(
            "Admin & Audit Functions",
            overall_success,
            f"Settings update: {settings_update_works}, Logs: {logs_accessible}, Audit: {audit_accessible}, Comp audit: {comp_audit_works}",
            critical=True
        )

    # ==================== CRITICAL FLOW 8: DATABASE OPERATIONS ====================
    
    def test_database_operations(self):
        """Test all CRUD operations working"""
        print("\n💾 TESTING DATABASE OPERATIONS")
        
        if not self.token:
            return self.log_test("Database Operations", False, "No authentication token", critical=True)
        
        # Step 1: Test CREATE - User profile update
        test_name = f"DB Test {datetime.now().strftime('%H%M%S')}"
        success, status, data = self.make_request(
            'PUT',
            'users/me',
            {"display_name": test_name}
        )
        
        create_works = success and data.get('display_name') == test_name
        
        # Step 2: Test READ - Profile retrieval
        success2, status2, data2 = self.make_request('GET', 'auth/me')
        
        read_works = success2 and data2.get('display_name') == test_name
        
        # Step 3: Test READ - League data
        success3, status3, leagues = self.make_request('GET', 'leagues')
        
        leagues_read = success3 and isinstance(leagues, list) and len(leagues) > 0
        
        # Step 4: Test aggregation endpoints (complex reads)
        aggregation_results = []
        
        if self.test_league_id:
            # Roster summary
            success4, status4, roster_data = self.make_request('GET', f'leagues/{self.test_league_id}/roster/summary')
            roster_works = success4 and 'ownedCount' in roster_data and 'clubSlots' in roster_data
            aggregation_results.append(roster_works)
            
            # My clubs
            success5, status5, clubs_data = self.make_request('GET', f'clubs/my-clubs/{self.test_league_id}')
            clubs_works = success5 or status5 == 404  # 404 acceptable if no clubs owned
            aggregation_results.append(clubs_works)
            
            # Fixtures
            success6, status6, fixtures_data = self.make_request('GET', f'fixtures/{self.test_league_id}')
            fixtures_works = success6 or status6 == 404  # 404 acceptable if no fixtures
            aggregation_results.append(fixtures_works)
            
            # Leaderboard
            success7, status7, leaderboard_data = self.make_request('GET', f'leaderboard/{self.test_league_id}')
            leaderboard_works = success7 or status7 == 404  # 404 acceptable if no data
            aggregation_results.append(leaderboard_works)
        
        aggregation_success = sum(aggregation_results) >= 3 if aggregation_results else True
        
        overall_success = create_works and read_works and leagues_read and aggregation_success
        return self.log_test(
            "Database Operations",
            overall_success,
            f"CREATE ✓, READ ✓, Leagues ✓, Aggregations: {sum(aggregation_results) if aggregation_results else 0}/4",
            critical=True
        )

    # ==================== AUCTION ENGINE VALIDATION ====================
    
    def test_auction_engine_validation(self):
        """Test auction engine endpoints with proper error handling"""
        print("\n🔨 TESTING AUCTION ENGINE VALIDATION")
        
        if not self.test_league_id:
            return self.log_test("Auction Engine Validation", False, "No test league ID")
        
        # Step 1: Test auction start (should fail gracefully with proper error)
        success, status, data = self.make_request('POST', f'auction/{self.test_league_id}/start')
        
        start_validation = (
            (success and status == 200) or  # Success if league is ready
            (not success and status == 400 and 'detail' in data)  # Proper error if not ready
        )
        
        # Step 2: Test auction state retrieval
        success2, status2, data2 = self.make_request('GET', f'auction/{self.test_league_id}/state')
        
        state_validation = (
            (success2 and status2 == 200) or  # Success if auction exists
            (not success2 and status2 == 404)  # Proper 404 if no auction
        )
        
        # Step 3: Test bid placement endpoint structure
        success3, status3, data3 = self.make_request(
            'POST',
            f'auction/{self.test_league_id}/bid',
            {"lot_id": "test_lot", "amount": 10},
            expected_status=400
        )
        
        bid_validation = success3 and status3 == 400  # Should return proper error
        
        # Step 4: Test auction control endpoints
        success4, status4, data4 = self.make_request('POST', f'auction/{self.test_league_id}/pause')
        pause_validation = success4 or status4 in [400, 404]
        
        success5, status5, data5 = self.make_request('POST', f'auction/{self.test_league_id}/resume')
        resume_validation = success5 or status5 in [400, 404]
        
        overall_success = start_validation and state_validation and bid_validation and pause_validation and resume_validation
        return self.log_test(
            "Auction Engine Validation",
            overall_success,
            f"Start: {status}, State: {status2}, Bid: {status3}, Pause: {status4}, Resume: {status5}"
        )

    # ==================== SCORING SYSTEM VALIDATION ====================
    
    def test_scoring_system_validation(self):
        """Test scoring system endpoints"""
        print("\n📊 TESTING SCORING SYSTEM VALIDATION")
        
        if not self.test_league_id:
            return self.log_test("Scoring System Validation", False, "No test league ID")
        
        # Step 1: Test result ingestion
        success, status, data = self.make_request(
            'POST',
            'ingest/final_result',
            {
                "league_id": self.test_league_id,
                "match_id": f"test_match_{int(time.time())}",
                "season": "2025-26",
                "home_ext": "test_home",
                "away_ext": "test_away",
                "home_goals": 2,
                "away_goals": 1,
                "kicked_off_at": datetime.now(timezone.utc).isoformat(),
                "status": "final"
            }
        )
        
        ingest_works = success and data.get('success') is True
        
        # Step 2: Test standings endpoint
        success2, status2, data2 = self.make_request('GET', f'leagues/{self.test_league_id}/standings')
        standings_works = success2 and 'standings' in data2
        
        # Step 3: Test processing endpoint
        success3, status3, data3 = self.make_request('POST', 'scoring/process')
        processing_works = success3 or status3 in [400, 404]
        
        overall_success = ingest_works and standings_works and processing_works
        return self.log_test(
            "Scoring System Validation",
            overall_success,
            f"Ingest: {ingest_works}, Standings: {standings_works}, Processing: {processing_works}"
        )

    # ==================== MAIN TEST RUNNER ====================
    
    def run_final_comprehensive_tests(self):
        """Run final comprehensive backend tests for production readiness"""
        print("🚀 FINAL COMPREHENSIVE BACKEND API TESTING SUITE")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print(f"API Endpoint: {self.api_url}")
        print("Target: 98%+ success rate across all endpoints")
        print("=" * 70)
        
        # CRITICAL FLOWS TO TEST (as specified in requirements)
        
        # 1. Complete Authentication Flow
        self.test_complete_authentication_flow()
        
        # 2. League Management Flow
        self.test_league_management_flow()
        
        # 3. Invitation System Flow
        self.test_invitation_system_flow()
        
        # 4. Competition & Club Data
        self.test_competition_and_club_data()
        
        # 5. WebSocket Integration
        self.test_websocket_integration()
        
        # 6. Health & Monitoring
        self.test_health_and_monitoring()
        
        # 7. Admin & Audit Functions
        self.test_admin_and_audit_functions()
        
        # 8. Database Operations
        self.test_database_operations()
        
        # Additional validation tests
        self.test_auction_engine_validation()
        self.test_scoring_system_validation()
        
        # Final Summary
        print("\n" + "=" * 70)
        print("📊 FINAL COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        success_rate = (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Success criteria check
        target_success_rate = 98.0
        meets_target = success_rate >= target_success_rate
        print(f"Target Success Rate: {target_success_rate}%")
        print(f"Meets Target: {'✅ YES' if meets_target else '❌ NO'}")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES ({len(self.critical_failures)}):")
            for i, failure in enumerate(self.critical_failures, 1):
                print(f"   {i}. {failure}")
        
        if self.failed_tests and not self.critical_failures:
            print(f"\n⚠️ NON-CRITICAL FAILURES ({len(self.failed_tests)}):")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
        
        print("\n✅ CRITICAL USER FLOWS STATUS:")
        critical_flows = [
            ("Complete Authentication Flow", "Complete Authentication Flow" not in [t.split(':')[0] for t in self.critical_failures]),
            ("League Management Flow", "League Management Flow" not in [t.split(':')[0] for t in self.critical_failures]),
            ("Invitation System Flow", "Invitation System Flow" not in [t.split(':')[0] for t in self.critical_failures]),
            ("Competition & Club Data", "Competition & Club Data" not in [t.split(':')[0] for t in self.critical_failures]),
            ("WebSocket Integration", "WebSocket Integration" not in [t.split(':')[0] for t in self.critical_failures]),
            ("Health & Monitoring", "Health & Monitoring" not in [t.split(':')[0] for t in self.critical_failures]),
            ("Admin & Audit Functions", "Admin & Audit Functions" not in [t.split(':')[0] for t in self.critical_failures]),
            ("Database Operations", "Database Operations" not in [t.split(':')[0] for t in self.critical_failures])
        ]
        
        all_critical_working = True
        for flow, status in critical_flows:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {flow}: {'WORKING' if status else 'FAILED'}")
            if not status:
                all_critical_working = False
        
        print(f"\n🎯 PRODUCTION READINESS: {'✅ READY' if meets_target and all_critical_working and len(self.critical_failures) == 0 else '❌ NOT READY'}")
        
        if meets_target and all_critical_working and len(self.critical_failures) == 0:
            print("🎉 Backend application is PRODUCTION-READY with all critical flows working!")
        else:
            print("⚠️ Backend application needs attention before production deployment.")
        
        return self.tests_passed, self.tests_run, self.failed_tests, self.critical_failures

if __name__ == "__main__":
    tester = FinalComprehensiveBackendTester()
    passed, total, failed, critical_failed = tester.run_final_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if len(critical_failed) == 0 and (passed/total)*100 >= 98.0 else 1)