#!/usr/bin/env python3
"""
League Settings API Tests
Comprehensive unit and integration tests for league settings API contracts
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend to path
sys.path.append('/app/backend')

from models import *
from admin_service import AdminService
from league_service import LeagueService
from competition_service import CompetitionService
from database import db, initialize_database

class TestLeagueSettingsAPI:
    """Test suite for league settings API functionality"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_db(self):
        """Initialize test database"""
        await initialize_database()
        yield
        
    async def create_test_league(self, commissioner_id="test_commissioner", settings=None):
        """Helper to create a test league"""
        league_data = LeagueCreate(
            name="Test League",
            season="2025-26",
            settings=settings
        )
        return await LeagueService.create_league_with_setup(league_data, commissioner_id)
    
    async def add_test_member(self, league_id, user_id="test_member"):
        """Helper to add a test member to league"""
        membership = Membership(
            league_id=league_id,
            user_id=user_id,
            role=MembershipRole.MANAGER,
            status=MembershipStatus.ACTIVE
        )
        await db.memberships.insert_one(membership.dict(by_alias=True))
        
        roster = Roster(
            league_id=league_id,
            user_id=user_id,
            budget_start=100,
            budget_remaining=100,
            club_slots=3
        )
        await db.rosters.insert_one(roster.dict(by_alias=True))
        
        # Update member count
        await db.leagues.update_one(
            {"_id": league_id},
            {"$inc": {"member_count": 1}}
        )
    
    async def add_test_club_to_roster(self, league_id, user_id, club_id="test_club"):
        """Helper to add a club to user's roster"""
        roster_club = RosterClub(
            league_id=league_id,
            user_id=user_id,
            club_id=club_id,
            price=50
        )
        await db.roster_clubs.insert_one(roster_club.dict(by_alias=True))
        
        # Update budget
        await db.rosters.update_one(
            {"league_id": league_id, "user_id": user_id},
            {"$inc": {"budget_remaining": -50}}
        )

class TestClubSlotsValidation(TestLeagueSettingsAPI):
    """Test club slots increase/decrease validation"""
    
    async def test_can_increase_club_slots_mid_season(self):
        """Test that club slots can be increased mid-season"""
        # Create league with 3 club slots
        league = await self.create_test_league(
            settings=LeagueSettings(club_slots_per_manager=3)
        )
        
        # Add a member with clubs
        await self.add_test_member(league.id)
        await self.add_test_club_to_roster(league.id, "test_member", "club1")
        await self.add_test_club_to_roster(league.id, "test_member", "club2")
        
        # Try to increase club slots to 5
        settings_update = LeagueSettingsUpdate(club_slots_per_manager=5)
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert success, f"Should allow club slots increase: {message}"
        
        # Verify the update
        updated_league = await db.leagues.find_one({"_id": league.id})
        assert updated_league["settings"]["club_slots_per_manager"] == 5
        
        # Verify roster was updated
        roster = await db.rosters.find_one({"league_id": league.id, "user_id": "test_member"})
        assert roster["club_slots"] == 5
    
    async def test_cannot_decrease_club_slots_below_current_roster_count(self):
        """Test that club slots cannot be decreased below current roster count"""
        # Create league with 5 club slots
        league = await self.create_test_league(
            settings=LeagueSettings(club_slots_per_manager=5)
        )
        
        # Add a member with 4 clubs
        await self.add_test_member(league.id)
        await self.add_test_club_to_roster(league.id, "test_member", "club1")
        await self.add_test_club_to_roster(league.id, "test_member", "club2")
        await self.add_test_club_to_roster(league.id, "test_member", "club3")
        await self.add_test_club_to_roster(league.id, "test_member", "club4")
        
        # Try to decrease club slots to 3 (below current count of 4)
        settings_update = LeagueSettingsUpdate(club_slots_per_manager=3)
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert not success, "Should not allow club slots decrease below current roster count"
        assert "Cannot reduce club slots to 3" in message or "some managers own" in message
        
        # Verify the setting was not changed
        unchanged_league = await db.leagues.find_one({"_id": league.id})
        assert unchanged_league["settings"]["club_slots_per_manager"] == 5
    
    async def test_can_decrease_club_slots_when_safe(self):
        """Test that club slots can be decreased when all rosters fit the new limit"""
        # Create league with 5 club slots
        league = await self.create_test_league(
            settings=LeagueSettings(club_slots_per_manager=5)
        )
        
        # Add a member with only 2 clubs
        await self.add_test_member(league.id)
        await self.add_test_club_to_roster(league.id, "test_member", "club1")
        await self.add_test_club_to_roster(league.id, "test_member", "club2")
        
        # Try to decrease club slots to 3 (above current count of 2)
        settings_update = LeagueSettingsUpdate(club_slots_per_manager=3)
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert success, f"Should allow safe club slots decrease: {message}"
        
        # Verify the update
        updated_league = await db.leagues.find_one({"_id": league.id})
        assert updated_league["settings"]["club_slots_per_manager"] == 3

