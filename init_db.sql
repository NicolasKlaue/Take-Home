-- Enable foreign keys (good practice even if not used yet)
PRAGMA foreign_keys = ON;

-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

-- =========================
-- SAMPLE DATA TABLE
-- =========================
CREATE TABLE IF NOT EXISTS sample_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    value REAL
);

-- =========================
-- INSERT DEFAULT USER
-- Password: "admin123"
-- Hashed using bcrypt
-- =========================
INSERT INTO users (username, password_hash)
VALUES (
    'admin',
    '$2a$12$mzAra9hv/sQEuOzHBd9Fh.qNPdDWuE7oHeOffoVvjI5avJ.qKRS/O'
)
ON CONFLICT(username) DO NOTHING;

-- =========================
-- INSERT SAMPLE DATA
-- =========================
INSERT INTO sample_data (name, value) VALUES
    ('Temperature', 23.5),
    ('Pressure', 1.02),
    ('Humidity', 45.0),
    ('Speed', 88.8)
ON CONFLICT DO NOTHING;