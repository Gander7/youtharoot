# Design: Youth Consent Boolean Fields (2026)

**Date:** 2026-04-01

## Overview

Add two boolean fields — `parental_permission_2026` and `photo_consent_2026` — to the youth data model. Both default to `false`. They appear as checkboxes labelled "Parental Permission" and "Photo Consent" on the Personal Info tab of the youth form.

---

## 1. Database

Two new columns added to the `persons` table:

```sql
ALTER TABLE persons ADD COLUMN parental_permission_2026 BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE persons ADD COLUMN photo_consent_2026 BOOLEAN NOT NULL DEFAULT FALSE;
```

**Safety guarantees:**
- Existing rows receive `false` automatically via the column default — no data is modified or dropped.
- Migration script is idempotent: checks column existence before issuing `ALTER TABLE`, so it is safe to run multiple times.
- No tables are dropped or recreated. No existing columns are modified.

**Migration script:** `backend/migrations/add_consent_fields_2026.py`
Follows the existing pattern established by `add_sms_fields_to_persons.py`.

---

## 2. Backend

### `backend/app/db_models.py`

Add two columns to `PersonDB` under the youth-specific fields section:

```python
parental_permission_2026 = Column(Boolean, default=False, nullable=False)
photo_consent_2026 = Column(Boolean, default=False, nullable=False)
```

### `backend/app/models.py`

- **`Youth`** — add both fields with `bool` type and default `False`
- **`PersonCreate`** — add both as `Optional[bool] = False`
- **`PersonUpdate`** — add both as `Optional[bool] = None`

### `backend/app/repositories/postgresql.py`

Three locations:

1. **`_db_to_dict`** (used by all unified API responses) — add both fields to the youth section of the result dict
2. **`create_person_unified`** — set both fields on `db_person` when `person_type == "youth"`
3. **`update_person_unified`** — already uses `model_dump(exclude_unset=True)` + `setattr`, so no changes needed as long as `PersonUpdate` and `PersonDB` have the fields

### `backend/app/repositories/memory.py`

Add both fields to the in-memory youth data mapping (read and write paths), defaulting to `False`.

---

## 3. Frontend

### `frontend/src/components/PersonForm.jsx`

#### Form state — three locations

The form initializes state in three places. All three need the new fields added with `false` as the base default:

1. **Initial `useState`** — add `parental_permission_2026: false` and `photo_consent_2026: false` to the base object before the `...person` spread
2. **`useEffect` on `[person]`** — same base defaults, plus add explicit boolean coercion in the null-handling loop (currently only `sms_opt_out` is coerced to `false`; the new fields must be treated the same way to prevent `null` → `''`)
3. **`useEffect` on `[open, person]`** — identical changes as #2

Edge cases handled:

| Scenario | Incoming value | Result |
|---|---|---|
| New youth | `person = null` | `false` (base default) |
| Existing youth, field set | `true` or `false` | Used as-is (spread from `person`) |
| Existing youth, field null (defensive) | `null` | Coerced to `false` in null-handler |

#### UI — Personal Info tab

Add two `<FormControlLabel><Checkbox>` controls in the Personal Info tab (tab index 0), grouped alongside the existing grade/birth-date/SMS opt-out row:

```jsx
<FormControlLabel
  control={
    <Checkbox
      checked={formData.parental_permission_2026}
      onChange={(e) => setFormData({ ...formData, parental_permission_2026: e.target.checked })}
    />
  }
  label="Parental Permission"
/>
<FormControlLabel
  control={
    <Checkbox
      checked={formData.photo_consent_2026}
      onChange={(e) => setFormData({ ...formData, photo_consent_2026: e.target.checked })}
    />
  }
  label="Photo Consent"
/>
```

These checkboxes are **always visible** (not conditional on phone number like SMS opt-out).

#### Submit payload

In `handleSubmit`, include both fields in the youth `personData` block:

```js
personData.parental_permission_2026 = formData.parental_permission_2026 || false;
personData.photo_consent_2026 = formData.photo_consent_2026 || false;
```

---

## Files Changed

| File | Change |
|---|---|
| `backend/migrations/add_consent_fields_2026.py` | New migration script |
| `backend/app/db_models.py` | 2 new columns on `PersonDB` |
| `backend/app/models.py` | 2 new fields on `Youth`, `PersonCreate`, `PersonUpdate` |
| `backend/app/repositories/postgresql.py` | `_db_to_dict`, `create_person_unified` |
| `backend/app/repositories/memory.py` | In-memory youth read/write |
| `frontend/src/components/PersonForm.jsx` | State init (×3), UI checkboxes, submit payload |

---

## Out of Scope

- No display of these fields anywhere other than the youth form (e.g. no column in the people list, no filter)
- No backend validation beyond accepting a boolean value
- No database migration for the memory repository (in-memory data is ephemeral; `memory.py` still needs code updates so the fields work at runtime in dev mode)
