"""
Deterministic Time Provider for Testing
Wraps all time operations to enable controlled time in tests
"""

import os
import threading
from datetime import datetime, timezone
from typing import Optional


class TimeProvider:
    """
    Time provider that can be controlled in test mode.
    In production, uses real system time.
    In test mode, uses controlled time that can be advanced.
    """
    
    def __init__(self):
        self._test_mode = os.environ.get('TEST_MODE', 'false').lower() == 'true'
        self._lock = threading.Lock()
        self._test_time_ms: Optional[int] = None
        
        if self._test_mode:
            # Initialize test time to current time
            self._test_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    @property
    def is_test_mode(self) -> bool:
        """Check if running in test mode"""
        return self._test_mode
    
    def now_ms(self) -> int:
        """Get current time in milliseconds since epoch"""
        if self._test_mode:
            with self._lock:
                return self._test_time_ms
        return int(datetime.now(timezone.utc).timestamp() * 1000)
    
    def now(self) -> datetime:
        """Get current datetime (timezone-aware UTC)"""
        if self._test_mode:
            with self._lock:
                return datetime.fromtimestamp(self._test_time_ms / 1000, tz=timezone.utc)
        return datetime.now(timezone.utc)
    
    def set_time_ms(self, time_ms: int) -> None:
        """Set the current time in test mode (milliseconds since epoch)"""
        if not self._test_mode:
            raise RuntimeError("set_time_ms can only be called in TEST_MODE")
        
        with self._lock:
            self._test_time_ms = time_ms
    
    def advance_time_ms(self, delta_ms: int) -> int:
        """Advance time by delta_ms milliseconds in test mode"""
        if not self._test_mode:
            raise RuntimeError("advance_time_ms can only be called in TEST_MODE")
        
        with self._lock:
            self._test_time_ms += delta_ms
            return self._test_time_ms
    
    def advance_time_seconds(self, delta_seconds: float) -> int:
        """Advance time by delta_seconds in test mode"""
        return self.advance_time_ms(int(delta_seconds * 1000))


# Global time provider instance
time_provider = TimeProvider()


def now() -> datetime:
    """Get current time - use this instead of datetime.now()"""
    return time_provider.now()


def now_ms() -> int:
    """Get current time in milliseconds - use this instead of time.time() * 1000"""
    return time_provider.now_ms()


def is_test_mode() -> bool:
    """Check if running in test mode"""
    return time_provider.is_test_mode


def require_test_mode():
    """Decorator to ensure endpoints are only accessible in TEST_MODE"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not is_test_mode():
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=404,
                    detail="Endpoint not found"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def set_test_time_ms(time_ms: int) -> None:
    """Set test time (TEST_MODE only)"""
    time_provider.set_time_ms(time_ms)


def advance_test_time_ms(delta_ms: int) -> int:
    """Advance test time (TEST_MODE only)"""
    return time_provider.advance_time_ms(delta_ms)


def advance_test_time_seconds(delta_seconds: float) -> int:
    """Advance test time by seconds (TEST_MODE only)"""
    return time_provider.advance_time_seconds(delta_seconds)