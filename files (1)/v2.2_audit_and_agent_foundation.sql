-- ============================================================================
-- COLAB ERP v2.2: AUDIT & AGENT FOUNDATION MIGRATION
-- ============================================================================
-- Classification: Internal Restricted
-- Status: 🟡 Pre-Production (Awaiting SRE Approval)
-- Date: January 29, 2026
-- 
-- CRITICAL WARNINGS:
-- 1. This script is NON-DESTRUCTIVE (no DROP TABLE commands)
-- 2. Always backup before running: pg_dump colab_erp > pre_v2.2_backup.sql
-- 3. Run as postgres user: sudo -u postgres psql -d colab_erp -f this_file.sql
-- ============================================================================

-- Set session timezone to UTC (consistent with v2.1.3 standards)
SET timezone = 'UTC';

-- ============================================================================
-- TABLE 1: AUDIT LOG (Immutable Agent Action Ledger)
-- ============================================================================
-- Purpose: Track all AI agent actions for compliance and debugging
-- Retention: Infinite (legal requirement for financial auditing)
-- Index Strategy: BRIN on timestamp (optimized for time-series queries)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    -- Primary Key: Auto-incrementing sequence
    id BIGSERIAL PRIMARY KEY,
    
    -- Temporal Data (UTC enforced)
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Agent Identification
    agent_id TEXT NOT NULL,
    agent_version TEXT,
    
    -- Action Classification
    operation TEXT NOT NULL CHECK (operation IN (
        'read',           -- Data retrieval
        'write',          -- Data insertion/update
        'delete',         -- Data deletion
        'vault_access',   -- Secure vault interaction
        'booking_propose',-- Booking proposal generated
        'booking_approve',-- Booking approved by agent
        'booking_reject', -- Booking rejected (conflict)
        'revenue_calc',   -- Revenue calculation performed
        'inventory_audit',-- Ghost inventory reconciliation
        'config_change'   -- System configuration modified
    )),
    
    -- Resource Target
    resource TEXT,  -- E.g., "booking_id:12345", "room_id:3", "vault:inventory_v1.xlsx"
    
    -- Structured Metadata (JSONB for flexible schema)
    metadata JSONB,
    
    -- Optional: Link to user who authorized the action (for HITL)
    authorized_by TEXT,  -- Username from users table
    authorization_timestamp TIMESTAMPTZ,
    
    -- Performance tracking
    execution_time_ms INTEGER,
    
    -- Error tracking
    error_occurred BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

-- ============================================================================
-- INDEXES FOR AUDIT LOG
-- ============================================================================

-- Primary query pattern: "Show me all agent actions in the last 24 hours"
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
ON audit_log USING BRIN (timestamp);

-- Secondary query pattern: "Show me all actions by agent_id='auditor_v1'"
CREATE INDEX IF NOT EXISTS idx_audit_log_agent_id 
ON audit_log (agent_id);

-- Tertiary query pattern: "Show me all failed operations"
CREATE INDEX IF NOT EXISTS idx_audit_log_errors 
ON audit_log (error_occurred) 
WHERE error_occurred = TRUE;

-- JSONB query optimization: "Show me all bookings proposed for room_id=3"
CREATE INDEX IF NOT EXISTS idx_audit_log_metadata 
ON audit_log USING GIN (metadata);

-- ============================================================================
-- TABLE 2: AGENT CONFIGURATION (Runtime Settings)
-- ============================================================================
-- Purpose: Store agent-specific configuration outside of secrets.toml
-- Use Case: Feature flags, thresholds, schedule overrides
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_config (
    -- Agent identifier (matches audit_log.agent_id)
    agent_id TEXT PRIMARY KEY,
    
    -- Lifecycle management
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    version TEXT NOT NULL,
    
    -- Configuration as JSON (flexible schema)
    config JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by TEXT  -- Username who last modified this config
);

-- Example seed data for The Auditor Agent
INSERT INTO agent_config (agent_id, enabled, version, config)
VALUES (
    'auditor_v1',
    TRUE,
    '1.0.0',
    '{
        "schedule": "0 2 * * *",
        "thresholds": {
            "max_discrepancy_percent": 5.0,
            "alert_on_negative_inventory": true
        },
        "notification_channels": ["admin_dashboard", "email"]
    }'::JSONB
)
ON CONFLICT (agent_id) DO NOTHING;

