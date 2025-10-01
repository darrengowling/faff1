#!/usr/bin/env python3
"""
TARGETED DATABASE SCHEMA FIX TEST
Specifically tests that lots can transition to "going_once" and "going_twice" status values
"""

import asyncio
import requests
import json
import os
import time
from datetime import datetime

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def test_lot_status_transitions():
    """Test that lots can transition through all status values including going_once and going_twice"""
    
    print("🎯 TARGETED DATABASE SCHEMA FIX TEST")
    print("Testing lot status transitions: open → going_once → going_twice")
    print("=" * 60)
    
    # Authenticate
    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json'})
    
    resp = session.post(f"{API_BASE}/auth/test-login", json={"email": "commissioner@example.com"})
    if resp.status_code != 200:
        print(f"❌ Authentication failed: {resp.status_code}")
        return False
        
    print("✅ Authenticated successfully")
    
    # Create league with short timer for testing
    league_data = {
        "name": f"Schema Fix Test {datetime.now().strftime('%H%M%S')}",
        "season": "2025-26",
        "settings": {
            "budget_per_manager": 100,
            "club_slots_per_manager": 8,
            "bid_timer_seconds": 10,  # Very short timer for testing
            "anti_snipe_seconds": 3,
            "league_size": {"min": 2, "max": 8}
        }
    }
    
    resp = session.post(f"{API_BASE}/leagues", json=league_data)
    if resp.status_code != 201:
        print(f"❌ League creation failed: {resp.status_code} - {resp.text}")
        return False
        
    league_id = resp.json()['leagueId']
    print(f"✅ League created: {league_id}")
    
    # Add a second user
    session2 = requests.Session()
    session2.headers.update({'Content-Type': 'application/json'})
    resp = session2.post(f"{API_BASE}/auth/test-login", json={"email": "manager@example.com"})
    if resp.status_code == 200:
        resp = session2.post(f"{API_BASE}/leagues/{league_id}/join")
        if resp.status_code == 200:
            print("✅ Second user joined league")
        
    # Start auction
    resp = session.post(f"{API_BASE}/auction/{league_id}/start")
    if resp.status_code != 200:
        print(f"❌ Auction start failed: {resp.status_code} - {resp.text}")
        return False
        
    print("✅ Auction started successfully")
    
    # Monitor lot status transitions
    print("\n🔍 Monitoring lot status transitions...")
    
    statuses_seen = set()
    max_wait_time = 30  # Wait up to 30 seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        resp = session.get(f"{API_BASE}/auction/{league_id}/state")
        if resp.status_code == 200:
            data = resp.json()
            current_lot = data.get('current_lot')
            if current_lot:
                status = current_lot.get('status')
                if status not in statuses_seen:
                    statuses_seen.add(status)
                    timer_ends_at = current_lot.get('timer_ends_at', 'No timer')
                    print(f"📊 Lot status: {status} (Timer: {timer_ends_at})")
                    
                    # Check if we've seen the target statuses
                    if 'going_once' in statuses_seen or 'going_twice' in statuses_seen:
                        print("🎉 SUCCESS: Database schema supports going_once/going_twice statuses!")
                        print(f"✅ Statuses observed: {sorted(statuses_seen)}")
                        return True
                        
        time.sleep(1)  # Check every second
        
    print(f"⏰ Test completed after {max_wait_time} seconds")
    print(f"📊 Statuses observed: {sorted(statuses_seen)}")
    
    if 'going_once' in statuses_seen or 'going_twice' in statuses_seen:
        print("🎉 SUCCESS: Database schema supports going_once/going_twice statuses!")
        return True
    else:
        print("❌ ISSUE: going_once/going_twice statuses not observed")
        print("   This could mean:")
        print("   1. Timer is too long for test duration")
        print("   2. Lot status transitions are not working")
        print("   3. Database schema still has validation issues")
        return False

if __name__ == "__main__":
    asyncio.run(test_lot_status_transitions())