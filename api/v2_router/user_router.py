import os
from fastapi import APIRouter
from api.models.user import DbUser, UserResponse
from api import  auth, crud
from fastapi import Depends
from database import get_db
from exception import serverErrorException, badRequestException
from sqlalchemy.orm import Session

from dotenv import load_dotenv

load_dotenv()

MAX_REQUESTS_PER_DAY = int(os.getenv("MAX_REQUESTS_PER_DAY"))

router = APIRouter(
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me", response_model=UserResponse, responses={500: {"description": "Server Error"}})
async def get_current_user_details(current_user: DbUser = Depends(auth.get_current_user)):
    """Get details of the current authenticated user."""
    try:
        return UserResponse(
            username=current_user.username,
            email=current_user.email,
            api_keys=[api_key.name for api_key in current_user.api_keys],
            last_login=current_user.last_login.isoformat(),
            api_key_quota=current_user.request_count.count,
            max_requests_per_day=MAX_REQUESTS_PER_DAY,
            is_locked=current_user.is_locked
        )
    except Exception as e:
        raise serverErrorException(message=str(e))  
    
@router.post("/users/{username}/unlock-account", responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def unlock_user_account(username: str, current_user: DbUser = Depends(auth.get_current_admin), db: Session = Depends(get_db)):
    """Unlock the current user's account."""
    try:
        db_user = auth.get_user_by_username(db, username)
        if not db_user:
            raise badRequestException(message="User not found")
        
        if not db_user.is_locked:
            return {"message": "Account is not locked."}        
        
        crud.unlock_user_account(db, db_user)

        return {"message": "Account has been unlocked successfully."}
    
    except Exception as e:
        raise serverErrorException(message=str(e))