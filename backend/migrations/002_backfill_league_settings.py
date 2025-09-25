#!/usr/bin/env python3
"""
Migration 002: Backfill League Settings
- Add missing leagueSize to existing leagues (default: {min: 2, max: 8})
- Add missing clubSlots to existing leagues (use current effective value)
- Remove hardcoded fallbacks by ensuring all leagues have proper settings
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / '.env')

async def get_db():
    """Get database connection"""
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

async def backfill_league_settings():
    """Backfill missing league settings"""
    
    db = await get_db()
    
    print("🔧 Starting League Settings Backfill Migration...")
    print(f"⏰ Migration started at: {datetime.now(timezone.utc)}")
    
    try:
        # Find all leagues
        leagues = await db.leagues.find({}).to_list(length=None)
        print(f"📊 Found {len(leagues)} leagues to check")
        
        updates_made = 0
        
        for league in leagues:
            league_id = league.get('_id', 'unknown')
            settings = league.get('settings', {})
            updates_needed = {}
            
            print(f"\n🔍 Checking league: {league_id}")
            
            # 1. Check for missing league_size
            if 'league_size' not in settings:
                updates_needed['settings.league_size'] = {'min': 2, 'max': 8}
                print(f"  ➕ Adding missing league_size: {{'min': 2, 'max': 8}}")
            else:
                # Check if league_size is missing min or max
                league_size = settings['league_size']
                if not isinstance(league_size, dict) or 'min' not in league_size or 'max' not in league_size:
                    updates_needed['settings.league_size'] = {'min': 2, 'max': 8}
                    print(f"  🔧 Fixing invalid league_size: {{'min': 2, 'max': 8}}")
            
            # 2. Check for missing club_slots_per_manager
            if 'club_slots_per_manager' not in settings:
                # Try to determine current effective value from rosters
                roster_count = await db.rosters.count_documents({'league_id': league_id})
                if roster_count > 0:
                    # Find a roster with clubs to determine effective slots
                    sample_roster = await db.rosters.find_one({
                        'league_id': league_id,
                        'clubs': {'$exists': True, '$ne': []}
                    })
                    
                    if sample_roster and sample_roster.get('clubs'):
                        # Use the length of clubs as a hint, but cap at reasonable values
                        effective_slots = min(max(len(sample_roster['clubs']), 3), 8)
                    else:
                        # Default to 5 (updated default from competitionProfiles)
                        effective_slots = 5
                else:
                    # No rosters exist, use updated default
                    effective_slots = 5
                
                updates_needed['settings.club_slots_per_manager'] = effective_slots
                print(f"  ➕ Adding missing club_slots_per_manager: {effective_slots}")
            
            # 3. Check for any settings structure issues
            if 'budget_per_manager' not in settings:
                updates_needed['settings.budget_per_manager'] = 100
                print(f"  ➕ Adding missing budget_per_manager: 100")
            
            if 'min_increment' not in settings:
                updates_needed['settings.min_increment'] = 1
                print(f"  ➕ Adding missing min_increment: 1")
            
            if 'anti_snipe_seconds' not in settings:
                updates_needed['settings.anti_snipe_seconds'] = 30
                print(f"  ➕ Adding missing anti_snipe_seconds: 30")
            
            if 'bid_timer_seconds' not in settings:
                updates_needed['settings.bid_timer_seconds'] = 60
                print(f"  ➕ Adding missing bid_timer_seconds: 60")
            
            # Apply updates if needed
            if updates_needed:
                await db.leagues.update_one(
                    {'_id': league_id},
                    {
                        '$set': {
                            **updates_needed,
                            'updated_at': datetime.now(timezone.utc)
                        }
                    }
                )
                updates_made += 1
                print(f"  ✅ Updated league {league_id}")
            else:
                print(f"  ✅ League {league_id} already has complete settings")
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"📊 Total leagues processed: {len(leagues)}")
        print(f"🔧 Leagues updated: {updates_made}")
        print(f"⏰ Migration completed at: {datetime.now(timezone.utc)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

async def verify_migration():
    """Verify that the migration was successful"""
    
    db = await get_db()
    
    print("\n🔍 Verifying migration results...")
    
    # Check for leagues missing required settings
    leagues_missing_league_size = await db.leagues.count_documents({
        '$or': [
            {'settings.league_size': {'$exists': False}},
            {'settings.league_size.min': {'$exists': False}},
            {'settings.league_size.max': {'$exists': False}}
        ]
    })
    
    leagues_missing_club_slots = await db.leagues.count_documents({
        'settings.club_slots_per_manager': {'$exists': False}
    })
    
    total_leagues = await db.leagues.count_documents({})
    
    print(f"📊 Total leagues: {total_leagues}")
    print(f"❌ Missing league_size: {leagues_missing_league_size}")
    print(f"❌ Missing club_slots_per_manager: {leagues_missing_club_slots}")
    
    if leagues_missing_league_size == 0 and leagues_missing_club_slots == 0:
        print("✅ All leagues have complete settings!")
        return True
    else:
        print("❌ Some leagues still missing settings")
        return False

async def main():
    """Run the migration"""
    print("🚀 Starting League Settings Backfill Migration")
    
    # Run the migration
    success = await backfill_league_settings()
    
    if success:
        # Verify the results
        verified = await verify_migration()
        if verified:
            print("\n🎉 Migration completed and verified successfully!")
        else:
            print("\n⚠️  Migration completed but verification failed")
            sys.exit(1)
    else:
        print("\n❌ Migration failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())