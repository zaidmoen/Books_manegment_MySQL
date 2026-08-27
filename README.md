# Book Management API - FastAPI + Raw MySQL

Book Management API is a FastAPI service that talks directly to MySQL with parameterized raw SQL. It does not use an ORM.

## Overview

- Register and authenticate users with JWT
- Protect all book routes with Bearer token auth
- Restrict create, update, patch, and delete actions to `admin` users
- Filter books by author and sort by `published_year`
- Initialize the database and tables on startup

## Tech Stack

- FastAPI
- MySQL
- `mysql-connector-python`
- `PyJWT`
- `pwdlib`
- Pydantic v2

## Project Structure

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

## Requirements

- Python 3.10+
- MySQL server running locally or remotely

## Environment Variables

Copy `.env.example` to `.env` and set your values:

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

Edit `.env` before starting the app.

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
3. Copy the returned token into the `Authorize` button in Swagger, or send it as:

```http
Authorization: Bearer <token>
```

## API Endpoints

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/` | No | - | Health message |
| POST | `/auth/register` | No | - | Create a user |
| POST | `/auth/login` | No | - | Return JWT token |
| GET | `/auth/me` | Yes | Any | Return current user |
| GET | `/books` | Yes | Any | List books |
| GET | `/books/{book_id}` | Yes | Any | Get one book |
| POST | `/books` | Yes | Admin | Create a book |
| PUT | `/books/{book_id}` | Yes | Admin | Replace all book fields |
| PATCH | `/books/{book_id}` | Yes | Admin | Update selected book fields |
| DELETE | `/books/{book_id}` | Yes | Admin | Delete a book |

## Query Parameters

`GET /books` supports:

- `author`: filter books by author name
- `sort_by=published_year`: sort by year
- `order=asc|desc`: choose sort order when sorting by year

## Example Requests

### Register

```json
{
  "username": "admin",
  "password": "admin123",
  "role": "admin"
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

### Patch Book

```json
{
  "title": "Clean Code - Updated"
}
```

## Database Notes

- The app creates the configured database and tables on startup.
- Tables:
  - `users`
  - `books`
- If startup creation fails, use `setup.sql` manually.

## Postman

The repository includes a Postman collection:

- `Book_Management_API_MySQL.postman_collection.json`

Import it into Postman and set the Bearer token after login.
