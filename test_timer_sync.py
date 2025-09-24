#!/usr/bin/env python3
"""
Unit tests for server-authoritative timer with client drift correction
Tests the invariants: auction rules, anti-snipe timing, UI design stay the same
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from auction_engine import AuctionEngine, AuctionState
from models import *
from database import db

class TestServerAuthoritativeTimer:
    """Test server-authoritative timer with client drift correction"""

    @pytest.fixture
    async def auction_engine(self):
        """Create auction engine with mocked socket.io"""
        mock_sio = AsyncMock()
        engine = AuctionEngine(mock_sio)
        return engine

    @pytest.fixture
    async def mock_auction_data(self):
        """Sample auction data for testing"""
        return {
            "auction_id": "test_auction_1",
            "league_id": "test_league_1", 
            "status": "live",
            "current_lot_index": 0,
            "nomination_order": ["user1", "user2", "user3"],
            "settings": {
                "min_increment": 1,
                "bid_timer_seconds": 60,
                "anti_snipe_seconds": 30,  # 30 seconds for anti-snipe
                "budget_per_manager": 100
            }
        }

    @pytest.mark.asyncio
    async def test_late_bid_with_drift_extends_timer(self, auction_engine, mock_auction_data):
        """
        Test: Late bid with drift correction should extend timer server-authoritatively
        """
        # Setup
        lot_id = "test_lot_1"
        auction_id = mock_auction_data["auction_id"]
        auction_engine.active_auctions[auction_id] = mock_auction_data
        
        # Mock current time - 15 seconds before end (within anti-snipe threshold of 30s)
        now = datetime.now(timezone.utc)
        timer_ends_at = now + timedelta(seconds=15)  # 15 seconds remaining
        
        # Mock lot data
        mock_lot = {
            "_id": lot_id,
            "status": "open",
            "timer_ends_at": timer_ends_at,
            "current_bid": 50,
            "leading_bidder_id": "user1"
        }
        
        # Mock database operations
        with patch('auction_engine.db') as mock_db:
            # Mock lot queries
            mock_db.lots.find_one.return_value = mock_lot
            mock_db.lots.update_one = AsyncMock()
            
            # Mock AdminService validation
            with patch('auction_engine.AdminService') as mock_admin:
                mock_admin.validate_budget_constraint.return_value = (True, "")
                mock_admin.handle_simultaneous_bids.return_value = (True, "Bid successful", "bid_123")
                mock_admin.validate_timer_monotonicity.return_value = (True, "")
                
                # Place bid within anti-snipe window
                result = await auction_engine.place_bid(auction_id, lot_id, "user2", 55)
                
                # Verify bid was successful
                assert result["success"] == True
                
                # Verify timer was extended (server-authoritative)
                timer_update_call = None
                for call in mock_db.lots.update_one.call_args_list:
                    if "$set" in call[0][1] and "timer_ends_at" in call[0][1]["$set"]:
                        timer_update_call = call
                        break
                
                assert timer_update_call is not None, "Timer should have been extended"
                
                # Verify extension is for anti_snipe_seconds + 3
                extended_time = timer_update_call[0][1]["$set"]["timer_ends_at"]
                expected_extension = mock_auction_data["settings"]["anti_snipe_seconds"] + 3  # 33 seconds
                
                # Check that extension is approximately correct (within 1 second tolerance)
                time_diff = (extended_time - now).total_seconds()
                assert 32 <= time_diff <= 34, f"Extension should be ~33 seconds, got {time_diff}"

    @pytest.mark.asyncio 
    async def test_anti_snipe_extends_only_forward(self, auction_engine, mock_auction_data):
        """
        Test: Anti-snipe should only extend timer forward, never backward
        """
        # Setup
        lot_id = "test_lot_2"
        auction_id = mock_auction_data["auction_id"]
        auction_engine.active_auctions[auction_id] = mock_auction_data
        
        # Current time and timer end time
        now = datetime.now(timezone.utc)
        current_timer_end = now + timedelta(seconds=10)  # 10 seconds remaining (within anti-snipe)
        
        mock_lot = {
            "_id": lot_id,
            "status": "open", 
            "timer_ends_at": current_timer_end,
            "current_bid": 30,
            "leading_bidder_id": "user1"
        }
        
        with patch('auction_engine.db') as mock_db:
            mock_db.lots.find_one.return_value = mock_lot
            mock_db.lots.update_one = AsyncMock()
            
            with patch('auction_engine.AdminService') as mock_admin:
                mock_admin.validate_budget_constraint.return_value = (True, "")
                mock_admin.handle_simultaneous_bids.return_value = (True, "Bid successful", "bid_124")
                mock_admin.validate_timer_monotonicity.return_value = (True, "")
                
                # Place bid to trigger anti-snipe
                await auction_engine.place_bid(auction_id, lot_id, "user3", 35)
                
                # Find timer extension call
                timer_update_call = None
                for call in mock_db.lots.update_one.call_args_list:
                    if "$set" in call[0][1] and "timer_ends_at" in call[0][1]["$set"]:
                        timer_update_call = call
                        break
                
                assert timer_update_call is not None
                
                # Verify new end time is AFTER current end time (only forward)
                new_end_time = timer_update_call[0][1]["$set"]["timer_ends_at"]
                assert new_end_time > current_timer_end, "Timer should only extend forward"
                assert new_end_time > now, "New timer should be in the future"

    @pytest.mark.asyncio
    async def test_time_sync_broadcast_every_2_seconds(self, auction_engine):
        """
        Test: Server should broadcast time sync every 2 seconds
        """
        auction_id = "test_auction_sync"
        
        # Mock auction in database
        mock_auction = {
            "_id": auction_id,
            "current_lot_id": "lot_123"
        }
        
        mock_lot = {
            "_id": "lot_123",
            "timer_ends_at": datetime.now(timezone.utc) + timedelta(seconds=30),
            "status": "open"
        }
        
        with patch('auction_engine.db') as mock_db:
            mock_db.auctions.find_one.return_value = mock_auction
            mock_db.lots.find_one.return_value = mock_lot
            
            # Add auction to active auctions
            auction_engine.active_auctions[auction_id] = {"test": "data"}
            
            # Start time sync task
            task = asyncio.create_task(auction_engine._time_sync_loop(auction_id))
            
            # Let it run for 2.5 seconds to ensure at least one broadcast
            try:
                await asyncio.wait_for(task, timeout=2.5)
            except asyncio.TimeoutError:
                task.cancel()
            
            # Verify that time_sync was called
            assert auction_engine.sio.emit.called
            
            # Find time_sync calls
            time_sync_calls = [
                call for call in auction_engine.sio.emit.call_args_list 
                if call[0][0] == 'time_sync'
            ]
            
            assert len(time_sync_calls) >= 1, "Should have at least one time_sync broadcast"
            
            # Verify structure of time_sync message
            sync_data = time_sync_calls[0][0][1]  # Second argument is the data
            assert 'server_now' in sync_data
            assert 'current_lot' in sync_data
            
            # Clean up
            if not task.cancelled():
                task.cancel()

    @pytest.mark.asyncio
    async def test_bid_outside_anti_snipe_window_no_extension(self, auction_engine, mock_auction_data):
        """
        Test: Bid outside anti-snipe window should not extend timer
        """
        # Setup
        lot_id = "test_lot_3"
        auction_id = mock_auction_data["auction_id"] 
        auction_engine.active_auctions[auction_id] = mock_auction_data
        
        # Timer with 45 seconds remaining (outside 30s anti-snipe window)
        now = datetime.now(timezone.utc)
        timer_ends_at = now + timedelta(seconds=45)
        
        mock_lot = {
            "_id": lot_id,
            "status": "open",
            "timer_ends_at": timer_ends_at,
            "current_bid": 20,
            "leading_bidder_id": "user1"
        }
        
        with patch('auction_engine.db') as mock_db:
            mock_db.lots.find_one.return_value = mock_lot
            mock_db.lots.update_one = AsyncMock()
            
            with patch('auction_engine.AdminService') as mock_admin:
                mock_admin.validate_budget_constraint.return_value = (True, "")
                mock_admin.handle_simultaneous_bids.return_value = (True, "Bid successful", "bid_125")
                
                # Place bid outside anti-snipe window
                result = await auction_engine.place_bid(auction_id, lot_id, "user2", 25)
                
                # Verify bid was successful
                assert result["success"] == True
                
                # Verify timer was NOT extended
                timer_extension_calls = [
                    call for call in mock_db.lots.update_one.call_args_list
                    if "$set" in call[0][1] and "timer_ends_at" in call[0][1]["$set"]
                ]
                
                assert len(timer_extension_calls) == 0, "Timer should not be extended outside anti-snipe window"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])