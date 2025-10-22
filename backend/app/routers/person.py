from fastapi import APIRouter, Request, HTTPException, Depends, Query, status
from typing import Union, List, Optional
from app.models import Youth, Leader, Parent, Person, User, PersonCreate, ParentYouthRelationshipCreate
from sqlalchemy.orm import Session
import datetime

router = APIRouter()

# Lazy loading functions
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
    from app.repositories import get_person_repository
    return {
        "person": get_person_repository(db_session)
    }

ERRORS = {
	"person_not_found": {
		"status_code": 404,
		"detail": "Person not found"
	}
}
PERSON_NOT_FOUND = "person_not_found"

@router.get("/person/youth", response_model=list[Youth])
async def get_all_non_archived_youth(
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	repos = get_repositories(db)
	youth_list = await repos["person"].get_all_youth()
	
	# Return youth dicts without archived_on field and without health fields (privacy)
	result = []
	for youth in youth_list:
		data = youth.model_dump()
		data.pop("archived_on", None)
		# Remove health fields for privacy in list endpoints
		data.pop("allergies", None)
		data.pop("other_considerations", None)
		result.append(data)
	return result

@router.get("/person/leaders", response_model=list[Leader])
async def get_all_non_archived_leaders(
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	try:
		repos = get_repositories(db)
		leaders_list = await repos["person"].get_all_leaders()
		
		# Return leaders dicts without archived_on field
		result = []
		for leader in leaders_list:
			data = leader.model_dump()
			data.pop("archived_on", None)
			result.append(data)
		return result
	except Exception as e:
		print(f"Error in get_all_non_archived_leaders: {e}")
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/person", response_model=Union[Youth, Leader])
async def create_person(
	person: Union[Youth, Leader], 
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	repos = get_repositories(db)
	try:
		created_person = await repos["person"].create_person(person)
		data = created_person.model_dump()
		data.pop("archived_on", None)
		return data
	except ValueError as e:
		raise HTTPException(status_code=422, detail=str(e))

@router.get("/person/{person_id}", response_model=Union[Youth, Leader])
async def get_person(
	person_id: int, 
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	repos = get_repositories(db)
	person = await repos["person"].get_person(person_id)
	
	if not person:
		raise HTTPException(**ERRORS[PERSON_NOT_FOUND])
	
	# For individual person requests, return all fields including health data
	data = person.model_dump()
	data.pop("archived_on", None)
	return data

@router.put("/person/{person_id}", response_model=Union[Youth, Leader])
async def update_person(
	person_id: int, 
	person: Union[Youth, Leader], 
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	repos = get_repositories(db)
	try:
		updated_person = await repos["person"].update_person(person_id, person)
		result = updated_person.model_dump()
		result.pop("archived_on", None)
		return result
	except ValueError as e:
		raise HTTPException(status_code=404 if "not found" in str(e) else 422, detail=str(e))

@router.delete("/person/{person_id}")
async def archive_person(
	person_id: int, 
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	repos = get_repositories(db)
	await repos["person"].archive_person(person_id)
	return {}

# Parent-specific endpoints
@router.post("/parent", response_model=Parent)
async def create_parent(
	parent: PersonCreate,
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	"""Create a new parent using the unified person system."""
	repos = get_repositories(db)
	try:
		# Ensure person_type is set to parent
		parent.person_type = "parent"
		created_parent = await repos["person"].create_person_unified(parent)
		data = created_parent
		data.pop("archived_on", None)
		return data
	except ValueError as e:
		raise HTTPException(status_code=422, detail=str(e))

@router.get("/parents", response_model=List[Parent])
async def get_all_parents(
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	"""Get all non-archived parents."""
	try:
		repos = get_repositories(db)
		parents_list = await repos["person"].get_all_parents()
		
		# Return parents without archived_on field
		result = []
		for parent in parents_list:
			data = parent.copy() if isinstance(parent, dict) else parent
			if isinstance(data, dict):
				data.pop("archived_on", None)
			result.append(data)
		return result
	except Exception as e:
		print(f"Error in get_all_parents: {e}")
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/parent/{parent_id}", response_model=Parent)
async def get_parent_by_id(
	parent_id: int,
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	"""Get a specific parent by ID."""
	try:
		repos = get_repositories(db)
		
		# Get the person by ID
		person = await repos["person"].get_person(parent_id)
		if not person:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Parent not found"
			)
		
		# Verify it's actually a parent
		if not isinstance(person, Parent):
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Person is not a parent"
			)
		
		return person
		
	except HTTPException:
		raise
	except Exception as e:
		print(f"Error in get_parent_by_id: {e}")
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/parents/search", response_model=List[Parent])
async def search_parents(
	query: str = Query(..., description="Search query for parent name, phone, or email"),
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	"""Search parents by name, phone, or email."""
	try:
		repos = get_repositories(db)
		parents_list = await repos["person"].search_persons("parent", query)
		
		# Return parents without archived_on field
		result = []
		for parent in parents_list:
			data = parent.copy() if isinstance(parent, dict) else parent
			if isinstance(data, dict):
				data.pop("archived_on", None)
			result.append(data)
		return result
	except Exception as e:
		print(f"Error in search_parents: {e}")
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Parent-Youth relationship endpoints
@router.post("/youth/{youth_id}/parents")
async def link_parent_to_youth(
	youth_id: int,
	relationship: ParentYouthRelationshipCreate,
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	"""Create a parent-youth relationship."""
	try:
		repos = get_repositories(db)
		# Ensure the youth_id in the URL matches the relationship data
		relationship.youth_id = youth_id
		result = await repos["person"].link_parent_to_youth(relationship)
		return result
	except ValueError as e:
		error_msg = str(e).lower()
		if "already linked" in error_msg:
			raise HTTPException(status_code=400, detail=str(e))
		elif "not found" in error_msg:
			raise HTTPException(status_code=404, detail=str(e))  # Person doesn't exist
		elif "not a parent type" in error_msg:
			raise HTTPException(status_code=400, detail=str(e))  # Person exists but wrong type
		else:
			raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		print(f"Error in link_parent_to_youth: {e}")
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/youth/{youth_id}/parents")
async def get_parents_for_youth(
	youth_id: int,
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	"""Get all parents for a specific youth with relationship details."""
	try:
		repos = get_repositories(db)
		parents = await repos["person"].get_parents_for_youth(youth_id)
		return parents
	except ValueError as e:
		raise HTTPException(status_code=404, detail=str(e))
	except Exception as e:
		print(f"Error in get_parents_for_youth: {e}")
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/youth/{youth_id}/parents/{parent_id}")
async def unlink_parent_from_youth(
	youth_id: int,
	parent_id: int,
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	"""Remove a parent-youth relationship."""
	try:
		repos = get_repositories(db)
		result = await repos["person"].unlink_parent_from_youth(parent_id, youth_id)
		if result:
			return {"success": True}
		else:
			raise HTTPException(status_code=404, detail="Relationship not found")
	except HTTPException:
		raise
	except Exception as e:
		print(f"Error in unlink_parent_from_youth: {e}")
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/parents/{parent_id}/youth")
async def get_youth_for_parent(
	parent_id: int,
	db: Session = Depends(connect_to_db()),
	current_user: User = Depends(get_current_user_lazy())
):
	"""Get all youth for a specific parent with relationship details."""
	try:
		repos = get_repositories(db)
		youth = await repos["person"].get_youth_for_parent(parent_id)
		return youth
	except ValueError as e:
		raise HTTPException(status_code=404, detail=str(e))
	except Exception as e:
		print(f"Error in get_youth_for_parent: {e}")
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")