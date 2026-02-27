# Changelog

All notable changes to Colab ERP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Silent error handling fixes (CDO-003)
- Deployment automation script (CDO-002)
- Database performance indexes
- Structured logging implementation
- Sentry error tracking integration
- Test infrastructure with pytest

---

## [2.2.3] - 2026-02-25

### Added
- Phase 3 Enhanced Booking Form with 13 new fields
- Ghost Inventory workflow - bookings can be created without immediate room assignment
- Multi-room booking support (one client, multiple date segments)
- Room approval interface for Room Boss
- Conflict override capability in room assignment
- Pending approvals dashboard
- Device availability checking across booking segments

### Changed
- Booking creation now supports `room_id=None` for pending status
- Admin users can choose between direct room booking or pending workflow
- Staff bookings automatically go to pending status

### Fixed
- Timezone handling for calendar view (switched to pytz.UTC.localize)
- Column name mapping in availability queries (`max_capacity` vs `capacity`)
- Date comparison in calendar grid (datetime64[ns, UTC] vs Python date)
- Room occupancy queries using correct column names

### Technical
- Added comprehensive error handling in booking form
- Device count now displayed in calendar cells
- Long-term offices (A302, A303, Vision) show client names only

---

## [2.2.2] - 2026-02-25

### Fixed
- **Critical**: Room availability returning 0 results due to timezone mismatch
- Fixed naive Python datetimes vs UTC database comparison
- Updated `availability_service.py` to use `pytz.UTC.localize()` for all datetime operations

### Changed
- Standardized on UTC timezone for all database operations
- Added timezone consistency checks in service methods

---

## [2.2.1] - 2026-02-25

### Added
- Ghost Inventory room assignment workflow
- Room Boss approval interface
- Conflict detection and override system

### Fixed
- **Critical**: Admin room selection showing "No rooms found"
- Fixed column name mismatch: `capacity` → `max_capacity`
- Fixed column name mismatch: `is_active` → `is_active`
- Removed references to non-existent columns: `room_type`, `has_devices`

### Technical
- Added `get_all_rooms()` method that uses correct column names
- Created `room_approval_service.py` for approval workflow

---

## [2.2.0] - 2026-01-20

### Added
- **Multi-Tenancy Support**: TECH and TRAINING divisions
- **Database-backed Authentication**: Migrated from secrets-based to bcrypt
- **Tenant Attribution**: All bookings and inventory movements tagged with tenant_id
- **Comprehensive Error Handling**: ConnectionError and RuntimeError throughout

### Changed
- Authentication now uses `src.auth.authenticate()` with bcrypt
- Added path setup for proper module imports (`sys.path.insert`)
- Updated `run_query()` to raise exceptions instead of silent failures
- Added `fetch_one` parameter to `run_transaction()` for RETURNING clauses

### Fixed
- **Bug**: `create_booking()` ignoring `purpose` parameter
- **Bug**: Module import errors when running `streamlit run src/app.py`
- **Bug**: Missing `bcrypt` dependency
- **Bug**: Silent database errors returning empty DataFrames
- **Bug**: Missing error handling in calendar and dashboard views
- **Bug**: Database call outside try-except block

### Database
- Created `tenant_type` ENUM (TECH, TRAINING)
- Added `tenant_id` column to bookings and inventory_movements
- Created index `idx_bookings_tenant` for reporting performance
- **Important**: Exclusion constraints remain GLOBAL (shared physics across tenants)

### Migration
- New migration file: `migrations/v2.2_add_tenancy.sql`
- Run: `psql -h <host> -U colabtechsolutions -d colab_erp -f migrations/v2.2_add_tenancy.sql`

---

## [2.1.9] - 2026-02-23

### Added
- New calendar grid view with Excel-style formatting
- Week and Month view modes
- Color-coded cells (Today, Weekend, Weekday, Booked)
- Horizontal scrolling for room display
- Long-term office handling (A302, A303, Vision)

### Fixed
- **Critical**: Calendar showing empty cells despite 807 bookings
- Fixed datetime64[ns, UTC] vs Python date object comparison
- Added `.dt.date` conversion for proper date matching

