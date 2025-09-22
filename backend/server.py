from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timezone

# Import our modules
from models import *
from database import db, initialize_database
from auth import (
    create_access_token, create_magic_link_token, verify_magic_link_token,
    send_magic_link_email, get_current_user, get_current_verified_user,
    require_league_access, require_commissioner_access, AccessControl
)

# Helper function to convert MongoDB document to response model
def convert_doc_to_response(doc, response_class):
    """Convert MongoDB document to Pydantic response model"""
    if not doc:
        return None
    
    # Create a copy and map _id to id
    converted = doc.copy()
    if '_id' in converted:
        converted['id'] = converted.pop('_id')
    
    return response_class(**converted)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(title="UCL Auction API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await initialize_database()
    logger.info("UCL Auction API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("UCL Auction API shutting down")

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

# Authentication Routes
@api_router.post("/auth/magic-link")
async def request_magic_link(request: MagicLinkRequest):
    """Request a magic link for email authentication"""
    # Check if user exists, if not create them
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        # Create new user
        new_user = User(
            email=request.email,
            display_name=request.email.split('@')[0],  # Default display name
            verified=False
        )
        user_dict = new_user.dict(by_alias=True)
        await db.users.insert_one(user_dict)
        logger.info(f"Created new user: {request.email}")
    
    # Create and send magic link
    token = create_magic_link_token(request.email)
    await send_magic_link_email(request.email, token)
    
    return {"message": "Magic link sent to your email"}

@api_router.post("/auth/verify", response_model=AuthResponse)
async def verify_magic_link(request: MagicLinkVerify):
    """Verify magic link token and return access token"""
    email = verify_magic_link_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Get user and mark as verified
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark user as verified
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"verified": True}}
    )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["_id"]})
    
    # Create user response with proper field mapping
    user_response = UserResponse(
        id=user["_id"],
        email=user["email"],
        display_name=user["display_name"],
        verified=True,
        created_at=user["created_at"]
    )
    
    return AuthResponse(
        access_token=access_token,
        user=user_response
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user info"""
    return current_user

# User Routes
@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: UserResponse = Depends(get_current_verified_user)):
    """Get user by ID"""
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user["_id"],
        email=user["email"],
        display_name=user["display_name"],
        verified=user["verified"],
        created_at=user["created_at"]
    )

@api_router.put("/users/me", response_model=UserResponse)
async def update_profile(
    display_name: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Update current user's profile"""
    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"display_name": display_name}}
    )
    
    updated_user = await db.users.find_one({"_id": current_user.id})
    return UserResponse(
        id=updated_user["_id"],
        email=updated_user["email"],
        display_name=updated_user["display_name"],
        verified=updated_user["verified"],
        created_at=updated_user["created_at"]
    )