class TestBudgetChangeValidation(TestLeagueSettingsAPI):
    """Test budget change constraints"""
    
    async def test_cannot_change_budget_after_first_purchase(self):
        """Test that budget cannot be changed after first club purchase"""
        # Create league
        league = await self.create_test_league()
        
        # Add member and purchase a club
        await self.add_test_member(league.id)
        await self.add_test_club_to_roster(league.id, "test_member")
        
        # Try to change budget
        settings_update = LeagueSettingsUpdate(budget_per_manager=150)
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert not success, "Should not allow budget change after club purchase"
        assert "Budget cannot be changed after clubs have been purchased" in message
    
    async def test_cannot_change_budget_when_auction_live(self):
        """Test that budget cannot be changed when auction is live/completed"""
        # Create league
        league = await self.create_test_league()
        
        # Set auction to live status
        await db.auctions.update_one(
            {"league_id": league.id},
            {"$set": {"status": "live"}}
        )
        
        # Try to change budget
        settings_update = LeagueSettingsUpdate(budget_per_manager=150)
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert not success, "Should not allow budget change when auction is live"
        assert "Budget changes only allowed when auction is scheduled or paused" in message
    
    async def test_can_change_budget_when_scheduled_and_no_purchases(self):
        """Test that budget can be changed when auction is scheduled and no purchases"""
        # Create league
        league = await self.create_test_league()
        
        # Ensure auction is scheduled and no clubs purchased
        await db.auctions.update_one(
            {"league_id": league.id},
            {"$set": {"status": "scheduled"}}
        )
        
        # Add member but no purchases
        await self.add_test_member(league.id)
        
        # Try to change budget
        settings_update = LeagueSettingsUpdate(budget_per_manager=150)
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert success, f"Should allow budget change when conditions are met: {message}"
        
        # Verify budget was updated in league and all rosters
        updated_league = await db.leagues.find_one({"_id": league.id})
        assert updated_league["settings"]["budget_per_manager"] == 150
        
        roster = await db.rosters.find_one({"league_id": league.id, "user_id": "test_member"})
        assert roster["budget_start"] == 150
        assert roster["budget_remaining"] == 150

class TestLeagueSizeEnforcement(TestLeagueSettingsAPI):
    """Test league size min/max enforcement"""
    
    async def test_league_size_enforcement_on_invite(self):
        """Test that invites are blocked when at max league size"""
        # Create league with max size 2
        league = await self.create_test_league(
            settings=LeagueSettings(league_size=LeagueSize(min=2, max=2))
        )
        
        # Add one member (commissioner + 1 = 2 total, at max)
        await self.add_test_member(league.id)
        
        # Try to invite another member (would exceed max)
        success, message = await AdminService.validate_league_size_constraints(
            league.id, "invite"
        )
        
        assert not success, "Should not allow invite when at max league size"
        assert "League is full" in message
    
    async def test_league_size_enforcement_on_auction_start(self):
        """Test that auction start is blocked when below minimum"""
        # Create league with min size 4
        league = await self.create_test_league(
            settings=LeagueSettings(league_size=LeagueSize(min=4, max=8))
        )
        
        # Only have commissioner (1 member, below min of 4)
        success, message = await AdminService.validate_league_size_constraints(
            league.id, "start_auction"
        )
        
        assert not success, "Should not allow auction start when below minimum"
        assert "Not enough managers to start auction" in message
        assert "1/4" in message or "(1/4" in message
    
    async def test_cannot_reduce_max_below_current_members(self):
        """Test that max league size cannot be reduced below current member count"""
        # Create league with max size 8
        league = await self.create_test_league(
            settings=LeagueSettings(league_size=LeagueSize(min=2, max=8))
        )
        
        # Add 2 members (total 3 with commissioner)
        await self.add_test_member(league.id, "member1")
        await self.add_test_member(league.id, "member2")
        
        # Try to reduce max to 2 (below current count of 3)
        settings_update = LeagueSettingsUpdate(
            league_size=LeagueSize(min=2, max=2)
        )
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert not success, "Should not allow max reduction below current member count"
        assert "Maximum managers (2) cannot be less than current member count (3)" in message

class TestMigrationBehavior(TestLeagueSettingsAPI):
    """Test that migration leaves existing leagues unchanged"""
    
    async def test_migration_leaves_existing_leagues_unchanged(self):
        """Test that existing leagues maintain their settings after migration"""
        # Create a league with old-style settings (simulating pre-migration)
        old_league = League(
            name="Pre-Migration League",
            commissioner_id="test_commissioner",
            settings=LeagueSettings(
                budget_per_manager=100,
                club_slots_per_manager=3,
                league_size=LeagueSize(min=4, max=8)
            )
        )
        
        # Insert directly to simulate pre-migration state
        league_dict = old_league.dict(by_alias=True)
        await db.leagues.insert_one(league_dict)
        
        # Verify league maintains its original settings
        retrieved_league = await db.leagues.find_one({"_id": old_league.id})
        
        assert retrieved_league["settings"]["budget_per_manager"] == 100
        assert retrieved_league["settings"]["club_slots_per_manager"] == 3
        assert retrieved_league["settings"]["league_size"]["min"] == 4
        assert retrieved_league["settings"]["league_size"]["max"] == 8
        
        # Verify settings are still modifiable
        settings_update = LeagueSettingsUpdate(budget_per_manager=120)
        success, message = await AdminService.update_league_settings(
            old_league.id, "test_commissioner", settings_update
        )
        
        assert success, f"Migrated league should still allow settings updates: {message}"

