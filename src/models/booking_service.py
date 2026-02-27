"""
Booking Service - Enhanced Booking Creation for Phase 3
Handles all 13 new fields including attendees, catering, supplies, and devices
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import src.db as db
from datetime import date, datetime
from typing import Optional, Dict, Any
from .availability_service import AvailabilityService


class BookingService:
    """
    Service class for creating enhanced bookings with full details.
    Handles the 13 new Phase 3 fields.
    """

    def __init__(self):
        """Initialize BookingService with database connection."""
        self.connection_pool = db.get_db_pool()
        self.availability_service = AvailabilityService()

    def create_enhanced_booking(
        self,
        room_id: int,
        start_date: date,
        end_date: date,
        client_name: str,
        client_contact_person: str,
        client_email: str,
        client_phone: str,
        num_learners: int = 0,
        num_facilitators: int = 0,
        coffee_tea_station: bool = False,
        morning_catering: Optional[str] = None,
        lunch_catering: Optional[str] = None,
        catering_notes: Optional[str] = None,
        stationery_needed: bool = False,
        water_bottles: int = 0,
        devices_needed: int = 0,
        device_type_preference: Optional[str] = None,
        room_boss_notes: Optional[str] = None,
        status: str = 'Pending'
    ) -> Dict[str, Any]:
        """
        Create an enhanced booking with all Phase 3 fields.
        NOTE: room_id is required (NOT NULL in database).
        For pending bookings, use a placeholder room or specific workflow.
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                start_dt = datetime.combine(start_date, datetime.min.time()).replace(hour=7, minute=30)
                end_dt = datetime.combine(end_date, datetime.min.time()).replace(hour=16, minute=30)

                # Calculate total headcount
                total_headcount = num_learners + num_facilitators

                # Insert booking with ALL fields properly mapped
                cur.execute(
                    """
                    INSERT INTO bookings (
                        room_id, booking_period, client_name, status,
                        headcount, end_date, num_learners, num_facilitators,
                        coffee_tea_station, morning_catering, lunch_catering, catering_notes,
                        stationery_needed, water_bottles,
                        devices_needed, device_type_preference,
                        client_contact_person, client_email, client_phone,
                        room_boss_notes
                    ) VALUES (
                        %s, tstzrange(%s, %s, '[)'), %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        room_id, start_dt, end_dt, client_name, status,
                        total_headcount, end_date, num_learners, num_facilitators,
                        coffee_tea_station, morning_catering, lunch_catering, catering_notes,
                        stationery_needed, water_bottles,
                        devices_needed, device_type_preference,
                        client_contact_person, client_email, client_phone,
                        room_boss_notes
                    )
                )

                booking_id = cur.fetchone()[0]
                conn.commit()

                status_text = "confirmed" if status == 'Confirmed' else "pending approval"
                return {
                    'success': True,
                    'booking_id': booking_id,
                    'message': f'Booking #{booking_id} created successfully for {client_name} ({status_text})'
                }

        except Exception as e:
            if conn:
                conn.rollback()
            return {
                'success': False,
                'booking_id': None,
                'message': f'Failed to create booking: {str(e)}'
            }
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def create_device_only_booking(
        self,
        client_name: str,
        client_contact_person: str,
        client_email: str,
        client_phone: str,
        start_date: date,
        end_date: date,
        device_requests: list,
        rental_no: str,
        offsite_contact: str,
        offsite_phone: str,
        offsite_email: Optional[str],
        offsite_company: str,
        offsite_address: str,
        return_expected_date: date,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a device-only booking (off-site rental without room).
        Uses room_id=1 as a placeholder for tracking purposes.
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                start_dt = datetime.combine(start_date, datetime.min.time()).replace(hour=7, minute=30)
                end_dt = datetime.combine(end_date, datetime.min.time()).replace(hour=16, minute=30)

                # Calculate total devices needed
                total_devices = sum(req['quantity'] for req in device_requests)

                # Use room_id=1 as placeholder for device-only bookings
                # This ensures database constraint is satisfied
                placeholder_room_id = 1

                # Insert booking
                cur.execute(
                    """
                    INSERT INTO bookings (
                        room_id, booking_period, client_name, status,
                        headcount, end_date, num_learners, num_facilitators,
                        coffee_tea_station, morning_catering, lunch_catering, catering_notes,
                        stationery_needed, water_bottles,
                        devices_needed, device_type_preference,
                        client_contact_person, client_email, client_phone,
                        room_boss_notes, created_by
                    ) VALUES (
                        %s, tstzrange(%s, %s, '[)'), %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        placeholder_room_id, start_dt, end_dt, client_name, 'Pending',
                        total_devices, end_date, 0, 0,  # headcount = devices for device-only
                        False, None, None, None,  # no catering
                        False, 0,  # no stationery
                        total_devices, 'any',  # device info
                        client_contact_person, client_email, client_phone,
                        f"OFF-SITE RENTAL | Rental No: {rental_no} | Contact: {offsite_contact} | "
                        f"Phone: {offsite_phone} | Company: {offsite_company} | "
                        f"Address: {offsite_address} | Return: {return_expected_date} | "
                        f"Notes: {notes or 'N/A'}",
                        created_by
                    )
                )

                booking_id = cur.fetchone()[0]

                # Create device assignment records (pending actual device assignment)
                for req in device_requests:
                    cur.execute(
                        """
                        INSERT INTO booking_device_assignments 
                        (booking_id, device_category_id, quantity, assigned_by, notes)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            booking_id,
                            req['category_id'],
                            req['quantity'],
                            created_by,
                            f"Off-site rental request for {req['category_name']} - {rental_no}"
                        )
                    )

                conn.commit()

                return {
                    'success': True,
                    'booking_id': booking_id,
                    'message': f'Device booking #{booking_id} created successfully for {client_name}'
                }

        except Exception as e:
            if conn:
                conn.rollback()
            return {
                'success': False,
                'booking_id': None,
                'message': f'Failed to create device booking: {str(e)}'
            }
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_booking_details(self, booking_id: int) -> Dict[str, Any]:
        """Retrieve full booking details including all Phase 3 fields."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        b.id, b.room_id, r.name as room_name,
                        b.booking_period, b.client_name, b.status,
                        b.num_learners, b.num_facilitators,
                        b.client_contact_person, b.client_email, b.client_phone,
                        b.coffee_tea_station, b.morning_catering, b.lunch_catering,
                        b.catering_notes, b.stationery_needed, b.water_bottles,
                        b.devices_needed, b.device_type_preference,
                        b.created_at
                    FROM bookings b
                    LEFT JOIN rooms r ON b.room_id = r.id
                    WHERE b.id = %s
                    """,
                    (booking_id,)
                )

                row = cur.fetchone()
                if not row:
                    return {'success': False, 'message': 'Booking not found'}

                columns = [desc[0] for desc in cur.description]
                booking_dict = dict(zip(columns, row))

                return {'success': True, 'booking': booking_dict}

        except Exception as e:
            return {'success': False, 'message': f'Error retrieving booking: {str(e)}'}
        finally:
            if conn:
                self.connection_pool.putconn(conn)
