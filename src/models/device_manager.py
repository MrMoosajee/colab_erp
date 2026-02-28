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
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Manages device inventory, assignments, and movements.
    All decisions are manual (IT Staff) - logged for future AI training.
    """
    
    def __init__(self):
        """Initialize DeviceManager with database connection."""
        logger.info("DeviceManager initialized")
    
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
        logger.debug(f"get_available_devices called: category={category}, start={start_date}, end={end_date}, exclude={exclude_booking_id}")
        
        # Validate inputs
        if not category:
            logger.error("get_available_devices: category is empty or None")
            return pd.DataFrame()
        
        if not start_date or not end_date:
            logger.error(f"get_available_devices: invalid dates - start={start_date}, end={end_date}")
            return pd.DataFrame()
        
        if start_date > end_date:
            logger.error(f"get_available_devices: start_date {start_date} is after end_date {end_date}")
            return pd.DataFrame()
        
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
        
        try:
            start_ts = datetime.combine(start_date, datetime.min.time())
            end_ts = datetime.combine(end_date, datetime.min.time())
            
            logger.debug(f"get_available_devices: executing query with params: ({category}, {exclude_booking_id}, {start_ts}, {end_ts})")
            
            result = db.run_query(query, (category, exclude_booking_id, start_ts, end_ts))
            
            logger.info(f"get_available_devices: found {len(result)} available devices for category={category}")
            return result
            
        except Exception as e:
            logger.error(f"get_available_devices: ERROR - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"get_available_devices: traceback - {traceback.format_exc()}")
            return pd.DataFrame()
    
    def get_devices_by_booking(self, booking_id: int) -> pd.DataFrame:
        """
        Get all devices assigned to a specific booking.
        
        Args:
            booking_id: The booking ID
            
        Returns:
            DataFrame with assigned devices
        """
        logger.debug(f"get_devices_by_booking called: booking_id={booking_id}")
        
        if not booking_id or not isinstance(booking_id, int):
            logger.error(f"get_devices_by_booking: invalid booking_id={booking_id}")
            return pd.DataFrame()
        
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
        
        try:
            result = db.run_query(query, (booking_id,))
            logger.info(f"get_devices_by_booking: found {len(result)} devices for booking {booking_id}")
            return result
        except Exception as e:
            logger.error(f"get_devices_by_booking: ERROR - {type(e).__name__}: {e}")
            return pd.DataFrame()
    
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
        logger.info(f"assign_device called: booking_id={booking_id}, device_id={device_id}, assigned_by={assigned_by}, is_offsite={is_offsite}")
        
        # Validate inputs
        if not booking_id:
            logger.error(f"assign_device: ERROR - booking_id is None or empty")
            return {'success': False, 'error': 'booking_id is required'}
        
        if not device_id:
            logger.error(f"assign_device: ERROR - device_id is None or empty")
            return {'success': False, 'error': 'device_id is required'}
        
        if not assigned_by:
            logger.error(f"assign_device: ERROR - assigned_by is None or empty")
            return {'success': False, 'error': 'assigned_by is required'}
        
        try:
            logger.debug(f"assign_device: Step 1 - Getting category_id for device {device_id}")
            
            # Get category_id for the device
            category_query = "SELECT category_id FROM devices WHERE id = %s"
            category_result = db.run_query(category_query, (device_id,))
            
            if category_result.empty:
                logger.error(f"assign_device: ERROR - Device {device_id} not found in database")
                return {'success': False, 'error': f'Device {device_id} not found'}
            
            category_id = int(category_result.iloc[0]['category_id'])
            logger.debug(f"assign_device: Step 1 complete - category_id={category_id}")
            
            # Delete any pending placeholder records for this booking/category
            logger.debug(f"assign_device: Step 2 - Deleting placeholder records for booking {booking_id}, category {category_id}")
            
            delete_query = """
                DELETE FROM booking_device_assignments 
                WHERE booking_id = %s 
                AND device_category_id = %s
                AND device_id IS NULL
            """
            delete_result = db.run_transaction(delete_query, (booking_id, category_id))
            logger.debug(f"assign_device: Step 2 complete - delete result: {delete_result}")
            
            # Insert actual device assignment
            logger.debug(f"assign_device: Step 3 - Inserting device assignment")
            
            insert_query = """
                INSERT INTO booking_device_assignments 
                (booking_id, device_id, device_category_id, assigned_by, 
                 is_offsite, notes, assignment_type, quantity)
                VALUES (%s, %s, %s, 
                    (SELECT user_id FROM users WHERE username = %s),
                    %s, %s, 'manual', 1)
                RETURNING id
            """
            
            logger.debug(f"assign_device: Step 3 - executing insert with params: ({booking_id}, {device_id}, {category_id}, {assigned_by}, {is_offsite}, {notes})")
            
            result = db.run_transaction(
                insert_query, 
                (booking_id, device_id, category_id, assigned_by, is_offsite, notes),
                fetch_one=True
            )
            
            logger.debug(f"assign_device: Step 3 complete - insert result: {result}")
            
            if result:
                assignment_id = result[0]
                logger.info(f"assign_device: SUCCESS - Device {device_id} assigned to booking {booking_id}, assignment_id={assignment_id}")
                return {
                    'success': True, 
                    'assignment_id': assignment_id,
                    'message': f'Device {device_id} assigned to booking {booking_id}'
                }
            else:
                logger.error(f"assign_device: ERROR - db.run_transaction returned None for insert")
                return {'success': False, 'error': 'Failed to create assignment - database returned no result'}
                
        except Exception as e:
            logger.error(f"assign_device: ERROR - Exception during assignment: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"assign_device: traceback - {traceback.format_exc()}")
            return {'success': False, 'error': f'{type(e).__name__}: {str(e)}'}
    
    def unassign_device(self, assignment_id: int) -> Dict:
        """
        Remove device assignment.
        
        Args:
            assignment_id: The assignment ID to remove
            
        Returns:
            Dict with success status
        """
        logger.info(f"unassign_device called: assignment_id={assignment_id}")
        
        if not assignment_id:
            logger.error("unassign_device: ERROR - assignment_id is None or empty")
            return {'success': False, 'error': 'assignment_id is required'}
        
        try:
            delete_query = """
                DELETE FROM booking_device_assignments 
                WHERE id = %s
            """
            
            result = db.run_transaction(delete_query, (assignment_id,))
            logger.debug(f"unassign_device: delete result: {result}")
            
            if result:
                logger.info(f"unassign_device: SUCCESS - Assignment {assignment_id} removed")
                return {
                    'success': True,
                    'message': f'Assignment {assignment_id} removed'
                }
            else:
                logger.error(f"unassign_device: ERROR - db.run_transaction returned None/False")
                return {'success': False, 'error': 'Failed to remove assignment'}
            
        except Exception as e:
            logger.error(f"unassign_device: ERROR - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"unassign_device: traceback - {traceback.format_exc()}")
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
        logger.debug(f"get_device_conflicts called: device_id={device_id}, start={start_date}, end={end_date}, exclude={exclude_booking_id}")
        
        if not device_id:
            logger.error("get_device_conflicts: ERROR - device_id is None or empty")
            return pd.DataFrame()
        
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
        
        try:
            start_ts = datetime.combine(start_date, datetime.min.time())
            end_ts = datetime.combine(end_date, datetime.min.time())
            
            result = db.run_query(query, (device_id, exclude_booking_id, start_ts, end_ts))
            logger.info(f"get_device_conflicts: found {len(result)} conflicts for device {device_id}")
            return result
        except Exception as e:
            logger.error(f"get_device_conflicts: ERROR - {type(e).__name__}: {e}")
            return pd.DataFrame()
    
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
        logger.debug(f"can_reallocate_device called: device_id={device_id}, from={from_booking_id}, to={to_booking_id}")
        
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
        
        try:
            bookings = db.run_query(booking_query, (from_booking_id, to_booking_id))
            
            if len(bookings) != 2:
                logger.warning(f"can_reallocate_device: only found {len(bookings)} bookings, expected 2")
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
                result = {
                    'can_reallocate': True,
                    'reason': 'Original booking completed',
                    'requires_boss_approval': False
                }
            elif booking_started:
                result = {
                    'can_reallocate': True,
                    'reason': 'Booking in progress - recommend checking with client',
                    'requires_boss_approval': False,
                    'warning': 'Class already started - client coordination recommended'
                }
            else:
                result = {
                    'can_reallocate': True,
                    'reason': 'Booking has not started yet',
                    'requires_boss_approval': False
                }
            
            logger.info(f"can_reallocate_device: result={result}")
            return result
            
        except Exception as e:
            logger.error(f"can_reallocate_device: ERROR - {type(e).__name__}: {e}")
            return {
                'can_reallocate': False,
                'reason': f'Error checking reallocation: {str(e)}'
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
        logger.info(f"reallocate_device called: device_id={device_id}, from={from_booking_id}, to={to_booking_id}, by={performed_by}")
        
        if not device_id:
            return {'success': False, 'error': 'device_id is required'}
        if not from_booking_id:
            return {'success': False, 'error': 'from_booking_id is required'}
        if not to_booking_id:
            return {'success': False, 'error': 'to_booking_id is required'}
        if not performed_by:
            return {'success': False, 'error': 'performed_by is required'}
        
        try:
            # Remove from original booking
            logger.debug(f"reallocate_device: Step 1 - Removing device {device_id} from booking {from_booking_id}")
            
            unassign_query = """
                DELETE FROM booking_device_assignments 
                WHERE device_id = %s AND booking_id = %s
            """
            unassign_result = db.run_transaction(unassign_query, (device_id, from_booking_id))
            logger.debug(f"reallocate_device: Step 1 complete - unassign result: {unassign_result}")
            
            # Add to new booking
            logger.debug(f"reallocate_device: Step 2 - Getting category_id for device {device_id}")
            
            category_query = "SELECT category_id FROM devices WHERE id = %s"
            category_result = db.run_query(category_query, (device_id,))
            
            if category_result.empty:
                logger.error(f"reallocate_device: ERROR - Device {device_id} not found")
                return {'success': False, 'error': f'Device {device_id} not found'}
            
            category_id = int(category_result.iloc[0]['category_id'])
            logger.debug(f"reallocate_device: Step 2 complete - category_id={category_id}")
            
            # Insert into new booking
            logger.debug(f"reallocate_device: Step 3 - Inserting into booking {to_booking_id}")
            
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
            
            insert_result = db.run_transaction(
                insert_query,
                (to_booking_id, device_id, category_id, performed_by, reallocation_note)
            )
            
            logger.debug(f"reallocate_device: Step 3 complete - insert result: {insert_result}")
            
            if insert_result:
                logger.info(f"reallocate_device: SUCCESS - Device moved from {from_booking_id} to {to_booking_id}")
                return {
                    'success': True,
                    'message': f'Device moved from booking {from_booking_id} to {to_booking_id}'
                }
            else:
                logger.error(f"reallocate_device: ERROR - Insert returned None/False")
                return {'success': False, 'error': 'Failed to create new assignment'}
            
        except Exception as e:
            logger.error(f"reallocate_device: ERROR - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"reallocate_device: traceback - {traceback.format_exc()}")
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
        logger.debug(f"get_alternative_devices called: category={category}, exclude={exclude_device_id}")
        
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
        logger.debug(f"check_stock_levels called: category={category}, date={future_date}, threshold={min_threshold}")
        
        # Count total devices in category
        total_query = """
            SELECT COUNT(*) as total
            FROM devices d
            JOIN device_categories dc ON d.category_id = dc.id
            WHERE dc.name = %s
            AND d.status != 'retired'
        """
        
        try:
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
            
            logger.info(f"check_stock_levels: category={category}, total={total_devices}, available={available_count}, is_low={status['is_low']}")
            return status
            
        except Exception as e:
            logger.error(f"check_stock_levels: ERROR - {type(e).__name__}: {e}")
            return {
                'category': category,
                'total_devices': 0,
                'available': 0,
                'date': future_date,
                'is_low': True,
                'threshold': min_threshold,
                'warning': f'Error checking stock: {str(e)}'
            }
    
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
        logger.info(f"create_offsite_rental called: assignment_id={assignment_id}, rental_no={rental_no}")
        
        # Validate required inputs
        if not assignment_id:
            return {'success': False, 'error': 'assignment_id is required'}
        if not rental_no:
            return {'success': False, 'error': 'rental_no is required'}
        if not contact_person:
            return {'success': False, 'error': 'contact_person is required'}
        if not contact_number:
            return {'success': False, 'error': 'contact_number is required'}
        if not address:
            return {'success': False, 'error': 'address is required'}
        if not return_expected_date:
            return {'success': False, 'error': 'return_expected_date is required'}
        
        try:
            query = """
                INSERT INTO offsite_rentals 
                (booking_device_assignment_id, rental_no, rental_date,
                 contact_person, contact_number, contact_email, company,
                 address, return_expected_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            logger.debug(f"create_offsite_rental: executing insert with assignment_id={assignment_id}")
            
            result = db.run_transaction(
                query,
                (assignment_id, rental_no, rental_date, contact_person,
                 contact_number, contact_email, company, address, return_expected_date),
                fetch_one=True
            )
            
            if result:
                rental_id = result[0]
                logger.info(f"create_offsite_rental: SUCCESS - offsite_rental_id={rental_id}")
                return {
                    'success': True,
                    'offsite_rental_id': rental_id,
                    'message': f'Off-site rental {rental_no} created'
                }
            else:
                logger.error(f"create_offsite_rental: ERROR - db.run_transaction returned None")
                return {'success': False, 'error': 'Failed to create off-site rental - no result from database'}
                
        except Exception as e:
            logger.error(f"create_offsite_rental: ERROR - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"create_offsite_rental: traceback - {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # INVENTORY DASHBOARD METHODS
    # =========================================================================

    def get_inventory_summary(self) -> Dict:
        """
        Get overall inventory summary statistics.
        
        Returns:
            Dict with total, available, assigned, offsite counts
        """
        logger.debug("get_inventory_summary called")
        
        try:
            query = """
                SELECT 
                    COUNT(*) as total_devices,
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as available,
                    COUNT(CASE WHEN status = 'assigned' THEN 1 END) as assigned,
                    COUNT(CASE WHEN status = 'offsite' THEN 1 END) as offsite
                FROM devices
                WHERE status != 'retired'
            """
            
            result = db.run_query(query)
            
            if result.empty:
                logger.warning("get_inventory_summary: query returned empty result")
                return {
                    'total_devices': 0,
                    'available': 0,
                    'assigned': 0,
                    'offsite': 0,
                    'available_percent': 0
                }
            
            total = int(result.iloc[0]['total_devices'])
            available = int(result.iloc[0]['available'])
            
            summary = {
                'total_devices': total,
                'available': available,
                'assigned': int(result.iloc[0]['assigned']),
                'offsite': int(result.iloc[0]['offsite']),
                'available_percent': (available / total * 100) if total > 0 else 0
            }
            
            logger.info(f"get_inventory_summary: total={total}, available={available}, assigned={summary['assigned']}, offsite={summary['offsite']}")
            return summary
            
        except Exception as e:
            logger.error(f"get_inventory_summary: ERROR - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"get_inventory_summary: traceback - {traceback.format_exc()}")
            return {
                'total_devices': 0,
                'available': 0,
                'assigned': 0,
                'offsite': 0,
                'available_percent': 0
            }

    def get_device_categories(self) -> pd.DataFrame:
        """
        Get all device categories.
        
        Returns:
            DataFrame with category id and name
        """
        logger.debug("get_device_categories called")
        
        query = "SELECT id, name FROM device_categories ORDER BY name"
        
        try:
            result = db.run_query(query)
            logger.info(f"get_device_categories: found {len(result)} categories")
            return result
        except Exception as e:
            logger.error(f"get_device_categories: ERROR - {type(e).__name__}: {e}")
            return pd.DataFrame()

    def get_category_stats(self, category_id: int) -> Dict:
        """
        Get statistics for a specific device category.
        
        Args:
            category_id: The category ID
            
        Returns:
            Dict with total, available, and low_stock flag
        """
        logger.debug(f"get_category_stats called: category_id={category_id}")
        
        if not category_id:
            logger.error("get_category_stats: ERROR - category_id is None or empty")
            return {'total': 0, 'available': 0, 'low_stock': True}
        
        try:
            query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as available
                FROM devices
                WHERE category_id = %s
                AND status != 'retired'
            """
            
            result = db.run_query(query, (category_id,))
            
            if result.empty:
                logger.warning(f"get_category_stats: query returned empty for category_id={category_id}")
                return {'total': 0, 'available': 0, 'low_stock': True}
            
            total = int(result.iloc[0]['total'])
            available = int(result.iloc[0]['available'])
            
            stats = {
                'total': total,
                'available': available,
                'low_stock': available < 3  # Threshold of 3 devices
            }
            
            logger.info(f"get_category_stats: category_id={category_id}, total={total}, available={available}, low_stock={stats['low_stock']}")
            return stats
            
        except Exception as e:
            logger.error(f"get_category_stats: ERROR - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"get_category_stats: traceback - {traceback.format_exc()}")
            return {'total': 0, 'available': 0, 'low_stock': True}

    def get_devices_detailed(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        serial_search: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get detailed device list with optional filters.
        
        Args:
            status: Filter by status (optional)
            category: Filter by category name (optional)
            serial_search: Search by serial number (optional)
            
        Returns:
            DataFrame with device details
        """
        logger.debug(f"get_devices_detailed called: status={status}, category={category}, serial_search={serial_search}")
        
        query = """
            SELECT 
                d.serial_number,
                d.name,
                dc.name as category,
                d.status,
                d.office_account,
                d.anydesk_id,
                CASE 
                    WHEN b.id IS NOT NULL THEN b.client_name
                    ELSE NULL
                END as current_assignment,
                CASE 
                    WHEN b.id IS NOT NULL THEN upper(b.booking_period)::date
                    ELSE NULL
                END as assigned_until
            FROM devices d
            JOIN device_categories dc ON d.category_id = dc.id
            LEFT JOIN booking_device_assignments bda ON d.id = bda.device_id
                AND bda.id = (
                    SELECT MAX(id) FROM booking_device_assignments 
                    WHERE device_id = d.id
                )
            LEFT JOIN bookings b ON bda.booking_id = b.id
                AND b.status NOT IN ('cancelled', 'completed')
                AND upper(b.booking_period) >= CURRENT_DATE
            WHERE d.status != 'retired'
        """
        
        params = []
        
        if status and status != 'All':
            query += " AND d.status = %s"
            params.append(status.lower())
        
        if category and category != 'All':
            query += " AND dc.name = %s"
            params.append(category)
        
        if serial_search:
            query += " AND d.serial_number ILIKE %s"
            params.append(f"%{serial_search}%")
        
        query += " ORDER BY dc.name, d.serial_number"
        
        try:
            result = db.run_query(query, tuple(params) if params else None)
            logger.info(f"get_devices_detailed: found {len(result)} devices")
            return result
        except Exception as e:
            logger.error(f"get_devices_detailed: ERROR - {type(e).__name__}: {e}")
            return pd.DataFrame()

    def get_recent_activity(self, limit: int = 20) -> pd.DataFrame:
        """
        Get recent inventory activity.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            DataFrame with recent activity
        """
        logger.debug(f"get_recent_activity called: limit={limit}")
        
        query = """
            SELECT 
                bda.assigned_at as timestamp,
                CASE 
                    WHEN bda.device_id IS NULL THEN 'Device Requested'
                    ELSE 'Device Assigned'
                END as action,
                COALESCE(d.serial_number, 'Pending') as device_serial,
                u.username as user,
                COALESCE(b.client_name, 'N/A') as details
            FROM booking_device_assignments bda
            LEFT JOIN devices d ON bda.device_id = d.id
            LEFT JOIN users u ON bda.assigned_by = u.user_id
            LEFT JOIN bookings b ON bda.booking_id = b.id
            ORDER BY bda.assigned_at DESC
            LIMIT %s
        """
        
        try:
            result = db.run_query(query, (limit,))
            logger.info(f"get_recent_activity: found {len(result)} activity records")
            return result
        except Exception as e:
            logger.error(f"get_recent_activity: ERROR - {type(e).__name__}: {e}")
            return pd.DataFrame()

    def export_inventory_csv(self) -> str:
        """
        Export full inventory to CSV format.
        
        Returns:
            CSV string of inventory data
        """
        logger.debug("export_inventory_csv called")
        
        query = """
            SELECT 
                d.serial_number,
                d.name,
                dc.name as category,
                d.status,
                d.office_account,
                d.anydesk_id,
                d.purchase_date,
                d.notes
            FROM devices d
            JOIN device_categories dc ON d.category_id = dc.id
            WHERE d.status != 'retired'
            ORDER BY dc.name, d.serial_number
        """
        
        try:
            df = db.run_query(query)
            csv_data = df.to_csv(index=False)
            logger.info(f"export_inventory_csv: exported {len(df)} devices")
            return csv_data
        except Exception as e:
            logger.error(f"export_inventory_csv: ERROR - {type(e).__name__}: {e}")
            raise
