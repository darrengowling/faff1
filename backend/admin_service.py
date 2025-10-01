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
    async def validate_roster_capacity(user_id: str, league_id: str) -> Tuple[bool, str]:
        """
        GUARDRAIL: Validate roster capacity constraints with user-friendly errors
        
        Args:
            user_id: User acquiring club
            league_id: League context
            
        Returns:
            Tuple of (is_valid, user_friendly_error_message)
        """
        try:
            # Get league settings for club slots
            league = await db.leagues.find_one({"_id": league_id})
            if not league:
                return False, "League not found"
            
            max_slots = league["settings"]["club_slots_per_manager"]
            
            # Count current clubs owned by user
            current_clubs_count = await db.roster_clubs.count_documents({
                "user_id": user_id,
                "league_id": league_id
            })
            
            # Check if user has available club slots
            if current_clubs_count >= max_slots:
                return False, f"You already own {current_clubs_count}/{max_slots} clubs"
            
            return True, ""
        except Exception as e:
            logger.error(f"Failed to validate roster capacity: {e}")
            return False, "Roster capacity validation failed"

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
            current_time = datetime.now(timezone.utc)
            
            # Timer can only extend forward from current time
            if new_end_time <= current_time:
                return False, f"Timer cannot be set to past or current time"
            
            return True, ""
        except Exception as e:
            logger.error(f"Failed to validate timer monotonicity: {e}")
            return False, "Timer validation failed"

    @staticmethod
    async def validate_simultaneous_bid_handling(lot_id: str, bidder_id: str, bid_amount: int) -> Tuple[bool, str]:
        """
        GUARDRAIL: Handle simultaneous bidding attempts atomically
        
        Args:
            lot_id: Lot being bid on
            bidder_id: User placing bid
            bid_amount: Bid amount
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get current lot state
            lot = await db.lots.find_one({"_id": lot_id})
            if not lot:
                return False, "Lot not found"
            
            # Check if bid is valid (higher than current)
            if bid_amount <= lot["current_bid"]:
                return False, f"Bid must be higher than current bid of {lot['current_bid']}"
            
            # Check if lot is still active
            if lot["status"] not in ["open", "going_once", "going_twice"]:
                return False, "Lot is no longer accepting bids"
            
            return True, ""
        except Exception as e:
            logger.error(f"Failed to validate simultaneous bid: {e}")
            return False, "Bid validation failed"

    @staticmethod
    async def handle_simultaneous_bids(lot_id: str, bidder_id: str, bid_amount: int) -> Tuple[bool, str, str]:
        """
        Handle actual bid placement with atomic operations to prevent race conditions
        
        Args:
            lot_id: Lot being bid on
            bidder_id: User placing bid  
            bid_amount: Bid amount
            
        Returns:
            Tuple of (success, message, bid_id)
        """
        try:
            from models import Bid
            import uuid
            from datetime import datetime, timezone
            
            # Use atomic update to prevent race conditions
            # Only update if current bid is still lower than our bid
            update_result = await db.lots.update_one(
                {
                    "_id": lot_id,
                    "current_bid": {"$lt": bid_amount},
                    "status": {"$in": ["open", "going_once", "going_twice"]}
                },
                {
                    "$set": {
                        "current_bid": bid_amount,
                        "top_bidder_id": bidder_id,
                        "last_bid_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if update_result.modified_count == 0:
                # Either lot not found, bid too low, or lot not active
                lot = await db.lots.find_one({"_id": lot_id})
                if not lot:
                    return False, "Lot not found", ""
                elif lot["current_bid"] >= bid_amount:
                    return False, f"Bid of {bid_amount} is not higher than current bid of {lot['current_bid']}", ""
                else:
                    return False, "Lot is no longer accepting bids", ""
            
            # Create bid record
            bid = Bid(
                lot_id=lot_id,
                bidder_id=bidder_id,
                amount=bid_amount,
                timestamp=datetime.now(timezone.utc),
                status="winning"
            )
            
            bid_dict = bid.dict(by_alias=True)
            await db.bids.insert_one(bid_dict)
            
            # Mark previous bids for this lot as outbid
            await db.bids.update_many(
                {
                    "lot_id": lot_id,
                    "_id": {"$ne": bid.id},
                    "status": "winning"
                },
                {"$set": {"status": "outbid"}}
            )
            
            logger.info(f"Successful bid placed: {bidder_id} bid {bid_amount} on lot {lot_id}")
            return True, f"Successful bid of {bid_amount}", str(bid.id)
            
        except Exception as e:
            logger.error(f"Failed to handle simultaneous bids: {e}")
            return False, "Failed to place bid", ""

    @staticmethod
    async def validate_budget_change_constraints(league_id: str, new_budget: int) -> Tuple[bool, str]:
        """
        GUARDRAIL: Validate budget change constraints
        
        Budget changes are only allowed when:
        - Auction status is "scheduled" or "paused"
        - No roster clubs exist in the league (no purchases made)
        
        Args:
            league_id: League to check
            new_budget: New budget per manager
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get auction status
            auction = await db.auctions.find_one({"league_id": league_id})
            if not auction:
                return False, "Auction not found"
            
            # Check auction status
            if auction["status"] not in ["scheduled", "paused"]:
                return False, f"Budget changes only allowed when auction is scheduled or paused (current: {auction['status']})"
            
            # Check if any clubs have been purchased
            club_purchases = await db.roster_clubs.count_documents({"league_id": league_id})
            if club_purchases > 0:
                return False, f"Budget cannot be changed after clubs have been purchased ({club_purchases} clubs owned)"
            
            return True, ""
        except Exception as e:
            logger.error(f"Failed to validate budget change constraints: {e}")
            return False, "Budget change validation failed"

    @staticmethod
    async def validate_league_size_constraints(league_id: str, action: str) -> Tuple[bool, str]:
        """
        GUARDRAIL: Validate league size constraints with user-friendly errors
        
        Args:
            league_id: League to check
            action: Action being performed ("invite", "start_auction")
            
        Returns:
            Tuple of (is_valid, user_friendly_error_message)
        """
        try:
            # Get league settings
            league = await db.leagues.find_one({"_id": league_id})
            if not league:
                return False, "League not found"
            
            current_members = league["member_count"]
            league_size = league["settings"]["league_size"]
            min_size = league_size["min"]
            max_size = league_size["max"]
            
            if action == "invite":
                # Check if adding one more member would exceed max
                if current_members >= max_size:
                    return False, f"League is full ({current_members}/{max_size} managers)"
                
            elif action == "start_auction":
                # Check if current members meet minimum requirement
                if current_members < min_size:
                    return False, f"You must have ≥ {min_size} managers to start (currently have {current_members})"
            
            return True, ""
        except Exception as e:
            logger.error(f"Failed to validate league size constraints: {e}")
            return False, "League size validation failed"

    @staticmethod
    async def update_league_settings(
        league_id: str,
        user_id: str,
        updates: LeagueSettingsUpdate
    ) -> Tuple[bool, str]:
        """
        Update league settings with comprehensive validation guardrails
        
        Args:
            league_id: League to update
            user_id: User making the update (must be commissioner)
            updates: Settings to update
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # 1. Validate commissioner access
            if not await AdminService.validate_commissioner_access(user_id, league_id):
                return False, "Only commissioner can update league settings"
            
            # Get current league state
            league = await db.leagues.find_one({"_id": league_id})
            if not league:
                return False, "League not found"
            
            current_settings = league["settings"]
            
            # 2. BUDGET CHANGE VALIDATION
            if updates.budget_per_manager is not None and updates.budget_per_manager != current_settings.get("budget_per_manager"):
                budget_valid, budget_error = await AdminService.validate_budget_change_constraints(
                    league_id, updates.budget_per_manager
                )
                if not budget_valid:
                    return False, budget_error
            
            # 3. CLUB SLOTS VALIDATION
            if updates.club_slots_per_manager is not None:
                # After migration, all leagues should have club_slots_per_manager set
                current_slots = current_settings.get("club_slots_per_manager")
                if current_slots is None:
                    return False, "League missing club_slots_per_manager setting. Please run migration."
                
                new_slots = updates.club_slots_per_manager
                
                # If decreasing slots, ensure all current rosters fit the new limit
                if new_slots < current_slots:
                    max_clubs_owned = await db.roster_clubs.aggregate([
                        {"$match": {"league_id": league_id}},
                        {"$group": {
                            "_id": "$user_id",
                            "clubs_owned": {"$sum": 1}
                        }},
                        {"$group": {
                            "_id": None,
                            "max_clubs": {"$max": "$clubs_owned"}
                        }}
                    ]).to_list(length=1)
                    
                    max_owned = max_clubs_owned[0]["max_clubs"] if max_clubs_owned else 0
                    if max_owned > new_slots:
                        return False, f"Cannot reduce club slots to {new_slots}: some managers own {max_owned} clubs"
            
            # 4. LEAGUE SIZE VALIDATION
            if updates.league_size is not None and updates.league_size.max is not None:
                current_members = league["member_count"]
                if updates.league_size.max < current_members:
                    return False, f"Cannot reduce max league size to {updates.league_size.max}: currently have {current_members} members"
            
            # 5. Apply updates atomically
            update_dict = {}
            
            if updates.budget_per_manager is not None:
                update_dict["settings.budget_per_manager"] = updates.budget_per_manager
            
            if updates.club_slots_per_manager is not None:
                update_dict["settings.club_slots_per_manager"] = updates.club_slots_per_manager
                
                # Update all rosters with new club slots
                await db.rosters.update_many(
                    {"league_id": league_id},
                    {"$set": {"club_slots": updates.club_slots_per_manager}}
                )
            
            if updates.league_size is not None:
                if updates.league_size.min is not None:
                    update_dict["settings.league_size.min"] = updates.league_size.min
                if updates.league_size.max is not None:
                    update_dict["settings.league_size.max"] = updates.league_size.max
            
            # Update league settings
            if update_dict:
                await db.leagues.update_one(
                    {"_id": league_id},
                    {"$set": update_dict}
                )
                
                # BUDGET CHANGE: Update all rosters if budget changed
                if updates.budget_per_manager is not None:
                    await db.rosters.update_many(
                        {"league_id": league_id},
                        {"$set": {
                            "budget_start": updates.budget_per_manager,
                            "budget_remaining": updates.budget_per_manager
                        }}
                    )
                
                # Log the settings update
                await log_league_settings_update(
                    league_id=league_id,
                    actor_id=user_id,
                    before=current_settings,
                    after=update_dict
                )
            
            logger.info(f"Updated league {league_id} settings by user {user_id}")
            return True, "League settings updated successfully"
            
        except Exception as e:
            logger.error(f"Failed to update league settings: {e}")
            return False, f"Failed to update settings: {str(e)}"

    @staticmethod
    async def approve_member(league_id: str, commissioner_id: str, target_user_id: str) -> Tuple[bool, str]:
        """
        Approve a pending member (currently a no-op since auto-approval is enabled)
        """
        try:
            # Validate permissions
            if not await AdminService.validate_commissioner_access(commissioner_id, league_id):
                return False, "Only commissioner can approve members"
            
            # Log the action
            await log_member_action(
                league_id=league_id,
                user_id=commissioner_id,
                target_user_id=target_user_id,
                action="approve_member"
            )
            
            return True, "Member approved successfully"
            
        except Exception as e:
            logger.error(f"Failed to approve member: {e}")
            return False, f"Failed to approve member: {str(e)}"

    @staticmethod
    async def kick_member(league_id: str, commissioner_id: str, target_user_id: str) -> Tuple[bool, str]:
        """
        Remove a member from the league (with validation guardrails)
        """
        try:
            # Validate permissions
            if not await AdminService.validate_commissioner_access(commissioner_id, league_id):
                return False, "Only commissioner can kick members"
            
            # Cannot kick the commissioner
            if target_user_id == commissioner_id:
                return False, "Commissioner cannot kick themselves"
            
            # Validate member exists
            membership = await db.memberships.find_one({
                "league_id": league_id,
                "user_id": target_user_id
            })
            
            if not membership:
                return False, "Member not found in league"
            
            # TODO: Add auction state validation (cannot kick during active auction)
            
            # Remove membership, roster, and owned clubs
            await db.memberships.delete_one({
                "league_id": league_id,
                "user_id": target_user_id
            })
            
            await db.rosters.delete_one({
                "league_id": league_id,
                "user_id": target_user_id
            })
            
            await db.roster_clubs.delete_many({
                "league_id": league_id,
                "user_id": target_user_id
            })
            
            # Update league member count
            await db.leagues.update_one(
                {"_id": league_id},
                {"$inc": {"member_count": -1}}
            )
            
            # Log the action
            await log_member_action(
                league_id=league_id,
                user_id=commissioner_id,
                target_user_id=target_user_id,
                action="kick_member"
            )
            
            logger.info(f"Kicked member {target_user_id} from league {league_id}")
            return True, "Member removed successfully"
            
        except Exception as e:
            logger.error(f"Failed to kick member: {e}")
            return False, f"Failed to remove member: {str(e)}"

    @staticmethod
    async def manage_member(league_id: str, commissioner_id: str, member_action: 'MemberAction') -> Tuple[bool, str]:
        """
        Manage league member (approve or kick)
        """
        try:
            if member_action.action == "approve":
                return await AdminService.approve_member(league_id, commissioner_id, member_action.member_id)
            elif member_action.action == "kick":
                return await AdminService.kick_member(league_id, commissioner_id, member_action.member_id)
            else:
                return False, f"Unknown action: {member_action.action}"
        except Exception as e:
            logger.error(f"Failed to manage member: {e}")
            return False, f"Failed to manage member: {str(e)}"

    @staticmethod
    async def start_auction(league_id: str, commissioner_id: str) -> Tuple[bool, str]:
        """
        Start the auction for a league
        """
        try:
            # Validate permissions
            if not await AdminService.validate_commissioner_access(commissioner_id, league_id):
                return False, "Only commissioner can start auction"
            
            # Validate league size constraints
            size_valid, size_error = await AdminService.validate_league_size_constraints(league_id, "start_auction")
            if not size_valid:
                return False, size_error
            
            # Get auction
            auction = await db.auctions.find_one({"league_id": league_id})
            if not auction:
                return False, "Auction not found"
            
            if auction["status"] != "scheduled":
                return False, f"Auction cannot be started (current status: {auction['status']})"
            
            # Update auction status
            await db.auctions.update_one(
                {"_id": auction["_id"]},
                {"$set": {"status": "live"}}
            )
            
            # Log the action
            await log_auction_action(
                league_id=league_id,
                user_id=commissioner_id,
                action="start_auction"
            )
            
            logger.info(f"Started auction for league {league_id}")
            return True, "Auction started successfully"
            
        except Exception as e:
            logger.error(f"Failed to start auction: {e}")
            return False, f"Failed to start auction: {str(e)}"

    @staticmethod
    async def pause_auction(league_id: str, commissioner_id: str) -> Tuple[bool, str]:
        """
        Pause the auction for a league
        """
        try:
            # Validate permissions
            if not await AdminService.validate_commissioner_access(commissioner_id, league_id):
                return False, "Only commissioner can pause auction"
            
            # Get auction
            auction = await db.auctions.find_one({"league_id": league_id})
            if not auction:
                return False, "Auction not found"
            
            if auction["status"] != "live":
                return False, f"Auction cannot be paused (current status: {auction['status']})"
            
            # Update auction status
            await db.auctions.update_one(
                {"_id": auction["_id"]},
                {"$set": {"status": "paused"}}
            )
            
            # Log the action
            await log_auction_action(
                league_id=league_id,
                user_id=commissioner_id,
                action="pause_auction"
            )
            
            logger.info(f"Paused auction for league {league_id}")
            return True, "Auction paused successfully"
            
        except Exception as e:
            logger.error(f"Failed to pause auction: {e}")
            return False, f"Failed to pause auction: {str(e)}"

    @staticmethod
    async def resume_auction(league_id: str, commissioner_id: str) -> Tuple[bool, str]:
        """
        Resume the auction for a league
        """
        try:
            # Validate permissions
            if not await AdminService.validate_commissioner_access(commissioner_id, league_id):
                return False, "Only commissioner can resume auction"
            
            # Get auction
            auction = await db.auctions.find_one({"league_id": league_id})
            if not auction:
                return False, "Auction not found"
            
            if auction["status"] != "paused":
                return False, f"Auction cannot be resumed (current status: {auction['status']})"
            
            # Update auction status
            await db.auctions.update_one(
                {"_id": auction["_id"]},
                {"$set": {"status": "live"}}
            )
            
            # Log the action
            await log_auction_action(
                league_id=league_id,
                user_id=commissioner_id,
                action="resume_auction"
            )
            
            logger.info(f"Resumed auction for league {league_id}")
            return True, "Auction resumed successfully"
            
        except Exception as e:
            logger.error(f"Failed to resume auction: {e}")
            return False, f"Failed to resume auction: {str(e)}"

    @staticmethod
    async def get_comprehensive_audit(league_id: str, commissioner_id: str) -> Optional[Dict]:
        """
        Get comprehensive audit information for the league
        """
        try:
            # Validate permissions
            if not await AdminService.validate_commissioner_access(commissioner_id, league_id):
                return None
            
            # Get recent admin logs
            admin_logs = await db.admin_logs.find({
                "league_id": league_id
            }).sort("timestamp", -1).limit(50).to_list(length=None)
            
            # Get league statistics
            league = await db.leagues.find_one({"_id": league_id})
            auction = await db.auctions.find_one({"league_id": league_id})
            
            member_count = await db.memberships.count_documents({"league_id": league_id})
            club_count = await db.roster_clubs.count_documents({"league_id": league_id})
            total_spent = await db.roster_clubs.aggregate([
                {"$match": {"league_id": league_id}},
                {"$group": {"_id": None, "total": {"$sum": "$price"}}}
            ]).to_list(length=1)
            
            return {
                "league_info": {
                    "name": league["name"] if league else "Unknown",
                    "status": league["status"] if league else "Unknown",
                    "member_count": member_count,
                    "clubs_owned": club_count,
                    "total_spent": total_spent[0]["total"] if total_spent else 0
                },
                "auction_info": {
                    "status": auction["status"] if auction else "Unknown",
                    "budget_per_manager": auction["budget_per_manager"] if auction else 0
                },
                "recent_actions": [
                    {
                        "action": log["action"],
                        "user_id": log["user_id"],
                        "timestamp": log["timestamp"],
                        "details": log.get("details", {})
                    }
                    for log in admin_logs
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive audit: {e}")
            return None

    @staticmethod
    async def get_admin_logs(league_id: str, commissioner_id: str, limit: int = 50) -> List[Dict]:
        """
        Get admin action logs for the league
        """
        try:
            # Validate permissions
            if not await AdminService.validate_commissioner_access(commissioner_id, league_id):
                return []
            
            logs = await db.admin_logs.find({
                "league_id": league_id
            }).sort("timestamp", -1).limit(limit).to_list(length=None)
            
            return [
                {
                    "id": log["_id"],
                    "action": log["action"],
                    "user_id": log["user_id"],
                    "timestamp": log["timestamp"],
                    "details": log.get("details", {})
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Failed to get admin logs: {e}")
            return []

    @staticmethod
    async def get_bid_audit_trail(league_id: str, commissioner_id: str) -> List[Dict]:
        """
        Get bid audit trail for the league
        """
        try:
            # Validate permissions
            if not await AdminService.validate_commissioner_access(commissioner_id, league_id):
                return []
            
            # Get all bids for the league
            bids = await db.bids.find({
                "league_id": league_id
            }).sort("timestamp", -1).to_list(length=None)
            
            return [
                {
                    "id": bid["_id"],
                    "lot_id": bid["lot_id"],
                    "bidder_id": bid["bidder_id"],
                    "amount": bid["amount"],
                    "timestamp": bid["timestamp"],
                    "status": bid.get("status", "unknown")
                }
                for bid in bids
            ]
            
        except Exception as e:
            logger.error(f"Failed to get bid audit trail: {e}")
            return []