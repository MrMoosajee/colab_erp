# Decision Log - Colab ERP Development

**Project:** Colab ERP v2.2.3  
**Purpose:** Document all architectural and implementation decisions with rationale  
**Location:** `/home/shuaibadams/Projects/colab_erp/docs/memory/`  

---

## 🏛️ Architectural Decisions

### ADR-001: OOP Mandate (Strict)
**Date:** 2026-02-22  
**Status:** ✅ Accepted - Enforced  
**Decision:** ALL logic must be encapsulated in Classes and Objects. No procedural scripting.  

#### Rationale
- Maintainability: Classes provide clear structure and boundaries
- Testability: Object-oriented code is easier to unit test
- Architectural Integrity: Consistent patterns across codebase
- Type Safety: Classes enable better type hinting

#### Implementation
```python
# ✅ CORRECT
class BookingService:
    def __init__(self, db_pool: ConnectionPool):
        self._db_pool = db_pool
    
    def create_booking(self, ...) -> Booking:
        pass

# ❌ PROHIBITED
def create_booking(room_id, start, end):
    conn = get_connection()
    # ... procedural logic
```

#### Consequences
- ✅ Better code organization
- ✅ Easier to maintain and extend
- ⚠️ Requires discipline from all contributors
- ⚠️ Learning curve for procedural programmers

---

### ADR-002: Library Structure - main.py Orchestration Only
**Date:** 2026-02-22  
**Status:** ✅ Accepted - Enforced  
**Decision:** `main.py` (or equivalent entry point) must contain ZERO business logic. All functionality in external libraries.  

#### Rationale
- Separation of Concerns: Entry point only coordinates
- Testability: Business logic can be tested independently
- Reusability: Library modules can be imported elsewhere
- Clarity: Clear distinction between orchestration and implementation

#### Implementation
```python
# main.py - ✅ CORRECT
def main():
    config = Settings.from_env()
    db_pool = ConnectionPool(config.database_url)
    booking_service = BookingService(db_pool)
    result = booking_service.create_booking(...)

# main.py - ❌ PROHIBITED
def create_booking_logic(room_id, start, end):  # NO!
    # Business logic in main - VIOLATION
```

#### Consequences
- ✅ Clean architecture
- ✅ Easy to test business logic
- ✅ Can swap UIs without changing logic
- ⚠️ More files to manage

---

### ADR-003: HITL Gate (Human-in-the-Loop)
**Date:** 2026-02-22  
**Status:** ✅ Accepted - Absolute  
**Decision:** Never write files or execute commands without explicit user authorization.  

#### Rationale
- Safety: Prevents accidental destructive operations
- Trust: User maintains control over system changes
- Accountability: All changes are intentional
- Recovery: Reduces risk of corruption

#### Implementation
```python
class HITLGate:
    def propose_action(self, thought: str, proposed_action: str, impact: str) -> bool:
        # Present to user and await authorization
        # Blocks until response received
        pass

# Usage
gate = HITLGate()
if not gate.propose_action(
    thought="Database migration required",
    proposed_action="Execute migrations/v2.3_schema.sql",
    impact="Will alter bookings table"
):
    raise AuthorizationDenied("User rejected migration")
```

#### Consequences
- ✅ User maintains control
- ✅ Prevents accidents
- ⚠️ Slower workflow (requires user input)
- ⚠️ Cannot run fully automated

---

### ADR-004: Dual Memory System
**Date:** 2026-02-22  
**Status:** ✅ Accepted  
**Decision:** Maintain two memory systems: `.cline/` for Cline tool state, `.moa_memory/` for MOA architectural context.  

#### Rationale
- Tool Separation: Cline manages its own state
- Context Preservation: MOA memory survives model switches
- Structured Access: JSON files for programmatic access
- Audit Trail: Complete history of decisions and actions

#### Implementation
```
~/.cline/
├── data/
│   ├── state/taskHistory.json    # Task history
│   ├── tasks/{id}/               # Per-task data
│   └── logs/                     # Cline logs

~/.moa_memory/
├── 01_architectural_principles.json
├── 02_infrastructure.json
├── 03_projects_index.json
├── 04_colab_erp_structure.json
├── 05_coding_standards.md
├── 06_agents_manifest.json
├── logs/                         # CDO action logs
├── decisions/                    # HITL decisions
├── errors/                       # Error tracking
└── sessions/                     # Session summaries
```

