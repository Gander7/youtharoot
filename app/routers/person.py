from fastapi import APIRouter, Request, HTTPException
from typing import Union
from app.models import Youth, Leader, Person
import datetime

router = APIRouter()
person_store = {}

ERRORS = {
	"person_not_found": {
		"status_code": 404,
		"detail": "Person not found"
	}
}
PERSON_NOT_FOUND = "person_not_found"

@router.post("/person", response_model=Union[Youth, Leader])
async def create_person(person: Union[Youth, Leader]):
	if (person.archived_on is not None):
		raise HTTPException(status_code=422, detail="Cannot create archived person")
	person_store[person.id] = person
	return person

@router.get("/person/{person_id}", response_model=Union[Youth, Leader])
async def get_person(person_id: int):
	person = person_store.get(person_id)
	if not person or person.archived_on is not None:
		raise HTTPException(**ERRORS[PERSON_NOT_FOUND])
	return person

@router.put("/person/{person_id}", response_model=Union[Youth, Leader])
async def update_person(person_id: int, person: Union[Youth, Leader]):
	if (person.archived_on is not None):
		raise HTTPException(status_code=422, detail="Cannot update person with archived_on field")
	if person_id not in person_store:
		raise HTTPException(**ERRORS[PERSON_NOT_FOUND])

	data = person_store[person_id]
	if data.archived_on is not None:
		raise HTTPException(**ERRORS[PERSON_NOT_FOUND])

	person_store[person_id] = person
	return person

@router.delete("/person/{person_id}")
async def archive_person(person_id: int):
	person = person_store.get(person_id)
	if person:
		person.archived_on = datetime.datetime.now(datetime.timezone.utc)
	return {}