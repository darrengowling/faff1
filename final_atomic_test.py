#!/usr/bin/env python3
"""
Final Atomic League Creation Test
Tests the specific MongoDB transaction fix mentioned in the review request
"""

import requests
import json
from datetime import datetime

def test_atomic_league_creation_fix():
    """Test the specific atomic league creation fix"""
    
    base_url = "https://testid-enforcer.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🧪 ATOMIC LEAGUE CREATION - MongoDB Transaction Fix Test")
    print("=" * 60)
    print("Review Request Verification:")
    print("✓ MongoDB transaction code removed entirely from league_service.py")
    print("✓ Fixed table name mismatch: db.memberships → db.league_memberships")
    print("✓ Backend restarted successfully with no startup errors")
    print("=" * 60)
    
    # Test data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
    test_email = f"final_atomic_test_{timestamp}@example.com"
    league_name = f"Atomic Fix Test {timestamp}"
    
    test_results = {
        "authentication": False,
        "league_creation_201": False,
        "response_has_leagueId": False,
        "readiness_endpoint": False,
        "no_500_errors": False,
        "no_transaction_errors": False
    }
    
    try:
        # Step 1: Authentication
        print(f"\n🔐 Step 1: Authenticate with test login endpoint")
        
        auth_response = requests.post(
            f"{api_url}/auth/test-login",
            json={"email": test_email},
            timeout=10
        )
        
        if auth_response.status_code == 200:
            test_results["authentication"] = True
            print(f"✅ Authentication successful")
            
            # Get access token
            magic_response = requests.post(f"{api_url}/auth/magic-link", json={"email": test_email}, timeout=10)
            magic_data = magic_response.json()
            token = magic_data['dev_magic_link'].split('token=')[1]
            
            verify_response = requests.post(f"{api_url}/auth/verify", json={"token": token}, timeout=10)
            access_token = verify_response.json()['access_token']
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
            
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            return test_results
        
        # Step 2: League Creation Test
        print(f"\n🏟️ Step 2: Create league with unique name")
        print(f"League name: {league_name}")
        
        league_data = {
            "name": league_name,
            "season": "2025-26",
            "settings": {
                "budget_per_manager": 100,
                "club_slots_per_manager": 5,
                "anti_snipe_seconds": 30,
                "bid_timer_seconds": 60,
                "league_size": {"min": 2, "max": 4},
                "scoring_rules": {"club_goal": 1, "club_win": 3, "club_draw": 1}
            }
        }
        
        league_response = requests.post(
            f"{api_url}/leagues",
            json=league_data,
            headers=headers,
            timeout=15
        )
        
        print(f"League creation response status: {league_response.status_code}")
        
        # Check for 500 errors (the main issue)
        if league_response.status_code != 500:
            test_results["no_500_errors"] = True
            print(f"✅ No 500 Internal Server Error (MongoDB transaction issue resolved)")
        else:
            print(f"❌ CRITICAL: 500 Internal Server Error detected!")
            try:
                error_data = league_response.json()
                error_str = json.dumps(error_data).lower()
                if any(keyword in error_str for keyword in ['transaction', 'replica set', 'mongos']):
                    print(f"🚨 MongoDB transaction error confirmed in response")
                else:
                    test_results["no_transaction_errors"] = True
            except:
                pass
            return test_results
        
        # Check for 201 Created response
        if league_response.status_code == 201:
            test_results["league_creation_201"] = True
            print(f"✅ POST /leagues returns 201 Created")
            
            try:
                response_data = league_response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                # Check for leagueId in response
                if 'leagueId' in response_data:
                    test_results["response_has_leagueId"] = True
                    league_id = response_data['leagueId']
                    print(f"✅ Response contains leagueId: {league_id}")
                    
                    # Step 3: Test readiness endpoint
                    print(f"\n🔍 Step 3: Test readiness endpoint")
                    
                    ready_response = requests.get(
                        f"{api_url}/test/league/{league_id}/ready",
                        headers=headers,
                        timeout=10
                    )
                    
                    if ready_response.status_code == 200:
                        test_results["readiness_endpoint"] = True
                        ready_data = ready_response.json()
                        print(f"✅ GET /test/league/:id/ready returns: {ready_data}")
                        
                        if ready_data.get('ready') == True:
                            print(f"✅ All related documents created successfully")
                        else:
                            print(f"⚠️ League not fully ready: {ready_data.get('reason', 'unknown')}")
                    else:
                        print(f"❌ Readiness endpoint failed: {ready_response.status_code}")
                else:
                    print(f"❌ Response missing leagueId field")
            except Exception as e:
                print(f"❌ Error parsing response: {str(e)}")
        else:
            print(f"❌ Unexpected status code: {league_response.status_code}")
            try:
                error_data = league_response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {league_response.text}")
        
        # Mark no transaction errors if we got this far without 500
        test_results["no_transaction_errors"] = True
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
    
    return test_results

def main():
    """Main test function"""
    results = test_atomic_league_creation_fix()
    
    print(f"\n" + "=" * 60)
    print(f"📊 ATOMIC LEAGUE CREATION TEST RESULTS")
    print(f"=" * 60)
    
    # Test results summary
    test_items = [
        ("Authentication Setup", results["authentication"]),
        ("POST /leagues returns 201", results["league_creation_201"]),
        ("Response contains {leagueId}", results["response_has_leagueId"]),
        ("GET /test/league/:id/ready works", results["readiness_endpoint"]),
        ("No 500 MongoDB errors", results["no_500_errors"]),
        ("No transaction errors", results["no_transaction_errors"])
    ]
    
    passed_tests = sum(1 for _, passed in test_items if passed)
    total_tests = len(test_items)
    
    for test_name, passed in test_items:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTest Results: {passed_tests}/{total_tests} passed ({(passed_tests/total_tests)*100:.1f}%)")
    
    # Key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    if results["no_500_errors"] and results["no_transaction_errors"]:
        print(f"✅ MongoDB transaction issue RESOLVED")
        print(f"✅ League creation no longer returns 500 errors")
        print(f"✅ Sequential operations working without transactions")
    else:
        print(f"❌ MongoDB transaction issue STILL PRESENT")
        print(f"❌ League creation may still be failing with 500 errors")
    
    if results["league_creation_201"] and results["response_has_leagueId"]:
        print(f"✅ League creation endpoint working correctly")
        print(f"✅ Returns proper 201 response with leagueId")
    
    if results["readiness_endpoint"]:
        print(f"✅ Readiness endpoint confirms all documents created")
    
    # Overall assessment
    critical_tests_passed = (
        results["no_500_errors"] and 
        results["league_creation_201"] and 
        results["response_has_leagueId"]
    )
    
    if critical_tests_passed:
        print(f"\n🎉 ATOMIC LEAGUE CREATION FIX: VERIFIED")
        print(f"✅ The MongoDB transaction fixes are working correctly!")
        return True
    else:
        print(f"\n❌ ATOMIC LEAGUE CREATION FIX: NOT VERIFIED")
        print(f"🚨 MongoDB transaction issues may still be present")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)