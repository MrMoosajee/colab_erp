import streamlit as st
import psycopg2
from psycopg2 import pool
import pandas as pd
from datetime import datetime, time
import pytz
from contextlib import contextmanager

# ----------------------------------------------------------------------------
# 1. INFRASTRUCTURE: THREAD-SAFE CONNECTION POOLING
# ----------------------------------------------------------------------------

@st.cache_resource
def get_db_pool():
    """
    Creates a ThreadedConnectionPool.
    Cached once per process. Safe for concurrent Streamlit users.
    Configured for UTC to prevent Timezone Drift.
    """
    try:
        return psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20, # SRE NOTE: Fits within postgresql.conf limits (100)
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["dbname"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            options="-c timezone=UTC" # CRITICAL: Enforces v2.1 Timezone Standard
        )
    except Exception as e:
        # Fatal error if DB is unreachable
        raise ConnectionError(f"❌ Critical: DB Pool Creation Failed: {e}")

@contextmanager
def get_db_connection():
    """
    Context manager to checkout a connection from the pool.
    Guarantees 'putconn' is called even if code crashes.
    """
    pool_instance = get_db_pool()
    conn = None
    try:
        conn = pool_instance.getconn()
        yield conn
    finally:
        if conn:
            pool_instance.putconn(conn)

# ----------------------------------------------------------------------------
# 2. QUERY EXECUTION LAYER (Security & ACID)
# ----------------------------------------------------------------------------

def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    """
    Executes a SELECT query (Read-Only).
    Raises ConnectionError for connectivity issues, other exceptions for SQL errors.
    Returns empty DataFrame only if query succeeds but returns no rows.
    """
    try:
        with get_db_connection() as conn:
            # Pandas read_sql does not close the connection; we return it to pool in 'finally'
            return pd.read_sql(query, conn, params=params)
    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        # Connection/pool issues should bubble up
        raise ConnectionError(f"Database connection failed: {e}") from e
    except Exception as e:
        # SQL errors (table doesn't exist, syntax error, etc.) should be visible
        print(f"SQL Error: {e}")
        raise RuntimeError(f"Query failed: {e}") from e

def run_transaction(query: str, params: tuple = None, fetch_one: bool = False):
    """
    Executes INSERT/UPDATE/DELETE (Write).
    Manages explicit commit/rollback to ensure pool hygiene.

    If fetch_one is True, returns cursor.fetchone() (useful for INSERT ... RETURNING).
    """
    conn = None
    try:
        # We manually manage the context to ensure we can rollback inside the except blocks
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone() if fetch_one else None
            conn.commit()  # ACID Commit
            return result if fetch_one else True
    except psycopg2.errors.ExclusionViolation:
        if conn:
            conn.rollback()  # CRITICAL: Reset connection state
        raise ValueError("Double Booking Prevented by Database Constraint.")
    except psycopg2.errors.UndefinedColumn as e:
        if conn:
            conn.rollback()  # CRITICAL: Reset connection state
        # Provide helpful error message for missing columns (e.g., booking_reference)
        error_msg = str(e)
        if "booking_reference" in error_msg.lower():
            raise RuntimeError(
                "Schema Error: booking_reference column missing. "
                "Run: ALTER TABLE bookings ADD COLUMN booking_reference TEXT;"
            ) from e
        raise RuntimeError(f"Schema Error: {error_msg}") from e
    except Exception as e:
        if conn:
            conn.rollback()  # CRITICAL: Reset connection state
        print(f"Transaction Failed: {e}")
        raise

# ----------------------------------------------------------------------------
# 3. UTILITIES (Timezone & Normalization)
# ----------------------------------------------------------------------------

