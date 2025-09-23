import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone

from models import AdminLog, AdminLogCreate, AdminLogResponse
from database import db

logger = logging.getLogger(__name__)

class AuditService:
    """
    Comprehensive audit logging service for admin actions and system events
    Ensures compliance and traceability of all administrative operations
    """
    
    @staticmethod
    async def log_admin_action(
        league_id: str,
        actor_id: str,
        action: str,
        before: Optional[Dict] = None,
        after: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log an administrative action for audit trail
        
        Args:
            league_id: The league where action was performed
            actor_id: User ID of the commissioner performing action
            action: Action type (from AdminAction enum)
            before: State before the action
            after: State after the action
            metadata: Additional context or parameters
            
        Returns:
            The ID of the created audit log entry
        """
        try:
            audit_log = AdminLog(
                league_id=league_id,
                actor_id=actor_id,
                action=action,
                before=before,
                after=after,
                metadata=metadata
            )
            
            audit_dict = audit_log.dict(by_alias=True)
            result = await db.admin_logs.insert_one(audit_dict)
            
            logger.info(f"Admin action logged: {action} by {actor_id} in league {league_id}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
            # Don't raise exception to avoid breaking the main action
            return ""

    @staticmethod
    async def get_audit_logs(
        league_id: str,
        limit: int = 100,
        offset: int = 0,
        actor_id: Optional[str] = None,
        action_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AdminLogResponse]:
        """
        Retrieve audit logs with filtering
        
        Args:
            league_id: League to get logs for
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            actor_id: Filter by specific actor
            action_filter: Filter by action type
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            
        Returns:
            List of audit log responses
        """
        try:
            # Build query filter
            query = {"league_id": league_id}
            
            if actor_id:
                query["actor_id"] = actor_id
                
            if action_filter:
                query["action"] = action_filter
                
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["created_at"] = date_filter
            
            # Execute query with pagination
            cursor = db.admin_logs.find(query).sort("created_at", -1).skip(offset).limit(limit)
            logs = await cursor.to_list(length=None)
            
            # Convert to response models
            audit_responses = []
            for log in logs:
                audit_responses.append(AdminLogResponse(
                    id=log["_id"],
                    league_id=log["league_id"],
                    actor_id=log["actor_id"],
                    action=log["action"],
                    before=log.get("before"),
                    after=log.get("after"),
                    metadata=log.get("metadata"),
                    created_at=log["created_at"]
                ))
            
            return audit_responses
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []

    @staticmethod
    async def get_bid_audit(
        league_id: Optional[str] = None,
        auction_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get comprehensive bid audit information
        
        Args:
            league_id: Filter by league
            auction_id: Filter by auction
            user_id: Filter by user
            limit: Maximum number of bids to return
            offset: Number of bids to skip
            
        Returns:
            List of bid information with audit details
        """
        try:
            # Build aggregation pipeline for comprehensive bid audit
            pipeline = []
            
            # Match stage
            match_conditions = {}
            if league_id:
                match_conditions["league_id"] = league_id
            if auction_id:
                match_conditions["auction_id"] = auction_id
            if user_id:
                match_conditions["user_id"] = user_id
            
            if match_conditions:
                pipeline.append({"$match": match_conditions})
            
            # Lookup user information
            pipeline.extend([
                {"$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }},
                {"$unwind": "$user"},
                
                # Lookup lot information
                {"$lookup": {
                    "from": "lots",
                    "localField": "lot_id",
                    "foreignField": "_id",
                    "as": "lot"
                }},
                {"$unwind": "$lot"},
                
                # Lookup club information
                {"$lookup": {
                    "from": "clubs",
                    "localField": "lot.club_id",
                    "foreignField": "_id",
                    "as": "club"
                }},
                {"$unwind": "$club"},
                
                # Project final structure
                {"$project": {
                    "bid_id": "$_id",
                    "auction_id": 1,
                    "league_id": 1,
                    "lot_id": 1,
                    "user_id": 1,
                    "amount": 1,
                    "placed_at": 1,
                    "status": 1,
                    "user_name": "$user.display_name",
                    "user_email": "$user.email",
                    "club_name": "$club.name",
                    "club_short_name": "$club.short_name",
                    "lot_status": "$lot.status",
                    "lot_current_bid": "$lot.current_bid",
                    "lot_winner_id": "$lot.winner_id"
                }},
                
                # Sort by bid time (newest first)
                {"$sort": {"placed_at": -1}},
                
                # Pagination
                {"$skip": offset},
                {"$limit": limit}
            ])
            
            # Execute aggregation
            cursor = db.bids.aggregate(pipeline)
            bids = await cursor.to_list(length=None)
            
            return bids
            
        except Exception as e:
            logger.error(f"Failed to get bid audit: {e}")
            return []

    @staticmethod
    async def log_system_event(
        event_type: str,
        league_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> str:
        """
        Log system events (non-admin actions) for debugging and monitoring
        
        Args:
            event_type: Type of system event
            league_id: Associated league (if any)
            user_id: Associated user (if any)
            data: Event data
            
        Returns:
            Event log ID
        """
        try:
            # Use the same admin_logs collection but with system actor
            return await AuditService.log_admin_action(
                league_id=league_id or "system",
                actor_id=user_id or "system",
                action=f"system_{event_type}",
                after=data,
                metadata={"event_type": event_type}
            )
            
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
            return ""

    @staticmethod
    async def get_league_audit_summary(league_id: str) -> Dict:
        """
        Get audit summary for a league
        
        Args:
            league_id: League to get summary for
            
        Returns:
            Dictionary with audit statistics
        """
        try:
            # Aggregate audit statistics
            pipeline = [
                {"$match": {"league_id": league_id}},
                {"$group": {
                    "_id": "$action",
                    "count": {"$sum": 1},
                    "last_action": {"$max": "$created_at"},
                    "actors": {"$addToSet": "$actor_id"}
                }},
                {"$sort": {"count": -1}}
            ]
            
            action_stats = await db.admin_logs.aggregate(pipeline).to_list(length=None)
            
            # Get total counts
            total_logs = await db.admin_logs.count_documents({"league_id": league_id})
            
            # Get unique actors
            unique_actors = await db.admin_logs.distinct("actor_id", {"league_id": league_id})
            
            return {
                "league_id": league_id,
                "total_actions": total_logs,
                "unique_actors": len(unique_actors),
                "action_breakdown": action_stats,
                "actors": unique_actors
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit summary: {e}")
            return {}

# Convenience functions for common audit operations
async def log_league_settings_update(league_id: str, actor_id: str, before: Dict, after: Dict):
    """Log league settings update"""
    return await AuditService.log_admin_action(
        league_id=league_id,
        actor_id=actor_id,
        action="update_league_settings",
        before=before,
        after=after
    )

async def log_member_action(league_id: str, actor_id: str, action: str, member_id: str, details: Dict = None):
    """Log member management action"""
    return await AuditService.log_admin_action(
        league_id=league_id,
        actor_id=actor_id,
        action=action,
        metadata={"target_member_id": member_id, **(details or {})}
    )

async def log_auction_action(league_id: str, actor_id: str, action: str, auction_id: str, details: Dict = None):
    """Log auction management action"""
    return await AuditService.log_admin_action(
        league_id=league_id,
        actor_id=actor_id,
        action=action,
        metadata={"auction_id": auction_id, **(details or {})}
    )