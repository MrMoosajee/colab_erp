"""
FINAL CORRECTED Excel Schedule Import Script
Properly parses all Excel patterns including ranges and complex formats
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
    - "Client 25-30 - 15 laptops" → 25 learners, 1 facilitator, 15 devices
    - "Client 30 + 18 devices" → 30 learners, 1 facilitator, 18 devices
    """
    if pd.isna(entry) or not str(entry).strip():
        return None

    entry = str(entry).strip()

    # Skip non-booking entries
    skip_patterns = ['OFFICES', 'Storage', 'IT Office', 'IT Store', 'Store room', 
                     'Prayer Room', '4th Floor', 'A302', 'A303', 'Ambition']
    if any(pattern in entry for pattern in skip_patterns):
        return None

    # Check for long-term rentals (exact match only)
    for rental_name in LONG_TERM_RENTALS:
        if entry == rental_name:
            return None

    booking = {
        'client_name': entry,
        'num_learners': 0,
        'num_facilitators': 1,
        'devices_needed': 0,
        'devices_override': 0,
        'coffee_tea_station': False,
        'morning_catering': None,
        'lunch_catering': None,
        'stationery_needed': False,
    }

    has_own_devices = 'own' in entry.lower() and ('laptop' in entry.lower() or 'device' in entry.lower())

    # Pattern 1: "X + Y devices/laptops" (learners + separate devices)
    separate_devices = re.search(r'(\d+)\s*\+\s*(\d+)\s*(?:laptops?|devices?)', entry, re.IGNORECASE)
    if separate_devices:
        booking['num_learners'] = int(separate_devices.group(1))
        booking['num_facilitators'] = 1
        if not has_own_devices:
            booking['devices_needed'] = int(separate_devices.group(2))
    else:
        # Pattern 2: "X+Y" facilitator format (e.g., "7+1", "20+1")
        plus_match = re.search(r'(\d+)\s*\+\s*(\d+)', entry)
        if plus_match:
            booking['num_learners'] = int(plus_match.group(1))
            booking['num_facilitators'] = int(plus_match.group(2))

    # Pattern 3: Range format "X-Y" (e.g., "25-30", "10-15")
    # Use the first number as learners
    range_match = re.search(r'(\d+)-(\d+)', entry)
    if range_match and booking['num_learners'] == 0:
        booking['num_learners'] = int(range_match.group(1))

    # Pattern 4: Number followed by devices/laptops/desktops
    device_match = re.search(r'(\d+)\s*(?:laptops?|desktops?|devices?)', entry, re.IGNORECASE)
    if device_match and not has_own_devices:
        device_count = int(device_match.group(1))
        # Only set devices if different from learners (avoid double counting)
        if device_count != booking['num_learners'] or booking['num_learners'] == 0:
            booking['devices_needed'] = device_count
        # If learners not set, use device count
        if booking['num_learners'] == 0:
            booking['num_learners'] = device_count

    # Pattern 5: Simple number at end (only if nothing else matched)
    if booking['num_learners'] == 0:
        number_match = re.search(r'(\d+)$', entry)
        if number_match:
            booking['num_learners'] = int(number_match.group(1))

    # Pattern 6: "X own laptops/devices" → X learners, 0 devices
    if has_own_devices:
        own_match = re.search(r'(\d+)\s*own\s*(?:laptops?|devices?)', entry, re.IGNORECASE)
        if own_match:
            booking['num_learners'] = int(own_match.group(1))
            booking['devices_needed'] = 0

    # Default if still no learner count
    if booking['num_learners'] == 0:
        try:
            room = db.run_query("SELECT max_capacity FROM rooms WHERE id = %s", (room_id,))
            if not room.empty:
                booking['num_learners'] = min(20, room.iloc[0]['max_capacity'])
        except:
            booking['num_learners'] = 10

    # Clean up client name
    client_clean = entry
    client_clean = re.sub(r'\s*\([^)]*\)\s*', ' ', client_clean)
    client_clean = re.sub(r'\d+\s*-\s*\d+', ' ', client_clean)  # Remove ranges like "25-30"
    client_clean = re.sub(r'\d+\s*own\s*(?:laptops?|devices?)', ' ', client_clean, flags=re.IGNORECASE)
    client_clean = re.sub(r'\d+\s*(?:laptops?|desktops?|devices?)', ' ', client_clean, flags=re.IGNORECASE)
    client_clean = re.sub(r'\s*\+\s*\d+', ' ', client_clean)
    client_clean = re.sub(r'\s+\d+\s*$', ' ', client_clean)
    client_clean = re.sub(r'\s+', ' ', client_clean).strip()
    client_clean = re.sub(r'[-_]+$', '', client_clean).strip()
    
    booking['client_name'] = client_clean if client_clean else entry

    if booking['num_facilitators'] < 1:
        booking['num_facilitators'] = 1

    return booking


