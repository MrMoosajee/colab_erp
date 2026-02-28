# ----------------------------------------------------------------------------
# MAIN CONTROLLER - CORRECTED ROLE DEFINITIONS
# ----------------------------------------------------------------------------

def main():
    init_session_state()

    if not st.session_state['authenticated']:
        render_login()
        return

    st.sidebar.title("Colab ERP v2.2.0")
    st.sidebar.caption(f"User: {st.session_state['username']} ({st.session_state['role']})")
    st.sidebar.info("System Status: 🟢 Online (Headless)")

    # Navigation Logic based on Role - CORRECTED
    user_role = st.session_state['role']
    
    # Room Boss = training_facility_admin (Full access, assigns rooms)
    if user_role == 'training_facility_admin':
        menu = ["Dashboard", "Notifications", "Calendar", "Device Assignment Queue", "New Room Booking", 
                "New Device Booking", "Pricing Catalog", "Pending Approvals", "Inventory Dashboard"]
    
    # IT Boss = it_rental_admin (Full access, device queue)
    elif user_role == 'it_rental_admin':
        menu = ["Dashboard", "Notifications", "Calendar", "Device Assignment Queue", "New Room Booking", 
                "New Device Booking", "Pricing Catalog", "Pending Approvals", "Inventory Dashboard"]
    
    # Training Facility Admin (Viewer only - NO approval power)
    elif user_role == 'training_facility_admin_viewer':
        menu = ["Calendar", "Bookings", "Pricing Catalog", "Approvals", "Inventory Dashboard"]
    
    # Kitchen Staff (Calendar only with catering view)
    elif user_role == 'kitchen_staff':
        menu = ["Kitchen Calendar"]
    
    # Staff/Default (Limited access)
    else:
        menu = ["Calendar", "New Room Booking", "New Device Booking", 
                "Pending Approvals", "Inventory Dashboard"]

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
        render_enhanced_booking_form()
    elif choice == "New Device Booking":
        render_new_device_booking()
    elif choice == "Pricing Catalog":
        pricing_service = PricingService()
        render_pricing_catalog_new(pricing_service, st.session_state['role'])
    elif choice == "Pending Approvals":
        render_pending_approvals()
    elif choice == "Inventory Dashboard":
        render_inventory_dashboard()
    elif choice == "Kitchen Calendar":
        render_kitchen_calendar_view()
    elif choice == "Bookings":
        render_bookings_view()
    elif choice == "Approvals":
        render_approvals_view()

if __name__ == "__main__":
    main()
