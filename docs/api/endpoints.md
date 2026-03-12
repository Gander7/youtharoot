# API Endpoints

Base URL: `http://localhost:8000` (dev) | `https://api.youtharoot.app` (prod)

> **Auth note:** Most person/event/attendance endpoints currently have auth disabled (commented out). Group and SMS endpoints require a valid **Clerk** Bearer token: `Authorization: Bearer <clerk_session_token>`. The legacy `/users/login` endpoint issues its own JWT.

---

## People

### `GET /person/youth`
Returns all non-archived youth. Health fields (`allergies`, `other_considerations`) are omitted for privacy.

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "first_name": "Alex",
    "last_name": "Smith",
    "phone_number": "+19025550100",
    "sms_opt_out": false,
    "grade": 10,
    "school_name": "Halifax West",
    "birth_date": "2009-04-15",
    "email": "alex@example.com",
    "person_type": "youth",
    "emergency_contact_name": "Jane Smith",
    "emergency_contact_phone": "+19025550101",
    "emergency_contact_relationship": "mother",
    "emergency_contact_2_name": "",
    "emergency_contact_2_phone": "",
    "emergency_contact_2_relationship": ""
  }
]
```

---

### `GET /person/leaders`
Returns all non-archived leaders.

**Response** `200 OK`
```json
[
  {
    "id": 2,
    "first_name": "Jordan",
    "last_name": "Lee",
    "phone_number": "+19025550102",
    "sms_opt_out": false,
    "role": "Youth Leader",
    "birth_date": "1990-06-20",
    "person_type": "leader"
  }
]
```

---

### `GET /person/{person_id}`
Returns a single person (youth, leader, or parent) by ID. Includes all fields including health data.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `person_id` | `int` | Person ID |

**Response** `200 OK` — full Youth, Leader, or Parent object

**Errors**
- `404` — Person not found

---

### `POST /person`
Creates a new youth or leader.

**Request body** — `Youth` or `Leader` object
```json
{
  "first_name": "Alex",
  "last_name": "Smith",
  "birth_date": "2009-04-15",
  "grade": 10,
  "school_name": "Halifax West",
  "phone_number": "+19025550100",
  "person_type": "youth",
  "emergency_contact_name": "Jane Smith",
  "emergency_contact_phone": "+19025550101",
  "emergency_contact_relationship": "mother",
  "allergies": "peanuts",
  "other_considerations": ""
}
```

**Response** `200 OK` — created Youth or Leader object

**Errors**
- `422` — Validation error

---

### `PUT /person/{person_id}`
Updates an existing person (youth, leader, or parent).

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `person_id` | `int` | Person ID |

**Request body** — full Youth, Leader, or Parent object with updated fields

**Response** `200 OK` — updated person object

**Errors**
- `404` — Person not found
- `422` — Validation error

---

### `DELETE /person/{person_id}`
Archives (soft-deletes) a person.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `person_id` | `int` | Person ID |

**Response** `200 OK`
```json
{}
```

---

## Parents

### `GET /parents`
Returns all non-archived parents.

**Response** `200 OK`
```json
[
  {
    "id": 3,
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "+19025550101",
    "email": "jane@example.com",
    "address": "123 Main St",
    "person_type": "parent"
  }
]
```

---

### `GET /parent/{parent_id}`
Returns a single parent by ID.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `parent_id` | `int` | Parent ID |

**Response** `200 OK` — Parent object

**Errors**
- `404` — Parent not found or person is not a parent

---

### `GET /parents/search`
Search parents by name, phone, or email.

**Query params**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | Yes | Search term |

**Response** `200 OK` — array of Parent objects

---

### `POST /parent`
Creates a new parent.

**Request body**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "person_type": "parent",
  "phone_number": "+19025550101",
  "email": "jane@example.com",
  "address": "123 Main St"
}
```

**Response** `200 OK` — created Parent object

**Errors**
- `422` — Validation error

---

### `GET /youth/{youth_id}/parents`
Returns all parents linked to a youth, including relationship details.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `youth_id` | `int` | Youth ID |

**Response** `200 OK`
```json
[
  {
    "id": 3,
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "+19025550101",
    "person_type": "parent",
    "relationship_type": "mother",
    "is_primary_contact": true
  }
]
```

---