#### Consequences
- ✅ Complete context preservation
- ✅ Survives model switches
- ✅ Structured programmatic access
- ⚠️ Two systems to maintain
- ⚠️ Potential for divergence

---

### ADR-005: CDO Agent (Chief Documentation Officer)
**Date:** 2026-02-22  
**Status:** ✅ Accepted - Active  
**Decision:** Create dedicated sub-agent for autonomous logging of ALL activities.  

#### Rationale
- Audit Trail: Complete record of all actions
- Accountability: Track who did what and when
- Debugging: Historical context for issues
- Handoff: Enable session continuity

#### Implementation
```python
from chief_documentation_officer import get_cdo

cdo = get_cdo()
cdo.log_action("file_write", "Updated app.py", metadata={"lines": 5})
cdo.log_decision("user_authorized", "Deploy fix", authorized_by="user")
cdo.log_error("connection_failed", "SSH timeout", retry_count=3)
```

#### Consequences
- ✅ Complete audit trail
- ✅ Historical debugging capability
- ✅ Session continuity
- ⚠️ Overhead of logging calls
- ⚠️ Storage growth over time

---

## 🗄️ Database Decisions

### DB-001: PostgreSQL with Exclusion Constraints
**Date:** 2026-02-22  
**Status:** ✅ Accepted  
**Decision:** Use PostgreSQL with EXCLUDE constraints for collision prevention.  

#### Rationale
- ACID Compliance: Reliable transaction handling
- Exclusion Constraints: Native double-booking prevention
- tstzrange: Timezone-aware booking periods
- Mature: Well-supported, well-documented

#### Implementation
```sql
CONSTRAINT no_overlapping_bookings 
    EXCLUDE USING gist (room_id WITH =, booking_period WITH &&)
    WHERE (room_id IS NOT NULL)
```

#### Consequences
- ✅ Native collision prevention
- ✅ Timezone-aware
- ✅ Reliable and performant
- ⚠️ PostgreSQL-specific (not portable)

---

### DB-002: Multi-Tenancy with Shared Physics
**Date:** 2026-01-20 (v2.2.0)  
**Status:** ✅ Accepted  
**Decision:** TECH and TRAINING divisions share physical assets with logical separation. Exclusion constraints remain GLOBAL.  

#### Rationale
- Reality: Same rooms can't be double-booked regardless of tenant
- Simplicity: Single constraint prevents all conflicts
- Reporting: Can still filter by tenant_id
- Data Integrity: Physical constraints enforced

#### Implementation
```sql
-- tenant_id for logical separation
ALTER TABLE bookings ADD COLUMN tenant_id tenant_type NOT NULL DEFAULT 'TECH';

-- But exclusion constraint ignores tenant_id (shared physics)
CONSTRAINT no_overlapping_bookings 
    EXCLUDE USING gist (room_id WITH =, booking_period WITH &&)
```

#### Consequences
- ✅ Prevents real double-bookings
- ✅ Simple constraint model
- ✅ Can still report by tenant
- ⚠️ Cannot book same room for both tenants (correct behavior)

---

### DB-003: Connection Pooling (20 Connections)
**Date:** 2026-02-22  
**Status:** ✅ Accepted  
**Decision:** Use psycopg2.pool.ThreadedConnectionPool with 20 max connections.  

#### Rationale
- Performance: Reuse connections instead of creating new
- Concurrency: Support multiple simultaneous users
- Resource Limits: Prevent connection exhaustion
- Scalability: Current scale (5-10 users) well within limits

#### Implementation
```python
from psycopg2 import pool

self._pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    host=DB_HOST,
    ...
)
```

#### Consequences
- ✅ Better performance
- ✅ Connection reuse
- ✅ Prevents exhaustion
- ⚠️ Need proper cleanup (putconn)

---

## 🎨 UI/UX Decisions

### UI-001: Excel-Style Calendar Grid
**Date:** 2026-02-23  
**Status:** ✅ Accepted  
**Decision:** Transform calendar from list view to Excel-style grid with days as rows, rooms as columns.  

