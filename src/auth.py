import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import bcrypt
import logging
import src.db as db

logger = logging.getLogger(__name__)

def authenticate(username, password):
    """
    DB-backed credential check with bcrypt support.
    Handles BYTEA, str, and legacy plaintext password hashes.

    Returns:
        dict with user_id, username, role on success; None on failure.
    Raises:
        ConnectionError if the database is unreachable.
    """
    try:
        with db.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, username, role, password_hash
                    FROM users
                    WHERE username = %s
                    """,
                    (username,),
                )
                row = cur.fetchone()

        if not row:
            return None

        user_id, db_username, role, pw_hash = row

        if pw_hash is None:
            return None

        # Normalize pw_hash to bytes for bcrypt
        if isinstance(pw_hash, (bytes, bytearray, memoryview)):
            pw_hash_bytes = bytes(pw_hash)
        elif isinstance(pw_hash, str):
            if pw_hash.startswith("$2"):
                pw_hash_bytes = pw_hash.encode()
            else:
                # Legacy plaintext fallback
                if password == pw_hash:
                    logger.warning(
                        "User %s authenticated with legacy plaintext password. "
                        "Migrate to bcrypt.", db_username
                    )
                    return {"user_id": user_id, "username": db_username, "role": role}
                return None
        else:
            return None

        try:
            if bcrypt.checkpw(password.encode(), pw_hash_bytes):
                return {"user_id": user_id, "username": db_username, "role": role}
        except (ValueError, TypeError) as e:
            logger.exception("Password verification error for user %s: %s", db_username, e)
            return None

        return None
    except ConnectionError:
        # Bubble up so the UI can distinguish DB-down from bad credentials
        raise
    except Exception as e:
        logger.exception("Authentication failed: %s", e)
        return None
