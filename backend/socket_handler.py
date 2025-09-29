import socketio
import jwt
import logging
import os
from typing import Dict, Optional, List
from datetime import datetime, timezone

from models import UserResponse
from database import db
from auth import SECRET_KEY, ALGORITHM
from auction_engine import get_auction_engine

class StateSnapshot:
    """Manages server state snapshots for reconnection"""
    
    @staticmethod
    async def get_auction_snapshot(auction_id: str, user_id: str) -> Dict:
        """Get complete auction state snapshot for reconnecting user"""
        try:
            # Get auction state
            auction = await db.auctions.find_one({"_id": auction_id})
            if not auction:
                return {"error": "Auction not found"}
            
            # Get current lot
            current_lot = None
            if auction.get("current_lot_id"):
                lot = await db.lots.find_one({"_id": auction["current_lot_id"]})
                if lot:
                    current_lot = {
                        "id": lot["_id"],
                        "club_id": lot["club_id"],
                        "status": lot["status"],
                        "current_bid": lot.get("current_bid", 0),
                        "leading_bidder_id": lot.get("leading_bidder_id"),
                        "timer_ends_at": lot.get("timer_ends_at").isoformat() if lot.get("timer_ends_at") else None
                    }
            
            # Get user's roster and budget
            user_roster = await db.rosters.find_one({
                "league_id": auction["league_id"],
                "user_id": user_id
            })
            
            user_budget = user_roster["budget_remaining"] if user_roster else 0
            user_slots = len(user_roster.get("clubs", [])) if user_roster else 0
            
            # Get all auction participants
            participants = []
            league_rosters = await db.rosters.find({"league_id": auction["league_id"]}).to_list(length=None)
            for roster in league_rosters:
                user = await db.users.find_one({"_id": roster["user_id"]})
                if user:
                    participants.append({
                        "user_id": user["_id"],
                        "display_name": user["display_name"],
                        "budget_remaining": roster["budget_remaining"],
                        "clubs_owned": len(roster.get("clubs", []))
                    })
            
            # Get auction settings
            settings = {
                "min_increment": auction["min_increment"],
                "bid_timer_seconds": auction["bid_timer_seconds"],
                "anti_snipe_seconds": auction["anti_snipe_seconds"],
                "budget_per_manager": auction["budget_per_manager"]
            }
            
            # Get presence information
            present_users = connection_manager.get_auction_users(auction_id)
            
            snapshot = {
                "auction": {
                    "id": auction["_id"],
                    "status": auction["status"],
                    "settings": settings
                },
                "current_lot": current_lot,
                "user_state": {
                    "budget_remaining": user_budget,
                    "slots_used": user_slots,
                    "max_slots": user_roster.get("max_slots", 3) if user_roster else 3
                },
                "participants": participants,
                "presence": present_users,
                "server_time": datetime.now(timezone.utc).isoformat(),
                "snapshot_version": "1.0"
            }
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error creating auction snapshot: {e}")
            return {"error": "Failed to create snapshot"}
    
    @staticmethod
    async def validate_snapshot_integrity(snapshot: Dict) -> bool:
        """Validate that snapshot data is consistent"""
        try:
            required_fields = ["auction", "server_time", "snapshot_version"]
            for field in required_fields:
                if field not in snapshot:
                    return False
            
            # Validate auction exists
            auction_id = snapshot["auction"]["id"]
            auction = await db.auctions.find_one({"_id": auction_id})
            if not auction:
                return False
            
            return True
            
        except Exception:
            return False

logger = logging.getLogger(__name__)

# Socket.IO configuration with environment variables
SOCKET_PATH = os.getenv('SOCKET_PATH', '/api/socket.io')
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'https://magic-league.preview.emergentagent.com')

# Create Socket.IO server with CORS configuration (integrated via ASGIApp overlay)
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=FRONTEND_ORIGIN,
    logger=logging.getLogger('socketio'),
    engineio_logger=logging.getLogger('socketio.engineio'),
    transports=['websocket', 'polling']
)

