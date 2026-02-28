# 🏢 Colab ERP v2.2.3

[![Version](https://img.shields.io/badge/version-v2.2.3-blue)](https://github.com/MrMoosajee/colab_erp/releases)
[![Python](https://img.shields.io/badge/python-3.9+-green)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16+-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-Internal-lightgrey)](LICENSE)

**Professional Training Facility & IT Rental Management System**

Colab ERP is a comprehensive Enterprise Resource Planning system designed for [Colab Tech Solutions](https://github.com/colabtechsolutions), managing room bookings, device inventory, and training facility operations.

---

## 📋 Current Status

| Metric | Status |
|--------|--------|
| **Version** | v2.2.3 |
| **Deployment** | Production |
| **URL** | http://100.69.57.77:8501 |
| **Completeness** | 95% |
| **System Status** | 🟢 Online |

### Recent Updates (February 2026)
- **v2.2.3** (Feb 28, 2026) - Calendar indicators, Excel import (713 bookings), pricing system
- **v2.2.2** (Feb 25, 2026) - Timezone fixes, column name corrections
- **v2.2.1** (Feb 25, 2026) - Ghost Inventory workflow implementation
- **v2.2.0** (Jan 20, 2026) - Multi-tenancy support, database-backed authentication

### Production Statistics
- **807+ Bookings** in database
- **24 Rooms** managed
- **110+ Devices** tracked
- **713 Bookings** imported from Excel (Feb 2026)

---

## ✨ Features

### Core Functionality

#### Multi-Tenancy Support
- **TECH Division** - Technical training programs
- **TRAINING Division** - General training programs
- Global exclusion constraints prevent double-booking across all tenants (shared physical assets)

#### Ghost Inventory Room Booking (Phase 3) ✅
- Staff create bookings without immediate room assignment
- Room Boss interface for pending approvals
- Conflict detection with override capability
- Multi-room bookings (one client, multiple date segments)

#### Calendar View with Indicators (NEW v2.2.3)
- **Excel-style grid** with horizontal scrolling
- Week and Month view modes
- **Color-coded status indicators**:
  - 🟢 **Today** - Green highlight
  - 🟣 **Weekend** - Purple highlight
  - 🔵 **Weekday** - Blue highlight
- **Headcount display** (learners + facilitators)
- **Catering indicators**: ☕ Coffee, 🥪 Morning, 🍽️ Lunch, 📚 Stationery, 💻 Devices
- **Long-term office display** (A302, A303, Vision)

#### Admin Room Selection
- Direct room booking with real-time conflict detection
- Override capability for negotiated conflicts
- Capacity validation and warnings

#### Device Tracking (IT Staff Interface) ✅
- Manual device assignment by serial number
- Off-site rental tracking with full contact details
- Conflict detection and reallocation
- Alternative device suggestions
- Stock level monitoring

#### Pricing Catalog (NEW v2.2.3)
- **Dynamic pricing** for rooms, devices, and catering
- **Room pricing**: Daily, weekly, monthly rates
- **Device pricing**: Collective pricing by category (not individual devices)
- **Catering pricing**: Per-person rates for supplies and services
- **Role-based access**: Admin and IT admin only

#### Excel Import (NEW v2.2.3)
- **Bulk import** from "Colab 2026 Schedule.xlsx"
- **Pattern parsing**: "Client 25+1", "25 + 18 laptops"
- **Room mapping**: 24 rooms mapped from Excel columns
- **Long-term rentals**: Auto-generated daily bookings (Siyaya, Melissa)
- **Auto-approval**: Imported bookings marked as "Approved"

#### Notifications System ✅
- **IT Boss** notifications: Low stock, off-site conflicts, overdue returns
- **Room Boss** notifications: Booking requests, conflict alerts
- In-app notification center with filtering
- All notifications preserved for AI training

#### Authentication & Authorization ✅
- Database-backed bcrypt password hashing
- Role-based access control:
  - **Admin**: Full access including dashboard and pricing
  - **Room Boss**: Pending approvals, notifications (NO pricing)
  - **IT Staff**: Device assignment queue (NO pricing)
  - **Staff**: Create bookings (goes to pending, NO pricing)

#### Database Features ✅
- ACID-compliant transactions
- PostgreSQL exclusion constraints prevent double-booking
- tstzrange for timezone-aware booking periods
- Connection pooling (20 connections)

---

## 🏗️ Architecture

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit 1.28+ | Web UI framework |
| **Backend** | Python 3.9+ | Application logic |
| **Database** | PostgreSQL 16+ | Primary data store |
| **Connection** | psycopg2-binary 2.9+ | PostgreSQL adapter |
| **Pooling** | psycopg2.pool | Connection management |
| **Auth** | bcrypt 4.0+ | Password hashing |
| **Data** | pandas 2.0+ | Data manipulation |
| **Timezone** | pytz | Timezone handling |
| **Excel** | openpyxl 3.0+ | Excel file processing |

### Infrastructure

```
User → Tailscale VPN → Streamlit (100.69.57.77:8501) → PostgreSQL
```

- **Network**: Tailscale VPN for secure access
- **Server**: Ubuntu Linux with systemd service
- **Database**: PostgreSQL 16+ with exclusion constraints
- **Process**: Single Streamlit instance (current scale: 5-10 users)

### Data Model

**Key Tables:**
- `bookings` (807+ rows) - All booking records with Phase 3 fields
- `rooms` (24 rows) - Training rooms and offices
- `devices` (110+ rows) - IT equipment inventory
- `device_categories` - Laptop, Desktop
- `booking_device_assignments` - Device-to-booking links
- `offsite_rentals` - Off-site rental tracking
- `notification_log` - System notifications
- `pricing_catalog` (NEW) - Dynamic pricing management
- `users` - Authentication and roles

---

## 📊 Technical Debt & Roadmap

### Week 1 (Critical) - In Progress
- [ ] **Silent Error Handling** - Convert print statements to exceptions
- [ ] **Deployment Automation** - Create deploy.sh script
- [ ] **Database Indexes** - Add performance indexes for calendar queries

### Month 1 (Foundation) - Planned
- [ ] **Testing Infrastructure** - pytest setup, unit tests
- [ ] **Repository Pattern** - Extract database layer from services
- [ ] **Structured Logging** - JSON logging for observability
- [ ] **Monitoring** - Sentry integration for error tracking

### Month 2-3 (Architecture) - Planned
- [ ] **API Layer** - FastAPI for mobile app support
- [ ] **Caching Layer** - Redis for calendar data
- [ ] **Read Replica** - Database read replica for queries
- [ ] **Documentation** - Full API documentation

### Phase 4 (Future)
- Mobile app support
- Third-party integrations (Google Calendar, Outlook)
- Advanced reporting and analytics
- AI-powered recommendations

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 16+
- Tailscale VPN access (for production)

### Local Development

```bash
# Clone repository
git clone https://github.com/MrMoosajee/colab_erp.git
cd colab_erp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure secrets
cat > ~/.streamlit/secrets.toml << 'SECRETS'
[postgres]
host = "100.69.57.77"
port = "5432"
dbname = "colab_erp"
user = "colabtechsolutions"
password = "your_password"
timezone = "Africa/Johannesburg"
SECRETS

# Run migrations
psql -h $DB_HOST -U colabtechsolutions -d colab_erp -f migrations/v2.2_add_tenancy.sql
psql -h $DB_HOST -U colabtechsolutions -d colab_erp -f migrations/v2.4_device_assignment_system.sql
psql -h $DB_HOST -U colabtechsolutions -d colab_erp -f migrations/v2.5_enhanced_booking_form.sql

# Start application
streamlit run src/app.py --server.port 8501
```

### Production Deployment

```bash
# Using deployment script (recommended)
./deploy.sh

# Manual deployment
scp -r src/ colab:~/colab_erp/
ssh colab "sudo systemctl restart colab_erp"
```

### Excel Import

```bash
# Import from Colab 2026 Schedule.xlsx
cd /home/shuaibadams/Projects/colab_erp
python3 src/import_excel_schedule.py

# Expected output: 713 bookings imported
```

---

## 📁 Project Structure

```
colab_erp/
├── src/
│   ├── app.py                    # Main Streamlit application
│   ├── auth.py                   # Authentication module
│   ├── db.py                     # Database connection & queries
│   ├── booking_form.py           # Enhanced Phase 3 booking form
│   ├── pricing_catalog.py        # Pricing catalog UI (NEW)
│   ├── import_excel_schedule.py  # Excel import script (NEW)
│   └── models/
│       ├── __init__.py
│       ├── availability_service.py   # Room/device availability
│       ├── booking_service.py          # Enhanced booking creation
│       ├── room_approval_service.py    # Ghost Inventory workflow
│       ├── device_manager.py           # Device assignment
│       ├── notification_manager.py     # In-app notifications
│       └── pricing_service.py          # Dynamic pricing (NEW)
├── migrations/
│   ├── v2.2_add_tenancy.sql           # Multi-tenancy
│   ├── v2.4_device_assignment_system.sql  # Device tables
│   ├── v2.5_enhanced_booking_form.sql     # Phase 3 fields
│   └── v2.5.1_add_room_boss_notes.sql    # Room boss notes
├── infra/
│   └── systemd/
│       └── colab_erp.service            # Systemd service config
├── tests/                        # Test files (planned)
├── venv/                         # Virtual environment
├── requirements.txt              # Python dependencies
├── PRD.md                       # Product Requirements Document
├── ARCHITECTURE.md              # System architecture
├── BOOKING_FORM_RESOLUTION_SUMMARY.md  # Issue resolution log
├── README.md                    # This file
└── CHANGELOG.md                 # Version history
```

---

## 👥 User Roles & Permissions

| Role | Menu Access | Pricing Access | Special Features |
|------|-------------|----------------|------------------|
| **Admin** | Dashboard, Notifications, Calendar, Device Queue, Bookings, Approvals, Inventory, **Pricing** | ✅ Yes | Full system access |
| **Room Boss (training_facility_admin)** | Dashboard, Notifications, Calendar, Bookings, Pricing, Pending Approvals, Inventory | ✅ Yes | **Primary: Assign rooms to pending bookings** |
| **IT Boss (it_rental_admin)** | Dashboard, Notifications, Calendar, Bookings, Pricing, Pending Approvals, Inventory | ✅ Yes | **Primary: Device assignment queue** |
| **Training Facility Admin** | Calendar, Bookings, Pricing (view), Inventory | ❌ No | View-only access, **NO assignment privileges** |
| **Kitchen Staff** | Calendar ONLY | ❌ No | View catering needs, headcounts, push orders |
| **IT Staff** | Calendar, Device Assignment Queue | ❌ No | Device assignment operations |
| **Staff** | Calendar, Bookings | ❌ No | Create bookings (goes to pending) |

---

## 🛠️ Development

### Coding Standards
- **PEP8** compliance required
- **OOP Mandate**: All new code must use classes
- Type hints for function parameters
- Docstrings for public methods
- No silent error handling - raise exceptions

### HITL Protocol
All significant changes require Human-in-the-Loop authorization:
1. Present proposed changes with rationale
2. Wait for explicit user approval
3. Log authorization in CDO system
4. Implement with verification

### Testing (Planned)
```bash
# Run tests (future)
pytest tests/ -v --cov=src

# Check coverage (future)
pytest --cov-report=html
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PRD.md](PRD.md) | Product Requirements Document (v1.1.0) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and data model |
| [BOOKING_FORM_RESOLUTION_SUMMARY.md](BOOKING_FORM_RESOLUTION_SUMMARY.md) | Issue resolution log |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [MASTER_SYSTEM_DOCUMENT.md](../MASTER_SYSTEM_DOCUMENT.md) | Comprehensive system documentation |
| [TECHNICAL_REVIEW_SYNTHESIS.md](../TECHNICAL_REVIEW_SYNTHESIS.md) | Executive summary & action plan |

---

## 🐛 Known Issues

| Issue | ID | Severity | Status |
|-------|-----|----------|--------|
| Silent error handling in services | CDO-003 | Critical | 🔄 In Progress |
| No automated deployment pipeline | CDO-002 | Critical | 🔄 In Progress |
| Column name mismatches (capacity vs max_capacity) | CDO-001 | Critical | ✅ Fixed |
| Missing database indexes | - | Medium | 📋 Planned |
| No automated tests | - | Critical | 📋 Planned |

See [CDO_COMPREHENSIVE_SESSION_REPORT_2026-02-25.md](../CDO_COMPREHENSIVE_SESSION_REPORT_2026-02-25.md) for complete incident history.

---

## 🔒 Security

- All database connections use parameterized queries
- bcrypt password hashing with salt
- Tailscale VPN required for production access
- Role-based access control (RBAC)
- No hardcoded credentials (use secrets.toml)
- Pricing catalog restricted to admin roles only

---

## 📞 Support & Contact

**Technical Issues:**
1. Check this README and linked documentation
2. Review [MASTER_SYSTEM_DOCUMENT.md](../MASTER_SYSTEM_DOCUMENT.md)
3. Check service status: `curl http://100.69.57.77:8501`
4. Contact development team

**System Status:**
- Production URL: http://100.69.57.77:8501
- Server: Ubuntu via Tailscale (100.69.57.77)
- Database: PostgreSQL 16+

---

## 📈 System Health

```
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM HEALTH                        │
├─────────────────────────────────────────────────────────┤
│ Uptime:           🟢 Online                            │
│ Version:          v2.2.3                               │
│ Database:         🟢 Connected (807+ bookings)         │
│ Calendar:         🟢 Operational (indicators working)  │
│ Device Tracking:  🟢 Active                            │
│ Notifications:    🟢 Working                           │
│ Pricing Catalog:  🟢 Active (admin only)               │
│ Excel Import:     ✅ 713 bookings imported             │
└─────────────────────────────────────────────────────────┘
```

---

## 📄 License

Internal Confidential - For Colab Tech Solutions use only.

---

## 🙏 Acknowledgments

- **Master Orchestrator Agent (MOA)** - System coordination
- **Chief Documentation Officer (CDO-001)** - Documentation and audit trail
- **SRE & Architecture Sub-agents** - Technical reviews

---

**Last Updated:** February 28, 2026  
**Document Version:** 1.1.0  
**CDO Agent:** CDO-001
