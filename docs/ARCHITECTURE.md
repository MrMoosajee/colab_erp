# Colab ERP - System Architecture Documentation

**Version:** v2.2.3  
**Last Updated:** February 28, 2026  
**Classification:** Internal Confidential  
**Location:** `/home/shuaibadams/Projects/colab_erp/docs/`

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Module Dependencies](#module-dependencies)
4. [Component Interactions](#component-interactions)
5. [Data Flow](#data-flow)
6. [Technology Stack](#technology-stack)
7. [Database Schema](#database-schema)
8. [Configuration Points](#configuration-points)
9. [External Dependencies](#external-dependencies)
10. [Design Patterns](#design-patterns)

---

## System Overview

Colab ERP is a comprehensive Enterprise Resource Planning system built for Colab Tech Solutions, managing room bookings, device inventory, and training facility operations. The system supports multi-tenancy (TECH/TRAINING divisions) and handles 807+ bookings across 24 rooms with 110+ devices.

### Key Capabilities
- **Multi-tenancy Support**: TECH and TRAINING divisions with shared physical assets
- **Ghost Inventory Workflow**: Pending bookings without immediate room assignment
- **Device Management**: Manual IT staff assignment with off-site rental tracking
- **Dynamic Pricing**: Room, device category, and catering pricing management
- **Calendar Visualization**: Excel-style grid with indicators and headcounts
- **Role-Based Access**: 6 distinct user roles with granular permissions

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                      │
│                                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│   │   Browser   │  │   Browser   │  │   Browser   │  │      Browser        │ │
│   │   (Admin)   │  │(Room Boss)  │  │ (IT Staff)  │  │  (Kitchen Staff)    │ │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└──────────┼────────────────┼────────────────┼────────────────────┼────────────┘
           │                │                │                    │
           └────────────────┴────────────────┴────────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   Tailscale VPN     │
                        │  (100.69.57.77)     │
                        └──────────┬──────────┘
                                   │
┌──────────────────────────────────┼────────────────────────────────────────────┐
│                         APPLICATION LAYER                                  │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      Streamlit Application                          │   │
│   │                                                                     │   │
│   │  ┌────────────┐  ┌────────────┐  ┌─────────────────────────────────┐ │   │
│   │  │   app.py   │  │booking_form│  │         Service Layer         │ │   │
│   │  │  (Views)   │  │   (Forms)  │  │  ┌───────────────────────────┐ │ │   │
│   │  │            │  │            │  │  │   BookingService          │ │ │   │
│   │  │ • Login    │  │ • Multi-  │  │  │   AvailabilityService     │ │ │   │
│   │  │ • Calendar│  │   room     │  │  │   RoomApprovalService     │ │ │   │
│   │  │ • Dashboard│  │ • Conflict │  │  │   DeviceManager           │ │ │   │
│   │  │ • Pricing  │  │   detect   │  │  │   NotificationManager     │ │ │   │
│   │  │ • Approvals│  │ • Excel    │  │  │   PricingService          │ │ │   │
│   │  │ • Inventory│  │   import   │  │  └───────────────────────────┘ │ │   │
│   │  └────────────┘  └────────────┘  └─────────────────────────────────┘ │   │
│   │                                                                     │   │
│   └─────────────────────────────────┬───────────────────────────────────┘   │
│                                     │                                        │
│                    ┌────────────────┴────────────────┐                       │
│                    │   NumPy Type Converter          │                       │
│                    │   (src/numpy_type_converter.py) │                       │
│                    └────────────────┬────────────────┘                       │
│                                     │                                        │
│                    ┌────────────────┴────────────────┐                       │
│                    │    psycopg2 ThreadedConnectionPool                       │
│                    │    (minconn=1, maxconn=20)      │                       │
│                    └────────────────┬────────────────┘                       │
└─────────────────────────────────────┼────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼────────────────────────────────────────┐
│                              DATA LAYER                                      │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     PostgreSQL 16+                                   │   │
│   │                                                                     │   │
│   │  Core Tables:                                                     │   │
│   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐         │   │
│   │  │  rooms    │ │ bookings  │ │  devices  │ │   users   │         │   │
│   │  │ (24 rows) │ │ (807+ rows│ │ (110+ rows│ │ (5 roles) │         │   │
│   │  └───────────┘ └───────────┘ └───────────┘ └───────────┘         │   │
│   │                                                                     │   │
│   │  Supporting Tables:                                                │   │
│   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐     │   │
│   │  │device_cats  │ │ pricing_    │ │ booking_device_         │     │   │
│   │  │offsite_     │ │   catalog   │ │   assignments           │     │   │
│   │  │  rentals    │ │notification_│ │device_movement_log    │     │   │
│   │  └─────────────┘ └─────────────┘ └─────────────────────────┘     │   │
│   │                                                                     │   │
│   │  Key Features:                                                     │   │
│   │  • tstzrange for booking periods                                 │   │
│   │  • Exclusion constraints prevent double-booking                  │   │
│   │  • ACID compliance                                                  │   │
│   │  • Timezone handling (UTC)                                          │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Dependencies

### Dependency Graph

```
src/
├── __init__.py
├── app.py (main entry point)
│   ├── auth.py
│   ├── db.py
│   ├── booking_form.py
│   │   └── models/BookingService
│   │   └── models/AvailabilityService
│   ├── pricing_catalog.py
│   │   └── models/PricingService
│   └── models/
│       ├── DeviceManager
│       ├── NotificationManager
│       ├── BookingService
│       ├── AvailabilityService
│       ├── RoomApprovalService
│       └── PricingService
│           └── db.py (all services)
│
├── auth.py
│   └── db.py
│
├── db.py (core database layer)
│   └── numpy_type_converter.py
│
├── booking_form.py
│   └── models/BookingService
│   └── models/AvailabilityService
│
├── pricing_catalog.py
│   └── models/PricingService
│
├── numpy_type_converter.py (utility)
│
└── models/
    ├── __init__.py (exports all services)
    ├── device_manager.py → db.py
    ├── notification_manager.py → db.py
    ├── booking_service.py → db.py, AvailabilityService
    ├── availability_service.py → db.py
    ├── room_approval_service.py → db.py
    └── pricing_service.py → db.py
```

### External Dependencies

```
requirements.txt
├── streamlit (UI framework)
├── pandas (data manipulation)
├── psycopg2-binary (PostgreSQL adapter)
├── pytz (timezone handling)
├── bcrypt (password hashing)
└── openpyxl (Excel processing - via pandas)
```

---

## Component Interactions

### Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   User   │────▶│  Login   │────▶│  auth.py │────▶│  users   │
│          │     │   Form   │     │          │     │  table   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ bcrypt.check │
                              │   password   │
                              └───────┬──────┘
                                      │
                              ┌───────▼────────┐
                              │ Set session    │
                              │ state role     │
                              └───────┬────────┘
                                      ▼
                              ┌──────────────┐
                              │ Route to     │
                              │ role-based   │
                              │ menu         │
                              └──────────────┘
```

### Booking Creation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User fills booking form (booking_form.py)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Role-based validation:                                       │
│    - Admin: Can select room or skip to pending                 │
│    - Staff: Always goes to pending (Ghost Inventory)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Check availability (AvailabilityService):                    │
│    - Room conflicts detected                                   │
│    - Device availability validated                             │
│    - Capacity warnings generated                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Create booking (BookingService):                             │
│    - booking_period: tstzrange(start, end)                     │
│    - Status: 'Pending' or 'Confirmed'                          │
│    - All 13 Phase 3 fields populated                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Database insert with ACID transaction:                       │
│    - Exclusion constraint prevents double-booking              │
│    - Multi-tenancy (TECH/TRAINING) applied                     │
│    - Connection returned to pool                               │
└─────────────────────────────────────────────────────────────────┘
```

### Device Assignment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. IT Staff opens Device Assignment Queue                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. DeviceManager.get_available_devices():                     │
│    - Query devices by category                                  │
│    - Exclude already assigned devices                          │
│    - Check date range overlaps                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. IT Staff selects devices by serial number:                 │
│    - Multi-select interface                                     │
│    - Option for off-site rental                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. DeviceManager.assign_device():                               │
│    - Create booking_device_assignments record                   │
│    - Link device to booking                                     │
│    - Log assignment for AI training                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. If off-site:                                                 │
│    DeviceManager.create_offsite_rental():                     │
│    - Collect rental_no, contact info, return_date             │
│    - Create offsite_rentals record                              │
└─────────────────────────────────────────────────────────────────┘
```

### Room Approval (Ghost Inventory) Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Room Boss views Pending Approvals page                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. RoomApprovalService.get_pending_bookings():                  │
│    - Fetch bookings with status='Pending'                       │
│    - Show client info, dates, requirements                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Room Boss selects room:                                      │
│    - View current room occupancy                                │
│    - Check for conflicts (RoomApprovalService.check_room_conflicts)│
│    - Override option if conflicts exist                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. RoomApprovalService.assign_room():                           │
│    - Update booking with room_id                                │
│    - Set status='Room Assigned'                                 │
│    - Record room_boss_notes                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Calendar View Data Flow

```
User requests Calendar view
    │
    ▼
┌─────────────────────────────────────┐
│ db.get_rooms_for_calendar()         │
│ • Returns: 24 active rooms            │
│ • Ordered by predefined priority     │
└──────────────┬────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ db.get_calendar_grid(start, end)    │
│ • Returns: Expanded booking data    │
│ • One row per room per day          │
│ • Includes all Phase 3 fields       │
└──────────────┬────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Render Excel-style grid:            │
│ • Days as rows, rooms as columns   │
│ • Color coding (today, weekend)    │
│ • Headcount display (learners+fac) │
│ • Catering indicators (emoji)       │
└─────────────────────────────────────┘
```

### Pricing Catalog Data Flow

```
Admin accesses Pricing Catalog
    │
    ▼
┌─────────────────────────────────────┐
│ PricingService.get_room_pricing()   │
│ PricingService.get_device_pricing() │
│ PricingService.get_catering_pricing()│
└──────────────┬────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Display three-tab interface:        │
│ • Room pricing (daily/weekly/monthly)│
│ • Device category pricing (collective)│
│ • Catering/supplies pricing          │
└──────────────┬────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Admin edits pricing:                │
│ • PricingService.update_pricing()   │
│ • Soft delete via expiry_date       │
└─────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Streamlit | 1.28+ | Web UI framework |
| **Backend** | Python | 3.9+ | Application logic |
| **Database** | PostgreSQL | 16+ | Primary data store |
| **Connection** | psycopg2 | 2.9+ | PostgreSQL adapter |
| **Pooling** | psycopg2.pool | - | Connection management |
| **Auth** | bcrypt | 4.0+ | Password hashing |
| **Data** | pandas | 2.0+ | Data manipulation |
| **Timezone** | pytz | 2023.3+ | Timezone handling |
| **Excel** | openpyxl | 3.0+ | Excel file processing |

### Python Dependencies

```
streamlit>=1.28.0
psycopg2-binary>=2.9.0
pandas>=2.0.0
bcrypt>=4.0.0
python-dateutil>=2.8.0
pytz>=2023.3
openpyxl>=3.0.0
```

### Infrastructure

| Component | Technology | Configuration |
|-----------|-----------|---------------|
| **Server** | Ubuntu Linux | 100.69.57.77 |
| **VPN** | Tailscale | Secure network access |
| **Web Server** | Streamlit (built-in) | Port 8501 |
| **Process Manager** | systemd | colab_erp.service |
| **Database** | PostgreSQL | Port 5432, 100 max connections |
| **Connection Pool** | psycopg2.pool | minconn=1, maxconn=20 |

---

## Database Schema

### Core Tables

#### 1. rooms

```sql
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    max_capacity INTEGER NOT NULL,
    room_type VARCHAR(50),
    has_devices BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    parent_room_id INTEGER REFERENCES rooms(id)
);
```

**Purpose:** 24 training rooms and offices  
**Current Data:** Excellence, Inspiration, Honesty, Gratitude, Ambition, Perseverance, Courage, Possibilities, Motivation, A302, A303, Success 10, Respect 10, Innovation (12), Dedication, Integrity (15), Empower, Focus, Growth, Wisdom (8), Vision, Potential, Synergy, Ambition+Perseverance

**Key Fields:**
- `max_capacity`: Maximum room capacity for attendee validation
- `is_active`: Soft delete flag
- `parent_room_id`: For hierarchical room relationships

#### 2. bookings

```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id) NOT NULL,
    booking_period TSTZRANGE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    tenant_id tenant_type NOT NULL DEFAULT 'TECH',
    
    -- Attendees
    num_learners INTEGER DEFAULT 0,
    num_facilitators INTEGER DEFAULT 0,
    headcount INTEGER DEFAULT 0,
    
    -- Client Contact
    client_contact_person VARCHAR(100),
    client_email VARCHAR(100),
    client_phone VARCHAR(20),
    
    -- Catering
    coffee_tea_station BOOLEAN DEFAULT FALSE,
    morning_catering VARCHAR(50),
    lunch_catering VARCHAR(50),
    catering_notes TEXT,
    
    -- Supplies
    stationery_needed BOOLEAN DEFAULT FALSE,
    water_bottles INTEGER DEFAULT 0,
    
    -- Devices
    devices_needed INTEGER DEFAULT 0,
    device_type_preference VARCHAR(50),
    
    -- Notes
    room_boss_notes TEXT,
    
    -- Metadata
    end_date DATE,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT no_overlapping_bookings 
        EXCLUDE USING gist (room_id WITH =, booking_period WITH &&) 
        WHERE (room_id IS NOT NULL),
    CONSTRAINT chk_morning_catering 
        CHECK (morning_catering IS NULL OR morning_catering IN ('none', 'pastry', 'sandwiches')),
    CONSTRAINT chk_lunch_catering 
        CHECK (lunch_catering IS NULL OR lunch_catering IN ('none', 'self_catered', 'in_house')),
    CONSTRAINT chk_device_preference 
        CHECK (device_type_preference IS NULL OR device_type_preference IN ('any', 'laptops', 'desktops'))
);
```

**Purpose:** All booking records with complete Phase 3 fields  
**Current Count:** 807+ bookings  
**Key Features:**
- `booking_period`: TSTZRANGE for timezone-aware periods (07:30-16:30 daily)
- Exclusion constraint prevents double-booking (only when room_id IS NOT NULL)
- Multi-tenancy via `tenant_id` (TECH/TRAINING enum)
- Status workflow: Pending → Room Assigned → Confirmed

#### 3. devices

```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    category_id INTEGER REFERENCES device_categories(id),
    status VARCHAR(20) DEFAULT 'available',
    office_account VARCHAR(255),
    anydesk_id VARCHAR(255),
    CONSTRAINT chk_device_status 
        CHECK (status IN ('available', 'assigned', 'offsite', 'maintenance'))
);
```

**Purpose:** IT equipment inventory  
**Current Count:** 110+ devices  
**Statuses:** available, assigned, offsite, maintenance

#### 4. device_categories

```sql
CREATE TABLE device_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);
```

**Values:** Laptop, Desktop

#### 5. booking_device_assignments

```sql
CREATE TABLE booking_device_assignments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id),
    device_id INTEGER REFERENCES devices(id),
    device_category_id INTEGER REFERENCES device_categories(id),
    assigned_by VARCHAR(255) REFERENCES users(user_id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    is_offsite BOOLEAN DEFAULT FALSE,
    notes TEXT,
    assignment_type VARCHAR(20) DEFAULT 'manual',
    quantity INTEGER DEFAULT 1
);
```

**Purpose:** Links devices to bookings with full assignment tracking

#### 6. offsite_rentals

```sql
CREATE TABLE offsite_rentals (
    id SERIAL PRIMARY KEY,
    booking_device_assignment_id INTEGER REFERENCES booking_device_assignments(id),
    rental_no VARCHAR(255),
    rental_date DATE,
    contact_person VARCHAR(255),
    contact_number VARCHAR(255),
    contact_email VARCHAR(255),
    company VARCHAR(255),
    address TEXT,
    return_expected_date DATE,
    returned_at TIMESTAMP,
    rental_form_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose:** Tracks devices rented for off-site use with full contact details

#### 7. pricing_catalog (v2.2.3)

```sql
CREATE TABLE pricing_catalog (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,
    item_id INTEGER,
    item_name VARCHAR(255),
    daily_rate DECIMAL(10,2),
    weekly_rate DECIMAL(10,2),
    monthly_rate DECIMAL(10,2),
    unit VARCHAR(50),
    pricing_tier VARCHAR(20) DEFAULT 'standard',
    notes TEXT,
    effective_date DATE DEFAULT CURRENT_DATE,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT chk_item_type 
        CHECK (item_type IN ('room', 'device_category', 'catering')),
    CONSTRAINT chk_pricing_tier 
        CHECK (pricing_tier IN ('standard', 'premium', 'discounted'))
);
```

**Purpose:** Dynamic pricing management for rooms, device categories, and catering  
**Access Control:** Admin and IT admin roles only

#### 8. notification_log

```sql
CREATE TABLE notification_log (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    recipients TEXT[] NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    category_id INTEGER,
    threshold_percent INTEGER
);
```

**Purpose:** In-app notifications for IT Boss and Room Boss  
**Notification Types:**
- `low_stock`: Device stock below threshold
- `conflict_no_alternatives`: Device conflict with no alternatives
- `offsite_conflict`: Off-site rental conflicts
- `return_overdue`: Devices not returned by expected date

#### 9. users

```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL
);
```

**Roles (CORRECTED):**
- `admin`: Full system access including pricing
- `training_facility_admin` (Room Boss): Full access + Room assignment + pricing
- `it_rental_admin` (IT Boss): Full access + Device assignment + pricing
- `training_facility_admin_viewer`: View-only access (NO assignment, NO pricing)
- `kitchen_staff`: Calendar view ONLY (catering needs)
- `staff`: Calendar, bookings (pending only) - deprecated

### Supporting Tables

#### device_movement_log
- Tracks all device assignments/unassignments for AI learning
- Fields: log_id, device_id, action, from_booking_id, to_booking_id, performed_by, reason, created_at

#### stock_notifications
- Low stock alerts for device categories
- Fields: id, category, devices_available, devices_needed, notification_type, message, notified_it_boss, notified_room_boss, etc.

### Database Indexes

```sql
-- Performance indexes for common queries
CREATE INDEX idx_bookings_tenant ON bookings(tenant_id);
CREATE INDEX idx_bookings_status ON bookings(status) WHERE status = 'Pending';
CREATE INDEX idx_bookings_period ON bookings USING GIST(booking_period);
CREATE INDEX idx_offsite_rentals_assignment ON offsite_rentals(booking_device_assignment_id);
CREATE INDEX idx_device_movement_device ON device_movement_log(device_id);
CREATE INDEX idx_notifications_unread ON in_app_notifications(recipient_role, is_read, created_at DESC);
```

### Schema Relationships

```
                    ┌─────────────┐
                    │    users    │
                    │  (roles)    │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  bookings    │   │device_manager│   │ notification │
│  (main)      │◄──│  operations  │   │    log       │
└──────┬───────┘   └──────────────┘   └──────────────┘
       │
       │ references
       ▼
┌──────────────┐
│    rooms     │
│  (24 rooms)  │
└──────────────┘

┌──────────────┐
│   devices    │◄────┐
│  (110+ dev)  │     │
└──────┬───────┘     │
       │             │
       │ references  │ assigned via
       ▼             │
┌──────────────┐     │
│device_cats   │     │
└──────────────┘     │
                     │
                     ▼
        ┌─────────────────────────────┐
        │  booking_device_assignments │
        │      (junction table)       │
        └──────────────┬──────────────┘
                       │
                       ▼
              ┌──────────────┐
              │offsite_rentals│
              │  (tracking)   │
              └──────────────┘

┌─────────────────┐
│ pricing_catalog │
│  (3 item types) │
└─────────────────┘
```

---

## Configuration Points

### 1. Database Configuration

**Location:** `~/.streamlit/secrets.toml`

```toml
[postgres]
host = "100.69.57.77"
port = "5432"
dbname = "colab_erp"
user = "colabtechsolutions"
password = "[REDACTED]"
timezone = "Africa/Johannesburg"
```

**Accessed via:** `st.secrets["postgres"]["host"]` etc.

### 2. Connection Pool Configuration

**Location:** `src/db.py` - `get_db_pool()` function

```python
return psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=20,  # SRE NOTE: Fits within postgresql.conf limits (100)
    host=st.secrets["postgres"]["host"],
    port=st.secrets["postgres"]["port"],
    database=st.secrets["postgres"]["dbname"],
    user=st.secrets["postgres"]["user"],
    password=st.secrets["postgres"]["password"],
    options="-c timezone=UTC"  # CRITICAL: Enforces v2.1 Timezone Standard
)
```

### 3. Timezone Configuration

**UI-facing timezone:** Configured in secrets.toml (`Africa/Johannesburg`)  
**Database timezone:** UTC (enforced via connection options)

### 4. Systemd Service Configuration

**Location:** `infra/systemd/colab_erp.service`

```ini
[Unit]
Description=Colab ERP Streamlit Application
After=network.target

[Service]
Type=simple
User=colabtechsolutions
WorkingDirectory=/home/colabtechsolutions/colab_erp
Environment=PATH=/home/colabtechsolutions/venv/bin
ExecStart=/home/colabtechsolutions/venv/bin/streamlit run src/app.py --server.port 8501 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Application Constants

**Location:** Various service files

- **Default time range:** 07:30 - 16:30 (business hours)
- **Default tenant:** 'TECH'
- **Valid tenants:** {'TECH', 'TRAINING'}
- **Default device category:** 1 (Laptops)
- **Low stock threshold:** 3-5 devices per category

---

## External Dependencies

### Production Infrastructure

| Dependency | Purpose | Configuration |
|------------|---------|---------------|
| **Tailscale VPN** | Secure network access | 100.69.57.77 |
| **PostgreSQL** | Primary database | Port 5432 |
| **Ubuntu Server** | Host operating system | 100.69.57.77 |
| **systemd** | Process management | colab_erp.service |

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | 1.28+ | Web framework |
| psycopg2-binary | 2.9+ | PostgreSQL adapter |
| pandas | 2.0+ | Data manipulation |
| bcrypt | 4.0+ | Password hashing |
| pytz | 2023.3+ | Timezone handling |
| openpyxl | 3.0+ | Excel processing |

### Database Features

| Feature | PostgreSQL Version | Purpose |
|---------|-------------------|---------|
| TSTZRANGE | 9.2+ | Timezone-aware booking periods |
| EXCLUDE constraints | 9.0+ | Prevent double-booking |
| GIST indexes | All | Performance for range queries |
| Arrays | All | Notification recipients |

### Network Configuration

```
User Device
    │
    ▼
Internet
    │
    ▼
Tailscale VPN (Mesh network)
    │
    ▼
┌─────────────────┐
│ 100.69.57.77:8501 │ ← Streamlit application
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ 100.69.57.77:5432 │ ← PostgreSQL database
└─────────────────┘
```

---

## Design Patterns

### 1. Service Layer Pattern

All business logic encapsulated in service classes:

```python
# src/models/booking_service.py
class BookingService:
    """Service class for creating enhanced bookings"""
    
    def __init__(self):
        self.connection_pool = db.get_db_pool()
    
    def create_enhanced_booking(self, ...):
        # Business logic here
        pass
```

**Benefits:**
- Clear separation of concerns
- Reusable across UI components
- Testable in isolation

### 2. Repository Pattern

Database operations centralized in `db.py`:

```python
# src/db.py
def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    """Executes a SELECT query"""
    clean_params = convert_params_to_native(params)
    with get_db_connection() as conn:
        return pd.read_sql(query, conn, params=clean_params)

def run_transaction(query: str, params: tuple = None, fetch_one: bool = False):
    """Executes INSERT/UPDATE/DELETE with commit/rollback"""
    # ACID transaction handling
```

**Benefits:**
- Consistent database access
- Automatic connection pooling
- Type conversion safety

### 3. Context Manager Pattern

Database connections managed via context managers:

```python
@contextmanager
def get_db_connection():
    """Context manager to checkout a connection from the pool"""
    pool_instance = get_db_pool()
    conn = None
    try:
        conn = pool_instance.getconn()
        yield conn
    finally:
        if conn:
            pool_instance.putconn(conn)
```

**Benefits:**
- Guaranteed connection cleanup
- Exception-safe
- Pool hygiene maintained

### 4. Ghost Inventory Pattern

Bookings can exist without room assignment:

```
Pending → Room Assigned → Confirmed
    │
    └── Room Boss assigns room
```

**Benefits:**
- Flexible booking workflow
- Room Boss approval gate
- Conflict detection before assignment

### 5. Multi-Tenancy Pattern

Shared database with tenant discriminator:

```sql
ALTER TABLE bookings ADD COLUMN tenant_id tenant_type DEFAULT 'TECH';
-- Exclusion constraints remain GLOBAL (shared physical assets)
```

**Benefits:**
- Business separation (TECH/TRAINING)
- Shared physical asset constraints
- Single database maintenance

### 6. Result Dictionary Pattern

Service methods return consistent result dicts:

```python
return {
    'success': True,
    'booking_id': booking_id,
    'message': f'Booking #{booking_id} created successfully'
}

# Or on failure:
return {
    'success': False,
    'booking_id': None,
    'message': f'Failed to create booking: {str(e)}'
}
```

**Benefits:**
- Explicit success/failure indication
- Error messages for UI display
- Type-safe returns

### 7. Type Conversion Pattern

NumPy types automatically converted to Python native:

```python
# src/numpy_type_converter.py
def convert_params_to_native(params):
    """Convert numpy types to Python native types for database"""
    # Prevents psycopg2 "can't adapt type 'numpy.int64'" errors
```

**Benefits:**
- Prevents database adapter errors
- pandas/numpy compatibility
- Transparent to calling code

### 8. Role-Based Access Control (RBAC)

Menu and feature access determined by role:

```python
# src/app.py
user_role = st.session_state['role']

if user_role == 'training_facility_admin':
    menu = ["Dashboard", "Notifications", "Calendar", "Device Assignment Queue", ...]
elif user_role == 'it_rental_admin':
    menu = ["Dashboard", "Notifications", "Calendar", "Device Assignment Queue", ...]
```

**Benefits:**
- Granular permission control
- Role-specific UI
- Security by default

### 9. Logging for AI Training

All device assignments logged for future ML:

```python
# src/models/device_manager.py
logger.info(f"assign_device: Device {device_id} assigned to booking {booking_id}")
```

**Benefits:**
- Future AI automation
- Audit trail
- Pattern recognition data

### 10. Soft Delete Pattern

Pricing records soft-deleted via expiry_date:

```python
def delete_pricing(self, pricing_id: int) -> Dict[str, Any]:
    """Soft delete pricing by setting expiry date"""
    query = """
        UPDATE pricing_catalog 
        SET expiry_date = CURRENT_DATE - 1
        WHERE id = %s
    """
```

**Benefits:**
- Historical price tracking
- Audit compliance
- Data recovery possible

---

## System Statistics (February 2026)

| Metric | Value |
|--------|-------|
| **Version** | v2.2.3 |
| **Bookings** | 807+ |
| **Rooms** | 24 |
| **Devices** | 110+ |
| **User Roles** | 6 |
| **Database Size** | Growing daily |
| **Connection Pool** | 20 connections |
| **Response Time** | <500ms |
| **Excel Import** | 713 bookings |

---

## Recent Changes (v2.2.3)

### February 2026 Updates

| Feature | Description |
|---------|-------------|
| **Calendar Indicators** | Today (green), Weekend (purple), headcount display |
| **Excel Import** | 713 bookings from "Colab 2026 Schedule.xlsx" |
| **Pricing System** | Dynamic pricing catalog for rooms/devices/catering |
| **Multi-Tenancy** | TECH/TRAINING divisions with shared assets |
| **Ghost Inventory** | Pending → Room Assignment workflow |
| **Enhanced Booking Form** | All 13 Phase 3 fields |
| **Device Management** | Manual assignment, off-site tracking |
| **Notifications** | IT Boss & Room Boss alerts |

### Database Migrations Applied

1. **v2.2_add_tenancy.sql**: Multi-tenancy support (TECH/TRAINING)
2. **v2.4_device_assignment_system.sql**: Device management tables
3. **v2.5_enhanced_booking_form.sql**: Phase 3 booking fields
4. **v2.5.1_add_room_boss_notes.sql**: Room boss notes field

---

**Document Version:** 1.0.0  
**Maintained by:** Code Architecture Documenter  
**Last Updated:** February 28, 2026
