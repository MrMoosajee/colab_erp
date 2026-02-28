# Colab ERP - System Architecture

**Version:** v2.2.3  
**Last Updated:** February 28, 2026  
**Classification:** Internal Confidential

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Data Flow](#data-flow)
3. [Technology Stack](#technology-stack)
4. [Database Schema](#database-schema)
5. [Service Layer](#service-layer)
6. [Security Model](#security-model)
7. [Deployment Architecture](#deployment-architecture)
8. [Scalability Considerations](#scalability-considerations)
9. [Recent Changes (v2.2.3)](#recent-changes-v223)
10. [Future Architecture (Phase 4)](#future-architecture-phase-4)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER LAYER                                     │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   Browser    │  │   Browser    │  │   Browser    │  │   Future    │ │
│  │ (Staff User) │  │ (Room Boss)  │  │ (IT Staff)   │  │ (Mobile)    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
└─────────┼──────────────────┼──────────────────┼──────────────────┼──────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │      Tailscale VPN         │
                    │   (Secure Network Access)  │
                    └─────────────┬──────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────┐
│                      APPLICATION LAYER                                   │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Streamlit v2.2.3                               │  │
│  │                                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │  │
│  │  │    app.py    │  │booking_form  │  │   Service Layer      │    │  │
│  │  │   (Views)    │  │   (Forms)    │  │ ┌──────────────────┐ │    │  │
│  │  │              │  │              │  │ │BookingService    │ │    │  │
│  │  │ • Login      │  │ • Multi-room │  │ │AvailabilitySvc   │ │    │  │
│  │  │ • Calendar   │  │ • Validation │  │ │RoomApprovalSvc   │ │    │  │
│  │  │ • Dashboard  │  │ • Conflict   │  │ │DeviceManager     │ │    │  │
│  │  │ • Approvals  │  │   detection  │  │ │NotificationMgr   │ │    │  │
│  │  │ • Pricing    │  │ • Excel import│  │ │PricingService    │ │    │  │
│  │  └──────────────┘  └──────────────┘  │ └──────────────────┘ │    │  │
│  │                                    └──────────────────────┘    │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                           psycopg2 + pool (20 conn)                      │
│                                    │                                     │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                         DATA LAYER                                       │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 PostgreSQL 16+                                   │    │
│  │                                                                  │    │
│  │  Core Tables:                                                    │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │    │
│  │  │   rooms     │ │  bookings   │ │   devices   │ │   users   │ │    │
│  │  │  (24 rows)  │ │ (807+ rows) │ │  (110+)     │ │(auth/data)│ │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │    │
│  │                                                                  │    │
│  │  Supporting Tables:                                              │    │
│  │  ┌─────────────────┐ ┌──────────────────┐ ┌───────────────────┐ │    │
│  │  │pricing_catalog  │ │offsite_rentals   │ │booking_device_    │ │    │
│  │  │device_categories│ │device_movement_  │ │  assignments      │ │    │
│  │  │notification_log │ │     log          │ │stock_notifications │ │    │
│  │  └─────────────────┘ └──────────────────┘ └───────────────────┘ │    │
│  │                                                                  │    │
│  │  Key Features:                                                   │    │
│  │  • tstzrange for booking periods                                │    │
│  │  • Exclusion constraints prevent double-booking                 │    │
│  │  • Connection pooling (20 connections)                          │    │
│  │  • ACID compliance                                              │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Booking Creation Flow (Phase 3)

```
User fills form (booking_form.py)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Role Check                                            │
│ • Admin: Can select room or go to pending            │
│ • Staff: Always goes to pending                       │
└─────────────────────┬─────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                             │
        ▼                             ▼
┌───────────────┐            ┌──────────────────┐
│ Direct Booking│            │ Ghost Inventory  │
│ (room selected)│           │ (no room yet)     │
│               │            │                  │
│ Status:       │            │ Status: Pending  │
│ Confirmed     │            │                  │
└───────┬───────┘            └────────┬─────────┘
        │                             │
        │                    ┌────────▼────────┐
        │                    │ Room Boss        │
        │                    │ Assignment      │
        │                    │ Interface        │
        │                    └────────┬────────┘
        │                             │
        │                    ┌────────▼────────┐
        │                    │ Status: Room     │
        │                    │ Assigned         │
        │                    └──────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Database Insert (booking_service.py)                     │
│ • booking_period: tstzrange(start, end)               │
│ • room_id: int or NULL                                │
│ • status: 'Confirmed' or 'Pending'                    │
│ • All Phase 3 fields (13 total)                      │
└─────────────────────────────────────────────────────────┘
```

### Device Assignment Flow

```
IT Staff opens Device Assignment Queue
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Fetch pending device requests                           │
│ • Bookings with status='confirmed'                     │
│ • Device assignments with device_id=NULL               │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│ Check device availability                               │
│ • Query devices table for category                    │
│ • Exclude devices already assigned                     │
│ • Exclude devices with overlapping bookings           │
└─────────────────────┬─────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                             │
        ▼                             ▼
┌───────────────┐            ┌──────────────────┐
│ Devices       │            │ No Devices       │
│ Available     │            │ Available        │
│               │            │                  │
│ Show list of  │            │ Notify IT Boss   │
│ serial numbers│            │ & Room Boss      │
└───────┬───────┘            └──────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ IT Staff selects devices                                │
│ • Multi-select by serial number                         │
│ • Option for off-site rental                           │
└─────────────────────┬─────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                             │
        ▼                             ▼
┌───────────────┐            ┌──────────────────┐
│ On-site       │            │ Off-site         │
│ Assignment    │            │ Rental           │
│               │            │                  │
│ Simple assign │            │ Collect:         │
│               │            │ • Rental No      │
│               │            │ • Contact info   │
│               │            │ • Return date    │
└───────┬───────┘            └────────┬─────────┘
        │                             │
        └─────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│ Create assignment record                                │
│ booking_device_assignments table                        │
└─────────────────────────────────────────────────────────┘
```

### Excel Import Flow

```
Excel File (Colab 2026 Schedule.xlsx)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Parse Excel (import_excel_schedule.py)                 │
│ • Month sheets (Jan-Dec 2026)                          │
│ • Room columns → Room IDs                              │
│ • Entry patterns: "Client 25+1", "25 + 18 laptops"    │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│ Create Bookings                                         │
│ • Daily bookings for each entry                        │
│ • Long-term rentals: Siyaya, Melissa                  │
│ • Auto-approved status                                │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│ Database Insert                                         │
│ • 713+ bookings created (Feb 2026 import)             │
│ • TECH tenant default                                 │
│ • Status: Approved                                    │
└─────────────────────────────────────────────────────────┘
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
| **Config** | toml | - | Secrets management |
| **Timezone** | pytz | 2023.3+ | Timezone handling |
| **Excel** | openpyxl | 3.0+ | Excel file processing |

### Dependencies (requirements.txt)

```
streamlit>=1.28.0
psycopg2-binary>=2.9.0
pandas>=2.0.0
bcrypt>=4.0.0
python-dateutil>=2.8.0
pytz>=2023.3
openpyxl>=3.0.0
```

---

## Database Schema

### Core Tables

#### rooms

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

**Description:** 24 training rooms and offices  
**Current Data:**
- Excellence, Inspiration, Honesty, Gratitude, Ambition, Perseverance, Courage, Possibilities
- Motivation, A302, A303, Success 10, Respect 10, Innovation (12), Dedication
- Integrity (15), Empower, Focus, Growth, Wisdom (8), Vision, Potential, Synergy, Ambition+Perseverance

**Key Fields:**
- `max_capacity`: Maximum room capacity for attendee validation
- `is_active`: Soft delete flag
- `parent_room_id`: For hierarchical room relationships (unused)

#### bookings

```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id) NOT NULL,
    booking_period TSTZRANGE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    tenant_id tenant_type NOT NULL DEFAULT 'TECH',
    
    -- Phase 3 Fields (Attendees)
    num_learners INTEGER DEFAULT 0,
    num_facilitators INTEGER DEFAULT 0,
    headcount INTEGER DEFAULT 0,
    
    -- Phase 3 Fields (Client Contact)
    client_contact_person VARCHAR(100),
    client_email VARCHAR(100),
    client_phone VARCHAR(20),
    
    -- Phase 3 Fields (Catering)
    coffee_tea_station BOOLEAN DEFAULT FALSE,
    morning_catering VARCHAR(50),
    lunch_catering VARCHAR(50),
    catering_notes TEXT,
    
    -- Phase 3 Fields (Supplies)
    stationery_needed BOOLEAN DEFAULT FALSE,
    water_bottles INTEGER DEFAULT 0,
    
    -- Phase 3 Fields (Devices)
    devices_needed INTEGER DEFAULT 0,
    device_type_preference VARCHAR(50),
    
    -- Phase 3 Fields (Notes)
    room_boss_notes TEXT,
    
    -- Legacy Fields
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

**Key Features:**
- `booking_period`: TSTZRANGE for timezone-aware periods (07:30-16:30 daily)
- Exclusion constraint prevents double-booking (only when room_id IS NOT NULL)
- Status workflow: Pending → Confirmed
- Current count: **807+ bookings** (growing daily)

**Recent Imports:**
- **713 bookings** imported from "Colab 2026 Schedule.xlsx" (February 2026)
- Includes long-term rentals: Siyaya (Success 10), Melissa (Wisdom 8)

#### devices

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

**Description:** IT equipment inventory (laptops, desktops)  
**Current count:** 110+ devices

#### device_categories

```sql
CREATE TABLE device_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);
```

**Values:** Laptop, Desktop

#### booking_device_assignments

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

**Description:** Links devices to bookings with assignment tracking

#### offsite_rentals

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

**Description:** Tracks devices rented for off-site use with full contact details

#### pricing_catalog (NEW v2.2.3)

```sql
CREATE TABLE pricing_catalog (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,  -- 'room', 'device_category', 'catering'
    item_id INTEGER,                 -- FK to rooms.id or device_categories.id
    item_name VARCHAR(255),            -- For catering items (when item_id is NULL)
    daily_rate DECIMAL(10,2),
    weekly_rate DECIMAL(10,2),
    monthly_rate DECIMAL(10,2),
    unit VARCHAR(50),                  -- 'per day', 'per device', 'per person'
    pricing_tier VARCHAR(20) DEFAULT 'standard',  -- 'standard', 'premium', 'discounted'
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

**Description:** Dynamic pricing management for rooms, device categories, and catering  
**Access Control:** Admin and IT admin roles only

#### notification_log

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

**Description:** In-app notifications for IT Boss and Room Boss  
**Notification Types:**
- `low_stock`: Device stock below threshold
- `conflict_no_alternatives`: Device conflict with no alternatives available
- `offsite_conflict`: Off-site rental conflicts
- `return_overdue`: Devices not returned by expected date

#### users

```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL
);
```

**Roles (CORRECTED):**
- `admin`: Full system access with pricing
- `training_facility_admin` (Room Boss = Admin): Full system access + Room assignment, has pricing access
- `it_rental_admin` (IT Boss = IT Rental Admin): Full system access + Device assignment, has pricing access
- `training_facility_admin_viewer` (Non-Admin): Calendar, Bookings, Pricing (view-only), Inventory - NO assignment privileges
- `kitchen_staff` (NEW): Calendar view ONLY - sees catering needs and headcounts
- `staff` (Legacy): Calendar, bookings (pending only) - being deprecated

### Supporting Tables

#### device_movement_log
- Tracks all device assignments/unassignments for AI learning
- Fields: log_id, device_id, action, from_booking_id, to_booking_id, performed_by, reason, created_at

#### stock_notifications
- Low stock alerts for device categories
- Fields: id, category, devices_available, devices_needed, notification_type, message, notified_it_boss, notified_room_boss, etc.

#### in_app_notifications
- General in-app notifications
- Fields: id, recipient_role, notification_type, title, message, related_booking_id, is_read, created_at

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

---

## Service Layer

### Service Architecture

The service layer follows a **modular design** with clear separation of concerns:

```
src/models/
├── __init__.py
├── availability_service.py   # Room/device availability checking
├── booking_service.py        # Booking creation with Phase 3 fields
├── room_approval_service.py  # Ghost Inventory workflow
├── device_manager.py         # Device assignment and tracking
├── notification_manager.py   # In-app notifications
└── pricing_service.py        # Dynamic pricing management
```

### Design Principles

1. **Single Responsibility**: Each service handles one domain
2. **Explicit Error Handling**: Services return result dicts with `success` flag
3. **Database Connection Management**: Each method gets/returns connections from pool
4. **Timezone Awareness**: All datetimes use `pytz.UTC.localize()`

### Service Interaction Pattern

```python
class SomeService:
    def __init__(self):
        self.connection_pool = db.get_db_pool()
    
    def some_operation(self, ...):
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                # Execute queries
                cur.execute("SELECT ...", params)
                result = cur.fetchall()
                
            conn.commit()  # If write operation
            return {'success': True, 'data': result}
            
        except Exception as e:
            if conn:
                conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            if conn:
                self.connection_pool.putconn(conn)
```

### Pricing Service (NEW v2.2.3)

```python
class PricingService:
    """Dynamic pricing management for rooms, devices, and catering"""
    
    # Room pricing
    def get_room_pricing(self) -> pd.DataFrame
    def get_rooms_without_pricing(self) -> pd.DataFrame
    def create_room_pricing(self, room_id, daily_rate, ...) -> Dict
    
    # Device pricing (collective by category)
    def get_device_pricing(self) -> pd.DataFrame
    def get_device_categories_without_pricing(self) -> pd.DataFrame
    def create_device_category_pricing(self, category_id, daily_rate, ...) -> Dict
    
    # Catering pricing
    def get_catering_pricing(self) -> pd.DataFrame
    def get_catering_items(self) -> pd.DataFrame
    def create_catering_pricing(self, item_name, unit_price, ...) -> Dict
    
    # Management
    def update_pricing(self, pricing_id, ...) -> Dict
    def delete_pricing(self, pricing_id) -> Dict  # Soft delete
```

**Access Control:** Only `admin` and `it_admin` roles can access pricing functionality.

---

## Security Model

### Authentication

1. **bcrypt Password Hashing**: Passwords hashed with salt before storage
2. **Database-backed**: Credentials stored in PostgreSQL `users` table
3. **Session Management**: Streamlit session state for login persistence
4. **Failsafe**: Legacy plaintext passwords caught for migration

### Authorization (RBAC)

| Role | Permissions | Pricing Access |
|------|-------------|----------------|
| **admin** | Full system access | ✅ Yes |
| **training_facility_admin (Room Boss)** | Full system access + Room Assignment | ✅ Yes |
| **it_rental_admin (IT Boss)** | Full system access + Device Assignment | ✅ Yes |
| **training_facility_admin_viewer** | Calendar, Bookings, Pricing (view-only), Inventory | ❌ No |
| **kitchen_staff** | Calendar view ONLY | ❌ No |
| **staff** | Calendar, bookings (pending only) | ❌ No |

### Data Security

- **Parameterized Queries**: All SQL uses `%s` placeholders (no injection)
- **Connection Pooling**: 20 connections max, proper cleanup
- **VPN Required**: Tailscale VPN for production access
- **Secrets Management**: Database credentials in `~/.streamlit/secrets.toml`

---

## Deployment Architecture

### Current Deployment

```
┌─────────────────────────────────────────────────────────┐
│ Production Server (100.69.57.77)                        │
│ Ubuntu Linux                                            │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Streamlit Service (systemd)                      │ │
│  │ • Port: 8501                                     │ │
│  │ • Process: Single instance                       │ │
│  │ • Auto-restart: yes                              │ │
│  │ • Status: 🟢 Online                              │ │
│  └───────────────────────────────────────────────────┘ │
│                          │                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │ PostgreSQL 16+                                   │ │
│  │ • Port: 5432                                     │ │
│  │ • Max connections: 100                           │ │
│  │ • Data: /var/lib/postgresql                      │ │
│  │ • Bookings: 807+ rows                            │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
              │
              │ Tailscale VPN
              ▼
        Users (authenticated)
```

### Deployment Process

**Current (Manual):**
1. Fix code locally
2. Run syntax check: `python3 -m py_compile src/app.py`
3. Copy files: `scp -r src/ colab:~/colab_erp/`
4. Restart service: `ssh colab "sudo systemctl restart colab_erp"`

**Target (Automated):**
1. Run `./deploy.sh`
2. Script handles: syntax check → rsync → restart → health check
3. Automatic rollback on failure

### Infrastructure Files

```
infra/
└── systemd/
    └── colab_erp.service

# colab_erp.service
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

---

## Scalability Considerations

### Current Scale (February 2026)

- **Users:** 5-10 concurrent
- **Bookings:** 807+ (growing daily)
- **Rooms:** 24
- **Devices:** 110+
- **Performance:** <500ms response time
- **Excel Import:** 713 bookings imported successfully

### Bottlenecks

1. **Single Streamlit Instance**: Single-threaded, single process
2. **Database Queries**: No read replica, no caching
3. **Calendar View**: Loads all bookings for date range
4. **Connection Pool**: 20 connections (adequate for current scale)

### Scaling Roadmap

| Users | Architecture Changes | Timeline |
|-------|---------------------|----------|
| 5-20 | Current (single server) | ✅ Now |
| 20-50 | Add Redis cache for calendar | Month 2 |
| 50-100 | Database read replica | Month 3 |
| 100+ | Load balancer + multiple Streamlit instances | Phase 4 |
| 200+ | API layer (FastAPI) + microservices | Phase 5 |

### Performance Optimizations Planned

1. **Database Indexes:**
   ```sql
   CREATE INDEX idx_bookings_period ON bookings USING GIST(booking_period);
   CREATE INDEX idx_bookings_status ON bookings(status) WHERE status = 'Pending';
   ```

2. **Caching Layer:**
   ```python
   @cache_result(ttl=300)  # 5 minutes
   def get_calendar_grid(...):
       # Expensive query
   ```

3. **Query Optimization:**
   - Only load visible date range
   - Exclude long-term offices from calendar queries
   - Materialized view for device availability

---

## Recent Changes (v2.2.3)

### February 2026 Updates

| Feature | Description | Impact |
|---------|-------------|--------|
| **Calendar Indicators** | Today (green), Weekend (purple), headcount display | Better visual tracking |
| **Excel Import** | 713 bookings from "Colab 2026 Schedule.xlsx" | Bulk data migration |
| **Pricing System** | Dynamic pricing catalog for rooms/devices/catering | Revenue management |
| **Multi-Tenancy** | TECH/TRAINING divisions with shared assets | Business separation |
| **Ghost Inventory** | Pending → Room Assignment workflow | Flexible booking |
| **Enhanced Booking Form** | All 13 Phase 3 fields | Complete booking info |
| **Device Management** | Manual assignment, off-site tracking | IT operations |
| **Notifications** | IT Boss & Room Boss alerts | Proactive management |

### Database Migrations Applied

1. **v2.2_add_tenancy.sql**: Multi-tenancy support (TECH/TRAINING)
2. **v2.4_device_assignment_system.sql**: Device management tables
3. **v2.5_enhanced_booking_form.sql**: Phase 3 booking fields
4. **v2.5.1_add_room_boss_notes.sql**: Room boss notes field

### New Services Added

1. **PricingService** (`src/models/pricing_service.py`)
   - Room pricing management
   - Device category pricing (collective)
   - Catering pricing
   - Role-based access control

2. **Excel Import** (`src/import_excel_schedule.py`)
   - Parse "Colab 2026 Schedule.xlsx"
   - Pattern matching for headcount
   - Long-term rental handling
   - 713 bookings imported

---

## Future Architecture (Phase 4)

### API Layer Addition

```
Mobile App ──┐
             ├──▶ FastAPI ──▶ PostgreSQL
Web App ─────┘      │
                    ├──▶ Redis (Cache)
                    └──▶ Celery (Background jobs)
```

### Microservices Consideration

**When to Decouple:**
- 100+ concurrent users
- Mobile app requirement
- Third-party integrations needed
- Sub-second response time SLA

**Candidate Services:**
1. **Booking Service**: Booking CRUD, availability
2. **Device Service**: Device inventory, assignments
3. **Notification Service**: Email, SMS, push notifications
4. **Auth Service**: Authentication, authorization
5. **Calendar Service**: Calendar generation, exports
6. **Pricing Service**: Dynamic pricing management

### Event-Driven Architecture

```
Booking Created ──▶ Event Bus ──▶ Notification Service
                                     │
                                     ├─▶ Email Service
                                     ├─▶ SMS Service
                                     └─▶ Dashboard Update
```

**Benefits:**
- Decoupled services
- Async processing
- Better retry logic
- Audit trail

---

## Monitoring & Observability (Planned)

### Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Response Time | <500ms | >1000ms |
| Error Rate | <1% | >5% |
| DB Pool Usage | <70% | >90% |
| Active Sessions | Track | N/A |
| Booking Creation Rate | Track | N/A |
| Device Stock Levels | >20% | <10% |

### Tools Planned

- **Sentry**: Error tracking and alerting
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards
- **Structured Logging**: JSON format for aggregation

---

## Decision Records

### ADR-001: Keep Monolithic Architecture
- **Status:** Accepted
- **Context:** Current scale (5-10 users) doesn't justify microservices complexity
- **Decision:** Stay with Streamlit + PostgreSQL monolith
- **Consequences:** Simpler development, limited scalability

### ADR-002: Add API Layer in Phase 4
- **Status:** Proposed
- **Context:** Need mobile app support and third-party integrations
- **Decision:** Add FastAPI layer alongside Streamlit
- **Consequences:** Enables mobile, adds complexity

### ADR-003: Ghost Inventory Workflow
- **Status:** Accepted
- **Context:** Room Boss needs approval workflow, staff shouldn't select rooms
- **Decision:** Pending → Room Assigned → Confirmed state machine
- **Consequences:** Flexible but requires careful state management

### ADR-004: Manual Device Assignment
- **Status:** Accepted
- **Context:** IT Staff wants full control over device selection
- **Decision:** Manual assignment by serial number, logged for AI training
- **Consequences:** More IT Staff work, better tracking

### ADR-005: Dynamic Pricing Catalog (v2.2.3)
- **Status:** Accepted
- **Context:** Need flexible pricing for rooms, devices, and catering
- **Decision:** pricing_catalog table with item_type discriminator
- **Consequences:** Single table for all pricing types, simpler queries

---

**Document Version:** 1.1.0  
**Maintained by:** Chief Documentation Officer (CDO-001)  
**Last Updated:** February 28, 2026
