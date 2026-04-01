# Youth Consent Boolean Fields Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `parental_permission_2026` and `photo_consent_2026` boolean fields (default `false`) to youth records, exposed as checkboxes labelled "Parental Permission" and "Photo Consent" in the youth form's Personal Info tab.

**Architecture:** New columns are added to `persons` via an idempotent migration script. The fields flow through `db_models` → `models` → `repositories` → API response → frontend form state and UI.

**Tech Stack:** Python/FastAPI backend, SQLAlchemy ORM, Pydantic v2, React/JSX frontend, Material UI v7, Vitest + Testing Library for frontend tests, pytest for backend tests.

---

## File Map

| File | Change |
|---|---|
| `backend/migrations/add_consent_fields_2026.py` | **Create** — migration script |
| `backend/app/db_models.py` | **Modify** — 2 new `Boolean` columns on `PersonDB` |
| `backend/app/models.py` | **Modify** — 2 new fields on `Youth`, `PersonCreate`, `PersonUpdate` |
| `backend/app/repositories/postgresql.py` | **Modify** — `_db_to_dict`, `create_person_unified` |
| `backend/app/repositories/memory.py` | **Modify** — `create_person_unified` dict |
| `backend/tests/api/test_youth_consent_fields.py` | **Create** — backend API tests |
| `frontend/src/components/PersonForm.jsx` | **Modify** — state init (×3), UI checkboxes, submit payload |
| `frontend/src/test/components/PersonForm.test.jsx` | **Create** — frontend component tests |

---

## Task 1: Write backend tests (RED)

**Files:**
- Create: `backend/tests/api/test_youth_consent_fields.py`

- [ ] **Step 1: Create the test file**

```python
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
```

- [ ] **Step 2: Commit the test file**

```bash
git add backend/tests/api/test_youth_consent_fields.py
git commit -m "test(backend): add TDD tests for youth consent fields 2026"
```

- [ ] **Step 3: Run tests to confirm they fail (RED)**

```bash
cd backend && source ../venv/bin/activate && python -m pytest tests/api/test_youth_consent_fields.py -v
```

Expected: All tests FAIL — `parental_permission_2026` key not found in response.

---

## Task 2: Add columns to DB model

**Files:**
- Modify: `backend/app/db_models.py`

- [ ] **Step 1: Add two columns to `PersonDB` under the youth-specific fields section**

In `backend/app/db_models.py`, find the youth-specific fields block (after `other_considerations`) and add:

```python
    other_considerations = Column(Text, nullable=True)
    parental_permission_2026 = Column(Boolean, default=False, nullable=False, server_default='false')
    photo_consent_2026 = Column(Boolean, default=False, nullable=False, server_default='false')
```

The `server_default='false'` ensures existing rows get `false` automatically at the DB level even before the migration script runs in tests.

- [ ] **Step 2: Commit**

```bash
git add backend/app/db_models.py
git commit -m "feat(backend): add parental_permission_2026 and photo_consent_2026 columns to PersonDB"
```

---

## Task 3: Add fields to Pydantic models

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Add fields to `Youth`**

Find the `Youth` class and add after `other_considerations`:

```python
    other_considerations: Optional[str] = ""
    parental_permission_2026: bool = False
    photo_consent_2026: bool = False
```

- [ ] **Step 2: Add fields to `PersonCreate`**

Find the `PersonCreate` class, under the youth-specific fields comment, add after `other_considerations`:

```python
    other_considerations: Optional[str] = None
    parental_permission_2026: Optional[bool] = False
    photo_consent_2026: Optional[bool] = False
```

- [ ] **Step 3: Add fields to `PersonUpdate`**

Find the `PersonUpdate` class, under the youth-specific fields comment, add after `other_considerations`:

```python
    other_considerations: Optional[str] = None
    parental_permission_2026: Optional[bool] = None
    photo_consent_2026: Optional[bool] = None
```

- [ ] **Step 4: Run backend tests to check progress**

```bash
cd backend && source ../venv/bin/activate && python -m pytest tests/api/test_youth_consent_fields.py -v
```

