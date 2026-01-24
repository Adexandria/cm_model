from datetime import datetime, timedelta, timezone
from fastapi import Cookie, Depends
from typing import Optional, Annotated
from passlib.context import CryptContext
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
from api.models.user import DbUser
from api import crud
from exception import unauthorizedException, notFoundException, badRequestException
import os
import logging
import pyotp
import time
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer(auto_error=True)

SECRET_KEY = os.getenv("SECRET_KEY")
V1_SECRET_KEY = os.getenv("V1_SECRET_KEY")
V1_ALGORITHM = os.getenv("V1_ALGORITHM")
TWO_FACTOR = os.getenv("TWO_FACTOR_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRY_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(): 
    """Create a JWT access token."""
    encoded_jwt = jwt.encode({},key=V1_SECRET_KEY, algorithm=V1_ALGORITHM)
    return encoded_jwt

def create_access_token_with_expiry(data: dict) -> str:
    """Create a JWT access token with an expiry time."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRY_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_two_factor_token(username:str, is_authenticated: bool) -> str:
    """Create a JWT token for two-factor authentication."""
    to_encode = {
        "sub": username,
        "is_authenticated": str(is_authenticated)
    }
    expire = datetime.now(timezone.utc) + timedelta(minutes=3)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, TWO_FACTOR, algorithm=ALGORITHM)
    return encoded_jwt
    
def generate_two_factor_secret(email: str) -> tuple[str, str]:
    """Generate a TOTP secret for two-factor authentication."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    return secret, totp.provisioning_uri(name=email, issuer_name="Content Moderation API")

def generate_refresh_token() -> str:
    """Generate a simple refresh token."""
    return pwd_context.hash(str(time.time()))

def generate_refresh_token_expiry() -> datetime:
    """Generate an expiry time for the refresh token."""
    refresh_token = datetime.now() + timedelta(days=REFRESH_TOKEN_DAYS)
    return pwd_context.hash(str(refresh_token))

def generate_email_confirmation_token(userId, email) -> str:
    """Generate a JWT token for email confirmation."""
    to_encode = {
        "sub": str(userId),
        "email": str(email)
    }
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_password_reset_token(userId, email) -> str:
    """Generate a JWT token for email confirmation."""
    to_encode = {
        "sub": str(userId),
        "email": str(email)
    }
    expire = datetime.now(timezone.utc) + timedelta(minutes=20)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password_reset_token(token: str, db: Session = Depends(get_db)) -> DbUser:
    """Verify password reset token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            raise unauthorizedException()
        
        user = crud.get_user_by_id_email(db, user_id=user_id, email=email)
        if user is None:
            raise unauthorizedException()
        return user
    except JWTError:
        raise unauthorizedException()

def generate_api_key() -> str:
    """Generate a simple API key."""
    return pwd_context.hash(str(time.time()))

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> DbUser:
    """Retrieve the current user based on the JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") 
        if username is None:
            raise unauthorizedException()
    except JWTError:
        raise unauthorizedException()
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise notFoundException()
    return user


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> DbUser:
    """Retrieve the current user based on the JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") 
        role: str = payload.get("role")
        if role != "admin":
            raise unauthorizedException(message="Admin privileges required.")
        if username is None:
            raise unauthorizedException()
    except JWTError:
        raise unauthorizedException()
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise notFoundException()
    return user




async def authenticate_user_by_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate user using JWT token."""
    try:
        _ = jwt.decode(credentials.credentials, V1_SECRET_KEY, algorithms=[V1_ALGORITHM])
        return True
    except JWTError:
        raise unauthorizedException()

    
async def verify_email_token(email_token: str, db: Session = Depends(get_db)) -> DbUser:
    """Verify email confirmation token and retrieve user."""
    try:
        print("email_token:", email_token)
        payload = jwt.decode(email_token, SECRET_KEY, algorithms=[ALGORITHM])
        logging.debug("Verified email token; payload keys: %s", list(payload.keys()))
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            logging.warning("Email token missing claims: sub=%s email=%s", user_id, bool(email))
            raise unauthorizedException()
    except JWTError as e:
        logging.exception("Invalid email confirmation token: %s", str(e))
        raise unauthorizedException()
    
    user = crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise notFoundException()
    
    crud.confirm_user_email(db, user)
    
    return user

async def get_otp_verifier(twofa_token: Annotated[str | None, Cookie()] = None, db: Session = Depends(get_db)) -> DbUser:
    """Verify if user has been authenticated and requires two-factor authentication"""
    try:
        payload = jwt.decode(twofa_token, TWO_FACTOR, algorithms=[ALGORITHM])
        username: str = payload.get("sub") 
        is_authenticated: bool = payload.get("is_authenticated")
        if username is None or not is_authenticated :
            raise unauthorizedException()
    except JWTError:
        raise unauthorizedException()
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise notFoundException()
    
    if not user.is_two_factor_enabled:
        raise badRequestException(message="Two-factor authentication is not enabled for this user.")
    
    return user

async def get_user_by_api_key(api_key: str, db: Session = Depends(get_db)) -> DbUser:
    """Retrieve user based on API key."""
    user = crud.get_user_by_api_key(db, api_key=api_key)
    if not user:
        raise unauthorizedException(message="Invalid API key.")
    
    crud.update_user_request_count(db=db, user=user)

    return user