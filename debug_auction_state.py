#!/usr/bin/env python3
"""
DEBUG AUCTION STATE
Debug the auction state to see what's happening with lots
"""

import requests
import json
import os
import time

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def debug_auction_state():
    """Debug auction state and lots"""
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'DebugAuctionState/1.0'
    })
    
    # Authenticate
    print("🔐 Authenticating...")
    resp = session.post(f"{API_BASE}/auth/test-login", json={"email": "debug2@test.com"})
    if resp.status_code != 200:
        print(f"❌ Authentication failed: {resp.status_code} - {resp.text}")
        return
    
    user_data = resp.json()
    print(f"✅ Authenticated as {user_data['userId']}")
    
    # Create league
    print("\n🏆 Creating league...")
    league_data = {
        "name": f"Debug League 2",
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
    
    # Add a second user to make league ready
    print("\n👥 Adding second user...")
    session2 = requests.Session()
    session2.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'DebugAuctionState/1.0'
    })
    
    resp = session2.post(f"{API_BASE}/auth/test-login", json={"email": "debug2_manager@test.com"})
    if resp.status_code == 200:
        resp = session2.post(f"{API_BASE}/leagues/{league_id}/join")
        if resp.status_code == 200:
            print("✅ Second user joined")
        else:
            print(f"❌ Second user join failed: {resp.status_code} - {resp.text}")
    
    # Check league status
    print("\n📊 Checking league status...")
    resp = session.get(f"{API_BASE}/leagues/{league_id}/status")
    if resp.status_code == 200:
        status_data = resp.json()
        print(f"✅ League status: {json.dumps(status_data, indent=2)}")
        
        if status_data['is_ready']:
            # Try to start auction
            print("\n🎯 Starting auction...")
            resp = session.post(f"{API_BASE}/auction/{league_id}/start")
            print(f"Auction start response: {resp.status_code}")
            
            if resp.status_code == 200:
                auction_data = resp.json()
                print(f"✅ Auction started: {json.dumps(auction_data, indent=2)}")
                
                # Wait a moment for lots to be created
                print("\n⏳ Waiting for lots to be created...")
                time.sleep(3)
                
                # Try to get auction state
                print("\n📊 Getting auction state...")
                resp = session.get(f"{API_BASE}/auction/{league_id}/state")
                print(f"Auction state response: {resp.status_code}")
                
                if resp.status_code == 200:
                    state_data = resp.json()
                    print(f"✅ Auction state: {json.dumps(state_data, indent=2)}")
                    
                    # Check if current_lot exists
                    current_lot = state_data.get('current_lot')
                    if current_lot:
                        print(f"✅ Current lot found: {current_lot.get('id', 'No ID')}")
                    else:
                        print("❌ No current lot found")
                        
                        # Let's check the database directly for lots
                        print("\n🔍 Checking database for lots...")
                        import asyncio
                        from motor.motor_asyncio import AsyncIOMotorClient
                        
                        async def check_lots():
                            client = AsyncIOMotorClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017'))
                            db = client[os.getenv('DB_NAME', 'test_database')]
                            
                            lots = await db.lots.find({"auction_id": league_id}).to_list(length=10)
                            print(f"Found {len(lots)} lots in database")
                            for lot in lots:
                                print(f"  - Lot {lot.get('_id')}: status={lot.get('status')}, club_id={lot.get('club_id')}")
                            
                            client.close()
                        
                        asyncio.run(check_lots())
                        
                else:
                    print(f"❌ Auction state failed: {resp.status_code} - {resp.text}")
            else:
                print(f"❌ Auction start failed: {resp.status_code} - {resp.text}")
        else:
            print("❌ League not ready for auction")
    else:
        print(f"❌ League status check failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    debug_auction_state()