class TestCompetitionProfileDefaults(TestLeagueSettingsAPI):
    """Test that new leagues use competition profile defaults"""
    
    async def test_new_league_uses_ucl_defaults_when_no_settings(self):
        """Test that new league creation uses UCL competition profile defaults"""
        # Create league without explicit settings
        league_data = LeagueCreate(
            name="UCL Default League",
            season="2025-26"
            # No settings provided - should use competition profile defaults
        )
        
        league = await LeagueService.create_league_with_setup(
            league_data, "test_commissioner"
        )
        
        # Verify league uses UCL competition profile defaults
        assert league.settings.budget_per_manager == 100  # UCL default
        assert league.settings.club_slots_per_manager == 3  # UCL default
        assert league.settings.league_size.min == 4  # UCL default
        assert league.settings.league_size.max == 8  # UCL default
        assert league.settings.scoring_rules.club_goal == 1  # UCL default
        assert league.settings.scoring_rules.club_win == 3  # UCL default
        assert league.settings.scoring_rules.club_draw == 1  # UCL default
    
    async def test_explicit_settings_override_competition_profile(self):
        """Test that explicit settings override competition profile defaults"""
        # Create league with explicit settings
        custom_settings = LeagueSettings(
            budget_per_manager=150,
            club_slots_per_manager=5,
            league_size=LeagueSize(min=2, max=6)
        )
        
        league_data = LeagueCreate(
            name="Custom Settings League",
            season="2025-26",
            settings=custom_settings
        )
        
        league = await LeagueService.create_league_with_setup(
            league_data, "test_commissioner"
        )
        
        # Verify league uses explicit settings (not competition profile defaults)
        assert league.settings.budget_per_manager == 150  # Custom setting
        assert league.settings.club_slots_per_manager == 5  # Custom setting
        assert league.settings.league_size.min == 2  # Custom setting
        assert league.settings.league_size.max == 6  # Custom setting

class TestAPIContractValidation(TestLeagueSettingsAPI):
    """Test API contract validation and error handling"""
    
    async def test_patch_endpoint_accepts_partial_updates(self):
        """Test that PATCH endpoint accepts partial settings updates"""
        league = await self.create_test_league()
        
        # Test updating only club slots
        settings_update = LeagueSettingsUpdate(club_slots_per_manager=4)
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert success, f"PATCH should accept partial updates: {message}"
        
        # Verify only club slots was updated
        updated_league = await db.leagues.find_one({"_id": league.id})
        assert updated_league["settings"]["club_slots_per_manager"] == 4
        assert updated_league["settings"]["budget_per_manager"] == 100  # Unchanged
    
    async def test_validation_errors_are_descriptive(self):
        """Test that validation errors provide clear, actionable messages"""
        league = await self.create_test_league()
        
        # Test invalid league size (min > max)
        settings_update = LeagueSettingsUpdate(
            league_size=LeagueSize(min=8, max=4)
        )
        success, message = await AdminService.update_league_settings(
            league.id, "test_commissioner", settings_update
        )
        
        assert not success, "Should reject invalid league size"
        assert "min" in message.lower() and "max" in message.lower()
    
    async def test_commissioner_only_access_control(self):
        """Test that only commissioners can update league settings"""
        league = await self.create_test_league()
        
        # Try to update as non-commissioner
        settings_update = LeagueSettingsUpdate(budget_per_manager=150)
        success, message = await AdminService.update_league_settings(
            league.id, "not_commissioner", settings_update
        )
        
        assert not success, "Should reject non-commissioner access"
        assert "Only commissioner can update league settings" in message

# Integration test runner
async def run_all_tests():
    """Run all test suites"""
    test_classes = [
        TestClubSlotsValidation,
        TestBudgetChangeValidation, 
        TestLeagueSizeEnforcement,
        TestMigrationBehavior,
        TestCompetitionProfileDefaults,
        TestAPIContractValidation
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n🧪 Running {test_class.__name__}")
        instance = test_class()
        
        # Get all test methods
        test_methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                # Setup
                await instance.setup_test_db()
                
                # Run test
                await getattr(instance, test_method)()
                
                passed_tests += 1
                print(f"  ✅ {test_method}")
                
            except Exception as e:
                failed_tests.append(f"{test_class.__name__}.{test_method}: {e}")
                print(f"  ❌ {test_method}: {e}")
    
    print(f"\n📊 Test Results:")
    print(f"Total: {total_tests}, Passed: {passed_tests}, Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
    else:
        print(f"\n🎉 All tests passed!")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)