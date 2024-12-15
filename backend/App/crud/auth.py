from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from App import models
from App.utils.auth import hash_password, verify_password
from App.schemas import UserType, UserCreate, UserUpdate, PasswordChange
from fastapi import HTTPException, status

class UserManager:
    def __init__(self):
        self.userid = None

    def get_user_by_email(self, db: Session, email: str) -> Optional[models.AuthUser]:
        """Get user by email."""
        return db.query(models.AuthUser).filter(models.AuthUser.email == email).first()

    def get_user_by_id(self, db: Session, user_id: UUID) -> Optional[models.AuthUser]:
        """Get user by ID."""
        return db.query(models.AuthUser).filter(models.AuthUser.userid == user_id).first()

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[models.AuthUser]:
        """Authenticate user with email and password."""
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        if not user.is_active:
            return None
        return user

    def create_user(self, db: Session, user_data: UserCreate) -> Optional[models.AuthUser]:
        """Create a new user."""
        try:
            # Check if user already exists
            if self.get_user_by_email(db, user_data.email):
                return None

            # Create new user
            new_user = models.AuthUser(
                firstname=user_data.firstname,
                lastname=user_data.lastname,
                email=user_data.email,
                user_type=user_data.user_type.value,
                password=hash_password(user_data.password),
                is_active=True,
                is_verified=False
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            self.userid = new_user.userid
            return new_user

        except Exception as e:
            print(f"Error creating user: {e}")
            db.rollback()
            return None

    def create_or_update_user(self, db: Session, user_data: UserCreate) -> Optional[models.AuthUser]:
        """Create a new user or update existing unverified user."""
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(db, user_data.email)
            
            if existing_user:
                # If user exists and is verified, return None (conflict)
                if existing_user.is_verified:
                    return None
                
                # If user exists but is not verified, update their data
                existing_user.firstname = user_data.firstname
                existing_user.lastname = user_data.lastname
                existing_user.user_type = user_data.user_type.value
                existing_user.password = hash_password(user_data.password)
                existing_user.is_active = True
                existing_user.is_verified = False
                existing_user.signup_timestamp = datetime.utcnow()
                
                db.commit()
                db.refresh(existing_user)
                
                self.userid = existing_user.userid
                return existing_user
            else:
                # Create new user
                new_user = models.AuthUser(
                    firstname=user_data.firstname,
                    lastname=user_data.lastname,
                    email=user_data.email,
                    user_type=user_data.user_type.value,
                    password=hash_password(user_data.password),
                    is_active=True,
                    is_verified=False
                )
                
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                self.userid = new_user.userid
                return new_user

        except Exception as e:
            print(f"Error creating or updating user: {e}")
            db.rollback()
            return None

    def update_user(self, db: Session, user_id: UUID, user_update: UserUpdate) -> Optional[models.AuthUser]:
        """Update user information."""
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                return None

            update_data = user_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            db.commit()
            db.refresh(user)
            return user

        except Exception as e:
            print(f"Error updating user: {e}")
            db.rollback()
            return None

    def change_password(self, db: Session, user_id: UUID, password_change: PasswordChange) -> bool:
        """Change user password."""
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                return False

            # Verify current password
            if not verify_password(password_change.current_password, user.password):
                return False

            # Update password
            user.password = hash_password(password_change.new_password)
            db.commit()
            return True

        except Exception as e:
            print(f"Error changing password: {e}")
            db.rollback()
            return False

    def deactivate_user(self, db: Session, user_id: UUID) -> bool:
        """Deactivate a user account."""
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                return False

            user.is_active = False
            db.commit()
            return True

        except Exception as e:
            print(f"Error deactivating user: {e}")
            db.rollback()
            return False

    def update_last_login(self, db: Session, user_id: UUID) -> bool:
        """Update user's last login timestamp."""
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                return False

            user.last_login = datetime.utcnow()
            db.commit()
            return True

        except Exception as e:
            print(f"Error updating last login: {e}")
            db.rollback()
            return False

    def get_users_by_type(self, db: Session, user_type: UserType) -> List[models.AuthUser]:
        """Get all users of a specific type."""
        return db.query(models.AuthUser).filter(models.AuthUser.user_type == user_type.value).all()

    def get_all_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.AuthUser]:
        """Get all users with pagination."""
        return db.query(models.AuthUser).offset(skip).limit(limit).all()

class RefreshTokenManager:
    def __init__(self):
        pass

    def create_refresh_token(self, db: Session, user_id: UUID, token: str, expires_at: datetime) -> Optional[models.RefreshToken]:
        """Create a refresh token record."""
        try:
            refresh_token = models.RefreshToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at
            )
            db.add(refresh_token)
            db.commit()
            db.refresh(refresh_token)
            return refresh_token

        except Exception as e:
            print(f"Error creating refresh token: {e}")
            db.rollback()
            return None

    def get_refresh_token(self, db: Session, token: str) -> Optional[models.RefreshToken]:
        """Get refresh token by token string."""
        return db.query(models.RefreshToken).filter(
            and_(
                models.RefreshToken.token == token,
                models.RefreshToken.is_revoked == False,
                models.RefreshToken.expires_at > datetime.utcnow()
            )
        ).first()

    def revoke_refresh_token(self, db: Session, token: str) -> bool:
        """Revoke a refresh token."""
        try:
            refresh_token = self.get_refresh_token(db, token)
            if not refresh_token:
                return False

            refresh_token.is_revoked = True
            db.commit()
            return True

        except Exception as e:
            print(f"Error revoking refresh token: {e}")
            db.rollback()
            return False

    def revoke_all_user_tokens(self, db: Session, user_id: UUID) -> bool:
        """Revoke all refresh tokens for a user."""
        try:
            db.query(models.RefreshToken).filter(
                models.RefreshToken.user_id == user_id
            ).update({"is_revoked": True})
            db.commit()
            return True

        except Exception as e:
            print(f"Error revoking user tokens: {e}")
            db.rollback()
            return False

class ActivityLogManager:
    def __init__(self):
        pass

    def create_activity_log(self, db: Session, user_id: UUID, ip_address: str, 
                           user_agent: str = None, action: str = "LOGIN") -> Optional[models.ActivityLog]:
        """Create an activity log entry."""
        try:
            activity_log = models.ActivityLog(
                userid=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                action=action
            )
            db.add(activity_log)
            db.commit()
            db.refresh(activity_log)
            return activity_log

        except Exception as e:
            print(f"Error creating activity log: {e}")
            db.rollback()
            return None

    def get_user_activity_logs(self, db: Session, user_id: UUID, limit: int = 50) -> List[models.ActivityLog]:
        """Get activity logs for a user."""
        return db.query(models.ActivityLog).filter(
            models.ActivityLog.userid == user_id
        ).order_by(models.ActivityLog.login_timestamp.desc()).limit(limit).all()

if __name__ == "__main__":
    dbmgr = UserManager()
