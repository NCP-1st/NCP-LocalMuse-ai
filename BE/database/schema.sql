-- LocalMuse AI schema (SQLite / MySQL 호환에 가깝게 작성)
-- PRD: User, Location, Course, CourseLocation (+ History)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname VARCHAR(100) NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500) NOT NULL DEFAULT '',
    latitude DOUBLE NOT NULL DEFAULT 0,
    longitude DOUBLE NOT NULL DEFAULT 0,
    category VARCHAR(100) NOT NULL DEFAULT '',
    content_id VARCHAR(64),
    UNIQUE(name, address)
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title VARCHAR(255) NOT NULL,
    story TEXT,
    source VARCHAR(50),
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS course_locations (
    course_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    duration VARCHAR(50),
    travel_time VARCHAR(50),
    reason TEXT,
    PRIMARY KEY (course_id, sequence),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    query_json TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
