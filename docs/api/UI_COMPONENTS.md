# Colab ERP UI Components

Complete documentation for Streamlit frontend components and views.

## Table of Contents

1. [Main Application (app.py)](#main-application-apppy)
2. [Booking Form (booking_form.py)](#booking-form-booking_formpy)
3. [Pricing Catalog (pricing_catalog.py)](#pricing-catalog-pricing_catalogpy)
4. [Authentication Components](#authentication-components)
5. [Calendar Views](#calendar-views)
6. [Device Management Views](#device-management-views)
7. [Role-Based Navigation](#role-based-navigation)

---

## Main Application (app.py)

**Location:** `src/app.py`

Main entry point for Colab ERP v2.2.0.

### Session State Management

#### `init_session_state()`
Initialize session state variables if they don't exist.

**Keys Initialized:**
```python
st.session_state['authenticated'] = False
st.session_state['username'] = None
st.session_state['role'] = None
```

**Calendar State:**
```python
st.session_state['calendar_view_mode'] = "Week"
st.session_state['calendar_week_offset'] = 0
st.session_state['calendar_month_offset'] = 0
```

---

### Authentication Views

#### `render_login()`
Login page with credential form.

**UI Elements:**
- Title: "🔐 Colab ERP Access"
- Caption: Version info
- Form fields: Username, Password
- Submit button: "Login"

**Example:**
```python
# Called automatically if not authenticated
render_login()
```

---

#### `check_login(username, password)`
Validate credentials and set session state.

**Success:**
```python
st.session_state['authenticated'] = True
st.session_state['username'] = user["username"]
st.session_state['role'] = user["role"]
```

**Error Display:**
- "Invalid Credentials" - Wrong username/password
- "🚨 CRITICAL: Database unreachable" - ConnectionError
- "🚨 CRITICAL: Auth secret missing" - KeyError

---

#### `logout()`
Hard reset of session state.

**Implementation:**
```python
st.session_state.clear()
st.rerun()
```

---

## Calendar Views

### `render_calendar_view()`

Professional Calendar Grid View v2 - Excel format with horizontal scrolling.

**Features:**
- Week/Month toggle
- Navigation buttons (Prev/Next, Today)
- Horizontal scrolling room grid
- Color-coded days (Today, Weekend, Weekday)
- Booking details with icons (👥, ☕, 🥪, 🍽️, 💻)

**Session State:**
```python
st.session_state.calendar_view_mode  # "Week" or "Month"
st.session_state.calendar_week_offset
st.session_state.calendar_month_offset
```

**UI Elements:**
```python
st.header("📅 Room Booking Calendar")

# Navigation
st.button("← Prev")
st.button("Next →")
st.segmented_control("View", ["Week", "Month"])
st.button("📅 Today")

# Scrollable grid with custom CSS
# 100px day column + 160px per room
```

**Cell Display Format:**
```
[CLIENT_NAME]
👥 [learners]+[facilitators]=[total]
🍽️ [Catering items]
✏️ [Stationery]
💻 [Device count]
```

**Long-term Offices (A302, A303, Vision):**
- Show client name only (no headcount)
- Still show catering/stationery/devices

---

### `render_week_view(today, rooms_df)`
Render week view with days as rows, rooms as columns.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `today` | `date` | Current date |
| `rooms_df` | `pd.DataFrame` | Room list from `get_rooms_for_calendar()` |

**Date Range:**
- Week start: Monday (calculated from `today + timedelta(weeks=offset)`)
- Week end: Sunday

**Grid Layout:**
```
          | Room1 | Room2 | Room3 | ... (160px each)
----------+-------+-------+-------+
Monday    |       |       |       |
Tuesday   |       |       |       |
...       |       |       |       |
```

---

### `render_month_view(today, rooms_df)`
Render month view with days as rows, rooms as columns.

**Date Range:**
- Month start: First day of current month
- Month end: Last day of current month
- Limited to 31 days for performance

---

## Booking Form (booking_form.py)

**Location:** `src/booking_form.py`

Enhanced Phase 3 booking form with Ghost Inventory workflow.

### `render_enhanced_booking_form()`

**Header:**
```python
st.header("📝 New Booking Request")
st.caption("Facility hours: 07:30 - 16:30 daily")
```

---

### Section 1: Client Information

**Layout:** 2 columns

**Fields:**
```python
with col1:
    client_name = st.text_input("Client/Company Name *", key="client_name")
    client_contact = st.text_input("Contact Person *", key="contact_person")

with col2:
    client_email = st.text_input("Email *", key="client_email")
    client_phone = st.text_input("Phone Number *", key="client_phone")
```

---

### Section 2: Booking Segments

**Multi-room Support:**
- Same client, multiple date ranges
- Different rooms per segment

**Session State:**
```python
st.session_state.booking_segments = []  # List of segment dicts
```

**Segment Display:**
```python
for i, segment in enumerate(st.session_state.booking_segments):
    st.write(f"{i+1}. {segment['start_date']} to {segment['end_date']} | Room: {segment['room_name']}")
    st.button("❌ Remove", key=f"remove_seg_{i}")
```

---

### Section 3: Add Segment Form

**Fields:**
```python
seg_start = st.date_input("Start Date *", min_value=date.today(), key="seg_start", on_change=on_start_date_change)
seg_end = st.date_input("End Date *", key="seg_end")
```

**Room Selection:**
```python
room_options = all_rooms['id'].tolist()
selected_room_id = st.selectbox(
    "Select Room *",
    options=room_options,
    format_func=lambda x: f"{room_name} (Capacity: {capacity})"
)
```

**Conflict Checking:**
```python
conflict_info = availability_service.check_room_conflicts(selected_room_id, seg_start, seg_end)
if conflict_info['has_conflict']:
    st.error(f"🚫 **CONFLICT DETECTED**: {conflict_info['message']}")
```

---

### Section 4: Attendees

**Layout:** 3 columns

**Fields:**
```python
num_learners = st.number_input("Number of Learners *", min_value=0, value=0, step=1)
num_facilitators = st.number_input("Number of Facilitators *", min_value=0, value=0, step=1)
st.metric("Total Headcount", num_learners + num_facilitators)
```

---

### Section 5: Catering

**Options:**
```python
coffee_tea = st.checkbox("Coffee/Tea Station")

morning_catering = st.selectbox(
    "Morning Catering",
    options=['none', 'pastry', 'sandwiches'],
    format_func=lambda x: {
        'none': 'None',
        'pastry': 'Pastry',
        'sandwiches': 'Sandwiches'
    }[x]
)

lunch_catering = st.selectbox(
    "Lunch Catering",
    options=['none', 'self_catered', 'in_house']
)

# Conditional notes field
if lunch_catering == 'in_house':
    catering_notes = st.text_area("Catering Requests")
```

---

### Section 6: Supplies

**Fields:**
```python
stationery = st.checkbox("Stationery (Pen & Book) - Per person")
water_bottles = st.number_input("Water Bottles (per day)", min_value=0, value=0, step=1)
```

---

### Section 7: Devices

**Fields:**
```python
devices_needed = st.number_input("Devices Needed", min_value=0, value=0, step=1)

device_type = st.selectbox(
    "Device Type Preference",
    options=[None, 'any', 'laptops', 'desktops'],
    format_func=lambda x: {
        None: 'None',
        'any': 'Any',
        'laptops': 'Laptops Only',
        'desktops': 'Desktops Only'
    }[x]
)
```

**Availability Check:**
```python
if devices_needed > 0:
    device_check = availability_service.check_device_availability(
        devices_needed, start_date, end_date, device_type
    )
    if not device_check['available']:
        st.error(f"❌ {device_check['message']}")
    else:
        st.success(device_check['message'])
```

---

### Submit Button

```python
if st.button("🚀 Submit Booking Request", type="primary", use_container_width=True):
    # Validation
    if errors:
        for error in errors:
            st.error(f"❌ {error}")
    else:
        # Create bookings for all segments
        for segment in st.session_state.booking_segments:
            result = booking_service.create_enhanced_booking(...)
            
        if created_bookings:
            st.success(f"✅ Successfully created {len(created_bookings)} booking(s)!")
            st.balloons()
```

---

## Device Booking Form

### `render_new_device_booking()`

Device-only booking for off-site rental (no room required).

**Header:**
```python
st.header("🖥️ New Device Booking")
st.caption("Request devices for off-site rental (no room required)")
```

**Client Information:** Same as room booking

**Rental Period:**
```python
start_date = st.date_input("Start Date *", min_value=date.today())
end_date = st.date_input("End Date *", min_value=start_date)
```

**Device Requirements:**
```python
for category in categories:
    qty = st.number_input(f"{category['name']} Quantity", min_value=0, value=0, step=1)
    if qty > 0:
        available = availability_service.get_available_device_count(category['id'], start_date, end_date)
        if available < qty:
            st.error(f"⚠️ Only {available} available")
        else:
            st.success(f"✅ {available} available")
```

**Off-site Details:**
```python
rental_no = st.text_input("Rental Number/PO *")
contact_person = st.text_input("On-site Contact Person *")
contact_number = st.text_input("Contact Number *")
contact_email = st.text_input("Contact Email")
company = st.text_input("Company Name *")
address = st.text_area("Delivery Address *")
return_date = st.date_input("Expected Return Date *")
```

**Submit:**
```python
if st.button("🚀 Submit Device Booking", type="primary", use_container_width=True):
    result = booking_service.create_device_only_booking(...)
```

---

## Pricing Catalog (pricing_catalog.py)

**Location:** `src/pricing_catalog.py`

Complete pricing management with three sections.

### `render_pricing_catalog(pricing_service, user_role)`

**Access Control:**
```python
allowed_roles = ['admin', 'it_admin', 'training_facility_admin', 'it_rental_admin']
if user_role not in allowed_roles:
    st.error("⛔ Access Denied: Only admin and IT admin can view pricing information.")
    return
```

**Tabs:**
```python
tab_rooms, tab_devices, tab_catering = st.tabs([
    "🏢 Room Pricing",
    "💻 Device Pricing",
    "☕ Catering & Supplies"
])
```

---

### Room Pricing Tab

**Current Pricing Display:**
```python
for room in room_pricing:
    with st.expander(f"{room['item_name']} (Capacity: {max_capacity})"):
        col1, col2, col3 = st.columns(3)
        col1.write(f"Daily: R{daily_rate:.2f}")
        col2.write(f"Weekly: R{weekly_rate:.2f}")
        col3.write(f"Monthly: R{monthly_rate:.2f}")
        st.button(f"Edit {room['item_name']}", key=f"edit_room_{room['id']}")
```

**Add New Pricing:**
```python
rooms_without = pricing_service.get_rooms_without_pricing()
if rooms_without.empty:
    st.info("All rooms have pricing set up.")
else:
    selected = st.selectbox("Select Room", room_options)
    daily = st.number_input("Daily Rate (R)", min_value=0.0, step=50.0)
    weekly = st.number_input("Weekly Rate (R)", min_value=0.0, step=100.0)
    monthly = st.number_input("Monthly Rate (R)", min_value=0.0, step=500.0)
    notes = st.text_area("Notes")
    st.button("Add Room Pricing")
```

---

### Device Pricing Tab

**Collective by Category:**
```python
for device in device_pricing:
    with st.expander(f"{device['item_name']} ({device_count} devices)"):
        # Show daily/weekly/monthly rates
```

---

### Catering Tab

**Current Items:**
```python
for item in catering_pricing:
    with st.expander(f"{item['item_name']}"):
        st.write(f"Price: R{item['unit_price']:.2f} {item['unit']}")
        st.button("Edit", key=f"edit_cater_{item['id']}")
        st.button("Delete", key=f"del_cater_{item['id']}")
```

**Add New Item:**
```python
item_name = st.text_input("Item Name", placeholder="e.g., Coffee/Tea Station")
unit_price = st.number_input("Unit Price (R)", min_value=0.0, step=5.0)
unit = st.selectbox("Unit", ["per person", "per item", "per day", "per booking"])
```

---

### Edit Mode

**Session State Pattern:**
```python
if st.button(f"Edit {room['item_name']}"):
    st.session_state['editing_room'] = room['id']
    st.session_state['edit_room_name'] = room['item_name']
    st.session_state['edit_daily'] = float(room['daily_rate'])
    st.rerun()

if 'editing_room' in st.session_state:
    # Show edit form
    new_daily = st.number_input("Daily Rate (R)", value=st.session_state['edit_daily'])
    st.button("💾 Save Changes", type="primary")
    st.button("❌ Cancel")
```

---

## Pending Approvals View

### `render_pending_approvals()`

Room Boss interface for ghost inventory room assignments.

**Header:**
```python
st.header("⏳ Pending Room Approvals")
st.caption("Ghost Inventory: Assign rooms to pending bookings")
```

**Pending Count:**
```python
pending_df = room_approval_service.get_pending_bookings()
st.write(f"📋 **{len(pending_df)} booking(s) pending room assignment**")
```

**Booking Display (per booking):**
```python
with st.expander(f"Booking #{booking_id} - {client_name} ({start_date} to {end_date})"):
    # Client info
    col1, col2 = st.columns(2)
    col1.write(f"**👤 Client Details**")
    col1.write(f"Name: {client_name}")
    col1.write(f"Contact: {contact_person}")
    
    # Requirements
    col2.write(f"**📊 Requirements**")
    col2.write(f"Headcount: {total_headcount}")
    
    # Room Assignment
    st.write("**🚪 Room Assignment**")
    selected_room = st.selectbox("Select Room", room_options)
    
    # Conflict check
    if conflict_check['has_conflict']:
        st.warning(conflict_check['message'])
        override = st.checkbox("⚠️ Override conflict and assign anyway")
    
    # Action buttons
    st.button("✅ Assign Room")
    st.button("❌ Reject Booking")
```

---

## Inventory Dashboard

### `render_inventory_dashboard()`

Complete inventory dashboard with real-time status.

**Header:**
```python
st.header("📦 Inventory Dashboard")
st.caption("Real-time device inventory and availability status")
```

**Summary Metrics:**
```python
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Devices", summary['total_devices'])
col2.metric("Available", summary['available'], delta=f"{available_percent:.0f}%")
col3.metric("Assigned", summary['assigned'])
col4.metric("Off-site", summary['offsite'])
```

**Categories Grid:**
```python
categories = device_manager.get_device_categories()
cols = st.columns(len(categories))

for idx, (_, cat) in enumerate(categories.iterrows()):
    with cols[idx]:
        st.write(f"**{cat['name']}**")
        cat_stats = device_manager.get_category_stats(cat['id'])
        st.metric("Total", cat_stats['total'])
        st.metric("Available", cat_stats['available'])
        if cat_stats['low_stock']:
            st.warning("⚠️ Low Stock!")
```

**Filtered Device List:**
```python
# Filters
cols = st.columns(3)
filter_status = cols[0].selectbox("Status Filter", ["All", "Available", "Assigned", "Off-site", "Maintenance"])
filter_category = cols[1].selectbox("Category Filter", ["All"] + categories)
search_serial = cols[2].text_input("Search by Serial")

# Styled dataframe
devices_df = device_manager.get_devices_detailed(...)
st.dataframe(devices_df.style.applymap(color_status, subset=['status']))
```

**Recent Activity:**
```python
activity_df = device_manager.get_recent_activity(limit=20)
st.dataframe(activity_df, column_config={...})
```

**Export:**
```python
if st.button("📥 Export Full Inventory (CSV)"):
    csv_data = device_manager.export_inventory_csv()
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"inventory_export_{date.today()}.csv",
        mime="text/csv"
    )
```

---

## Notifications View

### `render_notifications()`

Notifications page for IT Boss and Room Boss.

**Header:**
```python
st.header("🔔 Notifications")
```

**Metrics:**
```python
summary = notification_manager.get_daily_summary(notification_role)
col1.metric("Total (24h)", summary['total_24h'])
col2.metric("Unread (24h)", summary['unread_24h'])
col3.metric("Total Unread", unread_count)
```

**Filter Tabs:**
```python
filter_tabs = st.tabs(["All", "Unread", "Low Stock", "Conflicts", "Overdue"])
```

**Notification Display:**
```python
for _, notif in notifications_df.iterrows():
    # Icon based on type
    icon = "⚠️" if notif['type'] == 'low_stock' else "🔴"
    
    # Styling
    bg_color = "#fff3cd" if not notif['is_read'] else "#f8f9fa"
    border_left = "4px solid #ffc107" if not not notif['is_read'] else "4px solid #dee2e6"
    
    st.markdown(f"""
    <div style="background-color: {bg_color}; border-left: {border_left}; padding: 10px;">
        <b>{icon} {notif['type']}</b> <span style="color: #6c757d;">({time_str})</span>
    </div>
    "", unsafe_allow_html=True)
    
    if not notif['is_read']:
        st.button("Mark as Read", key=f"read_{notif['id']}")
```

---

## Device Assignment Queue

### `render_device_assignment_queue()`

IT Staff interface for manual device assignment.

**Header:**
```python
st.header("🔧 Device Assignment Queue")
```

**Filter Tabs:**
```python
filter_tabs = st.tabs(["Pending", "Off-site Requests", "Conflicts", "All"])
```

### Pending Assignments

**Display Pattern:**
```python
with st.expander(f"📋 Booking #{booking_id} - {client_name} ({room_name})"):
    # Client info
    col1, col2 = st.columns(2)
    col1.write(f"**Client:** {client_name}")
    col2.write(f"**Room:** {room_name}")
    
    # Device requests
    for request in booking_requests:
        st.write(f"**Device Request:** {quantity}x {category}")
        
        # Available devices
        available = device_manager.get_available_devices(category, start, end)
        if available.empty:
            st.error(f"⚠️ No {category}s available!")
        else:
            selected_serials = st.multiselect(
                f"Select {category}s (Serial Numbers)",
                options=available['serial_number'].tolist()
            )
            
            # Off-site option
            is_offsite = st.checkbox("Off-site Rental")
            
            if is_offsite:
                with st.form(key=f"offsite_form_{request_id}"):
                    rental_no = st.text_input("Rental No")
                    contact_person = st.text_input("Contact Person")
                    # ... more fields
                    st.form_submit_button("Assign with Off-site Details")
            else:
                st.button(f"Assign {len(selected_serials)} Devices")
```

---

## Role-Based Navigation

### `main()` - Navigation Controller

**Role Detection:**
```python
user_role = st.session_state['role']
```

**Menu by Role:**

**Room Boss (training_facility_admin):**
```python
menu = [
    "Dashboard", "Notifications", "Calendar", 
    "Device Assignment Queue", "New Room Booking",
    "New Device Booking", "Pricing Catalog", 
    "Pending Approvals", "Inventory Dashboard"
]
```

**IT Boss (it_rental_admin):**
```python
menu = [
    "Dashboard", "Notifications", "Calendar",
    "Device Assignment Queue", "New Room Booking",
    "New Device Booking", "Pricing Catalog",
    "Pending Approvals", "Inventory Dashboard"
]
```

**Viewer (training_facility_admin_viewer):**
```python
menu = [
    "Calendar", "Bookings", "Pricing Catalog",
    "Approvals", "Inventory Dashboard"
]
```

**Kitchen Staff:**
```python
menu = ["Kitchen Calendar"]
```

**Staff/Default:**
```python
menu = [
    "Calendar", "New Room Booking", "New Device Booking",
    "Pending Approvals", "Inventory Dashboard"
]
```

**Navigation Display:**
```python
st.sidebar.title("Colab ERP v2.2.0")
st.sidebar.caption(f"User: {username} ({role})")
st.sidebar.info("System Status: 🟢 Online (Headless)")

choice = st.sidebar.radio("Navigation", menu)
st.sidebar.button("🔴 Logout")
```

---

## Streamlit Configuration

### Page Config

```python
st.set_page_config(
    page_title="Colab ERP v2.2.0",
    layout="wide"
)
```

### Custom CSS

**Calendar Scroll Container:**
```python
st.markdown("""
<style>
.calendar-scroll-container {
    overflow-x: scroll;
    white-space: nowrap;
    width: 100%;
    border: none;
    scrollbar-width: none;
    -ms-overflow-style: none;
}
.calendar-scroll-container::-webkit-scrollbar {
    display: none;
}
.calendar-grid {
    display: inline-block;
    min-width: 3500px;
    background: transparent;
}
.calendar-cell {
    display: inline-block;
    width: 160px;
    height: 110px;
    border: 1px solid #ccc;
    padding: 6px;
    font-size: 11px;
    vertical-align: top;
}
.calendar-header {
    display: inline-block;
    width: 160px;
    height: 50px;
    border: 1px solid #ccc;
    padding: 8px;
    font-size: 12px;
    font-weight: bold;
    text-align: center;
    background-color: #f5f5f5;
}
</style>
""", unsafe_allow_html=True)
```

---

## Common UI Patterns

### Success/Error Feedback

```python
# Success
st.success(f"✅ Booking #{booking_id} created successfully!")
st.balloons()

# Error
st.error(f"❌ {error_message}")

# Warning
st.warning("⚠️ Low stock warning!")

# Info
st.info("📋 Please add at least one booking segment")
```

### Form Validation

```python
errors = []
if not client_name:
    errors.append("Client name is required")
if not st.session_state.booking_segments:
    errors.append("Please add at least one booking segment")

if errors:
    for error in errors:
        st.error(f"❌ {error}")
else:
    # Process form
```

### Loading States

```python
import time

st.success("Operation completed!")
time.sleep(1)  # Brief pause for user to read
st.rerun()  # Refresh the page
```

---

## See Also

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Service Guide](SERVICE_GUIDE.md) - Business logic services
- [Database Interface](DATABASE_INTERFACE.md) - Database operations
