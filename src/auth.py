import bcrypt
import streamlit as st
from db import get_connection

def authenticate(username, password):
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        # Fetch the hash stored in the DB
        cur.execute("""
            SELECT user_id, username, role, password_hash
            FROM users
            WHERE username = %s
        """, (username,))

        row = cur.fetchone()
        if not row:
            return None

        user_id, username, role, pw_hash = row

        # VERIFY: Check if the plain password matches the Hash
        try:
            # Check encrypted password
            if bcrypt.checkpw(password.encode(), pw_hash.encode()):
                return {"user_id": user_id, "username": username, "role": role}
        except ValueError:
            # FAILSAFE: If 'admin123' is stored as plain text (from our manual insert), this catches it.
            if password == pw_hash:
                 return {"user_id": user_id, "username": username, "role": role}

        return None

    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None
    finally:
        if conn: conn.close()
