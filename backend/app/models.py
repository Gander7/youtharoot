import abc
from pydantic import BaseModel
from pydantic import field_validator, ValidationError
from typing import List, Dict, Optional
import datetime

class Person(BaseModel, abc.ABC):
	id: Optional[int] = None  # Optional for creation, will be set by database
	first_name: str
	last_name: str
	phone_number: Optional[str] = None
	sms_opt_out: bool = False  # Allow users to opt out of SMS messages (default is to receive messages)
	archived_on: Optional[datetime.datetime] = None

	def __new__(cls, *args, **kwargs):
		if cls is Person:
			raise TypeError("Person is an abstract class and cannot be instantiated directly.")
		return super().__new__(cls)

class Youth(Person):
	grade: Optional[int] = None
	school_name: Optional[str] = None
	birth_date: datetime.date
	email: Optional[str] = ""
	emergency_contact_name: Optional[str] = ""
	emergency_contact_phone: Optional[str] = ""
	emergency_contact_relationship: Optional[str] = ""
	emergency_contact_2_name: Optional[str] = ""
	emergency_contact_2_phone: Optional[str] = ""
	emergency_contact_2_relationship: Optional[str] = ""
	allergies: Optional[str] = ""
	other_considerations: Optional[str] = ""

class Leader(Person):
	role: str
	birth_date: Optional[datetime.date] = None

class EventPerson(BaseModel):
	person_id: int
	check_in: datetime.datetime
	check_out: Optional[datetime.datetime] = None

class Event(BaseModel):
	id: Optional[int] = None  # Optional for creation, will be set by database
	date: str
	name: str = "Youth Group"
	desc: str = ""
	start_time: str = "19:00"
	end_time: str = "21:00"
	location: Optional[str] = None
	youth: List[EventPerson] = []
	leaders: List[EventPerson] = []

class User(BaseModel):
	id: Optional[int] = None  # Optional for creation, will be set by database
	username: str
	password_hash: str
	role: str = "user"
	created_at: Optional[datetime.datetime] = None
