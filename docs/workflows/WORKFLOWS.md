# Colab ERP - Business Process Workflows

**Version:** 1.0.0  
**Last Updated:** March 2026  
**System:** Colab ERP v2.2.3

---

## Table of Contents

1. [Overview](#overview)
2. [Ghost Inventory Workflow](#ghost-inventory-workflow)
3. [Booking Creation Process](#booking-creation-process)
4. [Device Assignment Workflow](#device-assignment-workflow)
5. [User Roles and Permissions](#user-roles-and-permissions)
6. [Approval Workflows](#approval-workflows)
7. [Notification System](#notification-system)
8. [Off-Site Rental Workflow](#off-site-rental-workflow)
9. [Multi-Tenancy Workflow](#multi-tenancy-workflow)
10. [Excel Import Workflow](#excel-import-workflow)

---

## Overview

Colab ERP manages training facility operations through structured workflows. The system implements **Ghost Inventory** pattern for flexible resource allocation, enabling bookings to be created before room assignment. This document details all business processes.

### Key Workflow Principles

1. **Ghost Inventory**: Bookings can exist without room assignment (Pending status)
2. **Role-Based Actions**: Different roles perform different workflow steps
3. **Conflict Detection**: Automatic conflict checking prevents double-booking
4. **Audit Trail**: All actions logged for accountability and AI training
5. **Approval Gates**: Critical steps require Boss approval

---

## Ghost Inventory Workflow

### Purpose
Allow bookings to be created and tracked before room assignment, giving Room Boss control over resource allocation.

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GHOST INVENTORY WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

STAFF/CLIENT                    ROOM BOSS                      DATABASE
    │                               │                              │
    │ 1. Create Booking             │                              │
    │    (No room selected)         │                              │
    │───────────────────────────────>│                              │
    │                               │                              │
    │                               │ 2. Store as PENDING          │
    │                               │─────────────────────────────>│
    │                               │                              │
    │                               │ 3. Review Pending Queue      │
    │                               │<─────────────────────────────│
    │                               │                              │
    │                               │ 4. Check Room Availability   │
    │                               │    - View conflicts          │
    │                               │    - Check alternatives      │
    │                               │                              │
    │                               │ 5. Assign Room (or Reject)   │
    │                               │    - Override if needed      │
    │                               │─────────────────────────────>│
    │                               │                              │
    │ 6. Booking Confirmed          │                              │
    │<──────────────────────────────│                              │
    │    Status: CONFIRMED          │                              │
```

### Detailed Steps

#### Step 1: Booking Request Creation
**Actor:** Staff/Client User  
**Action:** Fill booking form without room selection  
**System Response:**
- Validates client information (name, contact, email, phone)
- Validates dates (start ≤ end)
- Validates headcount (learners + facilitators > 0)
- Stores booking with status = 'Pending'

#### Step 2: Pending Queue Entry
**Actor:** System  
**Action:** Store booking in database  
**Database State:**
```
Table: bookings
- room_id: [set by user or NULL]
- status: 'Pending'
- client_name: [provided]
- booking_period: tstzrange(start_date, end_date)
- num_learners: [count]
- num_facilitators: [count]
- devices_needed: [count]
- catering requirements: [flags]
```

#### Step 3: Room Boss Review
**Actor:** Room Boss (training_facility_admin)  
**Action:** Access Pending Approvals interface  
**System Shows:**
- List of all Pending bookings
- Client information
- Date ranges
- Headcount requirements
- Catering needs
- Device requirements
- Current room occupancy for the dates

#### Step 4: Conflict Detection
**Actor:** System  
**Algorithm:**
1. Query existing bookings for target date range
2. Check for room_period overlaps using PostgreSQL exclusion constraint
3. Return conflict summary

**Conflict Check Output:**
```python
{
  'has_conflict': True/False,
  'conflicts': [
    {
      'booking_id': 123,
      'client_name': 'ABC Corp',
      'start_date': '2026-03-15',
      'end_date': '2026-03-17',
      'status': 'Confirmed'
    }
  ],
  'message': 'Room has N conflicting booking(s)',
  'can_override': True
}
```

#### Step 5: Room Assignment Decision
**Actor:** Room Boss  
**Options:**

**Option A: Assign Room (No Conflicts)**
- Select room from dropdown
- System validates availability
- Status changes to 'Room Assigned'
- Notification sent to requester

**Option B: Assign Room (With Conflicts)**
- View conflict details
- Check override checkbox
- Enter override justification
- Status changes to 'Room Assigned' with override flag

**Option C: Reject Booking**
- Enter rejection reason
- Status changes to 'Rejected'
- Notification sent to requester

#### Step 6: Confirmation
**Actor:** System  
**Action:** Update booking status and notify stakeholders  
**Database Update:**
```sql
UPDATE bookings 
SET status = 'Room Assigned',
    room_id = [selected_room_id],
    room_boss_notes = [notes],
    updated_at = NOW()
WHERE id = [booking_id]
```

### Decision Points

| Decision | Condition | Action |
|----------|-----------|--------|
| Has Conflicts? | conflict_check['has_conflict'] == True | Show warning, require override |
| Override Allowed? | User has training_facility_admin role | Enable override checkbox |
| Capacity OK? | headcount ≤ room.max_capacity | Allow assignment |
| Capacity Warning? | headcount > room.max_capacity * 0.9 | Show warning but allow |

---

## Booking Creation Process

### Purpose
Create comprehensive booking records with all client requirements.

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      BOOKING CREATION PROCESS                            │
└─────────────────────────────────────────────────────────────────────────┘

SECTION 1: CLIENT INFORMATION
┌─────────────────────────────────────────────────────────────────┐
│ • Client/Company Name *                                        │
│ • Contact Person *                                             │
│ • Email *                                                      │
│ • Phone Number *                                               │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
SECTION 2: BOOKING SEGMENTS (Multi-room Support)
┌─────────────────────────────────────────────────────────────────┐
│ Segment 1:                                                     │
│   • Start Date: [date picker]                                  │
│   • End Date: [date picker]                                  │
│   • Room: [dropdown with capacity]                            │
│   • Conflict Check: [automatic]                               │
│   • Notes: [text area]                                        │
│                                                                │
│ [+ Add Another Segment]                                       │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
SECTION 3: ATTENDEES
┌─────────────────────────────────────────────────────────────────┐
│ • Number of Learners: [number input]                           │
│ • Number of Facilitators: [number input]                       │
│ • Total Headcount: [auto-calculated]                         │
│                                                                │
│ Validation: total > 0                                         │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
SECTION 4: CATERING
┌─────────────────────────────────────────────────────────────────┐
│ • Coffee/Tea Station: [checkbox]                               │
│ • Morning Catering: [none/pastry/sandwiches dropdown]          │
│ • Lunch Catering: [none/self_catered/in_house dropdown]        │
│ • Catering Notes: [text area, optional]                       │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
SECTION 5: SUPPLIES
┌─────────────────────────────────────────────────────────────────┐
│ • Stationery (Pen & Book per person): [checkbox]               │
│ • Water Bottles (per day): [number input]                      │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
SECTION 6: DEVICES
┌─────────────────────────────────────────────────────────────────┐
│ • Devices Needed: [number input]                              │
│ • Device Type: [any/laptops/desktops dropdown]                 │
│                                                                │
│ Availability Check: [automatic - queries device pool]         │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ [🚀 SUBMIT BOOKING REQUEST]                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Validation Rules

| Field | Validation | Error Message |
|-------|-----------|---------------|
| client_name | Required, not empty | "Client name is required" |
| client_contact_person | Required, not empty | "Contact person is required" |
| client_email | Required, valid email format | "Email is required" |
| client_phone | Required, not empty | "Phone is required" |
| start_date | ≤ end_date, ≥ today | "Start date cannot be after end date" |
| end_date | ≥ start_date | "End date cannot be before start date" |
| num_learners + num_facilitators | > 0 | "At least one attendee is required" |
| room_id | Required (selected by user) | "Please select a room" |
| devices_needed | ≥ 0 | "Invalid device count" |

### Status Determination

| User Role | Room Selection | Booking Status |
|-----------|---------------|----------------|
| admin/training_facility_admin | Room selected, no conflicts | 'Confirmed' |
| admin/training_facility_admin | Room selected, with conflicts | 'Pending' (requires override) |
| staff/client | Any | 'Pending' (Room Boss approval required) |
| it_rental_admin | Room selected | 'Confirmed' (IT Boss has admin rights) |

### Multi-Segment Booking

When a client needs different rooms for different dates:

```
Client: "ABC Corporation"
├── Segment 1: March 1-5, Excellence Room
├── Segment 2: March 10-12, Innovation Room  
└── Segment 3: March 15-20, Dedication Room

System Creates:
├── Booking #1001: ABC Corporation, Excellence, March 1-5
├── Booking #1002: ABC Corporation, Innovation, March 10-12
└── Booking #1003: ABC Corporation, Dedication, March 15-20
```

---

## Device Assignment Workflow

### Purpose
Manually assign specific IT devices to bookings with full tracking.

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DEVICE ASSIGNMENT WORKFLOW                           │
└─────────────────────────────────────────────────────────────────────────┘

                            IT STAFF (it_rental_admin)
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Device Assignment Queue     │
                    │         Interface             │
                    └───────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
        ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
        │    PENDING    │   │  OFF-SITE     │   │  CONFLICTS    │
        │   REQUESTS    │   │  REQUESTS     │   │               │
        └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
                │                   │                   │
                ▼                   ▼                   ▼
        ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
        │  Show bookings│   │  Show active  │   │  Show device  │
        │  with device  │   │  off-site     │   │  conflicts    │
        │  requests but │   │  rentals      │   │  with options │
        │  no assignment│   │               │   │               │
        └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
                │                   │                   │
                ▼                   │                   │
        ┌───────────────┐          │                   │
        │ Check Device  │          │                   │
        │ Availability  │          │                   │
        │ by Category   │          │                   │
        └───────┬───────┘          │                   │
                │                   │                   │
        ┌───────┴───────┐          │                   │
        │               │          │                   │
        ▼               ▼          │                   │
┌───────────────┐ ┌───────────────┐│                   │
│ DEVICES       │ │ NO DEVICES    ││                   │
│ AVAILABLE     │ │ AVAILABLE     ││                   │
│               │ │               ││                   │
│ Show list of  │ │ Show "Notify  ││                   │
│ serial numbers│ │ Bosses" btn   ││                   │
└───────┬───────┘ └───────────────┘│                   │
        │                          │                   │
        ▼                          │                   │
┌───────────────┐                  │                   │
│ IT Staff      │                  │                   │
│ selects       │                  │                   │
│ serial numbers│                  │                   │
│ (multi-select)│                  │                   │
└───────┬───────┘                  │                   │
        │                          │                   │
        ▼                          ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│              ASSIGNMENT TYPE SELECTION                │
├─────────────────────────────────────────────────────────┤
│  On-Site: [ ]  |  Off-Site: [ ]                        │
└─────────────────────────┬───────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
    ┌───────────────┐           ┌───────────────┐
    │   ON-SITE     │           │   OFF-SITE    │
    │   ASSIGNMENT  │           │   RENTAL      │
    │               │           │               │
    │ Simple assign │           │ Show form:    │
    │ to booking    │           │ • Rental No   │
    │               │           │ • Contact     │
    │ Status:       │           │ • Phone       │
    │ assigned      │           │ • Email       │
    │               │           │ • Company     │
    │               │           │ • Address     │
    │               │           │ • Return Date │
    └───────┬───────┘           └───────┬───────┘
            │                           │
            └─────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────────┐
            │  CREATE ASSIGNMENT RECORD     │
            │                               │
            │  Table: booking_device_assignments│
            │  • booking_id                 │
            │  • device_id (serial number) │
            │  • device_category_id        │
            │  • assigned_by (IT Staff)    │
            │  • is_offsite                 │
            │  • notes                      │
            └───────────────────────────────┘
```

### Device Assignment Queue States

| State | Description | Query Condition |
|-------|-------------|-----------------|
| **Pending** | Bookings with device requests but no device_id | `device_id IS NULL` |
| **Off-Site** | Active off-site rentals not yet returned | `returned_at IS NULL` |
| **Conflicts** | Devices with overlapping assignments | Manual conflict detection query |

### Conflict Detection Algorithm

```sql
-- Find devices with overlapping bookings
SELECT 
    d.id as device_id,
    d.serial_number,
    b1.id as booking1_id,
    b2.id as booking2_id,
    b1.booking_period && b2.booking_period as overlaps
FROM devices d
JOIN booking_device_assignments bda1 ON d.id = bda1.device_id
JOIN bookings b1 ON bda1.booking_id = b1.id
JOIN booking_device_assignments bda2 ON d.id = bda2.device_id
JOIN bookings b2 ON bda2.booking_id = b2.id
WHERE b1.id < b2.id  -- Avoid duplicates
AND b1.status = 'confirmed'
AND b2.status = 'confirmed'
AND b1.booking_period && b2.booking_period  -- Overlap operator
```

### Off-Site Rental Details

Required fields for off-site rental:
| Field | Required | Description |
|-------|----------|-------------|
| rental_no | Yes | Rental document/PO number |
| contact_person | Yes | On-site contact name |
| contact_number | Yes | Contact phone |
| contact_email | No | Contact email |
| company | Yes | Company name |
| address | Yes | Delivery address |
| return_expected_date | Yes | Expected return date |

---

## User Roles and Permissions

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ROLE HIERARCHY                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              ADMIN LEVEL                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐   │
│  │    admin (Full Access)      │    │  it_admin (IT Admin)        │   │
│  │                             │    │                             │   │
│  │ • All system access         │    │ • All system access         │   │
│  │ • User management           │    │ • Device management focus   │   │
│  │ • Pricing management        │    │ • Pricing management        │   │
│  └─────────────────────────────┘    └─────────────────────────────┘   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                            BOSS LEVEL                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐   │
│  │ training_facility_admin     │    │   it_rental_admin (IT Boss) │   │
│  │       (Room Boss)           │    │                             │   │
│  │                             │    │ • Device Assignment Queue   │   │
│  │ • Room Assignment           │    │ • Off-site rental tracking  │   │
│  │ • Pending Approvals         │    │ • Device conflict resolution│   │
│  │ • Pricing access            │    │ • Inventory dashboard       │   │
│  │ • Full system access        │    │ • Pricing access            │   │
│  └─────────────────────────────┘    └─────────────────────────────┘   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                           VIEWER LEVEL                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐   │
│  │ training_facility_admin_    │    │      kitchen_staff          │   │
│  │         viewer               │    │                             │   │
│  │                             │    │ • Calendar view ONLY        │   │
│  │ • Calendar (view)           │    │ • Catering indicators     │   │
│  │ • Bookings (view)           │    │ • Headcounts visible      │   │
│  │ • Pricing (view-only)       │    │ • No device/room access   │   │
│  │ • Inventory (view)          │    │                             │   │
│  │ • NO approval privileges    │    │                             │   │
│  └─────────────────────────────┘    └─────────────────────────────┘   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                           STAFF LEVEL                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐                                       │
│  │        staff (Legacy)       │                                       │
│  │                             │                                       │
│  │ • Create bookings (pending) │                                       │
│  │ • View calendar             │                                       │
│  │ • No pricing access         │                                       │
│  └─────────────────────────────┘                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Menu Access by Role

| Menu Item | admin | training_facility_admin | it_rental_admin | training_facility_admin_viewer | kitchen_staff |
|-----------|-------|------------------------|-----------------|-------------------------------|---------------|
| Dashboard | ✅ | ✅ | ✅ | ❌ | ❌ |
| Notifications | ✅ | ✅ | ✅ | ❌ | ❌ |
| Calendar | ✅ | ✅ | ✅ | ✅ | ✅ |
| Device Assignment Queue | ✅ | ✅ | ✅ | ❌ | ❌ |
| New Room Booking | ✅ | ✅ | ✅ | ✅ | ❌ |
| New Device Booking | ✅ | ✅ | ✅ | ✅ | ❌ |
| Pricing Catalog | ✅ | ✅ | ✅ | ✅ (view) | ❌ |
| Pending Approvals | ✅ | ✅ | ✅ | ❌ | ❌ |
| Inventory Dashboard | ✅ | ✅ | ✅ | ✅ | ❌ |
| Kitchen Calendar | ❌ | ❌ | ❌ | ❌ | ✅ |

### Permission Matrix

| Permission | admin | training_facility_admin | it_rental_admin | training_facility_admin_viewer | kitchen_staff |
|------------|-------|------------------------|-----------------|-------------------------------|---------------|
| Create Booking | ✅ | ✅ | ✅ | ✅ | ❌ |
| Assign Room | ✅ | ✅ | ❌ | ❌ | ❌ |
| Assign Device | ✅ | ❌ | ✅ | ❌ | ❌ |
| View Pricing | ✅ | ✅ | ✅ | ✅ | ❌ |
| Edit Pricing | ✅ | ✅ | ✅ | ❌ | ❌ |
| Approve Booking | ✅ | ✅ | ❌ | ❌ | ❌ |
| Reject Booking | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Inventory | ✅ | ✅ | ✅ | ✅ | ❌ |
| Export Data | ✅ | ✅ | ✅ | ❌ | ❌ |

---

## Approval Workflows

### Room Assignment Approval

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ROOM ASSIGNMENT APPROVAL FLOW                        │
└─────────────────────────────────────────────────────────────────────────┘

REQUESTER                      SYSTEM                     ROOM BOSS
    │                            │                           │
    │ 1. Submit Booking           │                           │
    │    (No room selected)       │                           │
    │────────────────────────────>│                           │
    │                            │                           │
    │                            │ 2. Store as PENDING       │
    │                            │    Trigger notification   │
    │                            │──────────────────────────>│
    │                            │                           │
    │                            │                           │ 3. Review Queue
    │                            │                           │
    │                            │<──────────────────────────│
    │                            │ 4. Fetch pending bookings │
    │                            │                           │
    │                            │                           │ 5. Check availability
    │                            │    ┌───────────────┐      │
    │                            │    │ Conflict?     │      │
    │                            │    └───────┬───────┘      │
    │                            │            │              │
    │                            │      ┌─────┴─────┐        │
    │                            │      ▼           ▼        │
    │                            │   [Yes]        [No]       │
    │                            │    │            │        │
    │                            │    ▼            ▼        │
    │                            │ Override?    Assign Room  │
    │                            │    │            │        │
    │                            │  ┌─┴─┐          │        │
    │                            │  ▼   ▼          │        │
    │                            │ Yes  No          │        │
    │                            │  │    │          │        │
    │                            │  ▼    ▼          ▼        │
    │                            │ Assign  Reject  Confirm   │
    │                            │  │      │        │        │
    │                            │  ▼      ▼        ▼        │
    │                            │ UPDATE STATUS             │
    │                            │                           │
    │ 6. Notification           │                           │
    │<───────────────────────────│                           │
    │    Booking:               │                           │
    │    [Confirmed/Rejected]   │                           │
```

### Decision Logic

```python
def room_assignment_decision(booking, room_boss_role, conflicts):
    """
    Decision tree for room assignment
    """
    # Check role permission
    if room_boss_role not in ['admin', 'training_facility_admin']:
        return {'allowed': False, 'reason': 'Insufficient privileges'}
    
    # Check conflicts
    if conflicts['has_conflict']:
        # Check if override is requested
        if booking.get('override_conflict'):
            # Log override for audit
            log_audit_action(
                action='room_assignment_override',
                booking_id=booking['id'],
                user=room_boss_role,
                reason=booking.get('override_reason')
            )
            return {
                'allowed': True, 
                'status': 'Room Assigned',
                'override': True
            }
        else:
            return {
                'allowed': False, 
                'reason': 'Conflicts detected. Override required.',
                'conflicts': conflicts['conflicts']
            }
    
    # No conflicts - proceed
    return {'allowed': True, 'status': 'Room Assigned', 'override': False}
```

### Override Scenarios

| Scenario | Conflict Type | Override Action | Audit Log |
|----------|--------------|-----------------|-----------|
| Same client, extended dates | Temporal overlap | Allow with notes | "Extended existing booking" |
| Different clients, adjacent rooms | Room capacity | Allow if capacity OK | "Room reassignment" |
| Emergency training | High priority | Allow with justification | "Emergency override - [reason]" |
| Existing booking cancelled | Should be free | Investigate | "Conflict with cancelled booking" |

---

## Notification System

### Notification Types

| Type | Trigger | Recipients | Action Required |
|------|---------|------------|-----------------|
| **low_stock** | Available devices < threshold | it_boss, room_boss | Procure more devices |
| **conflict_no_alternatives** | Device conflict, no alternatives | it_boss, room_boss | Manual resolution |
| **offsite_conflict** | Off-site rental issue | it_boss | Contact client |
| **return_overdue** | Return date passed | it_boss | Follow up return |
| **booking_pending** | New booking created | room_boss | Review and assign |

### Notification Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      NOTIFICATION SYSTEM FLOW                           │
└─────────────────────────────────────────────────────────────────────────┘

TRIGGER EVENTS                          NOTIFICATION MANAGER
┌─────────────────┐                           ┌───────────────┐
│ Device Stock    │                           │  create_      │
│ Check (Daily)   │──────────────────────────>│  notification │
└─────────────────┘                           │  ()           │
                                              └───────┬───────┘
┌─────────────────┐                                   │
│ Conflict        │──────────────────────────>        │
│ Detection       │                                   │
└─────────────────┘                                   │
                                                      │
┌─────────────────┐                                   │
│ Booking         │──────────────────────────>        │
│ Created         │                                   │
└─────────────────┘                                   │
                                                      ▼
                                              ┌───────────────┐
                                              │ Store in      │
                                              │ notification_ │
                                              │ log table     │
                                              └───────┬───────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │ Recipients:   │
                                              │ • it_boss     │
                                              │ • room_boss   │
                                              │ • admin       │
                                              └───────┬───────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │ Dashboard     │
                                              │ Badge Update  │
                                              │ (unread count)│
                                              └───────┬───────┘
                                                      │
                                           ┌─────────┴─────────┐
                                           │                   │
                                           ▼                   ▼
                                    ┌───────────────┐  ┌───────────────┐
                                    │ IT Boss       │  │ Room Boss     │
                                    │ Dashboard     │  │ Dashboard     │
                                    │               │  │               │
                                    │ [5] Alerts    │  │ [3] Alerts    │
                                    └───────────────┘  └───────────────┘
```

### Notification Retention

**Policy:** All notifications kept forever for AI training  
**Rationale:** Build training dataset for future AI agent  
**Storage:** PostgreSQL notification_log table  
**Archival:** No archival - full history maintained

---

## Off-Site Rental Workflow

### Purpose
Track devices rented for use outside the facility.

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      OFF-SITE RENTAL WORKFLOW                           │
└─────────────────────────────────────────────────────────────────────────┘

CLIENT/ADMIN                          IT STAFF                    LOGISTICS
    │                                   │                           │
    │ 1. Request off-site rental        │                           │
    │    via Device Booking form        │                           │
    │──────────────────────────────────>│                           │
    │                                   │                           │
    │                                   │ 2. Review request         │
    │                                   │    in Assignment Queue    │
    │                                   │                           │
    │                                   │ 3. Select devices         │
    │                                   │    (serial numbers)       │
    │                                   │                           │
    │                                   │ 4. Check "Off-site"       │
    │                                   │    checkbox               │
    │                                   │                           │
    │                                   │ 5. Fill rental details:   │
    │                                   │    • Rental No            │
    │                                   │    • Contact Person       │
    │                                   │    • Phone               │
    │                                   │    • Email               │
    │                                   │    • Company             │
    │                                   │    • Address             │
    │                                   │    • Return Date         │
    │                                   │                           │
    │                                   │ 6. Submit assignment      │
    │                                   │                           │
    │                                   │ 7. Device prepared       │
    │                                   │─────────────────────────>│
    │                                   │                           │
    │                                   │                           │ 8. Ship/
    │                                   │                           │    Deliver
    │                                   │                           │
    │                                   │<─────────────────────────│
    │                                   │ 9. Confirmation           │
    │<──────────────────────────────────│    of dispatch            │
    │                                   │                           │
    │                                   │                           │
    │                                   │              [TIME PASSES]│
    │                                   │                           │
    │                                   │                           │
    │ 10. Device returned               │                           │
    │──────────────────────────────────>│                           │
    │                                   │                           │
    │                                   │ 11. Mark as returned      │
    │                                   │     in system             │
    │                                   │                           │
    │                                   │ 12. Device status        │
    │                                   │     → 'available'         │
    │                                   │                           │
    │<──────────────────────────────────│ 13. Confirmation          │
    │     Return confirmed              │                           │
```

### Rental Tracking Fields

| Field | Table | Purpose |
|-------|-------|---------|
| rental_no | offsite_rentals | PO/Document reference |
| rental_date | offsite_rentals | Date rented |
| contact_person | offsite_rentals | On-site contact |
| contact_number | offsite_rentals | Phone |
| contact_email | offsite_rentals | Email |
| company | offsite_rentals | Client company |
| address | offsite_rentals | Delivery address |
| return_expected_date | offsite_rentals | Expected return |
| returned_at | offsite_rentals | Actual return timestamp |

### Overdue Tracking

```sql
-- Find overdue rentals
SELECT 
    or2.rental_no,
    or2.contact_person,
    or2.return_expected_date,
    CURRENT_DATE - or2.return_expected_date as days_overdue,
    b.client_name,
    d.serial_number
FROM offsite_rentals or2
JOIN booking_device_assignments bda ON or2.booking_device_assignment_id = bda.id
JOIN bookings b ON bda.booking_id = b.id
JOIN devices d ON bda.device_id = d.id
WHERE or2.returned_at IS NULL
AND or2.return_expected_date < CURRENT_DATE
ORDER BY days_overdue DESC
```

---

## Multi-Tenancy Workflow

### Purpose
Support TECH and TRAINING divisions with shared physical resources.

### Tenant Separation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       MULTI-TENANCY MODEL                               │
└─────────────────────────────────────────────────────────────────────────┘

                        SHARED PHYSICAL ASSETS
                    ┌─────────────────────────┐
                    │    24 Rooms             │
                    │    110+ Devices         │
                    │    Common Spaces        │
                    └─────────────────────────┘
                              │
           ┌──────────────────┴──────────────────┐
           │                                  │
           ▼                                  ▼
    ┌───────────────┐                  ┌───────────────┐
    │    TECH       │                  │   TRAINING    │
    │   DIVISION    │                  │   DIVISION    │
    │               │                  │               │
    │ Bookings:     │                  │ Bookings:     │
    │ • Client A    │                  │ • Client X    │
    │ • Client B    │                  │ • Client Y    │
    │ tenant_id =   │                  │ tenant_id =   │
    │   'TECH'      │                  │   'TRAINING'  │
    └───────────────┘                  └───────────────┘
           │                                  │
           │    EXCLUSION CONSTRAINT          │
           │    prevents conflicts            │
           │    across tenants               │
           └────────────┬─────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  PHYSICAL ROOM  │
              │  CANNOT BE      │
              │  DOUBLE-BOOKED  │
              │  (regardless of │
              │   tenant)       │
              └─────────────────┘
```

### Database Implementation

```sql
-- Tenant type definition
CREATE TYPE tenant_type AS ENUM ('TECH', 'TRAINING');

-- Bookings table with tenant
ALTER TABLE bookings
ADD COLUMN tenant_id tenant_type NOT NULL DEFAULT 'TECH';

-- Exclusion constraint (global - applies to all tenants)
CONSTRAINT no_overlapping_bookings 
    EXCLUDE USING gist (room_id WITH =, booking_period WITH &&)
    WHERE (room_id IS NOT NULL)
```

### Workflow Impact

| Step | Tenant Handling | Database Action |
|------|-----------------|-----------------|
| Create Booking | tenant_id = user.tenant or 'TECH' default | Insert with tenant_id |
| Check Availability | Query all bookings regardless of tenant | tstzrange overlap check |
| Calendar View | Show all bookings (color-coded by tenant) | Filter by date range |
| Dashboard Stats | Filter by tenant_id | `WHERE tenant_id = 'TECH'` |
| Excel Import | Default to 'TECH' | `DEFAULT 'TECH'` |

---

## Excel Import Workflow

### Purpose
Bulk import bookings from Excel schedule files.

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXCEL IMPORT WORKFLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

ADMIN                        EXCEL PARSER                      DATABASE
    │                              │                             │
    │ 1. Upload Excel file          │                             │
    │    "Colab 2026 Schedule"      │                             │
    │──────────────────────────────>│                             │
    │                              │                             │
    │                              │ 2. Parse structure          │
    │                              │    • Month sheets (Jan-Dec)   │
    │                              │    • Room columns            │
    │                              │    • Date rows               │
    │                              │                             │
    │                              │ 3. Parse entries            │
    │                              │    Pattern matching:         │
    │                              │    "Client 25+1"            │
    │                              │    "25 + 18 laptops"        │
    │                              │                             │
    │                              │ 4. Map rooms                │
    │                              │    Excel name → Room ID      │
    │                              │    • Excellence → ID 1       │
    │                              │    • Inspiration → ID 2      │
    │                              │    • etc.                    │
    │                              │                             │
    │                              │ 5. Handle special cases     │
    │                              │    • Siyaya → Long-term     │
    │                              │    • Melissa → Long-term    │
    │                              │                             │
    │                              │ 6. Create bookings          │
    │                              │    One per day per room     │
    │                              │────────────────────────────>│
    │                              │                             │
    │                              │                             │ 7. Insert
    │                              │                             │    records
    │                              │                             │
    │<──────────────────────────────│                             │
    │ 8. Report results             │                             │
    │    • Created: N               │                             │
    │    • Errors: M                │                             │
    │    • Log file               │                             │
```

### Pattern Matching Rules

| Pattern | Extracted Data | Example |
|---------|---------------|---------|
| "ClientName N+M" | client=ClientName, learners=N, facilitators=M | "ABC Corp 25+1" |
| "N + M laptops" | learners=N, devices=M, type=laptops | "20 + 15 laptops" |
| "N + M desktops" | learners=N, devices=M, type=desktops | "10 + 10 desktops" |
| "Siyaya" | client=Siyaya, long-term, room=Success 10 | "Siyaya" |
| "Melissa" | client=Melissa, long-term, room=Wisdom 8 | "Melissa" |

### Room Mapping Table

| Excel Name | Database Room | Room ID |
|------------|--------------|---------|
| Excellence | Excellence | 1 |
| Inspiration | Inspiration | 2 |
| Honesty | Honesty | 3 |
| Gratitude | Gratitude | 4 |
| Ambition | Ambition | 5 |
| Perseverance | Perseverance | 6 |
| Courage | Courage | 7 |
| Possibilities | Possibilities | 8 |
| Success 10 | Success | 9 |
| Wisdom 8 | Wisdom | 10 |
| (etc.) | ... | ... |

### Long-Term Rental Handling

For entries like "Siyaya" and "Melissa":
1. Identify as long-term office rental
2. Create booking for entire date range
3. Mark as auto-approved
4. Set appropriate room (Success 10 for Siyaya, Wisdom 8 for Melissa)

---

## Workflow Summary Matrix

| Workflow | Primary Actor | System Components | Key Tables |
|----------|---------------|-------------------|------------|
| Ghost Inventory | Room Boss | RoomApprovalService | bookings, rooms |
| Booking Creation | Staff/Client | BookingService, AvailabilityService | bookings |
| Device Assignment | IT Staff | DeviceManager | booking_device_assignments, devices |
| Off-Site Rental | IT Staff | DeviceManager | offsite_rentals |
| Notifications | System | NotificationManager | notification_log |
| Excel Import | Admin | Excel Import Script | bookings |
| Multi-Tenancy | All | Tenant filtering | bookings (tenant_id) |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | March 2026 | Initial documentation for v2.2.3 |

---

**Document Owner:** Process & Workflow Documentation Team  
**Related Documents:** 
- PROCESS_FLOWS.md - Step-by-step process flows
- USER_GUIDE.md - Role-specific user guides
- PRD.md - Product Requirements Document
- ARCHITECTURE.md - System Architecture
