# Colab ERP v2.2: Phase 1 Deployment Guide
**For Cursor IDE/CLI Implementation**

---

## 🎯 Deployment Objective
Install the v2.2 Agent Infrastructure Foundation on COLAB-HOST-01 without disrupting v2.1.3 production services.

**Deployment Strategy:** Incremental, Non-Breaking
- No existing code modified (backward compatible)
- New tables added to database (non-destructive)
- New Python modules added to `src/agents/` (isolated)
- Production service continues running during deployment

---

## 📋 Pre-Deployment Checklist

Before starting deployment, verify:

- [ ] **Access**: Can SSH into COLAB-HOST-01 via Tailscale
- [ ] **Permissions**: User `colabtechsolutions` has write access to `/home/colabtechsolutions/colab_erp/`
- [ ] **Git Status**: No uncommitted changes in `colab_erp/` repo
- [ ] **Backup**: Recent database backup exists (`pg_dump` within last 24 hours)
- [ ] **Service Status**: `colab_erp.service` is running and healthy

---

## 🚀 Deployment Steps

### Step 1: Database Migration (10 minutes)

**Context:** Install audit_log, agent_config, pricing_catalog, and booking_costing tables.

```bash
# 1. SSH into server
ssh colabtechsolutions@<TAILSCALE_IP>

# 2. Navigate to repo
cd /home/colabtechsolutions/colab_erp

# 3. Create migrations directory if it doesn't exist
mkdir -p migrations

# 4. Upload the migration script (via Cursor)
# File: migrations/v2.2_audit_and_agent_foundation.sql
# Content: (See DELIVERABLE 1 above)

# 5. Create backup BEFORE migration
pg_dump colab_erp > ~/backups/pre_v2.2_$(date +%F_%H%M%S).sql

# 6. Run migration
sudo -u postgres psql -d colab_erp -f migrations/v2.2_audit_and_agent_foundation.sql

# 7. Verify migration success
sudo -u postgres psql -d colab_erp -c "\dt audit_log"
sudo -u postgres psql -d colab_erp -c "\dt agent_config"
sudo -u postgres psql -d colab_erp -c "\dt pricing_catalog"
sudo -u postgres psql -d colab_erp -c "\dt booking_costing"

# Expected output: All 4 tables should exist
```

**Success Criteria:**
- Migration completes with "Migration Complete" message
- All 4 tables exist in database
- No errors in PostgreSQL logs
- `colab_erp.service` still running (check: `sudo systemctl status colab_erp.service`)

---

### Step 2: Python Module Installation (5 minutes)

**Context:** Add agent infrastructure modules to `src/agents/` directory.

```bash
# Still in /home/colabtechsolutions/colab_erp

# 1. Create agents directory
mkdir -p src/agents

# 2. Upload Python modules (via Cursor)
# Files to create in src/agents/:
# - __init__.py (DELIVERABLE 2)
# - pool_manager.py (DELIVERABLE 2)
# - audit_logger.py (DELIVERABLE 3)
# - base_agent.py (DELIVERABLE 4)
# - vault_interface.py (DELIVERABLE 5)

# 3. Verify files exist
ls -lh src/agents/

# Expected output:
# __init__.py
# pool_manager.py
# audit_logger.py
# base_agent.py
# vault_interface.py

# 4. Check Python syntax
cd src/agents
python3 -m py_compile __init__.py
python3 -m py_compile pool_manager.py
python3 -m py_compile audit_logger.py
python3 -m py_compile base_agent.py
python3 -m py_compile vault_interface.py

# No output = success
# Errors = syntax error in code (fix before continuing)
```

**Success Criteria:**
- All 5 Python files exist in `src/agents/`
- No syntax errors when compiling
- File permissions are correct (readable by `colabtechsolutions`)

---

### Step 3: Git Commit & Version Control (5 minutes)

**Context:** Commit v2.2 foundation to Git for version tracking.

```bash
# Still in /home/colabtechsolutions/colab_erp

# 1. Check Git status
git status

# Should show:
# - migrations/v2.2_audit_and_agent_foundation.sql (new)
# - src/agents/ (new directory with 5 files)

# 2. Stage changes
git add migrations/v2.2_audit_and_agent_foundation.sql
git add src/agents/

# 3. Commit with descriptive message
git commit -m "v2.2 Phase 1: Agent Infrastructure Foundation

- Add audit_log table for immutable action tracking
- Add agent_config table for runtime configuration
- Add pricing_catalog table for superuser-controlled pricing
- Add booking_costing table for HITL revenue approval
- Add AgentPoolManager for connection safety
- Add AuditLogger for standardized logging
- Add BaseAgent abstract class for agent inheritance
- Add SecureVaultInterface for legacy data access

Status: Database schema updated, Python modules installed
Next: Phase 2 - Agent Implementation (Auditor, Conflict Resolver, Revenue)"

# 4. Push to remote (if configured)
git push origin main

# If push fails (no remote configured), that's fine for now
```

