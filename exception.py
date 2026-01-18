from fastapi import Depends, HTTPException, status


def badRequestException(message: str="Bad Request"):
    """Exception raised for bad requests with a 400 status code."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )
def unauthorizedException(message: str="Unauthorized"):
    """Exception raised for unauthorized access with a 401 status code."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )
def forbiddenException(message: str="Forbidden"):
    """Exception raised for forbidden access with a 403 status code."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message
    )
def notFoundException(message: str="Not Found"):
    """Exception raised when a resource is not found with a 404 status code."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=message
    )

def serverErrorException(message: str="Internal Server Error"):
    """Exception raised for internal server errors with a 500 status code."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )
    