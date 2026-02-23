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

# Page Config
st.set_page_config(page_title="Colab ERP v2.2.0", layout="wide")

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
        overflow-x: auto;
        white-space: nowrap;
        width: 100%;
        border: 1px solid #ddd;
    }
    .calendar-grid {
        display: inline-block;
        min-width: 3500px;
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
                learners = int(booking.iloc[0]['learners_count']) if pd.notna(booking.iloc[0]['learners_count']) else 0
                facilitators = int(booking.iloc[0]['facilitators_count']) if pd.notna(booking.iloc[0]['facilitators_count']) else 1
                devices = int(booking.iloc[0]['device_count']) if pd.notna(booking.iloc[0]['device_count']) else 0
                
                # Cell content: Client<br/>Learners+Facilitators (+ Devices)
                cell_text = f"<b>{client}</b><br/>{learners}+{facilitators}"
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
    legend_cols[0].markdown("<div style='background-color: #28a745; padding: 5px; border-radius: 4px; color: white; text-align: center; font-size: 12px;'>🟢 Today</div>", unsafe_allow_html=True)
    legend_cols[1].markdown("<div style='background-color: #6f42c1; padding: 5px; border-radius: 4px; color: white; text-align: center; font-size: 12px;'>🟣 Weekend</div>", unsafe_allow_html=True)
    legend_cols[2].markdown("<div style='background-color: #e3f2fd; padding: 5px; border-radius: 4px; text-align: center; font-size: 12px;'>🔵 Weekday</div>", unsafe_allow_html=True)
    legend_cols[3].markdown("<div style='background-color: #d4edda; padding: 5px; border-radius: 4px; text-align: center; font-size: 12px;'>📅 Booked</div>", unsafe_allow_html=True)

def render_month_view(today, rooms_df):
    """Render month view with days as rows, rooms as columns"""
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
    # st.write(f"DEBUG: Month view - {month_start} to {month_end}")
    
    # Fetch calendar data for entire month
    calendar_df = db.get_calendar_grid(month_start, month_end)
    # st.write(f"DEBUG: Month query returned {len(calendar_df)} rows")
    
    num_rooms = len(rooms_df)
    
    # Header row - Room names
    header_cols = st.columns([0.8] + [1] * num_rooms)
    header_cols[0].markdown("**Date**")
    
    for idx, (_, room) in enumerate(rooms_df.iterrows()):
        room_name = room['name']
        header_cols[idx + 1].markdown(f"<div style='font-size: 10px; text-align: center;'><b>{room_name[:10]}</b></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Generate all days in month
    current_date = month_start
    day_count = 0
    
    while current_date <= month_end:
        is_weekend = current_date.weekday() >= 5
        is_today = current_date == today
        
        # Create row
        row_cols = st.columns([0.8] + [1] * num_rooms)
        
        # Date column
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
        
        row_cols[0].markdown(
            f"<div style='background-color: {day_bg}; color: {day_color}; padding: 6px; border-radius: 4px; text-align: center; font-size: 10px;'>"
            f"<b>{day_name}</b><br/>{current_date.strftime('%d')}</div>",
            unsafe_allow_html=True
        )
        
        # Room cells
        for room_idx, (_, room) in enumerate(rooms_df.iterrows()):
            room_id = room['id']
            
            # Convert booking_date to date for month view too (only once)
            if 'booking_date' in calendar_df.columns and not pd.api.types.is_datetime64_any_dtype(calendar_df['booking_date']):
                calendar_df['booking_date'] = pd.to_datetime(calendar_df['booking_date']).dt.date
            
            booking = calendar_df[
                (calendar_df['room_id'] == room_id) & 
                (calendar_df['booking_date'] == current_date)
            ]
            
            if not booking.empty and pd.notna(booking.iloc[0]['booking_id']):
                client = booking.iloc[0]['client_name']
                devices = int(booking.iloc[0]['device_count']) if pd.notna(booking.iloc[0]['device_count']) else 0
                
                cell_text = f"<b>{client[:10]}</b>"
                if devices > 0:
                    cell_text += f"<br/>💻{devices}"
                
                if is_today:
                    bg_color = "#d4edda"
                    border = "2px solid #28a745"
                elif is_weekend:
                    bg_color = "#e8d5f2"
                    border = "2px solid #6f42c1"
                else:
                    bg_color = "#e3f2fd"
                    border = "1px solid #90caf9"
                
                row_cols[room_idx + 1].markdown(
                    f"<div style='background-color: {bg_color}; border: {border}; padding: 3px; border-radius: 4px; font-size: 8px; min-height: 40px; text-align: center; color: black;'>"
                    f"{cell_text}</div>",
                    unsafe_allow_html=True
                )
            else:
                if is_today:
                    bg_color = "#d4edda"
                    border = "2px solid #28a745"
                elif is_weekend:
                    bg_color = "#f3e5f5"
                    border = "1px solid #ce93d8"
                else:
                    bg_color = "#f5f5f5"
                    border = "1px solid #e0e0e0"
                
                row_cols[room_idx + 1].markdown(
                    f"<div style='background-color: {bg_color}; border: {border}; padding: 3px; border-radius: 4px; min-height: 40px;'></div>",
                    unsafe_allow_html=True
                )
        
        current_date += timedelta(days=1)
        day_count += 1
        
        # Limit display for performance (show max 31 days)
        if day_count > 31:
            st.warning("Month display limited to 31 days for performance")
            break
    
    # st.write(f"DEBUG: Displayed {day_count} days")

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
    # RBAC Check: Only Admins can see the dashboard
    if st.session_state.get('role') != 'admin':
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
    if st.session_state['role'] == 'admin':
        menu = ["Dashboard", "Calendar", "New Booking"]
    else:
        # Staff see a limited menu
        menu = ["Calendar", "New Booking"]

    choice = st.sidebar.radio("Navigation", menu)

    st.sidebar.divider()
    if st.sidebar.button("🔴 Logout"):
        logout()

    if choice == "Dashboard":
        render_admin_dashboard()
    elif choice == "Calendar":
        render_calendar_view()
    elif choice == "New Booking":
        render_new_booking_form()

if __name__ == "__main__":
    main()