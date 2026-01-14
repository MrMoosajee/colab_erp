import streamlit as st
import pandas as pd
from datetime import date
from db import (
    check_room_availability,
    check_asset_availability,
    normalize_dates,
    get_connection
)
from auth import authenticate

# --- PAGE CONFIG ---
st.set_page_config(page_title="Colab ERP V 1.0", layout="wide")

# --- SESSION STATE & LOGIN ---
if "user" not in st.session_state:
    st.session_state.user = None

# If not logged in, show Login Screen
if not st.session_state.user:
    st.title("🔐 Colab ERP Login")

    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.success("Login Successful")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    st.stop() # Stop execution here if not logged in

# --- MAIN APP (LOGGED IN) ---
user = st.session_state.user
role = user["role"]

# Sidebar Header
st.sidebar.title(f"👤 {user['username']}")
st.sidebar.caption(f"Role: {role}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# -----------------------------
# ADMIN / BOSS UI
# -----------------------------
if role == "Admin":
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Calendar", "Approvals", "Settings"])

    if menu == "Dashboard":
        st.header("📊 Admin Dashboard")
        
        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                # Metric 1: Bookings Today
                cur.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Approved' AND start_time::date <= CURRENT_DATE AND end_time::date >= CURRENT_DATE")
                today_bookings = cur.fetchone()[0]

                # Metric 2: Potential Revenue (Pending)
                cur.execute("\n"
                            "                    SELECT COALESCE(SUM(quantity * agreed_price), 0)\n"
                            "                    FROM booking_lines bl\n"
                            "                    JOIN bookings b ON bl.booking_id = b.booking_id\n"
                            "                    WHERE b.status = 'Pending'\n"
                            "                ")
                pending_revenue = cur.fetchone()[0]
                
                # Display Metrics
                m1, m2 = st.columns(2)
                m1.metric("Active Bookings Today", today_bookings)
                m2.metric("Pending Revenue", f"R {pending_revenue:,.2f}")
                
            except Exception as e:
                st.error(f"Dashboard Error: {e}")
            finally:
                conn.close()

    elif menu == "Calendar":
        st.header("📅 Room Booking Calendar")
        conn = get_connection()
        if conn:
            try:
                # Fetch data for dataframe
                query = """
                    SELECT r.name as "Room", b.start_time::date as "Start", b.end_time::date as "End", b.status
                    FROM bookings b
                    JOIN rooms r ON b.room_id = r.room_id
                    ORDER BY b.start_time DESC
                """
                df = pd.read_sql(query, conn)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(e)
            finally:
                conn.close()

    elif menu == "Approvals":
        st.header("✅ Pending Approvals")
        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT b.booking_id, r.name, b.start_time::date, b.end_time::date, u.username
                    FROM bookings b
                    JOIN rooms r ON b.room_id = r.room_id
                    JOIN users u ON b.user_id = u.user_id
                    WHERE b.status = 'Pending'
                """)
                rows = cur.fetchall()
                
                if not rows:
                    st.info("No pending approvals.")
                
                for bid, rname, start, end, booker in rows:
                    with st.expander(f"Booking #{bid} | {rname} | {start} to {end}"):
                        st.write(f"**Requested by:** {booker}")
                        # Fetch items for this booking
                        items_df = pd.read_sql(f"SELECT i.name, bl.quantity, bl.agreed_price FROM booking_lines bl JOIN catalog_items i ON bl.item_id = i.item_id WHERE bl.booking_id = {bid}", conn)
                        st.dataframe(items_df)
                        
                        c1, c2 = st.columns(2)
                        if c1.button("Approve", key=f"app_{bid}"):
                            cur.execute("UPDATE bookings SET status='Approved' WHERE booking_id=%s", (bid,))
                            conn.commit()
                            st.success("Approved!")
                            st.rerun()
                        if c2.button("Reject", key=f"rej_{bid}"):
                            cur.execute("UPDATE bookings SET status='Rejected' WHERE booking_id=%s", (bid,))
                            conn.commit()
                            st.warning("Rejected.")
                            st.rerun()
            except Exception as e:
                st.error(e)
            finally:
                conn.close()

    elif menu == "Settings":
        st.header("⚙️ Inventory & Rooms")
        st.info("Direct database editing is recommended for now. Contact IT for Schema changes.")
        conn = get_connection()
        if conn:
            st.subheader("Current Catalog")
            df = pd.read_sql("SELECT * FROM catalog_items", conn)
            st.dataframe(df)
            conn.close()

# -----------------------------
# CLIENT / STAFF UI
# -----------------------------
else:
    st.header("📝 New Booking Request")

    # --- SECTION 1: DATES & ROOM ---
    st.subheader("1. When & Where")
    
    c1, c2, c3 = st.columns([1, 1, 2])
    ds = c1.date_input("Start Date", min_value=date.today())
    de = c2.date_input("End Date", min_value=ds)

    room_id = None
    conn = get_connection()
    if conn:
        df_rooms = pd.read_sql("SELECT room_id, name, capacity FROM rooms", conn)
        # Create a dictionary for the dropdown
        room_map = {f"{row['name']} (Cap: {row['capacity']})": row['room_id'] for _, row in df_rooms.iterrows()}
        selected_name = c3.selectbox("Choose a Room", options=list(room_map.keys()))
        room_id = room_map[selected_name]

    st.divider()

    # --- SECTION 2: ASSETS & SERVICES ---
    st.subheader("2. Add Equipment & Services")
    
    selected_assets = {}
    
    if conn:
        # Fetch ALL items (Assets AND Services) - Removed category='Asset' filter
        df_items = pd.read_sql("SELECT item_id, name, total_stock, type, default_price FROM catalog_items ORDER BY type, name", conn)
        conn.close()

        # Group items by Type (e.g., Asset vs Service) for cleaner UI
        types = df_items['type'].unique()
        
        for t in types:
            with st.expander(f"📦 {t}s", expanded=True):
                # Filter df for this type
                type_items = df_items[df_items['type'] == t]
                
                # Create a grid layout for items
                cols = st.columns(3)
                for index, row in type_items.iterrows():
                    col = cols[index % 3]
                    with col:
                        # Show Stock limit in label
                        label = f"{row['name']} (R{row['default_price']:.0f})"
                        max_stock = int(row['total_stock'])
                        
                        qty = st.number_input(
                            label, 
                            min_value=0, 
                            max_value=max_stock, 
                            step=1, 
                            key=f"item_{row['item_id']}",
                            help=f"Max available: {max_stock}"
                        )
                        if qty > 0:
                            selected_assets[row['item_id']] = qty

    st.divider()
    
    # --- SUBMIT BUTTON ---
    if st.button("🚀 Submit Booking Request", type="primary", use_container_width=True):
        
        # 1. Check Room Availability (Sliding Door)
        if not check_room_availability(room_id, ds, de):
            st.error("❌ Room Unavailable: Conflict with another booking (or Combined Room).")
            st.stop()

        # 2. Check Asset Availability (Ghost Inventory)
        for item_id, qty in selected_assets.items():
            ok, shortage = check_asset_availability(item_id, qty, ds, de)
            if not ok:
                st.error(f"❌ Inventory Shortage: Not enough stock for Item ID {item_id}. Short by {shortage}.")
                st.stop()

        # 3. Commit to Database
        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                start_dt, end_dt = normalize_dates(ds, de)
                
                # Insert Booking
                cur.execute("""
                    INSERT INTO bookings (user_id, room_id, start_time, end_time, status)
                    VALUES (%s, %s, %s, %s, 'Pending')
                    RETURNING booking_id
                """, (user['user_id'], room_id, start_dt, end_dt))
                
                new_booking_id = cur.fetchone()[0]
                
                # Insert Assets
                for item_id, qty in selected_assets.items():
                    # Fetch default price
                    cur.execute("SELECT default_price FROM catalog_items WHERE item_id = %s", (item_id,))
                    price = cur.fetchone()[0]
                    
                    cur.execute("""
                        INSERT INTO booking_lines (booking_id, item_id, quantity, agreed_price)
                        VALUES (%s, %s, %s, %s)
                    """, (new_booking_id, item_id, qty, price))
                
                conn.commit()
                st.balloons()
                st.success(f"✅ Request Submitted! Reference #{new_booking_id}. Admin will review.")
                
            except Exception as e:
                conn.rollback()
                st.error(f"Database Error: {e}")
            finally:
                conn.close()
