"""
Availability Service - Room and Device Availability Checking for Phase 3
Handles availability validation and capacity checking
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import src.db as db
from datetime import date, datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import pytz


class AvailabilityService:
    """
    Service class for checking room and device availability.
    Handles capacity validation and conflict detection.
    """

    def __init__(self):
        """Initialize AvailabilityService with database connection."""
        self.connection_pool = db.get_db_pool()

    def get_available_rooms(
        self,
        start_date: date,
        end_date: date,
        min_capacity: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get list of rooms available for the specified date range.
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                # FIX: Create timezone-aware datetimes in UTC to match database tstzrange
                utc = pytz.UTC
                start_dt = utc.localize(datetime.combine(start_date, datetime.min.time()).replace(hour=7, minute=30))
                end_dt = utc.localize(datetime.combine(end_date, datetime.min.time()).replace(hour=16, minute=30))

                query = """
                    SELECT
                        r.id,
                        r.name,
                        r.capacity,
                        r.room_type,
                        r.has_devices,
                        COUNT(b.id) as conflicting_bookings
                    FROM rooms r
                    LEFT JOIN bookings b ON (
                        b.room_id = r.id
                        AND b.status IN ('Room Assigned', 'Confirmed')
                        AND b.booking_period && tstzrange(%s, %s, '[)')
                    )
                    WHERE 1=1
                """
                params = [start_dt, end_dt]

                if min_capacity:
                    query += " AND r.capacity >= %s"
                    params.append(min_capacity)

                query += """
                    GROUP BY r.id, r.name, r.capacity, r.room_type, r.has_devices
                    HAVING COUNT(b.id) = 0
                    ORDER BY r.capacity, r.name
                """

                cur.execute(query, params)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            print(f"Error getting available rooms: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_all_rooms(self) -> pd.DataFrame:
        """
        Get all rooms regardless of availability.
        Used for admin room selection.
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, max_capacity as capacity, is_active, parent_room_id
                    FROM rooms
                    ORDER BY max_capacity, name
                """)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return pd.DataFrame(rows, columns=columns)
        except Exception as e:
            print(f"Error getting all rooms: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def check_room_conflicts(
        self,
        room_id: int,
        start_date: date,
        end_date: date,
        exclude_booking_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if room has conflicting bookings.
        Returns conflict info for admin room selection.
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                # FIX: Create timezone-aware datetimes in UTC
                utc = pytz.UTC
                start_dt = utc.localize(datetime.combine(start_date, datetime.min.time()).replace(hour=7, minute=30))
                end_dt = utc.localize(datetime.combine(end_date, datetime.min.time()).replace(hour=16, minute=30))

                query = """
                    SELECT
                        b.id as booking_id,
                        b.client_name,
                        lower(b.booking_period)::date as booking_start,
                        upper(b.booking_period)::date as booking_end,
                        b.status
                    FROM bookings b
                    WHERE b.room_id = %s
                    AND b.status IN ('Room Assigned', 'Confirmed')
                    AND b.booking_period && tstzrange(%s, %s, '[)')
                """
                params = [room_id, start_dt, end_dt]

                if exclude_booking_id:
                    query += " AND b.id != %s"
                    params.append(exclude_booking_id)

                query += " ORDER BY lower(b.booking_period)"

                cur.execute(query, params)
                conflicts = cur.fetchall()

                if conflicts:
                    return {
                        'has_conflict': True,
                        'conflicts': [
                            {
                                'booking_id': c[0],
                                'client_name': c[1],
                                'start_date': c[2],
                                'end_date': c[3],
                                'status': c[4]
                            }
                            for c in conflicts
                        ],
                        'message': f"Room has {len(conflicts)} conflicting booking(s)"
                    }
                else:
                    return {
                        'has_conflict': False,
                        'conflicts': [],
                        'message': "Room is available for the selected dates"
                    }

        except Exception as e:
            return {
                'has_conflict': True,
                'conflicts': [],
                'message': f"Error checking conflicts: {str(e)}"
            }
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def validate_booking_capacity(
        self,
        room_id: int,
        total_attendees: int
    ) -> Dict[str, Any]:
        """
        Validate if room can accommodate the requested number of attendees.
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT capacity, name FROM rooms WHERE id = %s",
                    (room_id,)
                )
                result = cur.fetchone()

                if not result:
                    return {
                        'valid': False,
                        'warning': True,
                        'message': 'Room not found'
                    }

                capacity, room_name = result

                if total_attendees > capacity:
                    return {
                        'valid': False,
                        'warning': True,
                        'message': f'⚠️ {room_name} capacity ({capacity}) exceeded by {total_attendees - capacity} people'
                    }
                elif total_attendees > capacity * 0.9:
                    return {
                        'valid': True,
                        'warning': True,
                        'message': f'⚠️ {room_name} will be at {int((total_attendees/capacity)*100)}% capacity'
                    }
                else:
                    return {
                        'valid': True,
                        'warning': False,
                        'message': f'✅ {room_name} has sufficient capacity ({total_attendees}/{capacity})'
                    }

        except Exception as e:
            return {
                'valid': False,
                'warning': True,
                'message': f'Error validating capacity: {str(e)}'
            }
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def check_device_availability(
        self,
        devices_needed: int,
        start_date: date,
        end_date: date,
        device_type: str = 'any'
    ) -> Dict[str, Any]:
        """
        Check if requested number of devices are available.
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                # FIX: Create timezone-aware datetimes in UTC to match database tstzrange
                utc = pytz.UTC
                start_dt = utc.localize(datetime.combine(start_date, datetime.min.time()).replace(hour=7, minute=30))
                end_dt = utc.localize(datetime.combine(end_date, datetime.min.time()).replace(hour=16, minute=30))

                type_filter = ""
                params = [start_dt, end_dt]

                if device_type == 'laptops':
                    type_filter = "AND dc.name ILIKE '%laptop%'"
                elif device_type == 'desktops':
                    type_filter = "AND dc.name ILIKE '%desktop%'"

                query = f"""
                    SELECT COUNT(d.id)
                    FROM devices d
                    JOIN device_categories dc ON d.category_id = dc.id
                    WHERE d.status = 'available'
                    {type_filter}
                    AND d.id NOT IN (
                        SELECT bda.device_id
                        FROM booking_device_assignments bda
                        JOIN bookings b ON bda.booking_id = b.id
                        WHERE b.status = 'confirmed'
                        AND b.booking_period && tstzrange(%s, %s, '[)')
                        AND bda.device_id IS NOT NULL
                    )
                """

                cur.execute(query, params)
                available_count = cur.fetchone()[0]

                if available_count >= devices_needed:
                    return {
                        'available': True,
                        'available_count': available_count,
                        'message': f'✅ {available_count} devices available (need {devices_needed})'
                    }
                else:
                    return {
                        'available': False,
                        'available_count': available_count,
                        'message': f'❌ Only {available_count} devices available (need {devices_needed})'
                    }

        except Exception as e:
            return {
                'available': False,
                'available_count': 0,
                'message': f'Error checking device availability: {str(e)}'
            }
        finally:
            if conn:
                self.connection_pool.putconn(conn)
