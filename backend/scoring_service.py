import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClientSession
from pymongo.errors import DuplicateKeyError

from models import *
from database import db

logger = logging.getLogger(__name__)

class ScoringService:
    """
    Idempotent scoring service for UCL club matches
    Processes match results and calculates points: +1/goal, +3/win, +1/draw
    """
    
    @staticmethod
    def calculate_matchday_bucket(kicked_off_at: datetime, season: str) -> Dict:
        """
        Calculate matchday bucket from match date
        UCL typically has 6 group stage matchdays, then knockout rounds
        """
        # Simplified matchday calculation based on date
        season_start = datetime(2024, 9, 1, tzinfo=timezone.utc)  # UCL season start
        days_since_start = (kicked_off_at - season_start).days
        
        # Group stage: 6 matchdays (roughly every 2 weeks)
        if days_since_start < 84:  # ~12 weeks for group stage
            matchday = min(6, (days_since_start // 14) + 1)
            return {"type": "matchday", "value": matchday}
        
        # Knockout stage
        knockout_days = days_since_start - 84
        if knockout_days < 30:
            return {"type": "matchday", "value": 7}  # Round of 16
        elif knockout_days < 60:
            return {"type": "matchday", "value": 8}  # Quarter-finals
        elif knockout_days < 90:
            return {"type": "matchday", "value": 9}  # Semi-finals
        else:
            return {"type": "matchday", "value": 10}  # Final
    
    @staticmethod
    async def ingest_result(
        league_id: str,
        match_id: str,
        season: str,
        home_ext: str,
        away_ext: str,
        home_goals: int,
        away_goals: int,
        kicked_off_at: datetime,
        status: str = "final"
    ) -> Dict:
        """
        Ingest match result idempotently
        Returns: {"success": bool, "message": str, "created": bool}
        """
        try:
            # Create result ingest document
            result_ingest = ResultIngest(
                league_id=league_id,
                match_id=match_id,
                home_ext=home_ext,
                away_ext=away_ext,
                home_goals=home_goals,
                away_goals=away_goals,
                kicked_off_at=kicked_off_at,
                status=status,
                processed=False
            )
            
            result_dict = result_ingest.dict(by_alias=True)
            
            # Upsert result (idempotent by leagueId, matchId)
            update_result = await db.result_ingest.update_one(
                {
                    "league_id": league_id,
                    "match_id": match_id
                },
                {"$setOnInsert": result_dict},
                upsert=True
            )
            
            created = update_result.upserted_id is not None
            
            logger.info(f"Result ingested for match {match_id} in league {league_id}, created: {created}")
            
            return {
                "success": True,
                "message": "Result ingested successfully",
                "created": created,
                "result_id": result_dict["_id"] if created else None
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest result for match {match_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to ingest result: {str(e)}",
                "created": False
            }
    
    @staticmethod
    async def process_pending_results(limit: int = 100) -> Dict:
        """
        Process unprocessed results in order (settlement worker)
        Returns processing summary
        """
        try:
            # Get unprocessed results ordered by received_at
            unprocessed_results = await db.result_ingest.find({
                "processed": False
            }).sort("received_at", 1).limit(limit).to_list(length=None)
            
            if not unprocessed_results:
                return {
                    "success": True,
                    "processed_count": 0,
                    "message": "No unprocessed results found"
                }
            
            processed_count = 0
            errors = []
            
            for result in unprocessed_results:
                try:
                    success = await ScoringService._process_single_result(result)
                    if success:
                        processed_count += 1
                    else:
                        errors.append(f"Failed to process result {result['match_id']}")
                except Exception as e:
                    error_msg = f"Error processing result {result['match_id']}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return {
                "success": True,
                "processed_count": processed_count,
                "total_found": len(unprocessed_results),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to process pending results: {e}")
            return {
                "success": False,
                "processed_count": 0,
                "message": f"Processing failed: {str(e)}"
            }
    
    @staticmethod
    async def _process_single_result(result: Dict) -> bool:
        """
        Process a single result with idempotency (adapted for single MongoDB instance)
        Returns True if successfully processed, False otherwise
        """
        try:
            # Check if we're using a single MongoDB instance (no transactions available)
            try:
                # Try transaction-based approach first
                async with await db.client.start_session() as session:
                    async with session.start_transaction():
                        return await ScoringService._process_with_transaction(result, session)
            except Exception as e:
                if "Transaction numbers are only allowed" in str(e):
                    # Fall back to non-transactional approach for local MongoDB
                    logger.info("Using non-transactional processing for local MongoDB")
                    return await ScoringService._process_without_transaction(result)
                else:
                    raise e
        except Exception as e:
            logger.error(f"Failed to process result {result['match_id']}: {e}")
            return False
    
    @staticmethod
    async def _process_with_transaction(result: Dict, session) -> bool:
        """Process result with full transaction support"""
        # 1. Try to create settlement record (idempotency check)
        settlement = Settlement(
            league_id=result["league_id"],
            match_id=result["match_id"]
        )
        settlement_dict = settlement.dict(by_alias=True)
        
        try:
            await db.settlements.insert_one(settlement_dict, session=session)
        except DuplicateKeyError:
            # Already settled, abort transaction
            logger.info(f"Match {result['match_id']} already settled, skipping")
            await session.abort_transaction()
            return True  # Not an error, just already processed
        
        # Continue with processing logic...
        return await ScoringService._complete_processing(result, session)
    
    @staticmethod
    async def _process_without_transaction(result: Dict) -> bool:
        """Process result without transactions (for local MongoDB)"""
        try:
            # 1. Check if already settled (idempotency)
            existing_settlement = await db.settlements.find_one({
                "league_id": result["league_id"],
                "match_id": result["match_id"]
            })
            
            if existing_settlement:
                logger.info(f"Match {result['match_id']} already settled, skipping")
                return True
            
            # 2. Create settlement record
            settlement = Settlement(
                league_id=result["league_id"],
                match_id=result["match_id"]
            )
            settlement_dict = settlement.dict(by_alias=True)
            
            try:
                await db.settlements.insert_one(settlement_dict)
            except DuplicateKeyError:
                # Race condition - another process settled it
                logger.info(f"Match {result['match_id']} settled by another process, skipping")
                return True
            
            # 3. Process the settlement
            return await ScoringService._complete_processing(result, None)
            
        except Exception as e:
            logger.error(f"Failed to process result without transaction: {e}")
            return False
    
    @staticmethod
    async def _complete_processing(result: Dict, session=None) -> bool:
        """Complete the scoring processing logic"""
        try:
            # 2. Resolve club owners from roster_clubs
            home_owners = await ScoringService._get_club_owners(
                result["league_id"], result["home_ext"], session
            )
            away_owners = await ScoringService._get_club_owners(
                result["league_id"], result["away_ext"], session
            )
            
            # 3. Calculate points for each owner
            home_goals = result["home_goals"]
            away_goals = result["away_goals"]
            
            # Determine match result
            if home_goals > away_goals:
                home_result_points = 3  # Win
                away_result_points = 0  # Loss
            elif away_goals > home_goals:
                home_result_points = 0  # Loss
                away_result_points = 3  # Win
            else:
                home_result_points = 1  # Draw
                away_result_points = 1  # Draw
            
            # Calculate matchday bucket
            bucket = ScoringService.calculate_matchday_bucket(
                result["kicked_off_at"], 
                result.get("season", "2024-25")
            )
            
            # 4. Create/update weekly points for home team owners
            for owner_id in home_owners:
                total_points = home_goals + home_result_points  # Goals + result
                await ScoringService._upsert_weekly_points(
                    result["league_id"],
                    owner_id,
                    result["match_id"],
                    total_points,
                    bucket,
                    session
                )
            
            # 5. Create/update weekly points for away team owners
            for owner_id in away_owners:
                total_points = away_goals + away_result_points  # Goals + result
                await ScoringService._upsert_weekly_points(
                    result["league_id"],
                    owner_id,
                    result["match_id"],
                    total_points,
                    bucket,
                    session
                )
            
            # 6. Mark result as processed
            await db.result_ingest.update_one(
                {"_id": result["_id"]},
                {"$set": {"processed": True}},
                **({"session": session} if session else {})
            )
            
            # Commit transaction if using one
            if session:
                await session.commit_transaction()
            
            logger.info(
                f"Successfully processed match {result['match_id']}: "
                f"{result['home_ext']} {home_goals}-{away_goals} {result['away_ext']}, "
                f"Home owners: {len(home_owners)}, Away owners: {len(away_owners)}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete processing for {result['match_id']}: {e}")
            if session:
                await session.abort_transaction()
            return False
    
    @staticmethod
    async def _get_club_owners(league_id: str, club_ext: str, session=None) -> List[str]:
        """
        Get all owners of a club by external reference
        Returns list of user_ids
        """
        try:
            # Find club by external reference
            find_args = {"ext_ref": club_ext}
            if session:
                club = await db.clubs.find_one(find_args, session=session)
            else:
                club = await db.clubs.find_one(find_args)
                
            if not club:
                logger.warning(f"Club not found for ext_ref: {club_ext}")
                return []
            
            # Find all owners of this club in the league
            roster_find_args = {
                "league_id": league_id,
                "club_id": club["_id"]
            }
            
            if session:
                roster_clubs = await db.roster_clubs.find(roster_find_args, session=session).to_list(length=None)
            else:
                roster_clubs = await db.roster_clubs.find(roster_find_args).to_list(length=None)
            
            return [rc["user_id"] for rc in roster_clubs]
            
        except Exception as e:
            logger.error(f"Failed to get club owners for {club_ext}: {e}")
            return []
    
    @staticmethod
    async def _upsert_weekly_points(
        league_id: str,
        user_id: str,
        match_id: str,
        points_delta: int,
        bucket: Dict,
        session=None
    ) -> bool:
        """
        Upsert weekly points record (idempotent by leagueId, userId, matchId)
        """
        try:
            weekly_points = WeeklyPoints(
                league_id=league_id,
                user_id=user_id,
                bucket=WeeklyPointsBucket(**bucket),
                points_delta=points_delta,
                match_id=match_id
            )
            
            points_dict = weekly_points.dict(by_alias=True)
            
            # Upsert by unique key (league_id, user_id, match_id)
            update_args = {
                "$set": points_dict
            }
            upsert_args = {"upsert": True}
            
            if session:
                upsert_args["session"] = session
            
            await db.weekly_points.update_one(
                {
                    "league_id": league_id,
                    "user_id": user_id,
                    "match_id": match_id
                },
                update_args,
                **upsert_args
            )
            
            logger.debug(f"Upserted weekly points: {user_id} +{points_delta} for match {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert weekly points: {e}")
            return False
    
    @staticmethod
    async def get_league_standings(league_id: str) -> List[Dict]:
        """
        Get current league standings with total points
        """
        try:
            pipeline = [
                {"$match": {"league_id": league_id}},
                {"$group": {
                    "_id": "$user_id",
                    "total_points": {"$sum": "$points_delta"},
                    "matches_played": {"$sum": 1}
                }},
                {"$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user"
                }},
                {"$unwind": "$user"},
                {"$lookup": {
                    "from": "rosters",
                    "let": {"user_id": "$_id", "league_id": league_id},
                    "pipeline": [
                        {"$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$user_id", "$$user_id"]},
                                    {"$eq": ["$league_id", "$$league_id"]}
                                ]
                            }
                        }}
                    ],
                    "as": "roster"
                }},
                {"$unwind": "$roster"},
                {"$project": {
                    "user_id": "$_id",
                    "display_name": "$user.display_name",
                    "email": "$user.email",
                    "total_points": 1,
                    "matches_played": 1,
                    "budget_remaining": "$roster.budget_remaining",
                    "clubs_owned": {"$subtract": ["$roster.club_slots", {"$divide": ["$roster.budget_remaining", 10]}]}  # Approximation
                }},
                {"$sort": {"total_points": -1}}
            ]
            
            standings = await db.weekly_points.aggregate(pipeline).to_list(length=None)
            return standings
            
        except Exception as e:
            logger.error(f"Failed to get league standings: {e}")
            return []
    
    @staticmethod
    async def get_user_match_history(league_id: str, user_id: str) -> List[Dict]:
        """
        Get match history and points for a specific user
        """
        try:
            pipeline = [
                {"$match": {"league_id": league_id, "user_id": user_id}},
                {"$lookup": {
                    "from": "result_ingest",
                    "localField": "match_id",
                    "foreignField": "match_id",
                    "as": "match"
                }},
                {"$unwind": "$match"},
                {"$project": {
                    "match_id": 1,
                    "points_delta": 1,
                    "bucket": 1,
                    "created_at": 1,
                    "home_ext": "$match.home_ext",
                    "away_ext": "$match.away_ext",
                    "home_goals": "$match.home_goals",
                    "away_goals": "$match.away_goals",
                    "kicked_off_at": "$match.kicked_off_at"
                }},
                {"$sort": {"kicked_off_at": -1}}
            ]
            
            history = await db.weekly_points.aggregate(pipeline).to_list(length=None)
            return history
            
        except Exception as e:
            logger.error(f"Failed to get user match history: {e}")
            return []

