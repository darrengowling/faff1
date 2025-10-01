import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorClientSession
from pymongo.errors import DuplicateKeyError

from models import *
from database import db
from time_provider import now, now_ms, is_test_mode
import socketio

# Auction timing configuration from environment
DEFAULT_BID_TIMER = 8 if is_test_mode() else 60
DEFAULT_ANTI_SNIPE = 3 if is_test_mode() else 30
BID_TIMER_SECONDS = int(os.getenv("BID_TIMER_SECONDS", str(DEFAULT_BID_TIMER)))
ANTI_SNIPE_SECONDS = int(os.getenv("ANTI_SNIPE_SECONDS", str(DEFAULT_ANTI_SNIPE)))

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
        self.time_sync_tasks: Dict[str, asyncio.Task] = {}  # auction_id -> sync_task
        
    async def start_time_sync(self, auction_id: str):
        """Start periodic time synchronization for an auction"""
        if auction_id in self.time_sync_tasks:
            return  # Already running
        
        self.time_sync_tasks[auction_id] = asyncio.create_task(
            self._time_sync_loop(auction_id)
        )
        logger.info(f"Started time sync for auction {auction_id}")
    
    async def stop_time_sync(self, auction_id: str):
        """Stop time synchronization for an auction"""
        if auction_id in self.time_sync_tasks:
            self.time_sync_tasks[auction_id].cancel()
            del self.time_sync_tasks[auction_id]
            logger.info(f"Stopped time sync for auction {auction_id}")
    
    async def _time_sync_loop(self, auction_id: str):
        """Send server time every 2 seconds for client synchronization"""
        try:
            while auction_id in self.active_auctions:
                server_now = now()  # Use time provider
                
                # Get current lot timer info if exists
                current_lot = None
                auction = await db.auctions.find_one({"_id": auction_id})
                if auction and auction.get("current_lot_id"):
                    lot = await db.lots.find_one({"_id": auction["current_lot_id"]})
                    if lot and lot.get("timer_ends_at"):
                        current_lot = {
                            "lot_id": lot["_id"],
                            "timer_ends_at": lot["timer_ends_at"].isoformat(),
                            "status": lot["status"]
                        }
                
                # Broadcast time sync
                await self.sio.emit('time_sync', {
                    'server_now': server_now.isoformat(),
                    'current_lot': current_lot
                }, room=f"auction_{auction_id}")
                
                await asyncio.sleep(2)  # Send every 2 seconds
                
        except asyncio.CancelledError:
            logger.info(f"Time sync cancelled for auction {auction_id}")
        except Exception as e:
            logger.error(f"Time sync error for auction {auction_id}: {e}")
        
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
            
            # GUARDRAIL: Enforce minimum league size
            from admin_service import AdminService
            size_valid, size_error = await AdminService.validate_league_size_constraints(
                auction["league_id"], "start_auction"
            )
            if not size_valid:
                raise ValueError(size_error)
            
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
                    "bid_timer_seconds": auction.get("bid_timer_seconds", BID_TIMER_SECONDS),
                    "anti_snipe_seconds": auction.get("anti_snipe_seconds", ANTI_SNIPE_SECONDS),
                    "budget_per_manager": auction["budget_per_manager"]
                }
            }
            
            # Start time synchronization
            await self.start_time_sync(auction_id)
            
            # Start first lot
            await self._start_next_lot(auction_id)
            
            logger.info(f"Started auction {auction_id} for league {auction['league_id']}")
            return True
            
        except ValueError as e:
            # Re-raise business logic errors for proper HTTP status codes
            logger.error(f"Failed to start auction {auction_id}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to start auction {auction_id}: {e}")
            raise Exception(f"Auction start failed: {str(e)}")
    
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
            timer_ends_at = now() + timedelta(
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
            wait_time = (timer_ends_at - now()).total_seconds() - 6
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
                    
                    if lot["current_bid"] > 0 and lot["leading_bidder_id"]:
                        # SOLD - process transaction atomically with guardrails
                        try:
                            # Import AdminService here to avoid circular imports
                            from admin_service import AdminService
                            
                            # GUARDRAIL: Check no duplicate ownership
                            league_id = self.active_auctions[auction_id]["league_id"]
                            no_duplicate = await AdminService.validate_no_duplicate_ownership(
                                league_id, lot["club_id"]
                            )
                            
                            if not no_duplicate:
                                # Club already owned - mark as unsold
                                await db.lots.update_one(
                                    {"_id": lot_id},
                                    {"$set": {"status": "unsold"}},
                                    session=session
                                )
                                logger.warning(f"Lot {lot_id} - duplicate ownership prevented - marked unsold")
                                return
                            
                            # GUARDRAIL: Final budget check at lot close
                            budget_valid, budget_error = await AdminService.validate_budget_constraint(
                                lot["leading_bidder_id"], league_id, lot["current_bid"]
                            )
                            
                            if not budget_valid:
                                # Insufficient budget - mark as unsold
                                await db.lots.update_one(
                                    {"_id": lot_id},
                                    {"$set": {"status": "unsold"}},
                                    session=session
                                )
                                logger.warning(f"Lot {lot_id} - budget check failed: {budget_error} - marked unsold")
                                return
                            
                            # GUARDRAIL: Roster capacity check at lot close
                            capacity_valid, capacity_error = await AdminService.validate_roster_capacity(
                                lot["leading_bidder_id"], league_id
                            )
                            
                            if not capacity_valid:
                                # Roster full - mark as unsold
                                await db.lots.update_one(
                                    {"_id": lot_id},
                                    {"$set": {"status": "unsold"}},
                                    session=session
                                )
                                logger.warning(f"Lot {lot_id} - roster capacity check failed: {capacity_error} - marked unsold")
                                return
                            
                            # 1. Create roster club (with guardrails passed)
                            roster_club = RosterClub(
                                roster_id=f"roster_{lot['leading_bidder_id']}_{auction_id}",  # Will be resolved
                                league_id=league_id,
                                user_id=lot["leading_bidder_id"],
                                club_id=lot["club_id"],
                                price=lot["current_bid"]
                            )
                            roster_club_dict = roster_club.dict(by_alias=True)
                            await db.roster_clubs.insert_one(roster_club_dict, session=session)
                            
                            # 2. Deduct budget from winner's roster
                            await db.rosters.update_one(
                                {
                                    "league_id": league_id,
                                    "user_id": lot["leading_bidder_id"]
                                },
                                {"$inc": {"budget_remaining": -lot["current_bid"]}},
                                session=session
                            )
                            
                            # 3. Mark lot as sold with winner info
                            await db.lots.update_one(
                                {"_id": lot_id},
                                {"$set": {
                                    "status": "sold",
                                    "winner_id": lot["leading_bidder_id"],
                                    "final_price": lot["current_bid"]
                                }},
                                session=session
                            )
                            
                            logger.info(f"Lot {lot_id} SOLD to {lot['leading_bidder_id']} for {lot['current_bid']}")
                            
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
        Place bid with comprehensive validation guardrails and atomic operations
        Returns bid result with success/failure status
        """
        # Import AdminService here to avoid circular imports
        from admin_service import AdminService
        
        try:
            # Get auction data
            auction_data = self.active_auctions.get(auction_id)
            if not auction_data:
                return {"success": False, "error": "Auction not active"}
            
            league_id = auction_data["league_id"]
            
            # GUARDRAIL 1: Validate budget constraints
            budget_valid, budget_error = await AdminService.validate_budget_constraint(
                bidder_id, league_id, amount
            )
            if not budget_valid:
                return {"success": False, "error": budget_error}
            
            # GUARDRAIL 2: Validate roster capacity constraints  
            capacity_valid, capacity_error = await AdminService.validate_roster_capacity(
                bidder_id, league_id
            )
            if not capacity_valid:
                return {"success": False, "error": capacity_error}
            
            # GUARDRAIL 3: Use atomic simultaneous bid handling
            success, message, bid_id = await AdminService.handle_simultaneous_bids(
                lot_id, bidder_id, amount
            )
            
            if not success:
                return {"success": False, "error": message}
            
            # Get updated lot state
            lot = await db.lots.find_one({"_id": lot_id})
            if not lot:
                return {"success": False, "error": "Lot not found"}
            
            # Anti-snipe logic with server-authoritative timing (deterministic in test mode)
            current_time = now()  # Use time provider for deterministic testing
            if lot.get("timer_ends_at"):
                end_time = lot["timer_ends_at"]
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                elif isinstance(end_time, datetime) and end_time.tzinfo is None:
                    # Handle timezone-naive datetime from database
                    end_time = end_time.replace(tzinfo=timezone.utc)
                
                seconds_remaining = (end_time - current_time).total_seconds()
                # Use auction-specific anti-snipe seconds from settings
                anti_snipe_threshold = auction_data["settings"]["anti_snipe_seconds"]
                
                if seconds_remaining < anti_snipe_threshold:
                    # GUARDRAIL 3: Server-authoritative timer extension (deterministic)
                    # Extend to now + (threshold * 2) for deterministic behavior
                    extension_seconds = anti_snipe_threshold * 2
                    new_end_time = current_time + timedelta(seconds=extension_seconds)
                    
                    # Log the extension event for deterministic testing
                    logger.info(f"🕐 ANTI-SNIPE EXTEND: lot_id={lot_id}, threshold={anti_snipe_threshold}s, "
                               f"remaining={seconds_remaining:.1f}s, extended_by={extension_seconds}s, "
                               f"new_end={new_end_time.isoformat()}")
                    timer_valid, timer_error = await AdminService.validate_timer_monotonicity(
                        auction_id, new_end_time
                    )
                    
                    if timer_valid:
                        # Atomically update timer - only server can do this
                        await db.lots.update_one(
                            {"_id": lot_id},
                            {"$set": {"timer_ends_at": new_end_time}}
                        )
                        
                        # Cancel and restart timer
                        if lot_id in self.auction_timers:
                            self.auction_timers[lot_id].cancel()
                            self.auction_timers[lot_id] = asyncio.create_task(
                                self._lot_timer(auction_id, lot_id, new_end_time)
                            )
                        
                        logger.info(f"Server-authoritative anti-snipe: Timer extended for lot {lot_id} to {new_end_time}")
                    else:
                        logger.warning(f"Timer extension failed: {timer_error}")
            
            # Broadcast real-time update with latest server state
            await self._broadcast_lot_update(auction_id, lot_id)
            
            logger.info(f"Bid placed: {bidder_id} bid {amount} on lot {lot_id}")
            
            return {
                "success": True,
                "lot_id": lot_id,
                "amount": amount,
                "bidder_id": bidder_id,
                "current_bid": lot["current_bid"],
                "leading_bidder_id": lot["leading_bidder_id"],
                "bid_id": bid_id
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