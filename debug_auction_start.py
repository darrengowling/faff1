#!/usr/bin/env python3
"""
DEBUG AUCTION START
Debug the auction start issue to understand what's happening.
"""

import requests
import json
import os
import uuid

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://leaguemate-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def create_session(email: str) -> requests.Session:
    """Create authenticated session for user"""
    session = requests.Session()
    
    # Test login to get session cookie
    login_response = session.post(f"{API_BASE}/auth/test-login", json={"email": email})
    if login_response.status_code != 200:
        raise Exception(f"Failed to login user {email}: {login_response.status_code}")
        
    return session

def main():
    print("🔍 DEBUGGING AUCTION START ISSUE")
    
    # Create test users
    commissioner_email = f"debug-commissioner-{uuid.uuid4().hex[:8]}@test.com"
    manager_email = f"debug-manager-{uuid.uuid4().hex[:8]}@test.com"
    
    # Create sessions
    commissioner_session = create_session(commissioner_email)
    manager_session = create_session(manager_email)
    
    print(f"✅ Created sessions for {commissioner_email} and {manager_email}")
    
    # Create league
    league_data = {
        "name": f"Debug League {uuid.uuid4().hex[:8]}",
        "season": "2025-26",
        "settings": {
            "budget_per_manager": 100,
            "club_slots_per_manager": 8,
            "bid_timer_seconds": 60,
            "anti_snipe_seconds": 30,
            "league_size": {"min": 2, "max": 8}
        }
    }
    
    create_response = commissioner_session.post(f"{API_BASE}/leagues", json=league_data)
    if create_response.status_code != 201:
        print(f"❌ League creation failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return
        
    league_id = create_response.json()["leagueId"]
    print(f"✅ Created league: {league_id}")
    
    # Add manager to league
    join_response = manager_session.post(f"{API_BASE}/leagues/{league_id}/join")
    if join_response.status_code != 200:
        print(f"❌ Manager join failed: {join_response.status_code}")
        print(f"Response: {join_response.text}")
        return
        
    print(f"✅ Manager joined league")
    
    # Check league status
    status_response = commissioner_session.get(f"{API_BASE}/leagues/{league_id}/status")
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"✅ League status: {status_data}")
    else:
        print(f"❌ Status check failed: {status_response.status_code}")
        return
        
    # Try to start auction
    print(f"\n🚀 Attempting to start auction for league {league_id}")
    start_response = commissioner_session.post(f"{API_BASE}/auction/{league_id}/start")
    
    print(f"Status Code: {start_response.status_code}")
    print(f"Response Headers: {dict(start_response.headers)}")
    print(f"Response Text: {start_response.text}")
    
    if start_response.status_code == 200:
        try:
            start_data = start_response.json()
            print(f"Response JSON: {json.dumps(start_data, indent=2)}")
            
            if start_data.get('success'):
                auction_id = start_data.get('auction_id', league_id)
                print(f"✅ Auction started successfully: {auction_id}")
                
                # Try to get auction state
                print(f"\n🔍 Checking auction state...")
                state_response = commissioner_session.get(f"{API_BASE}/auction/{auction_id}/state")
                print(f"State Status Code: {state_response.status_code}")
                print(f"State Response: {state_response.text}")
                
            else:
                print(f"❌ Auction start failed: {start_data.get('error', 'Unknown error')}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
    else:
        print(f"❌ Auction start request failed")

if __name__ == "__main__":
    main()