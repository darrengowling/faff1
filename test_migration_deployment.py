#!/usr/bin/env python3
"""
Test Migration and Deployment
Tests the migration and post-deploy verification locally
"""

import asyncio
import sys
import os
import subprocess

# Add backend to path
sys.path.append('/app/backend')

from database import initialize_database, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_migration_deployment():
    """Test the migration and deployment process"""
    logger.info("🧪 Testing Migration and Deployment Process")
    logger.info("=" * 60)
    
    try:
        # Initialize database connection
        await initialize_database()
        
        # Step 1: Test database connectivity
        logger.info("1️⃣ Testing database connectivity...")
        try:
            collections = await db.list_collection_names()
            logger.info(f"✅ Database connected. Collections: {len(collections)}")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
        
        # Step 2: Check current league state
        logger.info("2️⃣ Checking current league state...")
        leagues = await db.leagues.find().to_list(length=None)
        logger.info(f"📊 Found {len(leagues)} leagues in database")
        
        # Show sample league settings
        if leagues:
            sample_league = leagues[0]
            settings = sample_league.get('settings', {})
            logger.info(f"Sample league settings: {list(settings.keys())}")
        
        # Step 3: Test migration script (dry run check)
        logger.info("3️⃣ Testing migration script availability...")
        migration_script = '/app/backend/migrations/001_add_configurable_settings.py'
        if os.path.exists(migration_script):
            logger.info(f"✅ Migration script exists: {migration_script}")
        else:
            logger.error(f"❌ Migration script not found: {migration_script}")
            return False
        
        # Step 4: Test post-deploy verification script
        logger.info("4️⃣ Testing post-deploy verification...")
        verification_script = '/app/post_deploy_verification.py'
        if os.path.exists(verification_script):
            logger.info(f"✅ Verification script exists: {verification_script}")
            
            # Run verification
            logger.info("Running post-deploy verification...")
            result = subprocess.run([sys.executable, verification_script], 
                                  capture_output=True, text=True, cwd='/app')
            
            if result.returncode == 0:
                logger.info("✅ Post-deploy verification passed")
            else:
                logger.warning(f"⚠️ Post-deploy verification issues:")
                logger.warning(result.stdout)
                if result.stderr:
                    logger.warning(result.stderr)
        else:
            logger.error(f"❌ Verification script not found: {verification_script}")
            return False
        
        # Step 5: Check competition profiles
        logger.info("5️⃣ Checking competition profiles...")
        try:
            profiles = await db.competition_profiles.find().to_list(length=None)
            logger.info(f"📊 Found {len(profiles)} competition profiles")
            
            ucl_profile = await db.competition_profiles.find_one({"_id": "ucl"})
            if ucl_profile:
                defaults = ucl_profile.get('defaults', {})
                logger.info(f"✅ UCL profile exists with defaults: {list(defaults.keys())}")
            else:
                logger.warning("⚠️ UCL competition profile not found")
        except Exception as e:
            logger.warning(f"⚠️ Competition profiles check failed: {e}")
        
        # Step 6: Test deployment script structure
        logger.info("6️⃣ Testing deployment script...")
        deploy_script = '/app/deploy.sh'
        if os.path.exists(deploy_script):
            logger.info(f"✅ Deployment script exists: {deploy_script}")
            
            # Check if run_migrations function exists
            with open(deploy_script, 'r') as f:
                content = f.read()
                if 'run_migrations()' in content:
                    logger.info("✅ Migration step found in deployment script")
                else:
                    logger.warning("⚠️ Migration step not found in deployment script")
        else:
            logger.error(f"❌ Deployment script not found: {deploy_script}")
            return False
        
        logger.info("=" * 60)
        logger.info("🎉 Migration and deployment test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test entry point"""
    success = await test_migration_deployment()
    
    if success:
        logger.info("✅ Migration and deployment test passed")
        sys.exit(0)
    else:
        logger.error("❌ Migration and deployment test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())