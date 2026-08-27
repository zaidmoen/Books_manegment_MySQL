import os
import re
from contextlib import contextmanager

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
        cursor.close()
        connection.commit()
    finally:
        connection.close()


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
