# Colab ERP Database Interface

Complete documentation for database operations layer (db.py).

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Connection Management](#connection-management)
3. [Query Execution](#query-execution)
4. [Transaction Management](#transaction-management)
5. [Domain Operations](#domain-operations)
6. [Utilities](#utilities)
7. [Error Handling](#error-handling)
8. [Security Considerations](#security-considerations)

---

## Architecture Overview

The database interface follows a layered architecture:

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│    (Services, UI Components, etc.)      │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│       Database Interface (db.py)        │
│  ┌──────────────┐    ┌───────────────┐  │
│  │ Query Layer  │    │  Connection   │  │
│  │ (run_query)  │    │    Pooling    │  │
│  └──────────────┘    └───────────────┘  │
│  ┌──────────────┐    ┌───────────────┐  │
│  │ Transaction  │    │   Domain      │  │
│  │   Layer      │    │   Logic       │  │
│  └──────────────┘    └───────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      PostgreSQL (psycopg2 driver)       │
│         └── Type Converter             │
└─────────────────────────────────────────┘
```

---

## Connection Management

### Thread-Safe Connection Pooling

#### `get_db_pool()`

Creates a ThreadedConnectionPool with caching for concurrent Streamlit users.

**Cached via:** `@st.cache_resource`

**Configuration:**
```python
ThreadedConnectionPool(
    minconn=1,           # Minimum connections
    maxconn=20,          # Maximum connections (fits within postgresql.conf: 100)
    host=st.secrets["postgres"]["host"],
    port=st.secrets["postgres"]["port"],
    database=st.secrets["postgres"]["dbname"],
    user=st.secrets["postgres"]["user"],
    password=st.secrets["postgres"]["password"],
    options="-c timezone=UTC"  # CRITICAL: UTC enforcement
)
```

**Critical Note:** The `options="-c timezone=UTC"` parameter enforces UTC storage to prevent timezone drift (v2.1 Timezone Standard).

**SRE Note:** maxconn=20 fits within typical PostgreSQL limits (100 connections).

---

#### `get_db_connection()`

Context manager for safe connection checkout/return.

**Guarantees:**
- Connection is always returned to pool (even on crashes)
- Exception-safe with `try/finally` pattern

**Implementation:**
```python
@contextmanager
def get_db_connection():
    pool_instance = get_db_pool()
    conn = None
    try:
        conn = pool_instance.getconn()
        yield conn
    finally:
        if conn:
            pool_instance.putconn(conn)
```

**Usage Pattern:**
```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM rooms")
        results = cur.fetchall()
```

**Never use without context manager - risk of pool exhaustion.**

---

## Query Execution

### Read Operations (SELECT)

#### `run_query(query: str, params: tuple = None) -> pd.DataFrame`

Executes SELECT queries with automatic numpy type conversion.

**Pre-processing:**
1. Converts numpy types to native Python types via `convert_params_to_native()`
2. Prevents psycopg2 "can't adapt type 'numpy.int64'" errors

**Post-processing:**
- Returns pandas DataFrame via `pd.read_sql()`

**Error Handling:**
| Exception | Cause | Action |
|-----------|-------|--------|
| `ConnectionError` | Operational/Interface error | Bubble up (connectivity issue) |
| `RuntimeError` | SQL syntax, table missing | Visible to user |

**Empty Results:**
- Returns empty DataFrame (not None) when query succeeds but returns no rows

**Example - Basic Query:**
```python
df = run_query("SELECT * FROM rooms WHERE is_active = true")
```

**Example - Parameterized Query:**
```python
df = run_query(
    """
    SELECT 
        r.name as room_name,
        COUNT(b.id) as booking_count
    FROM rooms r
    LEFT JOIN bookings b ON r.id = b.room_id
    WHERE r.id = %s
    GROUP BY r.id, r.name
    """,
    (room_id,)
)
```

**Example - Date Range Query:**
```python
df = run_query(
    """
    SELECT * FROM bookings
    WHERE booking_period && tstzrange(%s, %s, '[)')
    AND status = 'Confirmed'
    """,
    (start_datetime, end_datetime)
)
```

---

### Write Operations (INSERT/UPDATE/DELETE)

#### `run_transaction(query: str, params: tuple = None, fetch_one: bool = False)`

Executes write operations with explicit ACID management.

**ACID Guarantees:**
- **Atomicity:** All or nothing via explicit commit/rollback
- **Consistency:** Connection state reset on errors
- **Isolation:** Uses database isolation level (default: READ COMMITTED)
- **Durability:** fsync on commit (PostgreSQL default)

**Pre-processing:**
1. Numpy type conversion via `convert_params_to_native()`
2. Parameter validation

**Connection State Management:**
```python
conn = None
try:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, clean_params)
            result = cur.fetchone() if fetch_one else None
        conn.commit()  # ACID Commit
        return result if fetch_one else True
except SpecificError as e:
    if conn:
        conn.rollback()  # CRITICAL: Reset connection state
    raise
```

**Specific Error Handlers:**

| Error Type | PostgreSQL Exception | Handling |
|------------|---------------------|----------|
| Double Booking | `ExclusionViolation` | Raise `ValueError` with clear message |
| Missing Column | `UndefinedColumn` | Raise `RuntimeError` with ALTER TABLE hint |
| Type Adaptation | `ProgrammingError` | Raise `RuntimeError` with debugging info |
| General Error | Any other | Rollback, log, re-raise |

**Returns:**
- `fetch_one=True`: Returns tuple from `RETURNING` clause
- `fetch_one=False`: Returns `True` on success

**Example - Simple Insert:**
```python
run_transaction(
    "UPDATE bookings SET status = %s WHERE id = %s",
    ('Confirmed', booking_id)
)
```

**Example - Insert with RETURNING:**
```python
result = run_transaction(
    """
    INSERT INTO bookings (room_id, booking_period, status, client_name)
    VALUES (%s, tstzrange(%s, %s, '[)'), %s, %s)
    RETURNING id
    """,
    (room_id, start_dt, end_dt, 'Pending', client_name),
    fetch_one=True
)
booking_id = result[0]
```

**Example - Handling Double Booking:**
```python
try:
    result = run_transaction(
        "INSERT INTO bookings (room_id, booking_period, status) VALUES (%s, %s, %s)",
        (room_id, booking_period, 'Confirmed')
    )
except ValueError as e:
    if "Double Booking" in str(e):
        print("Room already booked for this time slot")
```

---

## Transaction Management

### Rollback Scenarios

The following triggers automatic rollback:

1. **ExclusionViolation** - Booking constraint violation
2. **UndefinedColumn** - Schema mismatch (e.g., missing `booking_reference`)
3. **ProgrammingError** - Type adaptation failure
4. **Any Exception** - Generic rollback for unknown errors

**Rollback Pattern:**
```python
try:
    # ... transaction code ...
    conn.commit()
except Exception as e:
    if conn:
        conn.rollback()  # CRITICAL: Always reset connection state
    raise
```

**Why Rollback is Critical:**
- Without rollback, failed transactions leave connections in error state
- Subsequent queries on same connection would fail
- Pool returns corrupted connections to other users

---

### Batch Operations

For multiple related operations, use explicit connection management:

```python
with get_db_connection() as conn:
    try:
        with conn.cursor() as cur:
            # Operation 1
            cur.execute("INSERT INTO bookings ... RETURNING id", params1)
            booking_id = cur.fetchone()[0]
            
            # Operation 2 (depends on 1)
            cur.execute(
                "INSERT INTO booking_device_assignments (booking_id, ...) VALUES (%s, ...)",
                (booking_id, ...)
            )
            
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

---

## Domain Operations

### Room Operations

#### `get_rooms() -> pd.DataFrame`

**Purpose:** Fetch available rooms with legacy compatibility shim

**Query:**
```sql
SELECT
    id,
    name,
    0 as capacity  -- Shim for legacy frontend
FROM rooms
ORDER BY name
```

**Returns:** `id`, `name`, `capacity` (always 0 for legacy compatibility)

---

### Booking Calendar Operations

#### `get_calendar_bookings(days_lookback=30) -> pd.DataFrame`

**Purpose:** Fetch bookings for calendar view

**Query Features:**
- Uses Postgres Range operators (`lower`, `upper`)
- v2.1 schema compatibility
- Time-based filtering with `NOW() - INTERVAL`

**Query:**
```sql
SELECT
    r.name as "Room",
    lower(b.booking_period) as "Start",
    upper(b.booking_period) as "End",
    b.status as "Status"
FROM bookings b
JOIN rooms r ON b.room_id = r.id
WHERE lower(b.booking_period) >= NOW() - (%s * INTERVAL '1 day')
ORDER BY lower(b.booking_period) DESC
```

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `days_lookback` | `int` | Days to look back | 30 |

**Returns:** `Room`, `Start`, `End`, `Status`

---

#### `get_calendar_grid(start_date, end_date) -> pd.DataFrame`

**Purpose:** Fetch expanded bookings for Excel-style calendar grid

**Query Features:**
- Generates date series with `generate_series`
- Cross join with rooms for complete grid
- Left join bookings to show empty cells
- Aggregates device counts

**Query:**
```sql
WITH date_range AS (
    SELECT generate_series(%s::date, %s::date, '1 day'::interval)::date AS booking_date
),
expanded_bookings AS (
    SELECT 
        r.id as room_id,
        r.name as room_name,
        dr.booking_date,
        b.id as booking_id,
        b.client_name,
        b.num_learners,
        b.num_facilitators,
        b.headcount,
        b.coffee_tea_station,
        b.morning_catering,
        b.lunch_catering,
        b.stationery_needed,
        b.devices_needed,
        b.status,
        b.tenant_id,
        COUNT(bda.device_id) as device_count
    FROM date_range dr
    CROSS JOIN rooms r
    LEFT JOIN bookings b ON ...
    LEFT JOIN booking_device_assignments bda ON ...
    WHERE r.is_active = true
    GROUP BY ...
)
SELECT * FROM expanded_bookings
ORDER BY room_name, booking_date
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `start_date` | `date` | Start of range |
| `end_date` | `date` | End of range |

**Returns:** Full booking details per room per day

---

#### `get_rooms_for_calendar() -> pd.DataFrame`

**Purpose:** Fetch rooms in custom display order

**Query Features:**
- CASE-based custom ordering (Excellence=1, Inspiration=2, etc.)
- Returns 23+ named rooms in specific sequence

**Query:**
```sql
SELECT id, name, max_capacity
FROM rooms
WHERE is_active = true
ORDER BY 
    CASE 
        WHEN name = 'Excellence' THEN 1
        WHEN name = 'Inspiration' THEN 2
        -- ... 20+ more rooms ...
        ELSE 25
    END
```

**Returns:** Rooms in fixed presentation order

---

### Dashboard Operations

#### `get_dashboard_stats(tenant_filter=None) -> pd.DataFrame`

**Purpose:** Calculate KPIs for Admin Dashboard

**Query Features:**
- Multi-tenancy support (v2.2)
- Filtered aggregates with `FILTER` clause
- Optional tenant filtering

**Query:**
```sql
SELECT
    COUNT(*) as total_bookings,
    COUNT(*) FILTER (WHERE status = 'Approved') as approved,
    COUNT(*) FILTER (WHERE lower(booking_period) > NOW()) as upcoming
FROM bookings
-- Optional: WHERE tenant_id = %s
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `tenant_filter` | `str` | 'TECH' or 'TRAINING' (optional) |

**Returns:** `total_bookings`, `approved`, `upcoming`

---

### Core Transaction Logic

#### `create_booking(room_id, start_dt, end_dt, purpose, user_ref="SYSTEM", tenant="TECH")`

**Purpose:** Core booking creation with ACID guarantees

**Validation:**
1. Tenant against valid set: `{'TECH', 'TRAINING'}`
2. Raises `ValueError` for invalid tenant

**Query:**
```sql
INSERT INTO bookings (
    room_id, 
    booking_period, 
    status, 
    booking_reference, 
    tenant_id
) VALUES (
    %s, 
    tstzrange(%s, %s, '[)'),  -- '[)' = inclusive start, exclusive end
    'Pending', 
    %s, 
    %s
)
RETURNING id
```

**Notes:**
- Uses `tstzrange` for timezone-aware period storage
- `'[)'` notation = inclusive lower bound, exclusive upper bound
- Exclusion constraints prevent double bookings at database level

**Returns:** `(booking_id,)` tuple from `RETURNING`

**Example:**
```python
result = create_booking(
    room_id=1,
    start_dt=start_utc,
    end_dt=end_utc,
    purpose="Training",
    tenant="TECH"
)
booking_id = result[0]  # Extract from tuple
```

---

## Utilities

### Date/Time Normalization

#### `normalize_dates(date_input, time_start, time_end)`

**Purpose:** Convert local datetime inputs to UTC for storage

**Algorithm:**
1. Combine date + time into naive datetime
2. Localize to configured timezone (from secrets.toml)
3. Convert to UTC
4. Return UTC-aware datetimes

**Configuration:**
```python
local_tz_name = st.secrets.get("postgres", {}).get("timezone", "Africa/Johannesburg")
```

**Default:** "Africa/Johannesburg" (fallback)

**Implementation:**
```python
def normalize_dates(date_input, time_start, time_end):
    dt_start_naive = datetime.combine(date_input, time_start)
    dt_end_naive = datetime.combine(date_input, time_end)
    
    local_tz = pytz.timezone(local_tz_name)
    
    # Convert Local -> UTC for Storage
    dt_start_utc = local_tz.localize(dt_start_naive).astimezone(pytz.UTC)
    dt_end_utc = local_tz.localize(dt_end_naive).astimezone(pytz.UTC)
    
    return dt_start_utc, dt_end_utc
```

**Example:**
```python
from datetime import date, time
import pytz

start_utc, end_utc = normalize_dates(
    date(2024, 1, 15),
    time(9, 0),   # 9:00 AM Johannesburg
    time(17, 0)   # 5:00 PM Johannesburg
)
# Returns: (2024-01-15 07:00:00+00:00, 2024-01-15 15:00:00+00:00)
# (Johannesburg is UTC+2, so 9 AM -> 7 AM UTC)
```

**Critical for:**
- Preventing timezone drift
- Consistent UTC storage
- Proper conflict detection across timezones

---

### Parameter Validation

#### `validate_params(params) -> Tuple[bool, str]`

**Purpose:** Debug helper for type conversion issues

**Returns:** `(is_valid, error_message)`

**Example:**
```python
is_valid, error = validate_params((np.int64(42), 'string'))
if not is_valid:
    print(f"Type issue: {error}")
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── ConnectionError (db.py raises for connectivity)
├── RuntimeError (db.py raises for SQL errors)
└── ValueError (db.py raises for constraint violations)
```

### ConnectionError

**Raised when:**
- `psycopg2.OperationalError` - Server down, network unreachable
- `psycopg2.InterfaceError` - Pool exhausted, connection lost

**Handling Pattern:**
```python
try:
    df = run_query("SELECT * FROM rooms")
except ConnectionError as e:
    st.error(f"🚨 Database unreachable: {e}")
    st.info("Fix: verify Tailscale VPN is up")
```

---

### RuntimeError

**Raised when:**
- SQL syntax errors
- Missing tables/columns
- Type adaptation failures

**Specific Cases:**

**Missing booking_reference column:**
```python
RuntimeError(
    "Schema Error: booking_reference column missing. "
    "Run: ALTER TABLE bookings ADD COLUMN booking_reference TEXT;"
)
```

**Type adaptation error:**
```python
RuntimeError(
    f"Type Error: {error_msg}. "
    "This may indicate a numpy type was not properly converted. "
    "Please report this error with the data types involved."
)
```

---

### ValueError

**Raised when:**
- Exclusion constraint violation (double booking)
- Invalid tenant ID

**Double Booking Message:**
```python
ValueError("Double Booking Prevented by Database Constraint.")
```

**Invalid Tenant:**
```python
valid_tenants = {'TECH', 'TRAINING'}
if tenant not in valid_tenants:
    raise ValueError(f"Invalid Tenant: {tenant}. Must be one of {valid_tenants}")
```

---

## Security Considerations

### SQL Injection Prevention

**All queries use parameterized statements:**

✅ **Safe:**
```python
db.run_query("SELECT * FROM users WHERE id = %s", (user_id,))
```

❌ **Never do this:**
```python
db.run_query(f"SELECT * FROM users WHERE id = {user_id}")  # VULNERABLE!
```

### Secrets Management

**All credentials from Streamlit secrets:**
```python
host=st.secrets["postgres"]["host"]
password=st.secrets["postgres"]["password"]
```

**Never hardcode credentials in source code.**

---

### Connection Pool Limits

**Configuration:**
- Min: 1 connection
- Max: 20 connections

**Why 20?**
- PostgreSQL default: 100 max connections
- Leaves room for other applications
- Prevents pool exhaustion attacks

**Monitoring:**
```python
# Check active connections
pool = get_db_pool()
# Monitor via PostgreSQL: 
# SELECT count(*) FROM pg_stat_activity;
```

---

### UTC Enforcement

**Critical security feature:**
```python
options="-c timezone=UTC"
```

**Prevents:**
- Timezone confusion attacks
- Scheduling conflicts from DST transitions
- Data inconsistency

---

## Performance Considerations

### Query Optimization

**Efficient patterns used:**

1. **Range operators** (`&&`, `@>`, `<@`) for period overlap detection
2. **FILTER clause** for conditional aggregation
3. **CTE (WITH clauses)** for complex grid generation
4. **Proper indexing** assumed on:
   - `bookings.room_id`
   - `bookings.booking_period` (GiST index for range)
   - `bookings.status`
   - `rooms.is_active`

### Connection Reuse

**Cached pool ensures:**
- Connection reuse across requests
- No connection per-query overhead
- Thread-safe concurrent access

### DataFrame Returns

**Why pandas DataFrames?**
- Optimized for tabular data
- Rich API for filtering/transforming
- Native Streamlit integration (`st.dataframe`)

---

## Migration Guide

### Adding New Queries

**Template for SELECT queries:**
```python
def get_new_data(filter_param):
    """
    Description of what this query does.
    
    Args:
        filter_param: Description
    
    Returns:
        DataFrame with columns: ...
    """
    query = """
        SELECT 
            column1,
            column2
        FROM table
        WHERE condition = %s
        ORDER BY column1
    """
    return run_query(query, (filter_param,))
```

**Template for INSERT/UPDATE:**
```python
def create_new_record(data):
    """
    Description of operation.
    
    Args:
        data: Description
    
    Returns:
        Dict with success status
    """
    try:
        result = run_transaction(
            "INSERT INTO table (col1, col2) VALUES (%s, %s) RETURNING id",
            (data['col1'], data['col2']),
            fetch_one=True
        )
        return {'success': True, 'id': result[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

---

## Testing

### Connection Test
```python
def test_connection():
    try:
        df = run_query("SELECT 1 as test")
        return df.iloc[0]['test'] == 1
    except Exception:
        return False
```

### Transaction Test
```python
def test_transaction_rollback():
    try:
        # This should fail (invalid table)
        run_transaction("INSERT INTO nonexistent_table VALUES (1)")
    except RuntimeError:
        return True  # Expected
    return False
```

---

## See Also

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Service Guide](SERVICE_GUIDE.md) - Business logic services
- [UI Components](UI_COMPONENTS.md) - Frontend documentation
