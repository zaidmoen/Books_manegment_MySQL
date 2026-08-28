# School, Class, and Book Management API

FastAPI + raw MySQL backend for managing schools, classes, and books with JWT authentication and role-based access control.

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
- Direct SQL with parameterized queries, no ORM

## Data Model

| Table | Purpose |
|---|---|
| `users` | Authentication and roles |
| `schools` | School master data |
| `classes` | Classes linked to a school |
| `books` | Book catalog |

## Project Layout

```text
app/
  auth.py
  database.py
  main.py
  schemas.py
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
SECRET_KEY=replace-with-a-long-random-secret
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
  "username": "admin",
  "password": "admin123",
  "role": "admin"
}
```

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

## Database Notes

- The app creates the database and tables on startup.
- Tables:
  - `users`
  - `schools`
  - `classes`
  - `books`
- `classes.school_id` is linked to `schools.id` with cascade delete.

## Postman

The repository includes a Postman collection:

- `Book_Management_API_MySQL.postman_collection.json`

Import it into Postman, authenticate once, and reuse the Bearer token for the protected routes.
