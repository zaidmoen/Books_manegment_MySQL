CREATE DATABASE IF NOT EXISTS books_management
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE books_management;

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS books (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(120) NOT NULL,
    published_year INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_books_author (author),
    INDEX idx_books_published_year (published_year)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS schools (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    address VARCHAR(255) NULL,
    principal_name VARCHAR(120) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

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
) ENGINE=InnoDB;
