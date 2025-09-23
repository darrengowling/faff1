import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta

from models import *
from database import db
from audit_service import AuditService, log_league_settings_update, log_member_action, log_auction_action

logger = logging.getLogger(__name__)

class AdminValidationError(Exception):
    """Custom exception for admin validation failures"""
    pass

class AdminService:
    """
    Comprehensive admin service with validation guardrails and audit logging
    Handles all commissioner-only operations with proper checks and balances
    """
    
    @staticmethod
    async def validate_commissioner_access(user_id: str, league_id: str) -> bool:
        """
        Validate that user is a commissioner for the league
        
        Args:
            user_id: User to check
            league_id: League to check access for
            
        Returns:
            True if user is commissioner, False otherwise
        """
        try:
            membership = await db.memberships.find_one({
                "user_id": user_id,
                "league_id": league_id,
                "role": "commissioner"
            })
            return membership is not None
        except Exception as e:
            logger.error(f"Failed to validate commissioner access: {e}")
            return False

    @staticmethod
    async def validate_no_duplicate_ownership(league_id: str, club_id: str, exclude_user_id: Optional[str] = None) -> bool:
        """
        GUARDRAIL: Ensure no duplicate club ownership in league
        
        Args:
            league_id: League to check
            club_id: Club to check ownership for
            exclude_user_id: User to exclude from check (for transfers)
            
        Returns:
            True if no duplicate ownership, False if club already owned
        """
        try:
            query = {"league_id": league_id, "club_id": club_id}
            if exclude_user_id:
                query["user_id"] = {"$ne": exclude_user_id}
            
            existing_ownership = await db.roster_clubs.find_one(query)
            return existing_ownership is None
        except Exception as e:
            logger.error(f"Failed to validate club ownership: {e}")
            return False

    @staticmethod
    async def validate_budget_constraint(user_id: str, league_id: str, bid_amount: int) -> Tuple[bool, str]:
        """
        GUARDRAIL: Validate budget constraints before bidding
        
        Args:
            user_id: User placing bid
            league_id: League context
            bid_amount: Amount being bid
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get user's roster
            roster = await db.rosters.find_one({"user_id": user_id, "league_id": league_id})
            if not roster:
                return False, "User roster not found"
            
            # Check if user has sufficient budget
            if roster["budget_remaining"] < bid_amount:
                return False, f"Insufficient budget: {roster['budget_remaining']} < {bid_amount}"
            
            return True, ""
        except Exception as e:
            logger.error(f"Failed to validate budget constraint: {e}")
            return False, "Budget validation failed"

    @staticmethod
    async def validate_timer_monotonicity(auction_id: str, new_end_time: datetime) -> Tuple[bool, str]:
        """
        GUARDRAIL: Ensure timer can only be extended forward
        
        Args:
            auction_id: Auction to check
            new_end_time: Proposed new end time
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get current auction state
            auction = await db.auctions.find_one({"_id": auction_id})
            if not auction:
                return False, "Auction not found"
            
            # Check if there's a current lot
            current_lot = await db.lots.find_one({
                "auction_id": auction_id,
                "status": "active"
            })
            
            if current_lot and current_lot.get("timer_ends_at"):
                current_end = current_lot["timer_ends_at"]
                if isinstance(current_end, str):
                    current_end = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
                
                if new_end_time <= current_end:
                    return False, f"Timer can only be extended forward: {new_end_time} <= {current_end}"
            
            return True, ""
        except Exception as e:
            logger.error(f"Failed to validate timer monotonicity: {e}")
            return False, "Timer validation failed"

    @staticmethod
    async def handle_simultaneous_bids(lot_id: str, user_id: str, bid_amount: int) -> Tuple[bool, str, Optional[str]]:
        """
        GUARDRAIL: Handle simultaneous bids with atomic operations
        Ensures last-write wins without violating constraints
        
        Args:
            lot_id: Lot being bid on
            user_id: User placing bid
            bid_amount: Bid amount
            
        Returns:
            Tuple of (success, message, bid_id)
        """
        try:
            # Use atomic findOneAndUpdate to handle concurrent bids
            result = await db.lots.find_one_and_update(
                {
                    "_id": lot_id,
                    "status": "active",
                    "current_bid": {"$lt": bid_amount}  # Only update if our bid is higher
                },
                {
                    "$set": {
                        "current_bid": bid_amount,
                        "leading_bidder_id": user_id,
                        "updated_at": datetime.now(timezone.utc)
                    }
                },
                return_document=True
            )
            
            if not result:
                # Check why update failed
                lot = await db.lots.find_one({"_id": lot_id})
                if not lot:
                    return False, "Lot not found", None
                if lot["status"] != "active":
                    return False, "Lot is not active", None
                if lot["current_bid"] >= bid_amount:
                    return False, f"Bid too low: current bid is {lot['current_bid']}", None
                
                return False, "Bid update failed", None
            
            # Create bid record
            bid = Bid(
                auction_id=result["auction_id"],
                league_id=result["league_id"],
                lot_id=lot_id,
                user_id=user_id,
                amount=bid_amount,
                status="active"
            )
            
            bid_dict = bid.dict(by_alias=True)
            bid_result = await db.bids.insert_one(bid_dict)
            
            return True, "Bid placed successfully", bid_result.inserted_id
            
        except Exception as e:
            logger.error(f"Failed to handle simultaneous bids: {e}")
            return False, "Bid processing failed", None

    # Admin Actions

    @staticmethod
    async def update_league_settings(league_id: str, actor_id: str, updates: LeagueSettingsUpdate) -> Dict:
        """
        Update league settings with comprehensive validation and audit logging
        
        Args:
            league_id: League to update
            actor_id: Commissioner performing update
            updates: New settings
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Validate commissioner access
            if not await AdminService.validate_commissioner_access(actor_id, league_id):
                raise AdminValidationError("Commissioner access required")
            
            # Get current league settings
            league = await db.leagues.find_one({"_id": league_id})
            if not league:
                raise AdminValidationError("League not found")
            
            current_settings = league.get("settings", {})
            current_member_count = league.get("member_count", 0)
            
            # Get auction status for budget/slots validation
            auction = await db.auctions.find_one({"league_id": league_id})
            auction_status = auction.get("status", "scheduled") if auction else "scheduled"
            
            # VALIDATION GUARDS
            
            # 1. Budget changes validation
            if updates.budget_per_manager is not None:
                if auction_status not in ["scheduled", "paused"]:
                    raise AdminValidationError("Budget can only be changed when auction is scheduled or paused")
                
                # Check if any club purchases exist
                purchases_exist = await db.roster_clubs.count_documents({"league_id": league_id}) > 0
                if purchases_exist:
                    raise AdminValidationError("Budget cannot be changed after club purchases have been made")
            
            # 2. Club slots validation
            if updates.club_slots_per_manager is not None:
                current_slots = current_settings.get("club_slots_per_manager", 3)
                new_slots = updates.club_slots_per_manager
                
                # If decreasing slots, check all rosters can accommodate
                if new_slots < current_slots:
                    # Check if any manager has more clubs than new limit
                    rosters_with_too_many_clubs = await db.roster_clubs.aggregate([
                        {"$match": {"league_id": league_id}},
                        {"$group": {"_id": "$user_id", "club_count": {"$sum": 1}}},
                        {"$match": {"club_count": {"$gt": new_slots}}}
                    ]).to_list(length=None)
                    
                    if rosters_with_too_many_clubs:
                        manager_names = []
                        for roster in rosters_with_too_many_clubs:
                            user = await db.users.find_one({"_id": roster["_id"]})
                            manager_names.append(f"{user.get('display_name', 'Unknown')} ({roster['club_count']} clubs)")
                        
                        raise AdminValidationError(
                            f"Cannot reduce club slots to {new_slots}. These managers have too many clubs: {', '.join(manager_names)}"
                        )
            
            # 3. League size validation
            if updates.league_size is not None:
                new_min = updates.league_size.min
                new_max = updates.league_size.max
                
                # Check that new max is not less than current member count
                if new_max < current_member_count:
                    raise AdminValidationError(
                        f"Maximum managers ({new_max}) cannot be less than current member count ({current_member_count})"
                    )
            
            # Prepare updates
            update_dict = {}
            if updates.budget_per_manager is not None:
                update_dict["settings.budget_per_manager"] = updates.budget_per_manager
                # Update all existing rosters if no purchases made
                await db.rosters.update_many(
                    {"league_id": league_id},
                    {"$set": {
                        "budget_start": updates.budget_per_manager,
                        "budget_remaining": updates.budget_per_manager
                    }}
                )
            if updates.min_increment is not None:
                update_dict["settings.min_increment"] = updates.min_increment
            if updates.club_slots_per_manager is not None:
                update_dict["settings.club_slots_per_manager"] = updates.club_slots_per_manager
                # Update all existing rosters
                await db.rosters.update_many(
                    {"league_id": league_id},
                    {"$set": {"club_slots": updates.club_slots_per_manager}}
                )
            if updates.anti_snipe_seconds is not None:
                update_dict["settings.anti_snipe_seconds"] = updates.anti_snipe_seconds
            if updates.bid_timer_seconds is not None:
                update_dict["settings.bid_timer_seconds"] = updates.bid_timer_seconds
            if updates.league_size is not None:
                update_dict["settings.league_size"] = updates.league_size.model_dump()
            if updates.scoring_rules is not None:
                update_dict["settings.scoring_rules"] = updates.scoring_rules.model_dump()
            
            if not update_dict:
                return {"success": False, "message": "No updates provided"}
            
            # Store before state for audit
            before_state = current_settings.copy()
            
            # Update league
            await db.leagues.update_one(
                {"_id": league_id},
                {"$set": update_dict}
            )
            
            # Get after state
            updated_league = await db.leagues.find_one({"_id": league_id})
            after_state = updated_league.get("settings", {})
            
            # Log audit trail
            await log_league_settings_update(league_id, actor_id, before_state, after_state)
            
            return {"success": True, "message": "League settings updated successfully"}
            
        except AdminValidationError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Failed to update league settings: {e}")
            return {"success": False, "message": "Failed to update league settings"}

    @staticmethod
    async def manage_member(league_id: str, actor_id: str, member_action: MemberAction) -> Dict:
        """
        Approve or kick league members
        
        Args:
            league_id: League context
            actor_id: Commissioner performing action
            member_action: Action to perform
            
        Returns:
            Result dictionary
        """
        try:
            # Validate commissioner access
            if not await AdminService.validate_commissioner_access(actor_id, league_id):
                raise AdminValidationError("Commissioner access required")
            
            member_id = member_action.member_id
            action = member_action.action
            
            if action == "kick":
                # Remove member from league
                await db.memberships.delete_one({
                    "user_id": member_id,
                    "league_id": league_id
                })
                
                # Remove their roster
                await db.rosters.delete_one({
                    "user_id": member_id,
                    "league_id": league_id
                })
                
                # Remove their club ownership
                await db.roster_clubs.delete_many({
                    "user_id": member_id,
                    "league_id": league_id
                })
                
                # Update league member count
                await db.leagues.update_one(
                    {"_id": league_id},
                    {"$inc": {"member_count": -1}}
                )
                
                # Log action
                await log_member_action(league_id, actor_id, "kick_member", member_id)
                
                return {"success": True, "message": "Member kicked successfully"}
            
            elif action == "approve":
                # Update membership status (if you have pending memberships)
                result = await db.memberships.update_one(
                    {"user_id": member_id, "league_id": league_id},
                    {"$set": {"status": "active"}}
                )
                
                if result.modified_count > 0:
                    # Log action
                    await log_member_action(league_id, actor_id, "approve_member", member_id)
                    return {"success": True, "message": "Member approved successfully"}
                else:
                    return {"success": False, "message": "Member not found or already approved"}
            
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
                
        except AdminValidationError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Failed to manage member: {e}")
            return {"success": False, "message": "Failed to manage member"}

    @staticmethod
    async def manage_auction(league_id: str, actor_id: str, action: str, auction_id: str, params: Dict = None) -> Dict:
        """
        Start, pause, or resume auction with proper validation
        
        Args:
            league_id: League context
            actor_id: Commissioner performing action
            action: Action to perform (start, pause, resume)
            auction_id: Auction ID
            params: Additional parameters
            
        Returns:
            Result dictionary
        """
        try:
            # Validate commissioner access
            if not await AdminService.validate_commissioner_access(actor_id, league_id):
                raise AdminValidationError("Commissioner access required")
            
            auction = await db.auctions.find_one({"_id": auction_id})
            if not auction:
                raise AdminValidationError("Auction not found")
            
            current_status = auction.get("status", "setup")
            
            if action == "start":
                if current_status != "setup":
                    raise AdminValidationError(f"Cannot start auction in {current_status} status")
                
                # Update auction status
                await db.auctions.update_one(
                    {"_id": auction_id},
                    {"$set": {
                        "status": "active",
                        "started_at": datetime.now(timezone.utc)
                    }}
                )
                
                # Log action
                await log_auction_action(league_id, actor_id, "start_auction", auction_id)
                
                return {"success": True, "message": "Auction started successfully"}
            
            elif action == "pause":
                if current_status != "active":
                    raise AdminValidationError(f"Cannot pause auction in {current_status} status")
                
                # Pause current lot timer
                current_lot = await db.lots.find_one({
                    "auction_id": auction_id,
                    "status": "active"
                })
                
                pause_time = datetime.now(timezone.utc)
                
                if current_lot and current_lot.get("timer_ends_at"):
                    # Calculate remaining time
                    end_time = current_lot["timer_ends_at"]
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    
                    remaining_seconds = max(0, (end_time - pause_time).total_seconds())
                    
                    # Store remaining time in lot
                    await db.lots.update_one(
                        {"_id": current_lot["_id"]},
                        {"$set": {
                            "timer_paused_at": pause_time,
                            "timer_remaining_seconds": remaining_seconds
                        }}
                    )
                
                # Update auction status
                await db.auctions.update_one(
                    {"_id": auction_id},
                    {"$set": {
                        "status": "paused",
                        "paused_at": pause_time
                    }}
                )
                
                # Log action
                await log_auction_action(league_id, actor_id, "pause_auction", auction_id)
                
                return {"success": True, "message": "Auction paused successfully"}
            
            elif action == "resume":
                if current_status != "paused":
                    raise AdminValidationError(f"Cannot resume auction in {current_status} status")
                
                # Resume current lot timer with monotonicity check
                current_lot = await db.lots.find_one({
                    "auction_id": auction_id,
                    "status": "active"
                })
                
                resume_time = datetime.now(timezone.utc)
                
                if current_lot and current_lot.get("timer_remaining_seconds"):
                    # Recompute timer end time (GUARDRAIL: Timer monotonicity)
                    remaining_seconds = current_lot["timer_remaining_seconds"]
                    new_end_time = resume_time + timedelta(seconds=remaining_seconds)
                    
                    # Validate monotonicity
                    is_valid, error_msg = await AdminService.validate_timer_monotonicity(auction_id, new_end_time)
                    if not is_valid:
                        raise AdminValidationError(f"Timer monotonicity violation: {error_msg}")
                    
                    # Update lot timer
                    await db.lots.update_one(
                        {"_id": current_lot["_id"]},
                        {"$set": {
                            "timer_ends_at": new_end_time,
                            "timer_resumed_at": resume_time
                        },
                        "$unset": {
                            "timer_paused_at": 1,
                            "timer_remaining_seconds": 1
                        }}
                    )
                
                # Update auction status
                await db.auctions.update_one(
                    {"_id": auction_id},
                    {"$set": {
                        "status": "active",
                        "resumed_at": resume_time
                    },
                    "$unset": {"paused_at": 1}}
                )
                
                # Log action
                await log_auction_action(league_id, actor_id, "resume_auction", auction_id)
                
                return {"success": True, "message": "Auction resumed successfully"}
            
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
                
        except AdminValidationError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Failed to manage auction: {e}")
            return {"success": False, "message": "Failed to manage auction"}

    @staticmethod
    async def reorder_nominations(league_id: str, actor_id: str, reorder_request: NominationReorder) -> Dict:
        """
        Reorder nomination queue for auction
        
        Args:
            league_id: League context
            actor_id: Commissioner performing action
            reorder_request: New order for nominations
            
        Returns:
            Result dictionary
        """
        try:
            # Validate commissioner access
            if not await AdminService.validate_commissioner_access(actor_id, league_id):
                raise AdminValidationError("Commissioner access required")
            
            auction_id = reorder_request.auction_id
            new_order = reorder_request.new_order
            
            # Get current lots for validation
            lots = await db.lots.find({
                "auction_id": auction_id,
                "status": {"$in": ["pending", "active"]}
            }).to_list(length=None)
            
            lot_club_ids = [lot["club_id"] for lot in lots]
            
            # Validate that all clubs in new order exist in lots
            if set(new_order) != set(lot_club_ids):
                raise AdminValidationError("New order doesn't match existing lots")
            
            # Update lot order
            for i, club_id in enumerate(new_order):
                await db.lots.update_one(
                    {"auction_id": auction_id, "club_id": club_id},
                    {"$set": {"nomination_order": i}}
                )
            
            # Log action
            await log_auction_action(
                league_id, actor_id, "reorder_nominations", auction_id,
                {"new_order": new_order}
            )
            
            return {"success": True, "message": "Nominations reordered successfully"}
            
        except AdminValidationError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Failed to reorder nominations: {e}")
            return {"success": False, "message": "Failed to reorder nominations"}

    @staticmethod
    async def get_comprehensive_audit(league_id: str, actor_id: str, request: BidAuditRequest) -> Dict:
        """
        Get comprehensive audit information including bids and admin actions
        
        Args:
            league_id: League context
            actor_id: Commissioner requesting audit
            request: Audit request parameters
            
        Returns:
            Comprehensive audit data
        """
        try:
            # Validate commissioner access
            if not await AdminService.validate_commissioner_access(actor_id, league_id):
                raise AdminValidationError("Commissioner access required")
            
            # Get bid audit
            bid_audit = await AuditService.get_bid_audit(
                league_id=league_id,
                auction_id=request.auction_id,
                user_id=request.user_id,
                limit=100
            )
            
            # Get admin logs
            admin_logs = await AuditService.get_audit_logs(
                league_id=league_id,
                start_date=request.start_date,
                end_date=request.end_date,
                limit=100
            )
            
            # Get audit summary
            audit_summary = await AuditService.get_league_audit_summary(league_id)
            
            return {
                "success": True,
                "data": {
                    "bid_audit": bid_audit,
                    "admin_logs": [log.dict() for log in admin_logs],
                    "audit_summary": audit_summary
                }
            }
            
        except AdminValidationError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Failed to get comprehensive audit: {e}")
            return {"success": False, "message": "Failed to get audit data"}