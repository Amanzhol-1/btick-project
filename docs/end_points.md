# BTick API Documentation

## Authentication & Users

### 1. Register user

- **URL:** `/api/auth/register/`
- **Method:** `POST`
- **Auth:** No
- **Description:** Create a new user. The email address (or phone number, depending on your model) is used as a unique identifier.
- **Request body (JSON):**
- `email` — string, required
- `password` — string, required
- `first_name` — string, optional
- `last_name` — string, optional
- **Responses:**
- `201 Created` — user successfully created
- `400 Bad Request` — invalid data

### 2. Obtain JWT token (login)

- **URL:** `/api/auth/jwt/create/`
- **Method:** `POST`
- **Auth:** No
- **Description:** Obtain a pair of `access` and `refresh` tokens. - **Request body (JSON):**
- `email` (or `username`) — string
- `password` — string
- **Responses:**
- `200 OK` — returns `access`, `refresh`
- `401 Unauthorized` — invalid login/password

### 3. Refresh JWT token

- **URL:** `/api/auth/jwt/refresh/`
- **Method:** `POST`
- **Auth:** No
- **Description:** Refresh the `access` token with `refresh`.

---

## Events & Tickets

### 4. List events

- **URL:** `/api/v1/events/`
- **Method:** `GET`
- **Auth:** Optional
- **Description:** Get a list of events. You can filter by category, status, and start date.
- **Query params (optional):**
- `category` — Category ID
- `status` — `DRAFT|PUBLISHED|CANCELLED`
- `starts_after` — date
- **Responses:**
- `200 OK` — list of events

### 5. Retrieve event

- **URL:** `/api/v1/events/{id}/`
- **Method:** `GET`
- **Auth:** Optional
- **Description:** Detailed information about the event.

### 6. List tickets for event

- **URL:** `/api/v1/events/{id}/tickets/`
- **Method:** `GET`
- **Auth:** Optional
- **Description:** List of ticket types for a specific event (Standard, VIP, etc.).

---

## Bookings

### 7. Create booking

- **URL:** `/api/v1/bookings/`
- **Method:** `POST`
- **Auth:** JWT (user must be logged in)
- **Description:** Book tickets for an event.
- **Request body:**
- `event_ticket` — ticket ID
- `quantity` — int, > 0
- **Responses:**
- `201 Created` — booking created
- `400 Bad Request` — insufficient quota, etc.
- `401 Unauthorized` — no token

### 8. List my bookings

- **URL:** `/api/bookings/`
- **Method:** `GET`
- **Auth:** JWT
- **Description:** List of bookings for the current user.

### 9. Cancel booking

- **URL:** `/api/v1/bookings/{id}/cancel/`
- **Method:** `POST` or `PATCH`
- **Auth:** JWT
- **Description:** Cancel a booking (status → `CANCELLED`), only available to the owner or admin.

---

## Admin / Organizer endpoints 

### 10. Create event (organizer)

- **URL:** `/api/v1/events/`
- **Method:** `POST`
- **Auth:** JWT + custom permission `IsOrganizerOrAdmin`
- **Description:** Create a new event.

---

### Seed-команда (autofilling the database with test data)

Run (Local / Cloud Shell):

```bash
python ./settings/manage.py seed --flush \
  --users 20 --orgs 5 --venues 6 --cats 6 --events 12 --bookings 80 \
  --settings=settings.local

--flush — clears old data before generation (except for superusers).

--users / --orgs / --venues / --cats / --events / --bookings — specify the volume of test data
