from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import secrets
import smtplib
import logging

from models import User, UserResponse
from database import db

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
MAGIC_LINK_EXPIRE_MINUTES = 15
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

# Email configuration (for development, we'll log the magic links)
SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@uclauction.com')

def send_email(to_email: str, subject: str, body: str, html_body: str = None) -> bool:
    """Send email using SMTP configuration"""
    try:
        # Check if SMTP is configured
        if not SMTP_SERVER:
            logger.warning(f"SMTP not configured - Email not sent to {to_email}")
            logger.info(f"EMAIL CONTENT for {to_email}:")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {body}")
            return False
            
        # Create message
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        
        # Attach text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Attach HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

def send_invitation_email(email: str, league_name: str, inviter_name: str, invitation_link: str) -> bool:
    """Send league invitation email"""
    subject = f"You're invited to join '{league_name}' league!"
    
    text_body = f"""Hello!

{inviter_name} has invited you to join the '{league_name}' league on Friends of PIFA.

Click the link below to accept your invitation:
{invitation_link}

This invitation will expire in 72 hours.

Best regards,
The Friends of PIFA Team
"""
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb;">You're invited to join a league!</h2>
            
            <p><strong>{inviter_name}</strong> has invited you to join the <strong>'{league_name}'</strong> league on Friends of PIFA.</p>
            
            <div style="margin: 30px 0;">
                <a href="{invitation_link}" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    Accept Invitation
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px;">This invitation will expire in 72 hours.</p>
            
            <hr style="border: 1px solid #eee; margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                Best regards,<br>
                The Friends of PIFA Team
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(email, subject, text_body, html_body)

# Security
security = HTTPBearer(auto_error=False)  # Make optional for cookie fallback
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_magic_link_token(email: str) -> str:
    """Create magic link token"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)
    to_encode = {
        "email": email,
        "exp": expire,
        "type": "magic_link"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_magic_link_token(token: str) -> Optional[str]:
    """Verify magic link token and return email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "magic_link":
            return None
        
        return email
    except JWTError:
        return None

async def send_magic_link_email(email: str, token: str):
    """Send magic link email (for development, we'll just log it)"""
    frontend_url = os.getenv("FRONTEND_URL", "https://livebid-app.preview.emergentagent.com")
    magic_link = f"{frontend_url}/auth/verify?token={token}"
    
    # For development, just log the magic link
    logger.info(f"Magic link for {email}: {magic_link}")
    print(f"\n🔗 Magic Link for {email}:")
    print(f"   {magic_link}\n")
    return

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Get current authenticated user from Bearer token or cookie"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authenticated",
    )
    
    token = None
    
    # Try to get token from Authorization header first
    if credentials:
        token = credentials.credentials
    else:
        # Fallback to cookie for test-login compatibility
        token = request.cookies.get("access_token")
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"_id": user_id})
    if user is None:
        raise credentials_exception
    
    return UserResponse(
        id=user["_id"],
        email=user["email"],
        display_name=user["display_name"],
        verified=user["verified"],
        created_at=user["created_at"]
    )

async def get_current_verified_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current authenticated and verified user"""
    if not current_user.verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user

# Access control helpers
async def check_league_access(user_id: str, league_id: str) -> Optional[str]:
    """Check if user has access to league and return their role"""
    membership = await db.league_memberships.find_one({
        "league_id": league_id,
        "user_id": user_id
    })
    return membership["role"] if membership else None

async def require_league_access(user_id: str, league_id: str) -> str:
    """Require league access and return role"""
    role = await check_league_access(user_id, league_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this league"
        )
    return role

async def require_commissioner_access(user_id: str, league_id: str):
    """Require commissioner access to league"""
    role = await require_league_access(user_id, league_id)
    if role != "commissioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Commissioner access required"
        )

class AccessControl:
    """Access control middleware for league-based operations"""
    
    @staticmethod
    async def league_member(current_user: UserResponse = Depends(get_current_verified_user)):
        """Dependency to ensure user is a league member (role check done per endpoint)"""
        return current_user
    
    @staticmethod
    async def commissioner_only(current_user: UserResponse = Depends(get_current_verified_user)):
        """Dependency for commissioner-only endpoints (league check done per endpoint)"""
        return current_user