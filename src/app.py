import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import src.db as db
import src.auth as auth
import time
import pandas as pd
from datetime import datetime, timedelta, date

# Import Device Manager and Notification Manager
from src.models import DeviceManager, NotificationManager, AvailabilityService

# Page Config
st.set_page_config(page_title="Colab ERP v2.2.0", layout="wide")

# Initialize Managers
device_manager = DeviceManager()
notification_manager = NotificationManager()
availability_service = AvailabilityService()

# ----------------------------------------------------------------------------
# AUTHENTICATION
# ----------------------------------------------------------------------------

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'role' not in st.session_state:
        st.session_state['role'] = None

def check_login(username, password):
    """
    DB-backed credential check (bcrypt).
    """
    try:
        user = auth.authenticate(username, password)
        if not user:
            st.error("Invalid Credentials")
            return

        st.session_state['authenticated'] = True
        st.session_state['username'] = user["username"]
        st.session_state['role'] = user["role"]
        st.success(f"Login Successful ({user['role']})")
        time.sleep(0.5)
        st.rerun()

    except ConnectionError as e:
        st.error(f"🚨 CRITICAL: Database unreachable: {e}")
        st.info("Fix: verify Tailscale is up, the secrets.toml host IP is correct, and PostgreSQL is listening on the VPN interface.")
        return
    except KeyError as e:
        st.error(f"🚨 CRITICAL: Auth secret missing: {e}")
        st.stop()

def logout():
    """
    Hard reset of session state.
    """
    st.session_state.clear() # Wipes everything
    st.rerun()

def render_login():
    st.title("🔐 Colab ERP Access")
    st.caption("v2.2.0 Production | Unauthorized Access Prohibited")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            check_login(username, password)

# ----------------------------------------------------------------------------
# VIEW MODULES (Pure UI - No SQL)
# ----------------------------------------------------------------------------

def render_calendar_view():
    """
    Professional Calendar Grid View v2 - Excel format
    Layout: Days as rows, Rooms as columns
    """
    st.header("📅 Room Booking Calendar")
    
    # DEBUG: Start of function (commented out for production)
    # st.write("DEBUG: Starting render_calendar_view()")
    
    # Initialize calendar state
    if 'calendar_view_mode' not in st.session_state:
        st.session_state.calendar_view_mode = "Week"
    if 'calendar_week_offset' not in st.session_state:
        st.session_state.calendar_week_offset = 0
    if 'calendar_month_offset' not in st.session_state:
        st.session_state.calendar_month_offset = 0
    
    # DEBUG: Show current state (commented out for production)
    # st.write(f"DEBUG: View mode = {st.session_state.calendar_view_mode}")
    # st.write(f"DEBUG: Week offset = {st.session_state.calendar_week_offset}")
    
    # View mode toggle and navigation
    col1, col2, col3, col4 = st.columns([1, 1, 2, 2])
    
    with col1:
        if st.button("← Prev", key="prev_period"):
            if st.session_state.calendar_view_mode == "Week":
                st.session_state.calendar_week_offset -= 1
            else:
                st.session_state.calendar_month_offset -= 1
            st.rerun()
    
    with col2:
        if st.button("Next →", key="next_period"):
            if st.session_state.calendar_view_mode == "Week":
                st.session_state.calendar_week_offset += 1
            else:
                st.session_state.calendar_month_offset += 1
            st.rerun()
    
    with col3:
        view_mode = st.segmented_control("View", ["Week", "Month"], 
                                        default=st.session_state.calendar_view_mode,
                                        key="view_mode_selector")
        if view_mode != st.session_state.calendar_view_mode:
            st.session_state.calendar_view_mode = view_mode
            st.rerun()
    
    with col4:
        if st.button("📅 Today", key="go_today"):
            st.session_state.calendar_week_offset = 0
            st.session_state.calendar_month_offset = 0
            st.rerun()
    
    # Calculate date range
    today = date.today()
    # st.write(f"DEBUG: Today = {today}")
    
    # Fetch rooms first (needed for both views)
    try:
        rooms_df = db.get_rooms_for_calendar()
        # st.write(f"DEBUG: Found {len(rooms_df)} rooms")
        
        if rooms_df.empty:
            st.warning("No rooms found.")
            return
        
        if st.session_state.calendar_view_mode == "Week":
            render_week_view(today, rooms_df)
        else:  # Month view
            render_month_view(today, rooms_df)
            
    except ConnectionError as e:
        st.error(f"🚨 Database unreachable: {e}")
    except Exception as e:
        st.error(f"❌ Error loading calendar: {e}")
        st.exception(e)

