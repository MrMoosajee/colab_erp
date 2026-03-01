# Project Memory - Colab ERP Complete Reference

**Project:** Colab ERP v2.2.3  
**Full Name:** Professional Training Facility & IT Rental Management System  
**Organization:** Colab Tech Solutions  
**Status:** Production Ready  
**Documentation:** `/home/shuaibadams/Projects/colab_erp/docs/memory/`  

---

## 📋 Executive Summary

Colab ERP is a comprehensive Enterprise Resource Planning system for managing room bookings, device inventory, and training facility operations. Built with Streamlit and PostgreSQL, it supports multi-tenancy (TECH/TRAINING divisions) with Ghost Inventory workflow for flexible resource management.

### Key Metrics (February 2026)
- **807+ Bookings** in production database
- **713 Bookings** imported from Excel (Colab 2026 Schedule)
- **24 Rooms** managed (training rooms and offices)
- **110+ Devices** tracked (laptops, desktops)
- **5-10 Concurrent Users** supported
- **99.9%+ Uptime** since v2.2.0

### Current State
- ✅ All Phase 3 features implemented
- ✅ Ghost Inventory workflow active
- ✅ Calendar with indicators working
- ✅ Device management functional
- ✅ Pricing catalog deployed (v2.2.3)
- ✅ Excel import completed

---

## 🏗️ Complete System Overview

### Technology Stack
| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend | Streamlit | 1.28+ | Web UI framework |
| Backend | Python | 3.9+ | Application logic (OOP only) |
| Database | PostgreSQL | 16+ | Primary data store |
| Auth | bcrypt | 4.0+ | Password hashing |
| Connection | psycopg2-binary | 2.9+ | PostgreSQL adapter |
| Pooling | psycopg2.pool | - | Connection management |
| Timezone | pytz | 2023.3+ | Timezone handling |
| Excel | openpyxl | 3.0+ | Excel file processing |
| VPN | Tailscale | - | Secure network access |

