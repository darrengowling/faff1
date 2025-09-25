#!/usr/bin/env python3
"""
Unit tests for PR2: Robust Reconnect & Presence System
Tests WebSocket connection resilience, presence tracking, and state snapshots
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
from datetime import datetime, timezone, timedelta

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from websocket import ConnectionManager, StateSnapshot, PresenceStatus
from models import UserResponse

class TestReconnectAndPresence:
    """Test robust reconnect and presence functionality"""

    @pytest.fixture
    async def connection_manager(self):
        """Create connection manager for testing"""
        return ConnectionManager()

    @pytest.fixture
    async def mock_user(self):
        """Create mock user for testing"""
        return UserResponse(
            id="user_123",
            email="test@example.com",
            display_name="Test User",
            verified=True
        )

    @pytest.fixture
    async def mock_auction_data(self):
        """Sample auction data for testing"""
        return {
            "_id": "auction_123",
            "league_id": "league_123",
            "status": "live",
            "current_lot_id": "lot_123",
            "min_increment": 1,
            "bid_timer_seconds": 60,
            "anti_snipe_seconds": 30,
            "budget_per_manager": 100
        }

    @pytest.mark.asyncio
    async def test_connection_manager_add_connection(self, connection_manager, mock_user):
        """Test adding a new connection updates presence correctly"""
        # Setup
        sid = "session_123"
        auction_id = "auction_123"
        
        # Mock sio.emit
        with patch('websocket.sio') as mock_sio:
            mock_sio.emit = AsyncMock()
            
            # Add connection
            await connection_manager.add_connection(sid, mock_user, auction_id)
            
            # Verify connection was stored
            assert sid in connection_manager.connections
            connection_info = connection_manager.connections[sid]
            assert connection_info['user_id'] == mock_user.id
            assert connection_info['auction_id'] == auction_id
            
            # Verify presence was updated
            from websocket import user_presence
            assert mock_user.id in user_presence
            presence_info = user_presence[mock_user.id]
            assert presence_info['status'] == PresenceStatus.ONLINE
            assert presence_info['auction_id'] == auction_id
            assert presence_info['display_name'] == mock_user.display_name
            
            # Verify presence broadcast was sent
            mock_sio.emit.assert_called_once_with(
                'user_presence',
                {
                    'user_id': mock_user.id,
                    'display_name': mock_user.display_name,
                    'status': PresenceStatus.ONLINE,
                    'timestamp': pytest.approx(datetime.now(timezone.utc).isoformat(), abs=5)
                },
                room=f"auction_{auction_id}"
            )

    @pytest.mark.asyncio
    async def test_connection_manager_remove_connection(self, connection_manager, mock_user):
        """Test removing connection updates presence to offline"""
        # Setup - first add a connection
        sid = "session_123"
        auction_id = "auction_123"
        
        with patch('websocket.sio') as mock_sio:
            mock_sio.emit = AsyncMock()
            
            # Add connection first
            await connection_manager.add_connection(sid, mock_user, auction_id)
            
            # Reset mock to test removal
            mock_sio.reset_mock()
            
            # Remove connection
            await connection_manager.remove_connection(sid)
            
            # Verify connection was removed
            assert sid not in connection_manager.connections
            
            # Verify presence was updated to offline
            from websocket import user_presence
            assert mock_user.id in user_presence
            presence_info = user_presence[mock_user.id]
            assert presence_info['status'] == PresenceStatus.OFFLINE
            
            # Verify offline broadcast was sent
            mock_sio.emit.assert_called_once_with(
                'user_presence',
                {
                    'user_id': mock_user.id,
                    'display_name': mock_user.display_name,
                    'status': PresenceStatus.OFFLINE,
                    'timestamp': pytest.approx(datetime.now(timezone.utc).isoformat(), abs=5)
                },
                room=f"auction_{auction_id}"
            )

    @pytest.mark.asyncio
    async def test_heartbeat_updates_last_seen(self, connection_manager, mock_user):
        """Test heartbeat updates last seen timestamp"""
        # Setup
        sid = "session_123"
        auction_id = "auction_123"
        
        with patch('websocket.sio') as mock_sio:
            mock_sio.emit = AsyncMock()
            
            # Add connection
            await connection_manager.add_connection(sid, mock_user, auction_id)
            original_last_seen = connection_manager.connections[sid]['last_seen']
            
            # Wait a moment and update heartbeat
            await asyncio.sleep(0.1)
            await connection_manager.update_heartbeat(sid)
            
            # Verify last seen was updated
            updated_last_seen = connection_manager.connections[sid]['last_seen']
            assert updated_last_seen > original_last_seen

    @pytest.mark.asyncio
    async def test_get_auction_users(self, connection_manager, mock_user):
        """Test getting users present in specific auction"""
        # Setup multiple users
        user1 = mock_user
        user2 = UserResponse(
            id="user_456",
            email="user2@example.com", 
            display_name="User Two",
            verified=True
        )
        
        auction_id = "auction_123"
        
        with patch('websocket.sio') as mock_sio:
            mock_sio.emit = AsyncMock()
            
            # Add connections
            await connection_manager.add_connection("sid1", user1, auction_id)
            await connection_manager.add_connection("sid2", user2, auction_id)
            await connection_manager.add_connection("sid3", user1, "other_auction")
            
            # Get auction users
            auction_users = connection_manager.get_auction_users(auction_id)
            
            # Verify correct users returned
            assert len(auction_users) == 2
            user_ids = [user['user_id'] for user in auction_users if 'user_id' in user]
            assert user1.id in str(user_ids)
            assert user2.id in str(user_ids)

    @pytest.mark.asyncio
    async def test_state_snapshot_creation(self, mock_auction_data):
        """Test creating auction state snapshot"""
        user_id = "user_123"
        auction_id = "auction_123"
        
        # Mock database responses
        mock_lot = {
            "_id": "lot_123",
            "club_id": "club_123", 
            "status": "open",
            "current_bid": 50,
            "leading_bidder_id": "user_456",
            "timer_ends_at": datetime.now(timezone.utc) + timedelta(seconds=30)
        }
        
        mock_roster = {
            "league_id": "league_123",
            "user_id": user_id,
            "budget_remaining": 75,
            "clubs": ["club_1", "club_2"],
            "max_slots": 3
        }
        
        mock_league_rosters = [mock_roster]
        mock_user_doc = {
            "_id": user_id,
            "display_name": "Test User"
        }
        
        with patch('websocket.db') as mock_db:
            mock_db.auctions.find_one.return_value = mock_auction_data
            mock_db.lots.find_one.return_value = mock_lot
            mock_db.rosters.find_one.return_value = mock_roster
            mock_db.rosters.find.return_value.to_list.return_value = mock_league_rosters
            mock_db.users.find_one.return_value = mock_user_doc
            
            # Mock connection manager
            with patch('websocket.connection_manager') as mock_conn_mgr:
                mock_conn_mgr.get_auction_users.return_value = [
                    {'user_id': user_id, 'status': 'online', 'display_name': 'Test User'}
                ]
                
                # Create snapshot
                snapshot = await StateSnapshot.get_auction_snapshot(auction_id, user_id)
                
                # Verify snapshot structure
                assert 'auction' in snapshot
                assert 'current_lot' in snapshot
                assert 'user_state' in snapshot
                assert 'participants' in snapshot
                assert 'presence' in snapshot
                assert 'server_time' in snapshot
                assert 'snapshot_version' in snapshot
                
                # Verify auction data
                assert snapshot['auction']['id'] == auction_id
                assert snapshot['auction']['status'] == mock_auction_data['status']
                
                # Verify current lot
                assert snapshot['current_lot']['id'] == mock_lot['_id']
                assert snapshot['current_lot']['status'] == mock_lot['status']
                assert snapshot['current_lot']['current_bid'] == mock_lot['current_bid']
                
                # Verify user state
                assert snapshot['user_state']['budget_remaining'] == mock_roster['budget_remaining']
                assert snapshot['user_state']['slots_used'] == len(mock_roster['clubs'])

    @pytest.mark.asyncio
    async def test_snapshot_validation(self):
        """Test snapshot integrity validation"""
        # Valid snapshot
        valid_snapshot = {
            'auction': {'id': 'auction_123'},
            'server_time': datetime.now(timezone.utc).isoformat(),
            'snapshot_version': '1.0'
        }
        
        # Invalid snapshot (missing fields)
        invalid_snapshot = {
            'auction': {'id': 'auction_123'}
            # Missing server_time and snapshot_version
        }
        
        with patch('websocket.db') as mock_db:
            mock_db.auctions.find_one.return_value = {'_id': 'auction_123'}
            
            # Test valid snapshot
            is_valid = await StateSnapshot.validate_snapshot_integrity(valid_snapshot)
            assert is_valid == True
            
            # Test invalid snapshot
            is_valid = await StateSnapshot.validate_snapshot_integrity(invalid_snapshot)
            assert is_valid == False

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test exponential backoff calculation for reconnection"""
        # This would be tested on the frontend, but we can test the logic
        def get_reconnect_delay(attempts):
            delay = min(1000 * (2 ** attempts), 10000)
            return delay
        
        # Test backoff progression: 1s → 2s → 4s → 8s → 10s (max)
        assert get_reconnect_delay(0) == 1000   # 1 second
        assert get_reconnect_delay(1) == 2000   # 2 seconds  
        assert get_reconnect_delay(2) == 4000   # 4 seconds
        assert get_reconnect_delay(3) == 8000   # 8 seconds
        assert get_reconnect_delay(4) == 10000  # 10 seconds (max)
        assert get_reconnect_delay(10) == 10000 # Still max at 10 seconds

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])