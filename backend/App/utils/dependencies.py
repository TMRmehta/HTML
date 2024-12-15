from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from Database.database import SessionLocal
from App.utils.auth import verify_token
from App.schemas import TokenData, UserType
from App.crud.auth import UserManager, RefreshTokenManager

# Security scheme
security = HTTPBearer()

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TokenData:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    token_data = verify_token(token, "access")
    
    # Verify user still exists and is active
    user_manager = UserManager()
    user = user_manager.get_user_by_id(db, UUID(token_data.user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data

def get_current_user_obj(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user object from database."""
    token = credentials.credentials
    token_data = verify_token(token, "access")
    
    user_manager = UserManager()
    user = user_manager.get_user_by_id(db, UUID(token_data.user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_roles(required_roles: List[UserType]):
    """Dependency factory for role-based access control."""
    def role_checker(current_user: TokenData = Depends(get_current_user)):
        if current_user.user_type not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def require_researcher(current_user: TokenData = Depends(get_current_user)):
    """Require researcher role."""
    if current_user.user_type != UserType.RESEARCHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Researcher access required"
        )
    return current_user

def require_patient_or_higher(current_user: TokenData = Depends(get_current_user)):
    """Require patient role or higher (any authenticated user)."""
    return current_user

def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[TokenData]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        token_data = verify_token(token, "access")
        
        # Verify user still exists and is active
        user_manager = UserManager()
        user = user_manager.get_user_by_id(db, UUID(token_data.user_id))
        
        if not user or not user.is_active:
            return None
        
        return token_data
    except:
        return None
