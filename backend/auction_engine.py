import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorClientSession
from pymongo.errors import DuplicateKeyError

from models import *
from database import db
import socketio

logger = logging.getLogger(__name__)

class AuctionState:
    """Auction state management"""
    WAITING = "waiting"
    OPEN = "open" 
    GOING_ONCE = "going_once"
    GOING_TWICE = "going_twice"
    SOLD = "sold"
    UNSOLD = "unsold"

class AuctionEngine:
    """
    Live auction engine with MongoDB atomicity and real-time updates
    Handles open ascending auctions for UCL clubs only
    """
    
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self.active_auctions: Dict[str, Dict] = {}  # auction_id -> auction_data
        self.auction_timers: Dict[str, asyncio.Task] = {}  # lot_id -> timer_task
        
    async def start_auction(self, auction_id: str, commissioner_id: str) -> bool:
        """Start an auction if league is ready"""
        try:
            # Verify commissioner permissions
            auction = await db.auctions.find_one({"_id": auction_id})
            if not auction:
                raise ValueError("Auction not found")
            
            league = await db.leagues.find_one({"_id": auction["league_id"]})
            if not league or league["commissioner_id"] != commissioner_id:
                raise ValueError("Only commissioner can start auction")
            
            if league["status"] != "ready":
                raise ValueError("League not ready for auction")
            
            # Update league and auction status
            await db.leagues.update_one(
                {"_id": auction["league_id"]},
                {"$set": {"status": "active"}}
            )
            
            await db.auctions.update_one(
                {"_id": auction_id},
                {"$set": {"status": AuctionStatus.LIVE}}
            )
            
            # Create lots for all clubs in round-robin nomination order
            await self._create_auction_lots(auction_id, auction["league_id"], auction["nomination_order"])
            
            # Store active auction data
            self.active_auctions[auction_id] = {
                "auction_id": auction_id,
                "league_id": auction["league_id"],
                "current_lot_index": 0,
                "nomination_order": auction["nomination_order"],
                "settings": {
                    "min_increment": auction["min_increment"],
                    "bid_timer_seconds": auction["bid_timer_seconds"],
                    "anti_snipe_seconds": 3,
                    "budget_per_manager": auction["budget_per_manager"]
                }
            }
            
            # Start first lot
            await self._start_next_lot(auction_id)
            
            logger.info(f"Started auction {auction_id} for league {auction['league_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start auction {auction_id}: {e}")
            return False
    
    async def _create_auction_lots(self, auction_id: str, league_id: str, nomination_order: List[str]):
        """Create lots for all clubs in nomination order"""
        try:
            # Get all clubs
            clubs = await db.clubs.find().to_list(length=None)
            
            # Create lots in round-robin order by nomination
            lots = []
            nominator_index = 0
            
            for i, club in enumerate(clubs):
                nominator_id = nomination_order[nominator_index % len(nomination_order)]
                
                lot = Lot(
                    auction_id=auction_id,
                    club_id=club["_id"],
                    nominated_by=nominator_id,
                    order_index=i,
                    status=LotStatus.PENDING
                )
                lots.append(lot.dict(by_alias=True))
                nominator_index += 1
            
            # Insert all lots
            if lots:
                await db.lots.insert_many(lots)
                logger.info(f"Created {len(lots)} lots for auction {auction_id}")
                
        except Exception as e:
            logger.error(f"Failed to create auction lots: {e}")
            raise
    
    async def _start_next_lot(self, auction_id: str):
        """Start the next lot in the auction"""
        try:
            auction_data = self.active_auctions.get(auction_id)
            if not auction_data:
                return
            
            # Get next pending lot
            lot = await db.lots.find_one({
                "auction_id": auction_id,
                "status": "pending"
            }, sort=[("order_index", 1)])
            
            if not lot:
                # No more lots - end auction
                await self._end_auction(auction_id)
                return
            
            # Set lot as open with timer
            timer_ends_at = datetime.now(timezone.utc) + timedelta(
                seconds=auction_data["settings"]["bid_timer_seconds"]
            )
            
            await db.lots.update_one(
                {"_id": lot["_id"]},
                {
                    "$set": {
                        "status": "open",
                        "timer_ends_at": timer_ends_at,
                        "current_bid": 0
                    }
                }
            )
            
            # Start timer task
            self.auction_timers[lot["_id"]] = asyncio.create_task(
                self._lot_timer(auction_id, lot["_id"], timer_ends_at)
            )
            
            # Broadcast lot start
            await self._broadcast_lot_update(auction_id, lot["_id"])
            
            logger.info(f"Started lot {lot['_id']} for club {lot['club_id']}")
            
        except Exception as e:
            logger.error(f"Failed to start next lot: {e}")
    
    async def _lot_timer(self, auction_id: str, lot_id: str, timer_ends_at: datetime):
        """Timer for individual lot with going once/twice states"""
        try:
            # Wait until 6 seconds before end
            wait_time = (timer_ends_at - datetime.now(timezone.utc)).total_seconds() - 6
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # Check if lot is still open (might have been extended)
            lot = await db.lots.find_one({"_id": lot_id})
            if not lot or lot["status"] != "open":
                return
            
            # Going once (3 seconds)
            await db.lots.update_one(
                {"_id": lot_id},
                {"$set": {"status": "going_once"}}
            )
            await self._broadcast_lot_update(auction_id, lot_id)
            await asyncio.sleep(3)
            
            # Check again
            lot = await db.lots.find_one({"_id": lot_id})
            if not lot or lot["status"] != "going_once":
                return
            
            # Going twice (3 seconds)
            await db.lots.update_one(
                {"_id": lot_id},
                {"$set": {"status": "going_twice"}}
            )
            await self._broadcast_lot_update(auction_id, lot_id)
            await asyncio.sleep(3)
            
            # Final check and close lot
            await self._close_lot(auction_id, lot_id)
            
        except asyncio.CancelledError:
            logger.info(f"Timer cancelled for lot {lot_id}")
        except Exception as e:
            logger.error(f"Timer error for lot {lot_id}: {e}")
    
    async def _close_lot(self, auction_id: str, lot_id: str):
        """Close lot and process sale atomically"""
        async with await db.client.start_session() as session:
            try:
                async with session.start_transaction():
                    # Get final lot state
                    lot = await db.lots.find_one({"_id": lot_id}, session=session)
                    if not lot:
                        return
                    
                    if lot["current_bid"] > 0 and lot["top_bidder_id"]:
                        # SOLD - process transaction atomically
                        try:
                            # 1. Create roster club (fails if already owned)
                            roster_club = RosterClub(
                                roster_id=f"roster_{lot['top_bidder_id']}_{auction_id}",  # Will be resolved
                                league_id=self.active_auctions[auction_id]["league_id"],
                                user_id=lot["top_bidder_id"],
                                club_id=lot["club_id"],
                                price=lot["current_bid"]
                            )
                            roster_club_dict = roster_club.dict(by_alias=True)
                            await db.roster_clubs.insert_one(roster_club_dict, session=session)
                            
                            # 2. Deduct budget from winner's roster
                            await db.rosters.update_one(
                                {
                                    "league_id": self.active_auctions[auction_id]["league_id"],
                                    "user_id": lot["top_bidder_id"]
                                },
                                {"$inc": {"budget_remaining": -lot["current_bid"]}},
                                session=session
                            )
                            
                            # 3. Mark lot as sold
                            await db.lots.update_one(
                                {"_id": lot_id},
                                {"$set": {"status": "sold"}},
                                session=session
                            )
                            
                            logger.info(f"Lot {lot_id} SOLD to {lot['top_bidder_id']} for {lot['current_bid']}")
                            
                        except DuplicateKeyError:
                            # Club already owned - mark as unsold
                            await db.lots.update_one(
                                {"_id": lot_id},
                                {"$set": {"status": "unsold"}},
                                session=session
                            )
                            logger.warning(f"Lot {lot_id} club already owned - marked unsold")
                    
                    else:
                        # UNSOLD - no bids
                        await db.lots.update_one(
                            {"_id": lot_id},
                            {"$set": {"status": "unsold"}},
                            session=session
                        )
                        logger.info(f"Lot {lot_id} UNSOLD - no bids")
                
                # Broadcast final lot state
                await self._broadcast_lot_update(auction_id, lot_id)
                
                # Start next lot after delay
                await asyncio.sleep(2)
                await self._start_next_lot(auction_id)
                
            except Exception as e:
                logger.error(f"Failed to close lot {lot_id}: {e}")
                await session.abort_transaction()
    
    async def place_bid(self, auction_id: str, lot_id: str, bidder_id: str, amount: int) -> Dict:
        """
        Place bid with atomic validation and anti-snipe logic
        Returns bid result with success/failure status
        """
        async with await db.client.start_session() as session:
            try:
                async with session.start_transaction():
                    # Get auction data
                    auction_data = self.active_auctions.get(auction_id)
                    if not auction_data:
                        return {"success": False, "error": "Auction not active"}
                    
                    # Get bidder's current budget
                    roster = await db.rosters.find_one({
                        "league_id": auction_data["league_id"],
                        "user_id": bidder_id
                    }, session=session)
                    
                    if not roster:
                        return {"success": False, "error": "Roster not found"}
                    
                    # Check if bidder can fill remaining slots at min price
                    current_clubs = await db.roster_clubs.count_documents({
                        "league_id": auction_data["league_id"],
                        "user_id": bidder_id
                    }, session=session)
                    
                    remaining_slots = roster["club_slots"] - current_clubs
                    min_budget_needed = remaining_slots * auction_data["settings"]["min_increment"]
                    
                    if roster["budget_remaining"] - amount < min_budget_needed:
                        return {"success": False, "error": "Insufficient budget for remaining slots"}
                    
                    # Atomic bid placement with guards
                    now = datetime.now(timezone.utc)
                    update_data = {
                        "current_bid": amount,
                        "top_bidder_id": bidder_id
                    }
                    
                    # Anti-snipe logic: extend timer if < 3 seconds remain
                    lot = await db.lots.find_one({"_id": lot_id}, session=session)
                    if lot and lot.get("timer_ends_at"):
                        seconds_remaining = (lot["timer_ends_at"] - now).total_seconds()
                        if seconds_remaining < 3:
                            update_data["timer_ends_at"] = now + timedelta(seconds=6)
                            # Cancel and restart timer
                            if lot_id in self.auction_timers:
                                self.auction_timers[lot_id].cancel()
                                self.auction_timers[lot_id] = asyncio.create_task(
                                    self._lot_timer(auction_id, lot_id, update_data["timer_ends_at"])
                                )
                    
                    # Atomic update with conditions
                    result = await db.lots.find_one_and_update(
                        {
                            "_id": lot_id,
                            "status": "open",
                            "current_bid": {"$lt": amount},
                            "$expr": {
                                "$gte": [amount, {"$add": ["$current_bid", auction_data["settings"]["min_increment"]]}]
                            }
                        },
                        {"$set": update_data},
                        session=session,
                        return_document=True
                    )
                    
                    if not result:
                        return {"success": False, "error": "Bid conditions not met"}
                    
                    # Record bid in bids collection
                    bid = Bid(
                        lot_id=lot_id,
                        bidder_id=bidder_id,
                        amount=amount
                    )
                    bid_dict = bid.dict(by_alias=True)
                    await db.bids.insert_one(bid_dict, session=session)
                    
                    # Broadcast real-time update
                    await self._broadcast_lot_update(auction_id, lot_id)
                    
                    logger.info(f"Bid placed: {bidder_id} bid {amount} on lot {lot_id}")
                    
                    return {
                        "success": True,
                        "lot_id": lot_id,
                        "amount": amount,
                        "bidder_id": bidder_id,
                        "current_bid": result["current_bid"],
                        "top_bidder_id": result["top_bidder_id"]
                    }
                    
            except Exception as e:
                logger.error(f"Bid placement failed: {e}")
                return {"success": False, "error": str(e)}
    
    async def nominate_club(self, auction_id: str, nominator_id: str, club_id: str) -> bool:
        """Nominate next club (if it's nominator's turn)"""
        try:
            auction_data = self.active_auctions.get(auction_id)
            if not auction_data:
                return False
            
            # Check if it's nominator's turn (simplified for now)
            # In full implementation, would check current nomination order
            
            # This would trigger the nomination of a specific club
            # For now, lots are pre-created in round-robin order
            
            return True
            
        except Exception as e:
            logger.error(f"Nomination failed: {e}")
            return False
    
    async def pause_auction(self, auction_id: str, commissioner_id: str) -> bool:
        """Pause auction (commissioner only)"""
        try:
            auction = await db.auctions.find_one({"_id": auction_id})
            if not auction:
                return False
            
            league = await db.leagues.find_one({"_id": auction["league_id"]})
            if not league or league["commissioner_id"] != commissioner_id:
                return False
            
            # Pause auction
            await db.auctions.update_one(
                {"_id": auction_id},
                {"$set": {"status": "paused"}}
            )
            
            # Cancel all timers
            for lot_id, timer_task in self.auction_timers.items():
                timer_task.cancel()
            
            # Broadcast pause
            await self.sio.emit('auction_paused', {
                "auction_id": auction_id,
                "message": "Auction paused by commissioner"
            }, room=f"auction_{auction_id}")
            
            logger.info(f"Auction {auction_id} paused by commissioner {commissioner_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause auction: {e}")
            return False
    
    async def resume_auction(self, auction_id: str, commissioner_id: str) -> bool:
        """Resume paused auction (commissioner only)"""
        try:
            auction = await db.auctions.find_one({"_id": auction_id})
            if not auction:
                return False
            
            league = await db.leagues.find_one({"_id": auction["league_id"]})
            if not league or league["commissioner_id"] != commissioner_id:
                return False
            
            # Resume auction
            await db.auctions.update_one(
                {"_id": auction_id},
                {"$set": {"status": "live"}}
            )
            
            # Restart current lot timer if exists
            current_lot = await db.lots.find_one({
                "auction_id": auction_id,
                "status": "open"
            })
            
            if current_lot and current_lot.get("timer_ends_at"):
                self.auction_timers[current_lot["_id"]] = asyncio.create_task(
                    self._lot_timer(auction_id, current_lot["_id"], current_lot["timer_ends_at"])
                )
            
            # Broadcast resume
            await self.sio.emit('auction_resumed', {
                "auction_id": auction_id,
                "message": "Auction resumed by commissioner"
            }, room=f"auction_{auction_id}")
            
            logger.info(f"Auction {auction_id} resumed by commissioner {commissioner_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume auction: {e}")
            return False
    
    async def _end_auction(self, auction_id: str):
        """End auction and cleanup"""
        try:
            # Update auction status
            await db.auctions.update_one(
                {"_id": auction_id},
                {"$set": {"status": "completed"}}
            )
            
            # Update league status
            if auction_id in self.active_auctions:
                league_id = self.active_auctions[auction_id]["league_id"]
                await db.leagues.update_one(
                    {"_id": league_id},
                    {"$set": {"status": "completed"}}
                )
            
            # Cancel all timers
            auction_timers_to_cancel = [
                timer_task for lot_id, timer_task in self.auction_timers.items()
                if lot_id.startswith(auction_id)
            ]
            for timer_task in auction_timers_to_cancel:
                timer_task.cancel()
            
            # Clean up
            if auction_id in self.active_auctions:
                del self.active_auctions[auction_id]
            
            # Broadcast end
            await self.sio.emit('auction_ended', {
                "auction_id": auction_id,
                "message": "Auction completed"
            }, room=f"auction_{auction_id}")
            
            logger.info(f"Auction {auction_id} completed")
            
        except Exception as e:
            logger.error(f"Failed to end auction: {e}")
    
    async def _broadcast_lot_update(self, auction_id: str, lot_id: str):
        """Broadcast lot state to all connected clients"""
        try:
            # Get current lot with club details
            pipeline = [
                {"$match": {"_id": lot_id}},
                {"$lookup": {
                    "from": "clubs",
                    "localField": "club_id",
                    "foreignField": "_id",
                    "as": "club"
                }},
                {"$unwind": "$club"}
            ]
            
            lots = await db.lots.aggregate(pipeline).to_list(1)
            if not lots:
                return
            
            lot = lots[0]
            
            # Get top bidder details if exists
            top_bidder = None
            if lot.get("top_bidder_id"):
                bidder = await db.users.find_one({"_id": lot["top_bidder_id"]})
                if bidder:
                    top_bidder = {
                        "id": bidder["_id"],
                        "display_name": bidder["display_name"]
                    }
            
            # Broadcast update
            await self.sio.emit('lot_update', {
                "auction_id": auction_id,
                "lot": {
                    "id": lot["_id"],
                    "club": {
                        "id": lot["club"]["_id"],
                        "name": lot["club"]["name"],
                        "short_name": lot["club"]["short_name"],
                        "country": lot["club"]["country"]
                    },
                    "status": lot["status"],
                    "current_bid": lot["current_bid"],
                    "top_bidder": top_bidder,
                    "timer_ends_at": lot.get("timer_ends_at").isoformat() if lot.get("timer_ends_at") else None,
                    "order_index": lot["order_index"]
                }
            }, room=f"auction_{auction_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast lot update: {e}")
    
    async def get_auction_state(self, auction_id: str) -> Optional[Dict]:
        """Get current auction state for clients"""
        try:
            if auction_id not in self.active_auctions:
                return None
            
            # Get current lot
            current_lot = await db.lots.find_one({
                "auction_id": auction_id,
                "status": {"$in": ["open", "going_once", "going_twice"]}
            })
            
            # Get league members with budgets
            league_id = self.active_auctions[auction_id]["league_id"]
            pipeline = [
                {"$match": {"league_id": league_id}},
                {"$lookup": {
                    "from": "users",
                    "localField": "user_id", 
                    "foreignField": "_id",
                    "as": "user"
                }},
                {"$unwind": "$user"},
                {"$project": {
                    "user_id": 1,
                    "budget_remaining": 1,
                    "club_slots": 1,
                    "display_name": "$user.display_name"
                }}
            ]
            rosters = await db.rosters.aggregate(pipeline).to_list(length=None)
            
            return {
                "auction_id": auction_id,
                "league_id": league_id,
                "status": "live",
                "current_lot": current_lot,
                "managers": rosters,
                "settings": self.active_auctions[auction_id]["settings"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get auction state: {e}")
            return None

# Global auction engine instance
auction_engine: Optional[AuctionEngine] = None

def get_auction_engine() -> AuctionEngine:
    """Get global auction engine instance"""
    global auction_engine
    if auction_engine is None:
        raise RuntimeError("Auction engine not initialized")
    return auction_engine

def initialize_auction_engine(sio: socketio.AsyncServer):
    """Initialize global auction engine"""
    global auction_engine
    auction_engine = AuctionEngine(sio)
    return auction_engine