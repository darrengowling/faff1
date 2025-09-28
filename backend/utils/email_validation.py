"""
Email validation shim with safe fallback
Provides a consistent interface for email validation that works with or without external packages
"""

import re
from typing import Tuple

try:
    from email_validator import validate_email as _validate_email, EmailNotValidError as _EmailError
    HAS_EMAIL_VALIDATOR = True
except Exception:
    HAS_EMAIL_VALIDATOR = False

# Fallback regex pattern for basic email validation
_FALLBACK = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")

def is_valid_email(addr: str) -> Tuple[bool, str | None]:
    """
    Validate email address with safe fallback
    
    Args:
        addr: Email address to validate
        
    Returns:
        Tuple[bool, str | None]: (is_valid, error_message)
        - (True, None) if email is valid
        - (False, error_message) if email is invalid
    """
    if not addr or not isinstance(addr, str):
        return False, "Email is required"
    
    addr = addr.strip()
    if not addr:
        return False, "Email cannot be empty"
    
    if HAS_EMAIL_VALIDATOR:
        try:
            # Use email-validator package with deliverability check disabled for speed
            _validate_email(addr, check_deliverability=False)
            return True, None
        except _EmailError as e:
            return False, str(e)
        except Exception as e:
            # Fallback to regex if email-validator fails unexpectedly
            ok = bool(_FALLBACK.fullmatch(addr))
            return ok, None if ok else f"Invalid email format: {str(e)}"
    else:
        # Fallback regex validation
        ok = bool(_FALLBACK.fullmatch(addr))
        return ok, None if ok else "Invalid email format"

def get_email_validator_info() -> dict:
    """
    Get information about the email validator being used
    
    Returns:
        dict: Information about email validator status
    """
    info = {
        "has_email_validator": HAS_EMAIL_VALIDATOR,
        "fallback_mode": not HAS_EMAIL_VALIDATOR
    }
    
    if HAS_EMAIL_VALIDATOR:
        try:
            import email_validator
            info["email_validator_version"] = getattr(email_validator, '__version__', 'unknown')
        except Exception:
            info["email_validator_version"] = 'unknown'
    
    return info