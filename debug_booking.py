#!/usr/bin/env python3
"""
Debug script to identify the exact issue with booking creation
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import src.db as db
from datetime import date, datetime

def debug_booking_query():
    """Debug the booking query step by step"""
    conn = None
    try:
        conn = db.get_db_pool().getconn()
        with conn.cursor() as cur:
            # Test data
            start_dt = datetime.combine(date.today(), datetime.min.time()).replace(hour=7, minute=30)
            end_dt = datetime.combine(date.today(), datetime.min.time()).replace(hour=16, minute=30)
            
            # Build query step by step
            query_parts = [
                "INSERT INTO bookings (",
                "room_id, booking_period, client_name, status,",
                "headcount, tenant_id, end_date,",
                "num_learners, num_facilitators,",
                "coffee_tea_station, morning_catering, lunch_catering, catering_notes,",
                "stationery_needed, water_bottles,",
                "devices_needed, device_type_preference,",
                "client_contact_person, client_email, client_phone,",
                "room_boss_notes, created_at",
                ") VALUES (",
                "%s, tstzrange(%s, %s, '[)'), %s, %s,",
                "%s, %s, %s,",
                "%s, %s,",
                "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()",
                ") RETURNING id"
            ]
            
            query = '\n'.join(query_parts)
            print("Query:")
            print(query)
            print()
            
            # Parameters
            params = (
                None, start_dt, end_dt, 'Test Client', 'Pending',
                11, 'TECH', date.today(),
                10, 1,
                True, 'pastry', 'self_catered', 'Test notes',
                True, 5,
                2, 'laptops',
                'Test Contact', 'test@example.com', '123-456-7890',
                'Test booking'
            )
            
            print(f"Parameters count: {len(params)}")
            print(f"Placeholders count: {query.count('%s')}")
            print(f"Parameters: {params}")
            print()
            
            # Execute
            cur.execute(query, params)
            result = cur.fetchone()
            print(f"Success! Booking ID: {result[0]}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            db.get_db_pool().putconn(conn)

if __name__ == "__main__":
    debug_booking_query()