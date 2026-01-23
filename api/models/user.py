import json
from fastapi.params import Form
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Literal 
from sqlalchemy import Column,Integer,String, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.orm import  Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.sql import func
import re



class SignUpRequest(BaseModel):
    """
     Registering a user
    """
    username: str = Field(..., min_length=3, max_length=20)
    password: str =Field(..., min_length=6, description="Password must be at least 6 characters long")
    

class UserCreate(BaseModel):
    """
    User creation model
    """
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr 
    password: str =Field(..., min_length=6, description="Password must be at least 6 characters long")
    repeat_password: str =Field(..., min_length=6, description="Repeat password must be at least 6 characters long")

    """User creation model with password validation"""
    @model_validator(mode='after')
    def validate_password(self,):
        password = self.password
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@#$%&*])[A-Za-z\d@#$%&*]{6,}$', password):
            raise ValueError('Password must contain at least one uppercase letter, one digit, and one special character(@,#,$,%,&,*).')
        return self

    """Ensure passwords match"""
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.repeat_password:
            raise ValueError('Passwords do not match')
        return self
    
    """Ensure username has no spaces and valid characters"""
    @model_validator(mode='after')
    def username_no_spaces(self):
        username = self.username
        if not re.match(r'^[a-z0-9_]+$', username):
            raise ValueError('Username can only contain lowercase letters, numbers, and underscores, with no spaces.')
        return self

class ChangePasswordRequest(BaseModel):
    """
    Change password model
    """
    old_password: str =Field(..., min_length=6, description="Old password must be at least 6 characters long")
    new_password: str =Field(..., min_length=6, description="New password must be at least 6 characters long")
    repeat_new_password: str =Field(..., min_length=6, description="Repeat new password must be at least 6 characters long")

    """Change password model with password validation"""
    @model_validator(mode='after')
    def validate_new_password(self,):
        new_password = self.new_password
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@#$%&*])[A-Za-z\d@#$%&*]{6,}$', new_password):
            raise ValueError('New password must contain at least one uppercase letter, one digit, and one special character(@,#,$,%,&,*).')
        return self

    """Ensure new passwords match"""
    @model_validator(mode='after')
    def new_passwords_match(self):
        if self.new_password != self.repeat_new_password:
            raise ValueError('New passwords do not match')
        return self
    
    

class PasswordResetRequest(BaseModel):
    """
    Password reset model
    """
    new_password: str =Field(..., min_length=6, description="New password must be at least 6 characters long")
    repeat_new_password: str =Field(..., min_length=6, description="Repeat new password must be at least 6 characters long")

    """Password reset model with password validation"""
    @model_validator(mode='after')
    def validate_new_password(self,):
        new_password = self.new_password
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@#$%&*])[A-Za-z\d@#$%&*]{6,}$', new_password):
            raise ValueError('New password must contain at least one uppercase letter, one digit, and one special character(@,#,$,%,&,*).')
        return self

    """Ensure new passwords match"""
    @model_validator(mode='after')
    def new_passwords_match(self):
        if self.new_password != self.repeat_new_password:
            raise ValueError('New passwords do not match')
        return self
    
"""Login response model"""
class LoginResponse(BaseModel):
    username: str
    email: EmailStr

"""Access token response model"""
class AccessRefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

"""Access token response model"""
class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str

"""Only Access token response model"""
class TokenResponse(BaseModel):
    token: str

"""User response model"""
class UserResponse(BaseModel):
    username: str
    email: EmailStr
    roles: list[str]
    is_locked: bool
    api_keys: list[str]
    last_login: str
    api_key_quota: int
    max_requests_per_day: int

"""User response model"""
class UsernameResponse(BaseModel):
    username: str
    email: EmailStr
    roles: list[str]
    password_hashed: str

"""Train model response model"""
class TrainModelResponse(BaseModel):
    message: str
    report_url: str
    accuracy: float
    model_path: str

class PredictionExplanationResponse(BaseModel):
    """Prediction explanation response model"""
    explanation: str

"""Prediction request model"""
class PredictionRequest(BaseModel):
    contents: list[str] = Field(..., example=["Sample content 1", "Sample content 2"],
                                max_length=5)
    
"""Prediction explanation request model"""
class PredictionExplanationRequest(BaseModel):
    contents: list[str] = Field(..., example=["Sample content 1", "Sample content 2"],
                                max_length=5)
    predicted_categories: list[str] = Field(..., example=["Spam", "Hate Speech"],
                                           max_length=5)
   
    """Ensure contents and predicted_categories lengths match"""
    @model_validator(mode='after')
    def check_lengths_match(self):
        if len(self.contents) != len(self.predicted_categories):
            raise ValueError('The number of contents and predicted_categories must match')
        return self
    
