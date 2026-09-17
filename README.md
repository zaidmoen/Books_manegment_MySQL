# School, Class, and Book Management API

FastAPI + raw MySQL backend for managing schools, classes, books, and book reviews with JWT authentication and role-based access control.

## Snapshot

| Layer | Stack |
|---|---|
| API | FastAPI |
| Database | MySQL |
| Auth | JWT, `PyJWT` |
| Password hashing | `pwdlib` |
| Driver | `mysql-connector-python` |
| Validation | Pydantic v2 |

## What It Covers

- User registration and login
- Bearer-token authentication
- Admin-only create, update, patch, and delete actions
- School records with address and principal data
- Class records linked to schools
- Book records with filtering and sorting
- One review per user and book, with ratings from 1 to 5
- Versioned SQL migrations, including data backfills
- Direct SQL with parameterized queries, no ORM
- Public registration always creates a regular user account

## Data Model

| Table | Purpose |
|---|---|
| `users` | Authentication and roles |
| `schools` | School master data |
| `classes` | Classes linked to a school |
| `books` | Book catalog |
| `reviews` | Ratings and comments linked to users and books |
| `schema_migrations` | Applied SQL migration versions |

## Project Layout

```text
app/
  auth.py
  database.py
  main.py
  schemas.py
migrations/
  001_create_reviews_table.sql
  002_seed_existing_book_reviews.sql
setup.sql
requirements.txt
Book_Management_API_MySQL.postman_collection.json
postman/
```

## Environment

Copy `.env.example` to `.env` and adjust values:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=books_management
SECRET_KEY=replace-this-with-at-least-32-random-characters
```

`SECRET_KEY` is required and must contain at least 32 characters. A quick local
value can be generated with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

If your MySQL user cannot create databases automatically, run `setup.sql` once in MySQL Workbench or another MySQL client.

## Run

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Authentication Flow

1. Register a user with `POST /auth/register`.
2. Log in with `POST /auth/login`.
3. Paste the token into Swagger or send it as:

```http
Authorization: Bearer <token>
```

## API Surface

### Auth

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/auth/register` | No | - | Create a user |
| POST | `/auth/login` | No | - | Return a JWT token |
| GET | `/auth/me` | Yes | Any | Return the current user |

### Schools

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/schools` | Yes | Any | List schools |
| GET | `/schools/{school_id}` | Yes | Any | Get one school |
| POST | `/schools` | Yes | Admin | Create a school |
| PUT | `/schools/{school_id}` | Yes | Admin | Replace school data |
| PATCH | `/schools/{school_id}` | Yes | Admin | Update selected school fields |
| DELETE | `/schools/{school_id}` | Yes | Admin | Delete a school |

### Classes

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/classes` | Yes | Any | List classes |
| GET | `/classes/{class_id}` | Yes | Any | Get one class |
| POST | `/classes` | Yes | Admin | Create a class |
| PUT | `/classes/{class_id}` | Yes | Admin | Replace class data |
| PATCH | `/classes/{class_id}` | Yes | Admin | Update selected class fields |
| DELETE | `/classes/{class_id}` | Yes | Admin | Delete a class |

### Books

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/books` | Yes | Any | List books |
| GET | `/books/{book_id}` | Yes | Any | Get one book |
| POST | `/books` | Yes | Admin | Create a book |
| PUT | `/books/{book_id}` | Yes | Admin | Replace book data |
| PATCH | `/books/{book_id}` | Yes | Admin | Update selected book fields |
| DELETE | `/books/{book_id}` | Yes | Admin | Delete a book |

### Reviews

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/books/{book_id}/reviews/` | Yes | Any | Review a book once |
| GET | `/books/{book_id}/reviews/` | Yes | Any | List reviews for a book |

## Query Parameters

`GET /books`

- `author`: filter by author name
- `sort_by=published_year`: sort by year
- `order=asc|desc`: choose sort order

`GET /classes`

- `school_id`: filter classes by school
- `grade_level`: filter by grade name or level

## Example Payloads

### Register User

```json
{
  "username": "student",
  "password": "strong-password"
}
```

New accounts are always created with the `user` role. Admin access should be
granted directly in the database by someone who already manages the system;
it cannot be requested through the public registration endpoint.

### Create School

```json
{
  "name": "Al Noor School",
  "address": "Hebron",
  "principal_name": "M. Hassan"
}
```

### Create Class

```json
{
  "school_id": 1,
  "grade_level": "Grade 5",
  "section": "A",
  "room_number": "101",
  "capacity": 30
}
```

### Create Book

```json
{
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "published_year": 2008
}
```

### Create Review

```json
{
  "rating": 5,
  "comment": "Excellent book"
}
```

## Database Notes

- The app creates the core database tables and applies pending files from `migrations/` on startup.
- `002_seed_existing_book_reviews.sql` gives every existing book a default rating of `5`, using the oldest existing user. It safely inserts nothing when no user exists and never duplicates a user/book review.
- Tables:
  - `users`
  - `schools`
  - `classes`
  - `books`
  - `reviews`
- `reviews.user_id` and `reviews.book_id` use foreign keys with cascade delete.
- `(user_id, book_id)` is unique, so one user cannot review the same book twice.
- `classes.school_id` is linked to `schools.id` with cascade delete.

## Postman

The repository includes a Postman collection:

- `Book_Management_API_MySQL.postman_collection.json`

Import it into Postman, authenticate once, and reuse the Bearer token for the protected routes.

## Tests

Install the development requirements and run the test suite:

```bash
pip install -r requirements-dev.txt
pytest -q
```

GitHub Actions runs the same tests on every push and pull request.

## Security and Code Review Report

This section records the main findings from a small security and code-quality
review of the project.

### Fixed in this update

| Finding | Why it mattered | Change |
|---|---|---|
| A client could submit `role: admin` during registration | Anyone could give their own account admin permissions | Registration now rejects unknown fields and always stores the `user` role |
| JWT had a predictable fallback secret | Tokens could be forged when the environment variable was missing | The app now requires a secret of at least 32 characters |
| The role was copied into the JWT | A token could contain an old role after database permissions changed | Authorization continues to use the current role loaded from MySQL |
| Authentication rules had no automated tests | A later edit could bring the same issue back | Added focused tests and a GitHub Actions workflow |
| The registration example showed an admin account | The documentation encouraged an unsafe flow | Replaced it with a regular-user example and documented admin provisioning |

### Current limitations

- The tests cover the security-sensitive registration and token rules. Full API
  integration tests still require a temporary MySQL database.
- Admin provisioning is intentionally kept outside the public API. A future
  version could add a protected command-line script for this task.
- The API uses synchronous MySQL connections. This is reasonable for this
  learning project, but connection pooling would be useful before heavier use.

The goal of these changes is to keep the project understandable while making
its authentication boundary safer and easier to maintain.