### `POST /youth/{youth_id}/parents`
Links a parent to a youth.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `youth_id` | `int` | Youth ID |

**Request body**
```json
{
  "parent_id": 3,
  "relationship_type": "mother",
  "is_primary_contact": true
}
```

Valid `relationship_type` values: `mother`, `father`, `parent`, `guardian`, `step-parent`, `grandparent`, `other`

**Response** `200 OK` — relationship object

**Errors**
- `400` — Parent already linked or person is wrong type
- `404` — Youth or parent not found

---

### `PUT /youth/{youth_id}/parents/{parent_id}`
Updates a parent-youth relationship.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `youth_id` | `int` | Youth ID |
| `parent_id` | `int` | Parent ID |

**Request body**
```json
{
  "relationship_type": "guardian",
  "is_primary_contact": false
}
```

**Response** `200 OK` — updated relationship object

---

### `DELETE /youth/{youth_id}/parents/{parent_id}`
Removes a parent-youth link.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `youth_id` | `int` | Youth ID |
| `parent_id` | `int` | Parent ID |

**Response** `200 OK`
```json
{ "success": true }
```

**Errors**
- `404` — Relationship not found

---

### `GET /parents/{parent_id}/youth`
Returns all youth linked to a parent.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `parent_id` | `int` | Parent ID |

**Response** `200 OK` — array of youth with relationship details

---

## Events

### `GET /events`
Returns events, optionally filtered.

**Query params**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `days` | `int` | No | Return events within the next N days |
| `name` | `string` | No | Filter by event name (partial match) |

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Youth Group",
    "date": "2026-03-15",
    "desc": "Regular weekly meeting",
    "start_time": "19:00",
    "end_time": "21:00",
    "location": "Main Hall",
    "start_datetime": "2026-03-15T23:00:00Z",
    "end_datetime": "2026-03-16T01:00:00Z",
    "youth": [],
    "leaders": [],
    "youth_count": 0,
    "leaders_count": 0,
    "youth_checked_out": 0,
    "leaders_checked_out": 0
  }
]
```

---

### `GET /event/{event_id}`
Returns a single event by ID.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `event_id` | `int` | Event ID |

**Response** `200 OK` — Event object

**Errors**
- `404` — Event not found

---

### `POST /event`
Creates a new event. Times are interpreted as Halifax (America/Halifax) timezone and stored as UTC.

**Request body**
```json
{
  "name": "Youth Group",
  "date": "2026-03-15",
  "desc": "Regular weekly meeting",
  "start_time": "19:00",
  "end_time": "21:00",
  "location": "Main Hall"
}
```

**Response** `200 OK` — created Event object

---

### `PUT /event/{event_id}`
Updates an event. All fields are optional — only provided fields are updated.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `event_id` | `int` | Event ID |

**Request body**
```json
{
  "name": "Special Event",
  "location": "Gym"
}
```

**Response** `200 OK` — updated Event object

**Errors**
- `404` — Event not found

---

### `DELETE /event/{event_id}`
Deletes an event. Fails if the event has attendees.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `event_id` | `int` | Event ID |

**Response** `200 OK`
```json
{ "message": "Event deleted successfully" }
```

**Errors**
- `404` — Event not found
- `409` — Event has attendees and cannot be deleted

---

### `GET /event/{event_id}/can-delete`
Checks whether an event can be safely deleted.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `event_id` | `int` | Event ID |

**Response** `200 OK`
```json
{ "can_delete": false, "has_attendees": true }
```

---

## Attendance

### `GET /event/{event_id}/attendance`
Returns all attendance records for an event.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `event_id` | `int` | Event ID |

**Response** `200 OK`
```json
[
  {
    "person_id": 1,
    "first_name": "Alex",
    "last_name": "Smith",
    "person_type": "youth",
    "check_in": "2026-03-15T23:05:00Z",
    "check_out": null,
    "grade": 10,
    "school_name": "Halifax West",
    "role": null
  }
]
```

---

### `POST /event/{event_id}/checkin`
Checks a person in to an event.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `event_id` | `int` | Event ID |

**Request body**
```json
{ "person_id": 1 }
```

**Response** `200 OK`
```json
{
  "message": "Person checked in successfully",
  "check_in": "2026-03-15T23:05:00Z"
}
```

**Errors**
- `404` — Event or person not found
- `409` — Person already checked in

---

### `PUT /event/{event_id}/checkout`
Checks a person out of an event.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `event_id` | `int` | Event ID |

**Request body**
```json
{ "person_id": 1 }
```

**Response** `200 OK`
```json
{
  "message": "Person checked out successfully",
  "check_out": "2026-03-16T00:55:00Z"
}
```

**Errors**
- `404` — Event not found or person not checked in
- `409` — Person already checked out

---

### `PUT /event/{event_id}/checkout-all`
Checks out all people still checked in to an event.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `event_id` | `int` | Event ID |

**Response** `200 OK`
```json
{
  "message": "Successfully checked out 12 people",
  "checked_out_count": 12,
  "people": [
    {
      "person_id": 1,
      "first_name": "Alex",
      "last_name": "Smith",
      "check_out": "2026-03-16T01:00:00Z"
    }
  ],
  "check_out_time": "2026-03-16T01:00:00Z"
}
```

---

## Users

All `/users` endpoints use the prefix `/users`. The legacy JWT token returned by `/users/login` expires after **2 hours**.

### `POST /users/login`
Authenticates a user and returns a JWT token.

**Request body**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2026-01-01T00:00:00"
  }
}
```

