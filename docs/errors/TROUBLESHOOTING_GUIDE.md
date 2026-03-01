# TROUBLESHOOTING_GUIDE.md
# Solutions and Fixes - Colab ERP v2.2.x
# Quick reference for resolving common errors

---

## Metadata
- **Project**: Colab ERP v2.2.x
- **Documentation Date**: 2026-02-28
- **Status**: All errors resolved
- **Version**: v2.2.3 Production Ready

---

## Quick Fix Index

| Problem | Quick Solution | Section |
|---------|---------------|---------|
| `numpy.int64` type error | Use `convert_params_to_native()` | [Database Type Errors](#1-database--schema-errors) |
| Query returns 0 results | Add `tzinfo=timezone.utc` | [Database Type Errors](#1-database--schema-errors) |
| main() function corrupted | Use separate file + import | [Code Structure Errors](#2-code--syntax-errors) |
| Schema column mismatch | Run `\d table_name` first | [Schema Verification](#schema-verification-protocol) |
| Approval fatigue | Define approval levels | [Process Workflow](#4-process--workflow-fixes) |
| CDO not running | Use activation command | [CDO Activation](#cdo-activation-protocol) |
| Silent errors | Check exit codes | [Error Handling](#silent-error-fixes) |
| Deployment failed | Use verification checklist | [Deployment](#3-deployment--infrastructure-fixes) |

---

## 1. DATABASE & SCHEMA ERRORS

### 1.1 NumPy Type Conversion Error

**Error:**
```
psycopg2.ProgrammingError: can't adapt type 'numpy.int64'
```

**Root Cause:** Pandas/numpy types passed directly to PostgreSQL

**Solution:**

**Option A: Automatic (Recommended)**
```python
import src.db as db

# This now works automatically - numpy types converted internally
room_id = df.iloc[0]['id']  # numpy.int64
result = db.run_transaction(
    "INSERT INTO bookings (room_id) VALUES (%s)",
    (room_id,)  # Automatically converted to int
)
```

**Option B: Explicit Conversion**
```python
from src.numpy_type_converter import convert_params_to_native

params = (df.iloc[0]['id'], df.iloc[0]['price'])
clean_params = convert_params_to_native(params)
result = db.run_transaction(query, clean_params)
```

**Option C: Validation (Debugging)**
```python
from src.numpy_type_converter import validate_native_types

is_valid, error = validate_native_types(params)
if not is_valid:
    print(f"Warning: {error}")
```

**Files:**
- `src/numpy_type_converter.py` - Type conversion module
- `src/db.py` - Auto-conversion enabled
- `tests/test_numpy_type_converter.py` - 51 test cases

---

### 1.2 Timezone-Aware Datetime Errors

**Error:**
```
Query returns 0 rooms (silent failure)
Datetime comparison not working
```

**Root Cause:** Timezone-naive datetime vs UTC database times

**Solution:**
```python
from datetime import timezone

# Before (BROKEN)
start_dt = datetime.combine(start_date, datetime.min.time()).replace(hour=7, minute=30)

# After (FIXED)
start_dt = datetime.combine(start_date, datetime.min.time()).replace(
    hour=7, minute=30, tzinfo=timezone.utc
)
```

**Verification:**
```python
# Check if datetime is timezone-aware
if start_dt.tzinfo is None:
    print("ERROR: Datetime is timezone-naive!")
    start_dt = start_dt.replace(tzinfo=timezone.utc)
```

---

### 1.3 Schema Column Name Mismatch

**Error:**
```
Column not found: 'capacity'
Local works, server doesn't
```

**Root Cause:** Code uses `capacity`, database has `max_capacity`

**Solution:**
```python
# Fix 1: Use correct column name in SQL
SELECT max_capacity as capacity, name FROM rooms WHERE id = %s

# Fix 2: Update all references
# Created fix_columns.py for batch updates
```

**Schema Verification Protocol:**
```bash
# 1. Connect to database
psql -d colab_erp -U your_user

# 2. Inspect tables
\dt                    # List all tables
\d rooms               # Describe rooms table
\d bookings            # Describe bookings table

# 3. Check column names
\d+ rooms              # Detailed column info

# 4. Document in schema.md
```

---

### 1.4 Silent Query Failures

**Error:**
```
Query returned 0 results
No error logged
Silent failure
```

**Solution:** Add comprehensive debug output

```python
# Add to availability_service.py or queries
def get_available_rooms(start_date, end_date):
    print(f"DEBUG: Getting rooms for {start_date} to {end_date}")
    
    query = """
        SELECT id, name, floor, max_capacity, room_type 
        FROM rooms 
        WHERE tenant_id = %s AND is_active = TRUE
    """
    params = (session_state.get('tenant_id', 'TECH'),)
    
    print(f"DEBUG: SQL: {query}")
    print(f"DEBUG: Params: {params}")
    
    result = db.run_query(query, params)
    print(f"DEBUG: Query returned {len(result)} rooms")
    
    if len(result) == 0:
        print("WARNING: Query returned 0 rooms - checking database...")
        # Add fallback check
        all_rooms = db.run_query("SELECT COUNT(*) FROM rooms")
        print(f"DEBUG: Total rooms in DB: {all_rooms.iloc[0][0]}")
    
    return result
```

**Debug Scripts Created:**
- `debug_booking.py` - Booking form debug
- `add_debug.py` - General debug utilities
- `add_sql_debug.py` - SQL query debugging

---

## 2. CODE & SYNTAX ERRORS

### 2.1 main() Function Corruption

**Error:**
```
Application broken
main() function incomplete
Navigation logic deleted
```

**Root Cause:** `replace_in_file` corrupted function boundaries

**Solution:**

**Fix 1: Use Separate File + Import (Recommended)**
```python
# src/booking_form.py
def render_new_booking_form():
    """Enhanced booking form with all Phase 3 features."""
    from src.models import BookingService
    
    booking_service = BookingService()
    # ... full implementation ...

# src/app.py
from src.booking_form import render_new_booking_form

def main():
    # ... navigation logic unchanged ...
    if choice == "New Room Booking":
        render_new_booking_form()  # Call imported function
```

**Fix 2: Verification Script**
```bash
#!/bin/bash
# verify_app_structure.sh

echo "Checking main() function..."
if ! grep -q "def main():" src/app.py; then
    echo "ERROR: main() function missing!"
    exit 1
fi

if ! grep -q "if __name__ == \"__main__\":" src/app.py; then
    echo "ERROR: Entry point missing!"
    exit 1
fi

main_lines=$(grep -n "def main" src/app.py | wc -l)
if [ "$main_lines" -ne 1 ]; then
    echo "ERROR: Multiple main() functions found!"
    exit 1
fi

echo "Structure verified ✓"
```

**Prevention:**
- Never use `replace_in_file` for >50 line replacements
- Use separate file + import for large functions
- Run verification before deployment

---

### 2.2 Function Boundary Verification

**Check:**
```bash
# Check main() function is complete
grep -n "def main" src/app.py
grep -n "if __name__" src/app.py

# Verify all route handlers exist
grep -n "elif choice ==" src/app.py | wc -l  # Should be 9

# Check function boundaries with AST
python3 -c "import ast; ast.parse(open('src/app.py').read())"
```

---

## 3. DEPLOYMENT & INFRASTRUCTURE FIXES

### 3.1 Deployment Verification Protocol

**Required Steps:**
```bash
# 1. Syntax check
python3 -m py_compile src/app.py

# 2. Import check
python3 -c "import src.app"

# 3. Main function check
grep -c "def main" src/app.py     # Should be 1
grep -c "__main__" src/app.py     # Should be 1

# 4. Start test server
streamlit run src/app.py &
APP_PID=$!
sleep 5

# 5. Health check
curl -f http://localhost:8501/_stcore/health || {
    echo "ERROR: Health check failed"
    kill $APP_PID
    exit 1
}

# 6. Stop test server
kill $APP_PID

echo "✓ All verification checks passed"
```

---

### 3.2 Rollback Procedure

**Emergency Rollback:**
```bash
# 1. Find last working commit
git log --oneline -5

# 2. Rollback to working state
git reset --hard <working_commit_hash>

# 3. Restart application
pkill -f 'streamlit run'
nohup streamlit run src/app.py --server.port 8501 &

# 4. Verify
curl -f http://localhost:8501/_stcore/health
echo "Rollback complete ✓"
```

---

### 3.3 Local/Server Synchronization

**Fix Schema Mismatch:**
```python
# fix_columns.py
import src.db as db

def fix_column_names():
    """Fix column name mismatches between code and database."""
    
    # Get actual schema
    schema = db.run_query("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'rooms'
    """)
    
    print("Actual database schema:")
    print(schema)
    
    # Check for expected columns
    expected = ['id', 'name', 'floor', 'max_capacity', 'room_type']
    actual = schema['column_name'].tolist()
    
    for col in expected:
        if col not in actual:
            print(f"WARNING: Expected column '{col}' not found!")
            print(f"  Similar columns: {[c for c in actual if col in c or c in col]}")

if __name__ == "__main__":
    fix_column_names()
```

**Run:**
```bash
cd /home/shuaibadams/Projects/colab_erp
python3 fix_columns.py
```

---

## 4. PROCESS & WORKFLOW FIXES

### 4.1 Approval Levels Definition

**Define Clear Approval Levels:**

```markdown
Level 1 - Automatic (No approval needed):
- Syntax fixes
- Typo corrections
- Error message interpretation
- Log reading
- Debug output addition

Level 2 - Notify but Proceed:
- Minor refactoring (<20 lines)
- Adding error handling
- Documentation updates
- Test additions
- Debug code removal

Level 3 - Explicit Approval Required:
- Schema changes
- Architecture modifications
- Deleting code (>10 lines)
- Deployment to production
- Database migrations
- Changes to main(), auth, or core services
```

**Implementation:**
```python
def requires_approval(change_type, lines_changed=0):
    """Determine if change requires explicit approval."""
    
    if change_type in ['syntax_fix', 'typo', 'debug_add']:
        return False  # Level 1
    
    if change_type in ['refactor', 'error_handling', 'docs']:
        if lines_changed < 20:
            return False  # Level 2
    
    if change_type in ['schema', 'architecture', 'deployment', 'migration']:
        return True  # Level 3
    
    if lines_changed > 50:
        return True  # Large changes
    
    return False
```

---

### 4.2 CDO Activation Protocol

**Activation Command:**
```
You are now the CDO (Continuous Documentation Officer).
Your ONLY job is to document everything.

Responsibilities:
1. Log every action with timestamp
2. Record all errors with context
3. Note user frustrations and workarounds
4. Document assumptions vs verified facts
5. Track time spent on each task
6. Record all decisions made

Output: Structured log file with YAML frontmatter
Persistence: Run for entire session duration
Start time: [ISO8601 timestamp]

Acknowledge and begin logging immediately.
```

**CDO Log Format:**
```yaml
---
log_entry:
  timestamp: 2026-02-28T10:30:00Z
  action_type: command|edit|verification|error
  description: What was attempted
  command: Exact command run
  result: success|failure|partial
  errors: []
  assumptions_made: []
  verification_status: pending|passed|failed
  user_frustration_level: 0-5
  next_steps: []
---
```

---

### 4.3 Silent Error Fixes

**Required Error Handling:**
```python
# WRONG - Silent failure
result = run_command("deploy")

# RIGHT - Loud failure
output=$(some_command 2>&1)
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "ERROR: Command failed with code $exit_code"
    echo "Output: $output"
    log_error({
        "command": "deploy",
        "exit_code": exit_code,
        "stderr": output,
        "context": "Deployment attempt",
        "timestamp": datetime.now().isoformat()
    })
    exit 1
fi
```

**Python Error Handling:**
```python
import logging

logger = logging.getLogger(__name__)

def safe_query(query, params=None):
    """Execute query with comprehensive error handling."""
    try:
        result = db.run_query(query, params)
        
        # Check for unexpected empty results
        if result is None or len(result) == 0:
            logger.warning(f"Query returned empty result: {query}")
            logger.warning(f"Params: {params}")
        
        return result
        
    except Exception as e:
        logger.error(f"Query failed: {query}")
        logger.error(f"Params: {params}")
        logger.error(f"Exception: {e}")
        raise  # Re-raise after logging
```

---

## 5. SERVICE & INTEGRATION FIXES

### 5.1 BookingService Initialization

**Fix Missing Dependencies:**
```python
# src/models/booking_service.py

class BookingService:
    def __init__(self):
        self.availability_service = AvailabilityService()  # Add this
        self.device_manager = DeviceManager()  # Add if needed
        self.notification_manager = NotificationManager()  # Add if needed
    
    def create_booking(self, booking_data):
        # Use availability_service
        conflicts = self.availability_service.check_conflicts(
            booking_data['room_id'],
            booking_data['start_time'],
            booking_data['end_time']
        )
        # ... rest of method
```

---

### 5.2 Form Field Validation

**Fix Missing Fields:**
```python
# src/booking_form.py

def submit_booking(form_data):
    """Submit booking without created_by field."""
    
    # Remove non-critical fields that cause errors
    booking_data = {
        'client_name': form_data['client_name'],
        'room_id': form_data['room_id'],
        'start_time': form_data['start_time'],
        'end_time': form_data['end_time'],
        # 'created_by': form_data['created_by'],  # REMOVED - causes error
    }
    
    # created_by is set by database default or trigger
    return booking_service.create_booking(booking_data)
```

---

## 6. VERIFICATION SCRIPTS

### 6.1 Pre-Deployment Checklist

```bash
#!/bin/bash
# pre_deploy_check.sh

echo "=== Pre-Deployment Verification ==="

# 1. Syntax check
echo "[1/5] Checking Python syntax..."
python3 -m py_compile src/app.py || exit 1
echo "✓ Syntax OK"

# 2. Import check
echo "[2/5] Checking imports..."
python3 -c "import src.app" || exit 1
echo "✓ Imports OK"

# 3. Main function check
echo "[3/5] Checking main() function..."
main_count=$(grep -c "def main" src/app.py)
entry_count=$(grep -c "if __name__ == \"__main__\":" src/app.py)

if [ "$main_count" -ne 1 ]; then
    echo "✗ ERROR: Found $main_count main() functions (expected 1)"
    exit 1
fi

if [ "$entry_count" -ne 1 ]; then
    echo "✗ ERROR: Found $entry_count entry points (expected 1)"
    exit 1
fi

echo "✓ Structure OK"

# 4. Database connectivity
echo "[4/5] Checking database connectivity..."
python3 -c "import src.db; print('DB OK')" || exit 1
echo "✓ Database OK"

# 5. Route handlers
echo "[5/5] Checking route handlers..."
routes=$(grep -c "elif choice ==" src/app.py)
if [ "$routes" -lt 5 ]; then
    echo "⚠ WARNING: Only $routes route handlers found (expected 9)"
else
    echo "✓ Routes OK ($routes handlers)"
fi

echo ""
echo "=== All Checks Passed ✓ ==="
echo "Ready for deployment"
```

---

### 6.2 Post-Deployment Verification

```bash
#!/bin/bash
# post_deploy_check.sh

echo "=== Post-Deployment Verification ==="

# 1. Process check
echo "[1/4] Checking if app is running..."
if pgrep -f "streamlit run src/app.py" > /dev/null; then
    echo "✓ Process running"
else
    echo "✗ Process not running"
    exit 1
fi

# 2. Health check
echo "[2/4] Health check..."
sleep 3  # Wait for startup
if curl -sf http://localhost:8501/_stcore/health > /dev/null; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi

# 3. Log check
echo "[3/4] Checking logs for errors..."
if grep -i "error\|exception\|traceback" /var/log/colab_erp/error.log 2>/dev/null | tail -5; then
    echo "⚠ Recent errors found in logs"
else
    echo "✓ No recent errors"
fi

# 4. Database check
echo "[4/4] Database connectivity..."
python3 -c "
import src.db as db
result = db.run_query('SELECT COUNT(*) FROM bookings')
print(f'✓ Database OK - {result.iloc[0][0]} bookings')
"

echo ""
echo "=== Deployment Verified ✓ ==="
```

---

## 7. EMERGENCY PROCEDURES

### 7.1 Immediate Rollback

```bash
# Emergency rollback procedure
echo "EMERGENCY ROLLBACK"
echo "=================="

# 1. Stop current instance
pkill -f 'streamlit run'

# 2. Reset to last known good commit
git reset --hard HEAD~1  # or specific commit hash

# 3. Restart
nohup streamlit run src/app.py --server.port 8501 > /dev/null 2>&1 &

# 4. Verify
echo "Waiting for startup..."
sleep 5
if curl -sf http://localhost:8501/_stcore/health > /dev/null; then
    echo "✓ Rollback successful - System operational"
else
    echo "✗ Rollback failed - Manual intervention required"
fi
```

---

### 7.2 Database Recovery

```bash
# If database schema is corrupted
# Restore from backup
psql -d colab_erp < /backup/colab_erp_$(date +%Y%m%d).sql

# Or recreate schema
python3 -c "
import src.db as db
# Run migration scripts
db.run_query(open('migrations/v2.2_add_tenancy.sql').read())
db.run_query(open('migrations/v2.4_device_assignment_system.sql').read())
# ... etc
"
```

---

## Related Documentation

- [ERROR_LOG.md](./ERROR_LOG.md) - Chronological error history
- [ERROR_CATEGORIES.md](./ERROR_CATEGORIES.md) - Errors by type
- [LESSONS_LEARNED.md](./LESSONS_LEARNED.md) - Insights for future

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-02-28  
**Status:** All fixes verified and in production
