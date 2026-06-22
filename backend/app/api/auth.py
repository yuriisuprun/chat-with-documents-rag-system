"""Authentication endpoints."""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from jose import JWTError, jwt
from app.config import settings
from app.schemas import AdminLoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


@router.post("/login", response_model=TokenResponse)
def login(request: AdminLoginRequest) -> TokenResponse:
    """Admin login endpoint."""
    # Verify credentials
    if request.username != settings.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create token
    access_token = create_access_token(
        data={"sub": settings.ADMIN_USERNAME}
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600
    )