#### Rationale
- Familiarity: Users know Excel format
- Density: More information in single view
- Scanning: Easy to scan across rooms for a date
- Professional: Matches business user expectations

#### Implementation
- Custom HTML/CSS grid (not Streamlit widgets)
- 140px × 90px cells
- Horizontal scrolling for many rooms
- Color coding: Today (green), Weekend (purple), Weekday (blue)

#### Consequences
- ✅ Professional appearance
- ✅ High information density
- ✅ Familiar to users
- ⚠️ Custom CSS maintenance
- ⚠️ Not responsive (fixed widths)

---

### UI-002: Ghost Inventory Workflow
**Date:** 2026-02-25  
**Status:** ✅ Accepted  
**Decision:** Allow bookings without immediate room assignment (Pending → Room Assigned → Confirmed).  

#### Rationale
- Flexibility: Staff can create bookings without knowing room
- Approval: Room Boss controls room assignment
- Workflow: Matches real business process
- Safety: Prevents unauthorized room bookings

#### Implementation
```python
# Staff always creates pending
if role in ['staff', 'client']:
    status = 'Pending'
    room_id = None

# Admin can choose
if role == 'admin':
    if admin_selects_room:
        status = 'Confirmed'
        room_id = selected_room
    else:
        status = 'Pending'
        room_id = None
```

#### Consequences
- ✅ Flexible booking process
- ✅ Room Boss approval control
- ✅ Prevents unauthorized bookings
- ⚠️ More complex state management
- ⚠️ Requires pending queue UI

---

### UI-003: Manual Device Assignment
**Date:** 2026-02-24  
**Status:** ✅ Accepted  
**Decision:** IT Staff manually assign specific devices by serial number (not auto-assigned).  

#### Rationale
- Control: IT Staff want full control over device selection
- Tracking: Serial numbers enable precise tracking
- Flexibility: Can choose specific devices for specific needs
- Learning: Data logged for future AI automation

#### Implementation
- IT Staff sees list of available serial numbers
- Multi-select interface
- Assignment recorded with timestamp and user
- Off-site rentals tracked separately

#### Consequences
- ✅ Full IT Staff control
- ✅ Precise tracking
- ✅ Data for future AI
- ⚠️ More manual work for IT Staff
- ⚠️ Slower than auto-assignment

---

## 🔧 Technical Decisions

### TECH-001: Timezone Handling (UTC Standard)
**Date:** 2026-02-25  
**Status:** ✅ Accepted  
**Decision:** Store all datetimes in UTC, convert to local (Africa/Johannesburg) for display.  

#### Rationale
- Consistency: Single timezone in database
- Accuracy: No DST issues
- Portability: UTC is universal
- Clarity: Always know what timezone data is in

#### Implementation
```python
import pytz

# Store in UTC
utc_start = pytz.UTC.localize(naive_start)

# Display in local
local_tz = pytz.timezone('Africa/Johannesburg')
local_start = utc_start.astimezone(local_tz)
```

#### Consequences
- ✅ Consistent storage
- ✅ No DST issues
- ✅ Clear timezone semantics
- ⚠️ Conversion overhead
- ⚠️ Must remember to convert

---

### TECH-002: Pricing Catalog (Dynamic)
**Date:** 2026-02-28 (v2.2.3)  
**Status:** ✅ Accepted  
**Decision:** Create unified pricing_catalog table with item_type discriminator for rooms, devices, and catering.  

#### Rationale
- Flexibility: Easy to add new pricing types
- Consistency: Single table for all pricing
- Management: One interface for all pricing
- History: Effective dates enable historical pricing

#### Implementation
```sql
CREATE TABLE pricing_catalog (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,  -- 'room', 'device_category', 'catering'
    item_id INTEGER,                 -- FK to rooms or device_categories
    item_name VARCHAR(255),          -- For catering items
    daily_rate DECIMAL(10,2),
    weekly_rate DECIMAL(10,2),
    monthly_rate DECIMAL(10,2),
    pricing_tier VARCHAR(20) DEFAULT 'standard'
);
```

#### Consequences
- ✅ Flexible pricing model
- ✅ Single management interface
- ✅ Historical pricing support
- ⚠️ Nullable FKs (item_id)
- ⚠️ item_name for catering only

