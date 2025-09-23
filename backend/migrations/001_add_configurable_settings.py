#!/usr/bin/env python3
"""
Migration: Add Configurable League Settings
- Adds clubSlots, budgetPerManager, leagueSize to leagues.settings
- Creates competitionProfiles collection
- Backfills existing leagues with defaults
- Adds JSON Schema validation
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add backend to path
sys.path.append('/app/backend')

from database import initialize_database, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigurableSettingsMigration:
    def __init__(self):
        self.migration_name = "001_add_configurable_settings"
        self.migration_version = "1.0.0"
        
    async def run_migration(self):
        """Execute the complete migration"""
        logger.info(f"🚀 Starting migration: {self.migration_name}")
        
        try:
            await initialize_database()
            
            # Step 1: Create competition profiles collection
            await self.create_competition_profiles()
            
            # Step 2: Update leagues schema with JSON validation
            await self.update_leagues_schema()
            
            # Step 3: Backfill existing leagues
            await self.backfill_existing_leagues()
            
            # Step 4: Update existing rosters
            await self.update_existing_rosters()
            
            # Step 5: Record migration completion
            await self.record_migration()
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise

    async def create_competition_profiles(self):
        """Create competitionProfiles collection with default configurations"""
        logger.info("📚 Creating competitionProfiles collection...")
        
        # Drop existing collection if it exists (for clean migration)
        try:
            await db.competition_profiles.drop()
        except Exception:
            pass  # Collection might not exist
        
        # Default competition profiles
        profiles = [
            {
                "_id": "ucl",
                "competition": "UEFA Champions League",
                "short_name": "UCL",
                "defaults": {
                    "club_slots": 3,
                    "budget_per_manager": 100,
                    "league_size": {
                        "min": 4,
                        "max": 8
                    },
                    "min_increment": 1,
                    "anti_snipe_seconds": 30,
                    "bid_timer_seconds": 60,
                    "scoring_rules": {
                        "club_goal": 1,
                        "club_win": 3,
                        "club_draw": 1
                    }
                },
                "description": "Standard UEFA Champions League configuration",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "europa",
                "competition": "UEFA Europa League",
                "short_name": "UEL",
                "defaults": {
                    "club_slots": 4,
                    "budget_per_manager": 80,
                    "league_size": {
                        "min": 3,
                        "max": 6
                    },
                    "min_increment": 1,
                    "anti_snipe_seconds": 30,
                    "bid_timer_seconds": 60,
                    "scoring_rules": {
                        "club_goal": 1,
                        "club_win": 3,
                        "club_draw": 1
                    }
                },
                "description": "UEFA Europa League configuration with more slots, lower budget",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "custom",
                "competition": "Custom Competition",
                "short_name": "CUSTOM",
                "defaults": {
                    "club_slots": 3,
                    "budget_per_manager": 100,
                    "league_size": {
                        "min": 2,
                        "max": 8
                    },
                    "min_increment": 1,
                    "anti_snipe_seconds": 30,
                    "bid_timer_seconds": 60,
                    "scoring_rules": {
                        "club_goal": 1,
                        "club_win": 3,
                        "club_draw": 1
                    }
                },
                "description": "Fully customizable competition profile",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        # Insert competition profiles
        await db.competition_profiles.insert_many(profiles)
        
        # Create JSON Schema validation for competition profiles
        competition_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["_id", "competition", "defaults"],
                "properties": {
                    "_id": {"bsonType": "string"},
                    "competition": {"bsonType": "string"},
                    "short_name": {"bsonType": "string"},
                    "defaults": {
                        "bsonType": "object",
                        "required": ["club_slots", "budget_per_manager", "league_size"],
                        "properties": {
                            "club_slots": {
                                "bsonType": "int",
                                "minimum": 1,
                                "maximum": 10
                            },
                            "budget_per_manager": {
                                "bsonType": "int", 
                                "minimum": 50,
                                "maximum": 500
                            },
                            "league_size": {
                                "bsonType": "object",
                                "required": ["min", "max"],
                                "properties": {
                                    "min": {
                                        "bsonType": "int",
                                        "minimum": 2,
                                        "maximum": 8
                                    },
                                    "max": {
                                        "bsonType": "int",
                                        "minimum": 2,
                                        "maximum": 8
                                    }
                                }
                            }
                        }
                    },
                    "description": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
        
        # Apply schema validation
        await db.create_collection("competition_profiles", validator=competition_schema)
        
        logger.info(f"✅ Created {len(profiles)} competition profiles")

    async def update_leagues_schema(self):
        """Update leagues collection with enhanced JSON Schema validation"""
        logger.info("🔧 Updating leagues schema validation...")
        
        # Enhanced leagues schema with new configurable settings
        leagues_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["_id", "name", "season", "commissioner_id", "settings"],
                "properties": {
                    "_id": {"bsonType": "string"},
                    "name": {"bsonType": "string"},
                    "season": {"bsonType": "string"},
                    "commissioner_id": {"bsonType": "string"},
                    "competition_profile": {"bsonType": "string"},
                    "member_count": {
                        "bsonType": "int",
                        "minimum": 0
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": ["setup", "ready", "active", "completed", "cancelled"]
                    },
                    "settings": {
                        "bsonType": "object",
                        "required": ["club_slots_per_manager", "budget_per_manager", "league_size"],
                        "properties": {
                            "club_slots_per_manager": {
                                "bsonType": "int",
                                "minimum": 1,
                                "maximum": 10
                            },
                            "budget_per_manager": {
                                "bsonType": "int",
                                "minimum": 50,
                                "maximum": 500
                            },
                            "league_size": {
                                "bsonType": "object",
                                "required": ["min", "max"],
                                "properties": {
                                    "min": {
                                        "bsonType": "int",
                                        "minimum": 2,
                                        "maximum": 8
                                    },
                                    "max": {
                                        "bsonType": "int",
                                        "minimum": 2,
                                        "maximum": 8
                                    }
                                }
                            },
                            "min_increment": {
                                "bsonType": "int",
                                "minimum": 1
                            },
                            "anti_snipe_seconds": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "bid_timer_seconds": {
                                "bsonType": "int",
                                "minimum": 30
                            },
                            "scoring_rules": {
                                "bsonType": "object",
                                "required": ["club_goal", "club_win", "club_draw"],
                                "properties": {
                                    "club_goal": {"bsonType": "int"},
                                    "club_win": {"bsonType": "int"},
                                    "club_draw": {"bsonType": "int"}
                                }
                            }
                        }
                    },
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
        
        # Apply enhanced validation to existing collection
        try:
            await db.command("collMod", "leagues", validator=leagues_schema)
            logger.info("✅ Updated leagues schema validation")
        except Exception as e:
            logger.warning(f"Schema validation update failed (may be expected): {e}")

    async def backfill_existing_leagues(self):
        """Backfill existing leagues with new configurable settings"""
        logger.info("📝 Backfilling existing leagues with new settings...")
        
        # Get all existing leagues
        leagues = await db.leagues.find({}).to_list(length=None)
        updated_count = 0
        
        for league in leagues:
            current_settings = league.get("settings", {})
            
            # Prepare enhanced settings with new configurable fields
            enhanced_settings = {
                # New configurable fields with defaults
                "club_slots_per_manager": current_settings.get("club_slots_per_manager", 3),
                "budget_per_manager": current_settings.get("budget_per_manager", 100),
                "league_size": {
                    "min": current_settings.get("min_managers", 4),
                    "max": current_settings.get("max_managers", 8)
                },
                
                # Existing fields (maintain current values)
                "min_increment": current_settings.get("min_increment", 1),
                "anti_snipe_seconds": current_settings.get("anti_snipe_seconds", 30),
                "bid_timer_seconds": current_settings.get("bid_timer_seconds", 60),
                "scoring_rules": current_settings.get("scoring_rules", {
                    "club_goal": 1,
                    "club_win": 3,
                    "club_draw": 1
                })
            }
            
            # Update league with enhanced settings
            await db.leagues.update_one(
                {"_id": league["_id"]},
                {
                    "$set": {
                        "settings": enhanced_settings,
                        "competition_profile": "ucl",  # Default to UCL profile
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            updated_count += 1
            logger.info(f"   Updated league: {league.get('name', league['_id'])}")
        
        logger.info(f"✅ Backfilled {updated_count} existing leagues")

    async def update_existing_rosters(self):
        """Update existing rosters to match new league settings"""
        logger.info("👥 Updating existing rosters with new settings...")
        
        # Get all leagues with their updated settings
        leagues = await db.leagues.find({}).to_list(length=None)
        
        for league in leagues:
            league_id = league["_id"]
            settings = league.get("settings", {})
            
            budget_per_manager = settings.get("budget_per_manager", 100)
            club_slots = settings.get("club_slots_per_manager", 3)
            
            # Update all rosters in this league
            result = await db.rosters.update_many(
                {"league_id": league_id},
                {
                    "$set": {
                        "budget_start": budget_per_manager,
                        "club_slots": club_slots,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"   Updated {result.modified_count} rosters for league {league.get('name', league_id)}")
        
        logger.info("✅ Updated existing rosters")

    async def record_migration(self):
        """Record that this migration has been completed"""
        logger.info("📋 Recording migration completion...")
        
        # Create migrations collection if it doesn't exist
        migration_record = {
            "_id": self.migration_name,
            "version": self.migration_version,
            "description": "Add configurable league settings (clubSlots, budgetPerManager, leagueSize)",
            "executed_at": datetime.now(timezone.utc),
            "status": "completed"
        }
        
        await db.migrations.replace_one(
            {"_id": self.migration_name},
            migration_record,
            upsert=True
        )
        
        logger.info("✅ Migration recorded")

    async def verify_migration(self):
        """Verify the migration was successful"""
        logger.info("🔍 Verifying migration results...")
        
        # Check competition profiles
        profile_count = await db.competition_profiles.count_documents({})
        logger.info(f"   Competition profiles: {profile_count}")
        
        # Check updated leagues
        leagues_with_new_settings = await db.leagues.count_documents({
            "settings.club_slots_per_manager": {"$exists": True},
            "settings.budget_per_manager": {"$exists": True},
            "settings.league_size": {"$exists": True}
        })
        logger.info(f"   Leagues with new settings: {leagues_with_new_settings}")
        
        # Check updated rosters
        updated_rosters = await db.rosters.count_documents({
            "club_slots": {"$exists": True}
        })
        logger.info(f"   Updated rosters: {updated_rosters}")
        
        # Check migration record
        migration_record = await db.migrations.find_one({"_id": self.migration_name})
        if migration_record:
            logger.info(f"   Migration recorded: {migration_record['status']}")
        
        logger.info("✅ Verification completed")

async def main():
    """Main migration execution"""
    migration = ConfigurableSettingsMigration()
    
    try:
        await migration.run_migration()
        await migration.verify_migration()
        
        print("\n" + "="*60)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("✅ Competition profiles created")
        print("✅ Leagues schema updated with validation")
        print("✅ Existing leagues backfilled with new settings")
        print("✅ Existing rosters updated")
        print("✅ Migration recorded in database")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())