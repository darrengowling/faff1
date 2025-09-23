#!/usr/bin/env python3
"""
Test script to verify configurable league settings work correctly
"""

import asyncio
import sys
import json

# Add backend to path
sys.path.append('/app/backend')

from database import initialize_database, db
from models import *
from admin_service import AdminService

async def test_configuration_changes():
    """Test the new configurable league settings"""
    print("🔧 Testing Configurable League Settings...")
    print("=" * 50)
    
    await initialize_database()
    
    # Find a demo league to test with
    demo_league = await db.leagues.find_one({"name": {"$regex": "Demo"}})
    if not demo_league:
        print("❌ No demo league found. Run seed script first.")
        return
    
    league_id = demo_league["_id"]
    print(f"✅ Found demo league: {league_id}")
    
    # Find commissioner
    commissioner = await db.memberships.find_one({
        "league_id": league_id,
        "role": "commissioner"
    })
    
    if not commissioner:
        print("❌ No commissioner found for demo league")
        return
    
    actor_id = commissioner["user_id"]
    print(f"✅ Found commissioner: {actor_id}")
    
    # Test 1: Valid configuration changes
    print("\n📝 Test 1: Valid Configuration Changes")
    
    updates = LeagueSettingsUpdate(
        budget_per_manager=150,  # Change from 100 to 150
        club_slots_per_manager=4,  # Change from 3 to 4  
        max_managers=6,  # Change max from 8 to 6
        min_managers=3   # Change min from 4 to 3
    )
    
    result = await AdminService.update_league_settings(league_id, actor_id, updates)
    if result["success"]:
        print("✅ Configuration changes applied successfully")
        print(f"   Message: {result['message']}")
    else:
        print(f"❌ Configuration changes failed: {result['message']}")
    
    # Test 2: Invalid budget change (when purchases exist)
    print("\n📝 Test 2: Invalid Budget Change (with purchases)")
    
    # Create a fake purchase to test constraint
    fake_purchase = {
        "_id": "test-purchase-123",
        "league_id": league_id,
        "user_id": actor_id,
        "club_id": "test-club-123",
        "price": 25
    }
    await db.roster_clubs.insert_one(fake_purchase)
    print("   Created fake purchase to test constraint")
    
    invalid_updates = LeagueSettingsUpdate(budget_per_manager=200)
    result = await AdminService.update_league_settings(league_id, actor_id, invalid_updates)
    
    if not result["success"]:
        print("✅ Budget change correctly blocked with purchases")
        print(f"   Error: {result['message']}")
    else:
        print("❌ Budget change should have been blocked")
    
    # Clean up fake purchase
    await db.roster_clubs.delete_one({"_id": "test-purchase-123"})
    print("   Cleaned up fake purchase")
    
    # Test 3: Invalid club slots decrease
    print("\n📝 Test 3: Invalid Club Slots Decrease")
    
    # Create fake roster with too many clubs
    fake_roster_clubs = [
        {
            "_id": f"test-club-{i}",
            "league_id": league_id,
            "user_id": actor_id,
            "club_id": f"fake-club-{i}",
            "price": 20
        }
        for i in range(5)  # 5 clubs when trying to set limit to 2
    ]
    
    await db.roster_clubs.insert_many(fake_roster_clubs)
    print("   Created fake roster with 5 clubs")
    
    invalid_updates = LeagueSettingsUpdate(club_slots_per_manager=2)
    result = await AdminService.update_league_settings(league_id, actor_id, invalid_updates)
    
    if not result["success"]:
        print("✅ Club slots decrease correctly blocked")
        print(f"   Error: {result['message']}")
    else:
        print("❌ Club slots decrease should have been blocked")
    
    # Clean up fake clubs
    await db.roster_clubs.delete_many({"_id": {"$in": [f"test-club-{i}" for i in range(5)]}})
    print("   Cleaned up fake clubs")
    
    # Test 4: Invalid league size
    print("\n📝 Test 4: Invalid League Size")
    
    current_members = demo_league.get("member_count", 0)
    invalid_updates = LeagueSettingsUpdate(max_managers=max(1, current_members - 1))
    result = await AdminService.update_league_settings(league_id, actor_id, invalid_updates)
    
    if not result["success"]:
        print("✅ League size decrease correctly blocked")
        print(f"   Error: {result['message']}")
    else:
        print("❌ League size decrease should have been blocked")
    
    # Test 5: Verify current settings
    print("\n📝 Test 5: Verify Final Settings")
    
    updated_league = await db.leagues.find_one({"_id": league_id})
    settings = updated_league.get("settings", {})
    
    print("Current league settings:")
    print(f"   Budget per manager: {settings.get('budget_per_manager')}M")
    print(f"   Club slots per manager: {settings.get('club_slots_per_manager')}")
    print(f"   League size: {settings.get('min_managers')}-{settings.get('max_managers')} members")
    print(f"   Current members: {updated_league.get('member_count')}")
    
    # Check if rosters were updated
    sample_roster = await db.rosters.find_one({"league_id": league_id})
    if sample_roster:
        print(f"   Sample roster budget: {sample_roster.get('budget_remaining')}M")
        print(f"   Sample roster slots: {sample_roster.get('club_slots')}")
    
    print("\n✅ Configuration testing completed!")

if __name__ == "__main__":
    asyncio.run(test_configuration_changes())