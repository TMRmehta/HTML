from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, TIMESTAMP, text, Boolean
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from Database.database import Base
import uuid
from datetime import datetime

class AuthUser(Base):
    __tablename__ = "auth_users"

    userid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=False)
    user_type = Column(String(20), nullable=False) 
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    signup_timestamp = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    last_login = Column(TIMESTAMP)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.userid", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    is_revoked = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("AuthUser", back_populates="refresh_tokens")

# Add relationship to AuthUser model
AuthUser.refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class UserLog(Base):
    __tablename__ = "user_logs"

    userid = Column(UUID(as_uuid=True), ForeignKey("auth_users.userid", ondelete="CASCADE"), primary_key=True)
    total_logins = Column(Integer, default=0)
    input_tokens_used = Column(BigInteger, default=0)
    output_tokens_used = Column(BigInteger, default=0)
    last_login_date = Column(TIMESTAMP)

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    userid = Column(UUID(as_uuid=True), ForeignKey("auth_users.userid", ondelete="CASCADE"), nullable=False)
    ip_address = Column(INET, nullable=False)
    login_timestamp = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    user_agent = Column(String(500))
    action = Column(String(100))

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.userid", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    is_used = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("AuthUser")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.userid", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    is_used = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("AuthUser")  