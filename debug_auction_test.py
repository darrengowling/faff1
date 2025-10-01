#!/usr/bin/env python3
"""
DEBUG AUCTION TEST
Debug the auction start and state retrieval issue
"""

import requests
import json
import os

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def debug_auction():
    """Debug auction start and state retrieval"""
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'DebugAuctionTest/1.0'
    })
    
    # Authenticate
    print("🔐 Authenticating...")
    resp = session.post(f"{API_BASE}/auth/test-login", json={"email": "debug@test.com"})
    if resp.status_code != 200:
        print(f"❌ Authentication failed: {resp.status_code} - {resp.text}")
        return
    
    user_data = resp.json()
    print(f"✅ Authenticated as {user_data['userId']}")
    
    # Create league
    print("\n🏆 Creating league...")
    league_data = {
        "name": f"Debug League",
        "season": "2025-26",
        "settings": {
            "budget_per_manager": 100,
            "club_slots_per_manager": 8,
            "bid_timer_seconds": 60,
            "anti_snipe_seconds": 30,
            "league_size": {"min": 2, "max": 8}
        }
    }
    
    resp = session.post(f"{API_BASE}/leagues", json=league_data)
    if resp.status_code != 201:
        print(f"❌ League creation failed: {resp.status_code} - {resp.text}")
        return
    
    league_response = resp.json()
    league_id = league_response['leagueId']
    print(f"✅ League created: {league_id}")
    
    # Check league status
    print("\n📊 Checking league status...")
    resp = session.get(f"{API_BASE}/leagues/{league_id}/status")
    if resp.status_code == 200:
        status_data = resp.json()
        print(f"✅ League status: {json.dumps(status_data, indent=2)}")
    else:
        print(f"❌ League status check failed: {resp.status_code} - {resp.text}")
    
    # Try to start auction
    print("\n🎯 Starting auction...")
    resp = session.post(f"{API_BASE}/auction/{league_id}/start")
    print(f"Auction start response: {resp.status_code}")
    print(f"Response text: {resp.text}")
    
    if resp.status_code == 200:
        auction_data = resp.json()
        print(f"✅ Auction started: {json.dumps(auction_data, indent=2)}")
        
        # Try to get auction state
        print("\n📊 Getting auction state...")
        resp = session.get(f"{API_BASE}/auction/{league_id}/state")
        print(f"Auction state response: {resp.status_code}")
        print(f"Response text: {resp.text}")
        
        if resp.status_code == 200:
            state_data = resp.json()
            print(f"✅ Auction state: {json.dumps(state_data, indent=2)}")
        else:
            print(f"❌ Auction state failed: {resp.status_code} - {resp.text}")
    else:
        print(f"❌ Auction start failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    debug_auction()