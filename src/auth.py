import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import bcrypt
import streamlit as st
import src.db as db

def authenticate(username, password):
    try:
        with db.get_db_connection() as conn:
            with conn.cursor() as cur:
        # Fetch the hash stored in the DB
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

        user_id, username, role, pw_hash = row

        # VERIFY: Check if the plain password matches the Hash
        try:
                    if pw_hash is None:
                        return None
                    if bcrypt.checkpw(password.encode(), str(pw_hash).encode()):
                return {"user_id": user_id, "username": username, "role": role}
        except ValueError:
                    # FAILSAFE: If a legacy plain password is stored (manual insert), this catches it.
            if password == pw_hash:
                 return {"user_id": user_id, "username": username, "role": role}

        return None
    except ConnectionError:
        # Bubble up pool/DB connectivity failures so the UI can distinguish them
        raise
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None
