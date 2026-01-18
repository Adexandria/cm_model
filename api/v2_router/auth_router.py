import os
from fastapi import APIRouter, Cookie, Response
from datetime import datetime
from api.models.user import LoginResponse, TokenResponse,UserCreate,SignUpRequest, PasswordResetRequest,DbUser, ChangePasswordRequest
from sqlalchemy.orm import Session
from database import get_db
from api import crud, auth
from fastapi import Depends
from exception import badRequestException, unauthorizedException, serverErrorException
from typing import Annotated
from email_service import send_email, Subject, Template
import qrcode
import io

from dotenv import load_dotenv

load_dotenv()

MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS"))
BACKEND_URL = os.getenv("BACKEND_URL")

router = APIRouter(
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register-user", responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        db_user = crud.get_user_by_username(db, username=user.username)
        if db_user:
            raise badRequestException(message="Username already registered")
    
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise badRequestException(message="Email already registered")
    
        new_user = crud.create_user(db=db, user=user, is_admin=False)
        email_token = auth.generate_email_confirmation_token(userId=new_user.id,email=new_user.email)
        confirmation_link = f"{BACKEND_URL}/api/v2/authentication/confirm-email?email_token={email_token}"
        context = {
        "username": new_user.username,
        "verification_url": confirmation_link
        }

        send_email(to_email=new_user.email, subject=Subject.EMAIL_CONFIRMATION, template=Template.EMAIL_CONFIRMATION, context=context)
        
        user = LoginResponse(
            username=new_user.username,
            email=new_user.email
        )

        return user
    except Exception as e:
        raise serverErrorException(message=str(e))

@router.post("/register-admin", responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def register_admin(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new admin user."""
    try:
        db_user = crud.get_user_by_username(db, username=user.username)
        if db_user:
            raise badRequestException(message="Username already registered")
    
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise badRequestException(message="Email already registered")
    
        new_user = crud.create_user(db=db, user=user, is_admin=True)
        email_token = auth.generate_email_confirmation_token(userId=new_user.id,email=new_user.email)
        confirmation_link = f"{BACKEND_URL}/api/v2/authentication/confirm-email?email_token={email_token}"

        context = {
        "username": new_user.username,
        "verification_url": confirmation_link
        }

        send_email(to_email=new_user.email, subject=Subject.EMAIL_CONFIRMATION, template=Template.EMAIL_CONFIRMATION, context=context)    

        user = LoginResponse(
        username=new_user.username,
        email=new_user.email
        )
        return user
    except Exception as e:
        raise serverErrorException(message=str(e))

@router.get("/confirm-email", responses={400: {"description": "Bad Request"},401:{"description": "Unauthorized"}, 500: {"description": "Server Error"}})
async def confirm_email(email_token: str, db: Session = Depends(get_db)):
    """Endpoint to confirm user email."""
    try:
        _ = await auth.verify_email_token(email_token=email_token, db=db)
        return {
            "message": "Email confirmed successfully."
        }
    except Exception as e:
        raise serverErrorException(message=str(e))

@router.post("/login", responses={400: {"description": "Bad Request"}, 401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
async def login(user: SignUpRequest, response: Response, db: Session = Depends(get_db)):
    """Login endpoint."""
    try:
        attempts, is_max_attempts_reached = crud.Update_user_login_attempts(db, user.username)
        db_user = crud.authenticate_user(db, user.username, user.password)

        if is_max_attempts_reached:
            user = crud.get_user_by_username(db, user.username)
            context = {
                "Company_Name": "Content Moderation API V2",
                "Time_Stamp" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Unlock_Link": f"{BACKEND_URL}/api/v2/authentication/forgot-password?email={user.email}"
            }
            send_email(to_email=user.email, subject=Subject.MAX_LOGIN_ATTEMPTS, template=Template.MAX_LOGIN_ATTEMPTS, context=context)
            raise unauthorizedException(message="Maximum login attempts exceeded. Please try again later.")
        
        if not db_user:
            raise unauthorizedException(message="Invalid username or password, Only" + str(MAX_ATTEMPTS - attempts) + " attempts left.")

        if not db_user.is_email_confirmed:
            email_token = auth.generate_email_confirmation_token(userId=db_user.id,email=db_user.email)
            confirmation_link = f"{BACKEND_URL}/api/v2/authentication/confirm-email?email_token={email_token}"
            send_email(to_email=db_user.email, subject=Subject.EMAIL_CONFIRMATION, template=Template.EMAIL_CONFIRMATION, context= {
            "username": db_user.username,
            "verification_url": confirmation_link
            })
            raise badRequestException(message="Email address is not confirmed. Please confirm your email before logging in.")
    
        if db_user.is_two_factor_enabled:
            token = auth.create_two_factor_token(username=db_user.username, is_authenticated=True)
            response.set_cookie(key="twofa_token", value=token, httponly=True)
            return {
                "message": "Two-factor authentication required",
                "requires_2fa": True
            }

        access_token = auth.create_access_token_with_expiry(
        data={"sub": db_user.username, "role": db_user.roles[0].name})
    
        refresh_token = auth.generate_refresh_token_expiry()

        crud.Set_refresh_token(db, db_user, refresh_token)

        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

        db_user = crud.Update_last_login(db, db_user)

        context = {
        "username": db_user.username,
        "login_time": db_user.last_login.strftime("%Y-%m-%d %H:%M:%S")
        }

        send_email(to_email=db_user.email, subject=Subject.LOGIN, template=Template.LOGIN, context=context)

        return {
        "message": "Login successful",
        "access_token": access_token
            }
    except Exception as e:
        raise serverErrorException(message=str(e))
   
@router.get("/token", responses={400: {"description": "Bad Request"}, 401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
async def token(refresh_token: Annotated[str | None, Cookie()] = None, db: Session = Depends(get_db)):
    """Endpoint to retrieve token from cookies."""
    try:
        if not refresh_token:
            raise badRequestException(message="No token found in cookies")
    
        user = crud.get_user_by_refresh_token_with_expiry(db, refresh_token=refresh_token)

        if not user:
            raise badRequestException(message="Invalid or expired refresh token")
        access_token = auth.create_access_token_with_expiry(
        data={"sub": user.username, "role": user.roles[0].name}
        )

        return TokenResponse(token=access_token)

    except Exception as e:
        raise serverErrorException(message=str(e))

@router.post("/two-factor/setup", responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def setup_two_factor_auth(current_user: DbUser = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Setup two-factor authentication for the current user."""
    try:
        if current_user.is_two_factor_enabled:
            raise badRequestException(message="Two-factor authentication is already enabled.")
    
        secret, provisioning_uri = auth.generate_two_factor_secret(current_user.email)

        _ = crud.enable_two_factor_auth(db, current_user, secret)

        qr_code = qrcode.make(provisioning_uri)
        img_bye_arr = io.BytesIO()
        qr_code.save(img_bye_arr, format='PNG')
        img_byte_arr = img_bye_arr.getvalue()

        return Response(content=img_byte_arr, media_type="image/png")
    except Exception as e:
        raise serverErrorException(message=str(e))

@router.post("/two-factor/disable", responses={400: {"description": "Bad Request"},401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}}   )
async def disable_two_factor_auth(current_user: DbUser = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Disable two-factor authentication for the current user."""
    try:

        _ = crud.disable_two_factor_auth(db, current_user)

        return {"message": "Two-factor authentication has been disabled."}

    except Exception as e:
        raise serverErrorException(message=str(e))

@router.post("/two-factor/verify", responses={400: {"description": "Bad Request"},401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}}    )
async def verify_two_factor_auth(totp:int, response: Response, current_user: DbUser = Depends(auth.get_otp_verifier), db: Session = Depends(get_db)):
    """Verify two-factor authentication token."""
    try:

        is_valid_token = crud.verify_two_factor_token(current_user, str(totp))
    
        if not is_valid_token:
            raise badRequestException(message="Invalid two-factor authentication token.")

        access_token = auth.create_access_token_with_expiry(
            data={"sub": current_user.username, "role": current_user.roles[0].name})
    
        refresh_token = auth.generate_refresh_token_expiry()

        crud.Set_refresh_token(db, current_user, refresh_token)

        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

        db_user = crud.Update_last_login(db, current_user)

        context = {
        "username": db_user.username,
        "login_time": db_user.last_login.strftime("%Y-%m-%d %H:%M:%S")
        }

        send_email(to_email=db_user.email, subject=Subject.LOGIN, template=Template.LOGIN, context=context)

        result = {
        "message": "Two-factor authentication successful",
        "access_token": access_token
        }
        return result
    except Exception as e:
        raise serverErrorException(message=str(e))
    

@router.post("/change-password", responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def change_password(change_password_request: ChangePasswordRequest, current_user: DbUser = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Change the password for the current user."""
    try:
        is_valid_password = crud.verify_user_password(current_user, change_password_request.current_password)
        if not is_valid_password:
            raise badRequestException(message="Invalid current password.")
        
        if change_password_request.current_password == change_password_request.new_password:
            raise badRequestException(message="New password cannot be the same as the current password.")
        
        _ = crud.change_user_password(db, current_user, change_password_request.new_password)
        return {"message": "Password changed successfully."}
    except Exception as e:
        raise serverErrorException(message=str(e))

@router.get("/forget-password", responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def forget_password(email: str, db: Session = Depends(get_db)):
    """Endpoint to handle forget password requests."""
    try:
        db_user = crud.get_user_by_email(db, email=email)
        if not db_user:
            raise badRequestException(message="Email not found")
        
        reset_token = auth.generate_password_reset_token(userId=db_user.id,email=db_user.email)
        reset_link = f"{BACKEND_URL}/api/v2/authentication/reset-password?reset_token={reset_token}"

        context = {
        "Company_Name": "Content Moderation API V2",
        "Reset_Link": reset_link,
        "Expiration_Time": "20 minutes"
        }

        send_email(to_email=db_user.email, subject=Subject.FORGOT_PASSWORD, template=Template.FORGOT_PASSWORD, context=context)
        return {"message": "Password reset link has been sent to your email."}
    except Exception as e:
        raise serverErrorException(message=str(e))
    
@router.post("/reset-password", responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def reset_password(reset_token: str, password_reset_request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Endpoint to reset password using reset token."""
    try:
        user = await auth.verify_password_reset_token(reset_token=reset_token, db=db)
        _ = crud.change_user_password(db, user, password_reset_request.new_password)
        return {"message": "Password has been reset successfully."}
    except Exception as e:
        raise serverErrorException(message=str(e))

