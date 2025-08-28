
from pydantic import BaseModel
from typing import Optional
import datetime

import abc
from pydantic import BaseModel
from typing import Optional
import datetime

class Person(BaseModel, abc.ABC):
	id: int
	first_name: str
	last_name: str
	phone_number: Optional[str] = None
	archived_on: Optional[datetime.datetime] = None

	def __new__(cls, *args, **kwargs):
		if cls is Person:
			raise TypeError("Person is an abstract class and cannot be instantiated directly.")
		return super().__new__(cls)

class Youth(Person):
	grade: int
	school_name: str
	birth_date: datetime.date
	emergency_contact_name: str
	emergency_contact_phone: str
	emergency_contact_relationship: str

class Leader(Person):
	role: str
	birth_date: Optional[datetime.date] = None
