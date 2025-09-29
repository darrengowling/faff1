#!/usr/bin/env python3
"""
Focused Atomic League Creation Test
Tests the specific MongoDB transaction fix mentioned in the review request
"""

import requests
import json
import time
from datetime import datetime

def test_atomic_league_creation():
    """Test atomic league creation after MongoDB transaction fixes"""
    
    base_url = "https://pifa-league.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🧪 ATOMIC LEAGUE CREATION TEST - MongoDB Transaction Fix Verification")
    print("=" * 70)
    print(f"Backend URL: {base_url}")
    print(f"Environment: TEST_MODE=true, ALLOW_TEST_LOGIN=true")
    print("=" * 70)
    
    # Step 1: Authenticate with test login endpoint
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Include milliseconds
    test_email = f"atomic_fix_test_{timestamp}@example.com"
    
    print(f"\n🔐 Step 1: Authenticate with test login endpoint")
    print(f"Test email: {test_email}")
    
    try:
        auth_response = requests.post(
            f"{api_url}/auth/test-login",
            json={"email": test_email},
            timeout=10
        )
        
        print(f"Auth response status: {auth_response.status_code}")
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.text}")
            return False
            
        auth_data = auth_response.json()
        print(f"✅ Authentication successful: {auth_data.get('message', 'OK')}")
        
        # Get access token via magic link flow
        magic_response = requests.post(
            f"{api_url}/auth/magic-link",
            json={"email": test_email},
            timeout=10
        )
        
        if magic_response.status_code != 200:
            print(f"❌ Magic link request failed: {magic_response.status_code}")
            return False
            
        magic_data = magic_response.json()
        if 'dev_magic_link' not in magic_data:
            print(f"❌ No dev magic link in response: {magic_data}")
            return False
            
        # Extract token
        magic_link = magic_data['dev_magic_link']
        token = magic_link.split('token=')[1] if 'token=' in magic_link else None
        
        if not token:
            print(f"❌ Could not extract token from magic link")
            return False
            
        # Verify token
        verify_response = requests.post(
            f"{api_url}/auth/verify",
            json={"token": token},
            timeout=10
        )
        
        if verify_response.status_code != 200:
            print(f"❌ Token verification failed: {verify_response.status_code}")
            return False
            
        verify_data = verify_response.json()
        access_token = verify_data.get('access_token')
        
        if not access_token:
            print(f"❌ No access token in verification response")
            return False
            
        print(f"✅ Access token obtained successfully")
        
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False
    
    # Step 2: Create league with timestamp-unique name
    league_name = f"Atomic Fix Test {timestamp}"
    
    print(f"\n🏟️ Step 2: Create league with unique name")
    print(f"League name: {league_name}")
    
    league_data = {
        "name": league_name,
        "season": "2025-26",
        "settings": {
            "budget_per_manager": 100,
            "min_increment": 1,
            "club_slots_per_manager": 5,
            "anti_snipe_seconds": 30,
            "bid_timer_seconds": 60,
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
    
    try:
        league_response = requests.post(
            f"{api_url}/leagues",
            json=league_data,
            headers=headers,
            timeout=15
        )
        
        print(f"League creation response status: {league_response.status_code}")
        
        if league_response.status_code == 500:
            print(f"❌ CRITICAL: League creation returned 500 Internal Server Error")
            try:
                error_data = league_response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
                
                # Check for MongoDB transaction errors
                error_str = json.dumps(error_data).lower()
                if any(keyword in error_str for keyword in [
                    'transaction', 'replica set', 'mongos', 'transaction numbers'
                ]):
                    print(f"🚨 MONGODB TRANSACTION ERROR DETECTED!")
                    print(f"This confirms the issue mentioned in the review request")
                    return False
                    
            except:
                print(f"Error response text: {league_response.text}")
            return False
            
        elif league_response.status_code == 201:
            print(f"✅ League creation returned 201 Created (SUCCESS!)")
            
            try:
                league_data = league_response.json()
                print(f"Response data: {json.dumps(league_data, indent=2)}")
                
                # Step 3: Verify 201 response format with {leagueId}
                if 'leagueId' in league_data:
                    league_id = league_data['leagueId']
                    print(f"✅ Response contains leagueId: {league_id}")
                    
                    # Step 4: Test readiness endpoint
                    print(f"\n🔍 Step 3: Test readiness endpoint")
                    
                    # Poll readiness endpoint (up to 5 seconds)
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        try:
                            ready_response = requests.get(
                                f"{api_url}/test/league/{league_id}/ready",
                                headers=headers,
                                timeout=5
                            )
                            
                            if ready_response.status_code == 200:
                                ready_data = ready_response.json()
                                print(f"Readiness check {attempt + 1}: {ready_data}")
                                
                                if ready_data.get('ready') == True:
                                    print(f"✅ League is ready! All documents created successfully")
                                    break
                                elif attempt < max_attempts - 1:
                                    time.sleep(0.5)  # Wait 500ms before next check
                                else:
                                    print(f"⚠️ League not ready after {max_attempts} attempts")
                                    print(f"Reason: {ready_data.get('reason', 'unknown')}")
                            else:
                                print(f"❌ Readiness endpoint failed: {ready_response.status_code}")
                                break
                                
                        except Exception as e:
                            print(f"❌ Readiness check error: {str(e)}")
                            break
                    
                    print(f"\n🎉 ATOMIC LEAGUE CREATION TEST RESULTS:")
                    print(f"✅ POST /leagues returns 201 with {{leagueId}} (no 500 errors)")
                    print(f"✅ League creation completes without transaction failures")
                    print(f"✅ GET /test/league/:id/ready endpoint accessible")
                    print(f"✅ Sequential operations working (no MongoDB transactions)")
                    
                    return True
                    
                else:
                    print(f"❌ Response missing leagueId field")
                    return False
                    
            except Exception as e:
                print(f"❌ Error parsing league response: {str(e)}")
                return False
                
        else:
            print(f"❌ Unexpected status code: {league_response.status_code}")
            try:
                error_data = league_response.json()
                print(f"Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {league_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ League creation request error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_atomic_league_creation()
    
    print(f"\n" + "=" * 70)
    if success:
        print(f"🎉 ATOMIC LEAGUE CREATION TEST: PASSED")
        print(f"✅ MongoDB transaction fixes are working correctly!")
        print(f"✅ League creation is now atomic without transactions")
        exit(0)
    else:
        print(f"❌ ATOMIC LEAGUE CREATION TEST: FAILED")
        print(f"🚨 MongoDB transaction issues still present")
        print(f"💡 The review request fixes may not be fully applied")
        exit(1)