# BTick API – Documentation (backend, endterm)

Project: Event ticketing service (BTick).

Main models:

- **Organization** – organizer (name, website, contact email).
- **Venue** – venue (name, address, capacity).
- **EventCategory** – event category (Music, Conference, Sport, etc.).
- **Event** – event (FK for Organization, Venue, Category; title, description, starts_at, ends_at, status, capacity).
- **EventsTicket** – event ticket type (FK for Event, ticket_type, price, quota, sold).
- **Booking** – ticket reservation (FK for User and EventsTicket; quantity, status, expires_at).

Custom user (User): email is used as a unique login.
Authorization: **JWT** (djangorestframework-simplejwt).

---

## 1. Authentication and Users

### 1.1 User Registration

- **URL:** `/api/auth/register/`
- **Method:** `POST`
- **Auth:** Not required
- **Description:** Create a new user.

**Body (JSON):**

- `email` – string, **required**, unique login
- `password` – string, **required**
- `first_name` – string, optional
- `last_name` – string, optional

**Responses:**

- `201 Created` – user created
- `400 Bad Request` – invalid data / email already taken

---

### 1.2 Obtaining a JWT token (login)

- **URL:** `/api/auth/jwt/create/`
- **Method:** `POST`
- **Auth:** Not required
- **Description:** Issues a pair of `access` and `refresh` tokens.

**Body (JSON):**

- `email` – user email
- `password` – password

**Responses:**

- `200 OK` – `{ "access": "...", "refresh": "..." }`
- `401 Unauthorized` – invalid login/password

---

### 1.3 Refreshing the Access Token

- **URL:** `/api/auth/jwt/refresh/`
- **Method:** `POST`
- **Auth:** Not required
- **Description:** Refreshes `access` on `refresh`.

**Body (JSON):**

- `refresh` – a valid refresh token

**Responses:**

- `200 OK` – new `access`
- `401 Unauthorized` – invalid/expired refresh

---

## 2. Events API (11 endpoints)

**Base URL:** `/api/v1/events/`
Model: `Event` (organization, venue, category, title, description, starts_at, ends_at, status, capacity).

### 2.1 Event List

- **URL:** `/api/v1/events/`
- **Method:** `GET`
- **Permissions:** `AllowAny` (public)
- **Description:** List of published events.

**Filters (query params):**

- `category` – Category ID
- `status` – `DRAFT|PUBLISHED|CANCELLED`
- `starts_after` – Date/date-time (show events starting after this date)

---

### 2.2 Creating an Event

- **URL:** `/api/v1/events/`
- **Method:** `POST`
- **Permissions:** `IsAuthenticated` + custom `IsOrganizerOrAdmin`
- **Description:** Create a new event by an organizer/admin.

---

### 2.3 Event Details

- **URL:** `/api/v1/events/{id}/`
- **Method:** `GET`
- **Permissions:** `AllowAny`
- **Description:** Full event information.

---

### 2.4 Event Update

- **URL:** `/api/v1/events/{id}/`
- **Method:** `PUT`
- **Permissions:** `IsAuthenticated` + `CanManageEvent`
- **Description:** Full event update by the organization owner/manager.

---

### 2.5 Partial Update

- **URL:** `/api/v1/events/{id}/`
- **Method:** `PATCH`
- **Permissions:** `IsAuthenticated` + `CanManageEvent`

---

### 2.6 Deleting an Event

- **URL:** `/api/v1/events/{id}/`
- **Method:** `DELETE`
- **Permissions:** `IsAuthenticated` + `CanManageEvent`

---

### 2.7 My Events (Organizer)

- **URL:** `/api/v1/events/my-events/`
- **Method:** `GET`
- **Permissions:** `IsAuthenticated` + `IsOrganizerOrAdmin`
- **Description:** List of events for organizations where the current user is a member (OWNER/MANAGER/MEMBER).

---

### 2.8 Available Event Tickets

