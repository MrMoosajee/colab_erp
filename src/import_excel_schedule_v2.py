"""
Excel Schedule Import Script
Imports bookings from 'Colab 2026 Schedule.xlsx' into the database
"""

import pandas as pd
import re
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import src.db as db

# Room mapping: Excel column names -> Database room IDs
ROOM_MAPPING = {
    'Excellence': 1,
    'Inspiration': 2,
    'Honesty': 3,
    'Gratitude': 4,
    'Ambition': 5,
    'Perserverence': 6,
    'Courage': 7,
    'Possibilities': 8,
    'Motivation': 9,
    'A302': 10,
    'A303': 11,
    'Success 10': 12,
    'Respect 10': 13,
    'Innovation (12)': 14,
    'Dedication': 15,
    'Integrity (15)': 16,
    'Empower': 17,
    'Focus': 18,
    'Growth': 19,
    'Wisdom (8)': 20,
    'Vision': 21,
    'Potential': 22,
    'Synergy': 23,
    'Ambition+Perseverence': 24,
}

# Long-term rental clients (daily bookings till year end)
LONG_TERM_RENTALS = {
    'Siyaya': {'room_id': 12, 'start_date': date(2026, 1, 1), 'end_date': date(2026, 12, 31)},
    'Melissa': {'room_id': 20, 'start_date': date(2026, 1, 1), 'end_date': date(2026, 12, 31)},
}


def parse_booking_entry(entry, room_id):
    """
    Parse a booking entry from Excel cell.
    
    Patterns:
    - "Client 25+1" -> learners=25, facilitators=1
    - "Client 25 + 18 laptops" -> learners=25, devices=18
    - "WNS - 34" -> client="WNS", learners=34
    - "Client 20" -> learners=20, facilitators=1
    - "Siyaya" -> Long-term rental
    """
    if pd.isna(entry) or not str(entry).strip():
        return None
    
    entry = str(entry).strip()
    
    # Check for long-term rentals
    if entry in LONG_TERM_RENTALS:
        return None  # Handle separately
    
    booking = {
        'client_name': entry,
        'num_learners': 0,
        'num_facilitators': 1,  # Always at least 1
        'devices_needed': 0,
        'devices_override': 0,  # For historical data from Excel
        'coffee_tea_station': False,
        'morning_catering': None,
        'lunch_catering': None,
        'stationery_needed': False,
    }
    
    # Pattern: "25+1" or "20+1" (learners + facilitators)
    plus_match = re.search(r'(\d+)\+(\d+)', entry)
    if plus_match:
        booking['num_learners'] = int(plus_match.group(1))
        booking['num_facilitators'] = int(plus_match.group(2))
        # Remove the count from client name
        booking['client_name'] = entry[:plus_match.start()].strip()
    
    # Pattern: "25 + 18 laptops" or "20 + 5 devices"
    device_match = re.search(r'(\d+)\s*+\s*(\d+)\s*(?:laptops?|devices?)', entry, re.IGNORECASE)
    if device_match:
        booking['num_learners'] = int(device_match.group(1))
        booking['devices_needed'] = int(device_match.group(2))
        booking['client_name'] = entry[:device_match.start()].strip()
    
    # Pattern: "Client Name (15 laptops)" or "Client (20 devices)"
    paren_device_match = re.search(r'\((\d+)\s*(laptops?|devices?|pcs?|desktops?)\)', entry, re.IGNORECASE)
    if paren_device_match:
        device_count = int(paren_device_match.group(1))
        booking['devices_override'] = device_count  # Use override for Excel imports
        # Remove the device text from client name
        booking['client_name'] = re.sub(
            r'\s*\(\d+\s*(laptops?|devices?|pcs?|desktops?)\)\s*',
            ' ',
            booking['client_name'],
            flags=re.IGNORECASE
        ).strip()
    
    # Pattern: "WNS - 34" or similar
    dash_number_match = re.search(r'\s*-\s*(\d+)$', entry)
    if dash_number_match and booking['num_learners'] == 0:
        booking['num_learners'] = int(dash_number_match.group(1))
        booking['client_name'] = entry[:dash_number_match.start()].strip()
    
    # Pattern: Just a number at the end (e.g., "Client 20")
    if booking['num_learners'] == 0:
        number_match = re.search(r'(\d+)$', entry)
        if number_match:
            booking['num_learners'] = int(number_match.group(1))
            booking['client_name'] = entry[:number_match.start()].strip()
    
    # If no number found, use room capacity as default
    if booking['num_learners'] == 0:
        # Get room capacity
        room = db.run_query("SELECT max_capacity FROM rooms WHERE id = %s", (room_id,))
        if not room.empty:
            booking['num_learners'] = min(20, room.iloc[0]['max_capacity'])  # Default to 20 or room capacity
    
    # Clean up client name
    booking['client_name'] = booking['client_name'].strip()
    
    return booking


