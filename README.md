# Book Management API — FastAPI + Raw MySQL

This version replaces **SQLite + SQLAlchemy ORM** with a direct MySQL connection:

```text
Postman -> FastAPI -> mysql-connector-python -> Raw SQL -> MySQL
```

Every database action uses raw, parameterized SQL through `cursor.execute()`.

## 1. Create the environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Linux/macOS:

```bash
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and enter your MySQL username and password. The MySQL server must be running. The API creates the configured database and its tables automatically. If your MySQL user cannot create databases, run `setup.sql` once in MySQL Workbench.

## 2. Run the API

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## Endpoints

| Method | Endpoint | Raw SQL operation |
|---|---|---|
| POST | `/auth/register` | INSERT user |
| POST | `/auth/login` | SELECT user |
| GET | `/auth/me` | SELECT user |
| GET | `/books` | SELECT books |
| GET | `/books/{id}` | SELECT one book |
| POST | `/books` | INSERT book |
| PUT | `/books/{id}` | UPDATE all book fields |
| PATCH | `/books/{id}` | UPDATE supplied fields only |
| DELETE | `/books/{id}` | DELETE book |

All book endpoints require a Bearer token. Creating, changing, or deleting a book requires an `admin` account.

## Quick test order

1. Register with role `admin` using `POST /auth/register`.
2. Log in at `POST /auth/login` using form-data.
3. Copy the returned token into Swagger's **Authorize** button or use `Authorization: Bearer <token>` in Postman.
4. Test the book endpoints.

Example book body:

```json
{
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "published_year": 2008
}
```

Example PATCH body:

```json
{
  "title": "Clean Code - Updated"
}
```
