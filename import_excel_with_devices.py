"""
Excel Import with Device Parsing - For Historical Bookings
Parses device counts from booking text and stores in devices_override field
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
import re
from datetime import datetime, timedelta
import src.db as db

def parse_devices_from_text(text):
    """Extract device count from booking text like '5 laptops', '18 Laptops', '30 + 18 Devices'"""
    if pd.isna(text) or not isinstance(text, str):
        return None, None
    
    text = str(text).strip()
    if not text or text.lower() in ['nan', 'none', '']:
        return None, None
    
    # Pattern: number + laptops/devices (case insensitive)
    patterns = [
        r'(\d+)\s*laptops?',  # 5 laptops, 18 Laptops
        r'(\d+)\s*devices?',  # 18 Devices
        r'(\d+)\s*pcs?',      # 5 PCs
        r'(\d+)\s*computers?', # 10 computers
    ]
    
    devices_found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        devices_found.extend([int(m) for m in matches])
    
    if devices_found:
        total_devices = sum(devices_found)
        device_note = f"Extracted from: {text}"
        return total_devices, device_note
    
    return None, None

def import_bookings_with_devices():
    """Import Excel bookings with device parsing"""
    
    # Read Excel
    filepath = "/home/shuaibadams/Downloads/Colab 2026 Schedule.xlsx"
    print(f"Reading: {filepath}")
    df = pd.read_excel(filepath)
    
    # Room mapping
    room_mapping = {
        'Upstairs': 'Excellence',
        'Right side of entrance': 'Inspiration',
        'Unnamed: 4': 'Honesty',
        'Unnamed: 5': 'Gratitude',
        'Unnamed: 6': 'Ambition',
        'Unnamed: 7': 'Perserverence',
        'Green Room': 'Courage',
        'SoundProof side': 'Possibilities',
        'Unnamed: 10': 'Motivation',
        'Unnamed: 11': 'A302',
        'Unnamed: 12': 'A303',
        'Unnamed: 13': 'Success 10',
        'Unnamed: 14': 'Respect 10',
        'Unnamed: 15': 'Innovation (12)',
        'Unnamed: 16': 'Dedication',
        'Unnamed: 17': 'Integrity (15)',
    }
    
    bookings_imported = 0
    devices_parsed = 0
    
    # Process each row (skip header rows)
    for idx, row in df.iloc[2:].iterrows():  # Skip first 2 header rows
        date_val = row.get('Unnamed: 0')
        day_val = row.get('Unnamed: 1')
        
        if pd.isna(date_val):
            continue
        
        # Parse date
        try:
            if isinstance(date_val, str):
                booking_date = pd.to_datetime(date_val).date()
            else:
                booking_date = date_val.date() if hasattr(date_val, 'date') else date_val
        except:
            continue
        
        # Process each room column
        for col, room_name in room_mapping.items():
            cell_value = row.get(col)
            if pd.isna(cell_value) or str(cell_value).strip() == '':
                continue
            
            cell_text = str(cell_value).strip()
            if cell_text.lower() in ['nan', 'none', 'storage', 'it office', 'it store', 'store room', 'prayer room']:
                continue
            
            # Parse devices from text
            devices_override, device_note = parse_devices_from_text(cell_text)
            
            if devices_override:
                devices_parsed += 1
                print(f"  📱 {room_name}: {cell_text} → {devices_override} devices")
            
            # Check if room exists first
            room_check = db.run_query("SELECT id FROM rooms WHERE name = %s", (room_name,))
            if room_check.empty:
                print(f"  ⚠️ Room '{room_name}' not found in database, skipping")
                continue
            
            # Insert booking
            try:
                db.run_transaction("""
                    INSERT INTO bookings (
                        room_id, booking_period, client_name, status,
                        headcount, end_date, num_learners, num_facilitators,
                        devices_needed, devices_override, device_notes, is_historical_data,
                        client_contact_person, client_email, client_phone
                    ) VALUES (
                        (SELECT id FROM rooms WHERE name = %s),
                        tstzrange(%s, %s, '[)'),
                        %s, 'Approved',
                        1, %s, 1, 0,
                        %s, %s, %s, TRUE,
                        'Historical Import', 'import@colab.com', '0000000000'
                    )
                    ON CONFLICT DO NOTHING
                """, (
                    room_name,
                    datetime.combine(booking_date, datetime.min.time()).replace(hour=7, minute=30),
                    datetime.combine(booking_date, datetime.min.time()).replace(hour=16, minute=30),
                    cell_text[:100],  # Truncate if too long
                    booking_date,
                    devices_override if devices_override else 0,
                    devices_override,
                    device_note
                ))
                bookings_imported += 1
                
            except Exception as e:
                print(f"  ⚠️ Error importing {room_name} on {booking_date}: {e}")
    
    print(f"\n✅ Import complete!")
    print(f"   Bookings imported: {bookings_imported}")
    print(f"   Device counts parsed: {devices_parsed}")
    
    return bookings_imported, devices_parsed

if __name__ == "__main__":
    print("="*60)
    print("EXCEL IMPORT WITH DEVICE PARSING")
    print("="*60)
    
    # Clear existing historical data first (optional)
    print("\nClearing existing historical data...")
    db.run_transaction("DELETE FROM bookings WHERE is_historical_data = TRUE")
    
    # Import
    bookings, devices = import_bookings_with_devices()
    
    print("\n" + "="*60)
    print("Import Summary:")
    print(f"  Total bookings: {bookings}")
    print(f"  With device data: {devices}")
    print("="*60)
