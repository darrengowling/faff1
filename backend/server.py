from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import socketio
from pathlib import Path
from typing import List
from datetime import datetime, timezone, timedelta

# Import our modules
from models import *
from database import db, initialize_database
from league_service import LeagueService
from auth import (
    create_access_token, create_magic_link_token, verify_magic_link_token,
    send_magic_link_email, get_current_user, get_current_verified_user,
    require_league_access, require_commissioner_access, AccessControl
)

# Import auction, scoring, aggregation, admin, and competition modules
from auction_engine import initialize_auction_engine, get_auction_engine
from scoring_service import ScoringService, get_scoring_worker
from aggregation_service import AggregationService
from admin_service import AdminService
from audit_service import AuditService
from lot_closing_service import LotClosingService
from competition_service import CompetitionService
from time_provider import time_provider, now, now_ms, is_test_mode
from database_indexes import initialize_scoring_indexes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Test environment overrides for deterministic testing  
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
DEFAULT_BID_TIMER = 8 if TEST_MODE else 60
DEFAULT_ANTI_SNIPE = 3 if TEST_MODE else 30
BID_TIMER_SECONDS = int(os.getenv("BID_TIMER_SECONDS", str(DEFAULT_BID_TIMER)))
ANTI_SNIPE_SECONDS = int(os.getenv("ANTI_SNIPE_SECONDS", str(DEFAULT_ANTI_SNIPE)))

# Legacy compatibility
IS_TEST_MODE = os.getenv("PLAYWRIGHT_TEST") == "true" or TEST_MODE

# Socket.IO ASGI wrapper configuration
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
SOCKET_PATH = os.getenv("SOCKET_PATH", "/api/socketio")
SOCKETIO_PATH_INTERNAL = SOCKET_PATH.lstrip("/")  # "api/socketio"

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=[FRONTEND_ORIGIN])

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"Socket.IO client connected: {sid}")

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Socket.IO client disconnected: {sid}")

@sio.event
async def join_auction(sid, data):
    """Join auction room"""
    auction_id = data.get('auction_id')
    if auction_id:
        await sio.enter_room(sid, f"auction_{auction_id}")
        await sio.emit('joined', {'auction_id': auction_id}, to=sid)

# Create FastAPI app
fastapi_app = FastAPI(title="Friends of PIFA API", version="1.0.0")

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Custom middleware to handle /api/socketio/diag before Socket.IO intercepts it
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class SocketIODiagMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Intercept /api/socketio/diag requests before they reach Socket.IO
        if request.url.path == "/api/socketio/diag":
            socket_path = os.getenv('SOCKET_PATH', '/api/socketio')
            return JSONResponse({
                "ok": True,
                "path": socket_path,
                "now": datetime.now(timezone.utc).isoformat()
            })
        
        # Let other requests continue normally
        response = await call_next(request)
        return response

# Add the diagnostic middleware
fastapi_app.add_middleware(SocketIODiagMiddleware)

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

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup event to initialize database, auction engine, and scoring worker
@fastapi_app.on_event("startup")
async def startup_event():
    """Initialize all systems on startup"""
    await initialize_database()
    
    # Initialize scoring database indexes for data integrity
    await initialize_scoring_indexes()
    
    initialize_auction_engine(sio)  # Initialize with Socket.IO server
    
    # Start scoring worker in background
    scoring_worker = get_scoring_worker()
    # Note: In production, run scoring worker as separate process/container
    # asyncio.create_task(scoring_worker.start_continuous_processing())
    
    logger.info("Friends of PIFA API with Live Auction Engine and Scoring System started successfully")

@fastapi_app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    scoring_worker = get_scoring_worker()
    scoring_worker.stop()
    logger.info("Friends of PIFA API shutting down")

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

# Time sync endpoint for client drift correction
@api_router.get("/timez")
async def get_server_time():
    """Return current server time for client synchronization"""
    return {"now": datetime.now(timezone.utc).isoformat()}

# Authentication Routes
@api_router.post("/auth/magic-link")
async def request_magic_link(request: MagicLinkRequest):
    """Request a magic link for email authentication"""
    try:
        # Import email validator
        from email_validator import EmailValidator
        
        # Validate email format first - return 400 on invalid email
        if not request.email or not request.email.strip():
            raise HTTPException(
                status_code=400, 
                detail={
                    "code": "INVALID_EMAIL",
                    "message": "Email address is required"
                }
            )
        
        email = request.email.strip()
        if not EmailValidator.is_valid_email(email):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_EMAIL", 
                    "message": "Please enter a valid email address"
                }
            )
        
        # Check environment settings for TEST_MODE behavior
        auth_require_magic_link = os.getenv("AUTH_REQUIRE_MAGIC_LINK", "true").lower() == "true"
        
        # In TEST_MODE with AUTH_REQUIRE_MAGIC_LINK=false, suggest test login
        if not auth_require_magic_link and TEST_MODE:
            logger.warning(f"Magic link requested for {email} in TEST_MODE with AUTH_REQUIRE_MAGIC_LINK=false - consider using test login")
        
        # Check if user exists, if not create them
        user = await db.users.find_one({"email": email})
        
        if not user:
            # Create new user
            new_user = User(
                email=email,
                display_name=email.split('@')[0],  # Default display name
                verified=False
            )
            user_dict = new_user.dict(by_alias=True)
            await db.users.insert_one(user_dict)
            logger.info(f"Created new user: {email}")
        
        # Create and send magic link
        token = create_magic_link_token(email)
        
        # In TEST_MODE, skip actual email sending if configured
        if not TEST_MODE:
            await send_magic_link_email(email, token)
        else:
            logger.info(f"TEST_MODE: Skipping email send for magic link to {email}")
        
        # For development mode, return the magic link in the response
        is_development = os.environ.get('NODE_ENV', 'development') == 'development' or not os.environ.get('SMTP_SERVER')
        response = {"message": "Magic link sent to your email"}
        
        if is_development or TEST_MODE:
            frontend_url = os.getenv("FRONTEND_URL", "https://auction-league.preview.emergentagent.com")
            magic_link = f"{frontend_url}/auth/verify?token={token}"
            response["dev_magic_link"] = magic_link
            response["message"] = "Magic link generated! (Development Mode - Check below)"
        
        return response
        
    except HTTPException:
        # Re-raise HTTPExceptions (400 errors) as-is
        raise
    except Exception as e:
        # Log unexpected errors but return 400 instead of 500 to prevent crashes
        logger.error(f"Magic link request failed for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MAGIC_LINK_FAILED",
                "message": "Unable to process magic link request. Please try again."
            }
        )

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

