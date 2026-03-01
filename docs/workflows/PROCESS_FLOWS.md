# Colab ERP - Process Flows

**Version:** 1.0.0  
**Last Updated:** March 2026  
**System:** Colab ERP v2.2.3

---

## Table of Contents

1. [Booking Creation Process Flow](#booking-creation-process-flow)
2. [Room Assignment Process Flow](#room-assignment-process-flow)
3. [Device Assignment Process Flow](#device-assignment-process-flow)
4. [Off-Site Rental Process Flow](#off-site-rental-process-flow)
5. [Conflict Resolution Process Flow](#conflict-resolution-process-flow)
6. [Notification Process Flow](#notification-process-flow)
7. [Pricing Update Process Flow](#pricing-update-process-flow)
8. [Excel Import Process Flow](#excel-import-process-flow)

---

## Booking Creation Process Flow

### Step-by-Step Process

```
START: User clicks "New Room Booking"
│
├─► Step 1: CLIENT INFORMATION ENTRY
│   ├── Input: Client/Company Name * (text field)
│   ├── Input: Contact Person * (text field)
│   ├── Input: Email * (text field with validation)
│   └── Input: Phone Number * (text field)
│
│   Validation Rules:
│   ├─ All fields required (*)
│   ├─ Email must be valid format (contains @ and domain)
│   └─ Phone must not be empty
│
│   Error Handling:
│   ├─ Empty field → "[Field] is required"
│   ├─ Invalid email → "Please enter a valid email"
│   └─ Success → Proceed to Step 2
│
├─► Step 2: BOOKING SEGMENTS (Multi-room support)
│   ├── Display: Current segments list (if any)
│   │   └── For each segment: Date range | Room name | [Remove button]
│   │
│   ├── Action: Add New Segment
│   │   ├── Input: Start Date * (date picker, min=today)
│   │   ├── Input: End Date * (date picker, min=start_date)
│   │   ├── Input: Room * (dropdown with capacity)
│   │   │   └── Format: "Room Name (Capacity: N)"
│   │   ├── Display: Conflict check result
│   │   │   ├─ No conflicts → "✅ Room available"
│   │   │   └─ Has conflicts → "❌ CONFLICT DETECTED"
│   │   │       └─ Show: Client name, dates for each conflict
│   │   └── Input: Room Notes (optional textarea)
│   │       └── Purpose: Preferences for Room Boss
│   │
│   ├── Validation:
│   │   ├─ Start date ≤ End date
│   │   ├─ Start date ≥ Today
│   │   ├─ Room must be selected
│   │   └─ No conflicts allowed (user must select different room)
│   │
│   └── Button: [+ Add This Segment]
│       └─ On click: Add to segments list, refresh display
│
├─► Step 3: ATTENDEES
│   ├── Input: Number of Learners (number, min=0, default=0)
│   ├── Input: Number of Facilitators (number, min=0, default=0)
│   └── Display: Total Headcount (auto-calculated: learners + facilitators)
│
│   Validation:
│   └─ Total > 0 → "At least one attendee is required"
│
├─► Step 4: CATERING
│   ├── Checkbox: Coffee/Tea Station
│   ├── Dropdown: Morning Catering
│   │   └── Options: none, pastry, sandwiches
│   ├── Dropdown: Lunch Catering
│   │   └── Options: none, self_catered, in_house
│   └── Conditional: If lunch = 'in_house'
│       └── Textarea: Catering Notes
│           └── Hint: "Specific requests (if < 3 days). ≥ 3 days = auto-menu"
│
├─► Step 5: SUPPLIES
│   ├── Checkbox: Stationery (Pen & Book per person)
│   └── Number: Water Bottles per day (min=0, default=0)
│
├─► Step 6: DEVICES
│   ├── Number: Devices Needed (min=0, default=0)
│   ├── Dropdown: Device Type Preference
│   │   └── Options: any, laptops, desktops
│   └── Conditional: If devices_needed > 0
│       ├── Query: Check device availability for all segments
│       └── Display: Availability result
│           ├─ ✅ "X devices available for all segments"
│           └─ ❌ "Not enough devices for [date range]"
│
├─► Step 7: REVIEW & SUBMIT
│   ├── Display: Booking Summary
│   │   ├── Client: [client_name]
│   │   ├── Segments: [count]
│   │   │   └── For each: [dates] → [room_name]
│   │   ├── Attendees: [total] ([learners] learners + [facilitators] facilitators)
│   │   ├── Catering: [coffee], [morning], [lunch]
│   │   ├── Supplies: [stationery], [water] bottles/day
│   │   └── Devices: [count] [type]
│   │
│   └── Button: [🚀 SUBMIT BOOKING REQUEST]
│       └─ Type: Primary, Full width
│
└─► Step 8: SUBMISSION & CONFIRMATION
    ├── Validate all required fields
    ├── For each segment:
    │   └── Create booking record
    │       ├── booking_id: Auto-generated
    │       ├── room_id: [selected_room_id]
    │       ├── client_name: [client_name]
    │       ├── booking_period: tstzrange(start_date 07:30, end_date 16:30)
    │       ├── status: 'Pending' (if staff) OR 'Confirmed' (if admin + no conflicts)
    │       ├── num_learners: [count]
    │       ├── num_facilitators: [count]
    │       ├── coffee_tea_station: [boolean]
    │       ├── morning_catering: [value or NULL]
    │       ├── lunch_catering: [value or NULL]
    │       ├── catering_notes: [text or NULL]
    │       ├── stationery_needed: [boolean]
    │       ├── water_bottles: [count]
    │       ├── devices_needed: [count]
    │       ├── device_type_preference: [value or NULL]
    │       ├── client_contact_person: [contact]
    │       ├── client_email: [email]
    │       ├── client_phone: [phone]
    │       └── room_boss_notes: [notes]
    │
    ├── Create device assignment placeholders (if devices_needed > 0)
    │   └── Table: booking_device_assignments
    │       ├── booking_id: [booking_id]
    │       ├── device_id: NULL (pending assignment)
    │       ├── device_category_id: [1 for laptops, 2 for desktops]
    │       └── quantity: [devices_needed]
    │
    └── Display: Results
        ├─ Success: "✅ Successfully created N booking(s)!"
        │   └── For each: "✅ Booking #ID: dates (room) - [Status]"
        ├─ Partial: "⚠️ Created X, Failed Y"
        └─ Failure: "❌ Failed to create bookings"
            └── List errors per segment

END: Return to dashboard or create another booking
```

### Decision Points in Booking Creation

| Decision Point | Condition | True Action | False Action |
|----------------|-----------|-------------|--------------|
| Role Check | user.role in ['admin', 'training_facility_admin', 'it_rental_admin'] | Can select any room | Room selection limited or pending |
| Conflict Check | conflict_info['has_conflict'] == True | Show warning, block submission | Show "available" message |
| Device Availability | devices_needed > available_count | Show error, block | Show success message |
| Multi-Segment | len(segments) > 1 | Create multiple bookings | Create single booking |
| Status Determination | is_admin AND no_conflicts | status = 'Confirmed' | status = 'Pending' |

---

## Room Assignment Process Flow

### Step-by-Step Process

```
START: Room Boss clicks "Pending Approvals"
│
├─► Step 1: FETCH PENDING BOOKINGS
│   ├── Query: SELECT * FROM bookings WHERE status = 'Pending'
│   ├── Sort: ORDER BY booking_period ASC, created_at ASC
│   └── Display: List of pending bookings
│       └── For each: Expandable card with booking details
│
├─► Step 2: DISPLAY BOOKING DETAILS
│   ├── Header: "Booking #ID - Client Name (dates)"
│   ├── Client Information Section:
│   │   ├── Name: [client_name]
│   │   ├── Contact: [client_contact_person]
│   │   ├── Email: [client_email]
│   │   └── Phone: [client_phone]
│   ├── Requirements Section:
│   │   ├── Headcount: [total] ([learners] + [facilitators])
│   │   ├── Dates: [start] to [end]
│   │   ├── Catering: [coffee], [morning], [lunch]
│   │   └── Devices: [count needed]
│   └── Notes Section:
│       └── Room Boss Notes: [room_boss_notes from requester]
│
├─► Step 3: SHOW CURRENT ROOM OCCUPANCY
│   ├── Query: Get all bookings for date range
│   ├── Display: List of occupied rooms
│   │   └── For each conflict: "Room: Client (dates)"
│   └── Purpose: Help Room Boss understand current load
│
├─► Step 4: ROOM SELECTION
│   ├── Dropdown: "Select Room"
│   │   ├── Options: All rooms from rooms table
│   │   └── Format: "Room Name (Capacity: N)"
│   └── Auto-trigger: Conflict Check on selection
│
├─► Step 5: CONFLICT DETECTION
│   ├── Query: Check room availability
│   │   └── SELECT * FROM bookings 
│   │       WHERE room_id = [selected]
│   │       AND booking_period && tstzrange([start], [end])
│   │       AND status IN ('Room Assigned', 'Confirmed')
│   │       AND id != [current_booking_id]
│   │
│   └── Display Result:
│       ├─ NO CONFLICTS:
│       │   └── Message: "✅ No conflicts - room is clear"
│       │   └── Show: Current room occupancy for context
│       │
│       └─ HAS CONFLICTS:
│           ├── Warning: "⚠️ [N] conflicting booking(s) found"
│           ├── List:
│           │   └── For each: "• [Client]: [start] to [end]"
│           └── Action:
│               └── Checkbox: "⚠️ Override conflict and assign anyway"
│                   └── Visible only when conflicts exist
│
├─► Step 6: ASSIGNMENT NOTES (Optional)
│   └── Textarea: "Assignment Notes"
│       └── Purpose: Document reason for assignment or override
│
└─► Step 7: EXECUTE ASSIGNMENT OR REJECTION
    │
    ├── Path A: ASSIGN ROOM
    │   ├── Button: "✅ Assign Room"
    │   ├── Validate:
    │   │   ├── Room selected
    │   │   ├── If conflicts: Override checkbox checked
    │   │   └── If capacity warning: User acknowledged
    │   │
    │   ├── Database Update:
    │   │   └── UPDATE bookings
    │   │       SET room_id = [selected_room_id],
    │   │           status = 'Room Assigned',
    │   │           room_boss_notes = [notes],
    │   │           updated_at = NOW()
    │   │       WHERE id = [booking_id]
    │   │
    │   ├── Audit Log:
    │   │   └── Log: room_assignment, user, timestamp, override_flag
    │   │
    │   └── Display:
    │       └── Success: "✅ Room [name] assigned successfully"
    │
    └── Path B: REJECT BOOKING
        ├── Button: "❌ Reject Booking"
        ├── Input: "Rejection Reason" (required)
        ├── Database Update:
        │   └── UPDATE bookings
        │       SET status = 'Rejected',
        │           room_boss_notes = 'REJECTED: [reason]',
        │           updated_at = NOW()
        │       WHERE id = [booking_id]
        │
        └── Display:
            └── Success: "Booking rejected"

END: Return to Pending Approvals list (auto-refresh)
```

### Room Assignment Decision Tree

```
                    START: Room Boss reviews booking
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Check Room Availability│
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        [Available]     [Conflict]        [Capacity Issue]
              │                │                │
              ▼                ▼                ▼
        ┌─────────┐    ┌─────────────┐   ┌─────────────┐
        │ Proceed │    │ Check if    │   │ Show warning  │
        │ to      │    │ override    │   │ "Over capacity│
        │ Assign  │    │ requested?  │   │ by N people"  │
        └────┬────┘    └───────┬─────┘   └───────┬─────┘
             │                 │                 │
             │            ┌────┴────┐          │
             │            ▼         ▼          │
             │        [Yes]      [No]         │
             │          │         │           │
             │          ▼         ▼           │
             │    ┌─────────┐  ┌────────┐      │
             │    │ Log     │  │ Require│      │
             │    │ override│  │ user to│      │
             │    │ reason  │  │ select │      │
             │    │ and     │  │ different│     │
             │    │ assign  │  │ room   │      │
             │    └────┬────┘  └────────┘      │
             │         │                       │
             └─────────┴───────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ User confirms│
                    │ assignment  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Update DB:  │
                    │ status =    │
                    │ 'Room       │
                    │ Assigned'   │
                    └─────────────┘
```

---

## Device Assignment Process Flow

### Step-by-Step Process

```
START: IT Staff clicks "Device Assignment Queue"
│
├─► Step 1: SELECT VIEW TAB
│   ├── Tab: "Pending" (default)
│   ├── Tab: "Off-site Requests"
│   ├── Tab: "Conflicts"
│   └── Tab: "All"
│
├─► Step 2: FETCH RELEVANT REQUESTS (Pending tab example)
│   └── Query:
│       └── SELECT b.id, b.client_name, b.learners_count,
│                  r.name as room_name, b.start_date, b.end_date,
│                  dc.name as device_category, bda.quantity
│          FROM bookings b
│          JOIN rooms r ON b.room_id = r.id
│          JOIN booking_device_assignments bda ON b.id = bda.booking_id
│          JOIN device_categories dc ON bda.device_category_id = dc.id
│          WHERE b.status IN ('Pending', 'Confirmed')
│          AND bda.device_id IS NULL  -- KEY: No device assigned yet
│          AND b.start_date >= CURRENT_DATE
│          ORDER BY b.start_date
│
├─► Step 3: DISPLAY REQUEST LIST
│   └── For each request:
│       ├── Expander: "📋 Booking #ID - Client (Room) | dates"
│       ├── Inside Expander:
│       │   ├── Client: [name]
│       │   ├── Room: [room_name]
│       │   ├── Dates: [start] to [end]
│       │   ├── Learners: [count]
│       │   └── Device Request: [quantity] x [category]
│       │
│       └── Step 4: CHECK DEVICE AVAILABILITY
│           ├── Query:
│           │   └── SELECT d.id, d.serial_number, d.name, d.status
│           │       FROM devices d
│           │       JOIN device_categories dc ON d.category_id = dc.id
│           │       WHERE dc.name = [category]
│           │       AND d.status IN ('available', 'rented')
│           │       AND d.id NOT IN (
│           │           -- Exclude devices already assigned for these dates
│           │           SELECT bda.device_id
│           │           FROM booking_device_assignments bda
│           │           JOIN bookings b ON bda.booking_id = b.id
│           │           WHERE bda.device_id IS NOT NULL
│           │           AND b.status NOT IN ('cancelled', 'completed')
│           │           AND b.booking_period && tstzrange([start], [end])
│           │       )
│           │
│           └── Display Result:
│               ├─ NO DEVICES:
│               │   └── Error: "⚠️ No [category]s available!"
│               │   └── Button: "Notify Bosses - No Stock"
│               │       └── Action: Create notification for IT Boss & Room Boss
│               │
│               └─ DEVICES AVAILABLE:
│                   └── Message: "✅ [N] [category]s available"
│
├─► Step 5: DEVICE SELECTION
│   ├── Multi-select: "Select [Category]s (Serial Numbers)"
│   │   └── Options: List of available serial numbers
│   │   └── Validation: Must select exactly [quantity] devices
│   │
│   └── Error if insufficient selected:
│       └── "Please select [quantity] devices"
│
├─► Step 6: ASSIGNMENT TYPE SELECTION
│   ├── Checkbox: "Off-site Rental"
│   │   └── Default: unchecked (on-site)
│   │
│   ├── IF unchecked (On-site):
│   │   └── Simple assignment, no additional fields
│   │
│   └── IF checked (Off-site):
│       └── Show Form:
│           ├── Input: Rental No/PO * (text)
│           ├── Input: Rental Date * (date, default=start_date)
│           ├── Input: Contact Person * (text)
│           ├── Input: Contact Number * (text)
│           ├── Input: Contact Email (text, optional)
│           ├── Input: Company * (text)
│           ├── Input: Address * (textarea)
│           └── Input: Expected Return Date * (date, default=end_date)
│
├─► Step 7: VALIDATION
│   └── Required Fields Check:
│       ├─ Devices selected: count == quantity
│       ├─ If off-site:
│       │   ├─ rental_no: not empty
│       │   ├─ contact_person: not empty
│       │   ├─ contact_number: not empty
│       │   ├─ company: not empty
│       │   ├─ address: not empty
│       │   └─ return_expected_date: not null
│       │
│       └── Error Display:
│           └── List all missing required fields
│
└─► Step 8: EXECUTE ASSIGNMENT
    │
    ├── For each selected device:
    │   │
    │   ├── A. Create Assignment Record
    │   │   └── INSERT INTO booking_device_assignments
    │   │       (booking_id, device_id, device_category_id, assigned_by,
    │   │        is_offsite, notes, assignment_type, quantity)
    │   │       VALUES
    │   │       ([booking_id], [device_id], [category_id],
    │   │        (SELECT user_id FROM users WHERE username = [it_staff]),
    │   │        [is_offsite], [notes], 'manual', 1)
    │   │
    │   ├── B. Update Device Status (if off-site)
    │   │   └── UPDATE devices
    │   │       SET status = 'offsite'
    │   │       WHERE id = [device_id]
    │   │
    │   └── C. If Off-Site, Create Rental Record
    │       └── INSERT INTO offsite_rentals
    │           (booking_device_assignment_id, rental_no, rental_date,
    │            contact_person, contact_number, contact_email,
    │            company, address, return_expected_date)
    │           VALUES
    │           ([assignment_id], [rental_no], [rental_date], ...)
    │
    ├── D. Log Activity
    │   └── Log: device_assigned, device_id, booking_id, user, timestamp
    │
    └── Display Result:
        ├─ Success: "✅ Assigned [N] devices"
        │   └── If off-site: "with off-site details"
        └─ Failure: "❌ [Error message]"

END: Refresh page, show updated queue
```

### Device Conflict Resolution Process

```
START: IT Staff clicks "Conflicts" tab
│
├─► Step 1: DETECT CONFLICTS
│   └── Query:
│       └── SELECT 
│               d.id as device_id,
│               d.serial_number,
│               b1.id as booking1_id,
│               b2.id as booking2_id,
│               b1.booking_period && b2.booking_period as overlaps
│           FROM devices d
│           JOIN booking_device_assignments bda1 ON d.id = bda1.device_id
│           JOIN bookings b1 ON bda1.booking_id = b1.id
│           JOIN booking_device_assignments bda2 ON d.id = bda2.device_id
│           JOIN bookings b2 ON bda2.booking_id = b2.id
│           WHERE b1.id < b2.id
│           AND b1.status = 'confirmed'
│           AND b2.status = 'confirmed'
│           AND b1.booking_period && b2.booking_period
│
├─► Step 2: DISPLAY CONFLICTS
│   └── For each conflict:
│       ├── Expander: "⚠️ [Serial Number] ([Category]) - Conflict Detected"
│       ├── Content:
│       │   ├── Booking 1: [Client 1] | [Dates 1]
│       │   └── Booking 2: [Client 2] | [Dates 2]
│       │
│       └── Step 3: SHOW REALLOCATION OPTIONS
│           ├── Query: Get alternative devices
│           │   └── SELECT * FROM devices
│           │       WHERE category_id = [category_id]
│           │       AND status = 'available'
│           │       AND id != [conflict_device_id]
│           │       AND id NOT IN (assigned for these dates)
│           │
│           └── Display:
│               ├─ NO ALTERNATIVES:
│               │   └── Error: "❌ No alternative devices available"
│               │   └── Button: "Notify IT Boss - No Alternatives"
│               │       └── Creates notification
│               │
│               └─ ALTERNATIVES AVAILABLE:
│                   └── Message: "✅ [N] alternative devices available"
│                   └── Dropdown: "Select alternative device"
│                       └── Options: Alternative serial numbers
│
└─► Step 4: EXECUTE REALLOCATION
    ├── Button: "Reallocate to Alternative"
    ├── Actions:
    │   ├── 1. Unassign from conflicting booking
    │   │   └── DELETE FROM booking_device_assignments
    │   │       WHERE device_id = [device_id]
    │   │       AND booking_id = [booking2_id]
    │   │
    │   └── 2. Assign alternative device
    │       └── INSERT INTO booking_device_assignments
    │           (booking_id, device_id, device_category_id, assigned_by, ...)
    │           VALUES ([booking2_id], [alt_device_id], ...)
    │
    ├── Log: device_reallocated, from_device, to_device, user, reason
    │
    └── Display: "✅ Reallocated to [serial_number]"

END: Refresh conflicts list
```

---

## Off-Site Rental Process Flow

### Step-by-Step Process

```
START: Device-only rental request
│
├─► Step 1: CLIENT INFORMATION (Same as regular booking)
│   ├── Client Name *
│   ├── Contact Person *
│   ├── Email *
│   └── Phone *
│
├─► Step 2: RENTAL PERIOD
│   ├── Start Date * (min=today)
│   └── End Date * (min=start_date)
│
├─► Step 3: DEVICE REQUIREMENTS
│   ├── For each device category:
│   │   ├── Number: "[Category] Quantity" (min=0)
│   │   └── Display: Availability check result
│   │       ├── Available: "✅ [N] available"
│   │       └── Not enough: "❌ Only [N] available"
│   │
│   └── Device Requests List:
│       └── Accumulate all categories with quantity > 0
│
├─► Step 4: OFF-SITE DETAILS (Required for device-only)
│   ├── Input: Rental Number/PO *
│   ├── Input: On-site Contact Person *
│   ├── Input: Contact Number *
│   ├── Input: Contact Email
│   ├── Input: Company Name *
│   ├── Input: Delivery Address *
│   └── Input: Expected Return Date * (default=end_date)
│
├─► Step 5: NOTES
│   └── Textarea: Additional Notes
│
└─► Step 6: SUBMIT
    ├── Validation:
    │   ├── All required fields present
    │   ├── At least one device requested
    │   └── All off-site details complete
    │
    ├── Create Booking:
    │   └── INSERT INTO bookings
    │       (room_id=1 [placeholder], booking_period, client_name='Pending',
    │        devices_needed=[total], device_type_preference='any',
    │        room_boss_notes='OFF-SITE RENTAL | ...details...')
    │
    └── Display:
        └── "✅ Device booking #ID created"

END: Booking goes to Device Assignment Queue
```

---

## Notification Process Flow

### Step-by-Step Process

```
START: Event triggers notification
│
├─► NOTIFICATION TRIGGERS:
│   ├── Trigger 1: Low Stock Check (Scheduled/Daily)
│   │   ├── Query: Check device availability vs threshold
│   │   └── If available < threshold:
│   │       └── Create notification
│   │
│   ├── Trigger 2: Conflict Detection (Real-time)
│   │   └── When device conflict detected AND no alternatives:
│   │       └── Create notification
│   │
│   ├── Trigger 3: Overdue Returns (Scheduled/Daily)
│   │   ├── Query: Find rentals where return_expected_date < today
│   │   └── For each overdue:
│   │       └── Create notification
│   │
│   └── Trigger 4: Booking Created (Real-time)
│       └── When new booking with status='Pending':
│           └── Create notification for Room Boss
│
├─► CREATE NOTIFICATION:
│   └── INSERT INTO notification_log
│       (notification_type, message, recipients, ...)
│       VALUES
│       ('[type]', '[title]: [message]', ARRAY['it_boss', 'room_boss'])
│
├─► DISPLAY TO USERS:
│   ├── User opens "Notifications" page
│   ├── Query:
│   │   └── SELECT * FROM notification_log
│   │       WHERE '[user_role]' = ANY(recipients)
│   │       ORDER BY created_at DESC
│   │
│   └── Display:
│       ├── Tabs: All | Unread | Low Stock | Conflicts | Overdue
│       ├── Badge: Unread count on menu
│       └── For each notification:
│           ├── Icon based on type
│           ├── Title with timestamp
│           ├── Full message
│           └── [Mark as Read] button
│
└─► USER ACTIONS:
    ├── Mark Single as Read:
    │   └── UPDATE notification_log
    │       SET is_read = true, read_at = NOW()
    │       WHERE id = [notification_id]
    │
    ├── Mark All as Read:
    │   └── UPDATE notification_log
    │       SET is_read = true, read_at = NOW()
    │       WHERE '[user_role]' = ANY(recipients)
    │       AND is_read = false
    │
    └── View Daily Summary:
        └── Display: Total (24h), Unread (24h), By Type

END: Notifications retained forever for AI training
```

---

## Pricing Update Process Flow

### Step-by-Step Process

```
START: Admin/IT Boss clicks "Pricing Catalog"
│
├─► ROLE CHECK:
│   └── Verify: user.role in ['admin', 'training_facility_admin', 'it_rental_admin']
│       └── If unauthorized: Show "⛔ Access Denied"
│
├─► DISPLAY PRICING TABS:
│   ├── Tab 1: "📋 View Pricing"
│   │   ├── Filter: Category (All/room/device)
│   │   └── Display by category:
│   │       └── For each item:
│   │           ├── Name: [item_name]
│   │           ├── Rates: Daily | Weekly | Monthly
│   │           └── Tier: [pricing_tier]
│   │
│   ├── Tab 2: "✏️ Edit Pricing"
│   │   ├── Dropdown: Select item to edit
│   │   ├── Form:
│   │   │   ├── Daily Rate (R): [number]
│   │   │   ├── Weekly Rate (R): [number]
│   │   │   ├── Monthly Rate (R): [number]
│   │   │   └── Notes: [textarea]
│   │   └── Button: [💾 Save Changes]
│   │
│   └── Tab 3: "➕ Add New Pricing"
│       ├── Radio: Item Type (room/device)
│       ├── IF room:
│       │   ├── Dropdown: Select Room (from rooms without pricing)
│       │   └── Form: Daily/Weekly/Monthly rates, Tier, Notes
│       ├── IF device:
│       │   ├── Dropdown: Select Device Category
│       │   └── Form: Daily/Weekly/Monthly rates, Tier, Notes
│       └── Button: [➕ Add Pricing]
│
└─► EXECUTE PRICING UPDATE:
    ├── For Edit:
    │   └── UPDATE pricing_catalog
    │       SET daily_rate = [value],
    │           weekly_rate = [value],
    │           monthly_rate = [value],
    │           notes = [value],
    │           updated_at = NOW(),
    │           updated_by = [username]
    │       WHERE id = [pricing_id]
    │
    └── For Add:
        └── INSERT INTO pricing_catalog
            (item_type, item_id, daily_rate, weekly_rate, monthly_rate,
             pricing_tier, notes, created_by)
            VALUES
            ([type], [item_id], [daily], [weekly], [monthly],
             [tier], [notes], [username])

END: Display success message, refresh data
```

---

## Excel Import Process Flow

### Step-by-Step Process

```
START: Admin initiates Excel import
│
├─► Step 1: FILE UPLOAD
│   ├── Input: File picker
│   ├── File: "Colab 2026 Schedule.xlsx"
│   └── Validation:
│       └── File extension: .xlsx
│
├─► Step 2: PARSE STRUCTURE
│   ├── Read workbook
│   ├── Identify month sheets:
│   │   ├── "January 2026"
│   │   ├── "February 2026"
│   │   └── ... through December
│   │
│   └── Identify columns:
│       ├── Row 1-2: Headers
│       ├── Column A: Dates
│       └── Columns B+: Room names
│
├─► Step 3: PARSE ENTRIES
│   └── For each cell with data:
│       ├── Pattern Match:
│       │   ├─ "ClientName N+M" → client, learners=N, facilitators=M
│       │   ├─ "N + M laptops" → learners=N, devices=M, type=laptops
│       │   ├─ "N + M desktops" → learners=N, devices=M, type=desktops
│       │   ├─ "Siyaya" → client=Siyaya, long-term, room=Success 10
│       │   └─ "Melissa" → client=Melissa, long-term, room=Wisdom 8
│       │
│       └── Extract:
│           ├── Client name
│           ├── Headcount breakdown
│           ├── Device needs
│           └── Room ID (from column mapping)
│
├─► Step 4: ROOM MAPPING
│   └── Map Excel column names to database room IDs:
│       ├── "Excellence" → ID 1
│       ├── "Inspiration" → ID 2
│       ├── ... (24 room mappings)
│       ├── "Success 10" → ID for Success
│       └── "Wisdom 8" → ID for Wisdom
│
├─► Step 5: CREATE BOOKINGS
│   └── For each parsed entry:
│       ├── Calculate dates:
│       │   ├─ Regular entry: Single day = cell date
│       │   └─ Long-term: Date range = sheet month
│       │
│       ├── Create booking record:
│       │   └── INSERT INTO bookings
│       │       (room_id, booking_period, client_name, status='Approved',
│       │        num_learners, num_facilitators, devices_needed,
│       │        tenant_id='TECH', created_by='excel_import')
│       │
│       └── Log result:
│           ├─ Success: Add to success list
│           └─ Error: Add to error log
│
└─► Step 6: REPORT RESULTS
    ├── Display:
    │   ├── Total entries found: [N]
    │   ├── Successfully created: [N_success]
    │   ├── Errors: [N_error]
    │   └── Time elapsed: [seconds]
    │
    └── Provide download:
        └── Error log CSV (if any errors)

END: Bookings now in system, visible in calendar
```

---

## Process Summary

| Process | Primary Actor | Key Steps | Average Time |
|---------|---------------|-----------|--------------|
| Booking Creation | Staff/Client | 8 steps | 3-5 minutes |
| Room Assignment | Room Boss | 7 steps | 2-3 minutes per booking |
| Device Assignment | IT Staff | 8 steps | 2-4 minutes per booking |
| Conflict Resolution | IT Staff | 4 steps | 1-2 minutes per conflict |
| Off-Site Rental | IT Staff | 6 steps | 3-5 minutes |
| Pricing Update | Admin/IT Boss | 3 steps | 1-2 minutes per item |
| Excel Import | Admin | 6 steps | 5-10 minutes for full year |

---

## Decision Point Summary

| Process | Decision Point | Options | Default |
|---------|---------------|---------|---------|
| Booking | Room selection | Any available room | First available |
| Booking | Status determination | Pending/Confirmed | Based on role |
| Room Assignment | Conflict handling | Override/Reject/Select different | No override |
| Device Assignment | Assignment type | On-site/Off-site | On-site |
| Device Assignment | Conflict resolution | Reallocate/Notify/Wait | Notify |
| Notification | Mark read | Single/All/None | None (user choice) |
| Pricing | Action type | View/Edit/Add | View |

---

**Document Owner:** Process & Workflow Documentation Team  
**Related Documents:** 
- WORKFLOWS.md - High-level workflow descriptions
- USER_GUIDE.md - Role-specific user guides
