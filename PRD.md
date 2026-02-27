# Product Requirements Document (PRD) - Colab ERP v2.2.3

**Document Version:** 1.0.0  
**Created:** February 27, 2026  
**Product:** Colab ERP - Professional Training Facility & IT Rental Management System  
**Target Version:** v2.2.3 (Production)  
**Status:** ✅ Complete - Ready for Implementation

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [User Personas](#3-user-personas)
4. [Functional Requirements](#4-functional-requirements)
5. [Technical Requirements](#5-technical-requirements)
6. [System Architecture](#6-system-architecture)
7. [Data Model](#7-data-model)
8. [User Interface Requirements](#8-user-interface-requirements)
9. [Quality Requirements](#9-quality-requirements)
10. [Deployment & Operations](#10-deployment--operations)
11. [Success Metrics](#11-success-metrics)
12. [Risk Assessment](#12-risk-assessment)

---

## 1. Executive Summary

Colab ERP is a comprehensive Enterprise Resource Planning system designed for Colab Tech Solutions, managing room bookings, device inventory, and training facility operations. The system supports multi-tenancy (TECH and TRAINING divisions) with Ghost Inventory workflow for efficient resource management.

**Key Objectives:**
- Streamline room and device booking processes
- Implement multi-tenancy support for different business units
- Provide real-time availability tracking and conflict detection
- Enable efficient resource allocation through Ghost Inventory workflow
- Maintain audit trail and notification system

**Current Status:** v2.2.3 in production with 558 bookings, 24 rooms, and comprehensive feature set.

---

## 2. Product Overview

### 2.1 Product Vision
To provide an intuitive, efficient, and scalable resource management system that eliminates double-booking, optimizes resource utilization, and provides real-time visibility into facility operations.

### 2.2 Product Scope
**In Scope:**
- Room booking management with conflict detection
- Device inventory tracking and assignment
- Multi-tenancy support (TECH/Training divisions)
- Ghost Inventory workflow for pending room assignments
- Real-time calendar view with Excel-style interface
- Role-based access control and notifications
- Catering and supply management
- User authentication and authorization

**Out of Scope:**
- Mobile application (Phase 4)
- Third-party calendar integrations (Phase 4)
- Advanced analytics and reporting (Phase 4)
- Payment processing integration (Phase 4)

### 2.3 Key Features
1. **Enhanced Booking Form (Phase 3)** - Complete booking workflow with all requirements
2. **Multi-Tenancy Support** - Separate divisions with shared physical assets
3. **Ghost Inventory Workflow** - Pending bookings with room assignment queue
4. **Real-time Calendar** - Excel-style grid with horizontal scrolling
5. **Device Management** - Manual assignment with conflict detection
6. **Notification System** - In-app notifications for IT Boss and Room Boss

---

## 3. User Personas

### 3.1 Admin (training_facility_admin)
**Role:** System administrator with full access
**Responsibilities:** Dashboard access, user management, system configuration
**Key Tasks:** View all bookings, manage users, configure system settings
**Access Level:** Full system access

### 3.2 Room Boss
**Role:** Room assignment manager
**Responsibilities:** Assign rooms to pending bookings, manage room conflicts
**Key Tasks:** Review pending bookings, assign rooms, override conflicts
**Access Level:** Pending approvals, calendar, notifications

### 3.3 IT Staff
**Role:** Device assignment and management
**Responsibilities:** Assign devices to bookings, manage off-site rentals
**Key Tasks:** Device assignment queue, conflict resolution, off-site tracking
**Access Level:** Device assignment, calendar, notifications

### 3.4 Staff
**Role:** Booking request creator
**Responsibilities:** Create booking requests, view calendar
**Key Tasks:** Submit booking requests, track status
**Access Level:** Calendar, booking creation, pricing

---

## 4. Functional Requirements

### 4.1 Authentication & Authorization (FR-001)
**Priority:** P1 - Critical
**Description:** Secure user authentication with role-based access control
**Requirements:**
- FR-001-01: Users must authenticate with username and bcrypt-hashed password
- FR-001-02: System must support 4 user roles: admin, room_boss, it_staff, staff
- FR-001-03: Role-based menu access must be enforced
- FR-001-04: Session management with logout functionality
- FR-001-05: Password security with bcrypt hashing

**Acceptance Criteria:**
- Only authenticated users can access the system
- Menu options display based on user role
- Admin users see all menu items
- Staff users see limited menu (no dashboard, no notifications)

### 4.2 Room Booking Management (FR-002)
**Priority:** P1 - Critical
**Description:** Complete room booking workflow with conflict detection
**Requirements:**
- FR-002-01: Users must be able to create booking requests with client information
- FR-002-02: System must validate room availability and prevent double-booking
- FR-002-03: Admin users can directly assign rooms or send to pending
- FR-002-04: Staff users always create pending bookings
- FR-002-05: System must support multi-room bookings (one client, multiple date segments)
- FR-002-06: Room capacity validation with warnings
- FR-002-07: Conflict detection with override capability for admins

**Acceptance Criteria:**
- Booking form captures all required client information
- System prevents booking conflicts using database constraints
- Admin can choose direct assignment or pending workflow
- Staff bookings automatically go to pending queue
- Multi-segment bookings are supported

### 4.3 Ghost Inventory Workflow (FR-003)
**Priority:** P1 - Critical
**Description:** Pending booking approval and room assignment workflow
**Requirements:**
- FR-003-01: Pending bookings must be visible to Room Boss
- FR-003-02: Room Boss can assign rooms to pending bookings
- FR-003-03: System must check for conflicts before assignment
- FR-003-04: Room Boss can override conflicts with justification
- FR-003-05: Assigned bookings change status to "Confirmed"
- FR-003-06: Rejection workflow with reason tracking

**Acceptance Criteria:**
- Pending bookings appear in Room Boss interface
- Room assignment validates availability
- Conflict override requires justification
- Status changes reflect in system

### 4.4 Device Management (FR-004)
**Priority:** P2 - High
**Description:** Device inventory tracking and assignment
**Requirements:**
- FR-004-01: System must track device inventory by serial number
- FR-004-02: Users can request devices when creating bookings
- FR-004-03: IT Staff can assign devices manually
- FR-004-04: System must prevent device double-booking
- FR-004-05: Off-site rental tracking with full contact details
- FR-004-06: Device conflict detection and reallocation
- FR-004-07: Alternative device suggestions

**Acceptance Criteria:**
- Device inventory is tracked by serial number
- Booking requests can include device requirements
- IT Staff can assign devices from available pool
- System prevents device conflicts
- Off-site rentals are fully tracked

### 4.5 Calendar View (FR-005)
**Priority:** P2 - High
**Description:** Real-time calendar with Excel-style interface
**Requirements:**
- FR-005-01: Calendar must display rooms as columns, dates as rows
- FR-005-02: Support for week and month view modes
- FR-005-03: Color-coded status indicators (Today, Weekend, Booked, Available)
- FR-005-04: Horizontal scrolling for many rooms
- FR-005-05: Headcount display (learners + facilitators)
- FR-005-06: Device count indicators
- FR-005-07: Long-term office display (A302, A303, Vision)

**Acceptance Criteria:**
- Calendar displays in Excel-style grid format
- Week and month views are available
- Color coding is intuitive and consistent
- Horizontal scrolling works smoothly
- All booking details are visible

### 4.6 Catering & Supplies (FR-006)
**Priority:** P3 - Medium
**Description:** Catering and supply management for bookings
**Requirements:**
- FR-006-01: Support for coffee/tea station selection
- FR-006-02: Morning catering options (none, pastry, sandwiches)
- FR-006-03: Lunch catering options (none, self-catered, in-house)
- FR-006-04: Catering notes for special requests
- FR-006-05: Stationery requirement tracking
- FR-006-06: Water bottle quantity tracking

**Acceptance Criteria:**
- All catering options are available in booking form
- Notes field captures special requests
- Supply requirements are tracked

### 4.7 Notifications System (FR-007)
**Priority:** P3 - Medium
**Description:** In-app notification system for IT Boss and Room Boss
**Requirements:**
- FR-007-01: Low stock alerts for devices
- FR-007-02: Off-site conflict notifications
- FR-007-03: Overdue return notifications
- FR-007-04: Booking request notifications
- FR-007-05: Notification filtering by type
- FR-007-06: Mark notifications as read
- FR-007-07: Daily summary statistics

**Acceptance Criteria:**
- Notifications appear for relevant users
- Filtering works correctly
- Read/unread status is maintained
- Daily summaries are accurate

### 4.8 Multi-Tenancy Support (FR-008)
**Priority:** P2 - High
**Description:** Support for TECH and TRAINING divisions
**Requirements:**
- FR-008-01: Bookings must be tagged with tenant (TECH/TRAINING)
- FR-008-02: Database constraints prevent cross-tenant conflicts
- FR-008-03: Dashboard filtering by tenant
- FR-008-04: Tenant-specific reporting
- FR-008-05: Shared physical assets with logical separation

**Acceptance Criteria:**
- All bookings have tenant assignment
- Database prevents conflicts across tenants
- Reports can be filtered by tenant

---

## 5. Technical Requirements

### 5.1 System Architecture (TR-001)
**Priority:** P1 - Critical
**Requirements:**
- TR-001-01: Single Streamlit application instance
- TR-001-02: PostgreSQL database with connection pooling
- TR-001-03: Tailscale VPN for secure access
- TR-001-04: systemd service for production deployment
- TR-001-05: ACID-compliant transactions

### 5.2 Database Requirements (TR-002)
**Priority:** P1 - Critical
**Requirements:**
- TR-002-01: PostgreSQL 14+ with exclusion constraints
- TR-002-02: tstzrange for timezone-aware booking periods
- TR-002-03: Connection pooling (20 max connections)
- TR-002-04: UTC timezone storage with local display
- TR-002-05: Referential integrity with foreign keys

### 5.3 Security Requirements (TR-003)
**Priority:** P1 - Critical
**Requirements:**
- TR-003-01: bcrypt password hashing
- TR-003-02: Parameterized queries to prevent SQL injection
- TR-003-03: Tailscale VPN for network security
- TR-003-04: Role-based access control
- TR-003-05: No hardcoded credentials

### 5.4 Performance Requirements (TR-004)
**Priority:** P2 - High
**Requirements:**
- TR-004-01: Support 5-10 concurrent users
- TR-004-02: Calendar load time under 3 seconds
- TR-004-03: Booking creation under 2 seconds
- TR-004-04: Database query optimization for calendar views
- TR-004-05: Connection pooling for concurrent access

### 5.5 Scalability Requirements (TR-005)
**Priority:** P3 - Medium
**Requirements:**
- TR-005-01: Database design supports growth to 1000+ bookings
- TR-005-02: Room capacity for 50+ rooms
- TR-005-03: Device inventory for 500+ devices
- TR-005-04: User support for 50+ concurrent users

---

## 6. System Architecture

### 6.1 Technology Stack
- **Frontend:** Streamlit 1.28+
- **Backend:** Python 3.9+
- **Database:** PostgreSQL 14+
- **Authentication:** bcrypt 4.0+
- **Connection Pooling:** psycopg2.pool
- **Timezone Handling:** pytz
- **Data Processing:** pandas 2.0+

### 6.2 Infrastructure
```
User → Tailscale VPN → Streamlit (100.69.57.77:8501) → PostgreSQL
```

### 6.3 Data Flow
1. User authenticates via Streamlit interface
2. Role-based menu access is enforced
3. Database operations use connection pooling
4. All writes use ACID transactions
5. Calendar views use optimized queries
6. Notifications are stored and retrieved as needed

---

## 7. Data Model

### 7.1 Core Entities

**Bookings Table:**
- id (PK)
- room_id (FK)
- booking_period (tstzrange)
- client_name
- status (Pending/Confirmed/Room Assigned/Cancelled)
- tenant_id (TECH/TRAINING)
- num_learners, num_facilitators
- catering fields, supply fields
- device requirements
- timestamps

**Rooms Table:**
- id (PK)
- name
- max_capacity
- room_type
- has_devices
- is_active
- parent_room_id

**Devices Table:**
- id (PK)
- serial_number
- category_id (FK)
- status (available/assigned/off-site)
- notes

**Users Table:**
- user_id (PK)
- username
- password_hash
- role
- created_at

### 7.2 Relationships
- Bookings → Rooms (many-to-one)
- Bookings → Devices (many-to-many via booking_device_assignments)
- Devices → Device Categories (many-to-one)
- Users → Roles (one-to-one)

---

## 8. User Interface Requirements

### 8.1 Design Principles
- Clean, professional interface
- Intuitive navigation
- Role-based menu visibility
- Responsive design for different screen sizes
- Consistent color coding and icons

### 8.2 Key Screens

**Login Screen:**
- Username/password fields
- Error handling for invalid credentials
- System status indicator

**Calendar View:**
- Excel-style grid layout
- Week/month toggle
- Horizontal scrolling for many rooms
- Color-coded status indicators
- Legend for color meanings

**Booking Form:**
- Multi-step form with clear sections
- Real-time validation
- Conflict warnings
- Clear success/error messages

**Pending Approvals:**
- List of pending bookings
- Room assignment interface
- Conflict detection and override
- Rejection workflow

---

## 9. Quality Requirements

### 9.1 Reliability
- 99.9% uptime requirement
- Database backup and recovery
- Error handling for all user actions
- Graceful degradation for network issues

### 9.2 Usability
- Intuitive interface requiring minimal training
- Clear error messages
- Help text and tooltips
- Keyboard navigation support

### 9.3 Maintainability
- Clean, documented code
- Modular architecture
- Version control with Git
- Automated deployment scripts

### 9.4 Security
- Secure authentication
- Role-based access control
- Network security via VPN
- Audit trail for sensitive operations

---

## 10. Deployment & Operations

### 10.1 Production Environment
- Ubuntu Linux server
- Tailscale VPN for access
- systemd service management
- PostgreSQL database
- Streamlit application

### 10.2 Deployment Process
1. Code changes pushed to GitHub
2. Manual deployment via deploy.sh script
3. Service restart with systemd
4. Health check verification

### 10.3 Monitoring
- Application uptime monitoring
- Database connection health
- Error logging and alerting
- Performance metrics

---

## 11. Success Metrics

### 11.1 Business Metrics
- **Booking Efficiency:** Reduce booking processing time by 50%
- **Resource Utilization:** Increase room utilization to 85%
- **User Satisfaction:** Achieve 90% user satisfaction rating
- **Error Reduction:** Eliminate double-booking incidents

### 11.2 Technical Metrics
- **System Uptime:** 99.9% availability
- **Response Time:** <3 seconds for all operations
- **Concurrent Users:** Support 10+ simultaneous users
- **Data Integrity:** Zero data corruption incidents

---

## 12. Risk Assessment

### 12.1 High Risk
- **Database Connectivity:** VPN or network issues could prevent access
  - *Mitigation:* Monitor VPN status, have backup access procedures

### 12.2 Medium Risk
- **User Training:** Staff unfamiliarity with new system
  - *Mitigation:* Comprehensive documentation, training sessions
- **Data Migration:** Existing booking data integrity
  - *Mitigation:* Backup before migration, validation scripts

### 12.3 Low Risk
- **Performance:** System slowdown with increased usage
  - *Mitigation:* Monitor performance, plan for scaling

---

## Approval

**Product Owner:** Shuaib Adams  
**Technical Lead:** [To be assigned]  
**Date:** February 27, 2026  
**Version:** 1.0.0

**Approval Status:** ✅ Ready for Implementation

---

*This PRD serves as the authoritative source for all development work on Colab ERP v2.2.3. All feature requests and changes must be documented and approved through this document.*