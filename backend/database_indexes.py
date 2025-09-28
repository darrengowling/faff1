"""
Database Index Management
Ensures unique indexes for scoring data integrity
"""

import asyncio
import logging
from typing import List, Dict
from pymongo import IndexModel, ASCENDING
from pymongo.errors import OperationFailure

from database import db

logger = logging.getLogger(__name__)

class DatabaseIndexManager:
    """Manages database indexes for scoring data integrity"""
    
    @staticmethod
    async def ensure_scoring_indexes() -> Dict[str, bool]:
        """
        Ensure unique indexes for scoring collections to prevent duplicates
        Returns: Dict with collection names and success status
        """
        results = {}
        
        try:
            # 1. settlements collection: unique (leagueId, matchId)
            settlements_indexes = [
                IndexModel([("league_id", ASCENDING), ("match_id", ASCENDING)], unique=True, name="unique_league_match"),
                IndexModel([("league_id", ASCENDING)], name="league_lookup"),
                IndexModel([("match_id", ASCENDING)], name="match_lookup")
            ]
            
            try:
                await db.settlements.create_indexes(settlements_indexes)
                results["settlements"] = True
                logger.info("✅ Settlements indexes created successfully")
            except OperationFailure as e:
                if "already exists" in str(e):
                    results["settlements"] = True
                    logger.info("ℹ️  Settlements indexes already exist")
                else:
                    results["settlements"] = False
                    logger.error(f"❌ Failed to create settlements indexes: {e}")
            
            # 2. weeklyPoints collection: unique (leagueId, userId, matchId)
            weekly_points_indexes = [
                IndexModel([("league_id", ASCENDING), ("user_id", ASCENDING), ("match_id", ASCENDING)], 
                          unique=True, name="unique_league_user_match"),
                IndexModel([("league_id", ASCENDING), ("user_id", ASCENDING)], name="league_user_lookup"),
                IndexModel([("league_id", ASCENDING)], name="league_points_lookup"),
                IndexModel([("match_id", ASCENDING)], name="match_points_lookup")
            ]
            
            try:
                await db.weeklyPoints.create_indexes(weekly_points_indexes)
                results["weeklyPoints"] = True
                logger.info("✅ WeeklyPoints indexes created successfully")
            except OperationFailure as e:
                if "already exists" in str(e):
                    results["weeklyPoints"] = True
                    logger.info("ℹ️  WeeklyPoints indexes already exist")
                else:
                    results["weeklyPoints"] = False
                    logger.error(f"❌ Failed to create weeklyPoints indexes: {e}")
            
            # 3. result_ingest collection: unique (league_id, match_id)
            result_ingest_indexes = [
                IndexModel([("league_id", ASCENDING), ("match_id", ASCENDING)], 
                          unique=True, name="unique_league_match_ingest"),
                IndexModel([("league_id", ASCENDING)], name="league_ingest_lookup"),
                IndexModel([("processed", ASCENDING)], name="processed_lookup"),
                IndexModel([("kicked_off_at", ASCENDING)], name="kickoff_lookup")
            ]
            
            try:
                await db.result_ingest.create_indexes(result_ingest_indexes)
                results["result_ingest"] = True
                logger.info("✅ Result ingest indexes created successfully")
            except OperationFailure as e:
                if "already exists" in str(e):
                    results["result_ingest"] = True
                    logger.info("ℹ️  Result ingest indexes already exist")
                else:
                    results["result_ingest"] = False
                    logger.error(f"❌ Failed to create result ingest indexes: {e}")
            
            # 4. Additional performance indexes
            performance_results = await DatabaseIndexManager._ensure_performance_indexes()
            results.update(performance_results)
            
        except Exception as e:
            logger.error(f"❌ Error ensuring scoring indexes: {e}")
            results["error"] = str(e)
        
        return results
    
    @staticmethod
    async def _ensure_performance_indexes() -> Dict[str, bool]:
        """Ensure performance indexes for common queries"""
        results = {}
        
        try:
            # Users collection indexes
            user_indexes = [
                IndexModel([("email", ASCENDING)], unique=True, name="unique_email"),
                IndexModel([("verified", ASCENDING)], name="verified_lookup")
            ]
            
            await db.users.create_indexes(user_indexes)
            results["users"] = True
            logger.info("✅ User indexes ensured")
            
        except OperationFailure as e:
            if "already exists" in str(e):
                results["users"] = True
            else:
                results["users"] = False
                logger.error(f"❌ Failed to create user indexes: {e}")
        except Exception as e:
            results["users"] = False
            logger.error(f"❌ Error creating user indexes: {e}")
        
        return results
    
    @staticmethod
    async def verify_indexes() -> Dict[str, List[str]]:
        """
        Verify that all required indexes exist
        Returns: Dict with collection names and their indexes
        """
        collections_to_check = [
            "settlements",
            "weeklyPoints", 
            "result_ingest",
            "users"
        ]
        
        results = {}
        
        for collection_name in collections_to_check:
            try:
                collection = getattr(db, collection_name)
                indexes = await collection.list_indexes().to_list(length=None)
                index_names = [idx["name"] for idx in indexes]
                results[collection_name] = index_names
                logger.info(f"📋 {collection_name} indexes: {index_names}")
            except Exception as e:
                results[collection_name] = [f"Error: {str(e)}"]
                logger.error(f"❌ Error checking {collection_name} indexes: {e}")
        
        return results


# Initialization function to be called at startup
async def initialize_scoring_indexes():
    """Initialize all scoring-related indexes"""
    logger.info("🔧 Initializing scoring database indexes...")
    index_manager = DatabaseIndexManager()
    results = await index_manager.ensure_scoring_indexes()
    
    success_count = sum(1 for v in results.values() if v is True)
    total_count = len([k for k in results.keys() if k != "error"])
    
    logger.info(f"📊 Scoring indexes initialized: {success_count}/{total_count} successful")
    
    if "error" in results:
        logger.error(f"❌ Index initialization error: {results['error']}")
    
    return results