-- FILE: migrations/v2.4_device_assignment_system.sql
-- Phase 2: IT Staff Device Assignment System
-- Date: 2026-02-23

-- ============================================================================
-- 1. UPDATE DEVICES TABLE - Add status tracking
-- ============================================================================

-- Add status column to track device availability
ALTER TABLE devices 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'AVAILABLE';

-- Add constraint to ensure valid status values
ALTER TABLE devices 
ADD CONSTRAINT chk_device_status 
CHECK (status IN ('AVAILABLE', 'ASSIGNED', 'OFFSITE', 'MAINTENANCE'));

-- ============================================================================
-- 2. CREATE OFFSITE RENTALS TABLE - Track off-site device rentals
-- ============================================================================

CREATE TABLE IF NOT EXISTS offsite_rentals (
    id SERIAL PRIMARY KEY,
    booking_device_assignment_id INTEGER REFERENCES booking_device_assignments(id) ON DELETE CASCADE,
    rental_no VARCHAR(50) UNIQUE,
    rental_date DATE NOT NULL,
    contact_person VARCHAR(100) NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    contact_email VARCHAR(100),
    company VARCHAR(200),
    address TEXT NOT NULL,
    return_expected_date DATE NOT NULL,
    returned_at TIMESTAMPTZ,
    rental_form_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick lookup by booking device assignment
CREATE INDEX IF NOT EXISTS idx_offsite_rentals_assignment 
ON offsite_rentals(booking_device_assignment_id);

-- Index for rental number lookups
CREATE INDEX IF NOT EXISTS idx_offsite_rentals_no 
ON offsite_rentals(rental_no);

-- ============================================================================
-- 3. CREATE DEVICE MOVEMENT LOG - For AI learning and audit trail
-- ============================================================================

CREATE TABLE IF NOT EXISTS device_movement_log (
    log_id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(device_id),
    action VARCHAR(50) NOT NULL,
    from_booking_id INTEGER REFERENCES bookings(id),
    to_booking_id INTEGER REFERENCES bookings(id),
    performed_by VARCHAR(100) NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for device movement history
CREATE INDEX IF NOT EXISTS idx_device_movement_device 
ON device_movement_log(device_id);

-- Index for booking lookups
CREATE INDEX IF NOT EXISTS idx_device_movement_from_booking 
ON device_movement_log(from_booking_id);

CREATE INDEX IF NOT EXISTS idx_device_movement_to_booking 
ON device_movement_log(to_booking_id);

-- Index for action type queries
CREATE INDEX IF NOT EXISTS idx_device_movement_action 
ON device_movement_log(action);

-- ============================================================================
-- 4. CREATE STOCK NOTIFICATIONS TABLE - Low stock alerts
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_notifications (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    devices_available INTEGER NOT NULL,
    devices_needed INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    notified_it_boss BOOLEAN DEFAULT FALSE,
    notified_room_boss BOOLEAN DEFAULT FALSE,
    it_boss_acknowledged BOOLEAN DEFAULT FALSE,
    room_boss_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for unread notifications
CREATE INDEX IF NOT EXISTS idx_stock_notifications_unread 
ON stock_notifications(notified_it_boss, notified_room_boss);

-- Index by category
CREATE INDEX IF NOT EXISTS idx_stock_notifications_category 
ON stock_notifications(category);

-- ============================================================================
-- 5. CREATE IN-APP NOTIFICATIONS TABLE - General notifications
-- ============================================================================

CREATE TABLE IF NOT EXISTS in_app_notifications (
    id SERIAL PRIMARY KEY,
    recipient_role VARCHAR(50) NOT NULL,
    recipient_username VARCHAR(100),
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    related_booking_id INTEGER REFERENCES bookings(id),
    related_device_id INTEGER REFERENCES devices(device_id),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for user's unread notifications
CREATE INDEX IF NOT EXISTS idx_notifications_unread 
ON in_app_notifications(recipient_role, is_read, created_at DESC);

-- Index by notification type
CREATE INDEX IF NOT EXISTS idx_notifications_type 
ON in_app_notifications(notification_type);

-- ============================================================================
-- 6. UPDATE BOOKING_DEVICE_ASSIGNMENTS - Add tracking fields
-- ============================================================================

-- Add assigned_at timestamp if not exists
ALTER TABLE booking_device_assignments 
ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMPTZ DEFAULT NOW();

-- Add is_offsite flag
ALTER TABLE booking_device_assignments 
ADD COLUMN IF NOT EXISTS is_offsite BOOLEAN DEFAULT FALSE;

-- Add notes field
ALTER TABLE booking_device_assignMENTS 
ADD COLUMN IF NOT EXISTS notes TEXT;

-- ============================================================================
-- 7. CREATE TRIGGER FUNCTION - Auto-update device status
-- ============================================================================

CREATE OR REPLACE FUNCTION update_device_status_on_assignment()
RETURNS TRIGGER AS $$
BEGIN
    -- When device is assigned, update status to ASSIGNED or OFFSITE
    IF NEW.is_offsite THEN
        UPDATE devices SET status = 'OFFSITE' WHERE device_id = NEW.device_id;
    ELSE
        UPDATE devices SET status = 'ASSIGNED' WHERE device_id = NEW.device_id;
    END IF;
    
    -- Log the assignment
    INSERT INTO device_movement_log (
        device_id, action, to_booking_id, performed_by, reason
    ) VALUES (
        NEW.device_id, 
        'ASSIGNED', 
        NEW.booking_id, 
        NEW.assigned_by,
        COALESCE(NEW.notes, 'Device assigned to booking')
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_device_assignment ON booking_device_assignments;
CREATE TRIGGER trigger_device_assignment
    AFTER INSERT ON booking_device_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_device_status_on_assignment();

-- ============================================================================
-- 8. CREATE TRIGGER FUNCTION - Auto-update device status on deletion
-- ============================================================================

CREATE OR REPLACE FUNCTION update_device_status_on_unassignment()
RETURNS TRIGGER AS $$
BEGIN
    -- When device is unassigned, update status back to AVAILABLE
    UPDATE devices SET status = 'AVAILABLE' WHERE device_id = OLD.device_id;
    
    -- Log the unassignment
    INSERT INTO device_movement_log (
        device_id, action, from_booking_id, performed_by, reason
    ) VALUES (
        OLD.device_id, 
        'UNASSIGNED', 
        OLD.booking_id, 
        COALESCE(OLD.assigned_by, 'SYSTEM'),
        'Device unassigned from booking'
    );
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_device_unassignment ON booking_device_assignments;
CREATE TRIGGER trigger_device_unassignment
    AFTER DELETE ON booking_device_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_device_status_on_unassignment();

-- ============================================================================
-- 9. GRANT PERMISSIONS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE ON offsite_rentals TO colabtechsolutions;
GRANT SELECT, INSERT ON device_movement_log TO colabtechsolutions;
GRANT SELECT, INSERT, UPDATE ON stock_notifications TO colabtechsolutions;
GRANT SELECT, INSERT, UPDATE ON in_app_notifications TO colabtechsolutions;
GRANT USAGE ON SEQUENCE offsite_rentals_id_seq TO colabtechsolutions;
GRANT USAGE ON SEQUENCE device_movement_log_log_id_seq TO colabtechsolutions;
GRANT USAGE ON SEQUENCE stock_notifications_id_seq TO colabtechsolutions;
GRANT USAGE ON SEQUENCE in_app_notifications_id_seq TO colabtechsolutions;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check devices table
SELECT 'devices table updated' as status, COUNT(*) as device_count 
FROM devices;

-- Check new tables exist
SELECT 'offsite_rentals table created' as status, COUNT(*) as count 
FROM information_schema.tables 
WHERE table_name = 'offsite_rentals';

SELECT 'device_movement_log table created' as status, COUNT(*) as count 
FROM information_schema.tables 
WHERE table_name = 'device_movement_log';

SELECT 'stock_notifications table created' as status, COUNT(*) as count 
FROM information_schema.tables 
WHERE table_name = 'stock_notifications';

SELECT 'in_app_notifications table created' as status, COUNT(*) as count 
FROM information_schema.tables 
WHERE table_name = 'in_app_notifications';