from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from uuid import UUID

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Database.database import SessionLocal
from App.schemas import (
    UserLogin, UserCreate, UserRead, UserProfile, TokenResponse, 
    RefreshTokenRequest, RefreshTokenResponse, PasswordChange,
    UserUpdate, UserType, ActivityLogCreate,
    EmailVerificationRequest, EmailVerificationResponse,
    ResendVerificationRequest, ResendVerificationResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse
)
from App.crud.auth import UserManager, RefreshTokenManager, ActivityLogManager
from App.crud.email_verification import EmailVerificationManager
from App.crud.password_reset import PasswordResetManager
from App.services.email_service import email_service
from App.utils.auth import create_tokens, verify_token
from App.utils.dependencies import get_current_user, get_current_user_obj, require_roles
from App.schemas import TokenData

router = APIRouter(prefix="/auth", tags=["authentication"])

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT tokens."""
    user_manager = UserManager()
    activity_manager = ActivityLogManager()
    
    # Authenticate user
    user = user_manager.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in. Check your email for a verification link.",
        )
    
    # Create tokens
    tokens = create_tokens(
        user_id=str(user.userid),
        email=user.email,
        user_type=UserType(user.user_type)
    )
    
    # Create refresh token record
    refresh_manager = RefreshTokenManager()
    expires_at = datetime.utcnow() + timedelta(days=7)  # Match JWT_CONFIG
    refresh_manager.create_refresh_token(
        db, user.userid, tokens["refresh_token"], expires_at
    )
    
    # Update last login
    user_manager.update_last_login(db, user.userid)
    
    # Log activity
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    activity_manager.create_activity_log(
        db, user.userid, client_ip, user_agent, "LOGIN"
    )
    
    return tokens

@router.post("/signup", response_model=UserRead)
async def signup(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user or update existing unverified user."""
    user_manager = UserManager()
    activity_manager = ActivityLogManager()
    email_verification_manager = EmailVerificationManager()
    
    # Create or update user
    user = user_manager.create_or_update_user(db, user_data)
    if not user:
        # Check if user exists and is verified
        existing_user = user_manager.get_user_by_email(db, user_data.email)
        if existing_user and existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists and is verified"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create or update user"
            )
    
    # Create email verification token (this will invalidate any existing tokens)
    verification_token = email_verification_manager.create_verification_token(db, user.userid)
    
    # Send verification email
    try:
        await email_service.send_verification_email(
            email=user.email,
            verification_token=verification_token,
            user_name=f"{user.firstname} {user.lastname}"
        )
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        # Don't fail signup if email sending fails
    
    # Log activity
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    activity_manager.create_activity_log(
        db, user.userid, client_ip, user_agent, "SIGNUP"
    )
    
    return user

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    refresh_manager = RefreshTokenManager()
    
    # Get refresh token from database
    refresh_token_record = refresh_manager.get_refresh_token(db, refresh_request.refresh_token)
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    user_manager = UserManager()
    user = user_manager.get_user_by_id(db, refresh_token_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token = create_tokens(
        user_id=str(user.userid),
        email=user.email,
        user_type=UserType(user.user_type)
    )["access_token"]
    
    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60  # 30 minutes
    )

@router.post("/logout")
async def logout(
    refresh_request: RefreshTokenRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and revoke refresh token."""
    refresh_manager = RefreshTokenManager()
    
    # Revoke the specific refresh token
    refresh_manager.revoke_refresh_token(db, refresh_request.refresh_token)
    
    return {"message": "Successfully logged out"}

@router.post("/logout-all")
async def logout_all(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user from all devices by revoking all refresh tokens."""
    refresh_manager = RefreshTokenManager()
    
    # Revoke all user's refresh tokens
    refresh_manager.revoke_all_user_tokens(db, UUID(current_user.user_id))
    
    return {"message": "Successfully logged out from all devices"}

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile."""
    user_manager = UserManager()
    user = user_manager.get_user_by_id(db, UUID(current_user.user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    user_manager = UserManager()
    
    # Remove fields that shouldn't be updated by user
    update_data = user_update.dict(exclude_unset=True)
    if "user_type" in update_data:
        del update_data["user_type"]  # Users can't change their own role
    if "is_active" in update_data:
        del update_data["is_active"]  # Users can't deactivate themselves
    
    user_update_filtered = UserUpdate(**update_data)
    user = user_manager.update_user(db, UUID(current_user.user_id), user_update_filtered)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user's password."""
    user_manager = UserManager()
    
    success = user_manager.change_password(db, UUID(current_user.user_id), password_change)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify user's email address using verification token."""
    email_verification_manager = EmailVerificationManager()
    
    # Verify the email
    success = email_verification_manager.verify_email(db, verification_data.token)
    
    if success:
        # Get user info for welcome email
        user = email_verification_manager.get_user_by_token(db, verification_data.token)
        if user:
            try:
                await email_service.send_welcome_email(
                    email=user.email,
                    user_name=f"{user.firstname} {user.lastname}",
                    user_type=user.user_type
                )
            except Exception as e:
                print(f"Failed to send welcome email: {e}")
        
        return EmailVerificationResponse(
            message="Email verified successfully! Welcome to OncoSight AI.",
            verified=True
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification_email(
    request_data: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """Resend verification email to user."""
    user_manager = UserManager()
    email_verification_manager = EmailVerificationManager()
    
    # Check if user exists
    user = user_manager.get_user_by_email(db, request_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Check verification status
    verification_status = email_verification_manager.get_user_verification_status(db, user.userid)
    if verification_status["has_pending_token"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification email already sent. Please check your email or wait before requesting another."
        )
    
    # Create new verification token
    verification_token = email_verification_manager.create_verification_token(db, user.userid)
    
    # Send verification email
    try:
        await email_service.send_verification_email(
            email=user.email,
            verification_token=verification_token,
            user_name=f"{user.firstname} {user.lastname}"
        )
        
        return ResendVerificationResponse(
            message="Verification email sent successfully!",
            sent=True
        )
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Send password reset email to user."""
    user_manager = UserManager()
    password_reset_manager = PasswordResetManager()
    
    # Check if user exists
    user = user_manager.get_user_by_email(db, request_data.email)
    if not user:
        # Don't reveal if user exists or not for security
        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent.",
            sent=True
        )
    
    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email address before resetting your password."
        )
    
    # Check reset status
    reset_status = password_reset_manager.get_user_reset_status(db, user.userid)
    if reset_status["has_pending_token"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset email already sent. Please check your email or wait before requesting another."
        )
    
    # Create new reset token
    reset_token = password_reset_manager.create_reset_token(db, user.userid)
    
    # Send reset email
    try:
        await email_service.send_password_reset_email(
            email=user.email,
            reset_token=reset_token,
            user_name=f"{user.firstname} {user.lastname}"
        )
        
        return ForgotPasswordResponse(
            message="Password reset email sent successfully!",
            sent=True
        )
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email. Please try again later."
        )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset user's password using reset token."""
    password_reset_manager = PasswordResetManager()
    
    # Reset the password
    success = password_reset_manager.reset_password(db, reset_data.token, reset_data.new_password)
    
    if success:
        return ResetPasswordResponse(
            message="Password reset successfully! You can now log in with your new password.",
            success=True
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
