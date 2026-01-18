from fastapi import APIRouter, Depends
from api.models.user import LoginResponse, AccessRefreshTokenResponse, AccessTokenResponse
from sqlalchemy.orm import Session
from database import get_db
from api import auth
from api import crud
from exception import badRequestException, unauthorizedException, serverErrorException

router = APIRouter(
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register-user",response_model=LoginResponse, responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def register_user(email: str, username: str, password: str, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        db_user = crud.get_user_by_username(db, username=username)

        if db_user:
            raise badRequestException(message="Username already registered")
        
        db_user = crud.get_user_by_email(db, email=email)
        if db_user:
            raise badRequestException(message="Email already registered")
        
        new_user = crud.create_user_v1(db=db, email=email, username=username, password=password, is_admin=False)

        return LoginResponse(
            username=new_user.username,
            email=new_user.email
        )
    except Exception as e:
        raise serverErrorException(message=str(e))
    

@router.post("/register-admin",response_model=LoginResponse, responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def register_admin(email: str, username: str, password: str, db: Session = Depends(get_db)):
    """Register a new admin user."""
    try:
        db_user = crud.get_user_by_username(db, username=username)

        if db_user:
            raise badRequestException(message="Username already registered")
        
        db_user = crud.get_user_by_email(db, email=email)
        if db_user:
            raise badRequestException(message="Email already registered")
        
        new_user = crud.create_user_v1(db=db, email=email, username=username, password=password, is_admin=True)

        return LoginResponse(
            username=new_user.username,
            email=new_user.email
        )
    except Exception as e:
        raise serverErrorException(message=str(e))
   

@router.post("/login",response_model=AccessRefreshTokenResponse, responses={400: {"description": "Bad Request"}, 401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
async def login(username: str, password: str, db: Session = Depends(get_db)):
    """Login endpoint placeholder."""
    try:
        user = crud.authenticate_user(db, username, password)
        if not user:
            raise unauthorizedException(message="Invalid username or password")
        
        access_token = auth.create_access_token()
        refresh_token = auth.generate_refresh_token()
        user = crud.Set_refresh_token(db, user, refresh_token)

        return AccessRefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token
        )
    except Exception as e:
        raise serverErrorException(message=str(e))


    
@router.get("/token",response_model=AccessTokenResponse, responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def token(refresh_token: str, db: Session = Depends(get_db)):
    """Endpoint to retrieve token from cookies."""
    try:
        if not refresh_token:
            raise badRequestException(message="No token found")
    
        user = crud.get_user_by_refresh_token(db, refresh_token=refresh_token)
        if not user:
            raise badRequestException(message="Invalid or expired refresh token")
    
        access_token = auth.create_access_token()

        return AccessTokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        raise serverErrorException(message=str(e))
