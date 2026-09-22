"""
models/user.py
Represents both students and admins (differentiated by `role`).
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("student", "admin", name="user_role"), default="student", nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # NEW
    created_at = Column(DateTime(timezone=True), server_default=func.now())