def create_booking_in_db(room_id, booking_date, booking_data):
    """Create a booking in the database."""
    try:
        headcount = booking_data['num_learners'] + booking_data['num_facilitators']
        start_dt = datetime.combine(booking_date, datetime.min.time().replace(hour=8))
        end_dt = datetime.combine(booking_date, datetime.min.time().replace(hour=17))
        start_utc, end_utc = db.normalize_dates(booking_date, start_dt.time(), end_dt.time())

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
            room_id, start_utc, end_utc,
            booking_data['client_name'], headcount,
            booking_data['num_learners'], booking_data['num_facilitators'],
            booking_data['devices_needed'], booking_data.get('devices_override', 0),
            booking_data['coffee_tea_station'], booking_data['morning_catering'],
            booking_data['lunch_catering'], booking_data['stationery_needed'],
            'Approved', 'TECH', booking_date
        ), fetch_one=True)

        return result[0] if result else None
    except Exception as e:
        if "Double Booking" in str(e):
            return None
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
        if current_date.weekday() < 5:
            booking_data = {
                'client_name': client_name, 'num_learners': 1, 'num_facilitators': 1,
                'devices_needed': 0, 'devices_override': 0, 'coffee_tea_station': False,
                'morning_catering': None, 'lunch_catering': None, 'stationery_needed': False,
            }
            if create_booking_in_db(room_id, current_date, booking_data):
                bookings_created += 1
        current_date += timedelta(days=1)

    return bookings_created


def import_excel_schedule(excel_path):
    """Main function to import Excel schedule."""
    print(f"Importing: {excel_path}")
    print("=" * 60)

    xls = pd.ExcelFile(excel_path)
    total_bookings = 0
    skipped = 0

    for sheet_name in xls.sheet_names:
        if sheet_name in ['May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']:
            continue

        print(f"\n{sheet_name}...", end=' ')
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        header_row = None
        for idx, row in df.iterrows():
            if 'Date' in str(row.values) or 'Day' in str(row.values):
                header_row = idx
                break

        if header_row is None:
            print("No header")
            continue

        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)

        month_new = 0
        month_skip = 0

        for idx, row in df.iterrows():
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

            if booking_date.year not in [2025, 2026]:
                continue

            for excel_room, room_id in ROOM_MAPPING.items():
                if excel_room in row and not pd.isna(row[excel_room]):
                    entry = str(row[excel_room]).strip()
                    
                    if entry in ['OFFICES', 'Storage', 'IT Office', 'Store room', 'Prayer Room']:
                        continue
                    if entry in LONG_TERM_RENTALS:
                        continue

                    booking_data = parse_booking_entry(entry, room_id)
                    if booking_data:
                        booking_id = create_booking_in_db(room_id, booking_date, booking_data)
                        if booking_id:
                            month_new += 1
                        else:
                            month_skip += 1

        print(f"New: {month_new}, Skip: {month_skip}")
        total_bookings += month_new
        skipped += month_skip

    print("\nLong-term rentals...")
    for client_name, rental_info in LONG_TERM_RENTALS.items():
        count = create_long_term_rental(client_name, rental_info)
        print(f"  {client_name}: {count}")
        total_bookings += count

    print("=" * 60)
    print(f"COMPLETE: {total_bookings} new, {skipped} skipped")
    return total_bookings


if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_excel_schedule(sys.argv[1])
    else:
        import_excel_schedule("/home/shuaibadams/Downloads/Colab 2026 Schedule.xlsx")