### Technical
- Created `get_calendar_grid()` function in db.py
- Added CSS styling for scrollable calendar grid
- Legend for color interpretation

---

## [2.1.8] - 2026-02-24

### Added
- Device Manager service for IT Staff interface
- Device assignment by serial number
- Off-site rental tracking with full contact details
- Device conflict detection and reallocation
- Stock level monitoring

### Added
- Notification Manager for IT Boss and Room Boss
- Low stock alerts
- Conflict notifications with no alternatives
- Off-site rental conflict alerts
- Overdue return tracking
- Daily summary dashboard

---

## [2.1.7] - 2026-02-24

### Added
- Room assignment interface for Room Boss
- Pending approvals workflow
- Conflict detection in room booking
- Override capability for negotiated conflicts

---

## [2.1.6] - 2026-02-23

### Changed
- Expanded navigation menu for all user roles
- Role-based menu access:
  - Admin: Full access
  - Bosses: Notifications + standard menu
  - Staff: Limited menu

---

## [2.1.5] - 2026-02-22

### Fixed
- Calendar styling - text colors now visible
- Facilitator count logic in calendar cells
- Weekend coloring (Saturday/Sunday)

---

## [2.1.4] - 2026-02-22

### Changed
- Calendar scrollbar hidden for cleaner appearance
- Empty box styling removed

---

## [2.1.3] - 2026-02-22

### Fixed
- Long-term office display in calendar
- Excel format restored for calendar grid

---

## [2.1.2] - 2026-02-22

### Changed
- Refactored calendar to Excel-style grid
- Horizontal scrolling for room display
- Days as rows, rooms as columns

---

## [2.1.1] - 2026-01-XX

### Added
- Core booking system
- Room management
- Basic calendar view
- User authentication
- Dashboard with KPIs

### Technical
- Database connection pooling (20 connections)
- PostgreSQL exclusion constraints for conflict prevention
- tstzrange for timezone-aware booking periods
- UTC standard for all timestamp storage

---

## Incident Log

### 2026-02-24 - Phase 3 App Corruption
**Incident:** Application completely non-functional after deployment  
**Root Cause:** `replace_in_file` inserted 209 lines at wrong location, corrupted `main()` function  
**Impact:** Production outage, 5 minutes downtime  
**Resolution:** Rolled back to stable commit 857d454  
**Prevention:** Tool usage limits (<30 lines per operation)  

### 2026-02-25 - Timezone Mismatch
**Incident:** Room availability returning 0 rooms for valid dates  
**Root Cause:** Naive Python datetimes vs UTC database comparison  
**Impact:** Users couldn't book rooms  
**Resolution:** Used `pytz.UTC.localize()` for timezone-aware datetimes  
**Prevention:** Consistent timezone handling, tests with real database  

### 2026-02-25 - get_all_rooms() Empty
**Incident:** Admin room selection showing "No rooms found"  
**Root Cause:** Query used wrong column names (`capacity` vs `max_capacity`)  
**Impact:** Admin couldn't select rooms for direct booking  
**Resolution:** Updated query to use correct column names  
**Prevention:** Schema-first development, validation tests  

### 2026-02-25 - Deployment Sync Issues
**Incident:** User saw old code despite fixes being "deployed"  
**Root Cause:** No automated deployment, manual SCP forgotten  
**Impact:** Wasted debugging time, user confusion  
**Resolution:** Created deploy.sh automation script (in progress)  
**Prevention:** Automated deployment with verification  

---

## Version History Summary

| Version | Date | Key Changes |
|---------|------|-------------|
| v2.2.3 | 2026-02-25 | Phase 3 Enhanced Booking Form, Ghost Inventory |
| v2.2.2 | 2026-02-25 | Timezone fixes |
| v2.2.1 | 2026-02-25 | Column name fixes, Ghost Inventory workflow |
| v2.2.0 | 2026-01-20 | Multi-tenancy, database auth, error handling |
| v2.1.9 | 2026-02-23 | New calendar grid view |
| v2.1.1 | 2026-01-XX | Core booking system |

---

**Last Updated:** February 27, 2026  
**Maintained by:** Chief Documentation Officer (CDO-001)
