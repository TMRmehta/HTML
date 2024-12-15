from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from uuid import UUID
import secrets
from App.models import EmailVerificationToken, AuthUser

class EmailVerificationManager:
    def create_verification_token(self, db: Session, user_id: UUID) -> str:
        """Create a new email verification token for a user."""
        # First, invalidate any existing unused tokens for this user
        existing_tokens = db.query(EmailVerificationToken).filter(
            and_(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.is_used == False
            )
        ).all()
        
        for existing_token in existing_tokens:
            existing_token.is_used = True
        
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        # Set expiration time (24 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Create verification token record
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)
        
        return token
    
    def get_verification_token(self, db: Session, token: str) -> EmailVerificationToken:
        """Get verification token by token string."""
        return db.query(EmailVerificationToken).filter(
            and_(
                EmailVerificationToken.token == token,
                EmailVerificationToken.is_used == False,
                EmailVerificationToken.expires_at > datetime.utcnow()
            )
        ).first()
    
    def verify_email(self, db: Session, token: str) -> bool:
        """Verify user's email using the token."""
        verification_token = self.get_verification_token(db, token)
        
        if not verification_token:
            return False
        
        # Mark token as used
        verification_token.is_used = True
        
        # Mark user as verified
        user = db.query(AuthUser).filter(AuthUser.userid == verification_token.user_id).first()
        if user:
            user.is_verified = True
            db.commit()
            return True
        
        return False
    
    def get_user_by_token(self, db: Session, token: str) -> AuthUser:
        """Get user associated with verification token."""
        verification_token = self.get_verification_token(db, token)
        if verification_token:
            return db.query(AuthUser).filter(AuthUser.userid == verification_token.user_id).first()
        return None
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired verification tokens."""
        expired_tokens = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_tokens)
        for token in expired_tokens:
            db.delete(token)
        
        db.commit()
        return count
    
    def get_user_verification_status(self, db: Session, user_id: UUID) -> dict:
        """Get user's verification status and pending tokens."""
        user = db.query(AuthUser).filter(AuthUser.userid == user_id).first()
        if not user:
            return {"verified": False, "has_pending_token": False}
        
        # Check if user has any pending (unused) verification tokens
        pending_token = db.query(EmailVerificationToken).filter(
            and_(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.is_used == False,
                EmailVerificationToken.expires_at > datetime.utcnow()
            )
        ).first()
        
        return {
            "verified": user.is_verified,
            "has_pending_token": pending_token is not None
        }