### Infrastructure
```
┌─────────────────────────────────────────────────────────┐
│ User Workstation                                        │
│ (Pop!_OS Linux 6.17, Python 3.10.12)                   │
│ • Development environment                               │
│ • ~/.moa_memory/ for context                            │
│ • ~/.cline/ for tool state                              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Tailscale VPN (WireGuard mesh)
                      │
┌─────────────────────▼───────────────────────────────────┐
│ Production Server (100.69.57.77)                       │
│ Ubuntu 24.04.4 LTS, Python 3.12.3                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Streamlit Application (Port 8501)              │   │
│  │ • Single instance (5-10 users)                 │   │
│  │ • Systemd managed (auto-restart)             │   │
│  │ • Tailscale VPN access only                  │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         │                              │
│  ┌──────────────────────▼──────────────────────────┐   │
│  │ PostgreSQL 16+ (Port 5432)                     │   │
│  │ • 807+ bookings                                │   │
│  │ • 24 rooms                                     │   │
│  │ • 110+ devices                                 │   │
│  │ • ACID transactions                            │   │
│  │ • Exclusion constraints                        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Complete Feature Inventory

### Core Features (All Complete ✅)

#### 1. Multi-Tenancy Support
- TECH and TRAINING divisions
- Shared physical assets with logical separation
- Global exclusion constraints (shared physics)
- Tenant-specific reporting

#### 2. Ghost Inventory Workflow (Phase 3)
- Bookings without immediate room assignment
- Pending → Room Assigned → Confirmed status flow
- Room Boss approval interface
- Conflict detection with override capability
- Multi-room bookings (one client, multiple segments)

#### 3. Enhanced Booking Form (13 Fields)
**Attendees:**
- Number of learners
- Number of facilitators
- Headcount calculation (learners + facilitators)

**Client Contact:**
- Contact person name
- Email address
- Phone number

**Catering:**
- Coffee/tea station (boolean)
- Morning catering (none/pastry/sandwiches)
- Lunch catering (none/self-catered/in-house)
- Catering notes

**Supplies:**
- Stationery needed (boolean)
- Water bottles quantity

**Devices:**
- Devices needed count
- Device type preference (any/laptops/desktops)

#### 4. Calendar View with Indicators
- Excel-style grid (days as rows, rooms as columns)
- Week and Month view modes
- Color-coded indicators:
  - 🟢 Today (green)
  - 🟣 Weekend (purple)
  - 🔵 Weekday (blue)
- Headcount display (learners + facilitators)
- Catering indicators: ☕ 🥪 🍽️ 📚 💻
- Long-term office display (A302, A303, Vision)
- Horizontal scrolling for many rooms

#### 5. Device Management (IT Staff)
- Manual device assignment by serial number
- Off-site rental tracking with full contact details
- Conflict detection and reallocation
- Alternative device suggestions
- Stock level monitoring with low stock alerts

#### 6. Dynamic Pricing Catalog (v2.2.3)
- Room pricing (daily/weekly/monthly rates)
- Device category pricing (collective, not individual)
- Catering and supplies pricing
- Pricing tiers (standard/premium/discounted)
- Role-based access (admin/it_admin only)

#### 7. Notifications System
- IT Boss notifications: Low stock, off-site conflicts, overdue returns
- Room Boss notifications: Booking requests, conflict alerts
- In-app notification center with filtering
- Mark as read/unread functionality
- Daily summary statistics

#### 8. Excel Import (v2.2.3)
- Bulk import from "Colab 2026 Schedule.xlsx"
- Pattern parsing: "Client 25+1", "25 + 18 laptops"
- Room mapping: 24 rooms from Excel columns
- Long-term rental handling (Siyaya, Melissa)
- Auto-approved status for imports
- 713 bookings imported successfully

#### 9. Authentication & Authorization
- Database-backed bcrypt password hashing
- 6 user roles with granular permissions
- Session management with logout
- Role-based menu access control

---

## 👥 User Roles (Corrected Hierarchy)

### Admin Roles (Full Access + Pricing)

#### 1. Admin (`admin`)
- **Access:** Full system access
- **Pricing:** ✅ Yes
- **Functions:** User management, system configuration, all features

#### 2. Room Boss (`training_facility_admin`)
- **Access:** Dashboard, Notifications, Calendar, Bookings, Pricing, Pending Approvals, Inventory
- **Pricing:** ✅ Yes
- **Primary Function:** Assign rooms to pending bookings (Ghost Inventory workflow)
- **Note:** This IS an admin role despite the name

#### 3. IT Boss (`it_rental_admin`)
- **Access:** Same as Room Boss
- **Pricing:** ✅ Yes
- **Primary Function:** Device assignment from queue
- **Note:** This IS an admin role despite the name

### Staff Roles (Limited Access, No Pricing)

#### 4. Training Facility Admin Viewer (`training_facility_admin_viewer`)
- **Access:** Calendar, Bookings, Pricing (view-only), Inventory
- **Pricing:** ❌ No
- **Permissions:** View-only, NO approval/assignment privileges
- **Note:** Cannot assign rooms or approve bookings

#### 5. Kitchen Staff (`kitchen_staff`)
- **Access:** Calendar view ONLY
- **Pricing:** ❌ No
- **Purpose:** Monitor catering needs and headcounts
- **What They See:** Calendar with catering requirements

#### 6. Staff (`staff`) - Legacy
- **Access:** Calendar, New Room Booking
- **Pricing:** ❌ No
- **Function:** Create bookings (always goes to pending)
- **Status:** Being deprecated

---

## 🗄️ Complete Database Schema

### Core Tables

#### bookings (Master Table)
```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id),  -- NULL for pending
    booking_period TSTZRANGE NOT NULL,    -- UTC, 07:30-16:30 daily
    client_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending', -- Pending → Room Assigned → Confirmed
    tenant_id tenant_type DEFAULT 'TECH', -- TECH/TRAINING
    
    -- Phase 3: Attendees
    num_learners INTEGER DEFAULT 0,
    num_facilitators INTEGER DEFAULT 0,
    headcount INTEGER DEFAULT 0,
    
    -- Phase 3: Client Contact
    client_contact_person VARCHAR(100),
    client_email VARCHAR(100),
    client_phone VARCHAR(20),
    
    -- Phase 3: Catering
    coffee_tea_station BOOLEAN DEFAULT FALSE,
    morning_catering VARCHAR(50),
    lunch_catering VARCHAR(50),
    catering_notes TEXT,
    
    -- Phase 3: Supplies
    stationery_needed BOOLEAN DEFAULT FALSE,
    water_bottles INTEGER DEFAULT 0,
    
    -- Phase 3: Devices
    devices_needed INTEGER DEFAULT 0,
    device_type_preference VARCHAR(50),
    
    -- Additional
    room_boss_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT no_overlapping_bookings 
        EXCLUDE USING gist (room_id WITH =, booking_period WITH &&)
        WHERE (room_id IS NOT NULL),
    CONSTRAINT chk_morning_catering 
        CHECK (morning_catering IN ('none', 'pastry', 'sandwiches')),
    CONSTRAINT chk_lunch_catering 
        CHECK (lunch_catering IN ('none', 'self_catered', 'in_house'))
);
```

#### rooms (24 Rows)
```sql
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    max_capacity INTEGER NOT NULL,        -- CORRECT: max_capacity (not capacity)
    room_type VARCHAR(50),
    has_devices BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    parent_room_id INTEGER REFERENCES rooms(id)
);
```

**Room Names:** Excellence, Inspiration, Honesty, Gratitude, Ambition, Perseverance, Courage, Possibilities, Motivation, A302, A303, Success 10, Respect 10, Innovation (12), Dedication, Integrity (15), Empower, Focus, Growth, Wisdom (8), Vision, Potential, Synergy, Ambition+Perseverance

#### devices (110+ Rows)
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

#### device_categories
```sql
CREATE TABLE device_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL  -- 'Laptop', 'Desktop'
);
```

#### booking_device_assignments
```sql
CREATE TABLE booking_device_assignments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id),
    device_id INTEGER REFERENCES devices(id),
    device_category_id INTEGER REFERENCES device_categories(id),
    assigned_by VARCHAR(255),
    assigned_at TIMESTAMP DEFAULT NOW(),
    is_offsite BOOLEAN DEFAULT FALSE,
    notes TEXT,
    assignment_type VARCHAR(20) DEFAULT 'manual',
    quantity INTEGER DEFAULT 1
);
```

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
    rental_form_generated BOOLEAN DEFAULT FALSE
);
```

