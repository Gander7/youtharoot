import abc
from pydantic import BaseModel
from pydantic import field_validator, ValidationError
from typing import List, Dict, Optional
import datetime
import pytz
from datetime import timezone

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
	date: str  # Keep for backward compatibility
	name: str = "Youth Group"
	desc: str = ""
	start_time: str = "19:00"  # Keep for backward compatibility
	end_time: str = "21:00"  # Keep for backward compatibility
	location: Optional[str] = None
	# New UTC datetime fields
	start_datetime: Optional[datetime.datetime] = None
	end_datetime: Optional[datetime.datetime] = None
	youth: List[EventPerson] = []
	leaders: List[EventPerson] = []

	class Config:
		json_encoders = {
			datetime.datetime: lambda v: v.isoformat() if v else None
		}

class EventCreate(BaseModel):
	name: str = "Youth Group"
	date: str  # Halifax date format: YYYY-MM-DD
	desc: str = ""
	start_time: str = "19:00"  # Halifax time format: HH:MM
	end_time: str = "21:00"  # Halifax time format: HH:MM  
	location: Optional[str] = None
	# Optional direct datetime fields (for API flexibility)
	start_datetime: Optional[datetime.datetime] = None
	end_datetime: Optional[datetime.datetime] = None
	
	def __init__(self, **data):
		super().__init__(**data)
		
		# Auto-generate UTC datetimes from Halifax date/time if not provided
		if not self.start_datetime or not self.end_datetime:
			self._generate_utc_datetimes()
	
	def _generate_utc_datetimes(self):
		"""Convert Halifax date/time to UTC datetimes"""
		halifax_tz = pytz.timezone('America/Halifax')
		
		# Parse date and times
		date_parts = self.date.split('-')
		year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
		
		start_parts = self.start_time.split(':')
		start_hour, start_minute = int(start_parts[0]), int(start_parts[1])
		
		end_parts = self.end_time.split(':')
		end_hour, end_minute = int(end_parts[0]), int(end_parts[1])
		
		# Create Halifax datetime objects
		start_halifax = halifax_tz.localize(datetime.datetime(year, month, day, start_hour, start_minute))
		end_halifax = halifax_tz.localize(datetime.datetime(year, month, day, end_hour, end_minute))
		
		# Convert to UTC
		self.start_datetime = start_halifax.astimezone(timezone.utc)
		self.end_datetime = end_halifax.astimezone(timezone.utc)

class EventUpdate(BaseModel):
	name: Optional[str] = None
	date: Optional[str] = None
	desc: Optional[str] = None
	start_time: Optional[str] = None
	end_time: Optional[str] = None
	location: Optional[str] = None
	start_datetime: Optional[datetime.datetime] = None
	end_datetime: Optional[datetime.datetime] = None
	
	def __init__(self, **data):
		super().__init__(**data)
		
		# If date/time fields are updated, regenerate UTC datetimes
		if any([self.date, self.start_time, self.end_time]) and not (self.start_datetime and self.end_datetime):
			self._update_utc_datetimes()
	
	def _update_utc_datetimes(self):
		"""Update UTC datetimes when legacy fields change"""
		if self.date and self.start_time and self.end_time:
			# Use the same conversion logic as EventCreate
			temp_create = EventCreate(
				name="temp",
				date=self.date,
				start_time=self.start_time, 
				end_time=self.end_time
			)
			self.start_datetime = temp_create.start_datetime
			self.end_datetime = temp_create.end_datetime

class User(BaseModel):
	id: Optional[int] = None  # Optional for creation, will be set by database
	username: str
	password_hash: str
	role: str = "user"
	created_at: Optional[datetime.datetime] = None
