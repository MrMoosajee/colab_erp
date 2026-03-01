"""Import 2025 Excel with different structure"""
import sys
sys.path.insert(0, '.')
import pandas as pd
import re
from datetime import datetime
import src.db as db

def parse_devices_from_text(text):
    """Extract device count from booking text"""
    if pd.isna(text) or not isinstance(text, str):
        return None, None
    text = str(text).strip()
    if not text or text.lower() in ['nan', 'none', '']:
        return None, None
    
    patterns = [
        r'(\d+)\s*laptops?',
        r'(\d+)\s*devices?',
        r'(\d+)\s*pcs?',
    ]
    
    devices_found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        devices_found.extend([int(m) for m in matches])
    
    if devices_found:
        return sum(devices_found), f"Extracted from: {text}"
    return None, None

# Read Excel
filepath = "/home/shuaibadams/Downloads/Colab 2025 Schedule (1).xlsx"
print(f"Reading: {filepath}")
df = pd.read_excel(filepath, header=None)

# The 2025 file has room names in row 0 and column headers in row 1
# Get room names from row 0 and 1
room_row = df.iloc[0].fillna('')
day_row = df.iloc[1].fillna('')

# Build room mapping from column index to room name
room_mapping = {}
for i in range(len(df.columns)):
    room_name = str(room_row[i]).strip() if i < len(room_row) else ''
    if room_name and room_name not in ['NaN', 'nan', '']:
        room_mapping[i] = room_name

print(f"\nRoom mapping: {room_mapping}")

# Process data rows (starting from row 2)
bookings_imported = 0
devices_parsed = 0

for idx in range(2, len(df)):
    row = df.iloc[idx]
    
    # Get date from column 0
    date_val = row[0]
    if pd.isna(date_val):
        continue
    
    try:
        if isinstance(date_val, str):
            booking_date = pd.to_datetime(date_val).date()
        else:
            booking_date = date_val.date() if hasattr(date_val, 'date') else None
        if not booking_date:
            continue
    except:
        continue
    
    # Process each room column
    for col_idx, room_name in room_mapping.items():
        if col_idx >= len(row):
            continue
            
        cell_value = row[col_idx]
        if pd.isna(cell_value):
            continue
        
        cell_text = str(cell_value).strip()
        if cell_text.lower() in ['nan', 'none', '']:
            continue
        
        # Skip non-booking entries
        skip_keywords = ['storage', 'it office', 'it store', 'store room', 'prayer room', 'melissa', 'tk office']
        if any(kw in cell_text.lower() for kw in skip_keywords):
            continue
        
        # Parse devices
        devices_override, device_note = parse_devices_from_text(cell_text)
        if devices_override:
            devices_parsed += 1
            print(f"  📱 {room_name}: {cell_text} → {devices_override} devices")
        
        # Check room exists
        room_check = db.run_query("SELECT id FROM rooms WHERE name = %s", (room_name,))
        if room_check.empty:
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
                    '2025 Historical Import', 'import@colab.com', '0000000000'
                )
                ON CONFLICT DO NOTHING
            """, (
                room_name,
                datetime.combine(booking_date, datetime.min.time()).replace(hour=7, minute=30),
                datetime.combine(booking_date, datetime.min.time()).replace(hour=16, minute=30),
                cell_text[:100],
                booking_date,
                devices_override if devices_override else 0,
                devices_override,
                device_note
            ))
            bookings_imported += 1
        except Exception as e:
            print(f"  ⚠️ Error: {e}")

print(f"\n✅ 2025 Import Complete!")
print(f"   Bookings imported: {bookings_imported}")
print(f"   Device counts parsed: {devices_parsed}")
