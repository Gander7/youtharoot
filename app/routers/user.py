"""
User management API router with admin-only access control.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


def connect_to_db():
    from app.database import get_db
    db_generator = get_db()
    try:
        db = next(db_generator)
        yield db
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass

def get_current_admin_user_dependency():
    from app.auth import get_current_admin_user
    return get_current_admin_user

# Use this as the actual dependency
get_current_admin_user_lazy = Depends(get_current_admin_user_dependency())

def get_repositories():
    from app.repositories import get_user_repository
    return get_user_repository

def get_auth_functions():
    from app.auth import get_password_hash, authenticate_user, create_access_token
    return get_password_hash, authenticate_user, create_access_token


class UserCreate(BaseModel):
    """User creation model"""
    username: str
    password: str
    role: str = "user"


class UserUpdate(BaseModel):
    """User update model"""
    username: str
    password: str
    role: str


class UserResponse(BaseModel):
    """User response model (excludes password hash)"""
    id: int
    username: str
    role: str
    created_at: str


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str
    user: UserResponse


def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse (excluding password hash)"""
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(connect_to_db)):
    """Authenticate user and return access token"""
    get_password_hash_func, authenticate_user_func, create_access_token_func = get_auth_functions()
    user = await authenticate_user_func(login_data.username, login_data.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token_func(data={"sub": user.username})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_to_response(user)
    )


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = get_current_admin_user_lazy,
    db: Session = Depends(connect_to_db)
):
    """Get all users (admin only)"""
    get_user_repository = get_repositories()
    user_repo = get_user_repository(db)
    users = await user_repo.get_all_users()
    return [user_to_response(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = get_current_admin_user_lazy,
    db: Session = Depends(connect_to_db)
):
    """Get a specific user (admin only)"""
    get_user_repository = get_repositories()
    user_repo = get_user_repository(db)
    user = await user_repo.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_to_response(user)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = get_current_admin_user_lazy,
    db: Session = Depends(connect_to_db)
):
    """Create a new user (admin only)"""
    get_user_repository = get_repositories()
    user_repo = get_user_repository(db)
    
    # Hash the password
    get_password_hash_func, authenticate_user_func, create_access_token_func = get_auth_functions()
    hashed_password = get_password_hash_func(user_data.password)
    
    # Create user object
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role
    )
    
    try:
        created_user = await user_repo.create_user(new_user)
        return user_to_response(created_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = get_current_admin_user_lazy,
    db: Session = Depends(connect_to_db)
):
    """Update a user (admin only)"""
    get_user_repository = get_repositories()
    user_repo = get_user_repository(db)
    
    # Check if user exists
    existing_user = await user_repo.get_user(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash the new password
    get_password_hash_func, authenticate_user_func, create_access_token_func = get_auth_functions()
    hashed_password = get_password_hash_func(user_data.password)
    
    # Create updated user object
    updated_user = User(
        id=user_id,
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role,
        created_at=existing_user.created_at
    )
    
    try:
        updated_user = await user_repo.update_user(user_id, updated_user)
        return user_to_response(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = get_current_admin_user_lazy,
    db: Session = Depends(connect_to_db)
):
    """Delete a user (admin only)"""
    get_user_repository = get_repositories()
    user_repo = get_user_repository(db)
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own user account"
        )
    
    success = await user_repo.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )