#!/usr/bin/env python3
"""
Seed UCL Competition Profile
Creates the UCL competition profile with default settings
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add backend to path
sys.path.append('/app/backend')

from database import initialize_database, db
from models import CompetitionProfile, CompetitionDefaults, LeagueSize, ScoringRulePoints

async def seed_ucl_profile():
    """Create UCL competition profile with default settings"""
    try:
        await initialize_database()
        
        # Check if UCL profile already exists
        existing_profile = await db.competition_profiles.find_one({"_id": "ucl"})
        if existing_profile:
            print("✅ UCL competition profile already exists")
            return
        
        # Create UCL competition profile
        ucl_profile = CompetitionProfile(
            id="ucl",
            competition="UEFA Champions League",
            short_name="UCL",
            description="Default settings for UEFA Champions League fantasy auction",
            defaults=CompetitionDefaults(
                club_slots=3,
                budget_per_manager=100,
                league_size=LeagueSize(min=4, max=8),
                min_increment=1,
                anti_snipe_seconds=30,
                bid_timer_seconds=60,
                scoring_rules=ScoringRulePoints(
                    club_goal=1,
                    club_win=3,
                    club_draw=1
                )
            )
        )
        
        # Insert into database
        profile_dict = ucl_profile.model_dump(by_alias=True)
        await db.competition_profiles.insert_one(profile_dict)
        
        print("✅ Created UCL competition profile successfully")
        print(f"   - Competition: {ucl_profile.competition}")
        print(f"   - Budget per manager: {ucl_profile.defaults.budget_per_manager}M")
        print(f"   - Club slots: {ucl_profile.defaults.club_slots}")
        print(f"   - League size: {ucl_profile.defaults.league_size.min}-{ucl_profile.defaults.league_size.max}")
        
    except Exception as e:
        print(f"❌ Failed to create UCL competition profile: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_ucl_profile())