---

### TECH-003: Excel Import for Bulk Data
**Date:** 2026-02-28 (v2.2.3)  
**Status:** ✅ Accepted  
**Decision:** Import bookings from "Colab 2026 Schedule.xlsx" with pattern parsing.  

#### Rationale
- Migration: Bulk import historical data
- Efficiency: Faster than manual entry
- Accuracy: Reduces transcription errors
- Pattern Recognition: Parse "Client 25+1" format

#### Implementation
- Pattern: "Client 25+1" → 25 learners, 1 facilitator
- Pattern: "25 + 18 laptops" → headcount + devices
- Room mapping: Excel columns → database room IDs
- Long-term rentals: Auto-generate daily bookings

#### Consequences
- ✅ Fast bulk import
- ✅ Pattern recognition
- ✅ 713 bookings imported successfully
- ⚠️ Pattern dependent
- ⚠️ Requires Excel format consistency

---

### TECH-004: Silent Error Handling → Exceptions
**Date:** 2026-02-26  
**Status:** 🔄 In Progress  
**Decision:** Convert all silent error handling (print statements) to raised exceptions.  

#### Rationale
- Visibility: Errors should be visible, not hidden
- Debugging: Exceptions provide stack traces
- Reliability: Fail fast, don't continue in bad state
- Monitoring: Exceptions can be tracked

#### Implementation
```python
# ❌ BEFORE (Silent)
try:
    result = risky_operation()
except Exception as e:
    print(f"Error: {e}")  # Silent failure!
    return None

# ✅ AFTER (Explicit)
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise ServiceError(f"Could not complete operation: {e}") from e
```

