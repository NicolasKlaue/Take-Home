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
-- LOADS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS loads (
    load_id TEXT PRIMARY KEY,

    origin TEXT NOT NULL,
    destination TEXT NOT NULL,

    pickup_datetime TEXT,
    delivery_datetime TEXT,

    equipment_type TEXT,
    loadboard_rate REAL,

    notes TEXT,

    weight REAL,
    commodity_type TEXT,

    num_of_pieces INTEGER,
    miles REAL,
    dimensions TEXT
);