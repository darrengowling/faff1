#!/usr/bin/env python3
"""
Simple Socket.IO connection test to debug authentication issues
"""

import asyncio
import requests
import json
import os
import socketio

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://livebid-app.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
SOCKET_URL = BACKEND_URL

async def test_socket_connection():
    """Test basic Socket.IO connection"""
    print("🔍 Testing Socket.IO Connection")
    
    try:
        # First, authenticate and get JWT token
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SimpleSocketTest/1.0'
        })
        
        # Test login
        resp = session.post(f"{API_BASE}/auth/test-login", json={"email": "test@socket.com"})
        if resp.status_code != 200:
            print(f"❌ Authentication failed: {resp.status_code} - {resp.text}")
            return
            
        print("✅ Authentication successful")
        
        # Get JWT token via magic link
        resp = session.post(f"{API_BASE}/auth/magic-link", json={"email": "test@socket.com"})
        if resp.status_code != 200:
            print(f"❌ Magic link failed: {resp.status_code} - {resp.text}")
            return
            
        data = resp.json()
        if 'dev_magic_link' not in data:
            print(f"❌ No dev magic link in response: {data}")
            return
            
        # Extract token
        magic_link = data['dev_magic_link']
        token = magic_link.split('token=')[1] if 'token=' in magic_link else None
        
        if not token:
            print(f"❌ No token in magic link: {magic_link}")
            return
            
        print("✅ Magic link token extracted")
        
        # Verify token to get JWT
        resp = session.post(f"{API_BASE}/auth/verify", json={"token": token})
        if resp.status_code != 200:
            print(f"❌ Token verification failed: {resp.status_code} - {resp.text}")
            return
            
        verify_data = resp.json()
        jwt_token = verify_data.get('access_token')
        
        if not jwt_token:
            print(f"❌ No JWT token in verify response: {verify_data}")
            return
            
        print("✅ JWT token obtained")
        
        # Now test Socket.IO connection
        sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=3,
            reconnection_delay=1
        )
        
        @sio.event
        async def connect():
            print("✅ Socket.IO connected successfully")
            
        @sio.event
        async def disconnect():
            print("🔌 Socket.IO disconnected")
            
        @sio.event
        async def connect_error(data):
            print(f"❌ Socket.IO connection error: {data}")
            
        # Connect with JWT authentication
        auth_data = {'token': jwt_token}
        print(f"🔗 Attempting Socket.IO connection to: {SOCKET_URL}/api/socket.io")
        print(f"🔑 Using JWT token: {jwt_token[:20]}...")
        
        await sio.connect(f"{SOCKET_URL}/api/socket.io", auth=auth_data)
        
        # Wait a bit to see if connection is stable
        await asyncio.sleep(2)
        
        # Test a simple event
        print("📤 Testing simple event emission")
        await sio.emit('test_event', {'message': 'hello'})
        
        await asyncio.sleep(1)
        
        # Disconnect
        await sio.disconnect()
        print("✅ Socket.IO test completed successfully")
        
    except Exception as e:
        print(f"❌ Socket.IO test failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    await test_socket_connection()

if __name__ == "__main__":
    asyncio.run(main())