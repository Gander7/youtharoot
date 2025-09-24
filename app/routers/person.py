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

@router.get("/person/youth", response_model=list[Youth])
async def get_all_non_archived_youth():
	# Return youth dicts without archived_on field
	result = []
	for person in person_store.values():
		if isinstance(person, Youth) and person.archived_on is None:
			data = person.model_dump()
			data.pop("archived_on", None)
			result.append(data)
	return result

@router.post("/person", response_model=Union[Youth, Leader])
async def create_person(person: Union[Youth, Leader]):
	if (person.archived_on is not None):
		raise HTTPException(status_code=422, detail="Cannot create archived person")
	person_store[person.id] = person
	data = person.model_dump()
	data.pop("archived_on", None)
	return data

@router.get("/person/{person_id}", response_model=Union[Youth, Leader])
async def get_person(person_id: int):
	person = person_store.get(person_id)
	if not person or person.archived_on is not None:
		raise HTTPException(**ERRORS[PERSON_NOT_FOUND])
	data = person.model_dump()
	data.pop("archived_on", None)
	return data

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
	result = person.model_dump()
	result.pop("archived_on", None)
	return result

@router.delete("/person/{person_id}")
async def archive_person(person_id: int):
	person = person_store.get(person_id)
	if person:
		person.archived_on = datetime.datetime.now(datetime.timezone.utc)
	return {}