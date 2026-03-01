# Colab ERP API Documentation

Complete API and interface documentation for Colab ERP v2.2.0.

## Documentation Files

| Document | Description |
|----------|-------------|
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API reference for all public interfaces, functions, and methods |
| [SERVICE_GUIDE.md](SERVICE_GUIDE.md) | Service classes documentation - DeviceManager, BookingService, etc. |
| [DATABASE_INTERFACE.md](DATABASE_INTERFACE.md) | Database layer (db.py) operations and utilities |
| [UI_COMPONENTS.md](UI_COMPONENTS.md) | Streamlit frontend components and views |

## Quick Reference

### Service Classes

```python
from src.models import (
    DeviceManager,          # Device inventory and assignments
    NotificationManager,    # Notifications for IT/Room Boss
    BookingService,         # Enhanced booking creation
    AvailabilityService,    # Room/device availability
    RoomApprovalService,    # Ghost inventory room assignment
    PricingService          # Dynamic pricing management
)
```

### Database Operations

```python
import src.db as db

# Read operations
df = db.run_query("SELECT * FROM rooms WHERE id = %s", (room_id,))

# Write operations
result = db.run_transaction(
    "INSERT INTO bookings (...) VALUES (...) RETURNING id",
    (params,),
    fetch_one=True
)
booking_id = result[0]

# Date normalization (UTC)
start_utc, end_utc = db.normalize_dates(date, start_time, end_time)
```

### Authentication

```python
from src.auth import authenticate

user = authenticate("username", "password")
if user:
    print(f"Role: {user['role']}")  # training_facility_admin, it_rental_admin, etc.
```

### Type Conversion

```python
from src.numpy_type_converter import convert_params_to_native

# Convert numpy types for database safety
clean_params = convert_params_to_native((np.int64(42), np.float64(3.14)))
```

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│         (Streamlit - UI_COMPONENTS.md)                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                          │
│    (BookingService, DeviceManager - SERVICE_GUIDE.md)  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Database Interface                       │
│              (db.py - DATABASE_INTERFACE.md)            │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                     │
└─────────────────────────────────────────────────────────┘
```

## Version Information

- **System:** Colab ERP v2.2.0
- **Framework:** Streamlit
- **Database:** PostgreSQL with psycopg2
- **Python:** 3.10+

## Key Features

### Multi-Tenancy Support
- TECH tenant (default)
- TRAINING tenant
- Shared physical assets (exclusion constraints are global)

### Ghost Inventory Pattern
- Bookings created without immediate room assignment
- Room Boss assigns rooms later
- Conflict detection with override capability

### Device Management
- Manual IT Staff assignment (no AI)
- Off-site rental tracking
- Conflict detection and reallocation

### Real-time Calendar
- Excel-style grid view
- Week/Month toggle
- Horizontal scrolling for many rooms
- Color-coded booking indicators

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
```

### Streamlit Config (`.streamlit/config.toml`)

```toml
[server]
headless = true
runOnSave = true
port = 8501
```

## Role Definitions

| Role | Access Level | Key Permissions |
|------|-------------|-----------------|
| `training_facility_admin` | Full | Room assignment, all views |
| `it_rental_admin` | Full | Device queue, all views |
| `training_facility_admin_viewer` | Read-only | View only, no approvals |
| `kitchen_staff` | Limited | Calendar with catering view |
| `admin`/`staff` | Default | Calendar, booking forms |

## Database Schema Notes

### Critical Fields
- `booking_period`: `tstzrange` type for timezone-aware periods
- `room_id`: NOT NULL (use placeholder for device-only bookings)
- `status`: 'Pending', 'Room Assigned', 'Confirmed', 'Rejected'
- `tenant_id`: 'TECH' or 'TRAINING'

### Exclusion Constraints
- Prevents double bookings at database level
- Global across all tenants (shared rooms)
- Uses GiST index on `booking_period`

## Support

For technical issues or questions about the API, refer to the detailed documentation in each markdown file.

---

**Location:** `/home/shuaibadams/Projects/colab_erp/docs/api/`