**Errors**
- `401` — Incorrect username or password

---

### `GET /users/`
Returns all users.

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2026-01-01T00:00:00"
  }
]
```

---

### `GET /users/{user_id}`
Returns a single user.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `user_id` | `int` | User ID |

**Response** `200 OK` — UserResponse object

**Errors**
- `404` — User not found

---

### `POST /users/`
Creates a new user.

**Request body**
```json
{
  "username": "newleader",
  "password": "securepassword",
  "role": "user"
}
```

Valid `role` values: `admin`, `user`

**Response** `201 Created` — UserResponse object

**Errors**
- `400` — Username already exists

---

### `PUT /users/{user_id}`
Updates a user.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `user_id` | `int` | User ID |

**Request body**
```json
{
  "username": "newleader",
  "password": "newpassword",
  "role": "user"
}
```

**Response** `200 OK` — updated UserResponse object

---

### `DELETE /users/{user_id}`
Deletes a user. Cannot delete your own account.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `user_id` | `int` | User ID |

**Response** `204 No Content`

**Errors**
- `400` — Cannot delete your own account
- `404` — User not found

---

## Groups

> **Auth required:** All `/groups` endpoints require a Clerk Bearer token.

All group endpoints use the prefix `/groups`. Groups are scoped to the authenticated Clerk user — each user can only see and manage their own groups.

### `GET /groups`
Lists all groups owned by the current user.

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Senior Youth",
    "description": "Grades 10-12",
    "is_active": true,
    "created_by": "user_abc123",
    "member_count": 8,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  }
]
```

---

### `GET /groups/{group_id}`
Returns a single group.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |

**Response** `200 OK` — MessageGroup object

**Errors**
- `404` — Group not found

---

### `POST /groups`
Creates a new group.

**Request body**
```json
{
  "name": "Senior Youth",
  "description": "Grades 10-12",
  "is_active": true
}
```

**Response** `201 Created` — MessageGroup object

**Errors**
- `400` — Validation error (e.g. duplicate name)

---

### `PUT /groups/{group_id}`
Updates a group.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |

**Request body** (all fields optional)
```json
{
  "name": "Renamed Group",
  "description": "Updated description",
  "is_active": false
}
```

**Response** `200 OK` — updated MessageGroup object

**Errors**
- `404` — Group not found

---

### `DELETE /groups/{group_id}`
Deletes a group and all its memberships.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |

**Response** `204 No Content`

**Errors**
- `404` — Group not found

---

