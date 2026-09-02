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
    ReviewCreate,
    ReviewResponse,
    SchoolClassCreate,
    SchoolClassPatch,
    SchoolClassResponse,
    SchoolClassUpdate,
    SchoolCreate,
    SchoolPatch,
    SchoolResponse,
    SchoolUpdate,
    Token,
    UserCreate,
    UserResponse,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="School, Class, and Book Management API - Raw MySQL",
    version="3.0.0",
    description="FastAPI connected directly to MySQL using parameterized raw SQL for school, class, and book management.",
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


def fetch_review(connection, review_id: int) -> dict | None:
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT id, user_id, book_id, rating, comment, created_at
            FROM reviews
            WHERE id = %s
            """,
            (review_id,),
        )
        return cursor.fetchone()


def fetch_school(connection, school_id: int) -> dict | None:
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT id, name, address, principal_name
            FROM schools
            WHERE id = %s
            """,
            (school_id,),
        )
        return cursor.fetchone()


def require_school(connection, school_id: int) -> dict:
    school = fetch_school(connection, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return school


def fetch_class(connection, class_id: int) -> dict | None:
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT
                c.id,
                c.school_id,
                s.name AS school_name,
                c.grade_level,
                c.section,
                c.room_number,
                c.capacity
            FROM classes c
            JOIN schools s ON s.id = c.school_id
            WHERE c.id = %s
            """,
            (class_id,),
        )
        return cursor.fetchone()


def require_class(connection, class_id: int) -> dict:
    school_class = fetch_class(connection, class_id)
    if school_class is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return school_class


@app.get("/")
def root():
    return {"message": "School, class, and book management API is running with MySQL"}


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


@app.post(
    "/books/{book_id}/reviews/",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    payload: ReviewCreate,
    book_id: int = Path(gt=0),
    connection=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_book(connection, book_id)
    try:
        with dictionary_cursor(connection) as cursor:
            cursor.execute(
                """
                INSERT INTO reviews (user_id, book_id, rating, comment)
                VALUES (%s, %s, %s, %s)
                """,
                (current_user["id"], book_id, payload.rating, payload.comment),
            )
            review_id = cursor.lastrowid
        connection.commit()
    except IntegrityError as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this book",
        ) from exc

    return fetch_review(connection, review_id)


@app.get("/books/{book_id}/reviews/", response_model=list[ReviewResponse])
def get_book_reviews(
    book_id: int = Path(gt=0),
    connection=Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    require_book(connection, book_id)
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT id, user_id, book_id, rating, comment, created_at
            FROM reviews
            WHERE book_id = %s
            ORDER BY created_at DESC, id DESC
            """,
            (book_id,),
        )
        return cursor.fetchall()