# Store user sessions with presence tracking
user_sessions: Dict[str, Dict] = {}  # session_id -> user_data
user_presence: Dict[str, Dict] = {}  # user_id -> presence_info

class PresenceStatus:
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"

class ConnectionManager:
    """Manages WebSocket connections and presence"""
    
    def __init__(self):
        self.connections: Dict[str, Dict] = {}  # session_id -> connection_info
        self.heartbeat_interval = 30  # seconds
        self.presence_timeout = 60  # seconds
    
    async def add_connection(self, sid: str, user: UserResponse, auction_id: str = None):
        """Add new connection and update presence"""
        connection_info = {
            'user_id': user.id,
            'user': user,
            'auction_id': auction_id,
            'last_seen': datetime.now(timezone.utc),
            'connected_at': datetime.now(timezone.utc)
        }
        
        self.connections[sid] = connection_info
        
        # Update user presence
        user_presence[user.id] = {
            'status': PresenceStatus.ONLINE,
            'last_seen': datetime.now(timezone.utc),
            'auction_id': auction_id,
            'display_name': user.display_name,
            'session_id': sid
        }
        
        # Broadcast presence update to auction room
        if auction_id:
            await sio.emit('user_presence', {
                'user_id': user.id,
                'display_name': user.display_name,
                'status': PresenceStatus.ONLINE,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=f"auction_{auction_id}")
            
        logger.info(f"User {user.display_name} connected to auction {auction_id}")
    
    async def remove_connection(self, sid: str):
        """Remove connection and update presence"""
        if sid not in self.connections:
            return
            
        connection_info = self.connections[sid]
        user_id = connection_info['user_id']
        auction_id = connection_info.get('auction_id')
        
        # Update presence to offline
        if user_id in user_presence:
            user_presence[user_id]['status'] = PresenceStatus.OFFLINE
            user_presence[user_id]['last_seen'] = datetime.now(timezone.utc)
            
            # Broadcast presence update
            if auction_id:
                await sio.emit('user_presence', {
                    'user_id': user_id,
                    'display_name': connection_info['user']['display_name'],
                    'status': PresenceStatus.OFFLINE,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }, room=f"auction_{auction_id}")
        
        del self.connections[sid]
        logger.info(f"User {connection_info['user']['display_name']} disconnected")
    
    async def update_heartbeat(self, sid: str):
        """Update last seen timestamp for connection"""
        if sid in self.connections:
            self.connections[sid]['last_seen'] = datetime.now(timezone.utc)
            user_id = self.connections[sid]['user_id']
            if user_id in user_presence:
                user_presence[user_id]['last_seen'] = datetime.now(timezone.utc)
    
    def get_auction_users(self, auction_id: str) -> List[Dict]:
        """Get all users present in an auction"""
        auction_users = []
        for sid, conn in self.connections.items():
            if conn.get('auction_id') == auction_id:
                user_id = conn['user_id']
                if user_id in user_presence:
                    auction_users.append(user_presence[user_id])
        return auction_users

# Global connection manager
connection_manager = ConnectionManager()

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
    """Handle client connection with enhanced presence tracking"""
    try:
        logger.info(f"Client {sid} attempting to connect")
        
        # Extract token from auth
        token = None
        if auth and 'token' in auth:
            token = auth['token']
        
        if not token:
            logger.warning(f"Client {sid} connected without token")
            await sio.emit('connection_status', {
                'status': 'unauthenticated',
                'message': 'Authentication required'
            }, to=sid)
            return False
        
        # Authenticate user
        user = await authenticate_socket(token)
        if not user:
            logger.warning(f"Client {sid} authentication failed")
            await sio.emit('connection_status', {
                'status': 'auth_failed',
                'message': 'Authentication failed'
            }, to=sid)
            return False
        
        # Store session
        user_sessions[sid] = {
            'user': user,
            'token': token,
            'connected_at': datetime.now(timezone.utc)
        }
        
        # Send connection success
        await sio.emit('connection_status', {
            'status': 'connected',
            'user': {
                'id': user.id,
                'display_name': user.display_name,
                'email': user.email
            },
            'server_time': datetime.now(timezone.utc).isoformat()
        }, to=sid)
        
        logger.info(f"Client {sid} connected successfully as {user.display_name}")
        return True
        
    except Exception as e:
        logger.error(f"Connection error for {sid}: {e}")
        await sio.emit('connection_status', {
            'status': 'error',
            'message': 'Connection failed'
        }, to=sid)
        return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection with presence cleanup"""
    try:
        # Remove from connection manager
        await connection_manager.remove_connection(sid)
        
        # Clean up session
        if sid in user_sessions:
            user = user_sessions[sid]['user']
            logger.info(f"User {user.display_name} disconnected")
            del user_sessions[sid]
        else:
            logger.info(f"Client {sid} disconnected")
            
    except Exception as e:
        logger.error(f"Disconnect error for {sid}: {e}")

@sio.event 
async def join_auction(sid, data):
    """Join auction room with presence tracking and state snapshot"""
    try:
        if sid not in user_sessions:
            await sio.emit('error', {'message': 'Not authenticated'}, to=sid)
            return
        
        auction_id = data.get('auction_id')
        if not auction_id:
            await sio.emit('error', {'message': 'Auction ID required'}, to=sid)
            return
        
        user = user_sessions[sid]['user']
        
        # Verify user has access to auction
        auction = await db.auctions.find_one({"_id": auction_id})
        if not auction:
            await sio.emit('error', {'message': 'Auction not found'}, to=sid)
            return
        
        # Check league membership
        membership = await db.memberships.find_one({
            "league_id": auction["league_id"],
            "user_id": user.id,
            "status": "accepted"
        })
        
        if not membership:
            await sio.emit('error', {'message': 'Access denied'}, to=sid)
            return
        
        # Join auction room
        await sio.enter_room(sid, f"auction_{auction_id}")
        
        # Add to connection manager
        await connection_manager.add_connection(sid, user, auction_id)
        
        # Get and send state snapshot
        snapshot = await StateSnapshot.get_auction_snapshot(auction_id, user.id)
        await sio.emit('auction_snapshot', snapshot, to=sid)
        
        # Send current presence list
        present_users = connection_manager.get_auction_users(auction_id)
        await sio.emit('presence_list', {'users': present_users}, to=sid)
        
        logger.info(f"User {user.display_name} joined auction {auction_id}")
        
    except Exception as e:
        logger.error(f"Join auction error for {sid}: {e}")
        await sio.emit('error', {'message': 'Failed to join auction'}, to=sid)

@sio.event
async def heartbeat(sid, data):
    """Handle client heartbeat for presence tracking"""
    try:
        if sid in user_sessions:
            await connection_manager.update_heartbeat(sid)
            await sio.emit('heartbeat_ack', {
                'server_time': datetime.now(timezone.utc).isoformat()
            }, to=sid)
    except Exception as e:
        logger.error(f"Heartbeat error for {sid}: {e}")

@sio.event
async def request_snapshot(sid, data):
    """Handle request for fresh state snapshot"""
    try:
        if sid not in user_sessions:
            await sio.emit('error', {'message': 'Not authenticated'}, to=sid)
            return
        
        auction_id = data.get('auction_id')
        if not auction_id:
            await sio.emit('error', {'message': 'Auction ID required'}, to=sid)
            return
        
        user = user_sessions[sid]['user']
        snapshot = await StateSnapshot.get_auction_snapshot(auction_id, user.id)
        
        # Validate snapshot before sending
        if await StateSnapshot.validate_snapshot_integrity(snapshot):
            await sio.emit('auction_snapshot', snapshot, to=sid)
            logger.info(f"Sent snapshot to {user.display_name} for auction {auction_id}")
        else:
            await sio.emit('error', {'message': 'Invalid snapshot'}, to=sid)
            
    except Exception as e:
        logger.error(f"Snapshot request error for {sid}: {e}")
        await sio.emit('error', {'message': 'Failed to get snapshot'}, to=sid)

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
    # Note: This function is kept for backward compatibility
    # The main integration now uses socketio.ASGIApp(sio, other_asgi_app=app)
    return socketio.ASGIApp(sio)