Expected: Still failing — fields not yet wired through repositories.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models.py
git commit -m "feat(backend): add parental_permission_2026 and photo_consent_2026 to Pydantic models"
```

---

## Task 4: Wire fields through PostgreSQL repository

**Files:**
- Modify: `backend/app/repositories/postgresql.py`

- [ ] **Step 1: Update `_db_to_dict` to include both fields in the youth section**

Find the `_db_to_dict` method. In the `if db_person.person_type == "youth":` block, add the two fields:

```python
        if db_person.person_type == "youth":
            result.update({
                "grade": db_person.grade,
                "school_name": db_person.school_name,
                "birth_date": db_person.birth_date,
                "email": db_person.email,
                "emergency_contact_name": db_person.emergency_contact_name,
                "emergency_contact_phone": db_person.emergency_contact_phone,
                "emergency_contact_relationship": db_person.emergency_contact_relationship,
                "emergency_contact_2_name": db_person.emergency_contact_2_name,
                "emergency_contact_2_phone": db_person.emergency_contact_2_phone,
                "emergency_contact_2_relationship": db_person.emergency_contact_2_relationship,
                "allergies": db_person.allergies,
                "other_considerations": db_person.other_considerations,
                "parental_permission_2026": db_person.parental_permission_2026 or False,
                "photo_consent_2026": db_person.photo_consent_2026 or False,
            })
```

- [ ] **Step 2: Update `create_person_unified` to write both fields**

In `create_person_unified`, find the `if person.person_type == "youth":` block and add after `other_considerations`:

```python
            db_person.other_considerations = person.other_considerations
            db_person.parental_permission_2026 = person.parental_permission_2026 or False
            db_person.photo_consent_2026 = person.photo_consent_2026 or False
```

Note: `update_person_unified` uses `model_dump(exclude_unset=True)` + `setattr`, so it picks up the new fields automatically from `PersonUpdate` — no changes needed there.

- [ ] **Step 3: Run backend tests**

```bash
cd backend && source ../venv/bin/activate && python -m pytest tests/api/test_youth_consent_fields.py -v
```

Expected: Tests PASS when running with `DATABASE_TYPE=memory` (memory repo still needs updating). If running against PostgreSQL, may still fail until Task 5.

- [ ] **Step 4: Commit**

```bash
git add backend/app/repositories/postgresql.py
git commit -m "feat(backend): wire consent fields through PostgreSQL repository"
```

---

## Task 5: Wire fields through in-memory repository

**Files:**
- Modify: `backend/app/repositories/memory.py`

- [ ] **Step 1: Update `create_person_unified` dict**

Find `create_person_unified` in `InMemoryPersonRepository`. In the `person_data` dictionary, add the two fields after `other_considerations`:

```python
            "other_considerations": person.other_considerations,
            "parental_permission_2026": person.parental_permission_2026 or False,
            "photo_consent_2026": person.photo_consent_2026 or False,
```

Note: `update_person_unified` in memory already uses `model_dump(exclude_unset=True)` + dict update, so it picks up new fields from `PersonUpdate` automatically — no changes needed there.

- [ ] **Step 2: Run all backend tests (GREEN)**

```bash
cd backend && source ../venv/bin/activate && python -m pytest tests/api/test_youth_consent_fields.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 3: Run full backend test suite to confirm no regressions**

```bash
cd backend && source ../venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_postgresql_migration.py
```

Expected: All previously passing tests still PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/app/repositories/memory.py
git commit -m "feat(backend): wire consent fields through in-memory repository"
```

---

## Task 6: Write migration script

**Files:**
- Create: `backend/migrations/add_consent_fields_2026.py`

- [ ] **Step 1: Create the migration script**

```python
"""
Migration script for adding consent fields to persons table (2026).

Adds parental_permission_2026 and photo_consent_2026 boolean columns
to the persons table. Existing rows receive FALSE as the default.

Usage:
    cd backend && python migrations/add_consent_fields_2026.py

Safety:
- Only adds new columns with safe defaults
- Never drops or modifies existing columns
- Idempotent (safe to run multiple times)
"""

