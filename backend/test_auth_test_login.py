#!/usr/bin/env python3
"""
Unit Tests for Test-Only Login Endpoint
Tests the /auth/test-login endpoint behavior with different ALLOW_TEST_LOGIN settings
"""

import pytest
import os
import asyncio
from httpx import AsyncClient
from server import fastapi_app
from database import initialize_database, client

# Test configuration
TEST_EMAIL = "test-login-unit@example.com"

class TestAuthTestLogin:
    
    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """Set up test database before each test"""
        await initialize_database()
        
    def test_endpoint_disabled_when_flag_false(self):
        """Test that the endpoint returns 403 when ALLOW_TEST_LOGIN=false"""
        
        async def run_test():
            # Temporarily set environment variable to false
            original_value = os.environ.get("ALLOW_TEST_LOGIN")
            os.environ["ALLOW_TEST_LOGIN"] = "false"
            
            try:
                async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
                    response = await ac.post("/api/auth/test-login", json={"email": TEST_EMAIL})
                
                # Should return 403 Forbidden
                assert response.status_code == 403
                assert "disabled" in response.json()["detail"].lower()
                print("✅ Test passed: Endpoint disabled when flag false")
                
            finally:
                # Restore original environment variable
                if original_value is not None:
                    os.environ["ALLOW_TEST_LOGIN"] = original_value
                else:
                    os.environ.pop("ALLOW_TEST_LOGIN", None)
        
        asyncio.run(run_test())
    
    def test_endpoint_enabled_when_flag_true(self):
        """Test that the endpoint works when ALLOW_TEST_LOGIN=true"""
        
        async def run_test():
            # Set environment variable to true
            original_value = os.environ.get("ALLOW_TEST_LOGIN")
            os.environ["ALLOW_TEST_LOGIN"] = "true"
            
            try:
                async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
                    response = await ac.post("/api/auth/test-login", json={"email": TEST_EMAIL})
                
                # Should return 200 with token
                assert response.status_code == 200
                data = response.json()
                
                assert "access_token" in data
                assert "user" in data
                assert data["user"]["email"] == TEST_EMAIL
                assert data["user"]["verified"] is True
                assert "Test login successful" in data["message"]
                
                print("✅ Test passed: Endpoint enabled when flag true")
                
            finally:
                # Restore original environment variable
                if original_value is not None:
                    os.environ["ALLOW_TEST_LOGIN"] = original_value
                else:
                    os.environ.pop("ALLOW_TEST_LOGIN", None)
        
        asyncio.run(run_test())
    
    def test_endpoint_requires_email(self):
        """Test that the endpoint returns 400 when email is missing"""
        
        async def run_test():
            # Set environment variable to true
            original_value = os.environ.get("ALLOW_TEST_LOGIN")
            os.environ["ALLOW_TEST_LOGIN"] = "true"
            
            try:
                async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
                    # Test with no email
                    response = await ac.post("/api/auth/test-login", json={})
                
                assert response.status_code == 400
                assert "email is required" in response.json()["detail"].lower()
                
                # Test with empty email
                response = await ac.post("/api/auth/test-login", json={"email": ""})
                
                assert response.status_code == 400
                assert "email is required" in response.json()["detail"].lower()
                
                print("✅ Test passed: Endpoint requires email")
                
            finally:
                # Restore original environment variable
                if original_value is not None:
                    os.environ["ALLOW_TEST_LOGIN"] = original_value
                else:
                    os.environ.pop("ALLOW_TEST_LOGIN", None)
        
        asyncio.run(run_test())
    
    def test_endpoint_creates_user_if_not_exists(self):
        """Test that the endpoint creates a new user if they don't exist"""
        
        async def run_test():
            # Set environment variable to true
            original_value = os.environ.get("ALLOW_TEST_LOGIN")
            os.environ["ALLOW_TEST_LOGIN"] = "true"
            
            new_user_email = f"new-user-{asyncio.get_event_loop().time()}@example.com"
            
            try:
                # Verify user doesn't exist first
                from database import db
                existing_user = await db.users.find_one({"email": new_user_email})
                assert existing_user is None, "User should not exist before test"
                
                async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
                    response = await ac.post("/api/auth/test-login", json={"email": new_user_email})
                
                # Should create user and return 200
                assert response.status_code == 200
                data = response.json()
                
                assert data["user"]["email"] == new_user_email
                assert data["user"]["verified"] is True
                
                # Verify user was created in database
                created_user = await db.users.find_one({"email": new_user_email})
                assert created_user is not None, "User should be created in database"
                assert created_user["verified"] is True
                
                print("✅ Test passed: Endpoint creates user if not exists")
                
            finally:
                # Restore original environment variable
                if original_value is not None:
                    os.environ["ALLOW_TEST_LOGIN"] = original_value
                else:
                    os.environ.pop("ALLOW_TEST_LOGIN", None)
                    
                # Clean up created user
                from database import db
                await db.users.delete_one({"email": new_user_email})
        
        asyncio.run(run_test())

def run_all_tests():
    """Run all test methods"""
    test_instance = TestAuthTestLogin()
    
    print("🧪 Running Test-Only Login Endpoint Tests...")
    
    try:
        test_instance.test_endpoint_disabled_when_flag_false()
        test_instance.test_endpoint_enabled_when_flag_true()
        test_instance.test_endpoint_requires_email()
        test_instance.test_endpoint_creates_user_if_not_exists()
        
        print("🎉 All test-only login tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)