"""
Unit tests for /auth/test-login endpoint idempotency and error handling
"""
import pytest
import asyncio
import os
from httpx import AsyncClient
from backend.server import fastapi_app

# Set up test environment
os.environ["ALLOW_TEST_LOGIN"] = "true"
os.environ["TEST_MODE"] = "true"

class TestAuthTestLogin:
    """Test suite for /auth/test-login endpoint"""
    
    @pytest.mark.asyncio
    async def test_test_login_idempotent(self):
        """Test that calling /auth/test-login twice returns 200 both times"""
        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            email = "test-idempotent@example.com"
            
            # First call
            response1 = await client.post("/api/auth/test-login", json={"email": email})
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["ok"] is True
            assert data1["userId"] is not None
            assert data1["email"] == email
            
            # Second call (should be idempotent)
            response2 = await client.post("/api/auth/test-login", json={"email": email})
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["ok"] is True
            assert data2["userId"] == data1["userId"]  # Same user ID
            assert data2["email"] == email
            
            # Verify cookie is present in both responses
            assert "access_token" in response1.cookies
            assert "access_token" in response2.cookies
            
    @pytest.mark.asyncio
    async def test_test_login_invalid_email(self):
        """Test that invalid email returns 400 with proper error structure"""
        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            
            # Test missing email
            response = await client.post("/api/auth/test-login", json={})
            assert response.status_code == 400
            error_data = response.json()
            assert error_data["detail"]["code"] == "INVALID_EMAIL"
            
            # Test invalid email format
            response = await client.post("/api/auth/test-login", json={"email": "not-an-email"})
            assert response.status_code == 400
            error_data = response.json()
            assert error_data["detail"]["code"] == "INVALID_EMAIL"
            
    @pytest.mark.asyncio
    async def test_test_login_disabled(self):
        """Test that endpoint returns 404 when ALLOW_TEST_LOGIN=false"""
        # Temporarily disable test login
        original_value = os.environ.get("ALLOW_TEST_LOGIN")
        os.environ["ALLOW_TEST_LOGIN"] = "false"
        
        try:
            async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
                response = await client.post("/api/auth/test-login", json={"email": "test@example.com"})
                assert response.status_code == 404
        finally:
            # Restore original value
            if original_value:
                os.environ["ALLOW_TEST_LOGIN"] = original_value
            else:
                os.environ.pop("ALLOW_TEST_LOGIN", None)
                
    @pytest.mark.asyncio
    async def test_test_login_cookie_settings(self):
        """Test that session cookie has proper settings for tests"""
        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            email = "test-cookie@example.com"
            
            response = await client.post("/api/auth/test-login", json={"email": email})
            assert response.status_code == 200
            
            # Check cookie is present and has correct attributes
            cookie = response.cookies.get("access_token")
            assert cookie is not None
            
            # Note: httpx doesn't expose all cookie attributes, but we can verify the cookie exists
            # In a real test environment, we'd check for HttpOnly, SameSite=Lax, etc.