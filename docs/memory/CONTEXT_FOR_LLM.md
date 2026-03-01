# Context for LLM - RAG-Optimized Reference

**Purpose:** Quick-reference context optimized for LLM consumption  
**Target Audience:** Future LLM instances (Kimi, Claude, etc.)  
**Format:** Structured for RAG (Retrieval-Augmented Generation) systems  
**Last Updated:** Current Session  

---

## 🎯 TL;DR - Essential Context

**Project:** Colab ERP v2.2.3  
**Type:** Streamlit-based room booking & device management system  
**Status:** Production Ready (807+ bookings, 24 rooms, 110+ devices)  
**Location:** `~/Projects/colab_erp`  
**Server:** `ssh colab` → 100.69.57.77 (Tailscale VPN)  
**URL:** http://100.69.57.77:8501  

**Key Memory Files:**
- `~/.moa_memory/00_README.md` - Loading instructions
- `~/.moa_memory/01_architectural_principles.json` - OOP mandate, HITL gate
- `~/.moa_memory/04_colab_erp_structure.json` - Schema & file structure
- `~/Projects/colab_erp/PRD.md` - Complete requirements
- `~/Projects/colab_erp/ARCHITECTURE.md` - System architecture
- `~/Projects/colab_erp/README.md` - Current status & features

**Critical Rules:**
1. **OOP Mandate:** ALL logic in Classes, no procedural code
2. **HITL Gate:** THOUGHT → PROPOSED ACTION → WAIT FOR AUTH
3. **main.py:** Orchestration ONLY, zero business logic
4. **Never proceed without user authorization**

---

## 🏗️ System Architecture (Simplified)

```
User → Tailscale VPN → Streamlit (100.69.57.77:8501) → PostgreSQL
```

**Stack:**
- Frontend: Streamlit 1.28+
- Backend: Python 3.9+ (Classes ONLY)
- Database: PostgreSQL 16+
- Auth: bcrypt (database-backed)
- Connection Pool: 20 connections

**Service Layer:**
```python
src/models/
├── booking_service.py        # Booking creation (13 Phase 3 fields)
├── availability_service.py   # Room/device availability
├── room_approval_service.py # Ghost Inventory workflow
├── device_manager.py       # Device assignment
├── notification_manager.py # IT Boss & Room Boss alerts
└── pricing_service.py      # Dynamic pricing (v2.2.3)
```

---

## 📊 Database Schema (Core Tables)

### bookings (807+ rows)
```sql
id SERIAL PRIMARY KEY
room_id INTEGER REFERENCES rooms(id)  -- NULL for pending
booking_period TSTZRANGE NOT NULL    -- UTC timezone
client_name VARCHAR(255) NOT NULL
status VARCHAR(20) DEFAULT 'Pending'  -- Pending → Confirmed
tenant_id tenant_type DEFAULT 'TECH'   -- TECH/TRAINING

-- Phase 3 Fields
num_learners INTEGER DEFAULT 0
num_facilitators INTEGER DEFAULT 0
headcount INTEGER DEFAULT 0
client_contact_person VARCHAR(100)
client_email VARCHAR(100)
client_phone VARCHAR(20)
coffee_tea_station BOOLEAN DEFAULT FALSE
morning_catering VARCHAR(50)  -- 'none', 'pastry', 'sandwiches'
lunch_catering VARCHAR(50)    -- 'none', 'self_catered', 'in_house'
catering_notes TEXT
stationery_needed BOOLEAN DEFAULT FALSE
water_bottles INTEGER DEFAULT 0
devices_needed INTEGER DEFAULT 0
device_type_preference VARCHAR(50)  -- 'any', 'laptops', 'desktops'

-- Constraints
EXCLUDE USING gist (room_id WITH =, booking_period WITH &&)
    WHERE (room_id IS NOT NULL)  -- Global collision prevention
```

### rooms (24 rows)
```sql
id SERIAL PRIMARY KEY
name VARCHAR(255) NOT NULL           -- e.g., "Excellence", "A302"
max_capacity INTEGER NOT NULL        -- CORRECT COLUMN NAME
room_type VARCHAR(50)                -- Training, Office
has_devices BOOLEAN DEFAULT FALSE
is_active BOOLEAN DEFAULT TRUE
```

### devices (110+ rows)
```sql
id SERIAL PRIMARY KEY
serial_number VARCHAR(255) UNIQUE NOT NULL
name VARCHAR(255)
category_id INTEGER REFERENCES device_categories(id)
status VARCHAR(20) DEFAULT 'available'  -- 'available', 'assigned', 'offsite', 'maintenance'
```