#### pricing_catalog (NEW v2.2.3)
```sql
CREATE TABLE pricing_catalog (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,  -- 'room', 'device_category', 'catering'
    item_id INTEGER,
    item_name VARCHAR(255),
    daily_rate DECIMAL(10,2),
    weekly_rate DECIMAL(10,2),
    monthly_rate DECIMAL(10,2),
    unit VARCHAR(50),
    pricing_tier VARCHAR(20) DEFAULT 'standard',
    effective_date DATE DEFAULT CURRENT_DATE,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### notification_log
```sql
CREATE TABLE notification_log (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50),
    message TEXT,
    recipients TEXT[],
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### users
```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL
);
```

---

## 📁 Complete File Structure

### Project Root (`~/Projects/colab_erp/`)
```
colab_erp/
├── src/                           # Source code
│   ├── app.py                    # Main Streamlit application (orchestration only)
│   ├── auth.py                   # bcrypt authentication
│   ├── db.py                     # Database connection & queries
│   ├── booking_form.py           # Phase 3 enhanced booking form
│   ├── pricing_catalog.py        # Pricing catalog UI (admin only)
│   ├── import_excel_schedule.py  # Excel import script
│   ├── debug_booking.py          # Debug utilities
│   ├── test_booking_form.py      # Unit tests
│   ├── integration_test.py       # Integration tests
│   └── models/                   # Service layer (OOP classes)
│       ├── __init__.py
│       ├── booking_service.py    # Booking creation logic
│       ├── availability_service.py # Room/device availability
│       ├── room_approval_service.py # Ghost Inventory workflow
│       ├── device_manager.py     # Device assignment
│       ├── notification_manager.py # Notifications
│       └── pricing_service.py    # Dynamic pricing (v2.2.3)
│
├── migrations/                    # Database migrations
│   ├── v2.2_add_tenancy.sql      # Multi-tenancy support
│   ├── v2.4_device_assignment_system.sql
│   ├── v2.5_enhanced_booking_form.sql
│   └── v2.5.1_add_room_boss_notes.sql
│
├── infra/                         # Infrastructure
│   └── systemd/
│       └── colab_erp.service     # Systemd service config
│
├── docs/                          # Documentation
│   └── memory/                   # Session memory (this directory)
│       ├── SESSION_HISTORY.md    # Complete timeline
│       ├── DECISION_LOG.md       # Decision rationale
│       ├── CONTEXT_FOR_LLM.md    # RAG-optimized reference
│       ├── PROJECT_MEMORY.md     # This file
│       └── MEMORY_STRUCTURE.md   # Memory system docs
│
├── .streamlit/                    # Streamlit config
│   ├── config.toml               # App configuration
│   └── secrets.toml              # Database credentials
│
├── .secure_vault/                 # Legacy data (outside Git)
├── venv/                          # Virtual environment
├── requirements.txt               # Python dependencies
├── README.md                      # Current status & features
├── PRD.md                        # Product Requirements Document
├── ARCHITECTURE.md               # System architecture
├── CHANGELOG.md                  # Version history
├── BOOKING_FORM_RESOLUTION_SUMMARY.md
├── NUMPY_FIX_SUMMARY.md
├── NUMPY_TYPE_FIX.md
├── DEPLOYMENT_SUMMARY.md
├── HANDOVER_v2.2.md
├── SECURITY.md
├── SECURITY_AUDIT_REPORT_v2.2.0.md
└── API.md
```

