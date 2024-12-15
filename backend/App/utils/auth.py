
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from App.config import JWT_CONFIG
from App.schemas import TokenData, UserType

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def is_password_strong(password: str) -> bool:
    """Check if the password is strong enough."""
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isalpha() for char in password):
        return False
    return True


def is_email_valid(email: str) -> bool:
    """Check if the email is valid."""
    import re
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + \
            timedelta(minutes=JWT_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"])

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, JWT_CONFIG["SECRET_KEY"], algorithm=JWT_CONFIG["ALGORITHM"])
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + \
        timedelta(days=JWT_CONFIG["REFRESH_TOKEN_EXPIRE_DAYS"])
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, JWT_CONFIG["SECRET_KEY"], algorithm=JWT_CONFIG["ALGORITHM"])
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify and decode a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_CONFIG["SECRET_KEY"], algorithms=[
                             JWT_CONFIG["ALGORITHM"]])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        user_type: str = payload.get("user_type")
        token_type_from_payload: str = payload.get("type")

        if user_id is None or email is None:
            raise credentials_exception

        if token_type_from_payload != token_type:
            raise credentials_exception

        return TokenData(
            user_id=user_id,
            email=email,
            user_type=UserType(user_type) if user_type else None
        )
    except JWTError:
        raise credentials_exception


def get_user_id_from_token(token: str) -> str:
    """Extract user ID from the token."""
    token_data = verify_token(token)
    return str(token_data.user_id)


def create_tokens(user_id: str, email: str, user_type: UserType) -> Dict[str, str]:
    """Create both access and refresh tokens for a user."""
    access_token = create_access_token(
        data={"sub": user_id, "email": email, "user_type": user_type.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": user_id, "email": email, "user_type": user_type.value}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": JWT_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"] * 60
    }


def check_user_permissions(user_type: UserType, required_roles: list[UserType]) -> bool:
    """Check if user has required permissions based on role hierarchy."""
    role_hierarchy = {
        UserType.PATIENT: 1,
        UserType.RESEARCHER: 2
    }

    user_level = role_hierarchy.get(user_type, 0)
    return any(role_hierarchy.get(role, 0) <= user_level for role in required_roles)
