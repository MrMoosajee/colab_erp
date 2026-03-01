# Colab ERP - Workflow Diagrams

**Version:** 1.0.0  
**Last Updated:** March 2026  
**System:** Colab ERP v2.2.3

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Ghost Inventory Workflow](#ghost-inventory-workflow)
3. [Role Hierarchy](#role-hierarchy)
4. [Data Flow](#data-flow)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           COLAB ERP SYSTEM ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│   │  ROOM BOSS  │   │   IT BOSS   │   │    ADMIN    │   │    STAFF    │       │
│   │             │   │             │   │  VIEWER       │   │  /CLIENT    │       │
│   │• Assign     │   │• Assign     │   │• View Only   │   │• Create     │       │
│   │  Rooms      │   │  Devices    │   │• Monitor     │   │  Bookings   │       │
│   │• Approve    │   │• Off-site   │   │• Reporting   │   │• Request    │       │
│   │  Bookings   │   │  Rentals    │   │              │   │  Devices    │       │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘       │
│          │                   │                   │                   │          │
│          └───────────────────┴───────────────────┴───────────────────┘          │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      STREAMLIT APPLICATION                             │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│   │  │  Calendar   │  │   Booking   │  │   Device    │  │   Pricing   │ │   │
│   │  │    View     │  │    Form     │  │   Queue     │  │   Catalog   │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│   │  │  Pending    │  │  Inventory  │  │    Admin    │  │ Notifications│ │   │
│   │  │ Approvals   │  │  Dashboard  │  │  Dashboard  │  │              │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│   └────────────────────────────────┬────────────────────────────────────┘   │
│                                    │                                         │
│                         ┌──────────▼──────────┐                             │
│                         │  Service Layer       │                             │
│                         │ ┌───────────────┐    │                             │
│                         │ │BookingService │    │                             │
│                         │ │RoomApprovalSvc│    │                             │
│                         │ │DeviceManager  │    │                             │
│                         │ └───────────────┘    │                             │
│                         └──────────┬────────┘                             │
│                                    │                                         │
│                         ┌──────────▼──────────┐                             │
│                         │   PostgreSQL 16+    │                             │
│                         │ ┌───────────────────┐│                             │
│                         │ │ 807+ Bookings     ││                             │
│                         │ │ 24 Rooms          ││                             │
│                         │ │ 110+ Devices      ││                             │
│                         │ └───────────────────┘│                             │
│                         └──────────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Ghost Inventory Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GHOST INVENTORY WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐          ┌─────────────────┐          ┌─────────────┐   │
│  │   STEP 1:       │          │   STEP 2:       │          │   STEP 3:   │   │
│  │  CREATE BOOKING │─────────▶│  PENDING QUEUE  │─────────▶│  REVIEW    │   │
│  │                 │          │                 │          │            │   │
│  │ Staff/Client    │          │ Status: PENDING │          │ Room Boss  │   │
│  │ fills form      │          │ Room: NULL      │          │ Reviews    │   │
│  │ No room yet     │          │ Ghost Record    │          │ Queue      │   │
│  └─────────────────┘          └─────────────────┘          └─────┬──────┘   │
│                                                                    │          │
│                                                                    ▼          │
│                                                          ┌─────────────────┐   │
│                                                          │   STEP 4:       │   │
│                                                          │  CHECK & ASSIGN │   │
│                                                          │                 │   │
│                                                          │ • Check conflicts│   │
│                                                          │ • Review capacity│   │
│                                                          │ • Assign room   │   │
│                                                          │ • Or reject     │   │
│                                                          └────────┬────────┘   │
│                                                                   │           │
│                                     ┌──────────────┬──────────────┼────────┐  │
│                                     │              │              │        │  │
│                                     ▼              ▼              ▼        │  │
│                            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│  │
│                            │  ASSIGNED   │ │  REJECTED   │ │  OVERRIDE   ││  │
│                            │             │ │             │ │  (with      ││  │
│                            │ Status:     │ │ Status:     │ │  reason)    ││  │
│                            │ Room Assigned│ │ Rejected    │ │ Status:     ││  │
│                            │ Room: X      │ │ Room: NULL  │ │ Room Assigned│ │  │
│                            └──────┬──────┘ └─────────────┘ └──────┬──────┘│  │
│                                   │                               │       │  │
│                                   └──────────────┬────────────────┘       │  │
│                                                  │                        │  │
│                                                  ▼                        │  │
│                                        ┌─────────────────┐              │  │
│                                        │   STEP 5:       │              │  │
│                                        │  NOTIFICATION   │              │  │
│                                        │                 │              │  │
│                                        │ Requester gets  │              │  │
│                                        │ confirmation    │              │  │
│                                        └─────────────────┘              │  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROLE HIERARCHY & ACCESS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ADMIN LEVEL                                  │   │
│  │  ┌─────────────────────┐     ┌─────────────────────────────────────┐ │   │
│  │  │ training_facility_  │     │ it_rental_admin (IT Boss)           │ │   │
│  │  │ admin (Room Boss)   │     │                                     │ │   │
│  │  │                     │     │ • Device Queue                      │ │   │
│  │  │ • Full Access       │     │ • Off-site Tracking                 │ │   │
│  │  │ • Room Assignment   │     │ • Conflict Resolution             │ │   │
│  │  │ • Pending Approvals │     │ • Inventory Management            │ │   │
│  │  │ • Pricing Edit      │     │ • Pricing Edit                      │ │   │
│  │  └─────────────────────┘     └─────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        VIEWER LEVEL                                │   │
│  │  ┌─────────────────────┐     ┌─────────────────────────────────────┐ │   │
│  │  │ training_facility_  │     │ kitchen_staff                       │ │   │
│  │  │ admin_viewer         │     │                                     │ │   │
│  │  │                     │     │ • Calendar ONLY                     │ │   │
│  │  │ • View Calendar       │     │ • Catering Indicators               │ │   │
│  │  │ • View Pricing        │     │ • Headcounts                        │ │   │
│  │  │ • Create Bookings     │     │ • No Device/Room Access             │ │   │
│  │  │ • NO Approval Rights  │     │                                     │ │   │
│  │  └─────────────────────┘     └─────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         STAFF LEVEL                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ staff (Legacy)                                                    │ │   │
│  │  │ • Create Bookings → PENDING                                     │ │   │
│  │  │ • View Calendar                                                 │ │   │
│  │  │ • No Pricing Access                                             │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  MENU ACCESS MATRIX:                                                         │
│  ┌──────────────────────┬────────┬────────┬────────┬────────┬────────┐      │
│  │ Menu Item            │ Room   │ IT     │ Viewer │ Kitchen│ Staff  │      │
│  │                      │ Boss   │ Boss   │        │ Staff  │        │      │
│  ├──────────────────────┼────────┼────────┼────────┼────────┼────────┤      │
│  │ Dashboard            │   ✅   │   ✅   │   ❌   │   ❌   │   ❌   │      │
│  │ Notifications        │   ✅   │   ✅   │   ❌   │   ❌   │   ❌   │      │
│  │ Calendar             │   ✅   │   ✅   │   ✅   │   ✅   │   ✅   │      │
│  │ Device Queue         │   ✅   │   ✅   │   ❌   │   ❌   │   ❌   │      │
│  │ New Room Booking     │   ✅   │   ✅   │   ✅   │   ❌   │   ✅   │      │
│  │ New Device Booking   │   ✅   │   ✅   │   ✅   │   ❌   │   ❌   │      │
│  │ Pricing Catalog      │   ✅   │   ✅   │   👁️   │   ❌   │   ❌   │      │
│  │ Pending Approvals    │   ✅   │   ✅   │   ❌   │   ❌   │   ❌   │      │
│  │ Inventory Dashboard  │   ✅   │   ✅   │   ✅   │   ❌   │   ❌   │      │
│  └──────────────────────┴────────┴────────┴────────┴────────┴────────┘      │
│                                                                              │
│  LEGEND: ✅ = Full Access  👁️ = View Only  ❌ = No Access                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           USER LAYER                                 │   │
│  │                                                                     │   │
│  │    Room Boss ───┐                                                   │   │
│  │    IT Boss ─────┼───▶ Streamlit UI ◀─── Kitchen Staff              │   │
│  │    Admin ───────┘         │              Admin Viewer               │   │
│  │                           │                                         │   │
│  │                           ▼                                         │   │
│  │    ┌──────────────────────────────┐                               │   │
│  │    │  Session State (per user)    │                               │   │
│  │    │  • authenticated             │                               │   │
│  │    │  • username                  │                               │   │
│  │    │  • role                      │                               │   │
│  │    └──────────────────────────────┘                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SERVICE LAYER                              │   │
│  │                                                                     │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │  │   │
│  │   │  │ BookingService│  │ RoomApproval  │  │ DeviceManager │   │  │   │
│  │   │  │               │  │ Service       │  │               │   │  │   │
│  │   │  │ • create      │  │               │  │ • assign      │   │  │   │
│  │   │  │ • get_details │  │ • get_pending │  │ • reallocate  │   │  │   │
│  │   │  │ • validate    │  │ • assign_room │  │ • check_stock │   │  │   │
│  │   │  └───────────────┘  └───────────────┘  └───────────────┘   │  │   │
│  │   │                                                             │  │   │
│  │   │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │  │   │
│  │   │  │ Availability  │  │ Notification  │  │ PricingService│   │  │   │
│  │   │  │ Service       │  │ Manager       │  │               │   │  │   │
│  │   │  │               │  │               │  │ • get_pricing │   │  │   │
│  │   │  │ • check_room  │  │ • create      │  │ • update      │   │  │   │
│  │   │  │ • check_device│  │ • mark_read   │  │ • add_item    │   │  │   │
│  │   │  └───────────────┘  └───────────────┘  └───────────────┘   │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │                   ┌──────────────────────┐                          │   │
│  │                   │ Connection Pool      │                          │   │
│  │                   │ (20 max connections) │                          │   │
│  │                   └──────────┬───────────┘                          │   │
│  └──────────────────────────────┼──────────────────────────────────────┘   │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        DATABASE LAYER                              │   │
│  │                                                                     │   │
│  │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │
│  │   │   bookings   │ │    rooms     │ │   devices    │              │   │
│  │   │              │ │              │ │              │              │   │
│  │   │ • id (PK)    │ │ • id (PK)    │ │ • id (PK)    │              │   │
│  │   │ • room_id(FK)│ │ • name       │ │ • serial_no  │              │   │
│  │   │ • period     │ │ • capacity   │ │ • category   │              │   │
│  │   │ • client     │ │ • type       │ │ • status     │              │   │
│  │   │ • status     │ │              │ │              │              │   │
│  │   └──────────────┘ └──────────────┘ └──────────────┘              │   │
│  │                                                                     │   │
│  │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │
│  │   │ booking_dev  │ │ offsite_     │ │ notification │              │   │
│  │   │ _assignments │ │ rentals      │ │ _log         │              │   │
│  │   │              │ │              │ │              │              │   │
│  │   │ • id (PK)    │ │ • id (PK)    │ │ • id (PK)    │              │   │
│  │   │ • booking(FK)│ │ • assignment │ │ • type       │              │   │
│  │   │ • device(FK) │ │ • rental_no  │ │ • message    │              │   │
│  │   │ • is_offsite │ │ • contact    │ │ • recipients │              │   │
│  │   └──────────────┘ └──────────────┘ └──────────────┘              │   │
│  │                                                                     │   │
│  │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │
│  │   │   users      │ │pricing_catalog│ │ device_categ │              │   │
│  │   │              │ │              │ │ ories        │              │   │
│  │   │ • user_id(PK)│ │ • id (PK)    │ │              │              │   │
│  │   │ • username   │ │ • item_type  │ │ • id (PK)    │              │   │
│  │   │ • role       │ │ • rates      │ │ • name       │              │   │
│  │   │ • password   │ │ • tier       │ │              │              │   │
│  │   └──────────────┘ └──────────────┘ └──────────────┘              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  DATA FLOW EXAMPLES:                                                         │
│                                                                              │
│  1. CREATE BOOKING:                                                          │
│     User ──▶ BookingService.create() ──▶ INSERT bookings ──▶ Return ID    │
│                                                                              │
│  2. ASSIGN ROOM:                                                             │
│     Room Boss ──▶ RoomApprovalService.assign() ──▶ UPDATE bookings         │
│                 ──▶ SELECT conflicts ──▶ Return result                       │
│                                                                              │
│  3. ASSIGN DEVICE:                                                         │
│     IT Staff ──▶ DeviceManager.assign() ──▶ INSERT booking_device_assign   │
│                ──▶ UPDATE device status ──▶ Log audit                      │
│                                                                              │
│  4. CHECK AVAILABILITY:                                                    │
│     System ──▶ AvailabilityService.check() ──▶ SELECT available devices      │
│              ──▶ EXCLUDE assigned for date range ──▶ Return list           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Booking Status State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BOOKING STATUS STATE MACHINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                        ┌──────────────┐                                     │
│           ┌───────────▶│   PENDING    │◀────────┐                          │
│           │            │  (No room)   │         │                          │
│           │            └──────┬───────┘         │                          │
│           │                   │                  │                          │
│    [Create│             [Room  │ Boss]      [Re- │ open]                     │
│    Booking│            Assign   or           or   Edit                       │
│    as Staff│                   │          Reject  ]                          │
│           │                   ▼                  │                          │
│           │            ┌──────────────┐         │                          │
│           │            │ ROOM ASSIGNED│─────────┘                          │
│           │            │  (Room set)  │                                     │
│           │            └──────┬───────┘                                     │
│           │                   │                                             │
│           │         [Devices] │ Assigned                                    │
│           │                   │                                             │
│           │                   ▼                                             │
│           │            ┌──────────────┐         ┌──────────────┐            │
│           │            │  CONFIRMED   │────────▶│  CANCELLED   │            │
│           │            │ (Fully Ready)│ [Cancel]│              │            │
│           │            └──────┬───────┘         └──────────────┘            │
│           │                   │                                             │
│           │         [Booking] │ Complete                                    │
│           │                   │                                             │
│           │                   ▼                                             │
│           │            ┌──────────────┐                                     │
│           └───────────▶│   COMPLETED  │                                     │
│              [Archive] │              │                                     │
│                        └──────────────┘                                     │
│                                                                              │
│  STATUS DEFINITIONS:                                                         │
│  ┌────────────────┬──────────────────────────────────────────────────────┐  │
│  │ Status         │ Definition                                           │  │
│  ├────────────────┼──────────────────────────────────────────────────────┤  │
│  │ PENDING        │ Booking created, awaiting room assignment            │  │
│  │ ROOM ASSIGNED  │ Room assigned, may need devices or final confirm   │  │
│  │ CONFIRMED      │ Fully approved, ready for execution                  │  │
│  │ REJECTED       │ Could not be accommodated, reason recorded           │  │
│  │ CANCELLED      │ Cancelled by client or admin                         │  │
│  │ COMPLETED      │ Booking dates passed, successfully executed          │  │
│  └────────────────┴──────────────────────────────────────────────────────┘  │
│                                                                              │
│  TRANSITION RULES:                                                           │
│  • PENDING → ROOM ASSIGNED: Room Boss assigns room                          │
│  • PENDING → REJECTED: Room Boss rejects with reason                        │
│  • ROOM ASSIGNED → CONFIRMED: All requirements met                         │
│  • ROOM ASSIGNED → PENDING: Room unassigned (rare)                          │
│  • CONFIRMED → CANCELLED: Client/admin cancels                             │
│  • CONFIRMED → COMPLETED: Booking dates pass                                  │
│  • Any → CANCELLED: Can cancel from any status (with permissions)           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Device Status Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DEVICE STATUS LIFECYCLE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│     ┌──────────────────────────────────────────────────────────┐          │
│     │                    AVAILABLE                             │          │
│     │  • In inventory                                            │          │
│     │  • Ready for assignment                                    │          │
│     │  • Can be assigned to any booking                          │          │
│     └────────────────────┬─────────────────────────────────────┘          │
│                          │                                                  │
│              [Assign to Booking]                                              │
│                          │                                                  │
│                          ▼                                                  │
│     ┌──────────────────────────────────────────────────────────┐          │
│     │                    ASSIGNED                              │          │
│     │  • Assigned to specific booking                            │          │
│     │  • Located in assigned room                                │          │
│     │  • Cannot be assigned to another booking                     │          │
│     └────────────────────┬─────────────────────────────────────┘          │
│                          │                                                  │
│         [Mark as Off-site] / [Return from Off-site]                         │
│                          │                                                  │
│                          ▼                                                  │
│     ┌──────────────────────────────────────────────────────────┐          │
│     │                    OFF-SITE                              │          │
│     │  • Rented for external use                                   │          │
│     │  • Has rental record with contact info                       │          │
│     │  • Expected return date tracked                              │          │
│     │  • Overdue notifications if not returned                     │          │
│     └────────────────────┬─────────────────────────────────────┘          │
│                          │                                                  │
│            [Mark Returned] / [Send to Maintenance]                          │
│                          │                                                  │
│                          ▼                                                  │
│     ┌──────────────────────────────────────────────────────────┐          │
│     │                   MAINTENANCE                            │          │
│     │  • Under repair or servicing                               │          │
│     │  • Not available for assignment                            │          │
│     │  • Return to Available when fixed                          │          │
│     └────────────────────┬─────────────────────────────────────┘          │
│                          │                                                  │
│               [Repair Complete] / [Retire]                                  │
│                          │                                                  │
│                          ▼                                                  │
│     ┌──────────────────────────────────────────────────────────┐          │
│     │                    RETIRED                               │          │
│     │  • No longer in service                                    │          │
│     │  • Kept for historical records                               │          │
│     │  • Not shown in availability queries                         │          │
│     └──────────────────────────────────────────────────────────┘          │
│                                                                              │
│  STATUS TRANSITIONS:                                                         │
│  ┌──────────────┬───────────────────────────────────────────────────────┐   │
│  │ Transition   │ Trigger                                               │   │
│  ├──────────────┼───────────────────────────────────────────────────────┤   │
│  │ AVAIL → ASSN │ Device assigned to booking                            │   │
│  │ ASSN → AVAIL │ Booking completed/cancelled, device returned           │   │
│  │ ASSN → OFF   │ Marked for off-site rental                              │   │
│  │ OFF → AVAIL  │ Returned from off-site, checked in                      │   │
│  │ AVAIL → MAINT│ Sent for repair                                         │   │
│  │ MAINT → AVAIL│ Repair completed                                        │   │
│  │ ANY → RETIRE │ Device no longer functional, end of life                │   │
│  └──────────────┴───────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Tenancy Data Isolation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-TENANCY DATA FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                         SHARED PHYSICAL RESOURCES                             │
│                    ┌─────────────────────────────┐                          │
│                    │     24 Rooms (Physical)       │                          │
│                    │     110+ Devices (Physical) │                          │
│                    └─────────────┬───────────────┘                          │
│                                  │                                           │
│                    ┌─────────────┴───────────────┐                         │
│                    │                               │                         │
│                    ▼                               ▼                         │
│     ┌───────────────────────────────┐   ┌───────────────────────────────┐   │
│     │      TECH DIVISION            │   │     TRAINING DIVISION         │   │
│     │      tenant_id = 'TECH'       │   │     tenant_id = 'TRAINING'    │   │
│     │                               │   │                               │   │
│     │  ┌─────────────────────────┐  │   │  ┌─────────────────────────┐  │   │
│     │  │  Bookings Table        │  │   │  │  Bookings Table        │  │   │
│     │  │  • Booking #1001       │  │   │  │  • Booking #2001       │  │   │
│     │  │  • Client: TechCorp     │  │   │  │  │ Client: TrainCo        │  │   │
│     │  │  • Room: Excellence     │  │   │  │  │ Room: Inspiration      │  │   │
│     │  │  • tenant_id: TECH      │  │   │  │  │ tenant_id: TRAINING    │  │   │
│     │  └─────────────────────────┘  │   │  └─────────────────────────┘  │   │
│     │                               │   │                               │   │
│     │  ┌─────────────────────────┐  │   │  ┌─────────────────────────┐  │   │
│     │  │  Dashboard Stats       │  │   │  │  Dashboard Stats       │  │   │
│     │  │  Total: 450 bookings    │  │   │  │  Total: 357 bookings    │  │   │
│     │  │  tenant-filtered         │  │   │  │  tenant-filtered         │  │   │
│     │  └─────────────────────────┘  │   │  └─────────────────────────┘  │   │
│     │                               │   │                               │   │
│     └───────────────────────────────┘   └───────────────────────────────┘   │
│                    │                               │                         │
│                    │    CONFLICT PREVENTION         │                         │
│                    │    (Global Constraint)         │                         │
│                    │                               │                         │
│                    └───────────────┬───────────────┘                         │
│                                    │                                         │
│                    ┌───────────────▼───────────────┐                         │
│                    │  EXCLUSION CONSTRAINT:       │                         │
│                    │                              │                         │
│                    │  No two bookings can       │                         │
│                    │  share same room + time    │                         │
│                    │  REGARDLESS of tenant_id     │                         │
│                    │                              │                         │
│                    │  If TECH books Room A        │                         │
│                    │  at 10:00-12:00              │                         │
│                    │  TRAINING cannot book        │                         │
│                    │  Room A at 10:00-12:00       │                         │
│                    │                              │                         │
│                    └──────────────────────────────┘                         │
│                                                                              │
│  QUERY PATTERNS:                                                             │
│                                                                              │
│  1. TECH Dashboard:                                                          │
│     SELECT * FROM bookings WHERE tenant_id = 'TECH'                        │
│                                                                              │
│  2. Global Calendar (all bookings):                                          │
│     SELECT * FROM bookings WHERE date_range overlaps                        │
│     (shows both TECH and TRAINING)                                           │
│                                                                              │
│  3. Conflict Check (global):                                                 │
│     SELECT * FROM bookings WHERE room_id = X                                 │
│     AND booking_period && target_period                                      │
│     (checks ALL tenants - cannot double-book physical room)                  │
│                                                                              │
│  DEFAULTS:                                                                   │
│  • New bookings default to 'TECH' tenant                                     │
│  • Excel imports default to 'TECH'                                           │
│  • Manual override possible by admin                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Document Owner:** Process & Workflow Documentation Team  
**Related Documents:** 
- WORKFLOWS.md - Business process workflows
- PROCESS_FLOWS.md - Step-by-step process flows
- USER_GUIDE.md - Role-specific user guides