# Test-only login endpoint (DO NOT USE IN PRODUCTION)
@api_router.post("/auth/test-login")
async def test_login(request: dict):
    """
    TEST-ONLY LOGIN ENDPOINT
    Creates session token for testing purposes without magic link verification.
    WARNING: Only enabled when ALLOW_TEST_LOGIN=true environment variable is set.
    """
    # Check if test login is allowed
    allow_test_login = os.getenv("ALLOW_TEST_LOGIN", "false").lower() == "true"
    
    if not allow_test_login:
        logger.warning("⚠️  TEST LOGIN ATTEMPTED BUT DISABLED - /auth/test-login endpoint called but ALLOW_TEST_LOGIN=false")
        raise HTTPException(
            status_code=403, 
            detail="Test login endpoint is disabled. Set ALLOW_TEST_LOGIN=true to enable."
        )
    
    # Log warning about test login usage
    logger.warning("🧪 TEST LOGIN USED - /auth/test-login endpoint called for email: %s", request.get('email', 'unknown'))
    
    # Validate request
    email = request.get('email')
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if user exists, if not create them
    user = await db.users.find_one({"email": email})
    
    if not user:
        # Create new user for testing
        new_user = User(
            email=email,
            display_name=email.split('@')[0],  # Default display name
            verified=True  # Auto-verify for test users
        )
        user_dict = new_user.dict(by_alias=True)
        await db.users.insert_one(user_dict)
        user = user_dict
        logger.info("🧪 TEST USER CREATED: %s", email)
    else:
        # Update existing user to be verified for testing
        await db.users.update_one(
            {"_id": user["_id"]}, 
            {"$set": {"verified": True}}
        )
        user["verified"] = True  # Update local user object
        logger.info("🧪 TEST USER VERIFIED: %s", email)
    
    # Create access token
    access_token = create_access_token(data={"sub": user["_id"]})
    
    # Create user response (user["verified"] is now guaranteed to be True)
    user_response = UserResponse(
        id=user["_id"],
        email=user["email"],
        display_name=user["display_name"],
        verified=user["verified"],  # Use actual database value (now True)
        created_at=user["created_at"]
    )
    
    return {
        "access_token": access_token,
        "user": user_response,
        "message": "Test login successful (TEST MODE ONLY)"
    }

# Test-only time control endpoints (TEST_MODE only)
@api_router.post("/test/time/set")
async def set_test_time(request: dict):
    """
    TEST-ONLY TIME CONTROL
    Set the current time for deterministic testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Time control endpoints only available in TEST_MODE"
        )
    
    if "nowMs" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'nowMs' field"
        )
    
    now_ms = request["nowMs"]
    if not isinstance(now_ms, int) or now_ms < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'nowMs' must be a positive integer"
        )
    
    time_provider.set_time_ms(now_ms)
    current_time = time_provider.now()
    
    logger.info("🕐 TEST TIME SET: %s (%d ms)", current_time.isoformat(), now_ms)
    
    return {
        "message": "Test time set successfully",
        "currentTimeMs": now_ms,
        "currentTime": current_time.isoformat()
    }

@api_router.post("/test/time/advance")
async def advance_test_time(request: dict):
    """
    TEST-ONLY TIME CONTROL
    Advance the current time by specified milliseconds for deterministic testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Time control endpoints only available in TEST_MODE"
        )
    
    if "ms" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'ms' field"
        )
    
    delta_ms = request["ms"]
    if not isinstance(delta_ms, int) or delta_ms < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'ms' must be a positive integer"
        )
    
    new_time_ms = time_provider.advance_time_ms(delta_ms)
    current_time = time_provider.now()
    
    logger.info("🕐 TEST TIME ADVANCED: +%d ms -> %s (%d ms)", 
               delta_ms, current_time.isoformat(), new_time_ms)
    
    return {
        "message": f"Test time advanced by {delta_ms}ms",
        "currentTimeMs": new_time_ms,
        "currentTime": current_time.isoformat(),
        "advancedMs": delta_ms
    }

