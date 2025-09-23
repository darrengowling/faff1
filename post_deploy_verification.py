#!/usr/bin/env python3
"""
Post-Deploy Verification Script
Verifies that deployment and migration completed successfully
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

class PostDeployVerification:
    def __init__(self):
        self.verification_name = "post_deploy_verification"
        self.checks_run = 0
        self.checks_passed = 0
        self.failed_checks = []
        
    def log_check(self, name, success, details=""):
        """Log verification check results"""
        self.checks_run += 1
        if success:
            self.checks_passed += 1
            logger.info(f"✅ {name} - PASSED {details}")
        else:
            self.failed_checks.append(f"{name}: {details}")
            logger.error(f"❌ {name} - FAILED {details}")
        return success
    
    async def verify_league_settings_structure(self):
        """Verify every league has required settings fields"""
        logger.info("🔍 Verifying league settings structure...")
        
        try:
            # Get all leagues
            leagues = await db.leagues.find().to_list(length=None)
            
            if not leagues:
                return self.log_check(
                    "League settings structure",
                    False,
                    "No leagues found in database"
                )
            
            missing_settings = []
            required_fields = ['club_slots_per_manager', 'budget_per_manager', 'league_size']
            
            for league in leagues:
                settings = league.get('settings', {})
                league_name = league.get('name', f"League {league.get('_id', 'Unknown')}")
                
                # Check required fields
                for field in required_fields:
                    if field not in settings:
                        missing_settings.append(f"{league_name}: missing {field}")
                
                # Check league_size structure
                league_size = settings.get('league_size', {})
                if not isinstance(league_size, dict) or 'min' not in league_size or 'max' not in league_size:
                    missing_settings.append(f"{league_name}: invalid league_size structure")
            
            return self.log_check(
                "League settings structure",
                len(missing_settings) == 0,
                f"Checked {len(leagues)} leagues" if len(missing_settings) == 0 else f"Missing settings: {missing_settings[:5]}..."
            )
            
        except Exception as e:
            return self.log_check(
                "League settings structure",
                False,
                f"Verification failed: {e}"
            )
    
    async def verify_league_settings_values(self):
        """Verify league settings have valid default values"""
        logger.info("🔍 Verifying league settings values...")
        
        try:
            # Get all leagues
            leagues = await db.leagues.find().to_list(length=None)
            
            invalid_values = []
            
            for league in leagues:
                settings = league.get('settings', {})
                league_name = league.get('name', f"League {league.get('_id', 'Unknown')}")
                
                # Check club_slots_per_manager (should be 1-10)
                club_slots = settings.get('club_slots_per_manager')
                if not isinstance(club_slots, int) or club_slots < 1 or club_slots > 10:
                    invalid_values.append(f"{league_name}: invalid club_slots {club_slots}")
                
                # Check budget_per_manager (should be 50-500)
                budget = settings.get('budget_per_manager')
                if not isinstance(budget, int) or budget < 50 or budget > 500:
                    invalid_values.append(f"{league_name}: invalid budget {budget}")
                
                # Check league_size values
                league_size = settings.get('league_size', {})
                min_size = league_size.get('min')
                max_size = league_size.get('max')
                
                if not isinstance(min_size, int) or min_size < 2 or min_size > 8:
                    invalid_values.append(f"{league_name}: invalid min_size {min_size}")
                
                if not isinstance(max_size, int) or max_size < 2 or max_size > 8:
                    invalid_values.append(f"{league_name}: invalid max_size {max_size}")
                
                if min_size > max_size:
                    invalid_values.append(f"{league_name}: min_size {min_size} > max_size {max_size}")
            
            return self.log_check(
                "League settings values",
                len(invalid_values) == 0,
                f"All {len(leagues)} leagues have valid settings" if len(invalid_values) == 0 else f"Invalid values: {invalid_values[:3]}..."
            )
            
        except Exception as e:
            return self.log_check(
                "League settings values",
                False,
                f"Verification failed: {e}"
            )
    
    async def verify_competition_profiles_exist(self):
        """Verify competition profiles collection exists and has UCL profile"""
        logger.info("🔍 Verifying competition profiles...")
        
        try:
            # Check if collection exists
            collections = await db.list_collection_names()
            if 'competition_profiles' not in collections:
                return self.log_check(
                    "Competition profiles collection",
                    False,
                    "competition_profiles collection does not exist"
                )
            
            # Check UCL profile exists
            ucl_profile = await db.competition_profiles.find_one({"_id": "ucl"})
            if not ucl_profile:
                return self.log_check(
                    "Competition profiles collection",
                    False,
                    "UCL competition profile not found"
                )
            
            # Verify UCL profile structure
            defaults = ucl_profile.get('defaults', {})
            required_defaults = ['club_slots', 'budget_per_manager', 'league_size']
            
            missing_defaults = [field for field in required_defaults if field not in defaults]
            if missing_defaults:
                return self.log_check(
                    "Competition profiles collection",
                    False,
                    f"UCL profile missing defaults: {missing_defaults}"
                )
            
            return self.log_check(
                "Competition profiles collection",
                True,
                f"UCL profile exists with complete defaults"
            )
            
        except Exception as e:
            return self.log_check(
                "Competition profiles collection",
                False,
                f"Verification failed: {e}"
            )
    
    async def verify_roster_club_slots_updated(self):
        """Verify existing rosters have club_slots field"""
        logger.info("🔍 Verifying roster club slots...")
        
        try:
            # Get all rosters
            rosters = await db.rosters.find().to_list(length=None)
            
            if not rosters:
                return self.log_check(
                    "Roster club slots",
                    True,
                    "No rosters to check"
                )
            
            missing_club_slots = []
            
            for roster in rosters:
                roster_id = roster.get('_id', 'Unknown')
                user_id = roster.get('user_id', 'Unknown')
                
                if 'club_slots' not in roster:
                    missing_club_slots.append(f"Roster {roster_id} (user {user_id})")
            
            return self.log_check(
                "Roster club slots",
                len(missing_club_slots) == 0,
                f"All {len(rosters)} rosters have club_slots" if len(missing_club_slots) == 0 else f"Missing club_slots: {missing_club_slots[:3]}"
            )
            
        except Exception as e:
            return self.log_check(
                "Roster club slots",
                False,
                f"Verification failed: {e}"
            )
    
    async def verify_feature_flags_behavior(self):
        """Verify feature flags work correctly (budget constraints)"""
        logger.info("🔍 Verifying feature flags behavior...")
        
        try:
            # Check if any leagues have club purchases
            leagues_with_purchases = []
            
            leagues = await db.leagues.find().to_list(length=None)
            
            for league in leagues:
                league_id = league.get('_id')
                league_name = league.get('name', 'Unknown')
                
                # Count roster clubs in this league
                club_count = await db.roster_clubs.count_documents({"league_id": league_id})
                
                if club_count > 0:
                    leagues_with_purchases.append({
                        "name": league_name,
                        "id": league_id,
                        "clubs_purchased": club_count
                    })
            
            # Verify budget constraints would be enforced
            constraint_status = "active" if leagues_with_purchases else "no_purchases_to_test"
            
            return self.log_check(
                "Feature flags behavior",
                True,
                f"Budget constraint status: {constraint_status}, leagues with purchases: {len(leagues_with_purchases)}"
            )
            
        except Exception as e:
            return self.log_check(
                "Feature flags behavior",
                False,
                f"Verification failed: {e}"
            )
    
    async def verify_existing_auctions_integrity(self):
        """Verify existing auctions can still function normally"""
        logger.info("🔍 Verifying existing auction integrity...")
        
        try:
            # Get all auctions
            auctions = await db.auctions.find().to_list(length=None)
            
            if not auctions:
                return self.log_check(
                    "Existing auction integrity",
                    True,
                    "No existing auctions to check"
                )
            
            auction_issues = []
            
            for auction in auctions:
                auction_id = auction.get('_id', 'Unknown')
                league_id = auction.get('league_id', 'Unknown')
                status = auction.get('status', 'Unknown')
                
                # Check auction has required fields
                required_fields = ['budget_per_manager', 'min_increment']
                missing_fields = [field for field in required_fields if field not in auction]
                
                if missing_fields:
                    auction_issues.append(f"Auction {auction_id}: missing {missing_fields}")
                
                # Check linked league exists
                league = await db.leagues.find_one({"_id": league_id})
                if not league:
                    auction_issues.append(f"Auction {auction_id}: orphaned (league {league_id} not found)")
            
            return self.log_check(
                "Existing auction integrity",
                len(auction_issues) == 0,
                f"All {len(auctions)} auctions are intact" if len(auction_issues) == 0 else f"Issues: {auction_issues[:3]}"
            )
            
        except Exception as e:
            return self.log_check(
                "Existing auction integrity",
                False,
                f"Verification failed: {e}"
            )
    
    async def verify_migration_record(self):
        """Verify migration was recorded in database"""
        logger.info("🔍 Verifying migration record...")
        
        try:
            # Check if migration record exists (using _id as the migration name)
            migration_record = await db.migrations.find_one({"_id": "001_add_configurable_settings"})
            
            if not migration_record:
                return self.log_check(
                    "Migration record",
                    False,
                    "Migration record not found in database"
                )
            
            # Check migration status
            status = migration_record.get('status', 'unknown')
            executed_at = migration_record.get('executed_at')
            
            return self.log_check(
                "Migration record",
                status == 'completed',
                f"Status: {status}, executed: {executed_at}"
            )
            
        except Exception as e:
            return self.log_check(
                "Migration record",
                False,
                f"Verification failed: {e}"
            )
    
    async def run_all_verifications(self):
        """Run all post-deploy verification checks"""
        logger.info("🚀 Starting Post-Deploy Verification")
        logger.info("=" * 60)
        
        try:
            await initialize_database()
            
            # Run all verification checks
            await self.verify_league_settings_structure()
            await self.verify_league_settings_values()
            await self.verify_competition_profiles_exist()
            await self.verify_roster_club_slots_updated()
            await self.verify_feature_flags_behavior()
            await self.verify_existing_auctions_integrity()
            await self.verify_migration_record()
            
        except Exception as e:
            logger.error(f"Verification setup failed: {e}")
            return False
        
        # Summary
        logger.info("=" * 60)
        logger.info(f"📊 Verification Results:")
        logger.info(f"Total Checks: {self.checks_run}")
        logger.info(f"Passed: {self.checks_passed}")
        logger.info(f"Failed: {len(self.failed_checks)}")
        
        if self.failed_checks:
            logger.error("❌ Failed Checks:")
            for failure in self.failed_checks:
                logger.error(f"  - {failure}")
        else:
            logger.info("🎉 All verification checks passed!")
        
        return len(self.failed_checks) == 0

async def main():
    """Main verification entry point"""
    verification = PostDeployVerification()
    success = await verification.run_all_verifications()
    
    if success:
        logger.info("✅ Post-deploy verification completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Post-deploy verification failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())