### `GET /groups/{group_id}/members`
Lists all members of a group with person details.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "group_id": 1,
    "person_id": 5,
    "added_by": 1,
    "joined_at": "2026-01-10T00:00:00Z",
    "person": {
      "id": 5,
      "first_name": "Alex",
      "last_name": "Smith",
      "person_type": "youth",
      "grade": 10,
      "school_name": "Halifax West",
      "birth_date": "2009-04-15"
    }
  }
]
```

---

### `POST /groups/{group_id}/members`
Adds a single person to a group.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |

**Request body**
```json
{ "person_id": 5 }
```

**Response** `201 Created` — MessageGroupMembership object

**Errors**
- `400` — Person already a member
- `404` — Group or person not found

---

### `POST /groups/{group_id}/members/bulk`
Adds multiple people to a group at once.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |

**Request body**
```json
{ "person_ids": [5, 6, 7, 8] }
```

**Response** `201 Created`
```json
{
  "added_count": 3,
  "skipped_count": 1,
  "failed_count": 0,
  "failed_person_ids": []
}
```

---

### `DELETE /groups/{group_id}/members/{person_id}`
Removes a person from a group.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |
| `person_id` | `int` | Person ID |

**Response** `204 No Content`

**Errors**
- `404` — Group not found or person is not a member

---

### `GET /groups/{group_id}/available-members`
Returns all persons (youth, leaders, parents) who could be added to the group, categorized by type.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |

**Response** `200 OK`
```json
{
  "youth": [ { "id": 1, "first_name": "Alex", "person_type": "youth", "..." : "..." } ],
  "leaders": [ { "id": 2, "first_name": "Jordan", "person_type": "leader", "..." : "..." } ],
  "parents": [ { "id": 3, "first_name": "Jane", "person_type": "parent", "..." : "..." } ]
}
```

---

## SMS

> **Auth required:** All `/api/sms` endpoints require a Clerk Bearer token.
> **Service required:** Twilio must be configured (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`). Returns `503` if not configured.

All SMS endpoints use the prefix `/api/sms`.

---

### `POST /api/sms/send`
Sends an SMS to an individual phone number. Respects opt-out status.