def render_week_view(today, rooms_df):
    """Render week view with days as rows, rooms as columns - Excel style with horizontal scrolling"""
    
    # Calculate week start (Monday)
    week_start = today + timedelta(weeks=st.session_state.calendar_week_offset)
    week_start = week_start - timedelta(days=week_start.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday
    
    st.subheader(f"Week of {week_start.strftime('%d %b %Y')} - {week_end.strftime('%d %b %Y')}")
    
    # Fetch calendar data
    calendar_df = db.get_calendar_grid(week_start, week_end)
    
    # Process data
    if not calendar_df.empty:
        # Convert booking_date to date for comparison
        calendar_df['booking_date'] = pd.to_datetime(calendar_df['booking_date']).dt.date
    
    # Create calendar grid with horizontal scrolling
    num_rooms = len(rooms_df)
    
    # Start scrollable container
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
        width: 140px;
        height: 90px;
        border: 1px solid #ccc;
        padding: 8px;
        font-size: 11px;
        vertical-align: top;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: normal;
        box-sizing: border-box;
    }
    .calendar-header {
        display: inline-block;
        width: 140px;
        height: 50px;
        border: 1px solid #ccc;
        padding: 8px;
        font-size: 11px;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        background-color: #f5f5f5;
        color: black;
        box-sizing: border-box;
    }
    .day-cell {
        display: inline-block;
        width: 100px;
        height: 90px;
        border: 1px solid #ccc;
        padding: 8px;
        font-size: 11px;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        color: black;
        box-sizing: border-box;
    }
    .day-header {
        display: inline-block;
        width: 100px;
        height: 50px;
        border: 1px solid #ccc;
        padding: 8px;
        font-size: 11px;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        background-color: #e3f2fd;
        color: black;
        box-sizing: border-box;
    }
    .calendar-row {
        display: block;
        white-space: nowrap;
    }
    </style>
    <div class="calendar-scroll-container">
        <div class="calendar-grid">
    """, unsafe_allow_html=True)
    
    # Header row
    header_html = '<div class="calendar-row">'
    header_html += '<div class="day-header">Day / Room</div>'
    
    for idx, (_, room) in enumerate(rooms_df.iterrows()):
        room_name = room['name']
        header_html += f'<div class="calendar-header">{room_name}</div>'
    
    header_html += '</div>'
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Day rows
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day_idx, day_name in enumerate(days):
        current_date = week_start + timedelta(days=day_idx)
        is_weekend = day_idx >= 5  # Sat=5, Sun=6
        is_today = current_date == today
        
        # Day cell styling
        if is_today:
            day_bg = "#28a745"
            day_color = "white"
        elif is_weekend:
            day_bg = "#6f42c1"
            day_color = "white"
        else:
            day_bg = "#e3f2fd"
            day_color = "black"
        
        row_html = '<div class="calendar-row">'
        row_html += f'<div class="day-cell" style="background-color: {day_bg}; color: {day_color};">{day_name[:3]}<br/>{current_date.strftime("%d")}</div>'
        
        # Room cells for this day
        for room_idx, (_, room) in enumerate(rooms_df.iterrows()):
            room_id = room['id']
            room_name = room['name']
            
            # Find booking for this room and date
            booking = calendar_df[
                (calendar_df['room_id'] == room_id) & 
                (calendar_df['booking_date'] == current_date)
            ]
            
            if not booking.empty and pd.notna(booking.iloc[0]['booking_id']):
                # Has booking
                client = booking.iloc[0]['client_name']
                
                # Long-term offices: show client name only (no headcount)
                if room_name in ['A302', 'A303', 'Vision']:
                    cell_text = f"<b>{client}</b>"
                else:
                    # Normal rooms with headcount
                    learners = int(booking.iloc[0]['learners_count']) if pd.notna(booking.iloc[0]['learners_count']) else 0
                    devices = int(booking.iloc[0]['device_count']) if pd.notna(booking.iloc[0]['device_count']) else 0
                    
                    # Excel format: learners + 1 facilitator (always minimum 1)
                    cell_text = f"<b>{client}</b><br/>{learners}+1"
                    if devices > 0:
                        cell_text += f" (+ {devices})"
                
                # Cell styling
                if is_today:
                    bg_color = "#d4edda"
                elif is_weekend:
                    bg_color = "#e8d5f2"
                else:
                    bg_color = "#e3f2fd"
                
                row_html += f'<div class="calendar-cell" style="background-color: {bg_color}; color: black;">{cell_text}</div>'
            else:
                # Empty cell
                if is_today:
                    bg_color = "#d4edda"
                elif is_weekend:
                    bg_color = "#f3e5f5"
                else:
                    bg_color = "#ffffff"
                
                row_html += f'<div class="calendar-cell" style="background-color: {bg_color};"></div>'
        
        row_html += '</div>'
        st.markdown(row_html, unsafe_allow_html=True)
    
    # Close scrollable container
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Legend
    st.markdown("---")
    legend_cols = st.columns(4)
    legend_cols[0].markdown("<div style='background-color: #28a745; padding: 5px; border-radius: 4px; color: black; text-align: center; font-size: 12px;'>🟢 Today</div>", unsafe_allow_html=True)
    legend_cols[1].markdown("<div style='background-color: #6f42c1; padding: 5px; border-radius: 4px; color: black; text-align: center; font-size: 12px;'>🟣 Weekend</div>", unsafe_allow_html=True)
    legend_cols[2].markdown("<div style='background-color: #e3f2fd; padding: 5px; border-radius: 4px; color: black; text-align: center; font-size: 12px;'>🔵 Weekday</div>", unsafe_allow_html=True)
    legend_cols[3].markdown("<div style='background-color: #d4edda; padding: 5px; border-radius: 4px; color: black; text-align: center; font-size: 12px;'>📅 Booked</div>", unsafe_allow_html=True)

def render_month_view(today, rooms_df):
    """Render month view with days as rows, rooms as columns - Excel style with horizontal scrolling"""
    from dateutil.relativedelta import relativedelta
    
    current_month = today + relativedelta(months=st.session_state.calendar_month_offset)
    month_start = current_month.replace(day=1)
    
    # Get last day of month
    if current_month.month == 12:
        next_month = current_month.replace(year=current_month.year + 1, month=1, day=1)
    else:
        next_month = current_month.replace(month=current_month.month + 1, day=1)
    month_end = next_month - timedelta(days=1)
    
    st.subheader(f"{current_month.strftime('%B %Y')}")
    
    # Fetch calendar data for entire month
    calendar_df = db.get_calendar_grid(month_start, month_end)
    
    # Process data
    if not calendar_df.empty:
        # Convert booking_date to date for comparison
        calendar_df['booking_date'] = pd.to_datetime(calendar_df['booking_date']).dt.date
    
    # Create calendar grid with horizontal scrolling (same as week view)
    num_rooms = len(rooms_df)
    
    # Start scrollable container (same styling as week view)
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
        width: 140px;
        height: 90px;
        border: 1px solid #ccc;
        padding: 8px;
        font-size: 11px;
        vertical-align: top;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: normal;
        box-sizing: border-box;
    }
    .calendar-header {
        display: inline-block;
        width: 140px;
        height: 50px;
        border: 1px solid #ccc;
        padding: 8px;
        font-size: 11px;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        background-color: #f5f5f5;
        color: black;
        box-sizing: border-box;
    }
    .day-cell {
        display: inline-block;
        width: 100px;
        height: 90px;
        border: 1px solid #ccc;
        padding: 8px;
        font-size: 11px;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        color: black;
        box-sizing: border-box;
    }
    .day-header {
        display: inline-block;
        width: 100px;
        height: 50px;
        border: 1px solid #ccc;
        padding: 8px;
        font-size: 11px;
        font-weight: bold;
        text-align: center;
        vertical-align: middle;
        background-color: #e3f2fd;
        color: black;
        box-sizing: border-box;
    }
    .calendar-row {
        display: block;
        white-space: nowrap;
    }
    </style>
    <div class="calendar-scroll-container">
        <div class="calendar-grid">
    """, unsafe_allow_html=True)
    
    # Header row
    header_html = '<div class="calendar-row">'
    header_html += '<div class="day-header">Day / Room</div>'
    
    for idx, (_, room) in enumerate(rooms_df.iterrows()):
        room_name = room['name']
        header_html += f'<div class="calendar-header">{room_name}</div>'
    
    header_html += '</div>'
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Generate all days in month
    current_date = month_start
    day_count = 0
    
    while current_date <= month_end:
        is_weekend = current_date.weekday() >= 5
        is_today = current_date == today
        
        # Day cell styling (same as week view)
        day_name = current_date.strftime('%a')
        if is_today:
            day_bg = "#28a745"
            day_color = "white"
        elif is_weekend:
            day_bg = "#6f42c1"
            day_color = "white"
        else:
            day_bg = "#e3f2fd"
            day_color = "black"
        
        row_html = '<div class="calendar-row">'
        row_html += f'<div class="day-cell" style="background-color: {day_bg}; color: {day_color};">{day_name}<br/>{current_date.strftime("%d")}</div>'
        
        # Room cells for this day
        for room_idx, (_, room) in enumerate(rooms_df.iterrows()):
            room_id = room['id']
            room_name = room['name']
            
            # Find booking for this room and date
            booking = calendar_df[
                (calendar_df['room_id'] == room_id) & 
                (calendar_df['booking_date'] == current_date)
            ]
            
            if not booking.empty and pd.notna(booking.iloc[0]['booking_id']):
                # Has booking
                client = booking.iloc[0]['client_name']
                
                # Long-term offices: show client name only (no headcount)
                if room_name in ['A302', 'A303', 'Vision']:
                    cell_text = f"<b>{client}</b>"
                else:
                    # Normal rooms with headcount
                    learners = int(booking.iloc[0]['learners_count']) if pd.notna(booking.iloc[0]['learners_count']) else 0
                    devices = int(booking.iloc[0]['device_count']) if pd.notna(booking.iloc[0]['device_count']) else 0
                    
                    # Excel format: learners + 1 facilitator
                    cell_text = f"<b>{client}</b><br/>{learners}+1"
                    if devices > 0:
                        cell_text += f" (+ {devices})"
                
                # Cell styling (same as week view)
                if is_today:
                    bg_color = "#d4edda"
                elif is_weekend:
                    bg_color = "#e8d5f2"
                else:
                    bg_color = "#e3f2fd"
                
                row_html += f'<div class="calendar-cell" style="background-color: {bg_color}; color: black;">{cell_text}</div>'
            else:
                # Empty cell
                if is_today:
                    bg_color = "#d4edda"
                elif is_weekend:
                    bg_color = "#f3e5f5"
                else:
                    bg_color = "#ffffff"
                
                row_html += f'<div class="calendar-cell" style="background-color: {bg_color};"></div>'
        
        row_html += '</div>'
        st.markdown(row_html, unsafe_allow_html=True)
        
        current_date += timedelta(days=1)
        day_count += 1
        
        # Limit display for performance (show max 31 days)
        if day_count > 31:
            st.warning("Month display limited to 31 days for performance")
            break
    
    # Close scrollable container
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Legend (same as week view)
    st.markdown("---")
    legend_cols = st.columns(4)
    legend_cols[0].markdown("<div style='background-color: #28a745; padding: 5px; border-radius: 4px; color: black; text-align: center; font-size: 12px;'>🟢 Today</div>", unsafe_allow_html=True)
    legend_cols[1].markdown("<div style='background-color: #6f42c1; padding: 5px; border-radius: 4px; color: black; text-align: center; font-size: 12px;'>🟣 Weekend</div>", unsafe_allow_html=True)
    legend_cols[2].markdown("<div style='background-color: #e3f2fd; padding: 5px; border-radius: 4px; color: black; text-align: center; font-size: 12px;'>🔵 Weekday</div>", unsafe_allow_html=True)
    legend_cols[3].markdown("<div style='background-color: #d4edda; padding: 5px; border-radius: 4px; color: black; text-align: center; font-size: 12px;'>📅 Booked</div>", unsafe_allow_html=True)

