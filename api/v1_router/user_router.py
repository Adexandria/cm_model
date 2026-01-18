from fastapi import APIRouter, Depends, Body
from api.models.user import UsernameResponse
from sqlalchemy.orm import Session
from database import get_db
from api import auth
from api import crud
from exception import notFoundException, serverErrorException, unauthorizedException


router = APIRouter(
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

@router.get("/user", response_model=UsernameResponse, responses={401: {"description": "Unauthorized"},404: {"description": "Not Found"}, 500: {"description": "Server Error"}})
async def get_user(username: str, db: Session = Depends(get_db), is_authenticated: bool = Depends(auth.authenticate_user_by_token)):
    """Get user details by username."""
    try:
        if not is_authenticated:
            raise unauthorizedException()
        
        db_user = crud.get_user_by_username(db, username=username)
        
        if not db_user:
            raise notFoundException(message="User not found")
        
        return UsernameResponse(    
            username=db_user.username,
            email=db_user.email,
            roles=[role.name for role in db_user.roles],
            password_hashed=db_user.password_hashed
        )
    except Exception as e:
        raise serverErrorException(message=str(e))
    