"""Train model request model"""
class TrainModelRequestWithValidation(BaseModel):
    out_path: str = Field(..., example="processed_data.csv")
    class_weight: list[int] = Field(..., example=[1,1,1,1,1,1], max_length=6, description="Class weights for each class in order from 0 to 5")
    random_state: int = Field(42, example=42, ge=1, le=100)
    c: float = Field(1.5, example=1.5, ge=1.0, le=3.0)
    dual: Literal['auto', 'true', 'false'] = Field('auto', example="auto")
    use_augmentation: bool = Field(False, example=False)

    """Allow form data submission"""
    @classmethod
    def as_form(cls):
        def _as_form(
                out_path: str = Form(..., example="processed_data.csv"),
                c: float = Form(1.5, example=1.5, ge=1.0, le=3.0),
                dual: Literal['auto', 'true', 'false'] = Form('auto', example="auto"),
                class_weight: list[int] = Form(..., example=[1,1,1,1,1,1], max_length=6, description="Class weights for each class in order from 0 to 5"),
                random_state: int = Form(42, example=42, ge=1, le=100),
                use_augmentation: bool = Form(False, example=False)
        ):
            return cls(**json.loads(json.dumps({
                "out_path": out_path,
                "c": c,
                "dual": dual,
                "class_weight": class_weight,
                "random_state": random_state,
                "use_augmentation": use_augmentation})))
        return _as_form



"""Train model request model"""
class TrainModelRequest(BaseModel):
    out_path: str = Field(..., example="processed_data.csv")
    class_weight: list[int] = Field(..., example=[1,1,1,1,1,1], description="Class weights for each class in order from 0 to 5")
    random_state: int = Field(42, example=42)
    c: float = Field(1.5, example=1.5)
    dual: Literal['auto', 'true', 'false'] = Field('auto', example="auto")
    random_state: int = Field(42, example=42)
    use_augmentation: bool = Field(False, example=False)

    """Allow form data submission"""
    @classmethod
    def as_form(cls):
        def _as_form(
                out_path: str = Form(..., example="processed_data.csv"),
                c: float = Form(1.5, example=1.5),
                dual: Literal['auto', 'true', 'false'] = Form('auto', example="auto"),
                class_weight: list[int] = Form(..., example=[1,1,1,1,1,1], description="Class weights for each class in order from 0 to 5"),
                random_state: int = Form(42, example=42),
                use_augmentation: bool = Form(False, example=False)
        ):
            return cls(**json.loads(json.dumps({
                "out_path": out_path,
                "c": c,
                "dual": dual,
                "class_weight": class_weight,
                "random_state": random_state,
                "use_augmentation": use_augmentation})))
        return _as_form


"""SQLAlchemy Base class"""
class Base(DeclarativeBase):
      pass


"""Association table for many-to-many relationship between users and roles"""
user_roles = Table(
    "user_role_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("user_roles.id"), primary_key=True)
)

"""RequestCount model to track user requests"""
class RequestCount(Base):
    __tablename__ = "requests_count"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0)
    last_request: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user = relationship("DbUser", back_populates="request_count")

"""ApiKey model to store API keys for users"""
class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user = relationship("DbUser", back_populates="api_keys")

"""DbUser model representing users"""
class DbUser(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    is_email_confirmed: Mapped[Boolean] = mapped_column(Boolean, default=False)
    password_hashed: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_two_factor_enabled: Mapped[Boolean] = mapped_column(Boolean, default=False)
    authentication_secret: Mapped[str] = mapped_column(String, nullable=True)
    refresh_token: Mapped[str] = mapped_column(String, nullable=True)
    expiry_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    roles = relationship("DbUserRole", secondary=user_roles, back_populates="users")
    request_count = relationship("RequestCount", back_populates="user", uselist=False)
    api_keys = relationship("ApiKey", back_populates="user")
    is_locked: Mapped[Boolean] = mapped_column(Boolean, default=False)

"""DbUserRole model representing user roles"""
class DbUserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    users = relationship("DbUser", secondary=user_roles, back_populates="roles")

"""LoginAttempt model to track login attempts"""
class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,index=True)
    username: Mapped[str] = mapped_column(String, index=True, nullable=False)
    attempt_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    no_attempts: Mapped[int] = mapped_column(Integer, default=1)