### pricing_catalog (NEW v2.2.3)
```sql
id SERIAL PRIMARY KEY
item_type VARCHAR(50) NOT NULL       -- 'room', 'device_category', 'catering'
item_id INTEGER                      -- FK to rooms or device_categories
item_name VARCHAR(255)             -- For catering items
daily_rate DECIMAL(10,2)
weekly_rate DECIMAL(10,2)
monthly_rate DECIMAL(10,2)
pricing_tier VARCHAR(20) DEFAULT 'standard'  -- 'standard', 'premium', 'discounted'
```

---

## 👥 User Roles & Permissions (CORRECTED)

| Role | Type | Pricing | Access |
|------|------|---------|--------|
| `admin` | Admin | ✅ Yes | Full system |
| `training_facility_admin` | Admin | ✅ Yes | Room Boss - Room assignment |
| `it_rental_admin` | Admin | ✅ Yes | IT Boss - Device assignment |
| `training_facility_admin_viewer` | Staff | ❌ No | View-only (NO approval privileges) |
| `kitchen_staff` | Limited | ❌ No | Calendar view ONLY |
| `staff` | Legacy | ❌ No | Create pending bookings |

**Key Correction:** Room Boss and IT Boss ARE admin roles with pricing access.

---

## 🔄 Key Workflows

### Ghost Inventory (Pending → Confirmed)
```
Staff/Client creates booking
    │
    ▼
room_id = NULL
status = 'Pending'
    │
    ▼
Room Boss sees in Pending Approvals
    │
    ▼
Room Boss assigns room (with conflict check)
    │
    ▼
status = 'Room Assigned' → 'Confirmed'
room_id = assigned_room
```

### Device Assignment
```
Booking confirmed with devices_needed > 0
    │
    ▼
IT Boss sees in Device Assignment Queue
    │
    ▼
IT Boss selects available devices by serial number
    │
    ▼
Device status = 'assigned'
booking_device_assignments record created
```

---

## ⚠️ Known Issues & Technical Debt

### Critical (Week 1)
- **CDO-003:** Silent error handling → Convert to exceptions
- **CDO-002:** No deployment automation → Create deploy.sh
- **Missing:** Database indexes for calendar queries

### Planned (Month 1)
- Testing infrastructure (pytest)
- Repository pattern extraction
- Structured logging (JSON)
- Sentry integration

### Future (Month 2-3)
- API layer (FastAPI)
- Caching layer (Redis)
- Read replica

---

## 📁 Important File Locations

### Project Files
```
~/Projects/colab_erp/
├── src/
│   ├── app.py                    # Main Streamlit app
│   ├── auth.py                   # bcrypt authentication
│   ├── db.py                     # Database connection pool
│   ├── booking_form.py           # Phase 3 booking form
│   ├── pricing_catalog.py        # Pricing UI (admin only)
│   ├── import_excel_schedule.py  # Excel import
│   └── models/
│       ├── booking_service.py
│       ├── availability_service.py
│       ├── room_approval_service.py
│       ├── device_manager.py
│       ├── notification_manager.py
│       └── pricing_service.py
├── migrations/                   # SQL migrations
├── PRD.md                       # Requirements (1,500+ lines)
├── ARCHITECTURE.md              # System architecture
├── README.md                    # Current status
└── CHANGELOG.md                 # Version history
```

### Memory Files
```
~/.moa_memory/
├── 00_README.md                 # Loading instructions
├── 01_architectural_principles.json  # OOP, HITL
├── 02_infrastructure.json       # SSH, Tailscale
├── 03_projects_index.json       # 9 projects
├── 04_colab_erp_structure.json  # Schema details
├── 05_coding_standards.md       # Python standards
├── 06_agents_manifest.json      # CDO-001
├── logs/                        # Action logs
├── decisions/                   # HITL decisions
├── errors/                      # Error tracking
├── thoughts/                    # Reasoning logs
└── sessions/                    # Session summaries
```

---

## 🔧 Common Commands

### Check System Status
```bash
# Check if app is running
curl -s http://100.69.57.77:8501 | head -5

# Check service status
ssh colab "sudo systemctl status colab_erp"

# View logs
ssh colab "sudo journalctl -u colab_erp -n 50"
```

### Deployment (Current - Manual)
```bash
cd ~/Projects/colab_erp

# 1. Verify syntax
python3 -m py_compile src/app.py

# 2. Copy to server
scp -r src/ colab:~/colab_erp/

# 3. Restart service
ssh colab "sudo systemctl restart colab_erp"

# 4. Verify
sleep 2 && curl -s http://100.69.57.77:8501 | head -1
```

