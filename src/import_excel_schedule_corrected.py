"""
CORRECTED Excel Schedule Import Script
Properly parses all Excel patterns for learners, facilitators, and devices
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
    Parse a booking entry from Excel cell with CORRECT logic.

    Patterns handled:
    - "Client 20" → 20 learners, 1 facilitator, 0 devices
    - "Client 7+1" → 7 learners, 1 facilitator, 0 devices
    - "Client 25 laptops" → 25 learners, 1 facilitator, 25 devices
    - "Client 17 own laptops" → 17 learners, 1 facilitator, 0 devices (CLIENT OWNS)
    - "Client 25 desktops" → 25 learners, 1 facilitator, 25 devices
    - "Client 30 + 18 devices" → 30 learners, 1 facilitator, 18 devices
    - "Client (15 laptops)" → 15 learners, 1 facilitator, 15 devices
    - "Client 14+1 (Feedem) 14 desktops" → 14 learners, 1 facilitator, 14 devices
    """
    if pd.isna(entry) or not str(entry).strip():
        return None

    entry = str(entry).strip()

    # Skip non-booking entries
    skip_patterns = ['OFFICES', 'Storage', 'IT Office', 'IT Store', 'Store room', 
                     'Prayer Room', '4th Floor', 'A302', 'A303', 'Ambition', 'Kitchen',
                     'Server', ' passages', ' walkways']
    if any(pattern in entry for pattern in skip_patterns):
        return None

    # Check for long-term rentals (exact match only for main name)
    for rental_name in LONG_TERM_RENTALS:
        if entry == rental_name or entry.startswith(rental_name + ' ') or entry == rental_name:
            if entry == rental_name:
                return None  # Handle separately

    # Initialize booking data
    booking = {
        'client_name': entry,
        'num_learners': 0,
        'num_facilitators': 1,  # Default: at least 1 facilitator
        'devices_needed': 0,
        'devices_override': 0,
        'coffee_tea_station': False,
        'morning_catering': None,
        'lunch_catering': None,
        'stationery_needed': False,
    }

    has_own_devices = 'own' in entry.lower() and ('laptop' in entry.lower() or 'device' in entry.lower())

    # Pattern 1: "X+Y" format (e.g., "7+1", "20+1", "14+1")
    # Extract this FIRST before other patterns
    plus_match = re.search(r'(\d+)\s*\+\s*(\d+)', entry)
    if plus_match:
        booking['num_learners'] = int(plus_match.group(1))
        booking['num_facilitators'] = int(plus_match.group(2))
        # Remove the +X part from client name for cleanup
        entry_clean = entry[:plus_match.start()] + entry[plus_match.end():]
    else:
        entry_clean = entry

    # Pattern 2: "X + Y devices/laptops" (separate learners and devices)
    # Example: "30 + 18 devices" → 30 learners, 18 devices
    separate_devices = re.search(r'(\d+)\s*\+\s*(\d+)\s*(?:laptops?|devices?)', entry, re.IGNORECASE)
    if separate_devices and not plus_match:
        # This is "X + Y devices" not "X+Y" facilitators
        booking['num_learners'] = int(separate_devices.group(1))
        booking['num_facilitators'] = 1  # Default
        if not has_own_devices:
            booking['devices_needed'] = int(separate_devices.group(2))
        entry_clean = entry[:separate_devices.start()]

    # Pattern 3: Number at end without + (e.g., "Training Force 5", "Datadrive 15")
    # Only if we haven't set learners yet
    if booking['num_learners'] == 0:
        # Look for number followed by optional device words
        number_match = re.search(r'(\d+)\s*(?:laptops?|devices?|desktops?)?$', entry, re.IGNORECASE)
        if number_match:
            booking['num_learners'] = int(number_match.group(1))
            entry_clean = entry[:number_match.start()]

    # Pattern 4: "X laptops/desktops/devices" (devices = learners count)
    # Example: "25 laptops" → 25 learners, 25 devices
    device_count_match = re.search(r'(\d+)\s*(laptops?|desktops?|devices?)', entry, re.IGNORECASE)
    if device_count_match and not has_own_devices:
        device_count = int(device_count_match.group(1))
        # If we haven't set learners from another pattern, use device count as learners
        if booking['num_learners'] == 0:
            booking['num_learners'] = device_count
        # Set devices needed (unless it's "own")
        booking['devices_needed'] = device_count

    # Pattern 5: "X own laptops/devices" → X learners, 0 devices (client owns them)
    if has_own_devices:
        own_match = re.search(r'(\d+)\s*own\s*(?:laptops?|devices?)', entry, re.IGNORECASE)
        if own_match:
            booking['num_learners'] = int(own_match.group(1))
            booking['devices_needed'] = 0  # Client owns, don't count

    # Pattern 6: "(X laptops)" format
    paren_match = re.search(r'\((\d+)\s*(laptops?|desktops?|devices?)\)', entry, re.IGNORECASE)
    if paren_match and not has_own_devices:
        paren_devices = int(paren_match.group(1))
        booking['devices_override'] = paren_devices
        # Don't add to devices_needed since it's in parentheses (historical notation)

    # If no learner count found, use room capacity as default
    if booking['num_learners'] == 0:
        try:
            room = db.run_query("SELECT max_capacity FROM rooms WHERE id = %s", (room_id,))
            if not room.empty:
                booking['num_learners'] = min(20, room.iloc[0]['max_capacity'])
        except:
            booking['num_learners'] = 10  # Fallback

    # Clean up client name
    # Remove numbers, +X patterns, device words, parentheses content
    client_clean = entry
    
    # Remove parentheses and their content
    client_clean = re.sub(r'\s*\([^)]*\)\s*', ' ', client_clean)
    
    # Remove device-related words with numbers
    client_clean = re.sub(r'\d+\s*own\s*(?:laptops?|devices?)', ' ', client_clean, flags=re.IGNORECASE)
    client_clean = re.sub(r'\d+\s*(?:laptops?|desktops?|devices?)', ' ', client_clean, flags=re.IGNORECASE)
    
    # Remove +X patterns
    client_clean = re.sub(r'\s*\+\s*\d+', ' ', client_clean)
    
    # Remove standalone numbers at end
    client_clean = re.sub(r'\s+\d+\s*$', ' ', client_clean)
    
    # Clean up whitespace and punctuation
    client_clean = re.sub(r'\s+', ' ', client_clean).strip()
    client_clean = re.sub(r'[-_]+$', '', client_clean).strip()
    
    booking['client_name'] = client_clean if client_clean else entry

    # Double-check: ensure facilitators is at least 1
    if booking['num_facilitators'] < 1:
        booking['num_facilitators'] = 1

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
        # Check if it's a double booking
        if "Double Booking" in str(e):
            print(f"  Skipped (already exists): {booking_data['client_name']}")
        else:
            print(f"  Error: {e}")
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
                'devices_override': 0,
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
    skipped_bookings = 0

    # Process each month sheet
    for sheet_name in xls.sheet_names:
        if sheet_name in ['May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']:
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
        month_skipped = 0
        
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

                    # Skip non-booking entries
                    if entry in ['OFFICES', 'Storage', 'IT Office', 'IT Store', 
                                'Store room', 'Prayer Room', '4th Floor']:
                        continue

                    # Check for long-term rentals
                    if entry in LONG_TERM_RENTALS:
                        continue

                    # Parse booking entry
                    booking_data = parse_booking_entry(entry, room_id)
                    if booking_data:
                        booking_id = create_booking_in_db(room_id, booking_date, booking_data)
                        if booking_id:
                            month_bookings += 1
                        else:
                            month_skipped += 1

        print(f"  Created: {month_bookings}, Skipped (exists): {month_skipped}")
        total_bookings += month_bookings
        skipped_bookings += month_skipped

    # Create long-term rentals
    print("\nCreating long-term rentals...")
    for client_name, rental_info in LONG_TERM_RENTALS.items():
        count = create_long_term_rental(client_name, rental_info)
        print(f"  {client_name}: {count} bookings")
        total_bookings += count

    print("\n" + "=" * 60)
    print(f"IMPORT COMPLETE: {total_bookings} new bookings")
    print(f"Skipped (already exist): {skipped_bookings}")
    print("=" * 60)

    return total_bookings


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "/home/shuaibadams/Downloads/Colab 2026 Schedule.xlsx"
    import_excel_schedule(excel_path)
