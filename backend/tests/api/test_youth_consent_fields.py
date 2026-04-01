"""
TDD tests for parental_permission_2026 and photo_consent_2026 youth fields.
"""
import pytest
from tests.test_helpers import get_authenticated_client

client = get_authenticated_client()
PERSON_ENDPOINT = "/person"


def valid_youth_payload(**overrides):
    base = {
        "first_name": "Alex",
        "last_name": "Smith",
        "birth_date": "2010-06-15",
        "person_type": "youth",
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def clear_store(clean_database):
    from app.repositories import get_person_repository
    from app.config import settings
    from app.repositories.memory import InMemoryPersonRepository

    if settings.DATABASE_TYPE != "postgresql":

        class MockSession:
            pass

        repo = get_person_repository(MockSession())
        if isinstance(repo, InMemoryPersonRepository):
            repo.store.clear()


class TestYouthConsentFieldDefaults:
    def test_create_youth_without_consent_fields_defaults_to_false(self):
        """Both consent fields default to False when omitted."""
        response = client.post(PERSON_ENDPOINT, json=valid_youth_payload())
        assert response.status_code == 200
        data = response.json()
        assert data["parental_permission_2026"] is False
        assert data["photo_consent_2026"] is False

    def test_create_youth_with_consent_fields_true(self):
        """Both consent fields accept True."""
        payload = valid_youth_payload(
            parental_permission_2026=True,
            photo_consent_2026=True,
        )
        response = client.post(PERSON_ENDPOINT, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["parental_permission_2026"] is True
        assert data["photo_consent_2026"] is True

    def test_create_youth_with_mixed_consent_values(self):
        """Each consent field can be set independently."""
        payload = valid_youth_payload(
            parental_permission_2026=True,
            photo_consent_2026=False,
        )
        response = client.post(PERSON_ENDPOINT, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["parental_permission_2026"] is True
        assert data["photo_consent_2026"] is False


class TestYouthConsentFieldUpdate:
    def test_update_youth_consent_fields(self):
        """PUT request can update consent fields."""
        # Create youth
        create_resp = client.post(PERSON_ENDPOINT, json=valid_youth_payload())
        assert create_resp.status_code == 200
        person_id = create_resp.json()["id"]

        # Update both to True
        update_resp = client.put(
            f"{PERSON_ENDPOINT}/{person_id}",
            json={"parental_permission_2026": True, "photo_consent_2026": True},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["parental_permission_2026"] is True
        assert data["photo_consent_2026"] is True

    def test_get_youth_returns_consent_fields(self):
        """GET single youth includes consent fields."""
        payload = valid_youth_payload(parental_permission_2026=True, photo_consent_2026=False)
        create_resp = client.post(PERSON_ENDPOINT, json=payload)
        assert create_resp.status_code == 200
        person_id = create_resp.json()["id"]

        get_resp = client.get(f"{PERSON_ENDPOINT}/{person_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["parental_permission_2026"] is True
        assert data["photo_consent_2026"] is False
