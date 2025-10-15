"""
Group Management API Router

Provides CRUD operations for message groups and group membership management.
Built using TDD methodology - tests drive the implementation.

Endpoints:
- POST /groups - Create a new message group
- GET /groups - List all groups for current user  
- GET /groups/{id} - Get specific group details
- PUT /groups/{id} - Update group details
- DELETE /groups/{id} - Delete a group
- POST /groups/{id}/members - Add member to group
- GET /groups/{id}/members - List group members
- DELETE /groups/{id}/members/{person_id} - Remove member from group
- POST /groups/{id}/members/bulk - Add multiple members to group
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models import User
from app.messaging_models import (
    MessageGroup, MessageGroupCreate, MessageGroupUpdate,
    MessageGroupMembership, MessageGroupMembershipCreate,
    MessageGroupMembershipWithPerson,
    BulkGroupMembershipCreate, BulkGroupMembershipResponse
)


router = APIRouter(prefix="/groups", tags=["groups"])


# Lazy loading functions (following existing pattern)
def connect_to_db():
    """Lazily import and return database dependency"""
    from app.database import get_db
    return get_db


def get_current_user_lazy():
    """Lazily import and return current user dependency"""
    from app.auth import get_current_user
    return get_current_user


def get_repositories(db_session):
    """Lazily import and return repository instances"""
    from app.repositories import get_group_repository, get_person_repository
    return {
        "group": get_group_repository(db_session),
        "person": get_person_repository(db_session)
    }


@router.post("", response_model=MessageGroup, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: MessageGroupCreate,
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """Create a new message group."""
    repos = get_repositories(db)
    
    try:
        created_group = await repos["group"].create_group(group, current_user.id)
        return created_group
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[MessageGroup])
async def list_groups(
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """List all groups created by the current user."""
    repos = get_repositories(db)
    groups = await repos["group"].get_all_groups(current_user.id)
    return groups


@router.get("/{group_id}", response_model=MessageGroup)
async def get_group(
    group_id: int,
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """Get a specific group by ID."""
    repos = get_repositories(db)
    group = await repos["group"].get_group(group_id, current_user.id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    return group


@router.put("/{group_id}", response_model=MessageGroup)
async def update_group(
    group_id: int,
    group_update: MessageGroupUpdate,
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """Update a group's details."""
    repos = get_repositories(db)
    
    try:
        updated_group = await repos["group"].update_group(group_id, group_update, current_user.id)
        if not updated_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        return updated_group
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """Delete a group and all its memberships."""
    repos = get_repositories(db)
    success = await repos["group"].delete_group(group_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )


@router.post("/{group_id}/members", response_model=MessageGroupMembership, status_code=status.HTTP_201_CREATED)
async def add_member_to_group(
    group_id: int,
    membership: MessageGroupMembershipCreate,
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """Add a person to a group."""
    repos = get_repositories(db)
    
    # Verify group exists and belongs to current user
    group = await repos["group"].get_group(group_id, current_user.id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Verify person exists
    person = await repos["person"].get_person(membership.person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    try:
        created_membership = await repos["group"].add_member(group_id, membership.person_id, current_user.id)
        return created_membership
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{group_id}/members", response_model=List[MessageGroupMembershipWithPerson])
async def list_group_members(
    group_id: int,
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """List all members of a group with person details."""
    repos = get_repositories(db)
    
    # Verify group exists and belongs to current user
    group = await repos["group"].get_group(group_id, current_user.id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Get all memberships for this group with person details
    memberships = await repos["group"].get_group_members_with_person(group_id)
    return memberships


@router.delete("/{group_id}/members/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_group(
    group_id: int,
    person_id: int,
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """Remove a person from a group."""
    repos = get_repositories(db)
    
    # Verify group exists and belongs to current user
    group = await repos["group"].get_group(group_id, current_user.id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Remove membership
    success = await repos["group"].remove_member(group_id, person_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person is not a member of this group"
        )


@router.post("/{group_id}/members/bulk", response_model=BulkGroupMembershipResponse, status_code=status.HTTP_201_CREATED)
async def add_multiple_members_to_group(
    group_id: int,
    bulk_membership: BulkGroupMembershipCreate,
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_lazy())
):
    """Add multiple people to a group at once."""
    repos = get_repositories(db)
    
    # Verify group exists and belongs to current user
    group = await repos["group"].get_group(group_id, current_user.id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Add multiple members
    result = await repos["group"].add_multiple_members(group_id, bulk_membership.person_ids, current_user.id)
    return result