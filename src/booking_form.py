"""
Enhanced Booking Form - Phase 3 Implementation with Ghost Inventory
Complete booking form with room selection, conflict checking, and multi-room support
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import date
from src.models import BookingService, AvailabilityService

# Initialize services
booking_service = BookingService()
availability_service = AvailabilityService()


def render_enhanced_booking_form():
    """
    Render the enhanced Phase 3 booking form with Ghost Inventory workflow.
    - Admin/Room Boss: Can select room (if no conflict) or skip to pending
    - Staff: Always skip to pending
    - Multi-room: One client, multiple date ranges
    """
    st.header("📝 New Booking Request")
    st.caption("Facility hours: 07:30 - 16:30 daily")

    # Check user role
    user_role = st.session_state.get('role', 'staff')
    is_admin = user_role in ['admin', 'training_facility_admin', 'room_boss']

    # Initialize session state
    today = date.today()
    if 'booking_start_date' not in st.session_state:
        st.session_state.booking_start_date = today
    if 'booking_end_date' not in st.session_state:
        st.session_state.booking_end_date = st.session_state.booking_start_date
    if 'booking_segments' not in st.session_state:
        st.session_state.booking_segments = []

    # Section 1: Client Information
    st.subheader("📋 Client Information")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("Client/Company Name *", key="client_name")
            client_contact = st.text_input("Contact Person *", key="contact_person")
        with col2:
            client_email = st.text_input("Email *", key="client_email")
            client_phone = st.text_input("Phone Number *", key="client_phone")

    st.divider()

    # Section 2: Booking Period Selection Mode
    st.subheader("📅 Booking Configuration")

    # Role-based room selection options
    if is_admin:
        room_selection_mode = st.radio(
            "Room Selection Mode",
            options=['select_room', 'skip_pending'],
            format_func=lambda x: {
                'select_room': '🏢 Select Room (Direct Booking)',
                'skip_pending': '⏳ Skip - Send to Room Boss for Approval'
            }[x],
            help="Select room now if available, or let Room Boss assign later"
        )
    else:
        room_selection_mode = 'skip_pending'
        st.info("⏳ As staff user, booking will be sent to Room Boss for room assignment")

    st.divider()

    # Section 3: Booking Segments (Multi-room support)
    st.subheader("📆 Booking Segments")
    st.caption("Add one or more date ranges. Same client can use different rooms for different dates.")

    # Display existing segments
    if st.session_state.booking_segments:
        st.write("**Current Segments:**")
        for i, segment in enumerate(st.session_state.booking_segments):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                room_text = f"Room: {segment['room_name']}" if segment.get('room_name') else "Room: Pending Assignment"
                st.write(f"{i+1}. {segment['start_date']} to {segment['end_date']} | {room_text}")
            with col2:
                if segment.get('conflict_warning'):
                    st.warning("⚠️ Conflict detected!")
            with col3:
                if st.button("❌ Remove", key=f"remove_seg_{i}"):
                    st.session_state.booking_segments.pop(i)
                    st.rerun()

    # Add new segment form
    with st.expander("➕ Add Booking Segment", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            seg_start = st.date_input(
                "Start Date *",
                value=st.session_state.booking_start_date,
                min_value=date.today(),
                key="seg_start"
            )
        with col2:
            seg_end = st.date_input(
                "End Date *",
                value=st.session_state.booking_end_date,
                key="seg_end"
            )

        # Validate date range manually (instead of using min_value which conflicts with session state)
        if seg_start > seg_end:
            st.error("❌ Start date cannot be after end date")
            # Auto-correct end date to match start date
            seg_end = seg_start

        # Room selection (only for admin in 'select_room' mode)
        selected_room_id = None
        selected_room_name = None
        conflict_info = None

        if room_selection_mode == 'select_room' and is_admin:
            # Get all rooms for selection (not just available)
            all_rooms = availability_service.get_all_rooms()

            if all_rooms.empty:
                st.error("❌ No rooms found in database")
            else:
                room_options = all_rooms['id'].tolist()
                selected_room_id = st.selectbox(
                    "Select Room *",
                    options=room_options,
                    format_func=lambda x: f"{all_rooms[all_rooms['id'] == x]['name'].values[0]} (Capacity: {all_rooms[all_rooms['id'] == x]['capacity'].values[0]})",
                    key="room_select"
                )

                if selected_room_id:
                    selected_room_name = all_rooms[all_rooms['id'] == selected_room_id]['name'].values[0]

                    # Check for conflicts
                    conflict_info = availability_service.check_room_conflicts(
                        selected_room_id, seg_start, seg_end
                    )

                    if conflict_info['has_conflict']:
                        st.error(f"🚫 **CONFLICT DETECTED**: {conflict_info['message']}")
                        st.write("Existing bookings:")
                        for conflict in conflict_info['conflicts']:
                            st.write(f"- {conflict['client_name']}: {conflict['start_date']} to {conflict['end_date']}")
                        st.warning("⚠️ You cannot book this room. Either choose a different room or use 'Skip - Send to Pending' mode.")
                    else:
                        st.success(f"✅ Room available: {conflict_info['message']}")

        # Notes for Room Boss (especially useful for staff)
        room_notes = st.text_area(
            "Room Preferences / Notes for Room Boss",
            placeholder="E.g., 'Prefer Dedication room if available', 'Need projector', etc.",
            key="room_notes"
        )

        # Add segment button
        if st.button("➕ Add This Segment", key="add_segment"):
            if seg_start > seg_end:
                st.error("❌ Start date cannot be after end date")
            elif room_selection_mode == 'select_room' and is_admin and not selected_room_id:
                st.error("❌ Please select a room")
            elif room_selection_mode == 'select_room' and is_admin and conflict_info and conflict_info['has_conflict']:
                st.error("🚫 Cannot add segment - room has conflicts. Choose a different room or use 'Skip to Pending' mode.")
            else:
                segment = {
                    'start_date': seg_start,
                    'end_date': seg_end,
                    'room_id': selected_room_id,
                    'room_name': selected_room_name,
                    'room_notes': room_notes,
                    'conflict_warning': conflict_info['has_conflict'] if conflict_info else False
                }
                st.session_state.booking_segments.append(segment)
                st.success(f"✅ Segment added: {seg_start} to {seg_end}")
                st.rerun()

    if not st.session_state.booking_segments:
        st.error("❌ Please add at least one booking segment")
        return

    st.divider()

    # Section 4: Attendees
    st.subheader("👥 Attendees")
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            num_learners = st.number_input(
                "Number of Learners *",
                min_value=0, value=0, step=1, key="num_learners"
            )
        with col2:
            num_facilitators = st.number_input(
                "Number of Facilitators *",
                min_value=0, value=0, step=1, key="num_facilitators"
            )
        with col3:
            total_headcount = num_learners + num_facilitators
            st.metric("Total Headcount", total_headcount)

    st.divider()

    # Section 5: Catering
    st.subheader("☕ Catering")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            coffee_tea = st.checkbox("Coffee/Tea Station", key="coffee_tea")
            morning_catering = st.selectbox(
                "Morning Catering",
                options=['none', 'pastry', 'sandwiches'],
                format_func=lambda x: {'none': 'None', 'pastry': 'Pastry', 'sandwiches': 'Sandwiches'}[x],
                key="morning_catering"
            )
        with col2:
            lunch_catering = st.selectbox(
                "Lunch Catering",
                options=['none', 'self_catered', 'in_house'],
                format_func=lambda x: {'none': 'None', 'self_catered': 'Self-catered', 'in_house': 'In-house'}[x],
                key="lunch_catering"
            )

        if lunch_catering == 'in_house':
            catering_notes = st.text_area(
                "Catering Requests",
                placeholder="Specific food requests (if < 3 days). Note: ≥ 3 days = auto-alternating menu",
                key="catering_notes"
            )
        else:
            catering_notes = None

    st.divider()

    # Section 6: Supplies
    st.subheader("📚 Supplies")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            stationery = st.checkbox("Stationery (Pen & Book) - Per person", key="stationery")
        with col2:
            water_bottles = st.number_input("Water Bottles (per day)", min_value=0, value=0, step=1, key="water_bottles")

    st.divider()

    # Section 7: Devices
    st.subheader("💻 Devices")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            devices_needed = st.number_input("Devices Needed", min_value=0, value=0, step=1, key="devices_needed")
        with col2:
            device_type = st.selectbox(
                "Device Type Preference",
                options=['any', 'laptops', 'desktops'],
                format_func=lambda x: {'any': 'Any', 'laptops': 'Laptops Only', 'desktops': 'Desktops Only'}[x],
                key="device_type"
            )

        device_check = {'available': True, 'message': ''}
        if devices_needed > 0:
            # Check device availability across all segments
            for segment in st.session_state.booking_segments:
                segment_device_check = availability_service.check_device_availability(
                    devices_needed, segment['start_date'], segment['end_date'], device_type
                )
                if not segment_device_check['available']:
                    device_check = segment_device_check
                    st.error(f"❌ {segment['start_date']} to {segment['end_date']}: {segment_device_check['message']}")
                    break
            else:
                device_check = {'available': True, 'message': f'✅ {devices_needed} devices available for all segments'}
                st.success(device_check['message'])

    st.divider()

    # Booking Summary
    st.subheader("📋 Booking Summary")
    st.write(f"**Client:** {client_name or '(not entered)'}")
    st.write(f"**Segments:** {len(st.session_state.booking_segments)}")
    for i, seg in enumerate(st.session_state.booking_segments):
        room_text = seg.get('room_name', 'Pending Assignment')
        st.write(f"  {i+1}. {seg['start_date']} to {seg['end_date']} → {room_text}")
    st.write(f"**Attendees:** {total_headcount} ({num_learners} learners + {num_facilitators} facilitators)")

    # Submit
    if st.button("🚀 Submit Booking Request", type="primary", use_container_width=True):
        errors = []
        if not client_name:
            errors.append("Client name is required")
        if not client_contact:
            errors.append("Contact person is required")
        if not client_email:
            errors.append("Email is required")
        if not client_phone:
            errors.append("Phone is required")
        if not st.session_state.booking_segments:
            errors.append("Please add at least one booking segment")
        if num_learners + num_facilitators == 0:
            errors.append("At least one attendee is required")
        if devices_needed > 0 and not device_check['available']:
            errors.append(f"Not enough devices available for one or more segments")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            try:
                # Create bookings for all segments
                created_bookings = []
                failed_bookings = []

                for segment in st.session_state.booking_segments:
                    # Determine status based on room selection
                    if segment.get('room_id'):
                        status = 'Confirmed'
                    else:
                        status = 'Pending'

                    result = booking_service.create_enhanced_booking(
                        room_id=segment.get('room_id'),  # None if pending
                        start_date=segment['start_date'],
                        end_date=segment['end_date'],
                        client_name=client_name,
                        client_contact_person=client_contact,
                        client_email=client_email,
                        client_phone=client_phone,
                        num_learners=num_learners,
                        num_facilitators=num_facilitators,
                        coffee_tea_station=coffee_tea,
                        morning_catering=morning_catering if morning_catering != 'none' else None,
                        lunch_catering=lunch_catering if lunch_catering != 'none' else None,
                        catering_notes=catering_notes,
                        stationery_needed=stationery,
                        water_bottles=water_bottles,
                        devices_needed=devices_needed,
                        device_type_preference=device_type if device_type != 'any' else None,
                        room_boss_notes=segment.get('room_notes'),
                        status=status,
                        created_by=st.session_state.get('username')
                    )

                    if result['success']:
                        created_bookings.append({
                            'booking_id': result['booking_id'],
                            'segment': segment,
                            'status': status
                        })
                    else:
                        failed_bookings.append({
                            'segment': segment,
                            'error': result.get('message', 'Unknown error')
                        })

                # Show results
                if created_bookings:
                    st.success(f"✅ Successfully created {len(created_bookings)} booking(s)!")
                    for booking in created_bookings:
                        seg = booking['segment']
                        room_text = seg.get('room_name', 'Pending Assignment')
                        status_icon = '✅' if booking['status'] == 'Confirmed' else '⏳'
                        st.write(f"{status_icon} Booking #{booking['booking_id']}: {seg['start_date']} to {seg['end_date']} ({room_text}) - **{booking['status']}**")

                if failed_bookings:
                    st.error(f"❌ Failed to create {len(failed_bookings)} booking(s)")
                    for fail in failed_bookings:
                        st.write(f"- {fail['segment']['start_date']} to {fail['segment']['end_date']}: {fail['error']}")

                if created_bookings and not failed_bookings:
                    st.balloons()
                    # Clear segments after successful creation
                    st.session_state.booking_segments = []
                    st.rerun()

            except Exception as e:
                st.error(f"❌ System error: {e}")
