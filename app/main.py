from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from mysql.connector import IntegrityError

from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
)
from .database import dictionary_cursor, get_db, initialize_database
from .schemas import (
    BookCreate,
    BookPatch,
    BookResponse,
    BookUpdate,
    Token,
    UserCreate,
    UserResponse,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Book Management REST API - Raw MySQL",
    version="2.0.0",
    description="FastAPI connected directly to MySQL using parameterized raw SQL.",
    lifespan=lifespan,
)


def fetch_book(connection, book_id: int) -> dict | None:
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            "SELECT id, title, author, published_year FROM books WHERE id = %s",
            (book_id,),
        )
        return cursor.fetchone()


def require_book(connection, book_id: int) -> dict:
    book = fetch_book(connection, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.get("/")
def root():
    return {"message": "Book Management API is running with MySQL"}


@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register_user(payload: UserCreate, connection=Depends(get_db)):
    try:
        with dictionary_cursor(connection) as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, hashed_password, role)
                VALUES (%s, %s, %s)
                """,
                (payload.username, hash_password(payload.password), payload.role),
            )
            user_id = cursor.lastrowid
        connection.commit()
    except IntegrityError as exc:
        connection.rollback()
        raise HTTPException(status_code=409, detail="Username already exists") from exc
    return {"id": user_id, "username": payload.username, "role": payload.role}


@app.post("/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection=Depends(get_db),
):
    user = authenticate_user(connection, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": create_access_token(
            subject=user["username"], role=user["role"]
        ),
        "token_type": "bearer",
    }


@app.get("/auth/me", response_model=UserResponse)
def read_my_profile(current_user: dict = Depends(get_current_user)):
    return current_user


@app.get("/books", response_model=list[BookResponse])
def get_books(
    author: str | None = Query(default=None, min_length=1),
    sort_by: Literal["published_year"] | None = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
    connection=Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    query = "SELECT id, title, author, published_year FROM books"
    parameters: list = []
    if author is not None:
        query += " WHERE author LIKE %s"
        parameters.append(f"%{author.strip()}%")

    if sort_by == "published_year":
        query += " ORDER BY published_year ASC" if order == "asc" else " ORDER BY published_year DESC"
    else:
        query += " ORDER BY id ASC"

    with dictionary_cursor(connection) as cursor:
        cursor.execute(query, tuple(parameters))
        return cursor.fetchall()


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int = Path(gt=0),
    connection=Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    return require_book(connection, book_id)


@app.post("/books", response_model=BookResponse, status_code=201)
def create_book(
    payload: BookCreate,
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            """
            INSERT INTO books (title, author, published_year)
            VALUES (%s, %s, %s)
            """,
            (payload.title, payload.author, payload.published_year),
        )
        book_id = cursor.lastrowid
    connection.commit()
    return require_book(connection, book_id)


@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(
    payload: BookUpdate,
    book_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_book(connection, book_id)
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            """
            UPDATE books
            SET title = %s, author = %s, published_year = %s
            WHERE id = %s
            """,
            (payload.title, payload.author, payload.published_year, book_id),
        )
    connection.commit()
    return require_book(connection, book_id)


@app.patch("/books/{book_id}", response_model=BookResponse)
def patch_book(
    payload: BookPatch,
    book_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_book(connection, book_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    allowed_columns = ("title", "author", "published_year")
    selected_columns = [column for column in allowed_columns if column in changes]
    set_clause = ", ".join(f"{column} = %s" for column in selected_columns)
    values = [changes[column] for column in selected_columns]
    values.append(book_id)

    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            f"UPDATE books SET {set_clause} WHERE id = %s",
            tuple(values),
        )
    connection.commit()
    return require_book(connection, book_id)


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_book(connection, book_id)
    with dictionary_cursor(connection) as cursor:
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
