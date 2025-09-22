import socketio
import jwt
import logging
from typing import Dict, Optional

from models import UserResponse
from database import db
from auth import SECRET_KEY, ALGORITHM
from auction_engine import get_auction_engine

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Store user sessions
user_sessions: Dict[str, Dict] = {}  # session_id -> user_data

async def authenticate_socket(token: str) -> Optional[UserResponse]:
    """Authenticate socket connection using JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        user = await db.users.find_one({"_id": user_id})
        if user is None:
            return None
        
        return UserResponse(
            id=user["_id"],
            email=user["email"],
            display_name=user["display_name"],
            verified=user["verified"],
            created_at=user["created_at"]
        )
    except Exception as e:
        logger.error(f"Socket authentication failed: {e}")
        return None

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    try:
        # Get token from auth data
        if not auth or 'token' not in auth:
            logger.warning(f"Connection {sid} rejected: no token")
            return False
        
        # Authenticate user
        user = await authenticate_socket(auth['token'])
        if not user:
            logger.warning(f"Connection {sid} rejected: invalid token")
            return False
        
        # Store user session
        user_sessions[sid] = {
            "user": user,
            "joined_auctions": set()
        }
        
        logger.info(f"User {user.display_name} connected with session {sid}")
        return True
        
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    try:
        if sid in user_sessions:
            user = user_sessions[sid]["user"]
            
            # Leave all auction rooms
            for auction_id in user_sessions[sid]["joined_auctions"]:
                await sio.leave_room(sid, f"auction_{auction_id}")
            
            # Clean up session
            del user_sessions[sid]
            
            logger.info(f"User {user.display_name} disconnected (session {sid})")
    except Exception as e:
        logger.error(f"Disconnect error: {e}")

@sio.event
async def join_auction(sid, data):
    """Join auction room for real-time updates"""
    try:
        if sid not in user_sessions:
            return {"success": False, "error": "Not authenticated"}
        
        auction_id = data.get("auction_id")
        if not auction_id:
            return {"success": False, "error": "Missing auction_id"}
        
        user = user_sessions[sid]["user"]
        
        # Verify user has access to this auction's league
        auction = await db.auctions.find_one({"_id": auction_id})
        if not auction:
            return {"success": False, "error": "Auction not found"}
        
        # Check membership
        membership = await db.memberships.find_one({
            "league_id": auction["league_id"],
            "user_id": user.id
        })
        
        if not membership:
            return {"success": False, "error": "Access denied"}
        
        # Join auction room
        await sio.enter_room(sid, f"auction_{auction_id}")
        user_sessions[sid]["joined_auctions"].add(auction_id)
        
        # Send current auction state
        engine = get_auction_engine()
        auction_state = await engine.get_auction_state(auction_id)
        
        if auction_state:
            await sio.emit('auction_state', auction_state, room=sid)
        
        # Notify room of new participant
        await sio.emit('user_joined', {
            "user": {
                "id": user.id,
                "display_name": user.display_name
            }
        }, room=f"auction_{auction_id}", skip_sid=sid)
        
        logger.info(f"User {user.display_name} joined auction {auction_id}")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Join auction error: {e}")
        return {"success": False, "error": str(e)}

@sio.event
async def leave_auction(sid, data):
    """Leave auction room"""
    try:
        if sid not in user_sessions:
            return {"success": False, "error": "Not authenticated"}
        
        auction_id = data.get("auction_id")
        if not auction_id:
            return {"success": False, "error": "Missing auction_id"}
        
        user = user_sessions[sid]["user"]
        
        # Leave auction room
        await sio.leave_room(sid, f"auction_{auction_id}")
        user_sessions[sid]["joined_auctions"].discard(auction_id)
        
        # Notify room of departure
        await sio.emit('user_left', {
            "user": {
                "id": user.id,
                "display_name": user.display_name
            }
        }, room=f"auction_{auction_id}")
        
        logger.info(f"User {user.display_name} left auction {auction_id}")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Leave auction error: {e}")
        return {"success": False, "error": str(e)}

@sio.event
async def place_bid(sid, data):
    """Place bid through WebSocket"""
    try:
        if sid not in user_sessions:
            return {"success": False, "error": "Not authenticated"}
        
        user = user_sessions[sid]["user"]
        auction_id = data.get("auction_id")
        lot_id = data.get("lot_id")
        amount = data.get("amount")
        
        if not all([auction_id, lot_id, amount]):
            return {"success": False, "error": "Missing required fields"}
        
        if not isinstance(amount, int) or amount <= 0:
            return {"success": False, "error": "Invalid bid amount"}
        
        # Place bid through auction engine
        engine = get_auction_engine()
        result = await engine.place_bid(auction_id, lot_id, user.id, amount)
        
        # Send individual response
        await sio.emit('bid_result', result, room=sid)
        
        return result
        
    except Exception as e:
        logger.error(f"Place bid error: {e}")
        return {"success": False, "error": str(e)}

@sio.event
async def send_chat_message(sid, data):
    """Send chat message to auction room"""
    try:
        if sid not in user_sessions:
            return {"success": False, "error": "Not authenticated"}
        
        user = user_sessions[sid]["user"]
        auction_id = data.get("auction_id")
        message = data.get("message", "").strip()
        
        if not auction_id or not message:
            return {"success": False, "error": "Missing auction_id or message"}
        
        if len(message) > 500:
            return {"success": False, "error": "Message too long"}
        
        # Broadcast chat message
        chat_data = {
            "auction_id": auction_id,
            "user": {
                "id": user.id,
                "display_name": user.display_name
            },
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await sio.emit('chat_message', chat_data, room=f"auction_{auction_id}")
        
        logger.info(f"Chat message from {user.display_name} in auction {auction_id}")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        return {"success": False, "error": str(e)}

@sio.event
async def get_auction_state(sid, data):
    """Get current auction state"""
    try:
        if sid not in user_sessions:
            return {"success": False, "error": "Not authenticated"}
        
        auction_id = data.get("auction_id")
        if not auction_id:
            return {"success": False, "error": "Missing auction_id"}
        
        engine = get_auction_engine()
        state = await engine.get_auction_state(auction_id)
        
        if state:
            await sio.emit('auction_state', state, room=sid)
            return {"success": True}
        else:
            return {"success": False, "error": "Auction not found or not active"}
        
    except Exception as e:
        logger.error(f"Get auction state error: {e}")
        return {"success": False, "error": str(e)}

# Heartbeat to keep connections alive
@sio.event
async def ping(sid, data):
    """Handle ping for connection keepalive"""
    return {"pong": True}

def get_socketio_app():
    """Get the Socket.IO ASGI application"""
    return socketio.ASGIApp(sio)