# Colab ERP API Reference

Complete API documentation for the Colab ERP system.

## Table of Contents

1. [Database Interface (db.py)](#database-interface-dbpy)
2. [Authentication (auth.py)](#authentication-authpy)
3. [Type Converter (numpy_type_converter.py)](#type-converter-numpy_type_converterpy)
4. [Configuration](#configuration)

---

## Database Interface (db.py)

### Connection Pooling

#### `get_db_pool()`
Creates a ThreadedConnectionPool cached via `@st.cache_resource`.

**Returns:** `psycopg2.pool.ThreadedConnectionPool`

**Configuration:**
- Min connections: 1
- Max connections: 20
- Timezone: UTC (enforced via `options="-c timezone=UTC"`)

**Example:**
```python
pool = get_db_pool()
# Used internally by get_db_connection()
```

---

#### `get_db_connection()`
Context manager for checkout/return of connections from the pool.

**Yields:** `psycopg2.extensions.connection`

**Example:**
```python
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM rooms")
```

---

### Query Operations

#### `run_query(query: str, params: tuple = None) -> pd.DataFrame`
Executes SELECT queries with automatic numpy type conversion.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `query` | `str` | SQL SELECT statement | Required |
| `params` | `tuple` | Query parameters | `None` |

**Returns:** `pd.DataFrame` - Query results

**Raises:**
- `ConnectionError` - Database connectivity issues
- `RuntimeError` - SQL execution errors

**Example:**
```python
# Basic query
df = run_query("SELECT * FROM rooms WHERE is_active = true")

# Parameterized query
df = run_query(
    "SELECT * FROM bookings WHERE room_id = %s AND status = %s",
    (room_id, 'Confirmed')
)
```

---

#### `run_transaction(query: str, params: tuple = None, fetch_one: bool = False)`
Executes INSERT/UPDATE/DELETE with explicit commit/rollback.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `query` | `str` | SQL statement | Required |
| `params` | `tuple` | Query parameters | `None` |
| `fetch_one` | `bool` | Return single row (for RETURNING) | `False` |

**Returns:** 
- `tuple` if `fetch_one=True` - Single row result
- `bool` if `fetch_one=False` - Success status

**Raises:**
- `ValueError` - Exclusion violation (double booking)
- `RuntimeError` - Schema errors, type adaptation errors

**Example:**
```python
# Insert with RETURNING
result = run_transaction(
    "INSERT INTO bookings (room_id, status) VALUES (%s, %s) RETURNING id",
    (room_id, 'Pending'),
    fetch_one=True
)
booking_id = result[0]

# Update without returning
run_transaction(
    "UPDATE bookings SET status = %s WHERE id = %s",
    ('Confirmed', booking_id)
)
```

---

### Date/Time Utilities

#### `normalize_dates(date_input, time_start, time_end) -> Tuple[datetime, datetime]`
Combines date and time into UTC-aware datetime objects.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `date_input` | `date` | Booking date |
| `time_start` | `time` | Start time |
| `time_end` | `time` | End time |

**Returns:** `(dt_start_utc, dt_end_utc)` - Timezone-aware UTC datetimes

**Configuration:**
- Local timezone from `st.secrets["postgres"]["timezone"]` (default: "Africa/Johannesburg")

**Example:**
```python
from datetime import date, time

start_dt, end_dt = normalize_dates(
    date(2024, 1, 15),
    time(9, 0),
    time(17, 0)
)
# Returns: (datetime(2024, 1, 15, 7, 0, tzinfo=UTC), datetime(2024, 1, 15, 15, 0, tzinfo=UTC))
```

---

### Domain Queries

#### `get_rooms() -> pd.DataFrame`
Fetch available rooms with capacity shim for legacy compatibility.

**Returns:** DataFrame with columns: `id`, `name`, `capacity` (always 0)

**Example:**
```python
rooms_df = get_rooms()
for _, room in rooms_df.iterrows():
    print(f"Room: {room['name']}")
```

---

#### `get_calendar_bookings(days_lookback=30) -> pd.DataFrame`
Fetch bookings for calendar view using Postgres range operators.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `days_lookback` | `int` | Days to look back from now | 30 |

**Returns:** DataFrame with columns: `Room`, `Start`, `End`, `Status`

**Example:**
```python
bookings_df = get_calendar_bookings(days_lookback=7)
```

---

#### `get_calendar_grid(start_date: date, end_date: date) -> pd.DataFrame`
Fetch expanded bookings for calendar grid view.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `start_date` | `date` | Start of range |
| `end_date` | `date` | End of range |

**Returns:** DataFrame with columns:
- `room_id`, `room_name`, `booking_date`
- `booking_id`, `client_name`, `num_learners`, `num_facilitators`, `headcount`
- `coffee_tea_station`, `morning_catering`, `lunch_catering`, `stationery_needed`
- `devices_needed`, `device_count`, `status`, `tenant_id`

**Example:**
```python
from datetime import date, timedelta

week_start = date.today()
week_end = week_start + timedelta(days=6)
calendar_df = get_calendar_grid(week_start, week_end)
```

---

#### `get_rooms_for_calendar() -> pd.DataFrame`
Fetch active rooms ordered for calendar display (custom sort order).

**Returns:** DataFrame with columns: `id`, `name`, `max_capacity`

**Example:**
```python
rooms_df = get_rooms_for_calendar()
# Returns rooms in order: Excellence, Inspiration, Honesty, Gratitude, ...
```

---

#### `get_dashboard_stats(tenant_filter=None) -> pd.DataFrame`
Calculate KPIs for Admin Dashboard.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `tenant_filter` | `str` | Optional tenant filter ('TECH' or 'TRAINING') | `None` |

**Returns:** DataFrame with columns: `total_bookings`, `approved`, `upcoming`

**Example:**
```python
# All bookings
stats = get_dashboard_stats()

# TECH tenant only
tech_stats = get_dashboard_stats(tenant_filter='TECH')
```

---

### Transaction Operations

#### `create_booking(room_id, start_dt, end_dt, purpose, user_ref="SYSTEM", tenant="TECH")`
Core transaction logic for creating bookings.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `room_id` | `int` | Room identifier | Required |
| `start_dt` | `datetime` | Start datetime (UTC) | Required |
| `end_dt` | `datetime` | End datetime (UTC) | Required |
| `purpose` | `str` | Booking purpose/reference | Required |
| `user_ref` | `str` | User reference (legacy) | "SYSTEM" |
| `tenant` | `str` | Tenant ID ('TECH' or 'TRAINING') | "TECH" |

**Returns:** `tuple` - `(booking_id,)` from RETURNING clause

**Raises:**
- `ValueError` - Invalid tenant
- `ValueError` - Exclusion violation (double booking)
- `RuntimeError` - Missing booking_reference column

**Example:**
```python
from datetime import datetime
import pytz

start = datetime(2024, 1, 15, 7, 30, tzinfo=pytz.UTC)
end = datetime(2024, 1, 15, 15, 30, tzinfo=pytz.UTC)

result = create_booking(
    room_id=1,
    start_dt=start,
    end_dt=end,
    purpose="Training Session",
    tenant="TECH"
)
booking_id = result[0]
```

---

## Authentication (auth.py)

### `authenticate(username, password)`
DB-backed credential check with bcrypt verification.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `username` | `str` | User's username |
| `password` | `str` | User's password |

**Returns:** `dict` or `None`

**Success Return:**
```python
{
    "user_id": 1,
    "username": "admin",
    "role": "training_facility_admin"
}
```

**Failure Return:** `None`

**Raises:**
- `ConnectionError` - Database unreachable
- `KeyError` - Missing auth secret

**Example:**
```python
user = authenticate("admin", "admin123")
if user:
    print(f"Welcome {user['username']} ({user['role']})")
else:
    print("Invalid credentials")
```

**Roles:**
- `training_facility_admin` - Room Boss (full room management)
- `it_rental_admin` - IT Boss (full device management)
- `training_facility_admin_viewer` - Read-only viewer
- `kitchen_staff` - Catering view only
- `admin`/`staff` - Default limited access

---

## Type Converter (numpy_type_converter.py)

### `convert_to_native(value: Any) -> Any`
Convert a numpy type to its Python native equivalent.

**Supported Conversions:**
| From | To |
|------|-----|
| `np.int64` | `int` |
| `np.float64` | `float` |
| `np.bool_` | `bool` |
| `np.str_` | `str` |
| `np.datetime64` | `datetime` or `date` |
| `pd.Timestamp` | `datetime` |
| `np.ndarray` (single) | native scalar |
| `np.ndarray` (multi) | `list` |

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `value` | `Any` | Value to convert |

**Returns:** Python native type

**Example:**
```python
import numpy as np
from src.numpy_type_converter import convert_to_native

numpy_int = np.int64(42)
native_int = convert_to_native(numpy_int)  # 42 (int)

numpy_float = np.float64(3.14)
native_float = convert_to_native(numpy_float)  # 3.14 (float)
```

---

### `convert_params_to_native(params: Optional[Tuple, List, Dict]) -> Optional[Tuple, List, Dict]`
Convert all numpy types in a parameters collection to native Python types.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `params` | `tuple/list/dict/None` | Parameters to convert |

**Returns:** Converted parameters (same type as input)

**Example:**
```python
import numpy as np
from src.numpy_type_converter import convert_params_to_native

# Tuple
params = (np.int64(42), np.float64(3.14), 'string')
clean_params = convert_params_to_native(params)
# Returns: (42, 3.14, 'string')

# Dict
params = {'id': np.int64(1), 'score': np.float64(95.5)}
clean_params = convert_params_to_native(params)
# Returns: {'id': 1, 'score': 95.5}
```

---

### `validate_native_types(params: Any) -> Tuple[bool, Optional[str]]`
Validate that parameters contain no numpy types.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `params` | `Any` | Parameters to validate |

**Returns:** `(is_valid, error_message)`

**Example:**
```python
from src.numpy_type_converter import validate_native_types

params = (42, 3.14, 'string')  # All native
is_valid, error = validate_native_types(params)
# is_valid = True, error = None

params = (np.int64(42),)  # Has numpy
is_valid, error = validate_native_types(params)
# is_valid = False, error = "Found numpy types: params[0]: int64"
```

---

### `deep_convert(obj: Any) -> Any`
Deep convert numpy types in nested data structures.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `obj` | `Any` | Object to convert (handles nested dicts/lists) |

**Example:**
```python
import numpy as np
from src.numpy_type_converter import deep_convert

data = {
    'id': np.int64(123),
    'items': [np.float64(1.5), np.float64(2.5)],
    'nested': {'count': np.int32(10)}
}
clean_data = deep_convert(data)
# Returns: {'id': 123, 'items': [1.5, 2.5], 'nested': {'count': 10}}
```

---

### `prepare_for_db(params: Any) -> Any`
Alias for `convert_params_to_native` with descriptive name for database operations.

---

## Configuration

### Secrets (`.streamlit/secrets.toml`)

```toml
[postgres]
host = "100.69.57.77"
port = 5432
dbname = "colab_erp"
user = "colabtechsolutions"
password = "LetMeIn123!"
timezone = "Africa/Johannesburg"

[auth]
admin_user = "admin"
admin_password = "admin123"
staff_user = "staff"
staff_password = "staff123"
```

**Access Pattern:**
```python
import streamlit as st

# PostgreSQL config
host = st.secrets["postgres"]["host"]
port = st.secrets["postgres"]["port"]
timezone = st.secrets["postgres"].get("timezone", "Africa/Johannesburg")

# Auth defaults (fallback only)
admin_user = st.secrets["auth"]["admin_user"]
```

---

### Streamlit Config (`.streamlit/config.toml`)

```toml
[server]
headless = true
runOnSave = true
port = 8501
```

**Settings:**
- `headless` - Run without browser auto-open (server mode)
- `runOnSave` - Auto-rerun when files change
- `port` - Web server port

---

## Error Handling

### Common Error Patterns

#### Connection Errors
```python
from psycopg2 import OperationalError, InterfaceError

try:
    df = run_query("SELECT * FROM rooms")
except ConnectionError as e:
    # Handle connectivity issues (Tailscale, network, etc.)
    print(f"Database unreachable: {e}")
```

#### Exclusion Violations (Double Booking)
```python
try:
    result = create_booking(room_id, start, end, purpose)
except ValueError as e:
    if "Double Booking" in str(e):
        print("Room already booked for this time")
```

#### Schema Errors
```python
try:
    result = create_booking(room_id, start, end, purpose)
except RuntimeError as e:
    if "booking_reference" in str(e):
        print("Missing column - run ALTER TABLE to add it")
```

---

## Version Information

- **System:** Colab ERP v2.2.0
- **Database:** PostgreSQL with psycopg2
- **UI Framework:** Streamlit
- **Python:** 3.10+

---

## See Also

- [Service Guide](SERVICE_GUIDE.md) - Business logic services
- [Database Interface](DATABASE_INTERFACE.md) - Complete db.py documentation
- [UI Components](UI_COMPONENTS.md) - Frontend documentation