### Memory System (`~/.moa_memory/`)
```
.moa_memory/
├── 00_README.md                   # Memory loading instructions
├── 01_architectural_principles.json # OOP mandate, HITL gate
├── 02_infrastructure.json         # Server connectivity
├── 03_projects_index.json         # 9 projects index
├── 04_colab_erp_structure.json    # Schema & structure
├── 05_coding_standards.md         # Python standards
├── 06_agents_manifest.json        # Agent registry
├── chief_documentation_officer.py # CDO agent code
├── future_phases_memory.json      # Phase planning
├── load_memory.py                 # Memory loader utility
├── user_roles_requirements.json   # Role definitions
│
├── logs/                          # CDO action logs
│   ├── 2026-02-22.log
│   ├── 2026-02-23_*.json
│   ├── 2026-02-27.log
│   └── PHASE_1_COMPLETE_DOCUMENTATION.json
│
├── decisions/                     # HITL decisions
│   ├── 2026-02-22_decision_*.json
│   └── 2026-02-27_decision_*.json
│
├── errors/                        # Error tracking
├── thoughts/                      # Reasoning logs
├── meetings/                      # User interactions
│
└── sessions/                      # Session summaries
    ├── session_2026-02-24_1912.md
    ├── session_2026-02-26_final.md
    └── session_2026-02-27_2332.md
```

---

## 🔄 Complete Session History Summary

| # | Date | Duration | Focus | Status |
|---|------|----------|-------|--------|
| 1 | Feb 22 | ~1.5h | Foundation & Agent Setup | ✅ Complete |
| 2 | Feb 23 | ~3h | Phase 1: Calendar Overhaul | ✅ Complete |
| 3 | Feb 24 | 11min | Memory Sync & Investigation | ✅ Complete |
| 4 | Feb 25-26 | ~2 days | Ghost Inventory Implementation | ✅ Complete |
| 5 | Feb 27 | ~4h | Booking Form Resolution | ✅ Complete |
| 6 | Feb 28 | Various | Documentation & Polish | ✅ Complete |
| 7 | Current | - | Memory Documentation | 📝 In Progress |

---

## 🎯 Technical Debt & Roadmap

### Week 1 (Critical - In Progress)
- [ ] **CDO-003:** Convert silent error handling to exceptions
- [ ] **CDO-002:** Create deploy.sh automation script
- [ ] Add database indexes for calendar queries

### Month 1 (Foundation - Planned)
- [ ] Testing infrastructure (pytest)
- [ ] Repository pattern extraction
- [ ] Structured JSON logging
- [ ] Sentry error tracking

### Month 2-3 (Architecture - Planned)
- [ ] API layer (FastAPI)
- [ ] Caching layer (Redis)
- [ ] Database read replica