**Request body**
```json
{
  "phone_number": "+19025550100",
  "message": "Don't forget youth group tonight at 7pm!",
  "person_id": 1
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | Yes | E.164 format (e.g. `+19025550100`) |
| `message` | `string` | Yes | 1–1600 characters |
| `person_id` | `int` | No | Used to check opt-out status |

**Response** `200 OK`
```json
{
  "success": true,
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "sent",
  "error": null
}
```

**Errors**
- `400` — Person has opted out of SMS
- `503` — SMS service not configured

---

### `POST /api/sms/send-group`
Sends an SMS to all eligible members of a group. Automatically skips opted-out members and deduplicates phone numbers.

**Request body**
```json
{
  "group_id": 1,
  "message": "Youth group is cancelled tonight.",
  "include_parents": false,
  "parent_message": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `group_id` | `int` | Yes | Target group ID |
| `message` | `string` | Yes | 1–1600 characters |
| `include_parents` | `bool` | No | Also message linked parents (default `false`) |
| `parent_message` | `string` | No | Custom message for parents |

**Response** `200 OK`
```json
{
  "success": true,
  "sent_count": 10,
  "skipped_count": 2,
  "failed_count": 0,
  "parent_count": 0,
  "results": [
    {
      "person_id": 1,
      "phone_number": "+19025550100",
      "person_type": "youth",
      "success": true,
      "message_sid": "SMxxxxxxxx",
      "message_sent": "Youth group is cancelled tonight.",
      "status": "sent",
      "error": null
    }
  ],
  "parent_recipients": null
}
```

**Errors**
- `400` — No eligible recipients (all opted out)
- `404` — Group not found

---

### `GET /api/sms/history`
Returns paginated SMS message history.

**Query params**
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `group_id` | `int` | No | — | Filter by group |
| `limit` | `int` | No | `50` | Max results (1–100) |
| `offset` | `int` | No | `0` | Pagination offset |

**Response** `200 OK`
```json
{
  "messages": [
    {
      "id": 1,
      "content": "Youth group is cancelled tonight.",
      "status": "delivered",
      "group_id": 1,
      "recipient_phone": "+19025550100",
      "recipient_person_id": 1,
      "sent_by": "user_abc123",
      "twilio_sid": "SMxxxxxxxx",
      "sent_at": "2026-03-15T23:05:00Z",
      "delivered_at": "2026-03-15T23:05:10Z",
      "created_at": "2026-03-15T23:05:00Z"
    }
  ],
  "total_count": 42,
  "group_id": null
}
```

> Returns empty results in memory mode.

---

### `GET /api/sms/history/top-level`
Returns a summarized message history: individual messages and group sends collapsed into one row per send.

**Query params**
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `days` | `int` | No | `30` | Look back N days (1–365) |
| `limit` | `int` | No | `50` | Max results (1–100) |
| `offset` | `int` | No | `0` | Pagination offset |

**Response** `200 OK`
```json
{
  "messages": [
    {
      "id": 1,
      "message_type": "group",
      "content": "Youth group is cancelled tonight.",
      "created_at": "2026-03-15T23:05:00Z",
      "sent_by": "user_abc123",
      "group_id": 1,
      "group_name": "Senior Youth",
      "total_recipients": 10,
      "sent_count": 8,
      "delivered_count": 7,
      "failed_count": 0,
      "pending_count": 1
    },
    {
      "id": 5,
      "message_type": "individual",
      "content": "Can you make it tonight?",
      "created_at": "2026-03-14T18:00:00Z",
      "sent_by": "user_abc123",
      "recipient_name": "Alex Smith",
      "recipient_phone": "+19025550100",
      "status": "delivered"
    }
  ],
  "total_count": 2
}
```

---

### `GET /api/sms/history/group/{group_id}/details`
Returns per-recipient status for a specific group message send.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Group ID |

**Query params**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `message_content` | `string` | Yes | Exact message text to identify the send |
| `send_time` | `string` | Yes | ISO timestamp of the send (e.g. `2026-03-15T23:05:00Z`) |

**Response** `200 OK`
```json
[
  {
    "person_id": 1,
    "person_name": "Alex Smith",
    "phone_number": "+19025550100",
    "status": "delivered",
    "twilio_sid": "SMxxxxxxxx",
    "sent_at": "2026-03-15T23:05:00Z",
    "delivered_at": "2026-03-15T23:05:10Z",
    "failed_at": null,
    "failure_reason": null
  }
]
```

**Errors**
- `400` — Invalid `send_time` format
- `404` — No messages found matching the criteria

---

### `GET /api/sms/status/{message_id}`
Returns the delivery status of a specific message by database ID.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `message_id` | `int` | Message DB ID |

**Response** `200 OK`
```json
{
  "id": 1,
  "content": "Youth group is cancelled tonight.",
  "status": "delivered",
  "channel": "sms",
  "group_id": 1,
  "sent_by": "user_abc123",
  "twilio_sid": "SMxxxxxxxx",
  "sent_at": "2026-03-15T23:05:00Z",
  "delivered_at": "2026-03-15T23:05:10Z",
  "failed_at": null,
  "failure_reason": null,
  "created_at": "2026-03-15T23:05:00Z",
  "updated_at": "2026-03-15T23:05:10Z"
}
```

**Errors**
- `404` — Message not found

---

### `POST /api/sms/webhook`
Twilio webhook endpoint for receiving delivery status updates. Called by Twilio, not by clients directly.

**Form fields** (sent by Twilio)
| Field | Description |
|-------|-------------|
| `MessageSid` | Twilio message SID |
| `MessageStatus` | New status (`sent`, `delivered`, `failed`, etc.) |
| `To` | Recipient phone number |
| `From` | Sender phone number |
| `ErrorCode` | Twilio error code (if failed) |

**Response** `200 OK`
```json
{
  "status": "processed",
  "message_sid": "SMxxxxxxxx",
  "updated": true
}
```

---

### `GET /api/sms/analytics`
Returns SMS delivery statistics and cost tracking.

**Query params**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `start_date` | `string` | No | `YYYY-MM-DD` filter start |
| `end_date` | `string` | No | `YYYY-MM-DD` filter end |

**Response** `200 OK`
```json
{
  "total_sent": 150,
  "total_delivered": 142,
  "total_failed": 3,
  "delivery_rate": 94.67,
  "total_cost": 1.245,
  "date_range": {
    "start_date": "2026-01-01",
    "end_date": "2026-03-12"
  },
  "youth_messages": 120,
  "parent_messages": 30,
  "parent_notification_rate": 0.25,
  "opt_out_rate": 0.1
}
```

---

## General

### `GET /`
Health check — confirms API is running.

**Response** `200 OK`
```json
{ "message": "Youtharoot API is running", "status": "ok" }
```

### `GET /health`
Returns runtime configuration info.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "database_type": "memory",
  "debug": true
}
```
