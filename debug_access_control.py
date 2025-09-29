#!/usr/bin/env python3
"""
Debug access control for aggregation endpoints
"""

import requests
import json

def test_unauthorized_access():
    base_url = "https://testid-enforcer.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    test_league_id = "2d221d74-ecfa-45fc-b388-4d8671b5637b"
    
    endpoints = [
        f'clubs/my-clubs/{test_league_id}',
        f'fixtures/{test_league_id}',
        f'leaderboard/{test_league_id}',
        f'analytics/head-to-head/{test_league_id}?user1_id=test1&user2_id=test2'
    ]
    
    print("Testing unauthorized access to aggregation endpoints:")
    print("=" * 60)
    
    for endpoint in endpoints:
        url = f"{api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        # No Authorization header
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"Endpoint: {endpoint}")
            print(f"Status: {response.status_code}")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            print("-" * 60)
            
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")
            print("-" * 60)

if __name__ == "__main__":
    test_unauthorized_access()