from typing import List, Optional
from datetime import datetime, timezone, timedelta
import logging

from models import *
from database import db
from auth import create_magic_link_token, send_magic_link_email
from competition_service import CompetitionService

logger = logging.getLogger(__name__)

class LeagueService:
    """
    Comprehensive service for league management operations
    Handles league creation, invitations, and member management
    """
    
    @staticmethod
    async def create_league_with_setup(
        league_data: LeagueCreate,
        commissioner_id: str
    ) -> LeagueResponse:
        """
        Create a complete league setup with all related documents
        """
        try:
            # Get default settings from competition profile if no explicit settings provided
            if league_data.settings is None:
                competition_service = CompetitionService()
                default_settings = await competition_service.get_default_settings("ucl")
                logger.info(f"Using default settings from UCL competition profile")
            else:
                default_settings = league_data.settings
                logger.info(f"Using explicit settings provided by commissioner")
            
            # Create league with enhanced settings
            league = League(
                name=league_data.name,
                season=league_data.season or "2025-26",
                commissioner_id=commissioner_id,
                settings=default_settings,
                status="setup",
                member_count=1
            )
            league_dict = league.dict(by_alias=True)
            await db.leagues.insert_one(league_dict)
            
            # Create commissioner membership
            membership = Membership(
                league_id=league.id,
                user_id=commissioner_id,
                role=MembershipRole.COMMISSIONER,
                status=MembershipStatus.ACTIVE
            )
            membership_dict = membership.dict(by_alias=True)
            await db.memberships.insert_one(membership_dict)
            
            # Create default auction document
            auction = Auction(
                league_id=league.id,
                budget_per_manager=league.settings.budget_per_manager,
                min_increment=league.settings.min_increment,
                anti_snipe_seconds=league.settings.anti_snipe_seconds,
                bid_timer_seconds=league.settings.bid_timer_seconds
            )
            auction_dict = auction.dict(by_alias=True)
            await db.auctions.insert_one(auction_dict)
            
            # Create scoring rules from league settings
            scoring_rules = ScoringRules(
                league_id=league.id,
                rules=league.settings.scoring_rules
            )
            scoring_dict = scoring_rules.dict(by_alias=True)
            await db.scoring_rules.insert_one(scoring_dict)
            
            # Create commissioner roster
            roster = Roster(
                league_id=league.id,
                user_id=commissioner_id,
                budget_start=league.settings.budget_per_manager,
                budget_remaining=league.settings.budget_per_manager,
                club_slots=league.settings.club_slots_per_manager
            )
            roster_dict = roster.dict(by_alias=True)
            await db.rosters.insert_one(roster_dict)
            
            logger.info(f"Created complete league setup {league.id} by user {commissioner_id}")
            
            return LeagueResponse(
                id=league.id,
                name=league.name,
                competition=league.competition,
                season=league.season,
                commissioner_id=league.commissioner_id,
                settings=league.settings,
                status=league.status,
                member_count=league.member_count,
                created_at=league.created_at
            )
            
        except Exception as e:
            logger.error(f"Failed to create league: {e}")
            raise

    @staticmethod
    async def invite_manager(
        league_id: str,
        inviter_id: str,
        email: str
    ) -> InvitationResponse:
        """
        Send invitation to join league as manager
        """
        try:
            # Validate league exists and inviter is commissioner
            league = await db.leagues.find_one({"_id": league_id})
            if not league:
                raise ValueError("League not found")
            
            if league["commissioner_id"] != inviter_id:
                raise ValueError("Only commissioner can send invitations")
            
            # Check league size limit using new league_size settings
            from admin_service import AdminService
            size_valid, size_error = await AdminService.validate_league_size_constraints(league_id, "invite")
            if not size_valid:
                raise ValueError(size_error)
            
            # Check if email is already invited or member
            existing_invitation = await db.invitations.find_one({
                "league_id": league_id,
                "email": email,
                "status": {"$in": ["pending", "accepted"]}
            })
            if existing_invitation:
                raise ValueError("User already invited or member")
            
            existing_member = await db.users.find_one({"email": email})
            if existing_member:
                existing_membership = await db.memberships.find_one({
                    "league_id": league_id,
                    "user_id": existing_member["_id"]
                })
                if existing_membership:
                    raise ValueError("User is already a member")
            
            # Create invitation token
            token = create_magic_link_token(email)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=72)  # 3 days
            
            invitation = Invitation(
                league_id=league_id,
                inviter_id=inviter_id,
                email=email,
                token=token,
                expires_at=expires_at
            )
            invitation_dict = invitation.dict(by_alias=True)
            await db.invitations.insert_one(invitation_dict)
            
            # Send invitation email (or log for development)
            invitation_link = f"http://localhost:3000/invite?token={token}"
            logger.info(f"Invitation link for {email}: {invitation_link}")
            print(f"\n📨 Invitation Link for {email}:")
            print(f"   {invitation_link}\n")
            
            logger.info(f"Sent invitation to {email} for league {league_id}")
            
            return InvitationResponse(
                id=invitation.id,
                league_id=invitation.league_id,
                inviter_id=invitation.inviter_id,
                email=invitation.email,
                status=invitation.status,
                expires_at=invitation.expires_at,
                created_at=invitation.created_at,
                accepted_at=invitation.accepted_at
            )
            
        except Exception as e:
            logger.error(f"Failed to send invitation: {e}")
            raise

    @staticmethod
    async def accept_invitation(token: str, user_id: str) -> LeagueResponse:
        """
        Accept league invitation and join as manager
        """
        try:
            # Find and validate invitation
            invitation = await db.invitations.find_one({
                "token": token,
                "status": "pending"
            })
            
            if not invitation:
                raise ValueError("Invalid or expired invitation")
            
            if invitation["expires_at"] < datetime.now(timezone.utc):
                # Mark as expired
                await db.invitations.update_one(
                    {"_id": invitation["_id"]},
                    {"$set": {"status": "expired"}}
                )
                raise ValueError("Invitation has expired")
            
            # Get league and validate capacity using league_size settings
            league = await db.leagues.find_one({"_id": invitation["league_id"]})
            if not league:
                raise ValueError("League not found")
            
            from admin_service import AdminService
            size_valid, size_error = await AdminService.validate_league_size_constraints(
                invitation["league_id"], "invite"
            )
            if not size_valid:
                raise ValueError(size_error)
            
            # Check if user is already a member
            existing_membership = await db.memberships.find_one({
                "league_id": invitation["league_id"],
                "user_id": user_id
            })
            if existing_membership:
                raise ValueError("Already a member of this league")
            
            # Create membership
            membership = Membership(
                league_id=invitation["league_id"],
                user_id=user_id,
                role=MembershipRole.MANAGER,
                status=MembershipStatus.ACTIVE
            )
            membership_dict = membership.dict(by_alias=True)
            await db.memberships.insert_one(membership_dict)
            
            # Create roster for new member
            roster = Roster(
                league_id=invitation["league_id"],
                user_id=user_id,
                budget_start=league["settings"]["budget_per_manager"],
                budget_remaining=league["settings"]["budget_per_manager"],
                club_slots=league["settings"]["club_slots_per_manager"]
            )
            roster_dict = roster.dict(by_alias=True)
            await db.rosters.insert_one(roster_dict)
            
            # Update league member count
            await db.leagues.update_one(
                {"_id": invitation["league_id"]},
                {"$inc": {"member_count": 1}}
            )
            
            # Mark invitation as accepted
            await db.invitations.update_one(
                {"_id": invitation["_id"]},
                {
                    "$set": {
                        "status": "accepted",
                        "accepted_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"User {user_id} accepted invitation to league {invitation['league_id']}")
            
            # Return updated league info
            updated_league = await db.leagues.find_one({"_id": invitation["league_id"]})
            return LeagueResponse(
                id=updated_league["_id"],
                name=updated_league["name"],
                competition=updated_league["competition"],
                season=updated_league["season"],
                commissioner_id=updated_league["commissioner_id"],
                settings=LeagueSettings(**updated_league["settings"]),
                status=updated_league["status"],
                member_count=updated_league["member_count"],
                created_at=updated_league["created_at"]
            )
            
        except Exception as e:
            logger.error(f"Failed to accept invitation: {e}")
            raise

    @staticmethod
    async def get_league_members(league_id: str) -> List[LeagueMemberResponse]:
        """
        Get all members of a league with user details
        """
        try:
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
                    "role": 1,
                    "status": 1,
                    "joined_at": 1,
                    "email": "$user.email",
                    "display_name": "$user.display_name"
                }},
                {"$sort": {"joined_at": 1}}  # Commissioner first
            ]
            
            members = await db.memberships.aggregate(pipeline).to_list(length=None)
            
            return [
                LeagueMemberResponse(
                    user_id=member["user_id"],
                    email=member["email"],
                    display_name=member["display_name"],
                    role=MembershipRole(member["role"]),
                    status=MembershipStatus(member["status"]),
                    joined_at=member["joined_at"]
                )
                for member in members
            ]
            
        except Exception as e:
            logger.error(f"Failed to get league members: {e}")
            raise

    @staticmethod
    async def get_league_invitations(league_id: str) -> List[InvitationResponse]:
        """
        Get all invitations for a league
        """
        try:
            invitations = await db.invitations.find({
                "league_id": league_id
            }).sort("created_at", -1).to_list(length=None)
            
            return [
                InvitationResponse(
                    id=invitation["_id"],
                    league_id=invitation["league_id"],
                    inviter_id=invitation["inviter_id"],
                    email=invitation["email"],
                    status=InvitationStatus(invitation["status"]),
                    expires_at=invitation["expires_at"],
                    created_at=invitation["created_at"],
                    accepted_at=invitation.get("accepted_at")
                )
                for invitation in invitations
            ]
            
        except Exception as e:
            logger.error(f"Failed to get league invitations: {e}")
            raise

    @staticmethod
    async def validate_league_ready(league_id: str) -> bool:
        """
        Check if league is ready to start (has minimum members)
        """
        try:
            league = await db.leagues.find_one({"_id": league_id})
            if not league:
                return False
            
            min_members = league["settings"]["min_managers"]
            current_members = league["member_count"]
            
            is_ready = current_members >= min_members
            
            # Update league status if ready
            if is_ready and league["status"] == "setup":
                await db.leagues.update_one(
                    {"_id": league_id},
                    {"$set": {"status": "ready"}}
                )
                logger.info(f"League {league_id} is now ready with {current_members} members")
            
            return is_ready
            
        except Exception as e:
            logger.error(f"Failed to validate league readiness: {e}")
            return False

    @staticmethod
    async def resend_invitation(invitation_id: str, inviter_id: str) -> InvitationResponse:
        """
        Resend an existing invitation
        """
        try:
            invitation = await db.invitations.find_one({"_id": invitation_id})
            if not invitation:
                raise ValueError("Invitation not found")
            
            if invitation["inviter_id"] != inviter_id:
                raise ValueError("Not authorized to resend this invitation")
            
            if invitation["status"] != "pending":
                raise ValueError("Can only resend pending invitations")
            
            # Create new token and extend expiry
            new_token = create_magic_link_token(invitation["email"])
            new_expires_at = datetime.now(timezone.utc) + timedelta(hours=72)
            
            await db.invitations.update_one(
                {"_id": invitation_id},
                {
                    "$set": {
                        "token": new_token,
                        "expires_at": new_expires_at
                    }
                }
            )
            
            # Log/send new invitation link
            invitation_link = f"http://localhost:3000/invite?token={new_token}"
            logger.info(f"Resent invitation link for {invitation['email']}: {invitation_link}")
            print(f"\n📨 Resent Invitation Link for {invitation['email']}:")
            print(f"   {invitation_link}\n")
            
            # Return updated invitation
            updated_invitation = await db.invitations.find_one({"_id": invitation_id})
            return InvitationResponse(
                id=updated_invitation["_id"],
                league_id=updated_invitation["league_id"],
                inviter_id=updated_invitation["inviter_id"],
                email=updated_invitation["email"],
                status=InvitationStatus(updated_invitation["status"]),
                expires_at=updated_invitation["expires_at"],
                created_at=updated_invitation["created_at"],
                accepted_at=updated_invitation.get("accepted_at")
            )
            
        except Exception as e:
            logger.error(f"Failed to resend invitation: {e}")
            raise