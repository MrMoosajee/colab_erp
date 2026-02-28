"""
Pricing Catalog Module - Complete pricing management for rooms, devices, and catering
Only accessible by admin and it_admin
"""

import streamlit as st
import pandas as pd
from datetime import date
import time


def render_pricing_catalog(pricing_service, user_role):
    """
    Complete Pricing Catalog with three sections:
    1. Room Pricing (individual rooms)
    2. Device Pricing (collective by category)
    3. Catering & Supplies Pricing
    """
    allowed_roles = ['admin', 'it_admin', 'training_facility_admin', 'it_rental_admin']
    
    if user_role not in allowed_roles:
        st.error("⛔ Access Denied: Only admin and IT admin can view pricing information.")
        return
    
    st.header("💰 Pricing Catalog")
    st.caption("Manage pricing for rooms, devices, and catering/supplies")
    
    # Tabs for the three pricing types
    tab_rooms, tab_devices, tab_catering = st.tabs([
        "🏢 Room Pricing", 
        "💻 Device Pricing", 
        "☕ Catering & Supplies"
    ])
    
    # =====================================================================
    # ROOM PRICING TAB
    # =====================================================================
    with tab_rooms:
        st.subheader("Room Pricing")
        
        room_col1, room_col2 = st.columns([2, 1])
        
        with room_col1:
            st.write("**Current Room Pricing**")
            try:
                room_pricing = pricing_service.get_room_pricing()
                if room_pricing.empty:
                    st.info("No room pricing set up yet.")
                else:
                    for _, room in room_pricing.iterrows():
                        with st.expander(f"{room['item_name']} (Capacity: {room.get('max_capacity', 'N/A')})"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"Daily: R{room.get('daily_rate', 0):.2f}")
                            with col2:
                                if pd.notna(room.get('weekly_rate')):
                                    st.write(f"Weekly: R{room['weekly_rate']:.2f}")
                            with col3:
                                if pd.notna(room.get('monthly_rate')):
                                    st.write(f"Monthly: R{room['monthly_rate']:.2f}")
                            
                            if pd.notna(room.get('notes')):
                                st.caption(f"Notes: {room['notes']}")
                            
                            # Edit button
                            if st.button(f"Edit {room['item_name']}", key=f"edit_room_{room['id']}"):
                                st.session_state['editing_room'] = room['id']
                                st.session_state['edit_room_name'] = room['item_name']
                                st.session_state['edit_daily'] = float(room.get('daily_rate', 0))
                                st.session_state['edit_weekly'] = float(room.get('weekly_rate', 0)) if pd.notna(room.get('weekly_rate')) else 0.0
                                st.session_state['edit_monthly'] = float(room.get('monthly_rate', 0)) if pd.notna(room.get('monthly_rate')) else 0.0
                                st.rerun()
            except Exception as e:
                st.error(f"Error loading room pricing: {e}")
        
        with room_col2:
            st.write("**Add Room Pricing**")
            try:
                rooms_without = pricing_service.get_rooms_without_pricing()
                if rooms_without.empty:
                    st.info("All rooms have pricing set up.")
                else:
                    room_options = [f"{r['name']} (Cap: {r['max_capacity']})" for _, r in rooms_without.iterrows()]
                    selected = st.selectbox("Select Room", room_options, key="room_select")
                    room_id = rooms_without.iloc[room_options.index(selected)]['id']
                    
                    daily = st.number_input("Daily Rate (R)", min_value=0.0, step=50.0, key="room_daily")
                    weekly = st.number_input("Weekly Rate (R)", min_value=0.0, step=100.0, key="room_weekly")
                    monthly = st.number_input("Monthly Rate (R)", min_value=0.0, step=500.0, key="room_monthly")
                    notes = st.text_area("Notes", key="room_notes")
                    
                    if st.button("Add Room Pricing", key="add_room_btn"):
                        result = pricing_service.create_room_pricing(
                            room_id=int(room_id),
                            daily_rate=daily if daily > 0 else None,
                            weekly_rate=weekly if weekly > 0 else None,
                            monthly_rate=monthly if monthly > 0 else None,
                            notes=notes if notes else None
                        )
                        if result['success']:
                            st.success("Room pricing added!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(result['message'])
            except Exception as e:
                st.error(f"Error: {e}")
    
    # =====================================================================
    # DEVICE PRICING TAB (Collective by Category)
    # =====================================================================
    with tab_devices:
        st.subheader("Device Pricing (Collective by Category)")
        st.caption("Set one price for all devices in each category")
        
        device_col1, device_col2 = st.columns([2, 1])
        
        with device_col1:
            st.write("**Current Device Category Pricing**")
            try:
                device_pricing = pricing_service.get_device_pricing()
                if device_pricing.empty:
                    st.info("No device pricing set up yet.")
                else:
                    for _, device in device_pricing.iterrows():
                        device_count = device.get('device_count', 0)
                        with st.expander(f"{device['item_name']} ({device_count} devices)"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"Daily: R{device.get('daily_rate', 0):.2f}")
                            with col2:
                                if pd.notna(device.get('weekly_rate')):
                                    st.write(f"Weekly: R{device['weekly_rate']:.2f}")
                            with col3:
                                if pd.notna(device.get('monthly_rate')):
                                    st.write(f"Monthly: R{device['monthly_rate']:.2f}")
                            
                            if pd.notna(device.get('notes')):
                                st.caption(f"Notes: {device['notes']}")
                            
                            if st.button(f"Edit {device['item_name']}", key=f"edit_device_{device['id']}"):
                                st.session_state['editing_device'] = device['id']
                                st.session_state['edit_device_name'] = device['item_name']
                                st.session_state['edit_dev_daily'] = float(device.get('daily_rate', 0))
                                st.session_state['edit_dev_weekly'] = float(device.get('weekly_rate', 0)) if pd.notna(device.get('weekly_rate')) else 0.0
                                st.session_state['edit_dev_monthly'] = float(device.get('monthly_rate', 0)) if pd.notna(device.get('monthly_rate')) else 0.0
                                st.rerun()
            except Exception as e:
                st.error(f"Error loading device pricing: {e}")
        
        with device_col2:
            st.write("**Add Device Category Pricing**")
            try:
                categories_without = pricing_service.get_device_categories_without_pricing()
                if categories_without.empty:
                    st.info("All device categories have pricing set up.")
                else:
                    cat_options = [f"{c['name']} ({c.get('device_count', 0)} devices)" for _, c in categories_without.iterrows()]
                    selected = st.selectbox("Select Category", cat_options, key="cat_select")
                    cat_id = categories_without.iloc[cat_options.index(selected)]['id']
                    
                    daily = st.number_input("Daily Rate (R)", min_value=0.0, step=10.0, key="dev_daily")
                    weekly = st.number_input("Weekly Rate (R)", min_value=0.0, step=50.0, key="dev_weekly")
                    monthly = st.number_input("Monthly Rate (R)", min_value=0.0, step=200.0, key="dev_monthly")
                    notes = st.text_area("Notes", key="dev_notes")
                    
                    if st.button("Add Device Pricing", key="add_device_btn"):
                        result = pricing_service.create_device_category_pricing(
                            category_id=int(cat_id),
                            daily_rate=daily if daily > 0 else None,
                            weekly_rate=weekly if weekly > 0 else None,
                            monthly_rate=monthly if monthly > 0 else None,
                            notes=notes if notes else None
                        )
                        if result['success']:
                            st.success("Device pricing added!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(result['message'])
            except Exception as e:
                st.error(f"Error: {e}")
    
    # =====================================================================
    # CATERING & SUPPLIES TAB
    # =====================================================================
    with tab_catering:
        st.subheader("Catering & Supplies Pricing")
        st.caption("Pricing for coffee/tea, pastries, sandwiches, water, stationery")
        
        cater_col1, cater_col2 = st.columns([2, 1])
        
        with cater_col1:
            st.write("**Current Catering & Supplies Pricing**")
            try:
                catering_pricing = pricing_service.get_catering_pricing()
                if catering_pricing.empty:
                    st.info("No catering/supplies pricing set up yet.")
                else:
                    for _, item in catering_pricing.iterrows():
                        with st.expander(f"{item['item_name']}"):
                            st.write(f"**Price: R{item.get('unit_price', 0):.2f}** {item.get('unit', 'per person')}")
                            
                            if pd.notna(item.get('notes')):
                                st.caption(f"Notes: {item['notes']}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"Edit", key=f"edit_cater_{item['id']}"):
                                    st.session_state['editing_catering'] = item['id']
                                    st.session_state['edit_cater_name'] = item['item_name']
                                    st.session_state['edit_cater_price'] = float(item.get('unit_price', 0))
                                    st.session_state['edit_cater_unit'] = item.get('unit', 'per person')
                                    st.rerun()
                            with col2:
                                if st.button(f"Delete", key=f"del_cater_{item['id']}"):
                                    result = pricing_service.delete_pricing(item['id'])
                                    if result['success']:
                                        st.success("Item removed!")
                                        time.sleep(1)
                                        st.rerun()
            except Exception as e:
                st.error(f"Error loading catering pricing: {e}")
        
        with cater_col2:
            st.write("**Add Catering/Supply Item**")
            
            item_name = st.text_input("Item Name", placeholder="e.g., Coffee/Tea Station", key="cater_name")
            unit_price = st.number_input("Unit Price (R)", min_value=0.0, step=5.0, key="cater_price")
            unit = st.selectbox("Unit", ["per person", "per item", "per day", "per booking"], key="cater_unit")
            notes = st.text_area("Notes", key="cater_notes")
            
            if st.button("Add Catering Item", key="add_cater_btn"):
                if not item_name:
                    st.error("Please enter an item name")
                elif unit_price <= 0:
                    st.error("Please enter a valid price")
                else:
                    result = pricing_service.create_catering_pricing(
                        item_name=item_name,
                        unit_price=unit_price,
                        unit=unit,
                        notes=notes if notes else None
                    )
                    if result['success']:
                        st.success("Catering item added!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result['message'])
    
    # =====================================================================
    # EDIT MODE (shown below tabs if editing)
    # =====================================================================
    if 'editing_room' in st.session_state:
        st.divider()
        st.subheader(f"✏️ Editing: {st.session_state.get('edit_room_name', 'Room')}")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_daily = st.number_input("Daily Rate (R)", value=st.session_state.get('edit_daily', 0.0), min_value=0.0, step=50.0, key="edit_room_daily")
        with col2:
            new_weekly = st.number_input("Weekly Rate (R)", value=st.session_state.get('edit_weekly', 0.0), min_value=0.0, step=100.0, key="edit_room_weekly")
        with col3:
            new_monthly = st.number_input("Monthly Rate (R)", value=st.session_state.get('edit_monthly', 0.0), min_value=0.0, step=500.0, key="edit_room_monthly")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("💾 Save Changes", type="primary"):
                result = pricing_service.update_pricing(
                    pricing_id=st.session_state['editing_room'],
                    daily_rate=new_daily if new_daily > 0 else None,
                    weekly_rate=new_weekly if new_weekly > 0 else None,
                    monthly_rate=new_monthly if new_monthly > 0 else None
                )
                if result['success']:
                    del st.session_state['editing_room']
                    st.success("Pricing updated!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result['message'])
        with col_cancel:
            if st.button("❌ Cancel"):
                del st.session_state['editing_room']
                st.rerun()
    
    if 'editing_device' in st.session_state:
        st.divider()
        st.subheader(f"✏️ Editing: {st.session_state.get('edit_device_name', 'Device Category')}")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_daily = st.number_input("Daily Rate (R)", value=st.session_state.get('edit_dev_daily', 0.0), min_value=0.0, step=10.0, key="edit_dev_daily")
        with col2:
            new_weekly = st.number_input("Weekly Rate (R)", value=st.session_state.get('edit_dev_weekly', 0.0), min_value=0.0, step=50.0, key="edit_dev_weekly")
        with col3:
            new_monthly = st.number_input("Monthly Rate (R)", value=st.session_state.get('edit_dev_monthly', 0.0), min_value=0.0, step=200.0, key="edit_dev_monthly")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("💾 Save Changes", type="primary", key="save_dev"):
                result = pricing_service.update_pricing(
                    pricing_id=st.session_state['editing_device'],
                    daily_rate=new_daily if new_daily > 0 else None,
                    weekly_rate=new_weekly if new_weekly > 0 else None,
                    monthly_rate=new_monthly if new_monthly > 0 else None
                )
                if result['success']:
                    del st.session_state['editing_device']
                    st.success("Pricing updated!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result['message'])
        with col_cancel:
            if st.button("❌ Cancel", key="cancel_dev"):
                del st.session_state['editing_device']
                st.rerun()
    
    if 'editing_catering' in st.session_state:
        st.divider()
        st.subheader(f"✏️ Editing: {st.session_state.get('edit_cater_name', 'Catering Item')}")
        new_price = st.number_input("Unit Price (R)", value=st.session_state.get('edit_cater_price', 0.0), min_value=0.0, step=5.0, key="edit_cater_price_input")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("💾 Save Changes", type="primary", key="save_cater"):
                result = pricing_service.update_pricing(
                    pricing_id=st.session_state['editing_catering'],
                    daily_rate=new_price if new_price > 0 else None
                )
                if result['success']:
                    del st.session_state['editing_catering']
                    st.success("Price updated!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result['message'])
        with col_cancel:
            if st.button("❌ Cancel", key="cancel_cater"):
                del st.session_state['editing_catering']
                st.rerun()