# League Routes
@api_router.post("/leagues", response_model=LeagueResponse)
async def create_league(
    league_data: LeagueCreate,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Create a new league"""
    # Create league
    league = League(
        name=league_data.name,
        season=league_data.season,
        commissioner_id=current_user.id,
        settings=league_data.settings or LeagueSettings()
    )
    league_dict = league.dict(by_alias=True)
    await db.leagues.insert_one(league_dict)
    
    # Add commissioner membership
    membership = Membership(
        league_id=league.id,
        user_id=current_user.id,
        role=MembershipRole.COMMISSIONER
    )
    membership_dict = membership.dict(by_alias=True)
    await db.memberships.insert_one(membership_dict)
    
    # Create scoring rules
    scoring_rules = ScoringRules(league_id=league.id)
    scoring_dict = scoring_rules.dict(by_alias=True)
    await db.scoring_rules.insert_one(scoring_dict)
    
    logger.info(f"Created league {league.id} by user {current_user.id}")
    
    return convert_doc_to_response(league_dict, LeagueResponse)

@api_router.get("/leagues", response_model=List[LeagueResponse])
async def get_my_leagues(current_user: UserResponse = Depends(get_current_verified_user)):
    """Get leagues where current user is a member"""
    memberships = await db.memberships.find({"user_id": current_user.id}).to_list(length=None)
    league_ids = [m["league_id"] for m in memberships]
    
    leagues = await db.leagues.find({"_id": {"$in": league_ids}}).to_list(length=None)
    return [LeagueResponse(**league) for league in leagues]

@api_router.get("/leagues/{league_id}", response_model=LeagueResponse)
async def get_league(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get league details"""
    await require_league_access(current_user.id, league_id)
    
    league = await db.leagues.find_one({"_id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    return LeagueResponse(**league)

@api_router.post("/leagues/{league_id}/join")
async def join_league(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Join a league as a manager"""
    # Check if league exists
    league = await db.leagues.find_one({"_id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check if already a member
    existing_membership = await db.memberships.find_one({
        "league_id": league_id,
        "user_id": current_user.id
    })
    if existing_membership:
        raise HTTPException(status_code=400, detail="Already a member of this league")
    
    # Add membership
    membership = Membership(
        league_id=league_id,
        user_id=current_user.id,
        role=MembershipRole.MANAGER
    )
    membership_dict = membership.dict(by_alias=True)
    await db.memberships.insert_one(membership_dict)
    
    # Create roster
    roster = Roster(
        league_id=league_id,
        user_id=current_user.id,
        budget_start=league["settings"]["budget_per_manager"],
        budget_remaining=league["settings"]["budget_per_manager"],
        club_slots=league["settings"]["club_slots_per_manager"]
    )
    roster_dict = roster.dict(by_alias=True)
    await db.rosters.insert_one(roster_dict)
    
    logger.info(f"User {current_user.id} joined league {league_id}")
    
    return {"message": "Successfully joined league"}

@api_router.get("/leagues/{league_id}/members", response_model=List[dict])
async def get_league_members(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get league members with their roles"""
    await require_league_access(current_user.id, league_id)
    
    # Get memberships with user details
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
            "display_name": "$user.display_name",
            "email": "$user.email"
        }}
    ]
    
    members = await db.memberships.aggregate(pipeline).to_list(length=None)
    return members

# Club Routes (seed data)
@api_router.post("/clubs/seed")
async def seed_clubs(current_user: UserResponse = Depends(get_current_verified_user)):
    """Seed UCL clubs data"""
    # Sample UCL clubs
    clubs_data = [
        {"name": "Real Madrid", "short_name": "RMA", "country": "Spain", "ext_ref": "real_madrid"},
        {"name": "FC Barcelona", "short_name": "BAR", "country": "Spain", "ext_ref": "barcelona"},
        {"name": "Manchester City", "short_name": "MCI", "country": "England", "ext_ref": "man_city"},
        {"name": "Liverpool FC", "short_name": "LIV", "country": "England", "ext_ref": "liverpool"},
        {"name": "Bayern Munich", "short_name": "BAY", "country": "Germany", "ext_ref": "bayern"},
        {"name": "Paris Saint-Germain", "short_name": "PSG", "country": "France", "ext_ref": "psg"},
        {"name": "Chelsea FC", "short_name": "CHE", "country": "England", "ext_ref": "chelsea"},
        {"name": "Juventus", "short_name": "JUV", "country": "Italy", "ext_ref": "juventus"},
        {"name": "AC Milan", "short_name": "MIL", "country": "Italy", "ext_ref": "ac_milan"},
        {"name": "Inter Milan", "short_name": "INT", "country": "Italy", "ext_ref": "inter"},
        {"name": "Arsenal FC", "short_name": "ARS", "country": "England", "ext_ref": "arsenal"},
        {"name": "Manchester United", "short_name": "MUN", "country": "England", "ext_ref": "man_united"},
        {"name": "Atlético Madrid", "short_name": "ATM", "country": "Spain", "ext_ref": "atletico"},
        {"name": "Borussia Dortmund", "short_name": "BVB", "country": "Germany", "ext_ref": "dortmund"},
        {"name": "Napoli", "short_name": "NAP", "country": "Italy", "ext_ref": "napoli"},
        {"name": "Tottenham", "short_name": "TOT", "country": "England", "ext_ref": "tottenham"}
    ]
    
    clubs = []
    for club_data in clubs_data:
        # Check if club already exists
        existing = await db.clubs.find_one({"ext_ref": club_data["ext_ref"]})
        if not existing:
            club = Club(**club_data)
            club_dict = club.dict(by_alias=True)
            clubs.append(club_dict)
    
    if clubs:
        await db.clubs.insert_many(clubs)
        logger.info(f"Seeded {len(clubs)} clubs")
    
    return {"message": f"Seeded {len(clubs)} clubs"}

@api_router.get("/clubs", response_model=List[ClubResponse])
async def get_clubs():
    """Get all clubs"""
    clubs = await db.clubs.find().to_list(length=None)
    return [ClubResponse(**club) for club in clubs]

# Include the router in the main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)