- **URL:** `/api/v1/events/{id}/available-tickets/`
- **Method:** `GET`
- **Permissions:** `AllowAny`
- **Description:** List of event ticket types with `quota > sold`, sorted by price.

---

### 2.9 Publishing an Event

- **URL:** `/api/v1/events/{id}/publish/`
- **Method:** `POST`
- **Permissions:** `IsAuthenticated` + `CanPublishEvent`
- **Description:** Translates an event from `DRAFT` to `PUBLISHED`.
- Checks: the event has not yet started, has not been canceled, and has at least one ticket.

---

### 2.10 Cancelling an Event

- **URL:** `/api/v1/events/{id}/cancel/`
- **Method:** `POST`
- **Permissions:** `IsAuthenticated` + `CanManageEvent`
- **Description:** Cancel an event (any status → `CANCELLED`).

---

### 2.11 Bookings by Event

- **URL:** `/api/v1/events/{id}/bookings/`
- **Method:** `GET`
- **Permissions:** `IsAuthenticated` + `IsOrganizationMember`
- **Description:** List of all bookings for this event (visible only to organization members).

---

## 3. Categories API (5 endpoints)

**Base URL:** `/api/v1/categories/`
Model: `EventCategory(name)`.

- **GET `/api/v1/categories/`** – list of categories, `AllowAny`
- **POST `/api/v1/categories/`** – create category, `IsAuthenticated + IsAdminOrReadOnly`
- **GET `/api/v1/categories/{id}/`** – category details, `AllowAny`
- **PUT/PATCH `/api/v1/categories/{id}/`** – update, `IsAuthenticated + IsAdminOrReadOnly`
- **DELETE `/api/v1/categories/{id}/`** – delete, `IsAuthenticated + IsAdminOrReadOnly`

---

## 4. Venues API (6 endpoints)

**Base URL:** `/api/v1/venues/`
Model: `Venue(name, address, capacity)`.

- **GET `/api/v1/venues/`** – list of venues, `AllowAny`
- **POST `/api/v1/venues/`** – create a venue, `IsAuthenticated + IsAdminOrReadOnly`
- **GET `/api/v1/venues/{id}/`** – venue details, `AllowAny`
- **PUT/PATCH `/api/v1/venues/{id}/`** – update, `IsAuthenticated + IsVenueManager`
- **DELETE `/api/v1/venues/{id}/`** – delete, `IsAuthenticated + IsAdminOrReadOnly`
- **GET `/api/v1/venues/{id}/schedule/`** – venue schedule
- Permissions: `AllowAny`
- Description: Future events published on this platform.

---

## 5. Organizations API (8 endpoints)

**Base URL:** `/api/v1/organizations/`
Models: `Organization` + membership (user role in the organization).

- **GET `/api/v1/organizations/`** – list, `AllowAny`
- **POST `/api/v1/organizations/`** – create organization, `IsAuthenticated + IsAdminOrReadOnly`
- **GET `/api/v1/organizations/{id}/`** – details, `AllowAny`
- **PUT/PATCH `/api/v1/organizations/{id}/`** – update, `IsAuthenticated + IsOrganizationOwnerOrManager`
- **DELETE `/api/v1/organizations/{id}/`** – delete, `IsAuthenticated + IsAdminOrReadOnly`

Custom actions:

### 5.1 Organization Events

- **URL:** `/api/v1/organizations/{id}/events/`
- **Method:** `GET`
- **Permissions:** `IsAuthenticated + IsOrganizationMember`
- **Description:**
- Members see all event statuses (including `DRAFT`),
- Outsiders see only `PUBLISHED`.

### 5.2 Organization Member List

- **URL:** `/api/v1/organizations/{id}/members/`
- **Method:** `GET`
- **Permissions:** `IsAuthenticated + IsOrganizationMember`
- **Description:** List of organization members with roles (`OWNER`, `MANAGER`, `MEMBER`).

### 5.3 Add a participant

