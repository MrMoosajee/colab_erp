# Colab ERP Service Guide

Complete documentation for all service classes and business logic.

## Table of Contents

1. [DeviceManager](#devicemanager)
2. [NotificationManager](#notificationmanager)
3. [BookingService](#bookingservice)
4. [AvailabilityService](#availabilityservice)
5. [RoomApprovalService](#roomapprovalservice)
6. [PricingService](#pricingservice)

---

## DeviceManager

**Location:** `src/models/device_manager.py`

Manages device inventory, assignments, and movements. All decisions are manual (IT Staff) with comprehensive logging for future AI training.

### Constructor

#### `DeviceManager()`
Initialize DeviceManager with database connection.

**Example:**
```python
from src.models import DeviceManager

device_manager = DeviceManager()
```

---

### Device Availability

#### `get_available_devices(category, start_date, end_date, exclude_booking_id=None) -> pd.DataFrame`
Get devices available for a date range.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `category` | `str` | Device category ('Laptop', 'Desktop', etc.) | Required |
| `start_date` | `date` | Start of booking period | Required |
| `end_date` | `date` | End of booking period | Required |
| `exclude_booking_id` | `int` | Optional booking ID to exclude | `None` |

**Returns:** `pd.DataFrame` with columns:
- `id`, `serial_number`, `name`, `status`
- `category_name`, `office_account`, `anydesk_id`

**Example:**
```python
from datetime import date

available = device_manager.get_available_devices(
    category='Laptop',
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17)
)

print(f"Found {len(available)} available laptops")
for _, device in available.iterrows():
    print(f"  - {device['serial_number']} ({device['name']})")
```

---

#### `get_devices_by_booking(booking_id) -> pd.DataFrame`
Get all devices assigned to a specific booking.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `booking_id` | `int` | The booking ID |

**Returns:** `pd.DataFrame` with columns:
- `assignment_id`, `device_id`, `serial_number`, `name`
- `category_name`, `is_offsite`, `assigned_at`, `assigned_by`

**Example:**
```python
devices = device_manager.get_devices_by_booking(123)
for _, device in devices.iterrows():
    print(f"Assigned: {device['serial_number']} ({device['category_name']})")
```

---

### Device Assignment

#### `assign_device(booking_id, device_id, assigned_by, is_offsite=False, notes=None) -> Dict`
Assign a specific device to a booking.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `booking_id` | `int` | Booking to assign to | Required |
| `device_id` | `int` | Device ID to assign | Required |
| `assigned_by` | `str` | Username of IT Staff | Required |
| `is_offsite` | `bool` | Whether off-site rental | `False` |
| `notes` | `str` | Optional notes | `None` |

**Returns:** `Dict` with keys:
- `success` (bool)
- `assignment_id` (int, on success)
- `message` (str, on success)
- `error` (str, on failure)

**Example:**
```python
result = device_manager.assign_device(
    booking_id=123,
    device_id=45,
    assigned_by="it_staff_01",
    is_offsite=True,
    notes="Client requested off-site delivery"
)

if result['success']:
    print(f"Assigned! ID: {result['assignment_id']}")
else:
    print(f"Failed: {result['error']}")
```

---

#### `unassign_device(assignment_id) -> Dict`
Remove device assignment.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `assignment_id` | `int` | Assignment ID to remove |

**Returns:** `Dict` with `success`, `message`/`error`

**Example:**
```python
result = device_manager.unassign_device(456)
if result['success']:
    print(f"Removed: {result['message']}")
```

---

### Conflict Management

#### `get_device_conflicts(device_id, start_date, end_date, exclude_booking_id=None) -> pd.DataFrame`
Find bookings that conflict with proposed device usage.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `device_id` | `int` | Device to check | Required |
| `start_date` | `date` | Proposed start | Required |
| `end_date` | `date` | Proposed end | Required |
| `exclude_booking_id` | `int` | Booking to exclude | `None` |

**Returns:** `pd.DataFrame` with columns:
- `booking_id`, `client_name`, `room_name`
- `start_date`, `end_date`, `status`

**Example:**
```python
conflicts = device_manager.get_device_conflicts(
    device_id=45,
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17)
)

if not conflicts.empty:
    print(f"Conflicts found: {len(conflicts)}")
    for _, conflict in conflicts.iterrows():
        print(f"  - {conflict['client_name']}: {conflict['start_date']} to {conflict['end_date']}")
```

---

#### `can_reallocate_device(device_id, from_booking_id, to_booking_id) -> Dict`
Check if device can be reallocated between bookings.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `device_id` | `int` | Device to reallocate |
| `from_booking_id` | `int` | Source booking |
| `to_booking_id` | `int` | Target booking |

**Returns:** `Dict` with keys:
- `can_reallocate` (bool)
- `reason` (str)
- `requires_boss_approval` (bool)
- `warning` (str, optional)

**Example:**
```python
check = device_manager.can_reallocate_device(
    device_id=45,
    from_booking_id=100,
    to_booking_id=101
)

if check['can_reallocate']:
    print(f"✅ Can reallocate: {check['reason']}")
    if check.get('warning'):
        print(f"⚠️ Warning: {check['warning']}")
else:
    print(f"❌ Cannot reallocate: {check['reason']}")
```

---

#### `reallocate_device(device_id, from_booking_id, to_booking_id, performed_by, reason=None) -> Dict`
Move device from one booking to another.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `device_id` | `int` | Device to move | Required |
| `from_booking_id` | `int` | Source booking | Required |
| `to_booking_id` | `int` | Target booking | Required |
| `performed_by` | `str` | IT Staff username | Required |
| `reason` | `str` | Reason for movement | `None` |

**Returns:** `Dict` with `success`, `message`/`error`

**Example:**
```python
result = device_manager.reallocate_device(
    device_id=45,
    from_booking_id=100,
    to_booking_id=101,
    performed_by="it_staff_01",
    reason="Client requested upgrade"
)

if result['success']:
    print(f"✅ {result['message']}")
else:
    print(f"❌ Failed: {result['error']}")
```

---

#### `get_alternative_devices(category, start_date, end_date, exclude_device_id) -> pd.DataFrame`
Get alternative devices when preferred is unavailable.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `category` | `str` | Device category |
| `start_date` | `date` | Required start |
| `end_date` | `date` | Required end |
| `exclude_device_id` | `int` | Device to exclude |

**Returns:** `pd.DataFrame` with alternative devices

**Example:**
```python
alternatives = device_manager.get_alternative_devices(
    category='Laptop',
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17),
    exclude_device_id=45  # The conflicting device
)

if alternatives.empty:
    print("❌ No alternatives available")
else:
    print(f"✅ {len(alternatives)} alternatives found")
```

---

### Stock Management

#### `check_stock_levels(category, future_date, min_threshold=5) -> Dict`
Check if stock is running low for future date.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `category` | `str` | Device category | Required |
| `future_date` | `date` | Date to check | Required |
| `min_threshold` | `int` | Minimum acceptable stock | 5 |

**Returns:** `Dict` with keys:
- `category`, `total_devices`, `available`, `date`
- `is_low` (bool), `threshold`, `warning` (str, if low)

**Example:**
```python
status = device_manager.check_stock_levels(
    category='Laptop',
    future_date=date(2024, 2, 1),
    min_threshold=10
)

print(f"Total: {status['total_devices']}, Available: {status['available']}")
if status['is_low']:
    print(f"⚠️ {status['warning']}")
```

---

### Off-site Rentals

#### `create_offsite_rental(assignment_id, rental_no, rental_date, contact_person, contact_number, contact_email, company, address, return_expected_date) -> Dict`
Create off-site rental record.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `assignment_id` | `int` | Booking device assignment ID |
| `rental_no` | `str` | Rental document number |
| `rental_date` | `date` | Date of rental |
| `contact_person` | `str` | Contact name |
| `contact_number` | `str` | Contact phone |
| `contact_email` | `str` | Contact email (optional) |
| `company` | `str` | Company name (optional) |
| `address` | `str` | Delivery address |
| `return_expected_date` | `date` | Expected return |

**Returns:** `Dict` with `success`, `offsite_rental_id`/`error`

**Example:**
```python
result = device_manager.create_offsite_rental(
    assignment_id=789,
    rental_no="REN-2024-001",
    rental_date=date(2024, 1, 15),
    contact_person="John Doe",
    contact_number="+27 123 456 7890",
    contact_email="john@example.com",
    company="ABC Corp",
    address="123 Main St, Johannesburg",
    return_expected_date=date(2024, 1, 20)
)

if result['success']:
    print(f"Rental created: ID {result['offsite_rental_id']}")
```

---

### Inventory Dashboard

#### `get_inventory_summary() -> Dict`
Get overall inventory summary statistics.

**Returns:** `Dict` with keys:
- `total_devices`, `available`, `assigned`, `offsite`
- `available_percent` (float)

**Example:**
```python
summary = device_manager.get_inventory_summary()
print(f"Total: {summary['total_devices']}")
print(f"Available: {summary['available']} ({summary['available_percent']:.1f}%)")
print(f"Assigned: {summary['assigned']}")
print(f"Off-site: {summary['offsite']}")
```

---

#### `get_device_categories() -> pd.DataFrame`
Get all device categories.

**Returns:** `pd.DataFrame` with `id`, `name`

**Example:**
```python
categories = device_manager.get_device_categories()
for _, cat in categories.iterrows():
    print(f"Category: {cat['name']} (ID: {cat['id']})")
```

---

#### `get_category_stats(category_id) -> Dict`
Get statistics for a specific device category.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `category_id` | `int` | Category ID |

**Returns:** `Dict` with `total`, `available`, `low_stock` (bool)

**Example:**
```python
stats = device_manager.get_category_stats(1)
print(f"Category 1: {stats['total']} total, {stats['available']} available")
if stats['low_stock']:
    print("⚠️ Low stock warning!")
```

---

#### `get_devices_detailed(status=None, category=None, serial_search=None) -> pd.DataFrame`
Get detailed device list with optional filters.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `status` | `str` | Filter by status | `None` |
| `category` | `str` | Filter by category | `None` |
| `serial_search` | `str` | Search serial number | `None` |

**Returns:** `pd.DataFrame` with columns:
- `serial_number`, `name`, `category`, `status`
- `office_account`, `anydesk_id`, `current_assignment`, `assigned_until`

**Example:**
```python
# All available laptops
available_laptops = device_manager.get_devices_detailed(
    status='available',
    category='Laptop'
)

# Search by serial
search_results = device_manager.get_devices_detailed(
    serial_search='ABC123'
)
```

---

#### `get_recent_activity(limit=20) -> pd.DataFrame`
Get recent inventory activity.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `limit` | `int` | Max records to return | 20 |

**Returns:** `pd.DataFrame` with `timestamp`, `action`, `device_serial`, `user`, `details`

**Example:**
```python
activity = device_manager.get_recent_activity(limit=10)
for _, row in activity.iterrows():
    print(f"[{row['timestamp']}] {row['action']}: {row['device_serial']} by {row['user']}")
```

---

#### `export_inventory_csv() -> str`
Export full inventory to CSV format.

**Returns:** `str` - CSV formatted data

**Example:**
```python
csv_data = device_manager.export_inventory_csv()
# Save to file
with open('inventory_export.csv', 'w') as f:
    f.write(csv_data)
```

---

## NotificationManager

**Location:** `src/models/notification_manager.py`

Manages in-app notifications for IT Boss and Room Boss. All notifications are kept forever for AI training.

### Constructor

#### `NotificationManager()`
Initialize NotificationManager.

**Example:**
```python
from src.models import NotificationManager

notification_manager = NotificationManager()
```

---

### Notification Types

**Class Constants:**
```python
TYPE_LOW_STOCK = 'low_stock'
TYPE_CONFLICT_NO_ALTERNATIVES = 'conflict_no_alternatives'
TYPE_OFFSITE_CONFLICT = 'offsite_conflict'
TYPE_RETURN_OVERDUE = 'return_overdue'
TYPE_DAILY_SUMMARY = 'daily_summary'
```

---

### Creating Notifications

#### `create_notification(notification_type, title, message, recipients, category_id=None, related_booking_id=None, related_device_id=None) -> Dict`
Create a new notification.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `notification_type` | `str` | Type of notification | Required |
| `title` | `str` | Short title | Required |
| `message` | `str` | Full message | Required |
| `recipients` | `List[str]` | Roles to notify | Required |
| `category_id` | `int` | Optional device category | `None` |
| `related_booking_id` | `int` | Optional booking ID | `None` |
| `related_device_id` | `int` | Optional device ID | `None` |

**Returns:** `Dict` with `success`, `notification_id`/`error`

**Example:**
```python
result = notification_manager.create_notification(
    notification_type='low_stock',
    title="LOW STOCK: Laptops",
    message="Only 3 laptops available for Feb 1. Threshold: 5",
    recipients=['it_boss', 'room_boss'],
    category_id=1
)

if result['success']:
    print(f"Notification created: ID {result['notification_id']}")
```

---

#### `check_low_stock(category, available_count, threshold=5) -> Optional[Dict]`
Check if stock is low and create notification if needed.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `category` | `str` | Device category | Required |
| `available_count` | `int` | Number available | Required |
| `threshold` | `int` | Minimum threshold | 5 |

**Returns:** `Dict` with notification details if created, `None` otherwise

**Example:**
```python
result = notification_manager.check_low_stock('Laptop', 3, threshold=5)
if result:
    print(f"Low stock notification created: {result['notification_id']}")
```

---

#### `notify_conflict_no_alternatives(device_serial, category, booking1_id, booking2_id) -> Dict`
Notify when device conflict has no alternatives.

**Example:**
```python
result = notification_manager.notify_conflict_no_alternatives(
    device_serial='ABC123',
    category='Laptop',
    booking1_id=100,
    booking2_id=101
)
```

---

#### `notify_offsite_conflict(device_serial, booking_id, client_name) -> Dict`
Notify IT Boss about off-site rental conflict.

**Example:**
```python
result = notification_manager.notify_offsite_conflict(
    device_serial='ABC123',
    booking_id=100,
    client_name="ABC Corp"
)
```

---

#### `check_overdue_returns() -> List[Dict]`
Check for overdue off-site rentals and create notifications.

**Returns:** `List[Dict]` - List of created notifications

**Example:**
```python
notifications = notification_manager.check_overdue_returns()
for notif in notifications:
    if notif['success']:
        print(f"Created overdue notification: {notif['notification_id']}")
```

---

### Reading Notifications

#### `get_notifications_for_user(user_role, unread_only=False, notification_type=None, limit=100) -> pd.DataFrame`
Get notifications for a specific user role.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `user_role` | `str` | User role ('it_boss', 'room_boss', 'admin') | Required |
| `unread_only` | `bool` | Only unread notifications | `False` |
| `notification_type` | `str` | Filter by type | `None` |
| `limit` | `int` | Max results | 100 |

**Returns:** `pd.DataFrame` with notification data

**Example:**
```python
# All notifications for IT Boss
all_notifs = notification_manager.get_notifications_for_user('it_boss')

# Unread only
unread = notification_manager.get_notifications_for_user(
    'it_boss',
    unread_only=True
)

# Low stock only
low_stock = notification_manager.get_notifications_for_user(
    'it_boss',
    notification_type='low_stock'
)
```

---

#### `get_unread_count(user_role) -> int`
Get count of unread notifications.

**Example:**
```python
unread_count = notification_manager.get_unread_count('it_boss')
print(f"Unread notifications: {unread_count}")
```

---

#### `get_daily_summary(user_role) -> Dict`
Get daily summary of notifications.

**Returns:** `Dict` with `total_24h`, `unread_24h`, `by_type`

**Example:**
```python
summary = notification_manager.get_daily_summary('it_boss')
print(f"Total (24h): {summary['total_24h']}")
print(f"Unread (24h): {summary['unread_24h']}")
for notif_type, counts in summary['by_type'].items():
    print(f"  {notif_type}: {counts['total']} total, {counts['unread']} unread")
```

---

### Managing Notifications

#### `mark_as_read(notification_id) -> Dict`
Mark specific notification as read.

**Example:**
```python
result = notification_manager.mark_as_read(123)
if result['success']:
    print(result['message'])
```

---

#### `mark_all_as_read(user_role) -> Dict`
Mark all notifications as read for a user.

**Returns:** `Dict` with `success`, `message`, `count`

**Example:**
```python
result = notification_manager.mark_all_as_read('it_boss')
if result['success']:
    print(f"Marked {result['count']} notifications as read")
```

---

## BookingService

**Location:** `src/models/booking_service.py`

Enhanced Booking Creation for Phase 3. Handles all 13 new fields including attendees, catering, supplies, and devices.

### Constructor

#### `BookingService()`
Initialize BookingService with database connection.

**Example:**
```python
from src.models import BookingService

booking_service = BookingService()
```

---

### Creating Bookings

#### `create_enhanced_booking(room_id, start_date, end_date, client_name, client_contact_person, client_email, client_phone, num_learners=0, num_facilitators=0, coffee_tea_station=False, morning_catering=None, lunch_catering=None, catering_notes=None, stationery_needed=False, water_bottles=0, devices_needed=0, device_type_preference=None, room_boss_notes=None, status='Pending') -> Dict`
Create an enhanced booking with all Phase 3 fields.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `room_id` | `int` | Room identifier | Required |
| `start_date` | `date` | Start date | Required |
| `end_date` | `date` | End date | Required |
| `client_name` | `str` | Client/Company name | Required |
| `client_contact_person` | `str` | Contact person | Required |
| `client_email` | `str` | Email | Required |
| `client_phone` | `str` | Phone | Required |
| `num_learners` | `int` | Number of learners | 0 |
| `num_facilitators` | `int` | Number of facilitators | 0 |
| `coffee_tea_station` | `bool` | Coffee/tea needed | `False` |
| `morning_catering` | `str` | Morning catering type | `None` |
| `lunch_catering` | `str` | Lunch catering type | `None` |
| `catering_notes` | `str` | Catering notes | `None` |
| `stationery_needed` | `bool` | Stationery needed | `False` |
| `water_bottles` | `int` | Water bottles count | 0 |
| `devices_needed` | `int` | Devices needed | 0 |
| `device_type_preference` | `str` | 'laptops', 'desktops', or None | `None` |
| `room_boss_notes` | `str` | Notes for room boss | `None` |
| `status` | `str` | Booking status | 'Pending' |

**Returns:** `Dict` with `success`, `booking_id`, `message`

**Example:**
```python
from datetime import date

result = booking_service.create_enhanced_booking(
    room_id=1,
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17),
    client_name="ABC Corp",
    client_contact_person="John Doe",
    client_email="john@example.com",
    client_phone="+27 123 456 7890",
    num_learners=10,
    num_facilitators=2,
    coffee_tea_station=True,
    morning_catering='sandwiches',
    lunch_catering='in_house',
    stationery_needed=True,
    water_bottles=24,
    devices_needed=10,
    device_type_preference='laptops',
    status='Pending'
)

if result['success']:
    print(f"Created booking #{result['booking_id']}")
else:
    print(f"Failed: {result['message']}")
```

---

#### `create_device_only_booking(client_name, client_contact_person, client_email, client_phone, start_date, end_date, device_requests, rental_no, offsite_contact, offsite_phone, offsite_email, offsite_company, offsite_address, return_expected_date, notes=None, created_by=None) -> Dict`
Create a device-only booking (off-site rental without room).

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `client_name` | `str` | Client name |
| `client_contact_person` | `str` | Contact person |
| `client_email` | `str` | Email |
| `client_phone` | `str` | Phone |
| `start_date` | `date` | Rental start |
| `end_date` | `date` | Rental end |
| `device_requests` | `list` | List of `{category_id, category_name, quantity}` |
| `rental_no` | `str` | Rental document number |
| `offsite_contact` | `str` | On-site contact |
| `offsite_phone` | `str` | Contact phone |
| `offsite_email` | `str` | Contact email |
| `offsite_company` | `str` | Company name |
| `offsite_address` | `str` | Delivery address |
| `return_expected_date` | `date` | Expected return |
| `notes` | `str` | Additional notes |
| `created_by` | `str` | Username who created |

**Returns:** `Dict` with `success`, `booking_id`, `message`

**Example:**
```python
device_requests = [
    {'category_id': 1, 'category_name': 'Laptop', 'quantity': 5},
    {'category_id': 2, 'category_name': 'Desktop', 'quantity': 3}
]

result = booking_service.create_device_only_booking(
    client_name="XYZ Corp",
    client_contact_person="Jane Smith",
    client_email="jane@example.com",
    client_phone="+27 987 654 3210",
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 20),
    device_requests=device_requests,
    rental_no="REN-2024-001",
    offsite_contact="Jane Smith",
    offsite_phone="+27 987 654 3210",
    offsite_email="jane@example.com",
    offsite_company="XYZ Corp",
    offsite_address="456 Business Park, Sandton",
    return_expected_date=date(2024, 1, 21),
    created_by="admin"
)
```

---

### Retrieving Bookings

#### `get_booking_details(booking_id) -> Dict`
Retrieve full booking details including all Phase 3 fields.

**Returns:** `Dict` with `success`, `booking` (dict with all fields) / `message`

**Example:**
```python
result = booking_service.get_booking_details(123)
if result['success']:
    booking = result['booking']
    print(f"Client: {booking['client_name']}")
    print(f"Room: {booking['room_name']}")
    print(f"Learners: {booking['num_learners']}")
    print(f"Devices: {booking['devices_needed']}")
```

---

## AvailabilityService

**Location:** `src/models/availability_service.py`

Room and device availability checking for Phase 3. Handles capacity validation and conflict detection.

### Constructor

#### `AvailabilityService()`
Initialize AvailabilityService with database connection.

**Example:**
```python
from src.models import AvailabilityService

availability_service = AvailabilityService()
```

---

### Room Availability

#### `get_available_rooms(start_date, end_date, min_capacity=None) -> pd.DataFrame`
Get list of rooms available for the specified date range.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `start_date` | `date` | Start date | Required |
| `end_date` | `date` | End date | Required |
| `min_capacity` | `int` | Minimum capacity | `None` |

**Returns:** `pd.DataFrame` with `id`, `name`, `capacity`, `room_type`, `has_devices`, `conflicting_bookings`

**Example:**
```python
from datetime import date

available = availability_service.get_available_rooms(
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17),
    min_capacity=20
)

print(f"Found {len(available)} rooms")
for _, room in available.iterrows():
    print(f"  - {room['name']} (Capacity: {room['capacity']})")
```

---

#### `get_all_rooms() -> pd.DataFrame`
Get all rooms regardless of availability (for admin room selection).

**Returns:** `pd.DataFrame` with `id`, `name`, `capacity`, `is_active`, `parent_room_id`

**Example:**
```python
all_rooms = availability_service.get_all_rooms()
room_options = all_rooms['name'].tolist()
```

---

#### `check_room_conflicts(room_id, start_date, end_date, exclude_booking_id=None) -> Dict`
Check if room has conflicting bookings.

**Returns:** `Dict` with:
- `has_conflict` (bool)
- `conflicts` (list of dicts with booking details)
- `message` (str)

**Example:**
```python
check = availability_service.check_room_conflicts(
    room_id=1,
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17)
)

if check['has_conflict']:
    print(f"⚠️ {check['message']}")
    for conflict in check['conflicts']:
        print(f"  - {conflict['client_name']}: {conflict['start_date']} to {conflict['end_date']}")
else:
    print(f"✅ {check['message']}")
```

---

#### `validate_booking_capacity(room_id, total_attendees) -> Dict`
Validate if room can accommodate the requested number of attendees.

**Returns:** `Dict` with:
- `valid` (bool)
- `warning` (bool)
- `message` (str)

**Example:**
```python
validation = availability_service.validate_booking_capacity(
    room_id=1,
    total_attendees=25
)

if not validation['valid']:
    print(f"❌ {validation['message']}")
elif validation['warning']:
    print(f"⚠️ {validation['message']}")
else:
    print(f"✅ {validation['message']}")
```

---

### Device Availability

#### `check_device_availability(devices_needed, start_date, end_date, device_type='any') -> Dict`
Check if requested number of devices are available.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `devices_needed` | `int` | Number needed | Required |
| `start_date` | `date` | Start date | Required |
| `end_date` | `date` | End date | Required |
| `device_type` | `str` | 'laptops', 'desktops', or 'any' | 'any' |

**Returns:** `Dict` with `available`, `available_count`, `message`

**Example:**
```python
check = availability_service.check_device_availability(
    devices_needed=10,
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17),
    device_type='laptops'
)

if check['available']:
    print(f"✅ {check['message']}")
else:
    print(f"❌ {check['message']}")
```

---

#### `get_device_categories() -> pd.DataFrame`
Get all device categories.

**Returns:** `pd.DataFrame` with `id`, `name`

**Example:**
```python
categories = availability_service.get_device_categories()
for _, cat in categories.iterrows():
    print(f"Category {cat['id']}: {cat['name']}")
```

---

#### `get_available_device_count(category_id, start_date, end_date) -> int`
Get count of available devices for a specific category.

**Example:**
```python
count = availability_service.get_available_device_count(
    category_id=1,  # Laptops
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17)
)
print(f"Available laptops: {count}")
```

---

## RoomApprovalService

**Location:** `src/models/room_approval_service.py`

Ghost Inventory Room Assignment for Room Boss. Handles pending bookings requiring room assignment with conflict detection.

### Constructor

#### `RoomApprovalService()`
Initialize RoomApprovalService with database connection.

**Example:**
```python
from src.models import RoomApprovalService

room_service = RoomApprovalService()
```

---

### Pending Bookings

#### `get_pending_bookings(limit=50) -> pd.DataFrame`
Get all bookings pending room assignment.

**Returns:** `pd.DataFrame` with columns:
- `booking_id`, `client_name`, `client_contact_person`, `client_email`, `client_phone`
- `num_learners`, `num_facilitators`, `total_headcount`
- `start_date`, `end_date`, `requested_room_id`, `requested_room_name`
- `morning_catering`, `lunch_catering`, `devices_needed`, `status`, `room_boss_notes`, `created_at`, `created_by`

**Example:**
```python
pending = room_service.get_pending_bookings()
print(f"{len(pending)} bookings pending room assignment")

for _, booking in pending.iterrows():
    print(f"#{booking['booking_id']}: {booking['client_name']} ({booking['start_date']} to {booking['end_date']})")
```

---

### Room Occupancy

#### `get_room_occupancy(start_date, end_date, exclude_booking_id=None) -> pd.DataFrame`
Get room occupancy for date range.

**Returns:** `pd.DataFrame` with:
- `room_id`, `room_name`, `capacity`, `booking_id`, `client_name`
- `booking_start`, `booking_end`, `status`, `headcount`

**Example:**
```python
occupancy = room_service.get_room_occupancy(
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17)
)

# Show occupied rooms
occupied = occupancy[occupancy['booking_id'].notna()]
for _, occ in occupied.iterrows():
    print(f"{occ['room_name']}: {occ['client_name']} ({occ['headcount']} people)")
```

---

### Conflict Checking

#### `check_room_conflicts(room_id, start_date, end_date, exclude_booking_id=None) -> Dict`
Check if room has conflicting bookings.

**Returns:** `Dict` with:
- `has_conflict` (bool)
- `conflicts` (list of dicts)
- `message` (str)
- `can_override` (bool)

**Example:**
```python
check = room_service.check_room_conflicts(
    room_id=1,
    start_date=date(2024, 1, 15),
    end_date=date(2024, 1, 17),
    exclude_booking_id=100  # Current booking
)

if check['has_conflict']:
    print(f"⚠️ {check['message']}")
    for conflict in check['conflicts']:
        print(f"  - {conflict['client_name']}: {conflict['booking_start']} to {conflict['booking_end']}")
else:
    print(f"✅ {check['message']}")
```

---

### Room Assignment

#### `assign_room(booking_id, room_id, room_boss_id, notes=None, override_conflict=False) -> Dict`
Assign room to pending booking.

**Parameters:**
| Name | Type | Description | Default |
|------|------|-------------|---------|
| `booking_id` | `int` | Booking to update | Required |
| `room_id` | `int` | Room to assign | Required |
| `room_boss_id` | `str` | Username of room boss | Required |
| `notes` | `str` | Assignment notes | `None` |
| `override_conflict` | `bool` | Proceed despite conflicts | `False` |

**Returns:** `Dict` with `success`, `message`/`error`, `room_name`, `override_used`

**Example:**
```python
result = room_service.assign_room(
    booking_id=100,
    room_id=1,
    room_boss_id="room_boss_01",
    notes="Assigned based on capacity requirements",
    override_conflict=False
)

if result['success']:
    print(f"✅ Room {result['room_name']} assigned successfully")
    if result['override_used']:
        print("⚠️ Conflict override was used")
else:
    print(f"❌ Failed: {result['error']}")
    if 'conflicts' in result:
        for conflict in result['conflicts']:
            print(f"  - {conflict['client_name']}")
```

---

#### `reject_booking(booking_id, room_boss_id, reason) -> Dict`
Reject a pending booking with reason.

**Example:**
```python
result = room_service.reject_booking(
    booking_id=100,
    room_boss_id="room_boss_01",
    reason="Room unavailable for requested dates"
)

if result['success']:
    print(f"✅ {result['message']}")
else:
    print(f"❌ Failed: {result['error']}")
```

---

### Room List

#### `get_room_list() -> pd.DataFrame`
Get list of all available rooms for selection.

**Returns:** `pd.DataFrame` with `id`, `name`, `capacity`, `room_type`, `has_devices`

**Example:**
```python
rooms = room_service.get_room_list()
for _, room in rooms.iterrows():
    print(f"{room['name']}: Capacity {room['capacity']}, Has devices: {room['has_devices']}")
```

---

## PricingService

**Location:** `src/models/pricing_service.py`

Dynamic pricing management for rooms, devices, and catering. Only accessible by admin and it_admin roles.

### Constructor

#### `PricingService()`
Initialize PricingService.

**Example:**
```python
from src.models import PricingService

pricing_service = PricingService()
```

---

### Room Pricing

#### `get_room_pricing() -> pd.DataFrame`
Get all room pricing.

**Returns:** `pd.DataFrame` with:
- `id`, `item_name`, `category`, `daily_rate`, `weekly_rate`, `monthly_rate`
- `pricing_tier`, `notes`, `max_capacity`

**Example:**
```python
room_prices = pricing_service.get_room_pricing()
for _, room in room_prices.iterrows():
    print(f"{room['item_name']}: R{room['daily_rate']}/day, R{room['weekly_rate']}/week")
```

---

#### `get_rooms_without_pricing() -> pd.DataFrame`
Get rooms that don't have pricing set up yet.

**Returns:** `pd.DataFrame` with `id`, `name`, `max_capacity`

**Example:**
```python
unpriced = pricing_service.get_rooms_without_pricing()
if unpriced.empty:
    print("All rooms have pricing set up")
else:
    print(f"{len(unpriced)} rooms need pricing")
```

---

#### `create_room_pricing(room_id, daily_rate, weekly_rate=None, monthly_rate=None, pricing_tier='standard', notes=None) -> Dict`
Create pricing for a room.

**Example:**
```python
result = pricing_service.create_room_pricing(
    room_id=1,
    daily_rate=500.00,
    weekly_rate=2500.00,
    monthly_rate=8000.00,
    pricing_tier='premium',
    notes="Premium room with projector"
)

if result['success']:
    print(f"Pricing created: ID {result['pricing_id']}")
```

---

### Device Pricing

#### `get_device_pricing() -> pd.DataFrame`
Get collective device pricing by category.

**Returns:** `pd.DataFrame` with:
- `id`, `item_name`, `category`, `daily_rate`, `weekly_rate`, `monthly_rate`
- `pricing_tier`, `notes`, `device_count`

**Example:**
```python
device_prices = pricing_service.get_device_pricing()
for _, device in device_prices.iterrows():
    print(f"{device['item_name']} ({device['device_count']} devices):")
    print(f"  Daily: R{device['daily_rate']}, Weekly: R{device['weekly_rate']}")
```

---

#### `get_device_categories_without_pricing() -> pd.DataFrame`
Get device categories without pricing.

**Example:**
```python
unpriced = pricing_service.get_device_categories_without_pricing()
print(f"{len(unpriced)} categories need pricing")
```

---

#### `create_device_category_pricing(category_id, daily_rate, weekly_rate=None, monthly_rate=None, pricing_tier='standard', notes=None) -> Dict`
Create collective pricing for a device category.

**Example:**
```python
result = pricing_service.create_device_category_pricing(
    category_id=1,  # Laptops
    daily_rate=50.00,
    weekly_rate=250.00,
    monthly_rate=800.00,
    pricing_tier='standard'
)
```

---

### Catering Pricing

#### `get_catering_pricing() -> pd.DataFrame`
Get all catering and supplies pricing.

**Returns:** `pd.DataFrame` with:
- `id`, `item_name`, `category`, `unit_price`, `unit`, `pricing_tier`, `notes`, `effective_date`

**Example:**
```python
catering = pricing_service.get_catering_pricing()
for _, item in catering.iterrows():
    print(f"{item['item_name']}: R{item['unit_price']} {item['unit']}")
```

---

#### `get_catering_items() -> pd.DataFrame`
Get available catering items.

**Example:**
```python
items = pricing_service.get_catering_items()
for _, item in items.iterrows():
    print(f"  - {item['item_name']}: R{item['unit_price']}")
```

---

#### `create_catering_pricing(item_name, unit_price, unit='per person', pricing_tier='standard', notes=None) -> Dict`
Create pricing for a catering/supplies item.

**Example:**
```python
result = pricing_service.create_catering_pricing(
    item_name="Coffee/Tea Station",
    unit_price=25.00,
    unit="per person",
    notes="Includes refills"
)
```

---

### Pricing Management

#### `update_pricing(pricing_id, daily_rate=None, weekly_rate=None, monthly_rate=None, notes=None) -> Dict`
Update pricing rates.

**Example:**
```python
result = pricing_service.update_pricing(
    pricing_id=1,
    daily_rate=550.00,  # Price increase
    weekly_rate=2750.00,
    notes="Updated for 2024 rates"
)

if result['success']:
    print("Pricing updated successfully")
```

---

#### `delete_pricing(pricing_id) -> Dict`
Soft delete pricing by setting expiry date.

**Example:**
```python
result = pricing_service.delete_pricing(1)
if result['success']:
    print("Pricing removed (soft delete)")
```

---

## Import Pattern

All services can be imported from the models package:

```python
from src.models import (
    DeviceManager,
    NotificationManager,
    BookingService,
    AvailabilityService,
    RoomApprovalService,
    PricingService
)
```

Or individually:

```python
from src.models.device_manager import DeviceManager
from src.models.notification_manager import NotificationManager
from src.models.booking_service import BookingService
from src.models.availability_service import AvailabilityService
from src.models.room_approval_service import RoomApprovalService
from src.models.pricing_service import PricingService
```

---

## Service Relationships

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  BookingService │────▶│ AvailabilityService│───▶│  PricingService │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│ RoomApprovalService│──▶│  DeviceManager   │
└─────────────────┘     └──────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│ BookingService  │◀────│ NotificationManager│
└─────────────────┘     └──────────────────┘
```

---

## Error Handling

All services return `Dict` objects with consistent structure:

**Success Pattern:**
```python
{
    'success': True,
    'data': {...},  # or specific keys like 'booking_id'
    'message': 'Operation completed successfully'
}
```

**Error Pattern:**
```python
{
    'success': False,
    'error': 'Descriptive error message'
}
```

**Always check success before accessing data:**
```python
result = service.some_method(...)

if result.get('success'):
    # Process successful result
    data = result.get('data') or result.get('booking_id')
else:
    # Handle error
    error = result.get('error', 'Unknown error')
    print(f"Operation failed: {error}")
```
