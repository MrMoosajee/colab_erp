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
st.set_page_config(page_title="Colab ERP v2.1.1", layout="wide")

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

    # --- Attempt 2: secrets.toml fallback (v2.1.1 legacy) ---
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
    st.caption("v2.1.1 Production | Unauthorized Access Prohibited")
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
    try:
        df = db.get_calendar_bookings()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No upcoming bookings found.")
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

    st.sidebar.title("Colab ERP v2.1.1")
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