class ScoringWorker:
    """
    Background worker for processing match results
    Can be run as cron job or continuous queue processor
    """
    
    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self.running = False
    
    async def start_continuous_processing(self):
        """Start continuous processing of results"""
        self.running = True
        logger.info("Starting continuous scoring worker")
        
        while self.running:
            try:
                result = await ScoringService.process_pending_results()
                if result["processed_count"] > 0:
                    logger.info(f"Processed {result['processed_count']} results")
                
                await asyncio.sleep(self.interval_seconds)
                
            except Exception as e:
                logger.error(f"Scoring worker error: {e}")
                await asyncio.sleep(self.interval_seconds)
    
    def stop(self):
        """Stop continuous processing"""
        self.running = False
        logger.info("Stopping scoring worker")
    
    @staticmethod
    async def run_once():
        """Process all pending results once (for cron jobs)"""
        logger.info("Running scoring worker once")
        result = await ScoringService.process_pending_results()
        logger.info(f"Scoring worker completed: {result}")
        return result

# Global scoring worker instance
scoring_worker: Optional[ScoringWorker] = None

def get_scoring_worker() -> ScoringWorker:
    """Get global scoring worker instance"""
    global scoring_worker
    if scoring_worker is None:
        scoring_worker = ScoringWorker()
    return scoring_worker