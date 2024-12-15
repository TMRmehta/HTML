from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from uuid import UUID
import secrets
from App.models import PasswordResetToken, AuthUser
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordResetManager:
    def create_reset_token(self, db: Session, user_id: UUID) -> str:
        """Create a new password reset token for a user."""
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        # Set expiration time (1 hour from now)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Create reset token record
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(reset_token)
        db.commit()
        db.refresh(reset_token)
        
        return token
    
    def get_reset_token(self, db: Session, token: str) -> PasswordResetToken:
        """Get reset token by token string."""
        return db.query(PasswordResetToken).filter(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        ).first()
    
    def reset_password(self, db: Session, token: str, new_password: str) -> bool:
        """Reset user's password using the token."""
        reset_token = self.get_reset_token(db, token)
        
        if not reset_token:
            return False
        
        # Mark token as used
        reset_token.is_used = True
        
        # Update user's password
        user = db.query(AuthUser).filter(AuthUser.userid == reset_token.user_id).first()
        if user:
            # Hash the new password
            hashed_password = pwd_context.hash(new_password)
            user.password = hashed_password
            db.commit()
            return True
        
        return False
    
    def get_user_by_token(self, db: Session, token: str) -> AuthUser:
        """Get user associated with reset token."""
        reset_token = self.get_reset_token(db, token)
        if reset_token:
            return db.query(AuthUser).filter(AuthUser.userid == reset_token.user_id).first()
        return None
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired reset tokens."""
        expired_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_tokens)
        for token in expired_tokens:
            db.delete(token)
        
        db.commit()
        return count
    
    def get_user_reset_status(self, db: Session, user_id: UUID) -> dict:
        """Get user's reset token status."""
        # Check if user has any pending (unused) reset tokens
        pending_token = db.query(PasswordResetToken).filter(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        ).first()
        
        return {
            "has_pending_token": pending_token is not None
        }