def create_booking_in_db(room_id, booking_date, booking_data):
    """Create a booking in the database."""
    try:
        # Calculate headcount
        headcount = booking_data['num_learners'] + booking_data['num_facilitators']
        
        # Create time range (full day booking 8:00 - 17:00)
        start_dt = datetime.combine(booking_date, datetime.min.time().replace(hour=8))
        end_dt = datetime.combine(booking_date, datetime.min.time().replace(hour=17))
        
        # Normalize to UTC
        start_utc, end_utc = db.normalize_dates(booking_date, start_dt.time(), end_dt.time())
        
        # Use run_transaction to create booking
        sql = """
            INSERT INTO bookings (
                room_id, booking_period, client_name, headcount,
                num_learners, num_facilitators, devices_needed, devices_override,
                coffee_tea_station, morning_catering, lunch_catering,
                stationery_needed, status, tenant_id, end_date
            ) VALUES (
                %s, tstzrange(%s, %s, '[)'), %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id;
        """
        
        result = db.run_transaction(sql, (
            room_id,
            start_utc, end_utc,
            booking_data['client_name'],
            headcount,
            booking_data['num_learners'],
            booking_data['num_facilitators'],
            booking_data['devices_needed'],
            booking_data.get('devices_override', 0),
            booking_data['coffee_tea_station'],
            booking_data['morning_catering'],
            booking_data['lunch_catering'],
            booking_data['stationery_needed'],
            'Approved',  # Auto-approve Excel imports
            'TECH',
            booking_date
        ), fetch_one=True)
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error creating booking: {e}")
        return None


def create_long_term_rental(client_name, rental_info):
    """Create daily bookings for long-term rentals."""
    room_id = rental_info['room_id']
    start_date = rental_info['start_date']
    end_date = rental_info['end_date']
    
    bookings_created = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            booking_data = {
                'client_name': client_name,
                'num_learners': 1,
                'num_facilitators': 1,
                'devices_needed': 0,
                'coffee_tea_station': False,
                'morning_catering': None,
                'lunch_catering': None,
                'stationery_needed': False,
            }
            
            booking_id = create_booking_in_db(room_id, current_date, booking_data)
            if booking_id:
                bookings_created += 1
        
        current_date += timedelta(days=1)
    
    return bookings_created


def import_excel_schedule(excel_path):
    """Main function to import Excel schedule."""
    print(f"Importing schedule from: {excel_path}")
    print("=" * 60)
    
    # Load Excel file
    xls = pd.ExcelFile(excel_path)
    
    total_bookings = 0
    
    # Process each month sheet
    for sheet_name in xls.sheet_names:
        if sheet_name in ['May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']:
            # These months are mostly empty in the Excel
            continue
        
        print(f"\nProcessing {sheet_name}...")
        
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        # Find the header row (row with room names)
        header_row = None
        for idx, row in df.iterrows():
            if 'Date' in str(row.values) or 'Day' in str(row.values):
                header_row = idx
                break
        
        if header_row is None:
            print(f"  Could not find header row in {sheet_name}")
            continue
        
        # Set column names from header row
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)
        
        # Process each row
        month_bookings = 0
        for idx, row in df.iterrows():
            # Get date from row
            if 'Date' not in row or pd.isna(row['Date']):
                continue
            
            try:
                if isinstance(row['Date'], datetime):
                    booking_date = row['Date'].date()
                elif isinstance(row['Date'], date):
                    booking_date = row['Date']
                else:
                    # Try to parse string
                    booking_date = pd.to_datetime(row['Date']).date()
            except:
                continue
            
            # Skip if not 2025 or 2026
            if booking_date.year not in [2025, 2026]:
                continue
            
            # Process each room column
            for excel_room, room_id in ROOM_MAPPING.items():
                if excel_room in row and not pd.isna(row[excel_room]):
                    entry = str(row[excel_room]).strip()
                    
                    # Skip certain entries
                    if entry in ['OFFICES', 'Storage', 'IT Office', 'IT Store', 'Store room', 'Prayer Room']:
                        continue
                    
                    # Check for long-term rentals
                    if entry in LONG_TERM_RENTALS:
                        continue  # Handle separately
                    
                    # Parse booking entry
                    booking_data = parse_booking_entry(entry, room_id)
                    if booking_data:
                        booking_id = create_booking_in_db(room_id, booking_date, booking_data)
                        if booking_id:
                            month_bookings += 1
        
        print(f"  Created {month_bookings} bookings")
        total_bookings += month_bookings
    
    # Create long-term rentals
    print("\nCreating long-term rentals...")
    for client_name, rental_info in LONG_TERM_RENTALS.items():
        count = create_long_term_rental(client_name, rental_info)
        print(f"  {client_name}: {count} daily bookings created")
        total_bookings += count
    
    print("\n" + "=" * 60)
    print(f"IMPORT COMPLETE: {total_bookings} total bookings created")
    print("=" * 60)
    
    return total_bookings


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "/home/shuaibadams/Downloads/Colab 2026 Schedule.xlsx"
    import_excel_schedule(excel_path)
