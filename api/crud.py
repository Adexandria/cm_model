from sqlalchemy.orm import Session
from passlib.context import CryptContext
import random
from api.models.user import RequestCount, UserCreate, DbUser, DbUserRole, ApiKey, LoginAttempt
from typing import Optional
from enum import Enum
import pyotp
from datetime import datetime, timedelta
import os

from exception import badRequestException, notFoundException

from dotenv import load_dotenv

load_dotenv()

EXPIRY_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
MAX_REQUESTS_PER_DAY = int(os.getenv("MAX_REQUESTS_PER_DAY"))
MAX_API_KEYS_PER_USER = int(os.getenv("MAX_API_KEYS_PER_USER"))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS"))
ATTEMPT_WINDOW_MINUTES = int(os.getenv("ATTEMPT_WINDOW_MINUTES"))

class Roles(Enum):
    ADMIN = "admin"
    USER = "user"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_username(db: Session, username: str) -> Optional[DbUser]:
    """Retrieve a user by their username."""
    return db.query(DbUser).filter(DbUser.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[DbUser]:
    """Retrieve a user by their email."""
    return db.query(DbUser).filter(DbUser.email == email).first()

def create_user(db: Session, user: UserCreate, is_admin: bool) -> DbUser:
    """Create a new user with hashed password."""
    if is_admin:
        role_name = Roles.ADMIN.value
    else:
        role_name = Roles.USER.value

    hashed_password = pwd_context.hash(user.password)
    db_user = DbUser(

        username=user.username,
        email=user.email,
        password_hashed=hashed_password,
        last_login=datetime.now()
    )

    db.add(db_user)

    user_role = db.query(DbUserRole).filter(DbUserRole.name == role_name).first()
    if user_role:
        db_user.roles.append(user_role)
    else: 
        create_role(db)
        user_role = db.query(DbUserRole).filter(DbUserRole.name == role_name).first()
        db_user.roles.append(user_role)

    request_count = RequestCount(
        user_id=db_user.id,
        count=0,
        last_request=datetime.now(),
    )
    db_user.request_count = request_count
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_v1(db: Session, username:str, password:str, email:str, is_admin: bool) -> DbUser:
    """Create a new user with hashed password."""
    if is_admin:
        role_name = Roles.ADMIN.value
    else:
        role_name = Roles.USER.value

    hashed_password = pwd_context.hash(password)
    db_user = DbUser(

        username=username,
        email=email,
        password_hashed=hashed_password,
        last_login=datetime.now()
    )

    db.add(db_user)

    user_role = db.query(DbUserRole).filter(DbUserRole.name == role_name).first()
    if user_role:
        db_user.roles.append(user_role)
    else: 
        create_role(db)
        user_role = db.query(DbUserRole).filter(DbUserRole.name == role_name).first()
        db_user.roles.append(user_role)

    request_count = RequestCount(
        user_id=db_user.id,
        count=0,
        last_request=datetime.now(),
    )
    db_user.request_count = request_count
    db.commit()
    db.refresh(db_user)
    return db_user

def Update_last_login(db: Session, user: DbUser) -> DbUser:
    """Update the last login time for a user."""
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    return user

def Set_refresh_token(db: Session, user: DbUser, refresh_token: str) -> DbUser:
    """Set the refresh token and its expiry time for a user."""
    user.refresh_token = refresh_token
    user.expiry_time = datetime.now() + timedelta(minutes=EXPIRY_MINUTES)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_refresh_token_with_expiry(db: Session,refresh_token: str) -> Optional[DbUser]:
    """Retrieve a user by their refresh token and ensure the token hasn't expired."""
    return (
        db.query(DbUser)
        .filter(
            DbUser.refresh_token == refresh_token,
            DbUser.expiry_time > datetime.now()
        )
        .first()
    )


def get_user_by_refresh_token(db: Session, refresh_token: str) -> Optional[DbUser]:
    """Retrieve a user by their refresh token."""
    return (
        db.query(DbUser)
        .filter(
            DbUser.refresh_token == refresh_token
        )
        .first()
    )


def get_user_by_id(db: Session, user_id: int) -> Optional[DbUser]:
    """Retrieve a user by their ID."""
    return db.query(DbUser).filter(DbUser.id == user_id).first()

def enable_two_factor_auth(db: Session, user: DbUser, secret: str) -> DbUser:
    """Enable two-factor authentication for a user."""
    user.is_two_factor_enabled = True
    user.authentication_secret = secret
    db.commit()
    db.refresh(user)
    return user

def disable_two_factor_auth(db: Session, user: DbUser) -> DbUser:
    """Disable two-factor authentication for a user."""
    user.is_two_factor_enabled = False
    user.authentication_secret = None
    db.commit()
    db.refresh(user)
    return user 

def change_user_password(db: Session, user: DbUser, new_password: str) -> DbUser:
    """Change a user's password."""
    hashed_password = pwd_context.hash(new_password)
    user.password_hashed = hashed_password
    db.commit()
    db.refresh(user)
    return user

def confirm_user_email(db: Session, user: DbUser) -> DbUser:
    """Confirm a user's email address."""
    user.is_email_confirmed = True
    db.commit()
    db.refresh(user)
    return user

def verify_two_factor_token(user: DbUser, token: str) -> bool:
    """Verify a TOTP token for a user."""
    if not user.is_two_factor_enabled or not user.authentication_secret:
        return False
    totp = pyotp.TOTP(user.authentication_secret)
    return totp.verify(token)


def lock_user_account(db: Session, user: DbUser) -> DbUser:
    """Lock a user's account."""
    user.is_locked = True
    db.commit()
    db.refresh(user)
    return user

def unlock_user_account(db: Session, user: DbUser) -> DbUser:
    """Unlock a user's account."""
    user.is_locked = False
    db.commit()
    db.refresh(user)
    return user


def Update_user_login_attempts(db: Session, username: str) -> int:
    """Update and retrieve the number of failed login attempts for a user in the 5 minute window."""
    is_max_attempts_reached = False

    five_minutes_ago = datetime.now() - timedelta(minutes=ATTEMPT_WINDOW_MINUTES)
    attempt = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.username == username,
            LoginAttempt.attempt_time > five_minutes_ago
        )
        .first()
    )
    if attempt:
        attempt.no_attempts += 1

        if(attempt.no_attempts >= MAX_ATTEMPTS):
            is_max_attempts_reached = True

        attempt.attempt_time =  datetime.now()
           
    else:
        attempt = LoginAttempt(
            username=username,
            attempt_time=datetime.now()
        )
        db.add(attempt)
    
    db.commit()
    db.refresh(attempt)
    return attempt.no_attempts, is_max_attempts_reached
  
