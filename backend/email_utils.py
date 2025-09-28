"""
Shared Email Validation Utility
Robust email validation supporting plus-addressing, subdomains, hyphens, and modern TLDs
"""

import re
from typing import Tuple

class EmailValidator:
    """
    Comprehensive email validator that handles modern email formats
    Supports: plus-addressing, subdomains, hyphens, international domains
    """
    
    # Comprehensive email regex pattern
    # Supports: user+tag@sub.domain.tld, user_name-1@domain.io, user'test@domain.com etc.
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+\'-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # More detailed pattern for thorough validation
    DETAILED_EMAIL_PATTERN = re.compile(
        r'^(?P<local>[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+)*)@'
        r'(?P<domain>(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)$'
    )
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Validate email address with comprehensive rules
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        
        # Basic format check
        if not EmailValidator.EMAIL_PATTERN.match(email):
            return False
        
        # Additional checks
        return EmailValidator._additional_checks(email)
    
    @staticmethod
    def validate_email_detailed(email: str) -> Tuple[bool, str]:
        """
        Validate email with detailed error message
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return False, "Email is required"
        
        # Check for leading/trailing whitespace before stripping
        if email != email.strip():
            return False, "Email cannot have leading or trailing whitespace"
        
        if not email:
            return False, "Email cannot be empty"
        
        if len(email) > 254:  # RFC 5321 limit
            return False, "Email address is too long (max 254 characters)"
        
        if email.count('@') != 1:
            return False, "Email must contain exactly one @ symbol"
        
        local_part, domain_part = email.split('@')
        
        # Validate local part (before @)
        local_valid, local_error = EmailValidator._validate_local_part(local_part)
        if not local_valid:
            return False, local_error
        
        # Validate domain part (after @)
        domain_valid, domain_error = EmailValidator._validate_domain_part(domain_part)
        if not domain_valid:
            return False, domain_error
        
        return True, ""
    
    @staticmethod
    def _additional_checks(email: str) -> bool:
        """Additional validation checks"""
        try:
            # Check for consecutive dots
            if '..' in email:
                return False
            
            # Check for leading/trailing spaces
            if email != email.strip():
                return False
            
            local_part, domain_part = email.split('@')
            
            # Check for leading/trailing dots in local part
            if local_part.startswith('.') or local_part.endswith('.'):
                return False
            
            # Check for spaces
            if ' ' in email:
                return False
            
            # Check domain has valid TLD
            if '.' not in domain_part:
                return False
            
            # Check for hyphens at start/end of domain labels
            labels = domain_part.split('.')
            for label in labels:
                if label.startswith('-') or label.endswith('-'):
                    return False
                if not label:  # Empty label
                    return False
            
            # Check length limits
            if len(local_part) > 64:
                return False
            if len(domain_part) > 253:
                return False
            
            # TLD validation
            tld = labels[-1]
            if len(tld) < 2 or not tld.isalpha():
                return False
            
            # Check for invalid characters in local part (add apostrophe for RFC compliance)
            allowed_local_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&\'*+-/=?^_`{|}~.')
            if not all(c in allowed_local_chars for c in local_part):
                return False
            
            # Check domain label lengths
            for label in labels:
                if len(label) > 63:  # RFC 1035 limit
                    return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def _validate_local_part(local_part: str) -> Tuple[bool, str]:
        """Validate the local part (before @) of email"""
        if not local_part:
            return False, "Local part cannot be empty"
        
        if len(local_part) > 64:  # RFC 5321 limit
            return False, "Local part is too long (max 64 characters)"
        
        if local_part.startswith('.') or local_part.endswith('.'):
            return False, "Local part cannot start or end with a dot"
        
        if '..' in local_part:
            return False, "Local part cannot contain consecutive dots"
        
        # Check allowed characters
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&\'*+-/=?^_`{|}~.')
        if not all(c in allowed_chars for c in local_part):
            return False, "Local part contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def _validate_domain_part(domain_part: str) -> Tuple[bool, str]:
        """Validate the domain part (after @) of email"""
        if not domain_part:
            return False, "Domain part cannot be empty"
        
        if len(domain_part) > 253:  # RFC 1035 limit
            return False, "Domain part is too long (max 253 characters)"
        
        if domain_part.startswith('.') or domain_part.endswith('.'):
            return False, "Domain cannot start or end with a dot"
        
        if domain_part.startswith('-') or domain_part.endswith('-'):
            return False, "Domain cannot start or end with a hyphen"
        
        # Split into labels
        labels = domain_part.split('.')
        
        if len(labels) < 2:
            return False, "Domain must have at least one dot (e.g., domain.com)"
        
        for label in labels:
            label_valid, label_error = EmailValidator._validate_domain_label(label)
            if not label_valid:
                return False, f"Invalid domain label '{label}': {label_error}"
        
        # Check TLD (last label)
        tld = labels[-1]
        if len(tld) < 2:
            return False, "Top-level domain must be at least 2 characters"
        
        if not tld.isalpha():
            return False, "Top-level domain must contain only letters"
        
        return True, ""
    
    @staticmethod
    def _validate_domain_label(label: str) -> Tuple[bool, str]:
        """Validate a single domain label"""
        if not label:
            return False, "Domain label cannot be empty"
        
        if len(label) > 63:  # RFC 1035 limit
            return False, "Domain label is too long (max 63 characters)"
        
        if label.startswith('-') or label.endswith('-'):
            return False, "Domain label cannot start or end with hyphen"
        
        # Check allowed characters (letters, numbers, hyphens)
        if not re.match(r'^[a-zA-Z0-9-]+$', label):
            return False, "Domain label contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def normalize_email(email: str) -> str:
        """
        Normalize email address (lowercase, strip whitespace)
        
        Args:
            email: Email address to normalize
            
        Returns:
            str: Normalized email address
        """
        if not email:
            return ""
        
        return email.strip().lower()
    
    @staticmethod
    def extract_domain(email: str) -> str:
        """
        Extract domain from email address
        
        Args:
            email: Email address
            
        Returns:
            str: Domain part or empty string if invalid
        """
        if not email or '@' not in email:
            return ""
        
        return email.split('@')[1].lower()
    
    @staticmethod
    def supports_plus_addressing(email: str) -> bool:
        """
        Check if email uses plus-addressing (e.g., user+tag@domain.com)
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if email contains plus-addressing
        """
        if not email or '@' not in email:
            return False
        
        local_part = email.split('@')[0]
        return '+' in local_part


# Convenience functions for easy imports
def is_valid_email(email: str) -> bool:
    """Convenience function for email validation"""
    return EmailValidator.is_valid_email(email)

def validate_email(email: str) -> Tuple[bool, str]:
    """Convenience function for detailed email validation"""
    return EmailValidator.validate_email_detailed(email)

def normalize_email(email: str) -> str:
    """Convenience function for email normalization"""
    return EmailValidator.normalize_email(email)