#### Consequences
- ✅ Visible errors
- ✅ Better debugging
- ✅ Fail-fast behavior
- ⚠️ More crashes (but that's good!)
- ⚠️ Need proper error handling UI

---

## 👥 Role-Based Access Decisions

### RBAC-001: Role Definitions (Corrected)
**Date:** 2026-02-27  
**Status:** ✅ Accepted  
**Decision:** Clarify role hierarchy and permissions after confusion.  

#### Final Roles
| Role | Type | Pricing Access | Primary Function |
|------|------|----------------|------------------|
| admin | Admin | ✅ Yes | Full system access |
| training_facility_admin | Admin | ✅ Yes | Room assignment (Room Boss) |
| it_rental_admin | Admin | ✅ Yes | Device assignment (IT Boss) |
| training_facility_admin_viewer | Staff | ❌ No | View-only access |
| kitchen_staff | Limited | ❌ No | Calendar view only |
| staff | Legacy | ❌ No | Create pending bookings |

#### Rationale
- Clarity: Clear distinction between admin and staff
- Security: Pricing restricted to admin roles
- Workflow: Room Boss and IT Boss are admin-level
- Simplicity: Reduced role confusion

#### Consequences
- ✅ Clear permissions
- ✅ Pricing protected
- ✅ Workflow clear
- ⚠️ Role names are long
- ⚠️ Legacy 'staff' role exists

---

## 📱 Infrastructure Decisions

### INF-001: Tailscale VPN for Access
**Date:** 2026-02-22  
**Status:** ✅ Accepted  
**Decision:** Use Tailscale VPN for secure server access instead of public internet.  

#### Rationale
- Security: Zero-trust network mesh
- Simplicity: No firewall rules to manage
- Access: Works from anywhere
- Cost: Free for personal use

#### Implementation
- Local IP: 100.70.101.12
- Remote IP: 100.69.57.77 (colab server)
- SSH: `ssh colab` (passwordless with ed25519 key)
- Protocol: WireGuard-based mesh VPN

#### Consequences
- ✅ Secure access
- ✅ Works from anywhere
- ✅ No firewall configuration
- ⚠️ Requires Tailscale client
- ⚠️ Dependency on Tailscale service

---

### INF-002: Systemd Service for Production
**Date:** 2026-02-22  
**Status:** ✅ Accepted  
**Decision:** Run Streamlit app as systemd service for production deployment.  

#### Rationale
- Reliability: Auto-restart on failure
- Monitoring: Standard Linux service management
- Logging: Journald integration
- Boot: Auto-start on server boot

#### Implementation
```ini
[Unit]
Description=Colab ERP Streamlit Application
After=network.target

[Service]
Type=simple
User=colabtechsolutions
ExecStart=/home/colabtechsolutions/venv/bin/streamlit run src/app.py --server.port 8501
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Consequences
- ✅ Auto-restart
- ✅ Boot startup
- ✅ Standard management
- ⚠️ Single instance only
- ⚠️ No load balancing

---

## 🚫 Decisions Rejected

### REJ-001: Auto-Assignment of Devices
**Date:** 2026-02-24  
**Status:** ❌ Rejected  
**Decision:** Do NOT auto-assign devices. Keep manual assignment.  

#### Rationale for Rejection
- IT Staff want control over specific device selection
- Different devices have different capabilities
- Need to track serial numbers precisely
- Manual process provides data for future AI training

---

### REJ-002: Public Internet Deployment
**Date:** 2026-02-22  
**Status:** ❌ Rejected  
**Decision:** Do NOT expose app directly to public internet. Use VPN.  

#### Rationale for Rejection
- Security risk for business data
- No need for public access (internal tool)
- VPN provides adequate access for all users
- Reduces attack surface

---

### REJ-003: Microservices Architecture
**Date:** 2026-02-22  
**Status:** ❌ Rejected (for now)  
**Decision:** Keep monolithic architecture. Do NOT split into microservices.  

#### Rationale for Rejection
- Current scale (5-10 users) doesn't justify complexity
- Single developer maintenance is easier with monolith
- Deployment is simpler
- Can migrate to microservices later if needed

#### Future Reconsideration
- Revisit when: 100+ concurrent users
- Revisit when: Mobile app requirement
- Revisit when: Third-party integrations needed

---

## 📋 Decision Registry

| ID | Decision | Date | Status | Impact |
|----|----------|------|--------|--------|
| ADR-001 | OOP Mandate | 2026-02-22 | ✅ Accepted | High |
| ADR-002 | main.py Orchestration Only | 2026-02-22 | ✅ Accepted | High |
| ADR-003 | HITL Gate | 2026-02-22 | ✅ Accepted | Critical |
| ADR-004 | Dual Memory System | 2026-02-22 | ✅ Accepted | High |
| ADR-005 | CDO Agent | 2026-02-22 | ✅ Accepted | Medium |
| DB-001 | PostgreSQL Exclusion Constraints | 2026-02-22 | ✅ Accepted | High |
| DB-002 | Multi-Tenancy Shared Physics | 2026-01-20 | ✅ Accepted | High |
| DB-003 | Connection Pooling (20) | 2026-02-22 | ✅ Accepted | Medium |
| UI-001 | Excel-Style Calendar | 2026-02-23 | ✅ Accepted | High |
| UI-002 | Ghost Inventory Workflow | 2026-02-25 | ✅ Accepted | High |
| UI-003 | Manual Device Assignment | 2026-02-24 | ✅ Accepted | Medium |
| TECH-001 | UTC Timezone Standard | 2026-02-25 | ✅ Accepted | High |
| TECH-002 | Dynamic Pricing Catalog | 2026-02-28 | ✅ Accepted | Medium |
| TECH-003 | Excel Import | 2026-02-28 | ✅ Accepted | Medium |
| TECH-004 | Exceptions over Silent Errors | 2026-02-26 | 🔄 Progress | High |
| RBAC-001 | Role Definitions | 2026-02-27 | ✅ Accepted | High |
| INF-001 | Tailscale VPN | 2026-02-22 | ✅ Accepted | High |
| INF-002 | Systemd Service | 2026-02-22 | ✅ Accepted | Medium |
| REJ-001 | No Auto-Assignment | 2026-02-24 | ❌ Rejected | - |
| REJ-002 | No Public Internet | 2026-02-22 | ❌ Rejected | - |
| REJ-003 | No Microservices | 2026-02-22 | ❌ Rejected | - |

---

**Document Version:** 1.0.0  
**Last Updated:** Current Session  
**Maintained by:** Chief Documentation Officer (CDO-001)  
**Review Cycle:** Monthly or per major decision
