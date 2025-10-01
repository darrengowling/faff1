#!/usr/bin/env python3
"""
Focused League Creation Test
Direct testing of the league creation endpoint with proper authentication
"""

import requests
import json
import time
from datetime import datetime

def test_league_creation():
    base_url = "https://leaguemate-1.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Generate unique test data
    timestamp = datetime.now().strftime('%H%M%S%f')[:-3]  # Include milliseconds
    test_email = f"league_test_{timestamp}@example.com"
    unique_league_name = f"Test League {timestamp}"
    
    print("🧪 FOCUSED LEAGUE CREATION TEST")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"Test Email: {test_email}")
    print(f"League Name: {unique_league_name}")
    print("=" * 50)
    
    # Step 1: Test Login
    print("\n1️⃣ Testing Authentication...")
    auth_response = requests.post(
        f"{api_url}/auth/test-login",
        json={"email": test_email},
        headers={'Content-Type': 'application/json'},
        timeout=15
    )
    
    print(f"   Auth Status: {auth_response.status_code}")
    if auth_response.status_code != 200:
        print(f"   ❌ Auth failed: {auth_response.text}")
        return False
    
    auth_data = auth_response.json()
    print(f"   ✅ Auth successful: {auth_data.get('email')}")
    
    # Step 2: Get proper access token via magic link
    print("\n2️⃣ Getting Access Token...")
    magic_response = requests.post(
        f"{api_url}/auth/magic-link",
        json={"email": test_email},
        headers={'Content-Type': 'application/json'},
        timeout=15
    )
    
    if magic_response.status_code != 200:
        print(f"   ❌ Magic link failed: {magic_response.status_code}")
        return False
    
    magic_data = magic_response.json()
    if 'dev_magic_link' not in magic_data:
        print(f"   ❌ No dev magic link in response")
        return False
    
    # Extract token
    magic_link = magic_data['dev_magic_link']
    token = magic_link.split('token=')[1]
    
    # Verify token
    verify_response = requests.post(
        f"{api_url}/auth/verify",
        json={"token": token},
        headers={'Content-Type': 'application/json'},
        timeout=15
    )
    
    if verify_response.status_code != 200:
        print(f"   ❌ Token verification failed: {verify_response.status_code}")
        return False
    
    verify_data = verify_response.json()
    access_token = verify_data.get('access_token')
    if not access_token:
        print(f"   ❌ No access token in response")
        return False
    
    print(f"   ✅ Access token obtained")
    
    # Step 3: Test League Creation
    print("\n3️⃣ Testing League Creation...")
    
    league_data = {
        "name": unique_league_name,
        "season": "2025-26",
        "settings": {
            "budget_per_manager": 100,
            "min_increment": 1,
            "club_slots_per_manager": 5,
            "anti_snipe_seconds": 3,
            "bid_timer_seconds": 8,
            "league_size": {
                "min": 2,
                "max": 4
            },
            "scoring_rules": {
                "club_goal": 1,
                "club_win": 3,
                "club_draw": 1
            }
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    print(f"   Creating league: {unique_league_name}")
    league_response = requests.post(
        f"{api_url}/leagues",
        json=league_data,
        headers=headers,
        timeout=15
    )
    
    print(f"   League Creation Status: {league_response.status_code}")
    
    try:
        response_data = league_response.json()
        print(f"   Response: {json.dumps(response_data, indent=2)}")
    except:
        print(f"   Response Text: {league_response.text}")
        response_data = {}
    
    # Analyze the response
    if league_response.status_code == 201:
        if 'leagueId' in response_data:
            league_id = response_data['leagueId']
            print(f"   ✅ League created successfully with ID: {league_id}")
            
            # Step 4: Test Readiness Endpoint
            print("\n4️⃣ Testing League Readiness...")
            readiness_response = requests.get(
                f"{api_url}/test/league/{league_id}/ready",
                timeout=15
            )
            
            print(f"   Readiness Status: {readiness_response.status_code}")
            if readiness_response.status_code == 200:
                readiness_data = readiness_response.json()
                print(f"   Readiness Data: {json.dumps(readiness_data, indent=2)}")
                
                if readiness_data.get('ready') is True:
                    print(f"   ✅ League is ready!")
                    return True
                else:
                    print(f"   ⚠️  League not ready: {readiness_data.get('reason')}")
                    return True  # Still success - league was created
            else:
                print(f"   ❌ Readiness check failed: {readiness_response.text}")
                return True  # Still success - league was created
        else:
            print(f"   ❌ No leagueId in 201 response")
            return False
    elif league_response.status_code == 500:
        error_text = league_response.text
        if "transaction" in error_text.lower() or "replica set" in error_text.lower():
            print(f"   🚨 MONGODB TRANSACTION ERROR CONFIRMED")
            print(f"   Error details: {error_text}")
        else:
            print(f"   ❌ 500 error (not transaction related): {error_text}")
        return False
    else:
        print(f"   ❌ Unexpected status code: {league_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_league_creation()
    if success:
        print("\n✅ LEAGUE CREATION TEST PASSED")
    else:
        print("\n❌ LEAGUE CREATION TEST FAILED")
    
    exit(0 if success else 1)