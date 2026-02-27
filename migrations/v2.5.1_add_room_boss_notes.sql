-- FILE: migrations/v2.5.1_add_room_boss_notes.sql
-- Hotfix: Add missing room_boss_notes column
-- Date: 2026-02-27

-- ============================================================================
-- ADD MISSING COLUMN FROM v2.5_enhanced_booking_form.sql
-- ============================================================================

ALTER TABLE bookings ADD COLUMN IF NOT EXISTS room_boss_notes TEXT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'room_boss_notes column added:' as info;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'bookings'
AND column_name = 'room_boss_notes';