**Success Criteria:**
- Git commit created successfully
- All new files tracked in Git
- `.secure_vault` NOT in Git (verify with `git status`)

---

### Step 4: Service Validation (5 minutes)

**Context:** Verify v2.1.3 service still works after v2.2 installation.

```bash
# 1. Check service status
sudo systemctl status colab_erp.service

# Should show: active (running)

# 2. Check service logs for errors
journalctl -u colab_erp.service -n 50 --no-pager

# Look for:
# - "DB Pool Creation Failed" (should NOT appear)
# - Any Python import errors (should NOT appear)
# - Normal Streamlit startup messages (should appear)

# 3. Test database connection
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/colabtechsolutions/colab_erp')

# Test v2.1.3 still works
from src.db import get_db_pool
pool = get_db_pool()
print("✓ v2.1.3 pool works")

# Test v2.2 imports
from src.agents import AgentPoolManager, AuditLogger, BaseAgent
print("✓ v2.2 modules import successfully")

# Test audit_log table
from src.agents.pool_manager import get_pool_manager
manager = get_pool_manager()
with manager.get_agent_connection("test_agent") as conn:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM audit_log")
    count = cur.fetchone()[0]
    print(f"✓ audit_log table accessible ({count} records)")
EOF

# Expected output:
# ✓ v2.1.3 pool works
# ✓ v2.2 modules import successfully
# ✓ audit_log table accessible (X records)
```

**Success Criteria:**
- Service is running
- No errors in logs
- v2.1.3 code still works
- v2.2 modules import successfully
- audit_log table is accessible

---

### Step 5: Security Validation (5 minutes)

**Context:** Verify `.secure_vault` isolation and permissions.

```bash
# 1. Check vault exists
ls -ld /home/colabtechsolutions/.secure_vault

# Expected output:
# drwx------ ... colabtechsolutions .secure_vault

# Permissions MUST be 700 (owner-only)

# 2. Verify vault is NOT in Git
cd /home/colabtechsolutions/colab_erp
git ls-files | grep secure_vault

# Expected output: (nothing)
# If anything appears, vault is tracked by Git - THIS IS BAD

# 3. Test vault interface
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/colabtechsolutions/colab_erp')

from src.agents.vault_interface import SecureVaultInterface

# Initialize vault interface
vault = SecureVaultInterface("deployment_test")
print("✓ Vault interface initialized")

# Test vault stats
stats = vault.get_vault_stats()
print(f"✓ Vault contains {stats['total_files']} files ({stats['total_size_mb']:.2f} MB)")

# Test audit logging of vault access
# (check audit_log table for new record)
EOF

# Expected output:
# ✓ Vault interface initialized
# ✓ Vault contains X files (Y MB)
```

**Success Criteria:**
- Vault exists with correct permissions (700)
- Vault is NOT tracked by Git
- Vault interface works without errors
- Vault access is logged to audit_log

---

## 🔍 Post-Deployment Verification

After completing all steps, run this comprehensive test:

