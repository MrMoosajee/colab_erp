# Colab ERP API Documentation

**Version:** v2.2.3  
**Last Updated:** February 27, 2026  

This document describes the public API of the Colab ERP service layer. These services provide the core business logic for room bookings, device management, and workflow processing.

---

## Table of Contents

1. [AvailabilityService](#availabilityservice)
2. [BookingService](#bookingservice)
3. [RoomApprovalService](#roomapprovalservicew)
4. [DeviceManager](#devicemanager)
5. [NotificationManager](#notificationmanager)
6. [Database Module (db.py)](#database-module-dbpy)

---

## AvailabilityService

**File:** `src/models/availability_service.py`

Service for checking room and device availability, conflict detection, and capacity validation.

### Constructor

```python
service = AvailabilityService()
```

Initializes with database connection pool.

---

### get_available_rooms

```python
def get_available_rooms(
    self,
    start_date: date,
    end_date: date,
    min_capacity: Optional[int] = None
) -> pd.DataFrame
```

Get list of rooms available for the specified date range.

**Parameters:**
- `start_date` (date): Start of booking period
- `end_date` (date): End of booking period
- `min_capacity` (Optional[int]): Minimum room capacity required

**Returns:**
- `pd.DataFrame`: Columns: id, name, capacity, room_type, has_devices, conflicting_bookings

**Example:**
```python
service = AvailabilityService()
available = service.get_available_rooms(
    start_date=date(2026, 4, 1),
    end_date=date(2026, 4, 3),
    min_capacity=20
)
```

**Notes:**
- Returns empty DataFrame on error (silent failure - see CDO-003)
- Times default to 07:30-16:30 (facility hours)
- Only returns rooms with no conflicting bookings

---

### get_all_rooms

```python
def get_all_rooms(self) -> pd.DataFrame
```

Get all rooms regardless of availability. Used for admin room selection.

**Returns:**
- `pd.DataFrame`: Columns: id, name, capacity, is_active, parent_room_id

**Example:**
```python
all_rooms = service.get_all_rooms()
room_options = all_rooms['id'].tolist()
```

**Notes:**
- Uses correct column names (max_capacity as capacity)
- Orders by capacity, then name

---

### check_room_conflicts

```python
def check_room_conflicts(
    self,
    room_id: int,
    start_date: date,
    end_date: date,
    exclude_booking_id: Optional[int] = None
) -> Dict[str, Any]
```

Check if room has conflicting bookings.

**Parameters:**
- `room_id` (int): Room to check
- `start_date` (date): Start of proposed booking
- `end_date` (date): End of proposed booking
- `exclude_booking_id` (Optional[int]): Booking ID to exclude (for updates)

**Returns:**
```python
{
    'has_conflict': bool,
    'conflicts': [
        {
            'booking_id': int,
            'client_name': str,
            'start_date': date,
            'end_date': date,
            'status': str
        }
    ],
    'message': str
}
```

**Example:**
```python
conflict_check = service.check_room_conflicts(
    room_id=5,
    start_date=date(2026, 4, 1),
    end_date=date(2026, 4, 3)
)

if conflict_check['has_conflict']:
    print(f"Conflicts: {conflict_check['message']}")
    for conflict in conflict_check['conflicts']:
        print(f"  - {conflict['client_name']}")
```

---

### validate_booking_capacity

```python
def validate_booking_capacity(
    self,
    room_id: int,
    total_attendees: int
) -> Dict[str, Any]
```

Validate if room can accommodate the requested number of attendees.

**Parameters:**
- `room_id` (int): Room to check
- `total_attendees` (int): Total number of people

**Returns:**
```python
{
    'valid': bool,           # Can accommodate
    'warning': bool,         # Near capacity (>90%)
    'message': str           # User-friendly message
}
```

**Example:**
```python
validation = service.validate_booking_capacity(
    room_id=5,
    total_attendees=25
)

if not validation['valid']:
    st.error(validation['message'])
elif validation['warning']:
    st.warning(validation['message'])
else:
    st.success(validation['message'])
```

---

### check_device_availability

```python
def check_device_availability(
    self,
    devices_needed: int,
    start_date: date,
    end_date: date,
    device_type: str = 'any'
) -> Dict[str, Any]
```

Check if requested number of devices are available.

**Parameters:**
- `devices_needed` (int): Number of devices required
- `start_date` (date): Start of booking period
- `end_date` (date): End of booking period
- `device_type` (str): 'any', 'laptops', or 'desktops'

**Returns:**
```python
{
    'available': bool,
    'available_count': int,
    'message': str
}
```

**Example:**
```python
device_check = service.check_device_availability(
    devices_needed=10,
    start_date=date(2026, 4, 1),
    end_date=date(2026, 4, 3),
    device_type='laptops'
)

if device_check['available']:
    st.success(device_check['message'])
else:
    st.error(device_check['message'])
```

---

## BookingService

**File:** `src/models/booking_service.py`

Service for creating enhanced bookings with all Phase 3 fields.

### Constructor

```python
service = BookingService()
```

---

### create_enhanced_booking

```python
def create_enhanced_booking(
    self,
    room_id: Optional[int],
    start_date: date,
    end_date: date,
    client_name: str,
    client_contact_person: str,
    client_email: str,
    client_phone: str,
    num_learners: int = 0,
    num_facilitators: int = 0,
    coffee_tea_station: bool = False,
    morning_catering: Optional[str] = None,
    lunch_catering: Optional[str] = None,
    catering_notes: Optional[str] = None,
    stationery_needed: bool = False,
    water_bottles: int = 0,
    devices_needed: int = 0,
    device_type_preference: Optional[str] = None,
    room_boss_notes: Optional[str] = None,
    status: str = 'Pending',
    created_by: Optional[str] = None
) -> Dict[str, Any]
```

Create an enhanced booking with all Phase 3 fields.

**Parameters:**
- `room_id` (Optional[int]): Room ID or None for pending (Ghost Inventory)
- `start_date` (date): Booking start date
- `end_date` (date): Booking end date
- `client_name` (str): Client/company name
- `client_contact_person` (str): Primary contact person
- `client_email` (str): Contact email
- `client_phone` (str): Contact phone
- `num_learners` (int): Number of learners
- `num_facilitators` (int): Number of facilitators
- `coffee_tea_station` (bool): Coffee/tea station required
- `morning_catering` (Optional[str]): 'pastry', 'sandwiches', or None
- `lunch_catering` (Optional[str]): 'self_catered', 'in_house', or None
- `catering_notes` (Optional[str]): Special catering requests
- `stationery_needed` (bool): Pen & book per person
- `water_bottles` (int): Water bottles per day
- `devices_needed` (int): Number of devices required
- `device_type_preference` (Optional[str]): 'laptops', 'desktops', or None
- `room_boss_notes` (Optional[str]): Notes for Room Boss
- `status` (str): 'Pending', 'Confirmed', or 'Room Assigned'
- `created_by` (Optional[str]): Username of creator

**Returns:**
```python
{
    'success': bool,
    'booking_id': Optional[int],
    'message': str
}
```

**Example:**
```python
result = service.create_enhanced_booking(
    room_id=None,  # Ghost Inventory - goes to pending
    start_date=date(2026, 4, 1),
    end_date=date(2026, 4, 3),
    client_name="Acme Corp",
    client_contact_person="John Doe",
    client_email="john@acme.com",
    client_phone="+27 123 456 7890",
    num_learners=15,
    num_facilitators=2,
    coffee_tea_station=True,
    morning_catering="pastry",
    lunch_catering="in_house",
    devices_needed=15,
    device_type_preference="laptops",
    status='Pending',
    created_by='admin'
)

if result['success']:
    st.success(f"Booking #{result['booking_id']} created")
else:
    st.error(result['message'])
```

**Notes:**
- Times default to 07:30-16:30
- If room_id is None, status should be 'Pending'
- If room_id is provided, status should be 'Confirmed'

---

### get_booking_details

```python
def get_booking_details(self, booking_id: int) -> Dict[str, Any]
```

Retrieve full booking details including all Phase 3 fields.

**Parameters:**
- `booking_id` (int): Booking ID

**Returns:**
```python
{
    'success': bool,
    'booking': {           # Only if success=True
        'id': int,
        'room_id': int,
        'room_name': str,
        'booking_period': str,
        'client_name': str,
        # ... all other fields
    },
    'message': str        # Only if success=False
}
```

**Example:**
```python
details = service.get_booking_details(123)
if details['success']:
    booking = details['booking']
    print(f"Client: {booking['client_name']}")
```

---

## RoomApprovalService

**File:** `src/models/room_approval_service.py`

Service for Room Boss workflow - Ghost Inventory room assignment.

### Constructor

```python
service = RoomApprovalService()
```

---

### get_pending_bookings

```python
def get_pending_bookings(self, limit: int = 50) -> pd.DataFrame
```

Get all bookings pending room assignment.

**Parameters:**
- `limit` (int): Maximum number of bookings to return (default: 50)

**Returns:**
- `pd.DataFrame`: Columns include:
  - booking_id, client_name, client_contact_person
  - client_email, client_phone, num_learners, num_facilitators
  - total_headcount, start_date, end_date
  - requested_room_name, morning_catering, lunch_catering
  - devices_needed, status, created_by

**Example:**
```python
pending = service.get_pending_bookings(limit=20)
for _, booking in pending.iterrows():
    print(f"#{booking['booking_id']}: {booking['client_name']}")
```

---

### get_room_occupancy

```python
def get_room_occupancy(
    self, 
    start_date: date, 
    end_date: date, 
    exclude_booking_id: Optional[int] = None
) -> pd.DataFrame
```

Get room occupancy for date range to show Room Boss current bookings.

**Parameters:**
- `start_date` (date): Start of date range
- `end_date` (date): End of date range
- `exclude_booking_id` (Optional[int]): Booking to exclude from results

**Returns:**
- `pd.DataFrame`: Columns: room_id, room_name, capacity, booking_id, client_name, booking_start, booking_end, status, headcount

**Example:**
```python
occupancy = service.get_room_occupancy(
    start_date=date(2026, 4, 1),
    end_date=date(2026, 4, 3)
)
```

---

### check_room_conflicts

```python
def check_room_conflicts(
    self, 
    room_id: int, 
    start_date: date, 
    end_date: date,
    exclude_booking_id: Optional[int] = None
) -> Dict[str, Any]
```

Check if room has conflicting bookings (same as AvailabilityService).

**Returns:**
```python
{
    'has_conflict': bool,
    'conflicts': [...],
    'message': str,
    'can_override': bool
}
```

---

### assign_room

```python
def assign_room(
    self, 
    booking_id: int, 
    room_id: int, 
    room_boss_id: str,
    notes: Optional[str] = None,
    override_conflict: bool = False
) -> Dict[str, Any]
```

Assign room to pending booking.

**Parameters:**
- `booking_id` (int): ID of booking to update
- `room_id` (int): ID of room to assign
- `room_boss_id` (str): Username of room boss making assignment
- `notes` (Optional[str]): Optional notes about decision
- `override_conflict` (bool): Whether to proceed despite conflicts

**Returns:**
```python
{
    'success': bool,
    'message': str,
    'room_name': str,       # Only if success=True
    'override_used': bool   # Only if success=True
}
```

**Example:**
```python
result = service.assign_room(
    booking_id=123,
    room_id=5,
    room_boss_id='room_boss_1',
    notes='Client requested room with projector',
    override_conflict=False
)

if result['success']:
    st.success(result['message'])
else:
    st.error(result['error'])
```

---

### get_room_list

```python
def get_room_list(self) -> pd.DataFrame
```

Get list of all available rooms for selection.

**Returns:**
- `pd.DataFrame`: Columns: id, name, capacity, room_type, has_devices

---

### reject_booking

```python
def reject_booking(
    self, 
    booking_id: int, 
    room_boss_id: str,
    reason: str
) -> Dict[str, Any]
```

Reject a pending booking with reason.

**Parameters:**
- `booking_id` (int): Booking to reject
- `room_boss_id` (str): Username of room boss
- `reason` (str): Rejection reason

**Returns:**
```python
{
    'success': bool,
    'message': str  # or 'error' if success=False
}
```

---

## DeviceManager

**File:** `src/models/device_manager.py`

Service for device inventory, assignment, and tracking.

### Constructor

```python
manager = DeviceManager()
```

---

### get_available_devices

```python
def get_available_devices(
    self, 
    category: str, 
    start_date: date, 
    end_date: date,
    exclude_booking_id: Optional[int] = None
) -> pd.DataFrame
```

Get devices available for a date range.

**Parameters:**
- `category` (str): Device category ('Laptop', 'Desktop', etc.)
- `start_date` (date): Start of booking period
- `end_date` (date): End of booking period
- `exclude_booking_id` (Optional[int]): Booking to exclude from conflict check

**Returns:**
- `pd.DataFrame`: Columns: id, serial_number, name, status, category_name, office_account, anydesk_id

**Example:**
```python
available = manager.get_available_devices(
    category='Laptop',
    start_date=date(2026, 4, 1),
    end_date=date(2026, 4, 3)
)
```

---

### get_devices_by_booking

```python
def get_devices_by_booking(self, booking_id: int) -> pd.DataFrame
```

Get all devices assigned to a specific booking.

**Parameters:**
- `booking_id` (int): The booking ID

**Returns:**
- `pd.DataFrame`: Columns: assignment_id, device_id, serial_number, name, category_name, is_offsite, assigned_at, assigned_by

---

### assign_device

```python
def assign_device(
    self, 
    booking_id: int, 
    device_id: int, 
    assigned_by: str,
    is_offsite: bool = False,
    notes: Optional[str] = None
) -> Dict
```

Assign a specific device to a booking.

**Parameters:**
- `booking_id` (int): The booking to assign to
- `device_id` (int): The specific device ID
- `assigned_by` (str): Username of IT Staff performing assignment
- `is_offsite` (bool): Whether device is going off-site
- `notes` (Optional[str]): Optional notes

**Returns:**
```python
{
    'success': bool,
    'assignment_id': int,  # Only if success=True
    'message': str,        # or 'error' if success=False
}
```

**Example:**
```python
result = manager.assign_device(
    booking_id=123,
    device_id=45,
    assigned_by='it_staff_1',
    is_offsite=False
)
```

---

### unassign_device

```python
def unassign_device(self, assignment_id: int) -> Dict
```

Remove device assignment.

**Parameters:**
- `assignment_id` (int): The assignment ID to remove

**Returns:**
```python
{
    'success': bool,
    'message': str  # or 'error' if success=False
}
```

---

### get_device_conflicts

```python
def get_device_conflicts(
    self, 
    device_id: int, 
    start_date: date, 
    end_date: date,
    exclude_booking_id: Optional[int] = None
) -> pd.DataFrame
```

Find bookings that conflict with proposed device usage.

**Parameters:**
- `device_id` (int): The device to check
- `start_date` (date): Proposed start date
- `end_date` (date): Proposed end date
- `exclude_booking_id` (Optional[int]): Optional booking to exclude

**Returns:**
- `pd.DataFrame`: Columns: booking_id, client_name, room_name, start_date, end_date, status

---

### can_reallocate_device

```python
def can_reallocate_device(
    self,
    device_id: int,
    from_booking_id: int,
    to_booking_id: int
) -> Dict
```

Check if device can be reallocated between bookings.

**Returns:**
```python
{
    'can_reallocate': bool,
    'reason': str,
    'requires_boss_approval': bool,
    'warning': str  # Optional
}
```

---

### reallocate_device

```python
def reallocate_device(
    self,
    device_id: int,
    from_booking_id: int,
    to_booking_id: int,
    performed_by: str,
    reason: Optional[str] = None
) -> Dict
```

Move device from one booking to another.

---

### check_stock_levels

```python
def check_stock_levels(
    self,
    category: str,
    future_date: date,
    min_threshold: int = 5
) -> Dict
```

Check if stock is running low for future date.

**Returns:**
```python
{
    'category': str,
    'total_devices': int,
    'available': int,
    'date': date,
    'is_low': bool,
    'threshold': int,
    'warning': str  # Only if is_low=True
}
```

---

### create_offsite_rental

```python
def create_offsite_rental(
    self,
    assignment_id: int,
    rental_no: str,
    rental_date: date,
    contact_person: str,
    contact_number: str,
    contact_email: Optional[str],
    company: Optional[str],
    address: str,
    return_expected_date: date
) -> Dict
```

Create off-site rental record.

---

## NotificationManager

**File:** `src/models/notification_manager.py`

Service for in-app notifications to IT Boss and Room Boss.

### Constructor

```python
manager = NotificationManager()
```

---

### create_notification

```python
def create_notification(
    self,
    notification_type: str,
    title: str,
    message: str,
    recipients: List[str],
    category_id: Optional[int] = None,
    related_booking_id: Optional[int] = None,
    related_device_id: Optional[int] = None
) -> Dict
```

Create a new notification.

**Notification Types:**
- `low_stock`: Low device stock alert
- `conflict_no_alternatives`: Device conflict with no alternatives
- `offsite_conflict`: Off-site rental conflict
- `return_overdue`: Overdue device return
- `daily_summary`: Daily notification summary

**Parameters:**
- `notification_type` (str): Type of notification
- `title` (str): Short title
- `message` (str): Full message content
- `recipients` (List[str]): List of roles ['it_boss', 'room_boss']
- `category_id` (Optional[int]): Related device category
- `related_booking_id` (Optional[int]): Related booking
- `related_device_id` (Optional[int]): Related device

**Returns:**
```python
{
    'success': bool,
    'notification_id': int,  # Only if success=True
    'message': str          # or 'error' if success=False
}
```

---

### get_notifications_for_user

```python
def get_notifications_for_user(
    self,
    user_role: str,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    limit: int = 100
) -> pd.DataFrame
```

Get notifications for a specific user role.

**Parameters:**
- `user_role` (str): Role of user ('it_boss', 'room_boss', 'admin')
- `unread_only` (bool): If True, only return unread notifications
- `notification_type` (Optional[str]): Filter by type
- `limit` (int): Maximum to return (default: 100)

**Returns:**
- `pd.DataFrame`: Notifications with columns including id, notification_type, message, is_read, created_at

---

### get_unread_count

```python
def get_unread_count(self, user_role: str) -> int
```

Get count of unread notifications for a user.

---

### mark_as_read

```python
def mark_as_read(self, notification_id: int) -> Dict
```

Mark a specific notification as read.

---

### mark_all_as_read

```python
def mark_all_as_read(self, user_role: str) -> Dict
```

Mark all notifications as read for a user.

**Returns:**
```python
{
    'success': bool,
    'message': str,
    'count': int  # Number marked as read
}
```

---

### check_overdue_returns

```python
def check_overdue_returns(self) -> List[Dict]
```

Check for overdue off-site rentals and create notifications.

**Returns:** List of created notification dicts

---

## Database Module (db.py)

**File:** `src/db.py`

Low-level database operations and connection management.

### Connection Management

#### get_db_pool

```python
@st.cache_resource
def get_db_pool() -> ThreadedConnectionPool
```

Creates a ThreadedConnectionPool. Cached once per process.

**Returns:** `psycopg2.pool.ThreadedConnectionPool`

**Configuration:**
- minconn: 1
- maxconn: 20
- Timezone: UTC

---

#### get_db_connection

```python
@contextmanager
def get_db_connection()
```

Context manager to checkout a connection from the pool.

**Usage:**
```python
with db.get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT ...")
```

---

### Query Execution

#### run_query

```python
def run_query(query: str, params: tuple = None) -> pd.DataFrame
```

Execute a SELECT query (Read-Only).

**Parameters:**
- `query` (str): SQL query string
- `params` (tuple): Query parameters (for parameterized queries)

**Returns:** `pd.DataFrame` with query results

**Raises:**
- `ConnectionError`: Database connectivity issues
- `RuntimeError`: SQL errors (syntax, missing table, etc.)

**Example:**
```python
df = db.run_query(
    "SELECT * FROM bookings WHERE status = %s",
    ('Confirmed',)
)
```

---

#### run_transaction

```python
def run_transaction(
    query: str, 
    params: tuple = None, 
    fetch_one: bool = False
)
```

Execute INSERT/UPDATE/DELETE (Write operation).

**Parameters:**
- `query` (str): SQL query
- `params` (tuple): Query parameters
- `fetch_one` (bool): If True, returns cursor.fetchone() (for RETURNING clauses)

**Returns:**
- `True` if successful (fetch_one=False)
- Tuple if successful (fetch_one=True)

**Raises:**
- `ValueError`: ExclusionViolation (double booking)
- `RuntimeError`: UndefinedColumn or other SQL errors

**Example:**
```python
result = db.run_transaction(
    "INSERT INTO bookings (room_id) VALUES (%s) RETURNING id",
    (5,),
    fetch_one=True
)
booking_id = result[0]
```

---

### Utility Functions

#### normalize_dates

```python
def normalize_dates(
    date_input, 
    time_start, 
    time_end
) -> Tuple[datetime, datetime]
```

Combine date and time inputs into UTC-aware datetime objects.

**Parameters:**
- `date_input` (date): Booking date
- `time_start` (time): Start time
- `time_end` (time): End time

**Returns:** `(start_dt_utc, end_dt_utc)`

**Example:**
```python
start_dt, end_dt = db.normalize_dates(
    date_input=date(2026, 4, 1),
    time_start=time(9, 0),
    time_end=time(17, 0)
)
# Returns UTC-aware datetimes
```

---

### Domain Functions

#### get_rooms

```python
def get_rooms() -> pd.DataFrame
```

Fetch available rooms with capacity shim.

**Returns:** DataFrame with columns: id, name, capacity

---

#### get_calendar_bookings

```python
def get_calendar_bookings(days_lookback: int = 30) -> pd.DataFrame
```

Fetch bookings for calendar view (legacy format).

---

#### get_calendar_grid

```python
def get_calendar_grid(start_date, end_date) -> pd.DataFrame
```

Fetch bookings for calendar grid view with device counts.

**Returns:** DataFrame with expanded bookings across date range

---

#### get_rooms_for_calendar

```python
def get_rooms_for_calendar() -> pd.DataFrame
```

Fetch active rooms ordered for calendar display.

**Returns:** DataFrame ordered by room display priority

---

#### get_dashboard_stats

```python
def get_dashboard_stats(tenant_filter: str = None) -> pd.DataFrame
```

Calculate KPIs for Admin Dashboard.

**Parameters:**
- `tenant_filter` (str): Optional 'TECH' or 'TRAINING' filter

**Returns:** DataFrame with columns: total_bookings, approved, upcoming

---

#### create_booking

```python
def create_booking(
    room_id: int,
    start_dt: datetime,
    end_dt: datetime,
    purpose: str,
    user_ref: str = "SYSTEM",
    tenant: str = "TECH"
) -> tuple
```

Core booking creation (simplified version).

**Note:** For Phase 3 bookings with all fields, use `BookingService.create_enhanced_booking()`

---

## Error Handling

All services follow a consistent error handling pattern:

### Return Value Pattern

```python
# Success
{
    'success': True,
    'data': ...,          # Optional
    'message': '...'      # Optional success message
}

# Failure
{
    'success': False,
    'error': '...',       # Error description
    'details': ...        # Optional additional info
}
```

### Exception Handling

**Database Module:**
- Raises `ConnectionError` for connectivity issues
- Raises `RuntimeError` for SQL errors
- Raises `ValueError` for constraint violations

**Service Layer:**
- Catches exceptions internally
- Returns dict with `success: False`
- Logs errors (though currently via print - see CDO-003)

---

## Best Practices

1. **Always check success flag:**
   ```python
   result = service.some_operation(...)
   if not result['success']:
       handle_error(result.get('error'))
   ```

2. **Use parameterized queries:**
   ```python
   # Good
   db.run_query("SELECT * FROM bookings WHERE id = %s", (booking_id,))
   
   # Bad - SQL injection risk
   db.run_query(f"SELECT * FROM bookings WHERE id = {booking_id}")
   ```

3. **Handle timezone properly:**
   ```python
   # Always use pytz.UTC.localize() for database operations
   utc = pytz.UTC
   dt = utc.localize(datetime.combine(date, time))
   ```

4. **Release connections:**
   ```python
   # Good - context manager
   with db.get_db_connection() as conn:
       ...
   
   # Good - manual finally
   try:
       conn = pool.getconn()
       ...
   finally:
       pool.putconn(conn)
   ```

---

**Document Version:** 1.0.0  
**Last Updated:** February 27, 2026  
**Maintained by:** Chief Documentation Officer (CDO-001)
