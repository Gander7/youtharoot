
from fastapi import APIRouter, Request
from typing import Union
from app.models import Youth, Leader, Person

router = APIRouter()
person_store = {}

@router.post("/person", response_model=Union[Youth, Leader])
async def create_person(request: Request):
	data = await request.json()

	person = None
	if "grade" in data or "school_name" in data:
		person = Youth(**data)
	elif "role" in data:
		person = Leader(**data)

	if person is None:
		return {"error": f"Invalid Object type ({type(data)})"}

	person_store[person.id] = person
	return person