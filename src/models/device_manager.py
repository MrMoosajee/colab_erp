"""
Device Manager - Core business logic for device assignment and tracking.
NO AI - Pure manual IT Staff workflow with comprehensive logging for future AI training.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import src.db as db


class DeviceManager:
    """
    Manages device inventory, assignments, and movements.
    All decisions are manual (IT Staff) - logged for future AI training.
    """
    
    def __init__(self):
        """Initialize DeviceManager with database connection."""
        pass
    
    def get_available_devices(
        self, 
        category: str, 
        start_date: date, 
        end_date: date,
        exclude_booking_id: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get devices available for a date range.
        
        Args:
            category: Device category ('Laptop', 'Desktop', etc.)
            start_date: Start of booking period
            end_date: End of booking period
            exclude_booking_id: Optional booking ID to exclude (for reallocation)
            
        Returns:
            DataFrame with available devices
        """
        query = """
            SELECT 
                d.id,
                d.serial_number,
                d.name,
                d.status,
                dc.name as category_name,
                d.office_account,
                d.anydesk_id
            FROM devices d
            JOIN device_categories dc ON d.category_id = dc.id
            WHERE dc.name = %s
            AND d.status IN ('available', 'rented')
            AND d.id NOT IN (
                SELECT DISTINCT bda.device_id
                FROM booking_device_assignments bda
                JOIN bookings b ON bda.booking_id = b.id
                WHERE bda.device_id IS NOT NULL
                AND b.id != COALESCE(%s, 0)
                AND b.status NOT IN ('cancelled', 'completed')
                AND (b.booking_period && tstzrange(%s::timestamp, %s::timestamp, '[)'))
            )
            ORDER BY d.serial_number
        """
        
        start_ts = datetime.combine(start_date, datetime.min.time())
        end_ts = datetime.combine(end_date, datetime.min.time())
        
        return db.run_query(query, (category, exclude_booking_id, start_ts, end_ts))
    
    def get_devices_by_booking(self, booking_id: int) -> pd.DataFrame:
        """
        Get all devices assigned to a specific booking.
        
        Args:
            booking_id: The booking ID
            
        Returns:
            DataFrame with assigned devices
        """
        query = """
            SELECT 
                bda.id as assignment_id,
                d.id as device_id,
                d.serial_number,
                d.name,
                dc.name as category_name,
                bda.is_offsite,
                bda.assigned_at,
                u.username as assigned_by
            FROM booking_device_assignments bda
            JOIN devices d ON bda.device_id = d.id
            JOIN device_categories dc ON bda.device_category_id = dc.id
            LEFT JOIN users u ON bda.assigned_by = u.user_id
            WHERE bda.booking_id = %s
            ORDER BY dc.name, d.serial_number
        """
        
        return db.run_query(query, (booking_id,))
    
    def assign_device(
        self, 
        booking_id: int, 
        device_id: int, 
        assigned_by: str,
        is_offsite: bool = False,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Assign a specific device to a booking.
        
        Args:
            booking_id: The booking to assign to
            device_id: The specific device ID
            assigned_by: Username of IT Staff performing assignment
            is_offsite: Whether device is going off-site
            notes: Optional notes
            
        Returns:
            Dict with success status and message
        """
        try:
            # Get category_id for the device
            category_query = "SELECT category_id FROM devices WHERE id = %s"
            category_result = db.run_query(category_query, (device_id,))
            
            if category_result.empty:
                return {'success': False, 'error': 'Device not found'}
            
            category_id = int(category_result.iloc[0]['category_id'])
            
            # Insert assignment
            insert_query = """
                INSERT INTO booking_device_assignments 
                (booking_id, device_id, device_category_id, assigned_by, 
                 is_offsite, notes, assignment_type, quantity)
                VALUES (%s, %s, %s, 
                    (SELECT user_id FROM users WHERE username = %s),
                    %s, %s, 'manual', 1)
                RETURNING id
            """
            
            result = db.run_transaction(
                insert_query, 
                (booking_id, device_id, category_id, assigned_by, is_offsite, notes),
                fetch_one=True
            )
            
            if result:
                return {
                    'success': True, 
                    'assignment_id': result[0],
                    'message': f'Device {device_id} assigned to booking {booking_id}'
                }
            else:
                return {'success': False, 'error': 'Failed to create assignment'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def unassign_device(self, assignment_id: int) -> Dict:
        """
        Remove device assignment.
        
        Args:
            assignment_id: The assignment ID to remove
            
        Returns:
            Dict with success status
        """
        try:
            delete_query = """
                DELETE FROM booking_device_assignments 
                WHERE id = %s
            """
            
            db.run_transaction(delete_query, (assignment_id,))
            
            return {
                'success': True,
                'message': f'Assignment {assignment_id} removed'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_device_conflicts(
        self, 
        device_id: int, 
        start_date: date, 
        end_date: date,
        exclude_booking_id: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Find bookings that conflict with proposed device usage.
        
        Args:
            device_id: The device to check
            start_date: Proposed start date
            end_date: Proposed end date
            exclude_booking_id: Optional booking to exclude
            
        Returns:
            DataFrame with conflicting bookings
        """
        query = """
            SELECT 
                b.id as booking_id,
                b.client_name,
                r.name as room_name,
                lower(b.booking_period)::date as start_date,
                upper(b.booking_period)::date as end_date,
                b.status
            FROM booking_device_assignments bda
            JOIN bookings b ON bda.booking_id = b.id
            JOIN rooms r ON b.room_id = r.id
            WHERE bda.device_id = %s
            AND b.id != COALESCE(%s, 0)
            AND b.status NOT IN ('cancelled', 'completed')
            AND (b.booking_period && tstzrange(%s::timestamp, %s::timestamp, '[)'))
            ORDER BY lower(b.booking_period)
        """
        
        start_ts = datetime.combine(start_date, datetime.min.time())
        end_ts = datetime.combine(end_date, datetime.min.time())
        
        return db.run_query(query, (device_id, exclude_booking_id, start_ts, end_ts))
    
    def can_reallocate_device(
        self,
        device_id: int,
        from_booking_id: int,
        to_booking_id: int
    ) -> Dict:
        """
        Check if device can be reallocated between bookings.
        IT Staff has authority, but we track for audit.
        
        Args:
            device_id: The device to reallocate
            from_booking_id: Current booking
            to_booking_id: Target booking
            
        Returns:
            Dict with can_reallocate status and reason
        """
        # Get booking dates
        booking_query = """
            SELECT 
                id,
                lower(booking_period)::date as start_date,
                upper(booking_period)::date as end_date,
                status
            FROM bookings 
            WHERE id IN (%s, %s)
        """
        
        bookings = db.run_query(booking_query, (from_booking_id, to_booking_id))
        
        if len(bookings) != 2:
            return {
                'can_reallocate': False,
                'reason': 'One or both bookings not found'
            }
        
        from_booking = bookings[bookings['id'] == from_booking_id].iloc[0]
        
        # Check if original booking has started
        today = date.today()
        booking_started = from_booking['start_date'] <= today
        booking_completed = from_booking['end_date'] < today
        
        if booking_completed:
            return {
                'can_reallocate': True,
                'reason': 'Original booking completed',
                'requires_boss_approval': False
            }
        elif booking_started:
            return {
                'can_reallocate': True,
                'reason': 'Booking in progress - recommend checking with client',
                'requires_boss_approval': False,
                'warning': 'Class already started - client coordination recommended'
            }
        else:
            return {
                'can_reallocate': True,
                'reason': 'Booking has not started yet',
                'requires_boss_approval': False
            }
    
    def reallocate_device(
        self,
        device_id: int,
        from_booking_id: int,
        to_booking_id: int,
        performed_by: str,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Move device from one booking to another.
        
        Args:
            device_id: Device to move
            from_booking_id: Source booking
            to_booking_id: Target booking
            performed_by: IT Staff username
            reason: Optional reason for movement
            
        Returns:
            Dict with success status
        """
        try:
            # Remove from original booking
            unassign_query = """
                DELETE FROM booking_device_assignments 
                WHERE device_id = %s AND booking_id = %s
            """
            db.run_transaction(unassign_query, (device_id, from_booking_id))
            
            # Add to new booking
            category_query = "SELECT category_id FROM devices WHERE id = %s"
            category_result = db.run_query(category_query, (device_id,))
            category_id = int(category_result.iloc[0]['category_id'])
            
            insert_query = """
                INSERT INTO booking_device_assignments 
                (booking_id, device_id, device_category_id, assigned_by, 
                 notes, assignment_type, quantity)
                VALUES (%s, %s, %s, 
                    (SELECT user_id FROM users WHERE username = %s),
                    %s, 'manual', 1)
            """
            
            reallocation_note = f"Reallocated from booking {from_booking_id}"
            if reason:
                reallocation_note += f". Reason: {reason}"
            
            db.run_transaction(
                insert_query,
                (to_booking_id, device_id, category_id, performed_by, reallocation_note)
            )
            
            return {
                'success': True,
                'message': f'Device moved from booking {from_booking_id} to {to_booking_id}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_alternative_devices(
        self,
        category: str,
        start_date: date,
        end_date: date,
        exclude_device_id: int
    ) -> pd.DataFrame:
        """
        Get alternative devices when preferred device is unavailable.
        
        Args:
            category: Device category
            start_date: Required start date
            end_date: Required end date
            exclude_device_id: Device to exclude (unavailable one)
            
        Returns:
            DataFrame with alternative devices
        """
        return self.get_available_devices(
            category, start_date, end_date, exclude_booking_id=None
        ).query(f'id != {exclude_device_id}')
    
    def check_stock_levels(
        self,
        category: str,
        future_date: date,
        min_threshold: int = 5
    ) -> Dict:
        """
        Check if stock is running low for future date.
        
        Args:
            category: Device category to check
            future_date: Date to check availability for
            min_threshold: Minimum acceptable stock level
            
        Returns:
            Dict with stock status and warning if low
        """
        # Count total devices in category
        total_query = """
            SELECT COUNT(*) as total
            FROM devices d
            JOIN device_categories dc ON d.category_id = dc.id
            WHERE dc.name = %s
            AND d.status != 'retired'
        """
        total_result = db.run_query(total_query, (category,))
        total_devices = int(total_result.iloc[0]['total'])
        
        # Count available devices for date
        available = self.get_available_devices(
            category, future_date, future_date
        )
        available_count = len(available)
        
        status = {
            'category': category,
            'total_devices': total_devices,
            'available': available_count,
            'date': future_date,
            'is_low': available_count < min_threshold,
            'threshold': min_threshold
        }
        
        if available_count < min_threshold:
            status['warning'] = (
                f"LOW STOCK: Only {available_count} {category}s available "
                f"for {future_date}. Threshold: {min_threshold}"
            )
        
        return status
    
    def create_offsite_rental(
        self,
        assignment_id: int,
        rental_no: str,
        rental_date: date,
        contact_person: str,
        contact_number: str,
        contact_email: Optional[str],
        company: Optional[str],
        address: str,
        return_expected_date: date
    ) -> Dict:
        """
        Create off-site rental record.
        
        Args:
            assignment_id: The booking device assignment ID
            rental_no: Rental document number
            rental_date: Date of rental
            contact_person: Contact name
            contact_number: Contact phone
            contact_email: Contact email
            company: Company name
            address: Delivery address
            return_expected_date: Expected return date
            
        Returns:
            Dict with success status
        """
        try:
            query = """
                INSERT INTO offsite_rentals 
                (booking_device_assignment_id, rental_no, rental_date,
                 contact_person, contact_number, contact_email, company,
                 address, return_expected_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            result = db.run_transaction(
                query,
                (assignment_id, rental_no, rental_date, contact_person,
                 contact_number, contact_email, company, address, return_expected_date),
                fetch_one=True
            )
            
            if result:
                return {
                    'success': True,
                    'offsite_rental_id': result[0],
                    'message': f'Off-site rental {rental_no} created'
                }
            else:
                return {'success': False, 'error': 'Failed to create off-site rental'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