@app.get("/schools", response_model=list[SchoolResponse])
def get_schools(
    connection=Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    with dictionary_cursor(connection) as cursor:
        cursor.execute(
            """
            SELECT id, name, address, principal_name
            FROM schools
            ORDER BY id ASC
            """
        )
        return cursor.fetchall()


@app.get("/schools/{school_id}", response_model=SchoolResponse)
def get_school(
    school_id: int = Path(gt=0),
    connection=Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    return require_school(connection, school_id)


@app.post("/schools", response_model=SchoolResponse, status_code=201)
def create_school(
    payload: SchoolCreate,
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    try:
        with dictionary_cursor(connection) as cursor:
            cursor.execute(
                """
                INSERT INTO schools (name, address, principal_name)
                VALUES (%s, %s, %s)
                """,
                (payload.name, payload.address, payload.principal_name),
            )
            school_id = cursor.lastrowid
        connection.commit()
    except IntegrityError as exc:
        connection.rollback()
        raise HTTPException(status_code=409, detail="School name already exists") from exc
    return require_school(connection, school_id)


@app.put("/schools/{school_id}", response_model=SchoolResponse)
def update_school(
    payload: SchoolUpdate,
    school_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_school(connection, school_id)
    try:
        with dictionary_cursor(connection) as cursor:
            cursor.execute(
                """
                UPDATE schools
                SET name = %s, address = %s, principal_name = %s
                WHERE id = %s
                """,
                (payload.name, payload.address, payload.principal_name, school_id),
            )
        connection.commit()
    except IntegrityError as exc:
        connection.rollback()
        raise HTTPException(status_code=409, detail="School name already exists") from exc
    return require_school(connection, school_id)


@app.patch("/schools/{school_id}", response_model=SchoolResponse)
def patch_school(
    payload: SchoolPatch,
    school_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_school(connection, school_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    allowed_columns = ("name", "address", "principal_name")
    selected_columns = [column for column in allowed_columns if column in changes]
    set_clause = ", ".join(f"{column} = %s" for column in selected_columns)
    values = [changes[column] for column in selected_columns]
    values.append(school_id)

    try:
        with dictionary_cursor(connection) as cursor:
            cursor.execute(
                f"UPDATE schools SET {set_clause} WHERE id = %s",
                tuple(values),
            )
        connection.commit()
    except IntegrityError as exc:
        connection.rollback()
        raise HTTPException(status_code=409, detail="School name already exists") from exc
    return require_school(connection, school_id)


@app.delete("/schools/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_school(connection, school_id)
    with dictionary_cursor(connection) as cursor:
        cursor.execute("DELETE FROM schools WHERE id = %s", (school_id,))
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/classes", response_model=list[SchoolClassResponse])
def get_classes(
    school_id: int | None = Query(default=None, gt=0),
    grade_level: str | None = Query(default=None, min_length=1),
    connection=Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    query = """
        SELECT
            c.id,
            c.school_id,
            s.name AS school_name,
            c.grade_level,
            c.section,
            c.room_number,
            c.capacity
        FROM classes c
        JOIN schools s ON s.id = c.school_id
    """
    parameters: list = []
    conditions: list[str] = []

    if school_id is not None:
        conditions.append("c.school_id = %s")
        parameters.append(school_id)
    if grade_level is not None:
        conditions.append("c.grade_level LIKE %s")
        parameters.append(f"%{grade_level.strip()}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY c.id ASC"

    with dictionary_cursor(connection) as cursor:
        cursor.execute(query, tuple(parameters))
        return cursor.fetchall()


@app.get("/classes/{class_id}", response_model=SchoolClassResponse)
def get_class(
    class_id: int = Path(gt=0),
    connection=Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    return require_class(connection, class_id)


@app.post("/classes", response_model=SchoolClassResponse, status_code=201)
def create_class(
    payload: SchoolClassCreate,
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_school(connection, payload.school_id)
    try:
        with dictionary_cursor(connection) as cursor:
            cursor.execute(
                """
                INSERT INTO classes (school_id, grade_level, section, room_number, capacity)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    payload.school_id,
                    payload.grade_level,
                    payload.section,
                    payload.room_number,
                    payload.capacity,
                ),
            )
            class_id = cursor.lastrowid
        connection.commit()
    except IntegrityError as exc:
        connection.rollback()
        raise HTTPException(
            status_code=409,
            detail="A class with the same school, grade level, and section already exists",
        ) from exc
    return require_class(connection, class_id)


@app.put("/classes/{class_id}", response_model=SchoolClassResponse)
def update_class(
    payload: SchoolClassUpdate,
    class_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_class(connection, class_id)
    require_school(connection, payload.school_id)
    try:
        with dictionary_cursor(connection) as cursor:
            cursor.execute(
                """
                UPDATE classes
                SET school_id = %s,
                    grade_level = %s,
                    section = %s,
                    room_number = %s,
                    capacity = %s
                WHERE id = %s
                """,
                (
                    payload.school_id,
                    payload.grade_level,
                    payload.section,
                    payload.room_number,
                    payload.capacity,
                    class_id,
                ),
            )
        connection.commit()
    except IntegrityError as exc:
        connection.rollback()
        raise HTTPException(
            status_code=409,
            detail="A class with the same school, grade level, and section already exists",
        ) from exc
    return require_class(connection, class_id)


@app.patch("/classes/{class_id}", response_model=SchoolClassResponse)
def patch_class(
    payload: SchoolClassPatch,
    class_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_class(connection, class_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    if "school_id" in changes:
        require_school(connection, changes["school_id"])

    allowed_columns = ("school_id", "grade_level", "section", "room_number", "capacity")
    selected_columns = [column for column in allowed_columns if column in changes]
    set_clause = ", ".join(f"{column} = %s" for column in selected_columns)
    values = [changes[column] for column in selected_columns]
    values.append(class_id)

    try:
        with dictionary_cursor(connection) as cursor:
            cursor.execute(
                f"UPDATE classes SET {set_clause} WHERE id = %s",
                tuple(values),
            )
        connection.commit()
    except IntegrityError as exc:
        connection.rollback()
        raise HTTPException(
            status_code=409,
            detail="A class with the same school, grade level, and section already exists",
        ) from exc
    return require_class(connection, class_id)


@app.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int = Path(gt=0),
    connection=Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    require_class(connection, class_id)
    with dictionary_cursor(connection) as cursor:
        cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
