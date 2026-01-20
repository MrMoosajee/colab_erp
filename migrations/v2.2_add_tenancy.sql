-- FILE: migrations/v2.2_add_tenancy.sql
-- Multi-Tenancy Upgrade: Shared Ledger with Tenant Attribution
-- Constraint: Physical Exclusion Constraints remain GLOBAL (shared physics)

-- 1. Create the Tenant Enum (Fixed Business Entities)
DO $$ BEGIN
    CREATE TYPE tenant_type AS ENUM ('TECH', 'TRAINING');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Add Tenant Column to Bookings (The Schedule)
-- Default to 'TECH' to preserve legacy data integrity
ALTER TABLE bookings 
ADD COLUMN IF NOT EXISTS tenant_id tenant_type NOT NULL DEFAULT 'TECH';

-- 3. Add Tenant Column to Inventory Movements (The Audit Trail)
ALTER TABLE inventory_movements 
ADD COLUMN IF NOT EXISTS tenant_id tenant_type NOT NULL DEFAULT 'TECH';

-- 4. Create Index for Reporting Performance
CREATE INDEX IF NOT EXISTS idx_bookings_tenant ON bookings(tenant_id);

-- NOTE: We do NOT alter the EXCLUDE constraints. 
-- Physics is shared. If 'TECH' books Room A, 'TRAINING' cannot book it.
-- The exclusion constraints enforce global collision detection across all tenants.