```bash
# Comprehensive validation script
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/colabtechsolutions/colab_erp')

print("=" * 60)
print("Colab ERP v2.2 Phase 1 Deployment Verification")
print("=" * 60)

# Test 1: v2.1.3 Compatibility
print("\n[1/5] Testing v2.1.3 backward compatibility...")
from src.db import get_db_pool, run_query
pool = get_db_pool()
rooms = run_query("SELECT COUNT(*) FROM rooms")
print(f"    ✓ v2.1.3 database functions work ({rooms.iloc[0,0]} rooms)")

# Test 2: Agent Infrastructure
print("\n[2/5] Testing v2.2 agent infrastructure...")
from src.agents import AgentPoolManager, AuditLogger, BaseAgent
from src.agents.pool_manager import get_pool_manager
manager = get_pool_manager()
print("    ✓ AgentPoolManager initialized")
print("    ✓ AuditLogger available")
print("    ✓ BaseAgent available")

# Test 3: Database Schema
print("\n[3/5] Testing v2.2 database schema...")
tables = run_query("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('audit_log', 'agent_config', 'pricing_catalog', 'booking_costing')
    ORDER BY table_name
""")
for table in tables['table_name']:
    print(f"    ✓ Table exists: {table}")

# Test 4: Audit Logging
print("\n[4/5] Testing audit logging...")
logger = AuditLogger("deployment_test", "1.0.0")
log_id = logger.log_action(
    operation="read",
    resource="deployment_verification",
    metadata={"test": True, "timestamp": "2026-01-29"}
)
print(f"    ✓ Audit log written (log_id: {log_id})")

# Test 5: Vault Interface
print("\n[5/5] Testing secure vault interface...")
from src.agents.vault_interface import SecureVaultInterface
vault = SecureVaultInterface("deployment_test")
stats = vault.get_vault_stats()
print(f"    ✓ Vault accessible ({stats['total_files']} files)")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - v2.2 Phase 1 Deployment Successful")
print("=" * 60)
print("\nNext Steps:")
print("  1. Review audit_log table for test entries")
print("  2. Proceed to Phase 2: Agent Implementation")
print("  3. Monitor service logs for 24 hours")
EOF
```

---

## 🚨 Rollback Procedure (If Needed)

If deployment fails or causes issues:

```bash
# 1. Stop service
sudo systemctl stop colab_erp.service

# 2. Restore database backup
psql colab_erp < ~/backups/pre_v2.2_YYYYMMDD_HHMMSS.sql

# 3. Remove Python modules
rm -rf /home/colabtechsolutions/colab_erp/src/agents/

# 4. Revert Git commit
cd /home/colabtechsolutions/colab_erp
git reset --hard HEAD~1

# 5. Restart service
sudo systemctl start colab_erp.service

# 6. Verify v2.1.3 restored
sudo systemctl status colab_erp.service
journalctl -u colab_erp.service -n 50
```

---

## 📊 Monitoring After Deployment

Monitor these metrics for 24 hours after deployment:

1. **Service Health**
   ```bash
   # Check every 6 hours
   sudo systemctl status colab_erp.service
   journalctl -u colab_erp.service --since "1 hour ago"
   ```

2. **Database Performance**
   ```sql
   -- Run daily
   SELECT 
       schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

3. **Audit Log Growth**
   ```sql
   -- Run daily
   SELECT 
       DATE(timestamp) as date,
       COUNT(*) as log_entries,
       COUNT(DISTINCT agent_id) as unique_agents
   FROM audit_log
   GROUP BY DATE(timestamp)
   ORDER BY date DESC
   LIMIT 7;
   ```

---

## 📞 Support & Escalation

If you encounter issues:

1. **Check Logs First**
   - Service logs: `journalctl -u colab_erp.service -n 100`
   - PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*.log`
   - Python errors: Look for tracebacks in service logs

2. **Common Issues**
   - **"Module not found" error**: Check `PYTHONPATH` in systemd service file
   - **"Permission denied" on vault**: Check vault permissions (should be 700)
   - **"Pool exhausted" error**: Too many concurrent users - expected during load testing

3. **Escalation Path**
   - Level 1: Check this deployment guide
   - Level 2: Review audit_log for error details
   - Level 3: Execute rollback procedure
   - Level 4: Contact CDO with audit_log export

---

## ✅ Sign-Off Checklist

Before marking deployment complete:

- [ ] All 5 deployment steps completed successfully
- [ ] Post-deployment verification script passed all tests
- [ ] Service is running and accessible via Tailscale
- [ ] Git commit created and pushed (if applicable)
- [ ] Backup created and verified
- [ ] Audit log contains deployment test entries
- [ ] Vault interface working and isolated from Git
- [ ] No errors in service logs for 1 hour post-deployment

**Deployment Status**: 🟡 In Progress → 🟢 Complete

**Deployed By**: ________________  
**Deployment Date**: ________________  
**Deployment Time**: ________________  
**Sign-Off**: ________________

---

## 📚 Next Steps: Phase 2

Once Phase 1 is deployed and stable, proceed to:

**Phase 2: Agent Implementation**
- Auditor Agent (Ghost Inventory reconciliation)
- Conflict Resolver Agent (Sliding Doors pre-validation)
- Revenue Agent (Booking cost calculation with HITL)

Phase 2 deployment guide will be provided after Phase 1 sign-off.

---

**End of Deployment Guide**
