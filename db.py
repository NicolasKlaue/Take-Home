from dotenv import load_dotenv
import os

load_dotenv()
import sqlite3
from sqlite3 import Error


def get_connection():
    """
    Create and return a database connection.
    Reads DB path from environment variable DB_PATH.
    """
    db_path = os.getenv("DB_PATH")

    if not db_path:
        raise ValueError("Environment variable DB_PATH is not set")

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enables dict-like access
        return conn
    except Error as e:
        raise ConnectionError(f"Failed to connect to database: {e}")


def get_user_by_username(username):
    """
    Fetch a user by username.
    Returns: dict or None
    """
    query = "SELECT * FROM users WHERE username = ?"

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    except Error as e:
        raise RuntimeError(f"Database error in get_user_by_username: {e}")


def fetch_data():
    """
    Fetch all records from a generic 'data' table.
    Returns: list of dicts
    """
    query = "SELECT * FROM users"

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Error as e:
        raise RuntimeError(f"Database error in get_all_data: {e}")


def create_user(username, password_hash):
    """
    Create a new user.
    Returns: True if successful
    """
    query = "INSERT INTO users (username, password_hash) VALUES (?, ?)"

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (username, password_hash))
        conn.commit()
        conn.close()

        return True

    except sqlite3.IntegrityError:
        # Likely duplicate username (UNIQUE constraint)
        return False

    except Error as e:
        raise RuntimeError(f"Database error in create_user: {e}")