def create_role(db: Session) -> DbUserRole:
    """Create a new user role if and only if it doesn't exist."""             
    has_values = db.query(DbUserRole).count() > 0
    if has_values:
        return 
    
    for role in Roles:
        db_role = DbUserRole(name=role.value, description=f"{role.value} role")
        db.add(db_role)

    db.commit()
    db.refresh(db_role)

def authenticate_user(db: Session, username: str, password: str) -> Optional[DbUser]:
    """Authenticate a user by their username and password."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not pwd_context.verify(password, user.password_hashed):
        return None
    return user

def set_user_api_key(db: Session, user_id: int, api_key: str):
    """Set the API key for a user."""
    current_api_keys = get_api_keys_by_user(db, user_id)

    if len(current_api_keys) >= MAX_API_KEYS_PER_USER:
        raise badRequestException(message="Maximum number of API keys reached.")
    
    new_api_key = ApiKey(
        key=api_key,
        user_id=user_id
    )
    db.add(new_api_key)

    a, b = random.sample(range(1, 11), 2)
    new_api_key.name = f"api_key_{a}{b}"

    db.commit()
    db.refresh(new_api_key)

def get_authenticated_user_by_api_key(db: Session, user_id: int, api_key: str) -> Optional[DbUser]:
    """Retrieve the DbUser for a given `user_id` and `api_key`."""
    return (
        db.query(DbUser)
        .join(ApiKey, ApiKey.user_id == DbUser.id)
        .filter(ApiKey.name == api_key, ApiKey.user_id == user_id)
        .first()
    )

def get_user_by_api_key(db: Session, api_key: str) -> Optional[DbUser]:
    """Retrieve the DbUser for a given `api_key`."""
    return (
        db.query(DbUser)
        .join(ApiKey, ApiKey.user_id == DbUser.id)
        .filter(ApiKey.key == api_key)
        .first()
    )

def get_api_keys_by_user(db: Session, user_id: int) -> list[str]:
    """Retrieve all API keys for a given user."""
    api_keys =  db.query(ApiKey).filter(ApiKey.user_id == user_id).all()
    return [api_key.name for api_key in api_keys]


def delete_api_key(db: Session, user_id: int, api_key_name: str) -> None:
    """Delete an API key for a user by its name."""
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.user_id == user_id, ApiKey.name == api_key_name)
        .first()
    )
    if api_key:
        db.delete(api_key)  
        db.commit()

    else:
        raise notFoundException(message="API key not found.")

def update_user_request_count(db: Session, user: DbUser):
    """Update request count for a user."""

    if(user.request_count.last_request.date() < datetime.now().date()):
        user.request_count.count = 0
    else:
        if(user.request_count.count >= MAX_REQUESTS_PER_DAY):
            raise badRequestException(message="Maximum daily request limit reached.")
        
    user.request_count.count +=  1
    user.request_count.last_request = datetime.now()
    
    db.commit()
    db.refresh(user)