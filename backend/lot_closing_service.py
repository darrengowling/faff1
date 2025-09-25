"""
Lot Closing Service with Atomic Operations and Undo Support
Handles two-phase lot closing with 10-second undo window
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple, List
from motor.motor_asyncio import AsyncIOMotorClientSession

from database import db
from models import LotStatus, UndoableAction, AdminAction
from audit_service import AuditService

logger = logging.getLogger(__name__)

class LotClosingService:
    """Service for managing atomic lot closing with undo functionality"""
    
    UNDO_WINDOW_SECONDS = 10
    
    @staticmethod
    async def initiate_lot_close(
        lot_id: str, 
        commissioner_id: str, 
        forced: bool = False,
        reason: str = "Commissioner closed lot"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Initiate lot closing with 10-second undo window
        Returns: (success, message, action_id)
        """
        try:
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    # Get current lot state
                    lot = await db.lots.find_one({"_id": lot_id}, session=session)
                    if not lot:
                        return False, "Lot not found", None
                    
                    # Validate lot can be closed
                    can_close, close_error = await LotClosingService._validate_lot_closeable(
                        lot, forced, session
                    )
                    if not can_close:
                        return False, close_error, None
                    
                    # Store original state for undo
                    original_state = {
                        "status": lot["status"],
                        "timer_ends_at": lot.get("timer_ends_at"),
                        "current_bid": lot.get("current_bid", 0),
                        "leading_bidder_id": lot.get("leading_bidder_id"),
                        "bids_count": len(lot.get("bids", [])),
                        "closed_at": lot.get("closed_at"),
                        "winner_id": lot.get("winner_id"),
                        "winning_bid": lot.get("winning_bid", 0)
                    }
                    
                    # Calculate undo deadline
                    undo_deadline = datetime.now(timezone.utc) + timedelta(
                        seconds=LotClosingService.UNDO_WINDOW_SECONDS
                    )
                    
                    # Prepare new state (pre-closed)
                    new_state = {
                        "status": LotStatus.PRE_CLOSED,
                        "pre_close_initiated_at": datetime.now(timezone.utc),
                        "pre_close_commissioner": commissioner_id,
                        "undo_deadline": undo_deadline,
                        "pending_close_reason": reason
                    }
                    
                    # Update lot to pre-closed status
                    await db.lots.update_one(
                        {"_id": lot_id},
                        {
                            "$set": {
                                "status": LotStatus.PRE_CLOSED,
                                "pre_close_initiated_at": new_state["pre_close_initiated_at"],
                                "pre_close_commissioner": commissioner_id,
                                "undo_deadline": undo_deadline,
                                "pending_close_reason": reason,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        },
                        session=session
                    )
                    
                    # Create undoable action record
                    action = UndoableAction(
                        lot_id=lot_id,
                        action_type="lot_close",
                        commissioner_id=commissioner_id,
                        original_state=original_state,
                        new_state=new_state,
                        undo_deadline=undo_deadline
                    )
                    
                    await db.undoable_actions.insert_one(
                        action.dict(by_alias=True), session=session
                    )
                    
                    # Log the action
                    await AuditService.log_admin_action(
                        AdminAction(
                            commissioner_id=commissioner_id,
                            action="lot_pre_close_initiated",
                            entity_type="lot",
                            entity_id=lot_id,
                            details={
                                "reason": reason,
                                "forced": forced,
                                "undo_deadline": undo_deadline.isoformat(),
                                "action_id": action.action_id
                            }
                        ),
                        session
                    )
                    
                    # Schedule automatic finalization
                    asyncio.create_task(
                        LotClosingService._schedule_auto_finalize(
                            action.action_id, undo_deadline
                        )
                    )
                    
                    logger.info(
                        f"Lot {lot_id} pre-closed by {commissioner_id}, "
                        f"undo deadline: {undo_deadline}"
                    )
                    
                    return True, "Lot closing initiated. 10 seconds to undo.", action.action_id
                    
        except Exception as e:
            logger.error(f"Error initiating lot close: {e}")
            return False, f"Failed to initiate lot close: {str(e)}", None
    
    @staticmethod
    async def undo_lot_close(action_id: str, commissioner_id: str) -> Tuple[bool, str]:
        """
        Undo a lot closing within the undo window
        Returns: (success, message)
        """
        try:
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    # Get the undoable action
                    action_doc = await db.undoable_actions.find_one(
                        {"action_id": action_id}, session=session
                    )
                    if not action_doc:
                        return False, "Action not found"
                    
                    action = UndoableAction(**action_doc)
                    
                    # Validate undo is allowed
                    can_undo, undo_error = await LotClosingService._validate_undo_allowed(
                        action, commissioner_id, session
                    )
                    if not can_undo:
                        return False, undo_error
                    
                    # Get current lot state
                    lot = await db.lots.find_one({"_id": action.lot_id}, session=session)
                    if not lot:
                        return False, "Lot not found"
                    
                    # Verify no bids placed during undo window
                    if await LotClosingService._has_bids_after_pre_close(lot, session):
                        return False, "Cannot undo: new bids received after pre-close"
                    
                    # Restore original state
                    update_data = {
                        "status": action.original_state["status"],
                        "updated_at": datetime.now(timezone.utc)
                    }
                    
                    unset_data = {
                        "pre_close_initiated_at": "",
                        "pre_close_commissioner": "",
                        "undo_deadline": "",
                        "pending_close_reason": ""
                    }
                    
                    # Restore timer if it existed
                    if action.original_state.get("timer_ends_at"):
                        update_data["timer_ends_at"] = action.original_state["timer_ends_at"]
                    
                    await db.lots.update_one(
                        {"_id": action.lot_id},
                        {"$set": update_data, "$unset": unset_data},
                        session=session
                    )
                    
                    # Mark action as undone
                    await db.undoable_actions.update_one(
                        {"action_id": action_id},
                        {
                            "$set": {
                                "is_undone": True,
                                "undone_at": datetime.now(timezone.utc),
                                "undone_by": commissioner_id
                            }
                        },
                        session=session
                    )
                    
                    # Log the undo action
                    await AuditService.log_admin_action(
                        AdminAction(
                            commissioner_id=commissioner_id,
                            action="lot_close_undone",
                            entity_type="lot", 
                            entity_id=action.lot_id,
                            details={
                                "original_action_id": action_id,
                                "reason": "Commissioner undo within window"
                            }
                        ),
                        session
                    )
                    
                    logger.info(f"Lot close undone for lot {action.lot_id} by {commissioner_id}")
                    return True, "Lot close successfully undone"
                    
        except Exception as e:
            logger.error(f"Error undoing lot close: {e}")
            return False, f"Failed to undo lot close: {str(e)}"
    
    @staticmethod
    async def finalize_lot_close(action_id: str) -> Tuple[bool, str]:
        """
        Finalize lot closing after undo window expires
        Returns: (success, message)
        """
        try:
            async with await db.client.start_session() as session:
                async with session.start_transaction():
                    # Get the undoable action
                    action_doc = await db.undoable_actions.find_one(
                        {"action_id": action_id}, session=session
                    )
                    if not action_doc:
                        return False, "Action not found"
                    
                    action = UndoableAction(**action_doc)
                    
                    # Check if already undone or finalized
                    if action.is_undone:
                        return False, "Action was already undone"
                    
                    # Check if undo window has expired
                    if datetime.now(timezone.utc) < action.undo_deadline:
                        return False, "Undo window still active"
                    
                    # Get lot and finalize
                    lot = await db.lots.find_one({"_id": action.lot_id}, session=session)
                    if not lot:
                        return False, "Lot not found"
                    
                    # Determine final status and winner
                    final_status = LotStatus.SOLD if lot.get("leading_bidder_id") else LotStatus.UNSOLD
                    
                    update_data = {
                        "status": final_status,
                        "closed_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                    
                    unset_data = {
                        "pre_close_initiated_at": "",
                        "pre_close_commissioner": "",
                        "undo_deadline": "",
                        "pending_close_reason": ""
                    }
                    
                    if final_status == LotStatus.SOLD and lot.get("leading_bidder_id"):
                        update_data["winner_id"] = lot["leading_bidder_id"]
                        update_data["winning_bid"] = lot.get("current_bid", 0)
                    
                    await db.lots.update_one(
                        {"_id": action.lot_id},
                        {"$set": update_data, "$unset": unset_data},
                        session=session
                    )
                    
                    # Mark action as finalized
                    await db.undoable_actions.update_one(
                        {"action_id": action_id},
                        {
                            "$set": {
                                "finalized_at": datetime.now(timezone.utc),
                                "final_status": final_status
                            }
                        },
                        session=session
                    )
                    
                    # Log finalization
                    await AuditService.log_admin_action(
                        AdminAction(
                            commissioner_id="system",
                            action="lot_close_finalized",
                            entity_type="lot",
                            entity_id=action.lot_id,
                            details={
                                "action_id": action_id,
                                "final_status": final_status,
                                "winner_id": update_data.get("winner_id"),
                                "winning_bid": update_data.get("winning_bid", 0)
                            }
                        ),
                        session
                    )
                    
                    logger.info(f"Lot {action.lot_id} finalized as {final_status}")
                    return True, f"Lot closed as {final_status}"
                    
        except Exception as e:
            logger.error(f"Error finalizing lot close: {e}")
            return False, f"Failed to finalize lot close: {str(e)}"
    
    @staticmethod
    async def _validate_lot_closeable(
        lot: Dict, 
        forced: bool, 
        session: AsyncIOMotorClientSession
    ) -> Tuple[bool, str]:
        """Validate that a lot can be closed"""
        if lot["status"] == LotStatus.PRE_CLOSED:
            return False, "Lot is already in closing process"
        
        if lot["status"] in [LotStatus.SOLD, LotStatus.UNSOLD]:
            return False, "Lot is already closed"
        
        if not forced and lot["status"] == LotStatus.OPEN:
            # Check if timer is still running
            if lot.get("timer_ends_at"):
                timer_end = lot["timer_ends_at"]
                if isinstance(timer_end, str):
                    timer_end = datetime.fromisoformat(timer_end.replace('Z', '+00:00'))
                
                if timer_end > datetime.now(timezone.utc):
                    return False, "Cannot close lot while timer is active (use force close)"
        
        return True, ""
    
    @staticmethod
    async def _validate_undo_allowed(
        action: UndoableAction,
        commissioner_id: str, 
        session: AsyncIOMotorClientSession
    ) -> Tuple[bool, str]:
        """Validate that an undo is allowed"""
        if action.is_undone:
            return False, "Action has already been undone"
        
        if datetime.now(timezone.utc) > action.undo_deadline:
            return False, "Undo window has expired"
        
        # Only allow commissioners to undo
        return True, ""
    
    @staticmethod
    async def _has_bids_after_pre_close(
        lot: Dict, 
        session: AsyncIOMotorClientSession
    ) -> bool:
        """Check if any bids were placed after pre-close initiation"""
        if not lot.get("pre_close_initiated_at"):
            return False
        
        # Check if any bids have timestamps after pre-close
        bids = lot.get("bids", [])
        pre_close_time = lot["pre_close_initiated_at"]
        
        for bid in bids:
            bid_time = bid.get("timestamp")
            if bid_time and bid_time > pre_close_time:
                return True
        
        return False
    
    @staticmethod
    async def _schedule_auto_finalize(action_id: str, deadline: datetime):
        """Schedule automatic finalization of lot close"""
        try:
            # Calculate sleep time
            sleep_time = (deadline - datetime.now(timezone.utc)).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            
            # Auto-finalize
            success, message = await LotClosingService.finalize_lot_close(action_id)
            if success:
                logger.info(f"Auto-finalized lot close action {action_id}")
            else:
                logger.warning(f"Auto-finalize failed for action {action_id}: {message}")
                
        except Exception as e:
            logger.error(f"Error in auto-finalize task for action {action_id}: {e}")

    @staticmethod
    async def get_active_undo_actions(lot_id: str) -> List[Dict]:
        """Get active undo actions for a lot"""
        try:
            cursor = db.undoable_actions.find({
                "lot_id": lot_id,
                "is_undone": False,
                "undo_deadline": {"$gt": datetime.now(timezone.utc)}
            })
            
            actions = await cursor.to_list(length=None)
            return actions
            
        except Exception as e:
            logger.error(f"Error getting active undo actions: {e}")
            return []