# Test-only auction state management hooks (TEST_MODE only)
@api_router.post("/test/auction/create")
async def create_test_auction(request: dict):
    """
    TEST-ONLY AUCTION CREATION
    Creates a league directly without UI interaction for testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auction test hooks only available in TEST_MODE"
        )
    
    if "leagueSettings" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'leagueSettings' field"
        )
    
    settings = request["leagueSettings"]
    required_fields = ["name", "clubSlots", "budgetPerManager", "minManagers", "maxManagers"]
    for field in required_fields:
        if field not in settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Create league using LeagueService
    league_service = LeagueService()
    commissioner_id = "test-commissioner-" + str(int(now_ms()))
    
    # Create commissioner user if not exists
    commissioner = await db.users.find_one({"_id": commissioner_id})
    if not commissioner:
        commissioner_data = {
            "_id": commissioner_id,
            "email": f"commissioner-{int(now_ms())}@test.local",
            "display_name": "Test Commissioner",
            "verified": True,
            "created_at": now()
        }
        await db.users.insert_one(commissioner_data)
    
    # Create league data model (use valid timer values for model validation)
    league_create = LeagueCreate(
        name=settings["name"],
        season="2025-26",
        settings=LeagueSettings(
            budget_per_manager=settings["budgetPerManager"],
            club_slots_per_manager=settings["clubSlots"],
            bid_timer_seconds=max(30, BID_TIMER_SECONDS),  # Ensure minimum 30 for validation
            anti_snipe_seconds=ANTI_SNIPE_SECONDS,
            league_size=LeagueSize(
                min=settings["minManagers"],
                max=settings["maxManagers"]
            )
        )
    )
    
    league_response = await league_service.create_league_with_setup(league_create, commissioner_id)
    league_id = league_response.id
    
    # For testing, automatically set league to ready status
    await db.leagues.update_one(
        {"_id": league_id},
        {"$set": {"status": "ready"}}
    )
    
    logger.info("🧪 TEST LEAGUE CREATED: %s (ID: %s)", settings["name"], league_id)
    
    return {
        "leagueId": league_id,
        "message": "Test league created successfully",
        "settings": settings
    }

@api_router.post("/test/auction/add-member")
async def add_test_member(request: dict):
    """
    TEST-ONLY MEMBER ADDITION
    Adds and auto-verifies a member to a league for testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auction test hooks only available in TEST_MODE"
        )
    
    if "leagueId" not in request or "email" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'leagueId' or 'email' field"
        )
    
    league_id = request["leagueId"]
    email = request["email"]
    
    # Create or verify user
    user = await db.users.find_one({"email": email})
    if not user:
        user_data = {
            "_id": f"test-user-{email}-{int(now_ms())}",
            "email": email,
            "display_name": email.split("@")[0].title(),
            "verified": True,
            "created_at": now()
        }
        await db.users.insert_one(user_data)
        user = user_data
        logger.info("🧪 TEST USER CREATED: %s", email)
    else:
        # Ensure user is verified for testing
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"verified": True}})
        logger.info("🧪 TEST USER VERIFIED: %s", email)
    
    # Add user to league
    league = await db.leagues.find_one({"_id": league_id})
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Add to league members if not already added
    members = league.get("members", [])
    if user["_id"] not in [m.get("user_id") for m in members]:
        member_data = {
            "user_id": user["_id"],
            "email": email,
            "display_name": user["display_name"],
            "joined_at": now().isoformat(),
            "status": "active"
        }
        members.append(member_data)
        
        await db.leagues.update_one(
            {"_id": league_id},
            {"$set": {"members": members}}
        )
        logger.info("🧪 TEST MEMBER ADDED: %s to %s", email, league_id)
    
    return {
        "message": f"Test member {email} added to league {league_id}",
        "userId": user["_id"],
        "leagueId": league_id
    }

@api_router.post("/test/auction/start")
async def start_test_auction(request: dict):
    """
    TEST-ONLY AUCTION START
    Starts an auction directly without UI interaction for testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auction test hooks only available in TEST_MODE"
        )
    
    if "leagueId" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'leagueId' field"
        )
    
    league_id = request["leagueId"]
    
    # Get league
    league = await db.leagues.find_one({"_id": league_id})
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found"
        )
    
    # Get commissioner_id from league
    commissioner_id = league["commissioner_id"]
    
    # Start auction using auction engine
    auction_engine = get_auction_engine()
    result = await auction_engine.start_auction(league_id, commissioner_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start auction: {result.get('error', 'Unknown error')}"
        )
    
    logger.info("🧪 TEST AUCTION STARTED: %s", league_id)
    
    return {
        "message": f"Test auction started for league {league_id}",
        "leagueId": league_id,
        "auctionId": result.get("auction_id")
    }

@api_router.post("/test/auction/nominate")
async def nominate_test_asset(request: dict):
    """
    TEST-ONLY ASSET NOMINATION
    Nominates an asset directly without UI interaction for testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auction test hooks only available in TEST_MODE"
        )
    
    if "leagueId" not in request or "extRef" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'leagueId' or 'extRef' field"
        )
    
    league_id = request["leagueId"]
    ext_ref = request["extRef"]
    
    # Get auction engine and nominate asset
    auction_engine = get_auction_engine()
    result = await auction_engine.nominate_asset(league_id, ext_ref)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to nominate asset: {result.get('error', 'Unknown error')}"
        )
    
    logger.info("🧪 TEST ASSET NOMINATED: %s in %s", ext_ref, league_id)
    
    return {
        "message": f"Test asset {ext_ref} nominated in league {league_id}",
        "leagueId": league_id,
        "extRef": ext_ref
    }

