import bcrypt
from typing import Dict, Any, Optional

# Assumes db.py exposes a function: get_user_by_username(username: str)
# which returns a dict like:
# {
#     "id": int,
#     "username": str,
#     "password_hash": str
# }
from db import get_user_by_username


# -----------------------------
# Password Hashing
# -----------------------------
def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password (str): Plaintext password

    Returns:
        str: Hashed password (utf-8 decoded)
    """
    if not password:
        raise ValueError("Password cannot be empty")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# -----------------------------
# Password Verification
# -----------------------------
def authenticate_user(password: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    Args:
        password (str): Plaintext password
        hashed (str): Stored hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    if not password or not hashed:
        return False

    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
    except Exception:
        return False


# -----------------------------
# Login Logic
# -----------------------------
def login_user(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user against the database.

    Args:
        username (str): Username
        password (str): Plaintext password

    Returns:
        Dict[str, Any]: {
            "success": bool,
            "message": str,
            "user": Optional[dict]
        }
    """
    if not username or not password:
        return {
            "success": False,
            "message": "Username and password are required",
            "user": None
        }

    try:
        user = get_user_by_username(username)

        if not user:
            return {
                "success": False,
                "message": "User not found",
                "user": None
            }

        stored_hash = user.get("password_hash")

        if not stored_hash:
            return {
                "success": False,
                "message": "Invalid user credentials",
                "user": None
            }

        if not authenticate_user(password, stored_hash):
            return {
                "success": False,
                "message": "Incorrect password",
                "user": None
            }

        # Remove sensitive data before returning user object
        safe_user = {
            key: value for key, value in user.items()
            if key != "password_hash"
        }

        return {
            "success": True,
            "message": "Login successful",
            "user": safe_user
        }

    except Exception as e:
        # Avoid leaking internal errors in production
        return {
            "success": False,
            "message": "Authentication failed",
            "user": None
        }