### Database Operations
```bash
# Connect to database
ssh colab "psql -d colab_erp -U colabtechsolutions -c 'SELECT COUNT(*) FROM bookings;'"

# Check room count
ssh colab "psql -d colab_erp -U colabtechsolutions -c 'SELECT COUNT(*) FROM rooms;'"

# Check device count
ssh colab "psql -d colab_erp -U colabtechsolutions -c 'SELECT COUNT(*) FROM devices;'"
```

---

## 🐛 Common Issues & Fixes

### Issue: "No rooms found" in admin selection
**Cause:** Query using wrong column name (`capacity` vs `max_capacity`)  
**Fix:** Updated `get_all_rooms()` to use `max_capacity`  
**File:** `src/models/availability_service.py`  
**Status:** ✅ Fixed 2026-02-25

### Issue: Calendar showing empty despite 807 bookings
**Cause:** datetime64[ns, UTC] vs Python date comparison failing  
**Fix:** Convert to `datetime.date` using `.dt.date`  
**File:** `src/db.py`, `src/app.py`  
**Status:** ✅ Fixed 2026-02-23

### Issue: "can't adapt type 'numpy.int64'"
**Cause:** Pandas DataFrame returns numpy.int64 instead of Python int  
**Fix:** Added `int(exclude_booking_id)` conversion  
**File:** `src/models/availability_service.py`  
**Status:** ✅ Fixed 2026-02-27

### Issue: BookingService missing availability_service
**Cause:** Missing initialization in constructor  
**Fix:** Added `self.availability_service = AvailabilityService()`  
**File:** `src/models/booking_service.py`  
**Status:** ✅ Fixed 2026-02-27

---

## 📚 Documentation Quick Links

| Document | Purpose | Size |
|----------|---------|------|
| `~/.moa_memory/00_README.md` | Memory loading protocol | 5KB |
| `~/Projects/colab_erp/PRD.md` | Requirements (v1.1.0) | 50KB |
| `~/Projects/colab_erp/ARCHITECTURE.md` | System design | 40KB |
| `~/Projects/colab_erp/README.md` | Current status | 20KB |
| `~/Projects/colab_erp/CHANGELOG.md` | Version history | 15KB |
| `~/Projects/colab_erp/BOOKING_FORM_RESOLUTION_SUMMARY.md` | Issue resolution | 10KB |

---

## 🎓 What Worked Well

1. **Memory System:** `.moa_memory/` preserved context across sessions
2. **CDO Agent:** Autonomous logging provided complete audit trail
3. **HITL Protocol:** User authorization prevented accidents
4. **Git History:** Easy rollback when issues occurred
5. **Documentation:** PRD and ARCHITECTURE enabled quick context recovery

## ⚠️ What Didn't Work

1. **Silent Error Handling:** Print statements hid issues → Now converting to exceptions
2. **Large replace_in_file:** 209-line replacement corrupted main() → Now limit to 30 lines
3. **Manual Deployment:** Forgotten SCP steps caused confusion → Now creating deploy.sh
4. **Role Confusion:** Multiple role names caused permission issues → Now clarified

---

## 🚀 Next Steps (If Asked)

### Immediate (If User Asks)
1. Address silent error handling (CDO-003)
2. Create deploy.sh automation script
3. Add database indexes for performance

### Short-term (If User Asks)
1. Implement pytest testing infrastructure
2. Extract repository pattern from services
3. Add structured JSON logging

### Future (If User Asks)
1. Begin FastAPI layer for mobile support
2. Implement Redis caching
3. Set up Sentry monitoring

---

## 💡 Pro Tips for Future LLMs

1. **Always read `~/.moa_memory/00_README.md` first** - Contains loading protocol
2. **Check `~/.moa_memory/session_*.md` for recent context** - Last session summary
3. **Verify git log** - `git log --oneline -10` shows recent commits
4. **Test SSH before deploying** - `ssh colab "echo 'Connected'"`
5. **Use HITL for all changes** - Never write without authorization
6. **Follow OOP mandate** - Classes only, no procedural code
7. **Check PRD before implementing** - Requirements are documented
8. **Remember: Room Boss = Admin** - Has pricing access

---

**Document Version:** 1.0.0  
**Format:** RAG-Optimized  
**Token Estimate:** ~2,500 tokens  
**Last Updated:** Current Session  
**Maintained by:** Chief Documentation Officer (CDO-001)
