#!/usr/bin/env python3
"""
Quick verification script to check demo data integrity
"""

import asyncio
import sys
import json

# Add backend to path
sys.path.append('/app/backend')

from database import initialize_database, db

async def verify_demo():
    """Verify demo data was created correctly"""
    await initialize_database()
    
    print("🔍 Verifying Demo Data...")
    print("=" * 40)
    
    # Check clubs
    clubs = await db.clubs.find({}).to_list(length=None)
    print(f"✅ Clubs: {len(clubs)} found")
    
    # Check demo users
    demo_users = await db.users.find({"email": {"$regex": "@demo\\.com$"}}).to_list(length=None)
    print(f"✅ Demo Users: {len(demo_users)} found")
    
    # Check demo leagues
    demo_leagues = await db.leagues.find({"name": {"$regex": "Demo"}}).to_list(length=None)
    print(f"✅ Demo Leagues: {len(demo_leagues)} found")
    
    if demo_leagues:
        league_id = demo_leagues[0]["_id"]
        
        # Check memberships
        memberships = await db.memberships.find({"league_id": league_id}).to_list(length=None)
        print(f"✅ League Members: {len(memberships)} found")
        
        # Check rosters
        rosters = await db.rosters.find({"league_id": league_id}).to_list(length=None)
        print(f"✅ Member Rosters: {len(rosters)} found")
        
        # Check club ownership
        ownership = await db.roster_clubs.find({"league_id": league_id}).to_list(length=None)
        print(f"✅ Club Ownership: {len(ownership)} clubs owned")
        
        # Check fixtures
        fixtures = await db.fixtures.find({"league_id": league_id}).to_list(length=None)
        print(f"✅ Fixtures: {len(fixtures)} loaded")
        
        # Check results
        results = await db.result_ingest.find({"league_id": league_id}).to_list(length=None)
        print(f"✅ Results: {len(results)} processed")
        
        # Check auctions
        auctions = await db.auctions.find({"league_id": league_id}).to_list(length=None)
        print(f"✅ Auctions: {len(auctions)} found")
        
        if auctions:
            auction_id = auctions[0]["_id"]
            lots = await db.lots.find({"auction_id": auction_id}).to_list(length=None)
            print(f"✅ Auction Lots: {len(lots)} created")
            
        print("=" * 40)
        print("🎉 Demo verification completed!")
        print(f"🏆 League ID: {league_id}")
        print("🔗 Ready for testing!")
    else:
        print("❌ No demo leagues found!")

if __name__ == "__main__":
    asyncio.run(verify_demo())