- **URL:** `/api/v1/organizations/{id}/add-member/`
- **Method:** `POST`
- **Permissions:** `IsAuthenticated + IsOrganizationOwnerOrManager`
- **Body:**

```json
{ 
"user_email": "user@example.com", 
"role": "MANAGER"
}

## 6. Tickets API (5 endpoints)

**Base URL:** `/api/v1/tickets/`  
**Model:** `EventsTicket(event, ticket_type, price, quota, sold)`

### 6.1 Tickets endpoints overview

| #  | Method | URL                         | Permissions                          | Description                                     |
|----|--------|-----------------------------|--------------------------------------|-------------------------------------------------|
| 1  | GET    | `/api/v1/tickets/`         | `AllowAny`                           | List all ticket types                          |
| 2  | POST   | `/api/v1/tickets/`         | `IsAuthenticated + IsOrganizerOrAdmin` | Create a ticket type for an event             |
| 3  | GET    | `/api/v1/tickets/{id}/`    | `AllowAny`                           | Retrieve ticket type details                   |
| 4  | PUT    | `/api/v1/tickets/{id}/`    | `IsAuthenticated + IsOrganizerOrAdmin` | Full update of a ticket type                  |
| 5  | PATCH  | `/api/v1/tickets/{id}/`    | `IsAuthenticated + IsOrganizerOrAdmin` | Partial update of a ticket type               |
| 6  | DELETE | `/api/v1/tickets/{id}/`    | `IsAuthenticated + IsOrganizerOrAdmin` | Delete ticket type (only if `sold = 0`)       |

> **Permission note:**  
> `IsOrganizerOrAdmin` - the user must be the owner/manager of the organization that owns the event.

### 6.2 Tickets business rules

- When updating:
  - You can't set `quota < sold` (otherwise your inventory will be corrupted).
- When deleting:
  - Allowed to delete only if `sold = 0`, so as not to lose the history of sold tickets.

---

## 7. Bookings API (7 endpoints)

**Base URL:** `/api/v1/bookings/`  
**Model:** `Booking(user, event_ticket, quantity, status, expires_at)`

### 7.1 Bookings endpoints overview

| #  | Method | URL                                      | Permissions                         | Description                                              |
|----|--------|------------------------------------------|-------------------------------------|----------------------------------------------------------|
| 1  | GET    | `/api/v1/bookings/`                     | `IsAuthenticated`                   | List of user bookings / all for staff                    |
| 2  | POST   | `/api/v1/bookings/`                     | `IsAuthenticated + IsCustomer`      | Create a new booking                                     |
| 3  | GET    | `/api/v1/bookings/{id}/`                | `IsAuthenticated`                   | Booking details (owner or staff/support)                 |
| 4  | PATCH  | `/api/v1/bookings/{id}/cancel/`         | `IsAuthenticated`                   | Cancel booking (owner or staff/support)                  |
| 5  | POST   | `/api/v1/bookings/{id}/confirm/`        | `IsAuthenticated + IsSupportOrAdmin`| Confirm PENDING booking                                  |
| 6  | POST   | `/api/v1/bookings/{id}/refund/`         | `IsAuthenticated + CanRefundBooking`| Refund a confirmed booking                               |
| 7  | DELETE | `/api/v1/bookings/{id}/`                | —                                   | **Not allowed**, always returns `405 Method Not Allowed` |

### 7.2 List of my / all bookings

- **URL:** `/api/v1/bookings/`  
- **Method:** `GET`  
- **Permissions:** `IsAuthenticated`

**Logic:**

- Regular user:
  - Sees only **his** reservations.
- User with status `staff` / `admin`:
  - Sees **all** bookings.

---

### 7.3 Creating a booking

- **URL:** `/api/v1/bookings/`  
- **Method:** `POST`  
- **Permissions:** `IsAuthenticated + IsCustomer`

**Request body (JSON):**

```json
{
  "event_ticket": 123,
  "quantity": 2
}