### Phase 4 (Future)
- [ ] Mobile app support
- [ ] Third-party calendar integrations
- [ ] Advanced analytics
- [ ] AI-powered recommendations

---

## 📚 Documentation Inventory

### Primary Documentation
| Document | Size | Purpose |
|----------|------|---------|
| PRD.md | 50KB | Complete requirements v1.1.0 |
| ARCHITECTURE.md | 40KB | System design & data flow |
| README.md | 20KB | Current status & features |
| CHANGELOG.md | 15KB | Version history |
| BOOKING_FORM_RESOLUTION_SUMMARY.md | 10KB | Issue resolution |

### Memory Documentation
| Document | Size | Purpose |
|----------|------|---------|
| 00_README.md | 5KB | Memory loading protocol |
| SESSION_HISTORY.md | 15KB | Complete timeline |
| DECISION_LOG.md | 12KB | Decision rationale |
| CONTEXT_FOR_LLM.md | 10KB | RAG-optimized reference |
| PROJECT_MEMORY.md | 20KB | This comprehensive file |

### Technical Reviews (150KB total)
- SRE_REVIEW_COLAB_ERP.md
- SENIOR_SOFTWARE_DEV_REVIEW.md
- SYSTEMS_ARCHITECT_REVIEW.md
- TECHNICAL_REVIEW_SYNTHESIS.md
- MASTER_SYSTEM_DOCUMENT.md

---

## 🐛 Issue History (Resolved)

| Issue ID | Description | Date | Resolution |
|----------|-------------|------|------------|
| CDO-001 | Column name mismatch (capacity vs max_capacity) | Feb 25 | Fixed get_all_rooms() |
| CDO-002 | No deployment automation | Feb 26 | deploy.sh planned |
| CDO-003 | Silent error handling | Feb 26 | Convert to exceptions |
| CDO-004 | LLM context loss | Feb 26 | Memory system enhanced |
| CDO-005 | Implementation drift | Feb 26 | Better documentation |
| CDO-006 | App corruption (main() function) | Feb 24 | Rolled back, fixed |
| - | numpy.int64 type conversion | Feb 27 | Added int() conversion |
| - | BookingService initialization | Feb 27 | Added AvailabilityService |
| - | created_by field error | Feb 27 | Removed from form |

---

## 🔐 Security Model

### Authentication
- bcrypt password hashing with salt
- Database-backed (not secrets.toml)
- Session management with timeout

### Authorization (RBAC)
- 6 user roles with granular permissions
- Pricing catalog restricted to admin roles
- Role-based menu access control

### Network Security
- Tailscale VPN required for access
- No public internet exposure
- WireGuard-based mesh network

### Data Security
- Parameterized queries (SQL injection prevention)
- Connection pooling with proper cleanup
- No hardcoded credentials
- .secure_vault for sensitive data (outside Git)

---

## 💡 Key Architectural Principles

1. **OOP Mandate:** ALL logic in Classes/Objects, no procedural code
2. **Library Structure:** main.py orchestration only, zero business logic
3. **HITL Gate:** THOUGHT → PROPOSED ACTION → WAIT FOR AUTH
4. **Dual Memory:** .cline/ for tool state, .moa_memory/ for context
5. **CDO Logging:** Autonomous documentation of ALL activities
6. **UTC Standard:** All datetimes in UTC, convert for display
7. **ACID Compliance:** Database transactions with rollback
8. **Global Constraints:** Exclusion constraints prevent double-booking

---

## 📞 Contact & Access

### Server Access
```bash
# SSH (passwordless with ed25519 key)
ssh colab  # Alias for colabtechsolutions@100.69.57.77

# Check status
curl http://100.69.57.77:8501

# View logs
ssh colab "sudo journalctl -u colab_erp -n 50"
```

### Database Access
```bash
# Connect via SSH tunnel
ssh colab "psql -d colab_erp -U colabtechsolutions -c 'SELECT version();'"
```

---

**Document Version:** 1.0.0  
**Last Updated:** Current Session  
**Maintained by:** Chief Documentation Officer (CDO-001)  
**Next Review:** Weekly or per major change
