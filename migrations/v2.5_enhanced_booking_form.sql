-- FILE: migrations/v2.5_enhanced_booking_form.sql
-- Phase 3: Enhanced Booking Form
-- Date: 2026-02-24

-- ============================================================================
-- 1. ADD NEW COLUMNS TO BOOKINGS TABLE
-- ============================================================================

-- Attendee counts
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS num_learners INTEGER DEFAULT 0;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS num_facilitators INTEGER DEFAULT 0;

-- Catering options
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS coffee_tea_station BOOLEAN DEFAULT FALSE;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS morning_catering VARCHAR(50);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS lunch_catering VARCHAR(50);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS catering_notes TEXT;

-- Supplies
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS stationery_needed BOOLEAN DEFAULT FALSE;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS water_bottles INTEGER DEFAULT 0;

-- Devices
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS devices_needed INTEGER DEFAULT 0;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS device_type_preference VARCHAR(50);

-- Client contact info
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS client_contact_person VARCHAR(100);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS client_email VARCHAR(100);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS client_phone VARCHAR(20);

-- ============================================================================
-- 2. ADD CONSTRAINTS FOR VALID VALUES
-- ============================================================================

-- Morning catering options: 'none', 'pastry', 'sandwiches'
ALTER TABLE bookings 
ADD CONSTRAINT chk_morning_catering 
CHECK (morning_catering IS NULL OR morning_catering IN ('none', 'pastry', 'sandwiches'));

-- Lunch catering options: 'none', 'self_catered', 'in_house'
ALTER TABLE bookings 
ADD CONSTRAINT chk_lunch_catering 
CHECK (lunch_catering IS NULL OR lunch_catering IN ('none', 'self_catered', 'in_house'));

-- Device type preference: 'any', 'laptops', 'desktops'
ALTER TABLE bookings 
ADD CONSTRAINT chk_device_preference 
CHECK (device_type_preference IS NULL OR device_type_preference IN ('any', 'laptops', 'desktops'));

-- ============================================================================
-- 3. GRANT PERMISSIONS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE ON bookings TO colabtechsolutions;

-- ============================================================================
-- 4. VERIFICATION
-- ============================================================================

SELECT 'Bookings table columns:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'bookings' 
AND column_name IN (
    'num_learners', 'num_facilitators', 
    'coffee_tea_station', 'morning_catering', 'lunch_catering', 'catering_notes',
    'stationery_needed', 'water_bottles',
    'devices_needed', 'device_type_preference',
    'client_contact_person', 'client_email', 'client_phone'
)
ORDER BY ordinal_position;