### 7.4 Cancelling a booking

- **URL:** `/api/v1/bookings/{id}/cancel/`  
- **Method:** `PATCH`  
- **Permissions:** `IsAuthenticated` (owner или staff/support)

**Description:**

- Changes the reservation status:
  - `PENDING` → `CANCELLED`
  - `CONFIRMED` → `CANCELLED`
- Atomically returns tickets to inventory:
  - `event_ticket.sold -= quantity`
- You cannot cancel a reservation if the event has already taken place..

---

### 7.5 Booking confirmation (support)

- **URL:** `/api/v1/bookings/{id}/confirm/`  
- **Method:** `POST`  
- **Permissions:** `IsAuthenticated + IsSupportOrAdmin`

**Description:**

- Transfers the reservation from `PENDING` → `CONFIRMED`
- Resets `expires_at` (confirmed reservations no longer expire)
- Checks before changing:
  - that the reservation has not yet expired,
  - the event did not take place.

---

### 7.6 Refund

- **URL:** `/api/v1/bookings/{id}/refund/`  
- **Method:** `POST`  
- **Permissions:** `IsAuthenticated + CanRefundBooking`

**Description:**

- Logically formalizes the return:
  - reservation status → `CANCELLED`
- Returns tickets to inventory **only if** the reservation status was `CONFIRMED`:
  - `event_ticket.sold -= quantity` (but not lower than 0, taking into account atomicity)
- Used for refund scenarios (support/organization managers).

---

### 7.7 Deleting a booking

- **URL:** `/api/v1/bookings/{id}/`  
- **Method:** `DELETE`  
- **Response:** `405 Method Not Allowed`

**Description:**

- Hard deletion of reservations is prohibited.  
- Instead you should use:
  - `/cancel/` — for logical cancellation
  - `/refund/` — for a return with correct inventory adjustments

---

## 8. Seed Command (filling the DB with test data)

**Command (local / Cloud Shell):**

```bash
python ./settings/manage.py seed --flush \
  --users 20 --orgs 5 --venues 6 --cats 6 --events 12 --bookings 80 \
  --settings=settings.local

### 8.1. Options

When executing the command:

```bash
python ./settings/manage.py seed --flush \
  --users 20 --orgs 5 --venues 6 --cats 6 --events 12 --bookings 80 \
  --settings=settings.local

The following options are used:

--flush – clears old data (except for superusers) before seeding.

--users / --orgs / --venues / --cats / --events / --bookings –
specify the number of records of each type to be created.

8.2. What the command generates

The seed command creates a linked test data structure:

Users

Test users (email + password password123 or similar).

Organizations, Venues, Categories

Test entities for events:

organizations,

venues,

event categories.

Events – future events:

starts_at and ends_at are in the future;

the rule ends_at > starts_at is observed;

DRAFT and PUBLISHED statuses are used;

capacity – an optional field (can be specified or NULL).

Tickets per event (EventsTicket):

Several ticket types for each event:

STANDARD, VIP, EARLY_BIRD, STUDENT, GROUP;

Each ticket has its own:

price,

quota,

initial value sold = 0.

Bookings — bookings:

quantity ≥ 2 (corresponds to CheckConstraint in the model);

statuses: PENDING, CONFIRMED, CANCELLED;

correct expires_at logic for PENDING
(usually 1 day before the event).

After generation, the sold field for tickets is recalculated:

the sum of quantity for all CONFIRMED bookings is calculated (using Sum);

the sold value for each ticket is capped above its quota.

9. Auto-generated documentation (drf-spectacular)

The project is configured with drf-spectacular to generate the OpenAPI schema and interactive documentation.

Available endpoints:

Schema (YAML/JSON):
GET /api/schema/

Swagger UI:
GET /api/schema/swagger/

Redoc:
GET /api/schema/redoc/

Documentation is generated automatically based on:

DRF serializers;

viewsets and generic views;

configured permissions;

routes described in urls.py.