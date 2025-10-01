"""
Race-safe and Replay-safe Bidding Service
Implements atomic bidding with MongoDB transactions and operation ID deduplication
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClientSession
from pymongo.errors import DuplicateKeyError

from database import db
from time_provider import now

logger = logging.getLogger(__name__)

class BidService:
    """Race-safe and replay-safe bidding service using MongoDB transactions"""
    
    @staticmethod
    async def place_bid(league_id: str, user_id: str, amount: int, op_id: str) -> Dict:
        """
        Place bid with race-safety and replay-safety using MongoDB transactions
        
        Args:
            league_id: League/auction ID
            user_id: User placing the bid
            amount: Bid amount
            op_id: Unique operation ID for replay safety
            
        Returns:
            Dict with success status and details
        """
        async with await db.client.start_session() as session:
            try:
                async with session.start_transaction():
                    return await BidService._place_bid_transaction(
                        league_id, user_id, amount, op_id, session
                    )
                    
            except DuplicateKeyError as e:
                # Duplicate opId - this is a replay, return success without action
                if "unique_league_opid" in str(e):
                    logger.info(f"Bid replay detected - opId {op_id} already processed for league {league_id}")
                    return {"success": True, "message": "Bid already processed", "replay": True}
                else:
                    logger.error(f"Unexpected duplicate key error: {e}")
                    return {"success": False, "error": "Database constraint violation"}
                    
            except Exception as e:
                logger.error(f"Bid transaction failed: {e}")
                return {"success": False, "error": str(e)}

    @staticmethod
    async def _place_bid_transaction(
        league_id: str, 
        user_id: str, 
        amount: int, 
        op_id: str,
        session: AsyncIOMotorClientSession
    ) -> Dict:
        """
        Execute bid placement within a MongoDB transaction
        All validations and updates are atomic
        """
        timestamp = now()
        
        # 1. Get current auction/league state
        league = await db.leagues.find_one({"_id": league_id}, session=session)
        if not league:
            raise ValueError(f"League {league_id} not found")
            
        # 2. Find current open lot
        current_lot = await db.lots.find_one({
            "league_id": league_id,
            "status": {"$in": ["open", "going_once", "going_twice"]}
        }, session=session)
        
        if not current_lot:
            raise ValueError("No open lot available for bidding")
            
        lot_id = current_lot["_id"]
        current_bid = current_lot.get("current_bid", 0)
        
        # 3. Validate lot is open and club not sold
        if current_lot["status"] not in ["open", "going_once", "going_twice"]:
            raise ValueError(f"Lot is {current_lot['status']}, not accepting bids")
            
        # Check if club already sold
        if current_lot.get("final_price") is not None:
            raise ValueError("Club already sold")
            
        # 4. Validate amount > current bid
        if amount <= current_bid:
            raise ValueError(f"Bid {amount} must be higher than current bid {current_bid}")
            
        # 5. Validate user budget ≥ amount
        user_roster = await db.rosters.find_one({
            "league_id": league_id,
            "user_id": user_id
        }, session=session)
        
        if not user_roster:
            raise ValueError("User not found in league")
            
        if user_roster["budget_remaining"] < amount:
            raise ValueError(f"Insufficient budget: {user_roster['budget_remaining']} < {amount}")
            
        # 6. Create log entry with unique opId (this will fail if opId already exists)
        log_entry = {
            "_id": str(uuid.uuid4()),
            "league_id": league_id,
            "op_id": op_id,
            "operation_type": "bid",
            "user_id": user_id,
            "lot_id": lot_id,
            "amount": amount,
            "timestamp": timestamp,
            "previous_bid": current_bid,
            "previous_bidder": current_lot.get("top_bidder_id")
        }
        
        await db.auction_logs.insert_one(log_entry, session=session)
        
        # 7. Upsert highest bid and highest bidder atomically
        lot_update_result = await db.lots.update_one(
            {
                "_id": lot_id,
                "current_bid": current_bid,  # Ensure bid hasn't changed
                "status": {"$in": ["open", "going_once", "going_twice"]}
            },
            {
                "$set": {
                    "current_bid": amount,
                    "top_bidder_id": user_id,
                    "last_bid_at": timestamp
                }
            },
            session=session
        )
        
        if lot_update_result.modified_count == 0:
            # Lot state changed during transaction - race condition detected
            raise ValueError("Lot state changed during bid placement - please retry")
            
        # 8. Update user's budget
        await db.rosters.update_one(
            {"league_id": league_id, "user_id": user_id},
            {"$inc": {"budget_remaining": -amount + current_bid}},  # Adjust for previous bid if same user
            session=session
        )
        
        # 9. Mark previous bid as outbid if different user
        if current_lot.get("top_bidder_id") and current_lot.get("top_bidder_id") != user_id:
            # Restore budget to previous bidder
            await db.rosters.update_one(
                {"league_id": league_id, "user_id": current_lot["top_bidder_id"]},
                {"$inc": {"budget_remaining": current_bid}},
                session=session
            )
            
        # Create bid record
        bid_record = {
            "_id": str(uuid.uuid4()),
            "lot_id": lot_id,
            "league_id": league_id,
            "bidder_id": user_id,
            "amount": amount,
            "timestamp": timestamp,
            "status": "winning",
            "op_id": op_id
        }
        
        await db.bids.insert_one(bid_record, session=session)
        
        # Mark previous bids as outbid
        await db.bids.update_many(
            {
                "lot_id": lot_id,
                "_id": {"$ne": bid_record["_id"]},
                "status": "winning"
            },
            {"$set": {"status": "outbid"}},
            session=session
        )
        
        logger.info(f"Bid successfully placed: user={user_id}, amount={amount}, lot={lot_id}, opId={op_id}")
        
        return {
            "success": True,
            "lot_id": lot_id,
            "amount": amount,
            "bidder_id": user_id,
            "current_bid": amount,
            "leading_bidder_id": user_id,
            "bid_id": bid_record["_id"],
            "op_id": op_id,
            "timestamp": timestamp.isoformat()
        }

    @staticmethod
    async def get_bid_history(league_id: str, limit: int = 100) -> list:
        """Get bid history for a league"""
        try:
            cursor = db.auction_logs.find(
                {"league_id": league_id, "operation_type": "bid"},
                sort=[("timestamp", -1)],
                limit=limit
            )
            
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Failed to get bid history: {e}")
            return []

    @staticmethod
    async def verify_operation_integrity(league_id: str) -> Dict:
        """Verify no duplicate operations exist"""
        try:
            # Check for duplicate opIds
            pipeline = [
                {"$match": {"league_id": league_id}},
                {"$group": {"_id": "$op_id", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await db.auction_logs.aggregate(pipeline).to_list(length=None)
            
            return {
                "success": len(duplicates) == 0,
                "duplicate_count": len(duplicates),
                "duplicates": duplicates
            }
            
        except Exception as e:
            logger.error(f"Failed to verify operation integrity: {e}")
            return {"success": False, "error": str(e)}