def render_new_room_booking():
    st.header("📝 New Room Booking")

def render_new_device_booking():
    st.header("🖥️ New Device Booking")
    st.info("🚧 Coming Soon - Device booking functionality will be implemented in Phase 3")

def render_pricing_catalog():
    st.header("💰 Pricing Catalog")
    st.info("🚧 Coming Soon - Room and device pricing information")

def render_pending_approvals():
    st.header("⏳ Pending Approvals")
    st.info("🚧 Coming Soon - Booking approval workflow")

def render_inventory_dashboard():
    st.header("📦 Inventory Dashboard")
    st.info("🚧 Coming Soon - Device inventory management")

def render_notifications():
    """
    Notifications page for IT Boss and Room Boss.
    Shows low stock alerts, conflicts, and overdue returns.
    """
    st.header("🔔 Notifications")
    
    # Get user's role
    user_role = st.session_state.get('role')
    
    # Map role to notification recipient
    # admin (training_facility_admin) = room_boss
    # it_admin (it_rental_admin) = it_boss
    role_mapping = {
        'admin': 'admin',
        'training_facility_admin': 'room_boss',
        'it_rental_admin': 'it_boss',
        'it_admin': 'it_boss',
        'it_boss': 'it_boss',
        'room_boss': 'room_boss'
    }
    
    notification_role = role_mapping.get(user_role, user_role)
    
    # Get unread count for badge
    unread_count = notification_manager.get_unread_count(notification_role)
    
    # Show daily summary
    summary = notification_manager.get_daily_summary(notification_role)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total (24h)", summary['total_24h'])
    col2.metric("Unread (24h)", summary['unread_24h'])
    col3.metric("Total Unread", unread_count)
    
    st.divider()
    
    # Filter tabs
    filter_tabs = st.tabs(["All", "Unread", "Low Stock", "Conflicts", "Overdue"])
    
    with filter_tabs[0]:
        render_notification_list(notification_role, unread_only=False)
    
    with filter_tabs[1]:
        render_notification_list(notification_role, unread_only=True)
    
    with filter_tabs[2]:
        render_notification_list(notification_role, notification_type='low_stock')
    
    with filter_tabs[3]:
        render_notification_list(notification_role, notification_type='conflict_no_alternatives')
    
    with filter_tabs[4]:
        render_notification_list(notification_role, notification_type='return_overdue')

