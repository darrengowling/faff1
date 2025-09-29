#!/usr/bin/env python3
"""
Debug authentication system
"""

import requests
import json

def test_auth_system():
    base_url = "https://magic-league.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Test known protected endpoint
    endpoints = [
        'auth/me',  # Should require auth
        'leagues',  # Should require auth
        'clubs/my-clubs/test-league-id',  # Should require auth
    ]
    
    print("Testing authentication system:")
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
    test_auth_system()