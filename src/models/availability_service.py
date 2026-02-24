"""
Availability Service - Checks room and device availability for booking periods.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import src.db as db


class AvailabilityService:
    """
    Checks availability of rooms and devices for date ranges.
    """
    
    def __init__(self):
        """Initialize AvailabilityService."""
        pass
    
    def get_available_rooms(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Get rooms that are completely available for the entire date range.
        Rooms with ANY booking during the period are excluded.
        
        Args:
            start_date: Start of booking period
            end_date: End of booking period
            
        Returns:
            DataFrame with available rooms
        """
        query = """
            SELECT 
                r.id,
                r.name,
                r.capacity,
                r.location
            FROM rooms r
            WHERE r.id NOT IN (
                SELECT DISTINCT b.room_id
                FROM bookings b
                WHERE b.status NOT IN ('cancelled', 'completed')
                AND (
                    (lower(b.booking_period)::date <= %s AND upper(b.booking_period)::date >= %s)
                    OR (lower(b.booking_period)::date <= %s AND upper(b.booking_period)::date >= %s)
                    OR (lower(b.booking_period)::date >= %s AND upper(b.booking_period)::date <= %s)
                )
            )
            AND r.is_active = true
            ORDER BY r.name
        """
        
        return db.run_query(query, (
            end_date, start_date,  # Overlapping check
            end_date, start_date,
            start_date, end_date
        ))
    
    def check_room_conflicts(self, room_id: int, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Check for existing bookings that conflict with proposed dates.
        
        Args:
            room_id: Room to check
            start_date: Proposed start date
            end_date: Proposed end date
            
        Returns:
            DataFrame with conflicting bookings
        """
        query = """
            SELECT 
                b.id as booking_id,
                b.client_name,
                lower(b.booking_period)::date as start_date,
                upper(b.booking_period)::date as end_date,
                b.status
            FROM bookings b
            WHERE b.room_id = %s
            AND b.status NOT IN ('cancelled', 'completed')
            AND (
                (lower(b.booking_period)::date <= %s AND upper(b.booking_period)::date >= %s)
                OR (lower(b.booking_period)::date <= %s AND upper(b.booking_period)::date >= %s)
                OR (lower(b.booking_period)::date >= %s AND upper(b.booking_period)::date <= %s)
            )
            ORDER BY lower(b.booking_period)
        """
        
        return db.run_query(query, (
            room_id,
            end_date, start_date,
            end_date, start_date,
            start_date, end_date
        ))
    
    def check_device_availability(
        self, 
        device_count: int, 
        start_date: date, 
        end_date: date,
        device_type: str = 'any'
    ) -> Dict:
        """
        Check if enough devices are available for the date range.
        
        Args:
            device_count: Number of devices needed
            start_date: Start of booking period
            end_date: End of booking period
            device_type: 'any', 'laptops', or 'desktops'
            
        Returns:
            Dict with availability status and details
        """
        # Build device type filter
        type_filter = ""
        params = [end_date, start_date, end_date, start_date, start_date, end_date]
        
        if device_type == 'laptops':
            type_filter = "AND dc.name ILIKE '%laptop%'"
        elif device_type == 'desktops':
            type_filter = "AND dc.name ILIKE '%desktop%'"
        
        query = f"""
            SELECT 
                d.id,
                d.serial_number,
                d.name,
                dc.name as category_name
            FROM devices d
            JOIN device_categories dc ON d.category_id = dc.id
            WHERE d.status IN ('available', 'rented')
            AND d.id NOT IN (
                SELECT DISTINCT bda.device_id
                FROM booking_device_assignments bda
                JOIN bookings b ON bda.booking_id = b.id
                WHERE bda.device_id IS NOT NULL
                AND b.status NOT IN ('cancelled', 'completed')
                AND (
                    (lower(b.booking_period)::date <= %s AND upper(b.booking_period)::date >= %s)
                    OR (lower(b.booking_period)::date <= %s AND upper(b.booking_period)::date >= %s)
                    OR (lower(b.booking_period)::date >= %s AND upper(b.booking_period)::date <= %s)
                )
            )
            {type_filter}
            ORDER BY d.serial_number
        """
        
        available_df = db.run_query(query, tuple(params))
        available_count = len(available_df)
        
        result = {
            'available': available_count >= device_count,
            'requested': device_count,
            'available_count': available_count,
            'shortage': max(0, device_count - available_count),
            'devices': available_df
        }
        
        if available_count < device_count:
            result['message'] = f"⚠️ Only {available_count} devices available. Shortage: {device_count - available_count}"
        else:
            result['message'] = f"✅ {available_count} devices available"
        
        return result
    
    def validate_booking_capacity(self, room_id: int, headcount: int) -> Dict:
        """
        Check if room capacity is sufficient for headcount.
        Returns warning (does not block).
        
        Args:
            room_id: Room to check
            headcount: Total number of people
            
        Returns:
            Dict with validation result
        """
        query = "SELECT capacity, name FROM rooms WHERE id = %s"
        result = db.run_query(query, (room_id,))
        
        if result.empty:
            return {
                'valid': False,
                'message': 'Room not found',
                'capacity': 0,
                'headcount': headcount
            }
        
        capacity = int(result.iloc[0]['capacity'])
        room_name = result.iloc[0]['name']
        
        if headcount > capacity:
            return {
                'valid': True,  # Allow but warn
                'warning': True,
                'message': f'⚠️ Room "{room_name}" capacity ({capacity}) is less than headcount ({headcount}). Consider requesting B2 overflow room.',
                'capacity': capacity,
                'headcount': headcount,
                'overflow': headcount - capacity
            }
        else:
            return {
                'valid': True,
                'warning': False,
                'message': f'✅ Room "{room_name}" capacity sufficient ({capacity} seats for {headcount} people)',
                'capacity': capacity,
                'headcount': headcount
            }
    
    def check_all_availability(
        self,
        room_id: Optional[int],
        start_date: date,
        end_date: date,
        headcount: int = 0,
        devices_needed: int = 0,
        device_type: str = 'any'
    ) -> Dict:
        """
        Comprehensive availability check for booking.
        
        Args:
            room_id: Selected room (optional)
            start_date: Booking start date
            end_date: Booking end date
            headcount: Total attendees
            devices_needed: Number of devices needed
            device_type: 'any', 'laptops', or 'desktops'
            
        Returns:
            Dict with all availability checks
        """
        result = {
            'can_book': True,
            'room_available': True,
            'devices_available': True,
            'capacity_ok': True,
            'messages': [],
            'warnings': []
        }
        
        # Check room availability
        if room_id:
            conflicts = self.check_room_conflicts(room_id, start_date, end_date)
            if not conflicts.empty:
                result['room_available'] = False
                result['can_book'] = False
                result['messages'].append(f"❌ Room has {len(conflicts)} conflicting booking(s)")
            else:
                result['messages'].append("✅ Room is available")
        
        # Check room capacity
        if room_id and headcount > 0:
            capacity_check = self.validate_booking_capacity(room_id, headcount)
            if capacity_check.get('warning'):
                result['warnings'].append(capacity_check['message'])
            result['messages'].append(capacity_check['message'])
        
        # Check device availability
        if devices_needed > 0:
            device_check = self.check_device_availability(
                devices_needed, start_date, end_date, device_type
            )
            if not device_check['available']:
                result['devices_available'] = False
                result['can_book'] = False
            result['messages'].append(device_check['message'])
        
        return result