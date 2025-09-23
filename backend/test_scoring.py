#!/usr/bin/env python3
"""
UCL Auction Scoring Service Unit Tests
Tests idempotent settlement worker and scoring calculations
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

from scoring_service import ScoringService
from models import *
from database import db

# Load environment variables
load_dotenv()

class TestScoringService:
    """Unit tests for scoring service"""
    
    def __init__(self):
        """Initialize test instance"""
        self.test_league_id = "test_league_scoring"
        self.test_user_1 = "test_user_1"
        self.test_user_2 = "test_user_2"
        self.test_club_home = "test_club_home"
        self.test_club_away = "test_club_away"
        
    async def setup_test_data(self):
        """Setup test data in database"""
        # Clean up any existing test data
        await self.cleanup_test_data()
        
        # Create test clubs
        test_clubs = [
            {
                "_id": self.test_club_home,
                "name": "Test Home FC",
                "short_name": "THF",
                "country": "England",
                "ext_ref": "test_home"
            },
            {
                "_id": self.test_club_away,
                "name": "Test Away FC", 
                "short_name": "TAF",
                "country": "Spain",
                "ext_ref": "test_away"
            }
        ]
        await db.clubs.insert_many(test_clubs)
        
        # Create test users
        test_users = [
            {
                "_id": self.test_user_1,
                "email": "user1@test.com",
                "display_name": "Test User 1",
                "verified": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "_id": self.test_user_2,
                "email": "user2@test.com",
                "display_name": "Test User 2",
                "verified": True,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        await db.users.insert_many(test_users)
        
        # Create test rosters
        test_rosters = [
            {
                "_id": f"roster_{self.test_user_1}",
                "league_id": self.test_league_id,
                "user_id": self.test_user_1,
                "budget_start": 100,
                "budget_remaining": 50,
                "club_slots": 3
            },
            {
                "_id": f"roster_{self.test_user_2}",
                "league_id": self.test_league_id,
                "user_id": self.test_user_2,
                "budget_start": 100,
                "budget_remaining": 60,
                "club_slots": 3
            }
        ]
        await db.rosters.insert_many(test_rosters)
        
        # Create roster clubs (ownership)
        test_roster_clubs = [
            {
                "_id": f"rc_{self.test_user_1}_{self.test_club_home}",
                "roster_id": f"roster_{self.test_user_1}",
                "league_id": self.test_league_id,
                "user_id": self.test_user_1,
                "club_id": self.test_club_home,
                "price": 25,
                "acquired_at": datetime.now(timezone.utc)
            },
            {
                "_id": f"rc_{self.test_user_2}_{self.test_club_away}",
                "roster_id": f"roster_{self.test_user_2}",
                "league_id": self.test_league_id,
                "user_id": self.test_user_2,
                "club_id": self.test_club_away,
                "price": 30,
                "acquired_at": datetime.now(timezone.utc)
            }
        ]
        await db.roster_clubs.insert_many(test_roster_clubs)
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        collections = [
            "clubs", "users", "rosters", "roster_clubs", 
            "result_ingest", "settlements", "weekly_points"
        ]
        
        for collection_name in collections:
            collection = getattr(db, collection_name)
            await collection.delete_many({
                "$or": [
                    {"_id": {"$regex": "^test_"}},
                    {"league_id": self.test_league_id},
                    {"ext_ref": {"$in": ["test_home", "test_away"]}},
                    {"email": {"$regex": "@test.com$"}}
                ]
            })
    
    async def test_win_scenario(self):
        """Test scoring for a win scenario: 2-1 result"""
        print("\n=== Testing Win Scenario (2-1) ===")
        
        await self.setup_test_data()
        
        # Ingest match result: Home team wins 2-1
        result = await ScoringService.ingest_result(
            league_id=self.test_league_id,
            match_id="test_match_win",
            season="2024-25",
            home_ext="test_home",
            away_ext="test_away",
            home_goals=2,
            away_goals=1,
            kicked_off_at=datetime.now(timezone.utc),
            status="final"
        )
        
        assert result["success"], f"Failed to ingest result: {result['message']}"
        assert result["created"], "Result should be newly created"
        
        # Process the result
        process_result = await ScoringService.process_pending_results()
        assert process_result["success"], f"Failed to process results: {process_result}"
        assert process_result["processed_count"] == 1, "Should process exactly 1 result"
        
        # Verify points calculation
        # Home team owner: 2 goals + 3 win = 5 points
        # Away team owner: 1 goal + 0 loss = 1 point
        
        home_points = await db.weekly_points.find_one({
            "league_id": self.test_league_id,
            "user_id": self.test_user_1,
            "match_id": "test_match_win"
        })
        
        away_points = await db.weekly_points.find_one({
            "league_id": self.test_league_id,
            "user_id": self.test_user_2,
            "match_id": "test_match_win"
        })
        
        assert home_points is not None, "Home team owner should have points record"
        assert away_points is not None, "Away team owner should have points record"
        assert home_points["points_delta"] == 5, f"Home team should have 5 points, got {home_points['points_delta']}"
        assert away_points["points_delta"] == 1, f"Away team should have 1 point, got {away_points['points_delta']}"
        
        # Verify settlement was created
        settlement = await db.settlements.find_one({
            "league_id": self.test_league_id,
            "match_id": "test_match_win"
        })
        assert settlement is not None, "Settlement record should be created"
        
        # Verify result marked as processed
        result_record = await db.result_ingest.find_one({
            "league_id": self.test_league_id,
            "match_id": "test_match_win"
        })
        assert result_record["processed"] == True, "Result should be marked as processed"
        
        print("✅ Win scenario test passed")
    
    async def test_draw_scenario(self):
        """Test scoring for a draw scenario: 1-1 result"""
        print("\n=== Testing Draw Scenario (1-1) ===")
        
        await self.setup_test_data()
        
        # Ingest match result: Draw 1-1
        result = await ScoringService.ingest_result(
            league_id=self.test_league_id,
            match_id="test_match_draw",
            season="2024-25",
            home_ext="test_home",
            away_ext="test_away",
            home_goals=1,
            away_goals=1,
            kicked_off_at=datetime.now(timezone.utc),
            status="final"
        )
        
        assert result["success"], f"Failed to ingest result: {result['message']}"
        
        # Process the result
        process_result = await ScoringService.process_pending_results()
        assert process_result["success"], f"Failed to process results: {process_result}"
        
        # Verify points calculation
        # Both teams: 1 goal + 1 draw = 2 points each
        
        home_points = await db.weekly_points.find_one({
            "league_id": self.test_league_id,
            "user_id": self.test_user_1,
            "match_id": "test_match_draw"
        })
        
        away_points = await db.weekly_points.find_one({
            "league_id": self.test_league_id,
            "user_id": self.test_user_2,
            "match_id": "test_match_draw"
        })
        
        assert home_points["points_delta"] == 2, f"Home team should have 2 points, got {home_points['points_delta']}"
        assert away_points["points_delta"] == 2, f"Away team should have 2 points, got {away_points['points_delta']}"
        
        print("✅ Draw scenario test passed")
    
    async def test_zero_zero_draw(self):
        """Test scoring for a 0-0 draw"""
        print("\n=== Testing 0-0 Draw Scenario ===")
        
        await self.setup_test_data()
        
        # Ingest match result: 0-0 draw
        result = await ScoringService.ingest_result(
            league_id=self.test_league_id,
            match_id="test_match_0_0",
            season="2024-25",
            home_ext="test_home",
            away_ext="test_away",
            home_goals=0,
            away_goals=0,
            kicked_off_at=datetime.now(timezone.utc),
            status="final"
        )
        
        assert result["success"], f"Failed to ingest result: {result['message']}"
        
        # Process the result
        process_result = await ScoringService.process_pending_results()
        assert process_result["success"], f"Failed to process results: {process_result}"
        
        # Verify points calculation
        # Both teams: 0 goals + 1 draw = 1 point each
        
        home_points = await db.weekly_points.find_one({
            "league_id": self.test_league_id,
            "user_id": self.test_user_1,
            "match_id": "test_match_0_0"
        })
        
        away_points = await db.weekly_points.find_one({
            "league_id": self.test_league_id,
            "user_id": self.test_user_2,
            "match_id": "test_match_0_0"
        })
        
        assert home_points["points_delta"] == 1, f"Home team should have 1 point, got {home_points['points_delta']}"
        assert away_points["points_delta"] == 1, f"Away team should have 1 point, got {away_points['points_delta']}"
        
        print("✅ 0-0 Draw scenario test passed")
    
    async def test_duplicate_result_idempotency(self):
        """Test that duplicate results don't cause double scoring"""
        print("\n=== Testing Duplicate Result Idempotency ===")
        
        await self.setup_test_data()
        
        # Ingest the same match result twice
        match_id = "test_match_duplicate"
        
        # First ingestion
        result1 = await ScoringService.ingest_result(
            league_id=self.test_league_id,
            match_id=match_id,
            season="2024-25",
            home_ext="test_home",
            away_ext="test_away",
            home_goals=3,
            away_goals=0,
            kicked_off_at=datetime.now(timezone.utc),
            status="final"
        )
        
        # Second ingestion (duplicate)
        result2 = await ScoringService.ingest_result(
            league_id=self.test_league_id,
            match_id=match_id,
            season="2024-25",
            home_ext="test_home",
            away_ext="test_away",
            home_goals=3,
            away_goals=0,
            kicked_off_at=datetime.now(timezone.utc),
            status="final"
        )
        
        assert result1["success"] and result1["created"], "First ingestion should succeed and create"
        assert result2["success"] and not result2["created"], "Second ingestion should succeed but not create"
        
        # Process results (should only process once due to settlement uniqueness)
        process_result1 = await ScoringService.process_pending_results()
        process_result2 = await ScoringService.process_pending_results()  # Second run
        
        assert process_result1["processed_count"] == 1, "First run should process 1 result"
        assert process_result2["processed_count"] == 0, "Second run should process 0 results"
        
        # Verify only one settlement was created
        settlements = await db.settlements.find({
            "league_id": self.test_league_id,
            "match_id": match_id
        }).to_list(length=None)
        
        assert len(settlements) == 1, "Should have exactly 1 settlement record"
        
        # Verify points are only recorded once
        home_points_records = await db.weekly_points.find({
            "league_id": self.test_league_id,
            "user_id": self.test_user_1,
            "match_id": match_id
        }).to_list(length=None)
        
        assert len(home_points_records) == 1, "Should have exactly 1 points record for home team"
        assert home_points_records[0]["points_delta"] == 6, "Home team should have 6 points (3 goals + 3 win)"
        
        print("✅ Duplicate result idempotency test passed")
    
    async def test_unknown_club_no_points(self):
        """Test that unknown clubs don't generate points"""
        print("\n=== Testing Unknown Club (No Points) ===")
        
        await self.setup_test_data()
        
        # Ingest match result with unknown club
        result = await ScoringService.ingest_result(
            league_id=self.test_league_id,
            match_id="test_match_unknown",
            season="2024-25",
            home_ext="unknown_club",  # This club doesn't exist
            away_ext="test_away",
            home_goals=2,
            away_goals=1,
            kicked_off_at=datetime.now(timezone.utc),
            status="final"
        )
        
        assert result["success"], f"Failed to ingest result: {result['message']}"
        
        # Process the result
        process_result = await ScoringService.process_pending_results()
        assert process_result["success"], f"Failed to process results: {process_result}"
        
        # Verify only away team (known club) gets points
        home_points = await db.weekly_points.find_one({
            "league_id": self.test_league_id,
            "match_id": "test_match_unknown"
        })
        
        away_points = await db.weekly_points.find_one({
            "league_id": self.test_league_id,
            "user_id": self.test_user_2,
            "match_id": "test_match_unknown"
        })
        
        # Should have no points records for unknown home club
        all_points = await db.weekly_points.find({
            "league_id": self.test_league_id,
            "match_id": "test_match_unknown"
        }).to_list(length=None)
        
        assert len(all_points) == 1, "Should have exactly 1 points record (only for known club)"
        assert away_points is not None, "Away team should have points"
        assert away_points["points_delta"] == 1, "Away team should have 1 point (1 goal + 0 loss)"
        
        print("✅ Unknown club test passed")
    
    async def test_matchday_bucket_calculation(self):
        """Test matchday bucket calculation"""
        print("\n=== Testing Matchday Bucket Calculation ===")
        
        # Test group stage matchdays
        group_stage_date = datetime(2024, 9, 15, tzinfo=timezone.utc)  # Early season
        bucket1 = ScoringService.calculate_matchday_bucket(group_stage_date, "2024-25")
        assert bucket1["type"] == "matchday", "Should be matchday type"
        assert 1 <= bucket1["value"] <= 6, f"Group stage should be matchday 1-6, got {bucket1['value']}"
        
        # Test knockout stage
        knockout_date = datetime(2025, 2, 15, tzinfo=timezone.utc)  # Later in season
        bucket2 = ScoringService.calculate_matchday_bucket(knockout_date, "2024-25")
        assert bucket2["type"] == "matchday", "Should be matchday type"
        assert bucket2["value"] >= 7, f"Knockout should be matchday 7+, got {bucket2['value']}"
        
        print("✅ Matchday bucket calculation test passed")
    
    async def test_league_standings(self):
        """Test league standings calculation"""
        print("\n=== Testing League Standings ===")
        
        await self.setup_test_data()
        
        # Add some match results
        results = [
            ("match1", "test_home", "test_away", 2, 1, 5, 1),  # Home wins: +5, Away: +1
            ("match2", "test_away", "test_home", 1, 1, 2, 2),  # Draw: +2 each
        ]
        
        for match_id, home_ext, away_ext, home_goals, away_goals, home_expected, away_expected in results:
            await ScoringService.ingest_result(
                league_id=self.test_league_id,
                match_id=match_id,
                season="2024-25",
                home_ext=home_ext,
                away_ext=away_ext,
                home_goals=home_goals,
                away_goals=away_goals,
                kicked_off_at=datetime.now(timezone.utc),
                status="final"
            )
        
        # Process all results
        await ScoringService.process_pending_results()
        
        # Get standings
        standings = await ScoringService.get_league_standings(self.test_league_id)
        
        assert len(standings) == 2, "Should have 2 users in standings"
        
        # Both users should have 7 points total (5+2 and 1+2)
        user1_standing = next((s for s in standings if s["user_id"] == self.test_user_1), None)
        user2_standing = next((s for s in standings if s["user_id"] == self.test_user_2), None)
        
        assert user1_standing is not None, "User 1 should be in standings"
        assert user2_standing is not None, "User 2 should be in standings"
        assert user1_standing["total_points"] == 7, f"User 1 should have 7 points, got {user1_standing['total_points']}"
        assert user2_standing["total_points"] == 3, f"User 2 should have 3 points, got {user2_standing['total_points']}"
        
        print("✅ League standings test passed")

async def run_all_tests():
    """Run all scoring service tests"""
    print("🧪 Starting UCL Auction Scoring Service Tests")
    print("=" * 60)
    
    test_suite = TestScoringService()
    
    tests = [
        test_suite.test_win_scenario,
        test_suite.test_draw_scenario,
        test_suite.test_zero_zero_draw,
        test_suite.test_duplicate_result_idempotency,
        test_suite.test_unknown_club_no_points,
        test_suite.test_matchday_bucket_calculation,
        test_suite.test_league_standings,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        finally:
            # Clean up after each test
            await test_suite.cleanup_test_data()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return failed == 0

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)