import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine, text
from app.database import get_database_url


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = :table AND column_name = :col
                )
            """),
            {"table": table_name, "col": column_name},
        )
        return result.scalar()


def add_consent_fields():
    database_url = get_database_url()
    print(f"Starting migration: add consent fields (2026)")
    print(f"Database: {database_url.split('@')[-1] if '@' in database_url else 'Local'}")

    engine = create_engine(database_url)

    new_columns = [
        {
            "name": "parental_permission_2026",
            "sql": "ALTER TABLE persons ADD COLUMN parental_permission_2026 BOOLEAN NOT NULL DEFAULT FALSE",
        },
        {
            "name": "photo_consent_2026",
            "sql": "ALTER TABLE persons ADD COLUMN photo_consent_2026 BOOLEAN NOT NULL DEFAULT FALSE",
        },
    ]

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for col in new_columns:
                if check_column_exists(engine, "persons", col["name"]):
                    print(f"Column '{col['name']}' already exists — skipping")
                    continue
                print(f"Adding column: {col['name']}")
                conn.execute(text(col["sql"]))
                print(f"Added column: {col['name']}")
            trans.commit()
            print("Migration completed successfully.")
        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {e}")
            print("Rollback instructions:")
            for col in new_columns:
                print(f"  ALTER TABLE persons DROP COLUMN IF EXISTS {col['name']};")
            return False

    # Verify
    print("\nVerifying:")
    for col in new_columns:
        exists = check_column_exists(engine, "persons", col["name"])
        print(f"  {'OK' if exists else 'MISSING'}: {col['name']}")

    return True


def main():
    print("=" * 60)
    print("YOUTHAROOT DB MIGRATION — Add consent fields 2026")
    print("=" * 60)
    response = input("\nThis will modify the database. Continue? (y/N): ")
    if response.lower() not in ("y", "yes"):
        print("Migration cancelled.")
        return
    success = add_consent_fields()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/migrations/add_consent_fields_2026.py
git commit -m "feat(backend): add migration script for consent fields 2026"
```

---

## Task 7: Write frontend tests (RED)

**Files:**
- Create: `frontend/src/test/components/PersonForm.test.jsx`

- [ ] **Step 1: Create the test file**

```jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import PersonForm from '../../components/PersonForm.jsx';

vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn(),
}));

vi.mock('@mui/material/styles', () => ({
  ThemeProvider: ({ children }) => children,
  createTheme: () => ({}),
}));

const baseYouth = {
  id: 1,
  first_name: 'Alex',
  last_name: 'Smith',
  birth_date: '2010-06-15',
  person_type: 'youth',
  parental_permission_2026: false,
  photo_consent_2026: false,
};

describe('PersonForm - Youth consent checkboxes', () => {
  it('renders Parental Permission checkbox on Personal Info tab', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).toBeInTheDocument();
  });

  it('renders Photo Consent checkbox on Personal Info tab', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Photo Consent')).toBeInTheDocument();
  });

  it('defaults both checkboxes to unchecked when creating a new youth', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).not.toBeChecked();
    expect(screen.getByLabelText('Photo Consent')).not.toBeChecked();
  });

  it('reflects true values from existing youth record', () => {
    const youth = { ...baseYouth, parental_permission_2026: true, photo_consent_2026: true };
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={youth}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).toBeChecked();
    expect(screen.getByLabelText('Photo Consent')).toBeChecked();
  });

  it('reflects mixed values from existing youth record', () => {
    const youth = { ...baseYouth, parental_permission_2026: true, photo_consent_2026: false };
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={youth}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).toBeChecked();
    expect(screen.getByLabelText('Photo Consent')).not.toBeChecked();
  });

  it('defaults null consent values to unchecked (defensive — old records)', () => {
    const youth = { ...baseYouth, parental_permission_2026: null, photo_consent_2026: null };
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={youth}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).not.toBeChecked();
    expect(screen.getByLabelText('Photo Consent')).not.toBeChecked();
  });

  it('does not render consent checkboxes for leader form', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="leader"
      />
    );
    expect(screen.queryByLabelText('Parental Permission')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Photo Consent')).not.toBeInTheDocument();
  });

  it('does not render consent checkboxes for parent form', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="parent"
      />
    );
    expect(screen.queryByLabelText('Parental Permission')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Photo Consent')).not.toBeInTheDocument();
  });

  it('checkbox is interactive — toggling updates state', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="youth"
      />
    );
    const checkbox = screen.getByLabelText('Parental Permission');
    expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    fireEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });
});
```

- [ ] **Step 2: Run frontend tests to confirm they fail (RED)**

```bash
cd frontend && npm run test:run -- src/test/components/PersonForm.test.jsx
```

Expected: All tests FAIL — checkboxes not yet rendered.

---

## Task 8: Update PersonForm (GREEN)

**Files:**
- Modify: `frontend/src/components/PersonForm.jsx`

- [ ] **Step 1: Add defaults to the initial `useState` call**

In the `useState` initializer (around line 31), add both fields to the base object **before** the `...person` spread:

```js
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone_number: '',
    sms_opt_out: false,
    parental_permission_2026: false,
    photo_consent_2026: false,
    grade: '',
    school_name: '',
    // ... rest of existing fields unchanged
    ...person
  });
```

- [ ] **Step 2: Update the null-coercion loop in the `useEffect` on `[person]`**

In the first `useEffect` (around line 56), add both fields to the `baseData` object:

```js
    const baseData = {
      first_name: '',
      last_name: '',
      phone_number: '',
      sms_opt_out: false,
      parental_permission_2026: false,
      photo_consent_2026: false,
      // ... rest of existing fields unchanged
      ...(person || {}),
    };
```

Then update the null-coercion loop to handle the new boolean fields:

```js
    Object.keys(baseData).forEach(key => {
      if (baseData[key] === null || baseData[key] === undefined) {
        if (key === 'sms_opt_out' || key === 'parental_permission_2026' || key === 'photo_consent_2026') {
          baseData[key] = false;
        } else if (key === 'grade') {
          baseData[key] = '';
        } else {
          baseData[key] = '';
        }
      }
    });
```

- [ ] **Step 3: Apply identical changes to the `useEffect` on `[open, person]`**

The second `useEffect` (around line 95) has the same `baseData` initialization and the same null-coercion loop. Apply the same changes as Step 2 to this block as well.

- [ ] **Step 4: Add checkboxes to the Personal Info tab UI**

In the Personal Info tab (`tabValue === 0`), find the existing Grid container that holds the grade/birth-date/SMS opt-out row and add two new `Grid item` entries after the existing SMS opt-out item:

```jsx
                    {formData.phone_number && (
                      <Grid item xs={6} sm={6}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={formData.sms_opt_out}
                              onChange={(e) => setFormData({ ...formData, sms_opt_out: e.target.checked })}
                            />
                          }
                          label="SMS Opt out"
                        />
                      </Grid>
                    )}
                    <Grid item xs={6} sm={6}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.parental_permission_2026}
                            onChange={(e) => setFormData({ ...formData, parental_permission_2026: e.target.checked })}
                          />
                        }
                        label="Parental Permission"
                      />
                    </Grid>
                    <Grid item xs={6} sm={6}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.photo_consent_2026}
                            onChange={(e) => setFormData({ ...formData, photo_consent_2026: e.target.checked })}
                          />
                        }
                        label="Photo Consent"
                      />
                    </Grid>
```

- [ ] **Step 5: Add both fields to the youth `handleSubmit` payload**

In `handleSubmit`, find the `if (personType === 'youth')` block. After `personData.other_considerations = ...`, add:

```js
      personData.parental_permission_2026 = formData.parental_permission_2026 || false;
      personData.photo_consent_2026 = formData.photo_consent_2026 || false;
```

- [ ] **Step 6: Run frontend tests (GREEN)**

```bash
cd frontend && npm run test:run -- src/test/components/PersonForm.test.jsx
```

Expected: All 8 tests PASS.

- [ ] **Step 7: Run full frontend test suite to confirm no regressions**

```bash
cd frontend && npm run test:run
```

Expected: All previously passing tests still PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/PersonForm.jsx frontend/src/test/components/PersonForm.test.jsx
git commit -m "feat(frontend): add Parental Permission and Photo Consent checkboxes to youth form"
```

---

## Task 9: Final verification

- [ ] **Step 1: Run complete backend test suite**

```bash
cd backend && source ../venv/bin/activate && python -m pytest tests/ -v --ignore=tests/test_postgresql_migration.py
```

Expected: All tests PASS.

- [ ] **Step 2: Run complete frontend test suite**

```bash
cd frontend && npm run test:run
```

Expected: All tests PASS.

- [ ] **Step 3: Verify the migration script is runnable (dry check)**

```bash
cd backend && source ../venv/bin/activate && python -c "
import sys; sys.path.insert(0, '.')
from migrations.add_consent_fields_2026 import check_column_exists, add_consent_fields
print('Migration script imports OK')
"
```

Expected: `Migration script imports OK` with no errors.
