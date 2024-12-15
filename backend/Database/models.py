from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID, INET
# from sqlalchemy.orm import relationship
# from sqlalchemy.ext.declarative import declarative_base
from .database import Base
import uuid

# Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    userid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=False)
    user_type = Column(String(20), nullable=False)
    signup_timestamp = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


# class UserLog(Base):
#     __tablename__ = "user_logs"

#     userid = Column(UUID(as_uuid=True), ForeignKey("users.userid", ondelete="CASCADE"), primary_key=True)
#     total_logins = Column(Integer, default=0)
#     input_tokens_used = Column(BigInteger, default=0)
#     output_tokens_used = Column(BigInteger, default=0)
#     last_login_date = Column(TIMESTAMP)


# class ActivityLog(Base):
#     __tablename__ = "activity_logs"

#     log_id = Column(BigInteger, primary_key=True, autoincrement=True)
#     userid = Column(UUID(as_uuid=True), ForeignKey("users.userid", ondelete="CASCADE"), nullable=False)
#     ip_address = Column(INET, nullable=False)
#     login_timestamp = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


# class ChatLog(Base):
#     __tablename__ = "chat_logs"

#     chat_id = Column(BigInteger, primary_key=True)
#     userid = Column(UUID(as_uuid=True), ForeignKey("users.userid", ondelete="CASCADE"), nullable=False)
#     tokens_used = Column(int, autoincrement=True, default=0)
#     created_at = Column(TIMESTAMP)
