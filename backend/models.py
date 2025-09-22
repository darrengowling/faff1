from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Literal
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

class LeagueSettings(BaseModel):
    budget_per_manager: int = 100
    min_increment: int = 1
    club_slots_per_manager: int = 3
    anti_snipe_seconds: int = 30
    bid_timer_seconds: int = 60
    max_managers: int = 8
    min_managers: int = 4
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
    SOLD = "sold"
    UNSOLD = "unsold"

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