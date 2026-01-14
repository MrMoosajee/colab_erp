import psycopg2
import streamlit as st
from datetime import datetime, time

# -----------------------------
# Database Connection
# -----------------------------
def get_connection():
    try:
        # Connects using the [postgres] section in your secrets.toml
        return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            dbname=st.secrets["postgres"]["dbname"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"]
        )
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# -----------------------------
# Date Utilities
# -----------------------------
def normalize_dates(date_start, date_end):
    """Converts Date objects to Datetime (Start of day / End of day)"""
    start_dt = datetime.combine(date_start, time.min)
    end_dt = datetime.combine(date_end, time.max)
    return start_dt, end_dt

# -----------------------------
# Sliding Door Logic
# -----------------------------
def get_related_rooms(conn, room_id):
    """Finds Room A + Room B if Combined Room is selected, and vice versa."""
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT parent_room_id, child_room_id
            FROM room_dependencies
            WHERE parent_room_id = %s OR child_room_id = %s
        """, (room_id, room_id))

        related = {room_id}
        for parent, child in cur.fetchall():
            related.add(parent)
            related.add(child)

        return list(related)
    except Exception:
        return [room_id]

def check_room_availability(room_id, date_start, date_end):
    conn = get_connection()
    if not conn: return False

    try:
        start_dt, end_dt = normalize_dates(date_start, date_end)
        rooms = get_related_rooms(conn, room_id)

        cur = conn.cursor()
        # Checks if ANY related room is booked
        cur.execute("""
            SELECT COUNT(*)
            FROM bookings
            WHERE room_id = ANY(%s)
              AND status IN ('Pending', 'Approved')
              AND NOT (end_time < %s OR start_time > %s)
        """, (list(rooms), start_dt, end_dt))

        conflicts = cur.fetchone()[0]
        return conflicts == 0

    except Exception as e:
        st.error(f"Room check failed: {e}")
        return False
    finally:
        conn.close()

# -----------------------------
# Ghost Inventory Logic
# -----------------------------
def check_asset_availability(item_id, quantity, date_start, date_end):
    conn = get_connection()
    if not conn: return False, quantity

    try:
        start_dt, end_dt = normalize_dates(date_start, date_end)
        cur = conn.cursor()

        # Get Total Stock
        cur.execute("SELECT total_stock FROM catalog_items WHERE item_id = %s", (item_id,))
        row = cur.fetchone()
        if not row:
             return False, quantity # Item doesn't exist
        total_stock = row[0]

        # Calculate Used Stock
        cur.execute("""
            SELECT COALESCE(SUM(bl.quantity), 0)
            FROM booking_lines bl
            JOIN bookings b ON bl.booking_id = b.booking_id
            WHERE bl.item_id = %s
              AND b.status IN ('Pending', 'Approved')
              AND NOT (b.end_time < %s OR b.start_time > %s)
        """, (item_id, start_dt, end_dt))

        used = cur.fetchone()[0]
        remaining = total_stock - used

        if remaining < quantity:
            return False, quantity - remaining

        return True, 0

    except Exception as e:
        st.error(f"Inventory check failed: {e}")
        return False, quantity
    finally:
        conn.close()
