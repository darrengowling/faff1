from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Literal, Tuple
from datetime import datetime, timezone
from enum import Enum
import uuid

# Utility function for UUID generation
def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

# User Models
class User(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    email: EmailStr
    display_name: str
    created_at: datetime = Field(default_factory=utc_now)
    verified: bool = False
    
    class Config:
        populate_by_name = True

class UserCreate(BaseModel):
    email: EmailStr
    display_name: str

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    verified: bool
    created_at: datetime

# Enhanced League Models with Commissioner Controls
class ScoringRulePoints(BaseModel):
    club_goal: int = 1
    club_win: int = 3
    club_draw: int = 1

class LeagueSize(BaseModel):
    min: int = Field(ge=2, le=8, description="Minimum number of managers")
    max: int = Field(ge=2, le=8, description="Maximum number of managers")
    
    @validator('max')
    def max_must_be_gte_min(cls, v, values):
        if 'min' in values and v < values['min']:
            raise ValueError('max must be greater than or equal to min')
        return v

class LeagueSettings(BaseModel):
    budget_per_manager: int = Field(100, ge=50, le=500, description="Budget per manager (50-500M)")
    min_increment: int = Field(1, ge=1, description="Minimum bid increment")
    club_slots_per_manager: int = Field(3, ge=1, le=10, description="Club slots per manager (1-10)")
    anti_snipe_seconds: int = Field(30, ge=0, description="Anti-snipe timer extension")
    bid_timer_seconds: int = Field(60, ge=30, description="Default bid timer duration")
    league_size: LeagueSize = Field(default_factory=lambda: LeagueSize(min=4, max=8))
    scoring_rules: ScoringRulePoints = Field(default_factory=ScoringRulePoints)

class League(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    name: str
    competition: str = "UCL"
    season: str = "2025-26"
    commissioner_id: str
    settings: LeagueSettings = Field(default_factory=LeagueSettings)
    status: str = "setup"  # setup, ready, active, completed
    member_count: int = 1  # Commissioner is always first member
    created_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class LeagueCreate(BaseModel):
    name: str
    season: Optional[str] = "2025-26"
    settings: Optional[LeagueSettings] = None

class LeagueResponse(BaseModel):
    id: str
    name: str
    competition: str
    season: str
    commissioner_id: str
    settings: LeagueSettings
    status: str
    member_count: int
    created_at: datetime

# Invitation Models
class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class Invitation(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    inviter_id: str  # Commissioner who sent the invite
    email: EmailStr
    token: str
    status: InvitationStatus = InvitationStatus.PENDING
    expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)
    accepted_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True

class InvitationCreate(BaseModel):
    league_id: str
    email: EmailStr

class InvitationEmailRequest(BaseModel):
    email: EmailStr

class InvitationResponse(BaseModel):
    id: str
    league_id: str
    inviter_id: str
    email: str
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime
    accepted_at: Optional[datetime]

class InvitationAccept(BaseModel):
    token: str

# Membership Models
class MembershipRole(str, Enum):
    COMMISSIONER = "commissioner"
    MANAGER = "manager"

class MembershipStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"

class Membership(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    user_id: str
    role: MembershipRole
    status: MembershipStatus = MembershipStatus.ACTIVE
    joined_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class MembershipCreate(BaseModel):
    league_id: str
    user_id: str
    role: MembershipRole

class MembershipResponse(BaseModel):
    id: str
    league_id: str
    user_id: str
    role: MembershipRole
    status: MembershipStatus
    joined_at: datetime

# Enhanced League Member Response with User Details
class LeagueMemberResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: MembershipRole
    status: MembershipStatus
    joined_at: datetime

# Club Models
class Club(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    name: str
    short_name: str
    country: str
    ext_ref: str  # External reference (e.g., UEFA ID)
    
    class Config:
        populate_by_name = True

class ClubCreate(BaseModel):
    name: str
    short_name: str
    country: str
    ext_ref: str

class ClubResponse(BaseModel):
    id: str
    name: str
    short_name: str
    country: str
    ext_ref: str

# Auction Models
class AuctionStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    PAUSED = "paused"
    COMPLETED = "completed"

class Auction(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    status: AuctionStatus = AuctionStatus.SCHEDULED
    nomination_order: List[str] = []  # List of user IDs
    budget_per_manager: int = 100
    min_increment: int = 1
    anti_snipe_seconds: int = 30
    bid_timer_seconds: int = 60
    created_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class AuctionCreate(BaseModel):
    league_id: str
    nomination_order: List[str]
    budget_per_manager: Optional[int] = 100
    min_increment: Optional[int] = 1
    anti_snipe_seconds: Optional[int] = 30
    bid_timer_seconds: Optional[int] = 60

class AuctionResponse(BaseModel):
    id: str
    league_id: str
    status: AuctionStatus
    nomination_order: List[str]
    budget_per_manager: int
    min_increment: int
    anti_snipe_seconds: int
    bid_timer_seconds: int
    created_at: datetime

# Lot Models
class LotStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    PRE_CLOSED = "pre_closed"  # New: 10s undo window
    SOLD = "sold"
    UNSOLD = "unsold"

class UndoableAction(BaseModel):
    """Model for tracking undoable actions during lot closing"""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lot_id: str
    action_type: str  # "lot_close"
    commissioner_id: str
    original_state: Dict = {}
    new_state: Dict = {}
    undo_deadline: datetime
    is_undone: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Lot(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    auction_id: str
    club_id: str
    status: LotStatus = LotStatus.PENDING
    nominated_by: Optional[str] = None
    order_index: int
    current_bid: int = 0
    top_bidder_id: Optional[str] = None
    timer_ends_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class LotCreate(BaseModel):
    auction_id: str
    club_id: str
    nominated_by: Optional[str] = None
    order_index: int

class LotResponse(BaseModel):
    id: str
    auction_id: str
    club_id: str
    status: LotStatus
    nominated_by: Optional[str]
    order_index: int
    current_bid: int
    top_bidder_id: Optional[str]
    timer_ends_at: Optional[datetime]
    created_at: datetime

# Bid Models
class Bid(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    lot_id: str
    bidder_id: str
    amount: int
    created_at: datetime = Field(default_factory=utc_now)
    server_ts: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class BidCreate(BaseModel):
    lot_id: str
    amount: int

class BidResponse(BaseModel):
    id: str
    lot_id: str
    bidder_id: str
    amount: int
    created_at: datetime
    server_ts: datetime

# Roster Models
class Roster(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    user_id: str
    budget_start: int = 100
    budget_remaining: int = 100
    club_slots: int = 3
    
    class Config:
        populate_by_name = True

class RosterCreate(BaseModel):
    league_id: str
    user_id: str
    budget_start: Optional[int] = 100
    club_slots: Optional[int] = 3

class RosterResponse(BaseModel):
    id: str
    league_id: str
    user_id: str
    budget_start: int
    budget_remaining: int
    club_slots: int

# Roster Club Models
class RosterClub(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    roster_id: str
    league_id: str
    user_id: str
    club_id: str
    price: int
    acquired_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class RosterClubCreate(BaseModel):
    roster_id: str
    league_id: str
    user_id: str
    club_id: str
    price: int

class RosterClubResponse(BaseModel):
    id: str
    roster_id: str
    league_id: str
    user_id: str
    club_id: str
    price: int
    acquired_at: datetime

# Scoring Rules Models
class ScoringRules(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    rules: ScoringRulePoints = Field(default_factory=ScoringRulePoints)
    
    class Config:
        populate_by_name = True

class ScoringRulesCreate(BaseModel):
    league_id: str
    rules: Optional[ScoringRulePoints] = None

class ScoringRulesResponse(BaseModel):
    id: str
    league_id: str
    rules: ScoringRulePoints

# Fixture Models
class Fixture(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    season: str
    match_id: str  # External match ID
    date: datetime
    home_ext: str  # Home team external reference
    away_ext: str  # Away team external reference
    status: str = "scheduled"
    
    class Config:
        populate_by_name = True

class FixtureCreate(BaseModel):
    league_id: str
    season: str
    match_id: str
    date: datetime
    home_ext: str
    away_ext: str
    status: Optional[str] = "scheduled"

class FixtureResponse(BaseModel):
    id: str
    league_id: str
    season: str
    match_id: str
    date: datetime
    home_ext: str
    away_ext: str
    status: str

# Result Ingest Models
class ResultIngest(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    match_id: str
    home_ext: str
    away_ext: str
    home_goals: int
    away_goals: int
    kicked_off_at: datetime
    status: str = "final"
    received_at: datetime = Field(default_factory=utc_now)
    processed: bool = False
    
    class Config:
        populate_by_name = True

class ResultIngestCreate(BaseModel):
    league_id: str
    match_id: str
    season: str
    home_ext: str
    away_ext: str
    home_goals: int
    away_goals: int
    kicked_off_at: datetime
    status: Optional[str] = "final"

class ResultIngestResponse(BaseModel):
    id: str
    league_id: str
    match_id: str
    home_ext: str
    away_ext: str
    home_goals: int
    away_goals: int
    kicked_off_at: datetime
    status: str
    received_at: datetime
    processed: bool

# Settlement Models
class Settlement(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    match_id: str
    processed_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class SettlementCreate(BaseModel):
    league_id: str
    match_id: str

class SettlementResponse(BaseModel):
    id: str
    league_id: str
    match_id: str
    processed_at: datetime

# Weekly Points Models
class WeeklyPointsBucket(BaseModel):
    type: str = "matchday"
    value: int

class WeeklyPoints(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    user_id: str
    bucket: WeeklyPointsBucket
    points_delta: int
    match_id: str
    created_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class WeeklyPointsCreate(BaseModel):
    league_id: str
    user_id: str
    bucket: WeeklyPointsBucket
    points_delta: int
    match_id: str

class WeeklyPointsResponse(BaseModel):
    id: str
    league_id: str
    user_id: str
    bucket: WeeklyPointsBucket
    points_delta: int
    match_id: str
    created_at: datetime

# Authentication Models
class MagicLinkRequest(BaseModel):
    email: EmailStr

class MagicLinkVerify(BaseModel):
    token: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Competition Profile Models
class CompetitionDefaults(BaseModel):
    club_slots: int = Field(ge=1, le=10)
    budget_per_manager: int = Field(ge=50, le=500)
    league_size: LeagueSize
    min_increment: int = Field(ge=1)
    anti_snipe_seconds: int = Field(ge=0)
    bid_timer_seconds: int = Field(ge=30)
    scoring_rules: ScoringRulePoints

class CompetitionProfile(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    competition: str
    short_name: str
    defaults: CompetitionDefaults
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class CompetitionProfileResponse(BaseModel):
    id: str
    competition: str
    short_name: str
    defaults: CompetitionDefaults
    description: Optional[str] = None

# Admin & Audit Models
class AdminAction:
    """Enumeration of admin actions for audit logging"""
    # League Management
    UPDATE_LEAGUE_SETTINGS = "update_league_settings"
    APPROVE_MEMBER = "approve_member" 
    KICK_MEMBER = "kick_member"
    
    # Auction Management
    START_AUCTION = "start_auction"
    PAUSE_AUCTION = "pause_auction"
    RESUME_AUCTION = "resume_auction"
    REORDER_NOMINATIONS = "reorder_nominations"
    FORCE_LOT_CLOSE = "force_lot_close"
    
    # Emergency Actions
    EMERGENCY_STOP = "emergency_stop"
    RESET_AUCTION = "reset_auction"

class AdminLog(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    league_id: str
    actor_id: str  # Commissioner who performed the action
    action: str    # AdminAction value
    before: Optional[Dict] = None  # State before action
    after: Optional[Dict] = None   # State after action
    metadata: Optional[Dict] = None  # Additional context
    created_at: datetime = Field(default_factory=utc_now)
    
    class Config:
        populate_by_name = True

class AdminLogCreate(BaseModel):
    league_id: str
    actor_id: str
    action: str
    before: Optional[Dict] = None
    after: Optional[Dict] = None
    metadata: Optional[Dict] = None

class AdminLogResponse(BaseModel):
    id: str
    league_id: str
    actor_id: str
    action: str
    before: Optional[Dict] = None
    after: Optional[Dict] = None
    metadata: Optional[Dict] = None
    created_at: datetime

# Admin Request Models
class LeagueSettingsUpdate(BaseModel):
    budget_per_manager: Optional[int] = Field(None, ge=50, le=500, description="Budget per manager (50-500M)")
    min_increment: Optional[int] = Field(None, ge=1, description="Minimum bid increment")
    club_slots_per_manager: Optional[int] = Field(None, ge=1, le=10, description="Club slots per manager (1-10)")
    anti_snipe_seconds: Optional[int] = Field(None, ge=0, description="Anti-snipe timer extension")
    bid_timer_seconds: Optional[int] = Field(None, ge=30, description="Default bid timer duration")
    league_size: Optional[LeagueSize] = Field(None, description="League size constraints")
    scoring_rules: Optional[ScoringRulePoints] = None

class MemberAction(BaseModel):
    member_id: str
    action: str  # "approve", "kick", "promote", "demote"

class NominationReorder(BaseModel):
    auction_id: str
    new_order: List[str]  # List of club IDs in new order

class BidAuditRequest(BaseModel):
    auction_id: Optional[str] = None
    league_id: Optional[str] = None
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None