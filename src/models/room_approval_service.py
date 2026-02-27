"""
Room Approval Service - Ghost Inventory Room Assignment for Room Boss
Handles pending bookings requiring room assignment with conflict detection
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import src.db as db
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import pytz


class RoomApprovalService:
    """
    Service class for Room Boss room assignment workflow.
    Implements ghost inventory pattern - allows bookings without immediate room assignment.
    """

    def __init__(self):
        """Initialize RoomApprovalService with database connection."""
        self.connection_pool = db.get_db_pool()

    def get_pending_bookings(self, limit: int = 50) -> pd.DataFrame:
        """
        Get all bookings pending room assignment.
        
        Returns:
            DataFrame with booking details including client info, dates, requirements
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        b.id as booking_id,
                        b.client_name,
                        b.client_contact_person,
                        b.client_email,
                        b.client_phone,
                        b.num_learners,
                        b.num_facilitators,
                        (b.num_learners + b.num_facilitators) as total_headcount,
                        lower(b.booking_period)::date as start_date,
                        upper(b.booking_period)::date as end_date,
                        b.room_id as requested_room_id,
                        r.name as requested_room_name,
                        b.morning_catering,
                        b.lunch_catering,
                        b.devices_needed,
                        b.status,
                        b.room_boss_notes,
                        b.created_at,
                        u.username as created_by
                    FROM bookings b
                    LEFT JOIN rooms r ON b.room_id = r.id
                    LEFT JOIN users u ON b.created_by = u.user_id
                    WHERE b.status = 'Pending'
                    ORDER BY lower(b.booking_period), b.created_at
                    LIMIT %s
                """
                cur.execute(query, (limit,))
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return pd.DataFrame(rows, columns=columns)
        except Exception as e:
            print(f"Error getting pending bookings: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_room_occupancy(
        self, 
        start_date: date, 
        end_date: date, 
        exclude_booking_id: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get room occupancy for date range to show Room Boss current bookings.
        
        Returns:
            DataFrame with room occupancy data for calendar view
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                # Use UTC timezone for consistency
                utc = pytz.UTC
                start_dt = utc.localize(datetime.combine(start_date, datetime.min.time()))
                end_dt = utc.localize(datetime.combine(end_date, datetime.min.time()).replace(hour=23, minute=59))

                query = """
                    SELECT 
                        r.id as room_id,
                        r.name as room_name,
                        r.capacity,
                        b.id as booking_id,
                        b.client_name,
                        lower(b.booking_period)::date as booking_start,
                        upper(b.booking_period)::date as booking_end,
                        b.status,
                        (b.num_learners + b.num_facilitators) as headcount
                    FROM rooms r
                    LEFT JOIN bookings b ON (
                        b.room_id = r.id
                        AND b.status IN ('Room Assigned', 'Confirmed')
                        AND b.booking_period && tstzrange(%s, %s, '[)')
                    )
                    WHERE 1=1
                """
                params = [start_dt, end_dt]

                if exclude_booking_id:
                    query += " AND b.id != %s"
                    params.append(exclude_booking_id)

                query += " ORDER BY r.name, lower(b.booking_period)"

                cur.execute(query, params)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return pd.DataFrame(rows, columns=columns)
        except Exception as e:
            print(f"Error getting room occupancy: {e}")
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
        
        Returns:
            Dict with conflict info and override recommendation
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                utc = pytz.UTC
                start_dt = utc.localize(datetime.combine(start_date, datetime.min.time()))
                end_dt = utc.localize(datetime.combine(end_date, datetime.min.time()).replace(hour=23, minute=59))

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
                        'message': f"⚠️ {len(conflicts)} conflicting booking(s) found",
                        'can_override': True
                    }
                else:
                    return {
                        'has_conflict': False,
                        'conflicts': [],
                        'message': "✅ No conflicts - room is clear",
                        'can_override': True
                    }
        except Exception as e:
            return {
                'has_conflict': True,
                'conflicts': [],
                'message': f"Error checking conflicts: {str(e)}",
                'can_override': False
            }
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def assign_room(
        self, 
        booking_id: int, 
        room_id: int, 
        room_boss_id: str,
        notes: Optional[str] = None,
        override_conflict: bool = False
    ) -> Dict[str, Any]:
        """
        Assign room to pending booking.
        
        Args:
            booking_id: ID of booking to update
            room_id: ID of room to assign
            room_boss_id: Username of room boss making assignment
            notes: Optional notes about assignment decision
            override_conflict: Whether to proceed despite conflicts
            
        Returns:
            Dict with success status and message
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                # Verify booking exists and is pending
                cur.execute(
                    "SELECT status, lower(booking_period)::date, upper(booking_period)::date FROM bookings WHERE id = %s",
                    (booking_id,)
                )
                result = cur.fetchone()
                
                if not result:
                    return {'success': False, 'error': 'Booking not found'}
                
                status, start_date, end_date = result
                
                if status != 'Pending':
                    return {'success': False, 'error': f'Booking status is {status}, not Pending'}
                
                # Check for conflicts unless overriding
                if not override_conflict:
                    conflict_check = self.check_room_conflicts(room_id, start_date, end_date, booking_id)
                    if conflict_check['has_conflict']:
                        return {
                            'success': False, 
                            'error': 'Room conflicts detected. Use override to proceed anyway.',
                            'conflicts': conflict_check['conflicts']
                        }
                
                # Update booking with room assignment
                cur.execute("""
                    UPDATE bookings 
                    SET room_id = %s,
                        status = 'Room Assigned',
                        room_boss_notes = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (room_id, notes, booking_id))
                
                conn.commit()
                
                # Get room name for notification
                cur.execute("SELECT name FROM rooms WHERE id = %s", (room_id,))
                room_name = cur.fetchone()[0]
                
                return {
                    'success': True,
                    'message': f'✅ Room {room_name} assigned successfully',
                    'room_name': room_name,
                    'override_used': override_conflict
                }
                
        except Exception as e:
            if conn:
                conn.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}'}
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_room_list(self) -> pd.DataFrame:
        """
        Get list of all available rooms for selection.
        
        Returns:
            DataFrame with room details
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, capacity, room_type, has_devices
                    FROM rooms
                    ORDER BY capacity, name
                """)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return pd.DataFrame(rows, columns=columns)
        except Exception as e:
            print(f"Error getting room list: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def reject_booking(
        self, 
        booking_id: int, 
        room_boss_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Reject a pending booking with reason.
        
        Args:
            booking_id: ID of booking to reject
            room_boss_id: Username of room boss
            reason: Rejection reason
            
        Returns:
            Dict with success status
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE bookings 
                    SET status = 'Rejected',
                        room_boss_notes = %s,
                        updated_at = NOW()
                    WHERE id = %s AND status = 'Pending'
                """, (f"REJECTED: {reason}", booking_id))
                
                if cur.rowcount == 0:
                    return {'success': False, 'error': 'Booking not found or not in Pending status'}
                
                conn.commit()
                return {'success': True, 'message': 'Booking rejected'}
        except Exception as e:
            if conn:
                conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            if conn:
                self.connection_pool.putconn(conn)