@api_router.post("/test/auction/bid")
async def place_test_bid(request: dict):
    """
    TEST-ONLY BID PLACEMENT
    Places a bid directly without UI interaction for testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auction test hooks only available in TEST_MODE"
        )
    
    required_fields = ["leagueId", "email", "amount"]
    for field in required_fields:
        if field not in request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    league_id = request["leagueId"]
    email = request["email"]
    amount = request["amount"]
    
    # Get user
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Place bid using auction engine
    auction_engine = get_auction_engine()
    result = await auction_engine.place_bid(league_id, user["_id"], amount)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to place bid: {result.get('error', 'Unknown error')}"
        )
    
    logger.info("🧪 TEST BID PLACED: %s bid %d in %s", email, amount, league_id)
    
    return {
        "message": f"Test bid of {amount} placed by {email} in league {league_id}",
        "leagueId": league_id,
        "email": email,
        "amount": amount,
        "bidId": result.get("bid_id")
    }

# Test-only socket management hooks (TEST_MODE only)
@api_router.post("/test/sockets/drop")
async def drop_test_socket(request: dict):
    """
    TEST-ONLY SOCKET DISCONNECTION
    Force disconnects a user's socket for reconnection testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Socket test hooks only available in TEST_MODE"
        )
    
    if "email" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'email' field"
        )
    
    email = request["email"]
    
    # Get user
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Find and disconnect user's socket
    user_id = user["_id"]
    disconnected_count = 0
    
    # Emit a disconnect event to force client reconnection
    # This is a safer approach than directly manipulating socket.io internals
    try:
        await sio.emit('force_disconnect', {
            'reason': 'test_disconnect',
            'message': 'Socket disconnected for testing',
            'user_id': user_id
        }, room=f'user_{user_id}')
        disconnected_count = 1  # Assume success for testing
    except Exception as e:
        logger.warning(f"Could not emit disconnect to user {user_id}: {e}")
        # Try alternative approach - emit to all connections in user's rooms
        try:
            await sio.emit('force_disconnect', {
                'reason': 'test_disconnect',
                'message': 'Socket disconnected for testing',
                'user_id': user_id
            })
            disconnected_count = 1
        except Exception as e2:
            logger.warning(f"Could not emit disconnect globally: {e2}")
            disconnected_count = 0
    
    logger.info("🧪 TEST SOCKET DROPPED: %s (%d connections)", email, disconnected_count)
    
    return {
        "message": f"Test socket dropped for user {email}",
        "email": email,
        "userId": user_id,
        "disconnectedConnections": disconnected_count
    }

# Test-only scoring management hooks (TEST_MODE only)
@api_router.post("/test/scoring/reset")
async def reset_test_scoring(request: dict):
    """
    TEST-ONLY SCORING RESET
    Clears weeklyPoints and settlements for a specific league for testing.
    Only enabled when TEST_MODE=true environment variable is set.
    """
    if not is_test_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scoring test hooks only available in TEST_MODE"
        )
    
    if "leagueId" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'leagueId' field"
        )
    
    league_id = request["leagueId"]
    
    # Clear weeklyPoints for the league
    weekly_points_result = await db.weeklyPoints.delete_many({"league_id": league_id})
    
    # Clear settlements for the league
    settlements_result = await db.settlements.delete_many({"league_id": league_id})
    
    # Clear result_ingest for the league
    result_ingest_result = await db.result_ingest.delete_many({"league_id": league_id})
    
    logger.info("🧪 TEST SCORING RESET: %s (weeklyPoints: %d, settlements: %d, result_ingest: %d)", 
               league_id, 
               weekly_points_result.deleted_count,
               settlements_result.deleted_count,
               result_ingest_result.deleted_count)
    
    return {
        "message": f"Test scoring data cleared for league {league_id}",
        "leagueId": league_id,
        "deletedCounts": {
            "weeklyPoints": weekly_points_result.deleted_count,
            "settlements": settlements_result.deleted_count,
            "resultIngest": result_ingest_result.deleted_count
        }
    }

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
    user_update: dict,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Update current user's profile"""
    # Extract display_name from the request
    display_name = user_update.get('display_name')
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name is required")
    
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

