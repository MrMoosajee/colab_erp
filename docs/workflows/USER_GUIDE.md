# Colab ERP - User Guide

**Version:** 1.0.0  
**Last Updated:** March 2026  
**System:** Colab ERP v2.2.3

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Role-Based Guides](#role-based-guides)
   - [Room Boss Guide (training_facility_admin)](#room-boss-guide)
   - [IT Boss Guide (it_rental_admin)](#it-boss-guide)
   - [Admin Viewer Guide (training_facility_admin_viewer)](#admin-viewer-guide)
   - [Kitchen Staff Guide (kitchen_staff)](#kitchen-staff-guide)
3. [Common Tasks](#common-tasks)
4. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Access

**URL:** http://100.69.57.77:8501 (via Tailscale VPN)

**Login Steps:**
1. Connect to Tailscale VPN
2. Open browser and navigate to system URL
3. Enter your username and password
4. Click "Login"

**First-Time Setup:**
- Your administrator will provide initial credentials
- Passwords are securely hashed using bcrypt
- Contact IT if you need a password reset

### Navigation Overview

The sidebar menu adapts based on your role. Common elements include:
- **Calendar:** View all bookings (all roles)
- **New Room Booking:** Create booking requests
- **New Device Booking:** Request off-site device rentals
- **Pricing Catalog:** View/edit pricing (admin roles)
- **Pending Approvals:** Review and assign rooms (Room Boss)
- **Inventory Dashboard:** View device stock levels
- **Notifications:** System alerts and messages

---

## Role-Based Guides

---

## Room Boss Guide

**Role:** `training_facility_admin`  
**Primary Function:** Room assignment and booking approval

### Your Responsibilities

1. **Review pending bookings** and assign appropriate rooms
2. **Check for conflicts** and make assignment decisions
3. **Override conflicts** when necessary with proper justification
4. **Reject bookings** that cannot be accommodated
5. **Monitor room utilization** and capacity

### Your Menu Access

- ✅ Dashboard
- ✅ Notifications
- ✅ Calendar
- ✅ Device Assignment Queue (view only)
- ✅ New Room Booking
- ✅ New Device Booking
- ✅ Pricing Catalog (full access)
- ✅ **Pending Approvals** (your primary workspace)
- ✅ Inventory Dashboard

### Daily Workflow

#### Morning Routine

1. **Check Notifications**
   - Click "Notifications" in sidebar
   - Review unread messages
   - Look for low stock alerts, new bookings

2. **Review Pending Approvals**
   - Click "Pending Approvals"
   - Review list of bookings awaiting room assignment
   - Prioritize by start date (earliest first)

#### Assigning a Room

1. Open a pending booking (click the expander)
2. Review client information:
   - Client name and contact details
   - Required dates
   - Headcount (learners + facilitators)
   - Catering needs
   - Device requirements

3. Check current room occupancy for the dates
4. Select a room from the dropdown
5. Review conflict check results:
   - ✅ **No conflicts:** Room is clear
   - ⚠️ **Conflicts detected:** See overlapping bookings

6. If conflicts exist:
   - Review the conflicting bookings
   - Determine if override is appropriate
   - Check "Override conflict" checkbox
   - Enter justification in notes

7. Click "✅ Assign Room"

8. Booking status changes to "Room Assigned"

#### Handling Capacity Issues

When headcount exceeds room capacity:
- System will show capacity warning
- Consider:
  - Can the client reduce attendees?
  - Is there a larger room available?
  - Can the booking be split across multiple rooms?
- Document decision in assignment notes

#### Rejecting a Booking

1. Open the pending booking
2. Click "❌ Reject Booking"
3. Enter clear rejection reason:
   - "No rooms available for requested dates"
   - "Capacity requirements exceed any available room"
   - "Insufficient notice for requested dates"
4. Click confirm
5. Requester will see rejection with reason

### Conflict Override Guidelines

**When to Override:**
- Same client extending existing booking
- Emergency/critical training needs
- Previous booking was cancelled but still shows
- Client is willing to share space

**When NOT to Override:**
- Different client already confirmed
- Would significantly disrupt existing booking
- No valid business justification

**Documentation Required:**
Always document override reason:
- "Client extending existing booking - same participants"
- "Emergency compliance training - regulatory requirement"
- "Previous booking cancelled per client request [reference]"

### Tips for Success

1. **Check dates carefully** - Ensure you're viewing the correct date range
2. **Consider catering needs** - Some rooms better suited for catering than others
3. **Factor in device requirements** - Rooms with built-in devices vs. those needing setup
4. **Long-term bookings** - A302, A303, Vision are offices (different display rules)
5. **Weekend bookings** - Calendar shows weekends in purple

---

## IT Boss Guide

**Role:** `it_rental_admin`  
**Primary Function:** Device assignment and off-site rental management

### Your Responsibilities

1. **Assign devices** to bookings from the assignment queue
2. **Track off-site rentals** and monitor return dates
3. **Resolve device conflicts** by reallocating or finding alternatives
4. **Monitor stock levels** and notify when reordering needed
5. **Process device-only bookings** for off-site rentals

### Your Menu Access

- ✅ Dashboard
- ✅ Notifications
- ✅ Calendar
- ✅ **Device Assignment Queue** (your primary workspace)
- ✅ New Room Booking
- ✅ New Device Booking
- ✅ Pricing Catalog (full access)
- ✅ Pending Approvals
- ✅ Inventory Dashboard

### Daily Workflow

#### Morning Routine

1. **Check Notifications**
   - Look for overdue returns
   - Review low stock alerts
   - Check conflict notifications

2. **Review Device Assignment Queue**
   - Click "Device Assignment Queue"
   - Default tab: "Pending"
   - Review bookings needing device assignment

3. **Check Off-Site Rentals**
   - Switch to "Off-site Requests" tab
   - Review rentals due to return soon
   - Identify overdue returns

#### Assigning Devices

1. In "Pending" tab, open a booking request
2. Review:
   - Client name and room
   - Dates (crucial for availability)
   - Device category requested
   - Quantity needed

3. System shows available devices:
   - ✅ **Devices available:** Shows count and serial numbers
   - ❌ **No devices:** Shows "Notify Bosses" option

4. If devices available:
   - Select serial numbers from multi-select dropdown
   - Must select exactly the requested quantity

5. Choose assignment type:
   - **On-site:** Standard assignment to room
   - **Off-site:** Additional form appears

6. For off-site rentals, complete:
   - Rental No/PO (required)
   - Contact person and phone (required)
   - Company name and address (required)
   - Expected return date (required)

7. Click assignment button

8. System creates assignment record

#### Handling No Stock Situations

When no devices are available:
1. Click "Notify Bosses - No Stock"
2. Notification sent to you and Room Boss
3. Options:
   - Procure additional devices
   - Negotiate different dates with client
   - Suggest alternative device categories
   - Decline the device portion of booking

#### Resolving Conflicts

1. Switch to "Conflicts" tab
2. Review listed conflicts:
   - Device serial number
   - Two bookings with overlapping dates
   - Client names for each

3. Options displayed:
   - **Alternative devices available:** Select alternative and reallocate
   - **No alternatives:** Notify IT Boss button

4. To reallocate:
   - Select alternative device from dropdown
   - Click "Reallocate to Alternative"
   - System moves device from conflicting booking
   - Alternative device assigned instead

#### Processing Off-Site Returns

1. In "Off-site Requests" tab
2. Find returned rental
3. Click "Mark as Returned"
4. System updates:
   - Rental record (returned_at timestamp)
   - Device status (back to 'available')

#### Creating Device-Only Bookings

For clients who only need devices (no room):
1. Click "New Device Booking"
2. Complete client information
3. Set rental period
4. Specify device quantities by category
5. Fill off-site details (required)
6. Submit
7. Booking goes directly to Device Assignment Queue

### Device Status Reference

| Status | Meaning | Action Needed |
|--------|---------|---------------|
| **available** | In inventory, ready for assignment | None |
| **assigned** | Assigned to a booking | Track return |
| **offsite** | Rented for off-site use | Monitor return date |
| **maintenance** | Under repair | Unavailable for assignment |

### Tips for Success

1. **Serial number tracking** - Always record exact serial numbers assigned
2. **Off-site details** - Complete all contact information for tracking
3. **Return dates** - Set realistic return dates, update if changes
4. **Conflict resolution** - Check with clients before reallocating active bookings
5. **Stock monitoring** - Watch for low stock alerts and plan procurement

---

## Admin Viewer Guide

**Role:** `training_facility_admin_viewer`  
**Primary Function:** View-only access for monitoring and planning

### Your Responsibilities

1. **Monitor calendar** for facility planning
2. **View bookings** for reporting
3. **Check pricing** for client quotes
4. **Review inventory** for stock awareness

### What You CAN Do

- ✅ View full calendar with all bookings
- ✅ See booking details (client, dates, requirements)
- ✅ View pricing catalog (read-only)
- ✅ See inventory levels
- ✅ Create booking requests (go to pending)
- ✅ Create device-only bookings

### What You CANNOT Do

- ❌ Assign rooms to bookings
- ❌ Approve or reject bookings
- ❌ Assign devices
- ❌ Edit pricing
- ❌ Override conflicts
- ❌ Export sensitive data

### Your Menu Access

- ❌ Dashboard (not available)
- ❌ Notifications (not available)
- ✅ Calendar
- ❌ Device Assignment Queue (not available)
- ✅ New Room Booking
- ✅ New Device Booking
- ✅ Pricing Catalog (view-only)
- ❌ Pending Approvals (not available)
- ✅ Inventory Dashboard (view-only)

### Daily Workflow

#### Calendar Monitoring

1. Click "Calendar"
2. Use controls:
   - "← Prev" / "Next →" for navigation
   - "Week" / "Month" toggle for view mode
   - "📅 Today" to return to current date

3. Review bookings:
   - Green = Today
   - Purple = Weekend
   - Blue = Weekday
   - Each cell shows: Client, headcount, catering, devices

#### Checking Pricing

1. Click "Pricing Catalog"
2. Browse by category:
   - Room pricing
   - Device category pricing
   - Catering pricing

3. Use for:
   - Client quotes
   - Budget planning
   - Cost comparisons

#### Creating Booking Requests

1. Click "New Room Booking"
2. Complete all required fields
3. **Note:** Your bookings go to "Pending" status
4. Room Boss will assign room later
5. You cannot select rooms directly

#### Creating Device Requests

1. Click "New Device Booking"
2. Complete client and rental information
3. Specify device needs
4. Provide off-site details
5. Request goes to IT Staff queue

### Limitations and Workarounds

| Limitation | Workaround |
|------------|------------|
| Cannot assign room | Create booking, it goes to pending queue |
| Cannot see notifications | Check calendar daily for updates |
| Cannot approve | Contact Room Boss for urgent needs |
| View-only pricing | Contact admin for pricing changes |

---

## Kitchen Staff Guide

**Role:** `kitchen_staff`  
**Primary Function:** Catering planning and kitchen operations

### Your Responsibilities

1. **Monitor daily headcounts** for meal preparation
2. **Track catering requirements** for each booking
3. **Plan kitchen capacity** based on calendar
4. **Identify low stock** for kitchen supplies

### Your Menu Access

- ❌ Dashboard
- ❌ Notifications
- ✅ **Kitchen Calendar** (your only access)
- ❌ Device Assignment Queue
- ❌ New Room Booking
- ❌ New Device Booking
- ❌ Pricing Catalog
- ❌ Pending Approvals
- ❌ Inventory Dashboard

### Daily Workflow

#### Morning Routine

1. Click "Kitchen Calendar"
2. Review today's bookings
3. Note:
   - **Headcounts** (learners + facilitators)
   - **Coffee/Tea** needs
   - **Morning catering** type
   - **Lunch catering** type

#### Weekly Planning

1. Switch to "Week" view
2. Navigate through upcoming week
3. Plan:
   - Bulk ingredient ordering
   - Staff scheduling
   - Prep work timing

#### Monthly Overview

1. Switch to "Month" view
2. Identify patterns:
   - High-volume days
   - Recurring bookings
   - Special catering needs

### What You See

The Kitchen Calendar shows:
- **Date** and **Room**
- **Client name**
- **Total headcount** (learners + facilitators)
- **Catering indicators:**
  - ☕ Coffee/Tea station
  - 🥪 Morning catering
  - 🍽️ Lunch catering
  - 📚 Stationery (not kitchen-related)
  - 💻 Devices (not kitchen-related)

### Sample Daily View

```
Monday, March 15

Excellence Room: ABC Corp
  👥 25+1=26 people
  ☕ Coffee/Tea
  🥪 Sandwiches (morning)
  🍽️ In-house (lunch)
  
Inspiration Room: XYZ Ltd
  👥 15+2=17 people
  ☕ Coffee/Tea
  🍽️ Self-catered (no kitchen work)

TOTAL KITCHEN WORKLOAD:
- Coffee/Tea: 43 people
- Morning sandwiches: 26 people
- In-house lunch: 26 people
```

### Stock Management

While you cannot directly update stock in the system:
1. Monitor low stock through visual indicators
2. Report needs to facilities manager
3. Track usage patterns for ordering

### Special Instructions

**For In-House Lunch (≥ 3 days):**
- System uses alternating auto-menu
- No special requests needed
- Standard prep applies

**For In-House Lunch (< 3 days):**
- Check catering notes for special requests
- May have specific dietary requirements
- Plan accordingly

---

## Common Tasks

### Creating a Booking (All Roles)

1. Click "New Room Booking"
2. Fill **Client Information**:
   - All fields marked * are required
   - Ensure email is valid format
   - Phone number required

3. Add **Booking Segments**:
   - Start and end dates
   - Room selection (if available to your role)
   - System checks for conflicts automatically

4. Specify **Attendees**:
   - Number of learners
   - Number of facilitators
   - Total calculated automatically

5. Select **Catering** options
6. Specify **Supplies** needed
7. Request **Devices** if needed
8. Review summary
9. Submit

### Checking Availability

**Via Calendar:**
1. Open Calendar
2. Navigate to desired date
3. Look for empty cells (white background)
4. Check room capacity vs. your needs

**Via New Booking:**
1. Start creating booking
2. Select dates and room
3. System shows conflict status automatically

### Viewing Booking Details

**Via Calendar:**
1. Find booking in grid
2. Hover or click for details
3. Shows: Client, headcount, catering, devices

**No direct search:**
- Use calendar navigation
- Filter by date range
- No search by client name currently

### Understanding Statuses

| Status | Meaning | Next Step |
|--------|---------|-----------|
| **Pending** | Awaiting room assignment | Room Boss action |
| **Room Assigned** | Room confirmed | IT Staff may assign devices |
| **Confirmed** | Fully approved | Ready for execution |
| **Rejected** | Cannot accommodate | Contact client |
| **Cancelled** | Booking cancelled | No action |

---

## Troubleshooting

### Cannot Login

**Problem:** "Invalid Credentials" error  
**Solution:**
1. Check Caps Lock is off
2. Verify username spelling
3. Reset password via admin if needed

### Database Unreachable

**Problem:** "🚨 CRITICAL: Database unreachable"  
**Solution:**
1. Verify Tailscale VPN is connected
2. Check network connection
3. Contact IT if VPN issues persist

### No Rooms Available

**Problem:** "No rooms found"  
**Solution:**
- This is a database connectivity issue
- Contact administrator

### Conflict Detection Error

**Problem:** Cannot check room conflicts  
**Solution:**
- Try different date range
- Contact IT if persistent

### Cannot Assign Device

**Problem:** "Failed to assign device"  
**Solution:**
1. Check you're logged in (session not expired)
2. Verify device still available
3. Try again or select different device
4. Contact IT if persistent

### Calendar Not Loading

**Problem:** Blank calendar or errors  
**Solution:**
1. Refresh page (F5)
2. Clear browser cache
3. Try different browser
4. Contact IT if persistent

### Permission Denied

**Problem:** "⛔ Access Denied"  
**Solution:**
- Your role doesn't have permission for this feature
- Contact administrator if you believe this is an error

### Contact Information

**Technical Issues:** IT Support  
**Access/Permissions:** System Administrator  
**Training:** Your Department Manager

---

**Document Owner:** Process & Workflow Documentation Team  
**Related Documents:** 
- WORKFLOWS.md - Business process workflows
- PROCESS_FLOWS.md - Detailed process flows