def normalize_dates(date_input, time_start, time_end):
    """
    Combines date and time inputs into UTC-aware datetime objects.
    1. Localizes input to user's timezone (Configured in secrets.toml).
    2. Converts to UTC for database storage.
    """
    # Dynamic Config Injection
    # Per runbook: timezone is configured under [postgres] and is UI-facing (input locale).
    local_tz_name = st.secrets.get("postgres", {}).get("timezone", "Africa/Johannesburg")

    dt_start_naive = datetime.combine(date_input, time_start)
    dt_end_naive = datetime.combine(date_input, time_end)

    try:
        local_tz = pytz.timezone(local_tz_name)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.UTC

    # Convert Local -> UTC for Storage
    dt_start_utc = local_tz.localize(dt_start_naive).astimezone(pytz.UTC)
    dt_end_utc = local_tz.localize(dt_end_naive).astimezone(pytz.UTC)

    return dt_start_utc, dt_end_utc

# ----------------------------------------------------------------------------
# 4. DOMAIN LOGIC (The "Sliding Doors" Implementation)
# ----------------------------------------------------------------------------

def get_rooms():
    """
    Fetches available rooms.
    Includes '0 as capacity' shim for legacy frontend compatibility.
    """
    sql = """
          SELECT
              id,
              name,
              0 as capacity
          FROM rooms
          ORDER BY name; \
          """
    return run_query(sql)

def get_calendar_bookings(days_lookback=30):
    """
    Fetches bookings for the calendar view.
    Uses Postgres Range operators (lower/upper) for v2.1 schema compatibility.
    NOTE: booking_reference column removed until schema is updated.
    """
    sql = """
          SELECT
              r.name as "Room",
              lower(b.booking_period) as "Start",
              upper(b.booking_period) as "End",
              b.status as "Status"
          FROM bookings b
                   JOIN rooms r ON b.room_id = r.id
          WHERE lower(b.booking_period) >= NOW() - (%s * INTERVAL '1 day')
          ORDER BY lower(b.booking_period) DESC; \
          """
    return run_query(sql, (days_lookback,))

def get_dashboard_stats(tenant_filter=None):
    """
    Calculates KPIs for the Admin Dashboard.
    Supports optional filtering by Tenant (v2.2 Multi-Tenancy).
    
    Args:
        tenant_filter: Optional tenant_type value ('TECH' or 'TRAINING') to filter results
    """
    params = ()
    sql = """
          SELECT
              COUNT(*) as total_bookings,
              COUNT(*) FILTER (WHERE status = 'Approved') as approved,
              COUNT(*) FILTER (WHERE lower(booking_period) > NOW()) as upcoming
          FROM bookings
          """
    
    if tenant_filter:
        sql += " WHERE tenant_id = %s"
        params = (tenant_filter,)

    sql += ";"
    return run_query(sql, params)

def create_booking(room_id, start_dt, end_dt, purpose, user_ref="SYSTEM", tenant="TECH"):
    """
    Core Transaction Logic (v2.2 Multi-Tenancy Updated).
    1. Checks Constraints (via SQL Exception).
    2. Inserts Booking via strict ACID transaction.
    3. Adds tenant attribution to the ACID transaction.
    
    Args:
        room_id: Room identifier
        start_dt: Start datetime (UTC)
        end_dt: End datetime (UTC)
        purpose: Booking purpose/reference text
        user_ref: User reference (legacy parameter, currently unused)
        tenant: Tenant identifier ('TECH' or 'TRAINING'), defaults to 'TECH'
    
    NOTE: If booking_reference column doesn't exist, this will raise a SQL error.
    To add the column: ALTER TABLE bookings ADD COLUMN booking_reference TEXT;
    
    NOTE: Exclusion constraints remain GLOBAL. If 'TECH' books Room A at 10:00,
    'TRAINING' cannot book Room A at 10:00 (shared physical assets).
    """
    # Validate Tenant against Enum (Hardcoded safety)
    valid_tenants = {'TECH', 'TRAINING'}
    if tenant not in valid_tenants:
        raise ValueError(f"Invalid Tenant: {tenant}. Must be one of {valid_tenants}")
    
    sql = """
          INSERT INTO bookings (room_id, booking_period, status, booking_reference, tenant_id)
          VALUES (%s, tstzrange(%s, %s, '[)'), 'Pending', %s, %s)
          RETURNING id; \
          """
    return run_transaction(sql, (room_id, start_dt, end_dt, purpose, tenant), fetch_one=True)


 