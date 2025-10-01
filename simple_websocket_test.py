#!/usr/bin/env python3
"""
SIMPLE WEBSOCKET TEST - Debug authentication and basic connectivity
"""

import asyncio
import aiohttp
import json
import time

# Configuration
BACKEND_URL = "https://livebid-app.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

async def test_authentication():
    """Test basic authentication"""
    print("🔐 Testing authentication...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE}/auth/test-login", 
                                   json={"email": "test@example.com"}) as resp:
                print(f"Auth response status: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    print(f"Auth result: {result}")
                    
                    # Extract cookies
                    cookies = {}
                    try:
                        for cookie in resp.cookies:
                            cookies[cookie.key] = cookie.value
                            print(f"Cookie: {cookie.key}={cookie.value}")
                    except Exception as cookie_error:
                        print(f"Cookie extraction error: {cookie_error}")
                    
                    # Also try to get cookies from headers
                    if not cookies and 'Set-Cookie' in resp.headers:
                        print(f"Set-Cookie header: {resp.headers['Set-Cookie']}")
                        # Simple cookie parsing
                        cookie_str = resp.headers['Set-Cookie']
                        if 'access_token=' in cookie_str:
                            token_part = cookie_str.split('access_token=')[1].split(';')[0]
                            cookies['access_token'] = token_part
                            print(f"Extracted access_token: {token_part[:20]}...")
                    
                    return {
                        "success": True,
                        "user_id": result["userId"],
                        "cookies": cookies
                    }
                else:
                    text = await resp.text()
                    print(f"Auth failed: {resp.status} - {text}")
                    return {"success": False, "error": f"Auth failed: {resp.status}"}
        except Exception as e:
            print(f"Auth exception: {e}")
            return {"success": False, "error": str(e)}

async def test_league_creation(cookies):
    """Test league creation with authentication"""
    print("🏆 Testing league creation...")
    
    league_data = {
        "name": f"Test League {int(time.time())}",
        "season": "2025-26",
        "settings": {
            "budget_per_manager": 100,
            "club_slots_per_manager": 8,
            "bid_timer_seconds": 60,
            "anti_snipe_seconds": 30,
            "league_size": {
                "min": 2,
                "max": 8
            }
        }
    }
    
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    headers = {"Cookie": cookie_header, "Content-Type": "application/json"}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE}/leagues", 
                                   json=league_data, 
                                   headers=headers) as resp:
                print(f"League creation status: {resp.status}")
                if resp.status == 201:
                    result = await resp.json()
                    print(f"League created: {result}")
                    return {"success": True, "league_id": result["leagueId"]}
                else:
                    text = await resp.text()
                    print(f"League creation failed: {resp.status} - {text}")
                    return {"success": False, "error": f"Failed: {resp.status}"}
        except Exception as e:
            print(f"League creation exception: {e}")
            return {"success": False, "error": str(e)}

async def test_socket_io_basic():
    """Test basic Socket.IO connectivity"""
    print("📡 Testing Socket.IO connectivity...")
    
    try:
        import socketio
        
        sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        
        @sio.event
        async def connect():
            print("✅ Socket.IO connected successfully")
            
        @sio.event
        async def disconnect():
            print("❌ Socket.IO disconnected")
            
        # Try to connect
        await sio.connect(BACKEND_URL, socketio_path="/api/socketio")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Test join_league event
        await sio.emit('join_league', {
            'league_id': 'test-league-123',
            'user_id': 'test-user-456'
        })
        
        await asyncio.sleep(2)
        
        await sio.disconnect()
        
        return {"success": True}
        
    except Exception as e:
        print(f"Socket.IO test failed: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Main test execution"""
    print("🚀 Simple WebSocket Test")
    print("=" * 50)
    
    # Test 1: Authentication
    auth_result = await test_authentication()
    if not auth_result["success"]:
        print("❌ Authentication test failed")
        return False
    
    print("✅ Authentication test passed")
    
    # Test 2: League Creation
    league_result = await test_league_creation(auth_result["cookies"])
    if not league_result["success"]:
        print("❌ League creation test failed")
        return False
    
    print("✅ League creation test passed")
    
    # Test 3: Socket.IO Basic
    socket_result = await test_socket_io_basic()
    if not socket_result["success"]:
        print("❌ Socket.IO test failed")
        return False
    
    print("✅ Socket.IO test passed")
    
    print("\n🎉 All basic tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)