# Enhanced League Routes with Commissioner Controls
@api_router.post("/leagues", response_model=LeagueResponse, status_code=201)
async def create_league(
    league_data: LeagueCreate,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Create a new league with comprehensive setup - returns 201 on success"""
    try:
        league_response = await LeagueService.create_league_with_setup(league_data, current_user.id)
        logger.info(f"League {league_response.id} created successfully for user {current_user.id}")
        return league_response
    except Exception as e:
        logger.error(f"League creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/leagues", response_model=List[LeagueResponse])
async def get_my_leagues(current_user: UserResponse = Depends(get_current_verified_user)):
    """Get leagues where current user is a member"""
    memberships = await db.memberships.find({"user_id": current_user.id}).to_list(length=None)
    league_ids = [m["league_id"] for m in memberships]
    
    leagues = await db.leagues.find({"_id": {"$in": league_ids}}).to_list(length=None)
    
    # Add missing fields for each league
    enriched_leagues = []
    for league in leagues:
        # Add status field (default to 'setup' if not present)
        if 'status' not in league:
            league['status'] = 'setup'
        
        # Add member_count by counting memberships
        member_count = await db.memberships.count_documents({"league_id": league["_id"]})
        league['member_count'] = member_count
        
        enriched_leagues.append(league)
    
    return [convert_doc_to_response(league, LeagueResponse) for league in enriched_leagues]

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
    
    return convert_doc_to_response(league, LeagueResponse)

@api_router.post("/leagues/{league_id}/invite")
async def invite_manager(
    league_id: str,
    invitation_data: InvitationEmailRequest,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Send invitation to join league as manager"""
    await require_commissioner_access(current_user.id, league_id)
    
    try:
        return await LeagueService.invite_manager(
            league_id=league_id,
            inviter_id=current_user.id,
            email=invitation_data.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Invitation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send invitation")

@api_router.get("/leagues/{league_id}/invitations", response_model=List[InvitationResponse])
async def get_league_invitations(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get all invitations for a league (commissioner only)"""
    await require_commissioner_access(current_user.id, league_id)
    
    try:
        return await LeagueService.get_league_invitations(league_id)
    except Exception as e:
        logger.error(f"Failed to get invitations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get invitations")

@api_router.post("/leagues/{league_id}/invitations/{invitation_id}/resend")
async def resend_invitation(
    league_id: str,
    invitation_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Resend league invitation"""
    await require_commissioner_access(current_user.id, league_id)
    
    try:
        return await LeagueService.resend_invitation(invitation_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resend invitation: {e}")
        raise HTTPException(status_code=500, detail="Failed to resend invitation")

@api_router.post("/leagues/{league_id}/join")
async def join_league_direct(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Join a league directly (for testing/manual joins)"""
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
    
    # Check league capacity
    if league["member_count"] >= league["settings"]["league_size"]["max"]:
        raise HTTPException(status_code=400, detail="League is full")
    
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
    
    # Update league member count
    await db.leagues.update_one(
        {"_id": league_id},
        {"$inc": {"member_count": 1}}
    )
    
    # Check if league is now ready
    await LeagueService.validate_league_ready(league_id)
    
    logger.info(f"User {current_user.id} joined league {league_id}")
    
    return {"message": "Successfully joined league"}

@api_router.get("/leagues/{league_id}/members", response_model=List[LeagueMemberResponse])
async def get_league_members(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get league members with their details"""
    await require_league_access(current_user.id, league_id)
    
    try:
        return await LeagueService.get_league_members(league_id)
    except Exception as e:
        logger.error(f"Failed to get league members: {e}")
        raise HTTPException(status_code=500, detail="Failed to get league members")

@api_router.get("/leagues/{league_id}/status")
async def get_league_status(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get league readiness status"""
    await require_league_access(current_user.id, league_id)
    
    try:
        is_ready = await LeagueService.validate_league_ready(league_id)
        league = await db.leagues.find_one({"_id": league_id})
        
        return {
            "league_id": league_id,
            "status": league["status"],
            "member_count": league["member_count"],
            "min_members": league["settings"]["league_size"]["min"],
            "max_members": league["settings"]["league_size"]["max"],
            "is_ready": is_ready,
            "can_start_auction": is_ready and league["status"] == "ready"
        }
    except Exception as e:
        logger.error(f"Failed to get league status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get league status")

# Invitation Acceptance Route
@api_router.post("/invitations/accept", response_model=LeagueResponse)
async def accept_invitation(
    invitation_data: InvitationAccept,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Accept league invitation"""
    try:
        return await LeagueService.accept_invitation(invitation_data.token, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to accept invitation: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept invitation")

# Live Auction Routes
@api_router.post("/auction/{auction_id}/start")
async def start_auction(
    auction_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Start live auction (commissioner only)"""
    try:
        engine = get_auction_engine()
        success = await engine.start_auction(auction_id, current_user.id)
        
        if success:
            return {"message": "Auction started successfully", "auction_id": auction_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to start auction")
    except ValueError as e:
        # Handle specific business logic errors with appropriate status codes
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        elif "not ready" in error_msg or "permission" in error_msg or "commissioner" in error_msg:
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start auction: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Lot closing endpoints
@api_router.post("/lots/{lot_id}/close")
async def initiate_lot_close(
    lot_id: str,
    request: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """Initiate lot closing with 10-second undo window"""
    try:
        # Verify user is commissioner
        lot = await db.lots.find_one({"_id": lot_id})
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")
        
        auction = await db.auctions.find_one({"_id": lot["auction_id"]})
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        # Check commissioner permission
        membership = await db.memberships.find_one({
            "league_id": auction["league_id"],
            "user_id": current_user.id,
            "role": "commissioner"
        })
        
        if not membership:
            raise HTTPException(status_code=403, detail="Only commissioners can close lots")
        
        # Initiate closing
        forced = request.get("forced", False)
        reason = request.get("reason", "Commissioner closed lot")
        
        success, message, action_id = await LotClosingService.initiate_lot_close(
            lot_id, current_user.id, forced, reason
        )
        
        if success:
            return {
                "success": True,
                "message": message,
                "action_id": action_id,
                "undo_deadline": (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in lot close endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/lots/undo/{action_id}")
async def undo_lot_close(
    action_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Undo lot closing within undo window"""
    try:
        # Get the action to verify permissions
        action_doc = await db.undoable_actions.find_one({"action_id": action_id})
        if not action_doc:
            raise HTTPException(status_code=404, detail="Action not found")
        
        # Verify user is commissioner  
        lot = await db.lots.find_one({"_id": action_doc["lot_id"]})
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")
            
        auction = await db.auctions.find_one({"_id": lot["auction_id"]})
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        membership = await db.memberships.find_one({
            "league_id": auction["league_id"],
            "user_id": current_user.id,
            "role": "commissioner"
        })
        
        if not membership:
            raise HTTPException(status_code=403, detail="Only commissioners can undo lot closes")
        
        # Attempt undo
        success, message = await LotClosingService.undo_lot_close(action_id, current_user.id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in undo endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/lots/{lot_id}/undo-actions")
async def get_lot_undo_actions(
    lot_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get active undo actions for a lot"""
    try:
        # Verify access to lot
        lot = await db.lots.find_one({"_id": lot_id})
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")
            
        auction = await db.auctions.find_one({"_id": lot["auction_id"]})
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        # Check user has access to auction
        membership = await db.memberships.find_one({
            "league_id": auction["league_id"],
            "user_id": current_user.id,
            "status": "accepted"
        })
        
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get active undo actions
        actions = await LotClosingService.get_active_undo_actions(lot_id)
        
        return {"actions": actions}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in undo actions endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Place bid endpoint (existing endpoint)
@api_router.post("/auction/{auction_id}/bid")
async def place_bid_http(
    auction_id: str,
    bid_data: BidCreate,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Place bid via HTTP endpoint"""
    try:
        engine = get_auction_engine()
        result = await engine.place_bid(auction_id, bid_data.lot_id, current_user.id, bid_data.amount)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to place bid: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auction/{auction_id}/nominate")
async def nominate_club(
    auction_id: str,
    club_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Nominate club for auction"""
    try:
        engine = get_auction_engine()
        success = await engine.nominate_club(auction_id, current_user.id, club_id)
        
        if success:
            return {"message": "Club nominated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to nominate club")
    except Exception as e:
        logger.error(f"Failed to nominate club: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auction/{auction_id}/pause")
async def pause_auction(
    auction_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Pause auction (commissioner only)"""
    try:
        engine = get_auction_engine()
        success = await engine.pause_auction(auction_id, current_user.id)
        
        if success:
            return {"message": "Auction paused successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to pause auction")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to pause auction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auction/{auction_id}/resume")
async def resume_auction(
    auction_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Resume auction (commissioner only)"""
    try:
        engine = get_auction_engine()
        success = await engine.resume_auction(auction_id, current_user.id)
        
        if success:
            return {"message": "Auction resumed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to resume auction")
    except Exception as e:
        logger.error(f"Failed to resume auction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auction/{auction_id}/state")
async def get_auction_state(
    auction_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get current auction state"""
    try:
        engine = get_auction_engine()
        state = await engine.get_auction_state(auction_id)
        
        if state:
            return state
        else:
            raise HTTPException(status_code=404, detail="Auction not found or not active")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get auction state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Scoring and Results Routes
@api_router.post("/ingest/final_result")
async def ingest_final_result(result_data: ResultIngestCreate):
    """
    Ingest final match result for scoring (idempotent)
    Returns 200 with idempotent:true on duplicate submissions
    """
    try:
        # Check if result already exists (idempotent check)
        existing_result = await db.result_ingest.find_one({
            "league_id": result_data.league_id,
            "match_id": result_data.match_id
        })
        
        if existing_result:
            # Return idempotent response for duplicate
            logger.info(f"🔄 Idempotent result ingest: match {result_data.match_id} in league {result_data.league_id} already exists")
            return {
                "success": True,
                "message": "Result already ingested",
                "idempotent": True,
                "created": False,
                "match_id": result_data.match_id,
                "league_id": result_data.league_id
            }
        
        # Process new result
        result = await ScoringService.ingest_result(
            league_id=result_data.league_id,
            match_id=result_data.match_id,
            season=result_data.season,
            home_ext=result_data.home_ext,
            away_ext=result_data.away_ext,
            home_goals=result_data.home_goals,
            away_goals=result_data.away_goals,
            kicked_off_at=result_data.kicked_off_at,
            status=result_data.status or "final"
        )
        
        if result["success"]:
            # Add idempotent field to indicate this was a new ingestion
            result["idempotent"] = False
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/scoring/process")
async def process_pending_results(current_user: UserResponse = Depends(get_current_verified_user)):
    """Process pending results (manual trigger for testing)"""
    try:
        result = await ScoringService.process_pending_results()
        return result
    except Exception as e:
        logger.error(f"Failed to process results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/leagues/{league_id}/standings")
async def get_league_standings(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get league standings"""
    await require_league_access(current_user.id, league_id)
    
    try:
        standings = await ScoringService.get_league_standings(league_id)
        return {"league_id": league_id, "standings": standings}
    except Exception as e:
        logger.error(f"Failed to get standings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/leagues/{league_id}/user/{user_id}/history")
async def get_user_match_history(
    league_id: str,
    user_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get match history for a user"""
    await require_league_access(current_user.id, league_id)
    
    try:
        history = await ScoringService.get_user_match_history(league_id, user_id)
        return {"league_id": league_id, "user_id": user_id, "history": history}
    except Exception as e:
        logger.error(f"Failed to get match history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Club Routes (seed data)
@api_router.post("/clubs/seed")
async def seed_clubs(current_user: UserResponse = Depends(get_current_verified_user)):
    """Seed football clubs data"""
    # Sample football clubs
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
    return [convert_doc_to_response(club, ClubResponse) for club in clubs]

# Admin Routes (Commissioner-only)
@api_router.put("/admin/leagues/{league_id}/settings")
async def update_league_settings_admin(
    league_id: str,
    settings_update: LeagueSettingsUpdate,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Update league settings (commissioner only)"""
    try:
        success, message = await AdminService.update_league_settings(league_id, current_user.id, settings_update)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Failed to update league settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.patch("/leagues/{league_id}/settings")
async def patch_league_settings(
    league_id: str,
    settings_update: LeagueSettingsUpdate,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """PATCH league settings with partial updates (commissioner only)"""
    try:
        success, message = await AdminService.update_league_settings(league_id, current_user.id, settings_update)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Failed to update league settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/leagues/{league_id}/settings")
async def get_league_settings(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get league settings for centralized configuration"""
    try:
        # Verify user has access to this league
        membership = await db.memberships.find_one({
            "league_id": league_id,
            "user_id": current_user.id,
            "status": {"$in": ["accepted", "active"]}
        })
        if not membership:
            raise HTTPException(status_code=403, detail="Not a member of this league")
        
        # Get league data
        league = await db.leagues.find_one({"_id": league_id})
        if not league:
            raise HTTPException(status_code=404, detail="League not found")
        
        # Return centralized settings
        return {
            "clubSlots": league["settings"]["club_slots_per_manager"],
            "budgetPerManager": league["settings"]["budget_per_manager"],
            "leagueSize": {
                "min": league["settings"]["league_size"]["min"],
                "max": league["settings"]["league_size"]["max"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get league settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/leagues/{league_id}/members/manage")
async def manage_league_member(
    league_id: str,
    member_action: MemberAction,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Approve or kick league members (commissioner only)"""
    try:
        success, message = await AdminService.manage_member(league_id, current_user.id, member_action)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Failed to manage member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/auctions/{auction_id}/manage")
async def manage_auction_admin(
    auction_id: str,
    action: str,
    league_id: str,
    params: Optional[Dict] = None,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Start, pause, resume auction (commissioner only)"""
    try:
        result = await AdminService.manage_auction(league_id, current_user.id, action, auction_id, params or {})
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        logger.error(f"Failed to manage auction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/auctions/{auction_id}/reorder-nominations")
async def reorder_nominations_admin(
    auction_id: str,
    league_id: str,
    new_order: List[str],
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Reorder nomination queue (commissioner only)"""
    try:
        reorder_request = NominationReorder(auction_id=auction_id, new_order=new_order)
        result = await AdminService.reorder_nominations(league_id, current_user.id, reorder_request)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        logger.error(f"Failed to reorder nominations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/leagues/{league_id}/audit")
async def get_comprehensive_audit(
    league_id: str,
    auction_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get comprehensive audit information (commissioner only)"""
    try:
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        audit_request = BidAuditRequest(
            auction_id=auction_id,
            league_id=league_id,
            user_id=user_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        result = await AdminService.get_comprehensive_audit(league_id, current_user.id, audit_request)
        if result["success"]:
            return result["data"]
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        logger.error(f"Failed to get audit data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/leagues/{league_id}/logs")
async def get_admin_logs(
    league_id: str,
    limit: int = 100,
    offset: int = 0,
    actor_id: Optional[str] = None,
    action_filter: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get admin logs for league (commissioner only)"""
    try:
        # Validate commissioner access
        if not await AdminService.validate_commissioner_access(current_user.id, league_id):
            raise HTTPException(status_code=403, detail="Commissioner access required")
        
        logs = await AuditService.get_audit_logs(
            league_id=league_id,
            limit=limit,
            offset=offset,
            actor_id=actor_id,
            action_filter=action_filter
        )
        
        return {"logs": [log.dict() for log in logs]}
    except Exception as e:
        logger.error(f"Failed to get admin logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/leagues/{league_id}/bid-audit")
async def get_bid_audit(
    league_id: str,
    auction_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get read-only bid audit (commissioner only)"""
    try:
        # Validate commissioner access
        if not await AdminService.validate_commissioner_access(current_user.id, league_id):
            raise HTTPException(status_code=403, detail="Commissioner access required")
        
        bid_audit = await AuditService.get_bid_audit(
            league_id=league_id,
            auction_id=auction_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return {"bids": bid_audit}
    except Exception as e:
        logger.error(f"Failed to get bid audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Competition Profile Routes
@api_router.get("/competition-profiles")
async def get_competition_profiles():
    """Get all available competition profiles"""
    try:
        profiles = await CompetitionService.get_all_profiles()
        return {"profiles": [profile.dict() for profile in profiles]}
    except Exception as e:
        logger.error(f"Failed to get competition profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/competition-profiles/{profile_id}")
async def get_competition_profile(profile_id: str):
    """Get specific competition profile"""
    try:
        profile = await CompetitionService.get_profile_by_id(profile_id)
        if profile:
            return profile.dict()
        else:
            raise HTTPException(status_code=404, detail="Competition profile not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get competition profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/competition-profiles/{profile_id}/defaults")
async def get_profile_defaults(profile_id: str):
    """Get default settings for a competition profile"""
    try:
        defaults = await CompetitionService.get_default_settings(profile_id)
        return defaults.dict()
    except Exception as e:
        logger.error(f"Failed to get profile defaults: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Aggregation Routes for UI pages
@api_router.get("/clubs/my-clubs/{league_id}")
async def get_my_clubs(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get user's owned clubs with budget info and upcoming fixtures"""
    await require_league_access(current_user.id, league_id)
    
    try:
        clubs_data = await AggregationService.get_user_clubs(league_id, current_user.id)
        return clubs_data
    except Exception as e:
        logger.error(f"Failed to get user clubs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/leagues/{league_id}/roster/summary")
async def get_roster_summary(
    league_id: str,
    userId: str = None,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get roster summary with owned count and remaining slots computed server-side"""
    await require_league_access(current_user.id, league_id)
    
    try:
        # Use provided userId or default to current user
        target_user_id = userId or current_user.id
        
        # Get league settings for club slots
        league = await db.leagues.find_one({"_id": league_id})
        if not league:
            raise HTTPException(status_code=404, detail="League not found")
        
        club_slots = league["settings"]["club_slots_per_manager"]
        
        # Get user's roster to count owned clubs
        roster = await db.rosters.find_one({
            "league_id": league_id,
            "user_id": target_user_id
        })
        
        owned_count = len(roster.get("clubs", [])) if roster else 0
        remaining = club_slots - owned_count
        
        return {
            "ownedCount": owned_count,
            "clubSlots": club_slots,
            "remaining": max(0, remaining)  # Ensure non-negative
        }
    except Exception as e:
        logger.error(f"Failed to get roster summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/fixtures/{league_id}")
async def get_league_fixtures(
    league_id: str,
    season: str = "2024-25",
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get all fixtures and results for the league with ownership badges"""
    await require_league_access(current_user.id, league_id)
    
    try:
        fixtures_data = await AggregationService.get_league_fixtures(league_id, season)
        return fixtures_data
    except Exception as e:
        logger.error(f"Failed to get league fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/leaderboard/{league_id}")
async def get_league_leaderboard(
    league_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get comprehensive league leaderboard with total points and weekly breakdown"""
    await require_league_access(current_user.id, league_id)
    
    try:
        leaderboard_data = await AggregationService.get_league_leaderboard(league_id)
        return leaderboard_data
    except Exception as e:
        logger.error(f"Failed to get league leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/head-to-head/{league_id}")
async def get_head_to_head(
    league_id: str,
    user1_id: str,
    user2_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get head-to-head comparison between two managers"""
    await require_league_access(current_user.id, league_id)
    
    try:
        comparison_data = await AggregationService.get_manager_head_to_head(league_id, user1_id, user2_id)
        return comparison_data
    except Exception as e:
        logger.error(f"Failed to get head-to-head comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Check database connectivity
        from database import client
        await client.admin.command('ping')
        
        # Check collections exist
        collections = await db.list_collection_names()
        required_collections = ['users', 'leagues', 'clubs', 'auctions']
        missing_collections = [col for col in required_collections if col not in collections]
        
        # Basic system info
        import psutil
        import os
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database": {
                "connected": True,
                "collections_count": len(collections),
                "missing_collections": missing_collections
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "services": {
                "websocket": True,  # Socket.IO is mounted
                "email": bool(os.getenv("SMTP_HOST")),
                "auth": bool(os.getenv("JWT_SECRET"))
            }
        }
        
        # Determine overall health
        if missing_collections:
            health_status["status"] = "degraded"
        
        if health_status["system"]["memory_percent"] > 90:
            health_status["status"] = "warning"
            
        if health_status["system"]["disk_percent"] > 95:
            health_status["status"] = "critical"
            
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

# Version endpoint
@fastapi_app.get("/version")
async def get_version():
    """Get application version information"""
    return {
        "version": "1.0.0",
        "build_date": "2025-01-15",
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Socket.IO configuration endpoint
@api_router.get("/socket/config")
async def socket_config():
    """Socket.IO configuration endpoint - returns canonical socket path"""
    socket_path = os.getenv('SOCKET_PATH', '/api/socketio')
    return {"path": socket_path}

# Socket.IO Diagnostic endpoint (alternative path to avoid routing conflicts)
@api_router.get("/socket-diag") 
async def socketio_diagnostics():
    """Socket.IO diagnostics endpoint - GET /api/socket-diag (avoiding /api/socketio path conflict)"""
    socket_path = os.getenv('SOCKET_PATH', '/api/socketio')
    return {
        "ok": True,
        "path": socket_path,
        "now": datetime.now(timezone.utc).isoformat()
    }

# Health endpoint (as specified in the pattern) - Use detailed health check
@fastapi_app.get("/api/health")
async def health():
    """Detailed health check endpoint"""
    return await health_check()

# Include the router in the main app
fastapi_app.include_router(api_router)

# Create single ASGI wrapper - Socket.IO intercepts /api/socketio, all other routes go to FastAPI
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path=SOCKETIO_PATH_INTERNAL)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)