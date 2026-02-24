"""
Booking Service - Handles enhanced booking creation with all new fields.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import src.db as db
from datetime import datetime, date
from typing import Dict, Optional


class BookingService:
    """
    Handles booking creation with enhanced fields.
    """
    
    def __init__(self):
        """Initialize BookingService."""
        pass
    
    def create_enhanced_booking(
        self,
        room_id: int,
        start_date: date,
        end_date: date,
        client_name: str,
        client_contact_person: str,
        client_email: str,
        client_phone: str,
        num_learners: int,
        num_facilitators: int,
        coffee_tea_station: bool = False,
        morning_catering: Optional[str] = None,
        lunch_catering: Optional[str] = None,
        catering_notes: Optional[str] = None,
        stationery_needed: bool = False,
        water_bottles: int = 0,
        devices_needed: int = 0,
        device_type_preference: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict:
        """
        Create a booking with all enhanced fields.
        
        Args:
            room_id: Room ID
            start_date: Booking start date
            end_date: Booking end date
            client_name: Client/Company name
            client_contact_person: Contact person name
            client_email: Contact email
            client_phone: Contact phone
            num_learners: Number of learners
            num_facilitators: Number of facilitators
            coffee_tea_station: Coffee/tea station needed
            morning_catering: 'none', 'pastry', or 'sandwiches'
            lunch_catering: 'none', 'self_catered', or 'in_house'
            catering_notes: Additional catering notes
            stationery_needed: Stationery needed
            water_bottles: Number of water bottles
            devices_needed: Number of devices needed
            device_type_preference: 'any', 'laptops', or 'desktops'
            created_by: Username of creator
            
        Returns:
            Dict with success status and booking ID
        """
        try:
            # Create timestamp range (07:30 - 16:30 daily)
            start_dt = datetime.combine(start_date, datetime.strptime("07:30", "%H:%M").time())
            end_dt = datetime.combine(end_date, datetime.strptime("16:30", "%H:%M").time())
            
            # Insert booking
            query = """
                INSERT INTO bookings (
                    room_id, client_name, booking_period, status,
                    client_contact_person, client_email, client_phone,
                    num_learners, num_facilitators,
                    coffee_tea_station, morning_catering, lunch_catering, catering_notes,
                    stationery_needed, water_bottles,
                    devices_needed, device_type_preference,
                    created_by
                ) VALUES (
                    %s, %s, tstzrange(%s, %s, '[)'), 'pending',
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s
                )
                RETURNING id
            """
            
            result = db.run_transaction(
                query,
                (
                    room_id, client_name, start_dt, end_dt,
                    client_contact_person, client_email, client_phone,
                    num_learners, num_facilitators,
                    coffee_tea_station, morning_catering, lunch_catering, catering_notes,
                    stationery_needed, water_bottles,
                    devices_needed, device_type_preference,
                    created_by
                ),
                fetch_one=True
            )
            
            if result:
                return {
                    'success': True,
                    'booking_id': result[0],
                    'message': f'Booking #{result[0]} created successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to create booking'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
