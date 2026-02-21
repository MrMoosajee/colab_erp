import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import src.db as db
import src.auth as auth
import time

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
    Dual auth: tries DB-backed bcrypt first, falls back to secrets.toml
    if the database is unreachable.
    """
    # --- Attempt 1: DB-backed auth (v2.2.0 - preferred) ---
    try:
        user = auth.authenticate(username, password)
        if user:
            st.session_state['authenticated'] = True
            st.session_state['username'] = user["username"]
            st.session_state['role'] = user["role"]
            st.success(f"Login Successful ({user['role']})")
            time.sleep(0.5)
            st.rerun()
            return
        # user is None => credentials didn't match in DB
        # Fall through to secrets.toml check below
    except ConnectionError:
        # DB unreachable — fall back to secrets.toml
        pass
    except Exception:
        # Any other DB/auth error — fall back to secrets.toml
        pass

    # --- Attempt 2: secrets.toml fallback (v2.2.0 legacy) ---
    try:
        admin_user = st.secrets["auth"]["admin_user"]
        admin_pass = st.secrets["auth"]["admin_password"]
        staff_user = st.secrets["auth"]["staff_user"]
        staff_pass = st.secrets["auth"]["staff_password"]

        if username == admin_user and password == admin_pass:
            st.session_state['authenticated'] = True
            st.session_state['username'] = username
            st.session_state['role'] = 'admin'
            st.success("Login Successful (Admin)")
            time.sleep(0.5)
            st.rerun()
            return

        if username == staff_user and password == staff_pass:
            st.session_state['authenticated'] = True
            st.session_state['username'] = username
            st.session_state['role'] = 'staff'
            st.success("Login Successful (Staff)")
            time.sleep(0.5)
            st.rerun()
            return

        st.error("Invalid Credentials")

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
    st.header("📅 Room Booking Calendar")

    import pandas as pd
    from datetime import datetime, timedelta

    # --- Week Navigation ---
    if 'calendar_week_offset' not in st.session_state:
        st.session_state['calendar_week_offset'] = 0

    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
    with nav_col1:
        if st.button("◀ Previous Week"):
            st.session_state['calendar_week_offset'] -= 1
            st.rerun()
    with nav_col2:
        if st.button("Today"):
            st.session_state['calendar_week_offset'] = 0
            st.rerun()
    with nav_col3:
        if st.button("Next Week ▶"):
            st.session_state['calendar_week_offset'] += 1
            st.rerun()
    with nav_col4:
        view_mode = st.selectbox("View", ["Weekly", "Monthly"], label_visibility="collapsed")

    # Calculate date range
    today = datetime.now().date()
    if view_mode == "Weekly":
        week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state['calendar_week_offset'])
        week_end = week_start + timedelta(days=6)
        st.subheader(f"{week_start.strftime('%d %B %Y')} — {week_end.strftime('%d %B %Y')}")
    else:
        month_offset = st.session_state['calendar_week_offset']
        month = today.month + month_offset
        year = today.year
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        week_start = datetime(year, month, 1).date()
        if month == 12:
            week_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            week_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        st.subheader(f"{week_start.strftime('%B %Y')}")

    try:
        df = db.get_calendar_grid(week_start, week_end)

        if df.empty:
            st.info("No bookings for this period.")
            return

        import re

        # Room display order — includes split room
        room_order = [
            "Excellence", "Inspiration", "Honesty", "Gratitude",
            "Ambition", "Perseverence", "Ambition+Perseverence",
            "Courage", "Possibilities", "Motivation", "A302", "A303",
            "Success", "Respect", "Innovation", "Dedication", "Integrity",
            "Empower", "Focus", "Growth", "Wisdom",
            "Vision", "Potential", "Synergy"
        ]

        # Build cell labels: "Client (headcount)" + laptop icon if applicable
        def build_cell_label(row):
            client = row['client_name']
            headcount = row['headcount']
            raw = row.get('booking_reference', '') or ''
            label = client
            if headcount and headcount > 1:
                label = f"{client} ({headcount})"
            # Check for laptop/device mentions in raw reference
            laptop_match = re.search(r'(\d+)\s*(?:laptops?|devices?)', raw, re.IGNORECASE)
            if laptop_match:
                laptop_count = laptop_match.group(1)
                label += f" [{laptop_count}L]"
            return label

        df['cell_label'] = df.apply(build_cell_label, axis=1)

        # Pivot: rows = dates, columns = rooms, values = cell labels
        pivot = df.pivot_table(
            index='booking_date',
            columns='room_name',
            values='cell_label',
            aggfunc=lambda x: ', '.join(sorted(set(x)))
        )

        # Build full date range (include empty days)
        all_dates = pd.date_range(start=week_start, end=week_end, freq='D')
        pivot = pivot.reindex(all_dates)
        pivot.index = pivot.index.date

        # Reorder columns to match room_order, only include rooms that exist
        ordered_cols = [r for r in room_order if r in pivot.columns]
        pivot = pivot[ordered_cols]

        # Add Day column
        pivot.insert(0, 'Day', [datetime.combine(d, datetime.min.time()).strftime('%a') for d in pivot.index])

        # Fill NaN with empty string
        pivot = pivot.fillna("")

        # Style calendar rows
        def style_calendar(row):
            date = row.name
            day_of_week = datetime.combine(date, datetime.min.time()).weekday()
            if date == today:
                return ['background-color: #1a3a2a; color: #4ade80; font-weight: bold'] * len(row)
            elif day_of_week >= 5:
                return ['background-color: #2a1a3a; color: #c084fc'] * len(row)
            else:
                return [''] * len(row)

        styled = pivot.style.apply(style_calendar, axis=1)

        # Column config: Day column narrow, room columns wide enough for full text
        col_config = {"Day": st.column_config.TextColumn("Day", width=60)}
        for col in ordered_cols:
            col_config[col] = st.column_config.TextColumn(col, width=200)

        st.dataframe(
            styled,
            column_config=col_config,
            use_container_width=False,
            height=800,
            hide_index=False,
        )

    except ConnectionError as e:
        st.error(f"🚨 CRITICAL: Database unreachable: {e}")
        st.info("Fix: verify Tailscale is up, the secrets.toml host IP is correct, and PostgreSQL is listening on the VPN interface.")
    except Exception as e:
        st.error(f"❌ Database Error: Unable to fetch calendar bookings: {e}")

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
    if (st.session_state.get('role') or '').lower() != 'admin':
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
    if st.session_state['role'].lower() == 'admin':
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