-- ============================================================================
-- TABLE 3: PRICING CATALOG (Superuser-Controlled Pricing)
-- ============================================================================
-- Purpose: Centralize all pricing data (rooms, amenities, services)
-- RBAC: Only superuser can INSERT/UPDATE/DELETE
-- Display: Normal users see prices only if superuser enables public_display
-- ============================================================================

CREATE TABLE IF NOT EXISTS pricing_catalog (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Item Classification
    item_type TEXT NOT NULL CHECK (item_type IN (
        'room',           -- Room rental base price
        'device',         -- IT equipment rental
        'catering',       -- Food/beverage services
        'printing',       -- Printing services
        'amenity_other'   -- Misc (tea/coffee, flip charts, etc.)
    )),
    
    -- Foreign Keys (nullable - depends on item_type)
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    -- For devices: link to inventory table (to be created)
    -- device_id INTEGER REFERENCES inventory(id) ON DELETE CASCADE,
    
    -- Item Details
    item_name TEXT NOT NULL,
    description TEXT,
    
    -- Pricing Structure
    price_per_unit NUMERIC(10, 2) NOT NULL CHECK (price_per_unit >= 0),
    unit TEXT NOT NULL DEFAULT 'hour',  -- 'hour', 'day', 'item', 'person'
    
    -- Tax configuration
    tax_rate NUMERIC(5, 2) DEFAULT 15.00,  -- South Africa VAT = 15%
    
    -- Visibility Control (CRITICAL FOR HITL)
    public_display BOOLEAN NOT NULL DEFAULT FALSE,  -- Superuser toggle
    
    -- Temporal validity (for seasonal pricing)
    valid_from DATE,
    valid_until DATE,
    
    -- Audit trail
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT NOT NULL,  -- Username
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by TEXT
);

-- Example seed data (Superuser must customize)
INSERT INTO pricing_catalog (item_type, item_name, description, price_per_unit, unit, public_display, created_by)
VALUES 
    ('room', 'Hourly Rate - Standard Conference Room', 'Base rate for 10-person capacity', 500.00, 'hour', FALSE, 'system'),
    ('catering', 'Tea/Coffee Station', 'Per person, includes cups and condiments', 25.00, 'person', FALSE, 'system'),
    ('printing', 'Black & White Printing', 'Per page, A4 standard', 2.00, 'item', FALSE, 'system'),
    ('amenity_other', 'Flip Chart with Markers', 'Rental for duration of booking', 50.00, 'booking', FALSE, 'system')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- TABLE 4: BOOKING_COSTING (Generated by Revenue Agent)
-- ============================================================================
-- Purpose: Store calculated costs for each booking
-- Workflow: Agent calculates → Superuser reviews → Superuser approves
-- Display: Only superuser sees this table unless booking is finalized
-- ============================================================================

CREATE TABLE IF NOT EXISTS booking_costing (
    -- Link to bookings table
    booking_reference TEXT PRIMARY KEY REFERENCES bookings(booking_reference) ON DELETE CASCADE,
    
    -- Cost Breakdown (all amounts in ZAR)
    room_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    device_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    catering_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    printing_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    amenity_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    
    -- Calculated Totals
    subtotal NUMERIC(10, 2) GENERATED ALWAYS AS (
        room_cost + device_cost + catering_cost + printing_cost + amenity_cost
    ) STORED,
    tax_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total NUMERIC(10, 2) GENERATED ALWAYS AS (
        room_cost + device_cost + catering_cost + printing_cost + amenity_cost + tax_amount
    ) STORED,
    
    -- HITL Approval Workflow
    status TEXT NOT NULL DEFAULT 'pending_review' CHECK (status IN (
        'pending_review',   -- Agent calculated, awaiting superuser
        'approved',         -- Superuser approved
        'rejected',         -- Superuser rejected
        'invoiced'          -- Finalized and sent to client
    )),
    
    -- Audit Trail
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    calculated_by TEXT NOT NULL DEFAULT 'revenue_agent_v1',
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,  -- Superuser username
    
    -- Metadata (JSONB for itemized breakdown)
    cost_breakdown JSONB  -- E.g., {"devices": [{"id": 45, "qty": 2, "cost": 100}]}
);

