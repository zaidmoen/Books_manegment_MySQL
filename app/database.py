import os
import re
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from fastapi import HTTPException, status
from mysql.connector import Error

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "books_management")
MIGRATIONS_DIRECTORY = Path(__file__).resolve().parent.parent / "migrations"

if not re.fullmatch(r"[A-Za-z0-9_]+", MYSQL_DATABASE):
    raise RuntimeError("MYSQL_DATABASE may contain only letters, numbers, and underscores")


def _connection_config(*, include_database: bool = True) -> dict:
    config = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "autocommit": False,
    }
    if include_database:
        config["database"] = MYSQL_DATABASE
    return config


def initialize_database() -> None:
    """Create the database and tables when the API starts."""
    server_connection = mysql.connector.connect(
        **_connection_config(include_database=False)
    )
    try:
        cursor = server_connection.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.close()
        server_connection.commit()
    finally:
        server_connection.close()

    connection = mysql.connector.connect(**_connection_config())
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(120) NOT NULL,
                published_year INT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_books_author (author),
                INDEX idx_books_published_year (published_year)
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schools (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL UNIQUE,
                address VARCHAR(255) NULL,
                principal_name VARCHAR(120) NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                school_id INT UNSIGNED NOT NULL,
                grade_level VARCHAR(50) NOT NULL,
                section VARCHAR(20) NOT NULL,
                room_number VARCHAR(20) NULL,
                capacity INT UNSIGNED NOT NULL DEFAULT 30,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_classes_school
                    FOREIGN KEY (school_id) REFERENCES schools(id)
                    ON DELETE CASCADE,
                UNIQUE KEY uq_classes_school_grade_section (school_id, grade_level, section),
                INDEX idx_classes_school_id (school_id),
                INDEX idx_classes_grade_level (grade_level)
            ) ENGINE=InnoDB
            """
        )
        _apply_migrations(connection, cursor)
        cursor.close()
        connection.commit()
    finally:
        connection.close()


def _apply_migrations(connection, cursor) -> None:
    """Apply each SQL migration exactly once in filename order."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """
    )
    connection.commit()

    if not MIGRATIONS_DIRECTORY.exists():
        return

    for migration_path in sorted(MIGRATIONS_DIRECTORY.glob("*.sql")):
        version = migration_path.name
        cursor.execute(
            "SELECT 1 FROM schema_migrations WHERE version = %s",
            (version,),
        )
        if cursor.fetchone() is not None:
            continue

        try:
            cursor.execute(migration_path.read_text(encoding="utf-8"))
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def get_db():
    """FastAPI dependency: one direct MySQL connection per request."""
    connection = None
    try:
        connection = mysql.connector.connect(**_connection_config())
        yield connection
    except Error as exc:
        if connection is not None:
            connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection or query failed",
        ) from exc
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


@contextmanager
def dictionary_cursor(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
    finally:
        cursor.close()
