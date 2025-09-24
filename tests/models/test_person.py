import pytest
from app.models import Person, Youth, Leader


def test_person_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Person(
            id=1,
            first_name="Alex",
            last_name="Smith",
            birth_date="2005-04-12",
            phone_number="555-1234",
            emergency_contact_name="Jordan Smith",
            emergency_contact_phone="555-5678",
            emergency_contact_relationship="Parent"
        )

def test_youth_inherits_person():
    youth = Youth(
        id=2,
        first_name="Sam",
        last_name="Lee",
        birth_date="2007-09-21",
        grade=10,
        school_name="Central High",
        emergency_contact_name="Morgan Lee",
        emergency_contact_phone="555-8765",
        emergency_contact_relationship="Guardian"
        # phone_number is optional
    )
    assert isinstance(youth, Person)
    assert youth.grade == 10
    assert youth.school_name == "Central High"
    assert youth.phone_number is None or isinstance(youth.phone_number, str)

def test_leader_inherits_person():
    leader = Leader(
        id=3,
        first_name="Jamie",
        last_name="Brown",
        birth_date="1990-02-15",
        phone_number="555-2468",
        role="Mentor"
    )
    assert isinstance(leader, Person)
    assert leader.role == "Mentor"