def render_notification_list(user_role: str, unread_only: bool = False, notification_type: str = None):
    """Render list of notifications"""
    
    try:
        notifications_df = notification_manager.get_notifications_for_user(
            user_role, 
            unread_only=unread_only,
            notification_type=notification_type,
            limit=50
        )
        
        if notifications_df.empty:
            st.info("No notifications found.")
            return
        
        # Mark all as read button
        if unread_only or not notification_type:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Mark All Read", key=f"mark_all_{unread_only}_{notification_type}"):
                    result = notification_manager.mark_all_as_read(user_role)
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        time.sleep(1)
                        st.rerun()
        
        st.write(f"Showing {len(notifications_df)} notifications")
        
        # Display notifications
        for _, notif in notifications_df.iterrows():
            # Determine icon based on type
            icon = "📢"
            if notif['notification_type'] == 'low_stock':
                icon = "⚠️"
            elif notif['notification_type'] == 'conflict_no_alternatives':
                icon = "🔴"
            elif notif['notification_type'] == 'offsite_conflict':
                icon = "🚚"
            elif notif['notification_type'] == 'return_overdue':
                icon = "⏰"
            
            # Format timestamp
            created_at = notif['created_at']
            if isinstance(created_at, pd.Timestamp):
                time_ago = (pd.Timestamp.now() - created_at)
                if time_ago.days > 0:
                    time_str = f"{time_ago.days} days ago"
                elif time_ago.seconds // 3600 > 0:
                    time_str = f"{time_ago.seconds // 3600} hours ago"
                else:
                    time_str = f"{time_ago.seconds // 60} minutes ago"
            else:
                time_str = str(created_at)
            
            # Create expander for each notification
            is_unread = not notif['is_read']
            bg_color = "#fff3cd" if is_unread else "#f8f9fa"
            border_left = "4px solid #ffc107" if is_unread else "4px solid #dee2e6"
            
            with st.container():
                st.markdown(f"""
                <div style="background-color: {bg_color}; border-left: {border_left}; padding: 10px; margin: 5px 0; border-radius: 4px;">
                    <b>{icon} {notif['notification_type'].replace('_', ' ').title()}</b> 
                    <span style="color: #6c757d; font-size: 0.85em;">({time_str})</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.write(notif['message'])
                
                if is_unread:
                    if st.button("Mark as Read", key=f"read_{notif['id']}"):
                        result = notification_manager.mark_as_read(notif['id'])
                        if result['success']:
                            st.success("✅ Marked as read")
                            time.sleep(0.5)
                            st.rerun()
                
                st.divider()
    
    except Exception as e:
        st.error(f"Error loading notifications: {e}")

def render_device_assignment_queue():
    """
    IT Staff Device Assignment Interface
    Manual assignment with full tracking and conflict detection
    """
    st.header("🔧 Device Assignment Queue")
    
    # Initialize session state for this view
    if 'assignment_filter' not in st.session_state:
        st.session_state.assignment_filter = "Pending"
    
    # Filter tabs
    filter_tabs = st.tabs(["Pending", "Off-site Requests", "Conflicts", "All"])
    
    with filter_tabs[0]:
        render_pending_assignments()
    
    with filter_tabs[1]:
        render_offsite_requests()
    
    with filter_tabs[2]:
        render_conflicts()
    
    with filter_tabs[3]:
        render_all_assignments()

def render_pending_assignments():
    """Show bookings with pending device requests"""
    st.subheader("📋 Pending Device Requests")
    
    try:
        # Get bookings with device requests but no assignments
        query = """
            SELECT 
                b.id as booking_id,
                b.client_name,
                b.learners_count,
                r.name as room_name,
                lower(b.booking_period)::date as start_date,
                upper(b.booking_period)::date as end_date,
                dc.name as device_category,
                bda.quantity as requested_quantity,
                bda.id as request_id
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN booking_device_assignments bda ON b.id = bda.booking_id
            JOIN device_categories dc ON bda.device_category_id = dc.id
            WHERE b.status = 'confirmed'
            AND bda.device_id IS NULL
            AND lower(b.booking_period) >= CURRENT_DATE
            ORDER BY lower(b.booking_period)
        """
        
        pending_df = db.run_query(query)
        
        if pending_df.empty:
            st.info("No pending device requests.")
            return
        
        st.write(f"Found {len(pending_df)} pending requests")
        
        # Group by booking
        for booking_id in pending_df['booking_id'].unique():
            booking_requests = pending_df[pending_df['booking_id'] == booking_id]
            first = booking_requests.iloc[0]
            
            with st.expander(
                f"📋 Booking #{booking_id} - {first['client_name']} ({first['room_name']}) "
                f"| {first['start_date']} to {first['end_date']}"
            ):
                st.write(f"**Client:** {first['client_name']}")
                st.write(f"**Room:** {first['room_name']}")
                st.write(f"**Dates:** {first['start_date']} to {first['end_date']}")
                st.write(f"**Learners:** {first['learners_count']}")
                
                # Show each device request
                for _, request in booking_requests.iterrows():
                    st.divider()
                    st.write(f"**Device Request:** {request['requested_quantity']}x {request['device_category']}")
                    
                    # Get available devices
                    available = device_manager.get_available_devices(
                        request['device_category'],
                        request['start_date'],
                        request['end_date']
                    )
                    
                    if available.empty:
                        st.error(f"⚠️ No {request['device_category']}s available!")
                        if st.button(f"Notify Bosses - No Stock", key=f"notify_{request['request_id']}"):
                            st.info("📢 Notification sent to IT Boss and Room Boss")
                    else:
                        st.write(f"✅ {len(available)} {request['device_category']}s available")
                        
                        # Multi-select by serial number only
                        selected_serials = st.multiselect(
                            f"Select {request['device_category']}s (Serial Numbers)",
                            options=available['serial_number'].tolist(),
                            key=f"select_{request['request_id']}"
                        )
                        
                        # Off-site option
                        is_offsite = st.checkbox(
                            "Off-site Rental",
                            key=f"offsite_{request['request_id']}"
                        )
                        
                        # Off-site form
                        if is_offsite:
                            with st.form(key=f"offsite_form_{request['request_id']}"):
                                st.write("**Off-site Details:**")
                                rental_no = st.text_input("Rental No", key=f"rental_no_{request['request_id']}")
                                rental_date = st.date_input("Rental Date", value=request['start_date'], key=f"rental_date_{request['request_id']}")
                                contact_person = st.text_input("Contact Person", key=f"contact_{request['request_id']}")
                                contact_number = st.text_input("Contact Number", key=f"phone_{request['request_id']}")
                                contact_email = st.text_input("Email (optional)", key=f"email_{request['request_id']}")
                                company = st.text_input("Company", key=f"company_{request['request_id']}")
                                address = st.text_area("Address", key=f"address_{request['request_id']}")
                                return_date = st.date_input("Expected Return Date", value=request['end_date'], key=f"return_{request['request_id']}")
                                
                                submitted = st.form_submit_button("Assign with Off-site Details")
                                
                                if submitted and selected_serials:
                                    # Assign devices
                                    for serial in selected_serials:
                                        device_row = available[available['serial_number'] == serial]
                                        if not device_row.empty:
                                            device_id = int(device_row.iloc[0]['id'])
                                            result = device_manager.assign_device(
                                                booking_id,
                                                device_id,
                                                st.session_state['username'],
                                                is_offsite=True,
                                                notes=f"Off-site rental {rental_no}"
                                            )
                                            
                                            if result['success']:
                                                # Create off-site rental record
                                                device_manager.create_offsite_rental(
                                                    result['assignment_id'],
                                                    rental_no,
                                                    rental_date,
                                                    contact_person,
                                                    contact_number,
                                                    contact_email or None,
                                                    company or None,
                                                    address,
                                                    return_date
                                                )
                                    
                                    st.success(f"✅ Assigned {len(selected_serials)} devices with off-site details")
                                    time.sleep(1)
                                    st.rerun()
                        else:
                            # Simple assign button for on-site
                            if st.button(f"Assign {len(selected_serials)} Devices", key=f"assign_{request['request_id']}"):
                                if selected_serials:
                                    success_count = 0
                                    for serial in selected_serials:
                                        device_row = available[available['serial_number'] == serial]
                                        if not device_row.empty:
                                            device_id = int(device_row.iloc[0]['id'])
                                            result = device_manager.assign_device(
                                                booking_id,
                                                device_id,
                                                st.session_state['username'],
                                                is_offsite=False
                                            )
                                            if result['success']:
                                                success_count += 1
                                    
                                    st.success(f"✅ Assigned {success_count} devices")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.warning("Please select at least one device")
    
    except Exception as e:
        st.error(f"Error loading pending assignments: {e}")

def render_offsite_requests():
    """Show current off-site rentals"""
    st.subheader("🚚 Off-site Rentals")
    
    try:
        query = """
            SELECT 
                or2.id as rental_id,
                or2.rental_no,
                b.client_name,
                r.name as room_name,
                or2.contact_person,
                or2.contact_number,
                or2.company,
                or2.address,
                or2.return_expected_date,
                or2.returned_at,
                d.serial_number,
                dc.name as device_type
            FROM offsite_rentals or2
            JOIN booking_device_assignments bda ON or2.booking_device_assignment_id = bda.id
            JOIN bookings b ON bda.booking_id = b.id
            JOIN rooms r ON b.room_id = r.id
            JOIN devices d ON bda.device_id = d.id
            JOIN device_categories dc ON d.category_id = dc.id
            WHERE or2.returned_at IS NULL
            ORDER BY or2.return_expected_date
        """
        
        offsite_df = db.run_query(query)
        
        if offsite_df.empty:
            st.info("No active off-site rentals.")
            return
        
        st.write(f"Found {len(offsite_df)} active off-site rentals")
        
        for _, rental in offsite_df.iterrows():
            with st.expander(
                f"🚚 Rental #{rental['rental_no']} - {rental['client_name']} "
                f"| Return: {rental['return_expected_date']}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Client:** {rental['client_name']}")
                    st.write(f"**Room:** {rental['room_name']}")
                    st.write(f"**Device:** {rental['device_type']} ({rental['serial_number']})")
                
                with col2:
                    st.write(f"**Contact:** {rental['contact_person']}")
                    st.write(f"**Phone:** {rental['contact_number']}")
                    if rental['company']:
                        st.write(f"**Company:** {rental['company']}")
                    st.write(f"**Address:** {rental['address']}")
                
                if st.button("Mark as Returned", key=f"return_{rental['rental_id']}"):
                    # Update offsite_rental and device status
                    db.run_query(
                        "UPDATE offsite_rentals SET returned_at = NOW() WHERE id = %s",
                        (rental['rental_id'],)
                    )
                    st.success("✅ Device marked as returned")
                    time.sleep(1)
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error loading off-site rentals: {e}")

def render_conflicts():
    """Show device conflicts and reallocation options"""
    st.subheader("⚠️ Device Conflicts")
    
    try:
        # Find devices with overlapping bookings
        conflict_query = """
            SELECT DISTINCT
                d.id as device_id,
                d.serial_number,
                dc.name as category_name,
                b1.id as booking1_id,
                b1.client_name as client1,
                lower(b1.booking_period)::date as start1,
                upper(b1.booking_period)::date as end1,
                b2.id as booking2_id,
                b2.client_name as client2,
                lower(b2.booking_period)::date as start2,
                upper(b2.booking_period)::date as end2
            FROM devices d
            JOIN device_categories dc ON d.category_id = dc.id
            JOIN booking_device_assignments bda1 ON d.id = bda1.device_id
            JOIN bookings b1 ON bda1.booking_id = b1.id
            JOIN booking_device_assignments bda2 ON d.id = bda2.device_id
            JOIN bookings b2 ON bda2.booking_id = b2.id
            WHERE b1.id < b2.id
            AND b1.status = 'confirmed'
            AND b2.status = 'confirmed'
            AND b1.booking_period && b2.booking_period
            AND bda1.is_offsite = false
            AND bda2.is_offsite = false
            ORDER BY d.serial_number
        """
        
        conflicts_df = db.run_query(conflict_query)
        
        if conflicts_df.empty:
            st.success("✅ No device conflicts detected")
            return
        
        st.warning(f"Found {len(conflicts_df)} device conflict(s)")
        
        for _, conflict in conflicts_df.iterrows():
            with st.expander(
                f"⚠️ {conflict['serial_number']} ({conflict['category_name']}) - Conflict Detected"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Booking 1:**")
                    st.write(f"Client: {conflict['client1']}")
                    st.write(f"Dates: {conflict['start1']} to {conflict['end1']}")
                
                with col2:
                    st.write("**Booking 2:**")
                    st.write(f"Client: {conflict['client2']}")
                    st.write(f"Dates: {conflict['start2']} to {conflict['end2']}")
                
                # Show reallocation options
                st.divider()
                st.write("**Reallocation Options:**")
                
                # Get alternative devices for booking 2
                alternatives = device_manager.get_available_devices(
                    conflict['category_name'],
                    conflict['start2'],
                    conflict['end2'],
                    exclude_device_id=conflict['device_id']
                )
                
                if alternatives.empty:
                    st.error("❌ No alternative devices available")
                    if st.button(f"Notify IT Boss - No Alternatives", key=f"notify_alt_{conflict['device_id']}"):
                        st.info("📢 Notification sent to IT Boss")
                else:
                    st.success(f"✅ {len(alternatives)} alternative devices available")
                    
                    alt_serial = st.selectbox(
                        "Select alternative device",
                        options=alternatives['serial_number'].tolist(),
                        key=f"alt_select_{conflict['device_id']}"
                    )
                    
                    if st.button("Reallocate to Alternative", key=f"realloc_{conflict['device_id']}"):
                        alt_device = alternatives[alternatives['serial_number'] == alt_serial].iloc[0]
                        
                        result = device_manager.reallocate_device(
                            conflict['device_id'],
                            conflict['booking2_id'],
                            conflict['booking2_id'],  # Same booking, just different device
                            st.session_state['username'],
                            reason=f"Conflict resolution - moved to {alt_serial}"
                        )
                        
                        # Actually we need to unassign old and assign new
                        # First unassign the conflicting device
                        db.run_query(
                            "DELETE FROM booking_device_assignments WHERE booking_id = %s AND device_id = %s",
                            (conflict['booking2_id'], conflict['device_id'])
                        )
                        
                        # Assign the alternative
                        device_manager.assign_device(
                            conflict['booking2_id'],
                            int(alt_device['id']),
                            st.session_state['username'],
                            is_offsite=False,
                            notes=f"Assigned as alternative to resolve conflict with {conflict['serial_number']}"
                        )
                        
                        st.success(f"✅ Reallocated to {alt_serial}")
                        time.sleep(1)
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error loading conflicts: {e}")

def render_all_assignments():
    """Show all device assignments"""
    st.subheader("📊 All Device Assignments")
    
    try:
        query = """
            SELECT 
                bda.id as assignment_id,
                b.client_name,
                r.name as room_name,
                d.serial_number,
                dc.name as device_type,
                lower(b.booking_period)::date as start_date,
                upper(b.booking_period)::date as end_date,
                bda.is_offsite,
                u.username as assigned_by,
                bda.assigned_at
            FROM booking_device_assignments bda
            JOIN bookings b ON bda.booking_id = b.id
            JOIN rooms r ON b.room_id = r.id
            JOIN devices d ON bda.device_id = d.id
            JOIN device_categories dc ON d.category_id = dc.id
            LEFT JOIN users u ON bda.assigned_by = u.user_id
            WHERE b.status = 'confirmed'
            AND upper(b.booking_period) >= CURRENT_DATE
            ORDER BY lower(b.booking_period) DESC
            LIMIT 100
        """
        
        assignments_df = db.run_query(query)
        
        if assignments_df.empty:
            st.info("No device assignments found.")
            return
        
        st.write(f"Showing {len(assignments_df)} assignments")
        st.dataframe(
            assignments_df,
            column_config={
                'client_name': 'Client',
                'room_name': 'Room',
                'serial_number': 'Device Serial',
                'device_type': 'Type',
                'start_date': 'Start',
                'end_date': 'End',
                'is_offsite': 'Off-site',
                'assigned_by': 'Assigned By',
                'assigned_at': 'Assigned At'
            },
            hide_index=True,
            use_container_width=True
        )
    
    except Exception as e:
        st.error(f"Error loading assignments: {e}")

def render_new_booking_form():
    st.header("📝 New Booking Request")

    # 1. Fetch Rooms via Logic Bridge
    try:
        rooms_df = db.get_rooms()
        if rooms_df.empty:
            st.warning("⚠️ No rooms found in database. Please add rooms first.")
            return
    except ConnectionError as e:
        st.error(f"🚨 CRITICAL: Database unreachable: {e}")
        st.info("Fix: verify Tailscale is up, the secrets.toml host IP is correct, and PostgreSQL is listening on the VPN interface.")
        return
    except Exception as e:
        st.error(f"❌ Database Error: Unable to fetch room list: {e}")
        return

    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        with col1:
            selected_room_id = st.selectbox(
                "Select Room",
                options=rooms_df['id'].tolist(),
                format_func=lambda x: rooms_df[rooms_df['id'] == x]['name'].values[0]
            )

        with col2:
            booking_date = st.date_input("Date")
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")

        purpose = st.text_area("Purpose of Booking")
        submitted = st.form_submit_button("Check Availability & Book")

        if submitted:
            # 2. Normalize Data (Prevent Timezone Drift)
            try:
                start_dt, end_dt = db.normalize_dates(booking_date, start_time, end_time)

                # 3. Call Transaction Logic
                db.create_booking(selected_room_id, start_dt, end_dt, purpose)
                st.success("✅ Booking Confirmed! Database updated.")
                time.sleep(1)
                st.rerun()

            except ValueError as ve:
                st.error(f"⛔ Booking Failed: {ve}")
            except RuntimeError as re:
                # Schema errors (e.g., missing booking_reference column)
                st.error(f"❌ Schema Error: {re}")
                if "booking_reference" in str(re).lower():
                    st.info("💡 To enable purpose storage, run: `ALTER TABLE bookings ADD COLUMN booking_reference TEXT;`")
            except Exception as e:
                st.error(f"❌ System Error: {e}")

def render_admin_dashboard():
    # RBAC Check: Admins, training_facility_admin, and it_rental_admin can see dashboard
    allowed_roles = ['admin', 'training_facility_admin', 'it_rental_admin', 'it_admin']
    if st.session_state.get('role') not in allowed_roles:
        st.warning("⛔ Access Denied: You do not have permission to view this page.")
        return

    st.header("📊 Admin Dashboard")

    # Fetch Stats via Logic Bridge
    try:
        df = db.get_dashboard_stats()
        
        col1, col2, col3 = st.columns(3)
        if not df.empty:
            total = df.iloc[0]['total_bookings']
            approved = df.iloc[0]['approved']
            upcoming = df.iloc[0]['upcoming']
        else:
            total, approved, upcoming = 0, 0, 0

        col1.metric("Total Bookings", total)
        col2.metric("Approved", approved)
        col3.metric("Upcoming", upcoming)
    except ConnectionError as e:
        st.error(f"🚨 CRITICAL: Database unreachable: {e}")
        st.info("Fix: verify Tailscale is up, the secrets.toml host IP is correct, and PostgreSQL is listening on the VPN interface.")
    except Exception as e:
        st.error(f"❌ Database Error: Unable to fetch dashboard stats: {e}")

    st.divider()
    st.subheader("Revenue & Utilization (v2.1)")
    st.caption("Ghost Inventory tracking is active.")

# ----------------------------------------------------------------------------
# MAIN CONTROLLER
# ----------------------------------------------------------------------------

def main():
    init_session_state()

    if not st.session_state['authenticated']:
        render_login()
        return

    st.sidebar.title("Colab ERP v2.2.0")
    st.sidebar.caption(f"User: {st.session_state['username']} ({st.session_state['role']})")
    st.sidebar.info("System Status: 🟢 Online (Headless)")

    # Navigation Logic based on Role
    user_role = st.session_state['role']
    
    if user_role in ['admin', 'training_facility_admin', 'it_admin']:
        # Full admin menu with Notifications
        menu = ["Dashboard", "Notifications", "Calendar", "Device Assignment Queue", "New Room Booking", 
                "New Device Booking", "Pricing Catalog", "Pending Approvals", "Inventory Dashboard"]
    elif user_role in ['it_boss', 'room_boss']:
        # Bosses see notifications
        menu = ["Dashboard", "Notifications", "Calendar", "New Room Booking", 
                "New Device Booking", "Pricing Catalog", "Pending Approvals", "Inventory Dashboard"]
    else:
        # Staff see limited menu
        menu = ["Calendar", "New Room Booking", "New Device Booking", 
                "Pricing Catalog", "Pending Approvals", "Inventory Dashboard"]

    choice = st.sidebar.radio("Navigation", menu)

    st.sidebar.divider()
    if st.sidebar.button("🔴 Logout"):
        logout()

    if choice == "Dashboard":
        render_admin_dashboard()
    elif choice == "Notifications":
        render_notifications()
    elif choice == "Calendar":
        render_calendar_view()
    elif choice == "Device Assignment Queue":
        render_device_assignment_queue()
    elif choice == "New Room Booking":
        render_new_room_booking()
        # Show the actual booking form below
        render_new_booking_form()
    elif choice == "New Device Booking":
        render_new_device_booking()
    elif choice == "Pricing Catalog":
        render_pricing_catalog()
    elif choice == "Pending Approvals":
        render_pending_approvals()
    elif choice == "Inventory Dashboard":
        render_inventory_dashboard()

if __name__ == "__main__":
    main()