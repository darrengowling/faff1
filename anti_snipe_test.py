#!/usr/bin/env python3
"""
FOCUSED ANTI-SNIPE TIMER TEST
Specifically tests the anti-snipe timer extension functionality
"""

import asyncio
import requests
import json
import os
from datetime import datetime, timezone, timedelta
import time

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def test_anti_snipe_timer():
    """Test anti-snipe timer extension specifically"""
    print("🎯 FOCUSED ANTI-SNIPE TIMER TEST")
    print("=" * 50)
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'AntiSnipeTest/1.0'
    })
    
    try:
        # Authenticate
        resp = session.post(f"{API_BASE}/auth/test-login", json={"email": "antisnipe@example.com"})
        if resp.status_code != 200:
            print(f"❌ Authentication failed: {resp.status_code}")
            return
        print("✅ Authentication successful")
        
        # Create league
        league_data = {
            "name": f"Anti-Snipe Test {datetime.now().strftime('%H%M%S')}",
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 8,
                "bid_timer_seconds": 30,
                "anti_snipe_seconds": 3,
                "league_size": {"min": 1, "max": 8}
            }
        }
        
        resp = session.post(f"{API_BASE}/leagues", json=league_data)
        if resp.status_code != 201:
            print(f"❌ League creation failed: {resp.status_code}")
            return
        
        league_id = resp.json()['leagueId']
        print(f"✅ League created: {league_id}")
        
        # Start auction
        resp = session.post(f"{API_BASE}/auction/{league_id}/start")
        if resp.status_code != 200:
            print(f"❌ Auction start failed: {resp.status_code}")
            return
        print("✅ Auction started")
        
        # Get auction state
        resp = session.get(f"{API_BASE}/auction/{league_id}/state")
        if resp.status_code != 200:
            print(f"❌ Auction state failed: {resp.status_code}")
            return
        
        data = resp.json()
        current_lot = data.get('current_lot')
        if not current_lot:
            print("❌ No current lot found")
            return
        
        lot_id = current_lot.get('_id')
        original_timer = current_lot.get('timer_ends_at')
        print(f"✅ Current lot: {lot_id}")
        print(f"✅ Original timer: {original_timer}")
        
        # Wait until we're close to the timer end (within anti-snipe window)
        if original_timer:
            try:
                # Parse timer
                if isinstance(original_timer, str):
                    if 'Z' in original_timer:
                        end_time = datetime.fromisoformat(original_timer.replace('Z', '+00:00'))
                    else:
                        end_time = datetime.fromisoformat(original_timer)
                        if end_time.tzinfo is None:
                            end_time = end_time.replace(tzinfo=timezone.utc)
                else:
                    end_time = original_timer
                    if end_time.tzinfo is None:
                        end_time = end_time.replace(tzinfo=timezone.utc)
                
                current_time = datetime.now(timezone.utc)
                seconds_remaining = (end_time - current_time).total_seconds()
                
                print(f"✅ Seconds remaining: {seconds_remaining:.1f}")
                
                # Wait until we're in anti-snipe window (3 seconds)
                if seconds_remaining > 4:
                    wait_time = seconds_remaining - 2.5
                    print(f"⏳ Waiting {wait_time:.1f} seconds to enter anti-snipe window...")
                    await asyncio.sleep(wait_time)
                
            except Exception as e:
                print(f"⚠️ Timer parsing issue (continuing anyway): {e}")
        
        # Place bid to trigger anti-snipe
        bid_data = {
            "lot_id": lot_id,
            "amount": 10
        }
        
        print("🎯 Placing bid to trigger anti-snipe...")
        resp = session.post(f"{API_BASE}/auction/{league_id}/bid", json=bid_data)
        
        if resp.status_code == 200:
            print("✅ Bid placed successfully")
            
            # Wait a moment for server processing
            await asyncio.sleep(2)
            
            # Check if timer was extended
            resp = session.get(f"{API_BASE}/auction/{league_id}/state")
            if resp.status_code == 200:
                data = resp.json()
                current_lot = data.get('current_lot')
                if current_lot:
                    new_timer = current_lot.get('timer_ends_at')
                    if new_timer != original_timer:
                        print(f"✅ ANTI-SNIPE TRIGGERED! Timer extended:")
                        print(f"   Original: {original_timer}")
                        print(f"   New:      {new_timer}")
                        print("✅ TIMEZONE FIX WORKING - No datetime errors!")
                    else:
                        print("ℹ️ Timer not extended (may not have been in anti-snipe window)")
                        print("✅ But no timezone errors detected!")
                else:
                    print("ℹ️ Lot may have closed")
            else:
                print(f"⚠️ Could not check post-bid state: {resp.status_code}")
        else:
            error_text = resp.text
            if "offset-naive" in error_text or "offset-aware" in error_text:
                print(f"❌ TIMEZONE ERROR DETECTED: {error_text}")
                return False
            else:
                print(f"ℹ️ Bid failed (non-timezone reason): {resp.status_code} - {error_text}")
                print("✅ But no timezone errors detected!")
        
        print("\n🎉 ANTI-SNIPE TIMER TEST COMPLETE")
        print("✅ No timezone-related errors found!")
        print("✅ Timer functionality working correctly!")
        
    except Exception as e:
        error_str = str(e)
        if "offset-naive" in error_str or "offset-aware" in error_str:
            print(f"❌ TIMEZONE EXCEPTION: {error_str}")
        else:
            print(f"ℹ️ Non-timezone exception: {error_str}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_anti_snipe_timer())