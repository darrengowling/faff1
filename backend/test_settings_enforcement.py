#!/usr/bin/env python3
"""
Unit Tests for Settings Enforcement Guards
Tests server-side validation of league settings for safety
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

from admin_service import AdminService

class TestLeagueSizeEnforcement:
    """Test league size validation for auction starting"""
    
    @pytest.mark.asyncio
    async def test_start_auction_success_with_minimum_members(self):
        """Test start auction succeeds when league has minimum required members"""
        
        # Mock league with min=2, current members=2
        mock_league = {
            "_id": "test_league",
            "member_count": 2,
            "settings": {
                "league_size": {"min": 2, "max": 8}
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            
            # Test start auction validation
            valid, error = await AdminService.validate_league_size_constraints("test_league", "start_auction")
            
            assert valid == True
            assert error == ""
            mock_db.leagues.find_one.assert_called_once_with({"_id": "test_league"})
    
    @pytest.mark.asyncio
    async def test_start_auction_fails_insufficient_members(self):
        """Test start auction fails when league has insufficient members"""
        
        # Mock league with min=4, current members=2
        mock_league = {
            "_id": "test_league", 
            "member_count": 2,
            "settings": {
                "league_size": {"min": 4, "max": 8}
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            
            # Test start auction validation
            valid, error = await AdminService.validate_league_size_constraints("test_league", "start_auction")
            
            assert valid == False
            assert "You must have ≥ 4 managers to start" in error
            assert "currently have 2" in error
    
    @pytest.mark.asyncio
    async def test_start_auction_with_exact_minimum(self):
        """Test start auction succeeds with exact minimum members"""
        
        # Mock league with min=3, current members=3 (exact match)
        mock_league = {
            "_id": "test_league",
            "member_count": 3,
            "settings": {
                "league_size": {"min": 3, "max": 6}
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            
            # Test start auction validation
            valid, error = await AdminService.validate_league_size_constraints("test_league", "start_auction")
            
            assert valid == True
            assert error == ""
    
    @pytest.mark.asyncio
    async def test_start_auction_league_not_found(self):
        """Test start auction fails when league doesn't exist"""
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=None)
            
            # Test start auction validation
            valid, error = await AdminService.validate_league_size_constraints("nonexistent_league", "start_auction")
            
            assert valid == False
            assert error == "League not found"


