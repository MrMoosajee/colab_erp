📘 Colab ERP v2.2: Infrastructure Reference
Classification: Internal Restricted

Quadrant: Reference / Explanation

Status: 🟢 Production Ready (v2.2.0)

🎯 Context: The Multi-Tenant Evolution
Colab ERP v2.2 represents a structural upgrade to support Multi-Tenancy (TECH/TRAINING divisions) and an AI Agent Foundation. While the system now attributes bookings to specific tenants, it maintains "Shared Physics"—global exclusion constraints ensure that physical assets (rooms/inventory) cannot be double-booked across the enterprise.

🛠️ Tech Stack & Architecture

Layer,		Component,	Specification
Frontend,	Streamlit,	v2.2 UI with enhanced error propagation
Backend,	Python 3.x,	Logic Bridge with ThreadedConnectionPool
Database,	PostgreSQL,	ACID compliant with GIST/EXCLUDE constraints
Auth,		bcrypt,		Database-backed secure hashing
Networking,	Tailscale,	Zero-Trust VPN mesh

✨ Key Features (v2.2.0)
Multi-Tenancy: Logical separation of TECH and TRAINING entities.

Database-Backed Auth: Migration from static secrets to secure, encrypted user tables.

Agent Infrastructure: Foundation for autonomous Auditor, Conflict Resolver, and Revenue agents.

Secure Vault: Read-only access to legacy .secure_vault data with path validation.

HITL (Human-in-the-Loop): Financial decisions require superuser approval via booking_costing ledger.

🏗️ Project Structure

.
├── src/
│   ├── app.py          # Frontend & View Orchestration
│   ├── db.py           # Logic Bridge & Connection Pooling
│   ├── auth.py         # Bcrypt Authentication Logic
│   └── agents/         # AI Agent Infrastructure (v2.2 New)
│       ├── base_agent.py    # Abstract Foundation
│       ├── pool_manager.py  # Tiered Connection Management
│       └── vault_interface.py # Secure Legacy Access
├── migrations/         # SQL Schema Evolutions
├── .secure_vault/      # Legacy Data (Outside Git)
└── requirements.txt    # bcrypt, psycopg2-binary, pandas

🗄️ Database Schema & Constraints
The system relies on PostgreSQL Range Types and Exclusion Constraints to prevent overlapping bookings.

$$\text{Constraint} = \text{room\_id} (=) \cap \text{booking\_period} (\&\&)$$

Note: Even in a multi-tenant environment, the exclusion constraint does not include tenant_id. If Tenant A occupies a room, Tenant B is physically blocked.

Key Tables
bookings: The master schedule with tenant_id attribution.

audit_log: Immutable record of all agent and system actions.

agent_config: Runtime settings and feature flags for AI agents.

pricing_catalog: Superuser-controlled rates for rooms and amenities.

🚀 Getting Started
1. Environment Setup

# Clone and enter directory
Bash
git clone <repository-url>
cd colab_erp

# Install dependencies
pip install -r requirements.txt

2. Database Migration
Apply the v2.2 foundation migration to update the schema:

Bash
psql -h <host> -U <user> -d colab_erp -f migrations/v2.2_audit_and_agent_foundation.sql
3. Execution
Bash
streamlit run src/app.py
🛡️ Security & Observability
Auditability: Every agent operation is logged to audit_log with execution time and metadata.

Circuit Breaker: The AgentPoolManager pauses agent activity if pool saturation exceeds 90%.

Vault Isolation: The .secure_vault is strictly isolated from Git and accessible only via the SecureVaultInterface.