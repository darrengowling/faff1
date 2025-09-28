#!/usr/bin/env python3
"""
WebSocket Connection Debug Test
Focused testing of Socket.IO connectivity issues
"""

import requests
import socketio
import time
import json
from datetime import datetime

class WebSocketDebugTester:
    def __init__(self, base_url="https://auction-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        
    def get_auth_token(self):
        """Get authentication token for testing"""
        # Request magic link
        response = requests.post(f"{self.api_url}/auth/magic-link", 
                               json={"email": "test@example.com"})
        
        if response.status_code == 200:
            data = response.json()
            if 'dev_magic_link' in data:
                # Extract token from dev magic link
                magic_link = data['dev_magic_link']
                token = magic_link.split('token=')[1]
                
                # Verify token
                verify_response = requests.post(f"{self.api_url}/auth/verify",
                                              json={"token": token})
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    self.token = verify_data['access_token']
                    print(f"✅ Authentication successful")
                    return True
                else:
                    print(f"❌ Token verification failed: {verify_response.status_code}")
            else:
                print(f"❌ No dev magic link in response: {data}")
        else:
            print(f"❌ Magic link request failed: {response.status_code}")
        
        return False
    
    def test_socket_io_endpoint_direct(self):
        """Test Socket.IO endpoint directly"""
        print("\n🔍 Testing Socket.IO endpoint accessibility...")
        
        # Test different Socket.IO endpoints
        endpoints = [
            "/socket.io/?EIO=4&transport=polling",
            "/socket.io/?EIO=3&transport=polling", 
            "/socket.io/socket.io.js",
            "/socket.io/"
        ]
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                response = requests.get(url, timeout=10)
                print(f"  {endpoint}: Status {response.status_code}")
                
                # Check if response looks like Socket.IO
                content = response.text[:200]
                if "socket.io" in content.lower() or response.status_code == 200:
                    if "<!doctype html>" in content:
                        print(f"    ⚠️  Returns HTML (frontend) instead of Socket.IO response")
                    else:
                        print(f"    ✅ Proper Socket.IO response")
                        print(f"    Content preview: {content}")
                else:
                    print(f"    ❌ Not a Socket.IO response")
                    
            except Exception as e:
                print(f"  {endpoint}: Error - {e}")
    
    def test_socket_io_client_connection(self):
        """Test Socket.IO client connection with different configurations"""
        print(f"\n🔌 Testing Socket.IO client connections...")
        
        if not self.token:
            print("❌ No authentication token available")
            return
        
        # Test different Socket.IO client configurations
        configs = [
            {
                "name": "Default config",
                "params": {
                    "transports": ['websocket', 'polling'],
                    "auth": {'token': self.token}
                }
            },
            {
                "name": "Polling only",
                "params": {
                    "transports": ['polling'],
                    "auth": {'token': self.token}
                }
            },
            {
                "name": "WebSocket only", 
                "params": {
                    "transports": ['websocket'],
                    "auth": {'token': self.token}
                }
            },
            {
                "name": "No auth",
                "params": {
                    "transports": ['websocket', 'polling']
                }
            }
        ]
        
        for config in configs:
            print(f"\n  Testing: {config['name']}")
            try:
                sio = socketio.Client()
                connection_events = []
                
                @sio.event
                def connect():
                    connection_events.append('connected')
                    print(f"    ✅ Connected successfully")
                
                @sio.event
                def connect_error(data):
                    connection_events.append(f'connect_error: {data}')
                    print(f"    ❌ Connection error: {data}")
                
                @sio.event
                def disconnect():
                    connection_events.append('disconnected')
                    print(f"    🔌 Disconnected")
                
                @sio.event
                def connection_status(data):
                    connection_events.append(f'status: {data}')
                    print(f"    📡 Connection status: {data}")
                
                # Attempt connection
                try:
                    sio.connect(self.base_url, **config['params'])
                    time.sleep(2)  # Wait for connection
                    
                    if sio.connected:
                        print(f"    ✅ Client reports connected")
                        
                        # Test a simple event
                        try:
                            response = sio.call('ping', {}, timeout=5)
                            print(f"    ✅ Ping response: {response}")
                        except Exception as e:
                            print(f"    ⚠️  Ping failed: {e}")
                    else:
                        print(f"    ❌ Client reports not connected")
                    
                    sio.disconnect()
                    
                except Exception as e:
                    print(f"    ❌ Connection failed: {e}")
                
                print(f"    Events: {connection_events}")
                
            except Exception as e:
                print(f"    ❌ Setup error: {e}")
    
    def test_socket_io_server_info(self):
        """Get Socket.IO server information"""
        print(f"\n📊 Socket.IO Server Information...")
        
        # Check if Socket.IO server responds to info requests
        info_endpoints = [
            "/socket.io/?EIO=4&transport=polling&t=test",
            "/socket.io/socket.io.js"
        ]
        
        for endpoint in info_endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                response = requests.get(url, timeout=5)
                print(f"  {endpoint}:")
                print(f"    Status: {response.status_code}")
                print(f"    Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    content = response.text[:500]
                    print(f"    Content preview: {content}")
                    
            except Exception as e:
                print(f"  {endpoint}: Error - {e}")
    
    def run_debug_tests(self):
        """Run all debug tests"""
        print("🚀 WebSocket Connection Debug Test Suite")
        print("=" * 60)
        
        # Get authentication token
        if self.get_auth_token():
            print(f"🔑 Using token: {self.token[:20]}...")
        
        # Test Socket.IO endpoint accessibility
        self.test_socket_io_endpoint_direct()
        
        # Test Socket.IO server info
        self.test_socket_io_server_info()
        
        # Test client connections
        self.test_socket_io_client_connection()
        
        print("\n" + "=" * 60)
        print("🏁 Debug tests completed")

if __name__ == "__main__":
    tester = WebSocketDebugTester()
    tester.run_debug_tests()