-- ============================================================================
-- VIEW: AGENT PERFORMANCE METRICS (Read-Only Dashboard)
-- ============================================================================
-- Purpose: Provide SRE/Superuser visibility into agent health
-- ============================================================================

CREATE OR REPLACE VIEW agent_performance_metrics AS
SELECT 
    agent_id,
    COUNT(*) AS total_operations,
    COUNT(*) FILTER (WHERE error_occurred = TRUE) AS failed_operations,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE error_occurred = TRUE) / NULLIF(COUNT(*), 0),
        2
    ) AS error_rate_percent,
    AVG(execution_time_ms) AS avg_execution_time_ms,
    MAX(timestamp) AS last_activity,
    COUNT(DISTINCT DATE(timestamp)) AS active_days_last_30d
FROM audit_log
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY agent_id
ORDER BY total_operations DESC;

-- ============================================================================
-- FUNCTION: LOG AGENT ACTION (Helper for Agents)
-- ============================================================================
-- Purpose: Standardized logging function that agents can call
-- Usage: SELECT log_agent_action('auditor_v1', 'inventory_audit', 'room_id:3', '{"discrepancy": 2}');
-- ============================================================================

CREATE OR REPLACE FUNCTION log_agent_action(
    p_agent_id TEXT,
    p_operation TEXT,
    p_resource TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL,
    p_execution_time_ms INTEGER DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
) RETURNS BIGINT AS $$
DECLARE
    v_log_id BIGINT;
BEGIN
    INSERT INTO audit_log (
        agent_id,
        operation,
        resource,
        metadata,
        execution_time_ms,
        error_occurred,
        error_message
    ) VALUES (
        p_agent_id,
        p_operation,
        p_resource,
        p_metadata,
        p_execution_time_ms,
        (p_error_message IS NOT NULL),
        p_error_message
    )
    RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: AUTO-UPDATE updated_at ON agent_config
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agent_config_updated_at
    BEFORE UPDATE ON agent_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- GRANT PERMISSIONS (Align with v2.1.3 user model)
-- ============================================================================

-- Application user (colabtechsolutions) gets full access to audit_log
GRANT SELECT, INSERT ON audit_log TO colabtechsolutions;
GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq TO colabtechsolutions;

-- Agent config (read-only for app, write via admin interface only)
GRANT SELECT ON agent_config TO colabtechsolutions;

-- Pricing catalog (read for app, write via superuser UI only)
GRANT SELECT ON pricing_catalog TO colabtechsolutions;

-- Booking costing (full access for revenue agent)
GRANT SELECT, INSERT, UPDATE ON booking_costing TO colabtechsolutions;

-- Performance metrics view (read-only)
GRANT SELECT ON agent_performance_metrics TO colabtechsolutions;

-- ============================================================================
-- VALIDATION QUERIES (Run after migration to verify success)
-- ============================================================================

-- Check table creation
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'audit_log') = 1,
        'audit_log table not created';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'agent_config') = 1,
        'agent_config table not created';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'pricing_catalog') = 1,
        'pricing_catalog table not created';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'booking_costing') = 1,
        'booking_costing table not created';
    
    RAISE NOTICE '✓ All tables created successfully';
END $$;

-- Check indexes
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'audit_log') >= 4,
        'audit_log indexes not created';
    
    RAISE NOTICE '✓ All indexes created successfully';
END $$;

-- Check view
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM information_schema.views WHERE table_name = 'agent_performance_metrics') = 1,
        'agent_performance_metrics view not created';
    
    RAISE NOTICE '✓ Performance metrics view created successfully';
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Insert migration record (for tracking)
INSERT INTO audit_log (agent_id, operation, resource, metadata)
VALUES (
    'system',
    'config_change',
    'database_schema',
    '{"migration": "v2.2_audit_and_agent_foundation", "status": "complete"}'::JSONB
);

RAISE NOTICE '============================================================================';
RAISE NOTICE 'Colab ERP v2.2 Migration Complete';
RAISE NOTICE 'Tables Created: audit_log, agent_config, pricing_catalog, booking_costing';
RAISE NOTICE 'Next Step: Deploy agent Python modules via Cursor';
RAISE NOTICE '============================================================================';
