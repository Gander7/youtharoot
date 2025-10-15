from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Union, List
from app.models import Youth, Leader, Person, User
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