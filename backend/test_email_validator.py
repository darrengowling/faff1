"""
Unit Tests for Email Validator
Tests comprehensive email validation with various valid/invalid cases
"""

import pytest
from email_utils import EmailValidator, is_valid_email, validate_email, normalize_email

class TestEmailValidator:
    """Test cases for EmailValidator class"""
    
    def test_valid_emails(self):
        """Test various valid email formats"""
        valid_emails = [
            # Basic formats
            "user@domain.com",
            "test@example.org",
            "admin@site.net",
            
            # Plus-addressing
            "user+tag@domain.com",
            "a+b@sub.example.co.uk",
            "test+123@gmail.com",
            "user+very-long-tag@domain.io",
            
            # Underscores and hyphens in local part
            "user_name@domain.com",
            "user-name@domain.com", 
            "user_name-1@domain.io",
            "test_user+tag@example.com",
            
            # Subdomains
            "user@sub.domain.com",
            "admin@mail.google.com",
            "test@a.b.c.d.example.com",
            
            # Numbers and special characters
            "user123@domain123.com",
            "123user@domain.com",
            "user.name@domain.com",
            "user'test@domain.com",
            
            # International domains
            "user@domain.co.uk",
            "test@example.info",
            "admin@site.museum",
            
            # Edge cases
            "a@b.co",
            "very.long.email.address@very.long.domain.name.com",
        ]
        
        for email in valid_emails:
            assert EmailValidator.is_valid_email(email), f"Email should be valid: {email}"
            is_valid, error = EmailValidator.validate_email_detailed(email)
            assert is_valid, f"Email should be valid: {email} - Error: {error}"
    
    def test_invalid_emails(self):
        """Test various invalid email formats"""
        invalid_emails = [
            # Basic format issues
            "",
            " ",
            "invalid",
            "no-at-symbol",
            "missing-domain@",
            "@missing-local.com",
            
            # Multiple @ symbols
            "user@domain@extra.com",
            "bad@@x.com",
            "user@@domain.com",
            
            # No TLD
            "user@domain",
            "test@localhost",
            "no-tld@nodot",
            
            # Invalid TLD
            "user@domain.c",
            "test@domain.123",
            "user@domain.c0m",
            
            # Consecutive dots
            "user..name@domain.com",
            "user@domain..com",
            "user@domain.com.",
            ".user@domain.com",
            "user.@domain.com",
            
            # Invalid characters
            "user@domain.com ",  # trailing space
            " user@domain.com",  # leading space
            "user name@domain.com",  # space in local
            "user@domain .com",  # space in domain
            "user<>@domain.com",  # invalid chars
            "user@domain-.com",   # hyphen at start/end of label
            "user@-domain.com",   # hyphen at start of domain
            
            # Too long
            "a" * 65 + "@domain.com",  # local part too long
            "user@" + "a" * 254 + ".com",  # domain too long
            
            # Empty parts
            "@domain.com",
            "user@",
            "@",
        ]
        
        for email in invalid_emails:
            assert not EmailValidator.is_valid_email(email), f"Email should be invalid: {email}"
            is_valid, error = EmailValidator.validate_email_detailed(email)
            assert not is_valid, f"Email should be invalid: {email}"
            assert error, f"Error message should be provided for invalid email: {email}"
    
    def test_edge_case_emails(self):
        """Test edge cases and boundary conditions"""
        # RFC limit testing
        max_local = "a" * 64  # Exactly at limit
        assert EmailValidator.is_valid_email(f"{max_local}@domain.com")
        
        too_long_local = "a" * 65  # Over limit
        assert not EmailValidator.is_valid_email(f"{too_long_local}@domain.com")
        
        # Domain label limit
        max_label = "a" * 63
        assert EmailValidator.is_valid_email(f"user@{max_label}.com")
        
        too_long_label = "a" * 64
        assert not EmailValidator.is_valid_email(f"user@{too_long_label}.com")
    
    def test_plus_addressing_detection(self):
        """Test plus-addressing detection"""
        plus_emails = [
            "user+tag@domain.com",
            "test+123@example.org",
            "a+b+c@domain.io"
        ]
        
        regular_emails = [
            "user@domain.com",
            "test123@example.org",
            "user-name@domain.io"
        ]
        
        for email in plus_emails:
            assert EmailValidator.supports_plus_addressing(email), f"Should detect plus-addressing: {email}"
        
        for email in regular_emails:
            assert not EmailValidator.supports_plus_addressing(email), f"Should not detect plus-addressing: {email}"
    
    def test_email_normalization(self):
        """Test email normalization"""
        test_cases = [
            ("User@Domain.COM", "user@domain.com"),
            ("  test@example.org  ", "test@example.org"),
            ("MixedCase+Tag@DOMAIN.co.uk", "mixedcase+tag@domain.co.uk"),
            ("", ""),
            (None, "")
        ]
        
        for input_email, expected in test_cases:
            result = EmailValidator.normalize_email(input_email)
            assert result == expected, f"Normalization failed: {input_email} -> {result} (expected {expected})"
    
    def test_domain_extraction(self):
        """Test domain extraction"""
        test_cases = [
            ("user@domain.com", "domain.com"),
            ("test@SUB.EXAMPLE.ORG", "sub.example.org"),
            ("user+tag@mail.google.com", "mail.google.com"),
            ("invalid-email", ""),
            ("", ""),
            ("@domain.com", "domain.com"),  # Even with invalid format
        ]
        
        for email, expected_domain in test_cases:
            result = EmailValidator.extract_domain(email)
            assert result == expected_domain, f"Domain extraction failed: {email} -> {result} (expected {expected_domain})"
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly"""
        valid_email = "test@example.com"
        invalid_email = "invalid@"
        
        # Test is_valid_email convenience function
        assert is_valid_email(valid_email)
        assert not is_valid_email(invalid_email)
        
        # Test validate_email convenience function
        is_valid, error = validate_email(valid_email)
        assert is_valid
        assert error == ""
        
        is_valid, error = validate_email(invalid_email)
        assert not is_valid
        assert error != ""
        
        # Test normalize_email convenience function
        assert normalize_email("Test@EXAMPLE.COM") == "test@example.com"
    
    def test_comprehensive_valid_cases(self):
        """Comprehensive test of documented valid email cases"""
        comprehensive_valid = [
            # Specification examples
            "simple@example.com",
            "very.common@example.com",
            "disposable.style.email.with+symbol@example.com",
            "x@example.com",
            "example@s.example",
            
            # Plus-addressing variations
            "user+tag@example.com",
            "user+multiple+tags@example.com", 
            "a+b@sub.example.co.uk",  # From requirements
            "user_name-1@domain.io",  # From requirements
            
            # Subdomain variations
            "admin@mail.example.com",
            "user@deep.sub.domain.example.org",
            
            # Special characters in local part
            "test.email+tag@example.com",
            "user_name@example.com",
            "user-name@example.com",
            "user123@example.com",
        ]
        
        for email in comprehensive_valid:
            assert EmailValidator.is_valid_email(email), f"Should be valid: {email}"
    
    def test_comprehensive_invalid_cases(self):
        """Comprehensive test of documented invalid email cases"""
        comprehensive_invalid = [
            # From requirements
            "bad@@x",  # Double @
            "no-tld@domain",  # No TLD
            
            # Additional invalid cases
            "plainaddress",
            "@missingdomain.com",
            "missing@domain",
            "missing.domain.com",
            "missing@.com",
            "missing@domain.",
            "spaces in@email.com",
            "email@spaces in.com",
            "email@-domain.com",
            "email@domain-.com",
            "",
            " ",
            None,
        ]
        
        for email in comprehensive_invalid:
            assert not EmailValidator.is_valid_email(email), f"Should be invalid: {email}"


if __name__ == "__main__":
    # Run basic tests if executed directly
    validator = EmailValidator()
    
    print("Testing valid emails...")
    valid_tests = [
        "user@domain.com",
        "a+b@sub.example.co.uk", 
        "user_name-1@domain.io"
    ]
    
    for email in valid_tests:
        result = validator.is_valid_email(email)
        print(f"  {email}: {'✅ VALID' if result else '❌ INVALID'}")
    
    print("\nTesting invalid emails...")
    invalid_tests = [
        "bad@@x",
        "no-tld",
        "user@domain",
        ""
    ]
    
    for email in invalid_tests:
        result = validator.is_valid_email(email)
        print(f"  {email}: {'❌ VALID (ERROR!)' if result else '✅ INVALID'}")
    
    print("\n✅ Basic email validator tests complete!")