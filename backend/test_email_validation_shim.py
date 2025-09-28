"""
Unit tests for email validation shim
Tests both valid and invalid email addresses as specified in requirements
"""

import pytest
from utils.email_validation import is_valid_email, get_email_validator_info

class TestEmailValidationShim:
    """Test the email validation shim functionality"""
    
    def test_valid_emails(self):
        """Test valid email addresses"""
        valid_emails = [
            "a+b@sub.example.co.uk",
            "user_name-1@domain.io",
            "test@example.com",
            "user.with.dots@domain.com",
            "user+tag@sub.domain.tld",
            "first.last@subdomain.example.org",
            "user123@test-domain.co.uk"
        ]
        
        for email in valid_emails:
            is_valid, error_msg = is_valid_email(email)
            assert is_valid, f"Email '{email}' should be valid, but got error: {error_msg}"
            assert error_msg is None, f"Valid email '{email}' should not have error message"
    
    def test_invalid_emails(self):
        """Test invalid email addresses"""
        invalid_emails = [
            "bad@@domain.com",  # Double @
            "no-tld@domain",    # No TLD
            "x@",               # Incomplete domain
            "",                 # Empty string
            "plainaddress",     # No @ symbol
            "@domain.com",      # No local part
            "user@",            # No domain
            "user name@domain.com",  # Space in local part
            "user@domain .com", # Space in domain
            ".user@domain.com", # Leading dot in local
            "user.@domain.com", # Trailing dot in local
            "user@.domain.com", # Leading dot in domain
            "user@domain.com.", # Trailing dot in domain
        ]
        
        for email in invalid_emails:
            is_valid, error_msg = is_valid_email(email)
            assert not is_valid, f"Email '{email}' should be invalid"
            assert error_msg is not None, f"Invalid email '{email}' should have error message"
            assert isinstance(error_msg, str), f"Error message should be string, got {type(error_msg)}"
    
    def test_none_and_empty_inputs(self):
        """Test None and empty inputs"""
        test_cases = [
            None,
            "",
            "   ",  # Only whitespace
        ]
        
        for case in test_cases:
            is_valid, error_msg = is_valid_email(case)
            assert not is_valid, f"Input '{case}' should be invalid"
            assert error_msg is not None, f"Input '{case}' should have error message"
    
    def test_non_string_inputs(self):
        """Test non-string inputs"""
        test_cases = [
            123,
            [],
            {},
            True,
        ]
        
        for case in test_cases:
            is_valid, error_msg = is_valid_email(case)
            assert not is_valid, f"Input '{case}' (type: {type(case)}) should be invalid"
            assert error_msg is not None, f"Input '{case}' should have error message"
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        edge_cases = [
            ("user@domain.c", False),    # TLD too short (but this might be valid depending on validator)
            ("a@b.co", True),            # Minimal valid email
            ("test@sub.domain.co.uk", True),  # Multiple subdomains
            ("user+tag+more@domain.com", True),  # Multiple plus signs
            ("user@domain-with-hyphens.com", True),  # Hyphenated domain
        ]
        
        for email, expected_valid in edge_cases:
            is_valid, error_msg = is_valid_email(email)
            if expected_valid:
                assert is_valid, f"Email '{email}' should be valid, but got error: {error_msg}"
            else:
                assert not is_valid, f"Email '{email}' should be invalid"
    
    def test_whitespace_handling(self):
        """Test whitespace handling"""
        test_cases = [
            ("  test@example.com  ", True),   # Leading/trailing spaces should be stripped
            ("test @example.com", False),     # Space in local part
            ("test@ example.com", False),     # Space in domain part
            ("test@example .com", False),     # Space in domain
        ]
        
        for email, expected_valid in test_cases:
            is_valid, error_msg = is_valid_email(email)
            if expected_valid:
                assert is_valid, f"Email '{email}' should be valid after whitespace handling, but got error: {error_msg}"
            else:
                assert not is_valid, f"Email '{email}' should be invalid due to internal whitespace"
    
    def test_get_email_validator_info(self):
        """Test email validator info function"""
        info = get_email_validator_info()
        
        assert isinstance(info, dict), "get_email_validator_info should return a dict"
        assert "has_email_validator" in info, "Info should contain has_email_validator"
        assert "fallback_mode" in info, "Info should contain fallback_mode"
        assert isinstance(info["has_email_validator"], bool), "has_email_validator should be boolean"
        assert isinstance(info["fallback_mode"], bool), "fallback_mode should be boolean"
        
        # Check consistency
        assert info["fallback_mode"] == (not info["has_email_validator"]), "fallback_mode should be opposite of has_email_validator"
        
        # Check version info if email_validator is available
        if info["has_email_validator"]:
            assert "email_validator_version" in info, "Should have version info when email_validator is available"
            assert isinstance(info["email_validator_version"], str), "Version should be string"
    
    def test_return_type_consistency(self):
        """Test that return types are consistent"""
        test_emails = [
            "valid@example.com",
            "invalid@@example.com",
            "",
            None
        ]
        
        for email in test_emails:
            result = is_valid_email(email)
            assert isinstance(result, tuple), f"Result should be tuple for email: {email}"
            assert len(result) == 2, f"Result should be 2-tuple for email: {email}"
            
            is_valid, error_msg = result
            assert isinstance(is_valid, bool), f"First element should be bool for email: {email}"
            assert error_msg is None or isinstance(error_msg, str), f"Second element should be None or str for email: {email}"
            
            # If valid, error_msg should be None
            if is_valid:
                assert error_msg is None, f"Valid email should have None error message: {email}"
            else:
                assert error_msg is not None, f"Invalid email should have error message: {email}"

if __name__ == "__main__":
    # Run basic tests if executed directly
    import sys
    
    print("Running email validation shim tests...")
    
    # Test valid emails
    valid_emails = ["a+b@sub.example.co.uk", "user_name-1@domain.io"]
    for email in valid_emails:
        is_valid, error_msg = is_valid_email(email)
        print(f"✅ {email}: {is_valid} (error: {error_msg})")
        assert is_valid, f"Should be valid: {email}"
    
    # Test invalid emails  
    invalid_emails = ["bad@@domain.com", "no-tld", "x@"]
    for email in invalid_emails:
        is_valid, error_msg = is_valid_email(email)
        print(f"❌ {email}: {is_valid} (error: {error_msg})")
        assert not is_valid, f"Should be invalid: {email}"
    
    # Test info
    info = get_email_validator_info()
    print(f"📋 Email validator info: {info}")
    
    print("✅ All basic tests passed!")