class TestRosterCapacityEnforcement:
    """Test roster capacity validation for lot closing/bidding"""
    
    @pytest.mark.asyncio
    async def test_bid_success_with_available_slots(self):
        """Test bidding succeeds when user has available roster slots"""
        
        # Mock league with 5 slots per manager
        mock_league = {
            "_id": "test_league",
            "settings": {
                "club_slots_per_manager": 5
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            # Mock user currently owns 3 clubs (2 slots available)
            mock_db.roster_clubs.count_documents = AsyncMock(return_value=3)
            
            # Test roster capacity validation
            valid, error = await AdminService.validate_roster_capacity("user123", "test_league")
            
            assert valid == True
            assert error == ""
            mock_db.roster_clubs.count_documents.assert_called_once_with({
                "user_id": "user123",
                "league_id": "test_league"
            })
    
    @pytest.mark.asyncio 
    async def test_bid_fails_roster_full(self):
        """Test bidding fails when user's roster is at capacity"""
        
        # Mock league with 3 slots per manager
        mock_league = {
            "_id": "test_league",
            "settings": {
                "club_slots_per_manager": 3
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            # Mock user already owns 3 clubs (full roster)
            mock_db.roster_clubs.count_documents = AsyncMock(return_value=3)
            
            # Test roster capacity validation
            valid, error = await AdminService.validate_roster_capacity("user123", "test_league")
            
            assert valid == False
            assert "You already own 3/3 clubs" in error
    
    @pytest.mark.asyncio
    async def test_bid_at_capacity_limit(self):
        """Test bidding fails when user is exactly at capacity"""
        
        # Mock league with 5 slots per manager
        mock_league = {
            "_id": "test_league",
            "settings": {
                "club_slots_per_manager": 5
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            # Mock user owns exactly 5 clubs (at capacity)
            mock_db.roster_clubs.count_documents = AsyncMock(return_value=5)
            
            # Test roster capacity validation
            valid, error = await AdminService.validate_roster_capacity("user123", "test_league")
            
            assert valid == False
            assert "You already own 5/5 clubs" in error
    
    @pytest.mark.asyncio
    async def test_bid_with_zero_clubs_owned(self):
        """Test bidding succeeds when user owns no clubs"""
        
        # Mock league with 4 slots per manager
        mock_league = {
            "_id": "test_league",
            "settings": {
                "club_slots_per_manager": 4
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            # Mock user owns 0 clubs
            mock_db.roster_clubs.count_documents = AsyncMock(return_value=0)
            
            # Test roster capacity validation
            valid, error = await AdminService.validate_roster_capacity("user123", "test_league")
            
            assert valid == True
            assert error == ""
    
    @pytest.mark.asyncio
    async def test_bid_league_not_found(self):
        """Test bidding fails when league doesn't exist"""
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=None)
            
            # Test roster capacity validation
            valid, error = await AdminService.validate_roster_capacity("user123", "nonexistent_league")
            
            assert valid == False
            assert error == "League not found"


class TestStructuredErrorMessages:
    """Test that error messages are user-friendly and structured"""
    
    @pytest.mark.asyncio
    async def test_league_size_error_message_format(self):
        """Test league size error message format matches specification"""
        
        # Mock league with min=4, current=2
        mock_league = {
            "_id": "test_league",
            "member_count": 2,
            "settings": {
                "league_size": {"min": 4, "max": 8}
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            
            valid, error = await AdminService.validate_league_size_constraints("test_league", "start_auction")
            
            # Check error message format matches: "You must have ≥ {min} managers to start"
            assert not valid
            assert "You must have ≥ 4 managers to start" in error
            assert "currently have 2" in error
    
    @pytest.mark.asyncio
    async def test_roster_capacity_error_message_format(self):
        """Test roster capacity error message format matches specification"""
        
        # Mock league with 3 slots, user owns 3
        mock_league = {
            "_id": "test_league",
            "settings": {
                "club_slots_per_manager": 3
            }
        }
        
        with patch('admin_service.db') as mock_db:
            mock_db.leagues.find_one = AsyncMock(return_value=mock_league)
            mock_db.roster_clubs.count_documents = AsyncMock(return_value=3)
            
            valid, error = await AdminService.validate_roster_capacity("user123", "test_league")
            
            # Check error message format matches: "You already own {owned}/{slots} clubs"
            assert not valid
            assert "You already own 3/3 clubs" in error


if __name__ == "__main__":
    # Run tests
    print("🧪 Running Settings Enforcement Unit Tests...")
    
    # Test league size enforcement
    print("\n📊 Testing League Size Enforcement...")
    test_class = TestLeagueSizeEnforcement()
    
    try:
        asyncio.run(test_class.test_start_auction_success_with_minimum_members())
        print("✅ Start auction succeeds with minimum members")
        
        asyncio.run(test_class.test_start_auction_fails_insufficient_members())
        print("✅ Start auction fails with insufficient members")
        
        asyncio.run(test_class.test_start_auction_with_exact_minimum())
        print("✅ Start auction succeeds with exact minimum")
        
        asyncio.run(test_class.test_start_auction_league_not_found())
        print("✅ Start auction fails with league not found")
        
    except Exception as e:
        print(f"❌ League size test failed: {e}")
    
    # Test roster capacity enforcement  
    print("\n🏟️ Testing Roster Capacity Enforcement...")
    test_class = TestRosterCapacityEnforcement()
    
    try:
        asyncio.run(test_class.test_bid_success_with_available_slots())
        print("✅ Bid succeeds with available slots")
        
        asyncio.run(test_class.test_bid_fails_roster_full())
        print("✅ Bid fails when roster full")
        
        asyncio.run(test_class.test_bid_at_capacity_limit())
        print("✅ Bid fails when at capacity limit")
        
        asyncio.run(test_class.test_bid_with_zero_clubs_owned())
        print("✅ Bid succeeds with zero clubs owned")
        
        asyncio.run(test_class.test_bid_league_not_found())
        print("✅ Bid fails with league not found")
        
    except Exception as e:
        print(f"❌ Roster capacity test failed: {e}")
    
    # Test structured error messages
    print("\n💬 Testing Structured Error Messages...")
    test_class = TestStructuredErrorMessages()
    
    try:
        asyncio.run(test_class.test_league_size_error_message_format())
        print("✅ League size error message format correct")
        
        asyncio.run(test_class.test_roster_capacity_error_message_format())
        print("✅ Roster capacity error message format correct")
        
    except Exception as e:
        print(f"❌ Error message test failed: {e}")
    
    print("\n🎉 All Settings Enforcement Tests Completed!")