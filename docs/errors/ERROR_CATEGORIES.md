# ERROR_CATEGORIES.md
# Errors Organized by Type - Colab ERP v2.2.x
# For LLM RAG: Search by error type, keywords, or tags

---

## Metadata
- **Project**: Colab ERP v2.2.x
- **Documentation Date**: 2026-02-28
- **Total Errors**: 15+
- **Categories**: 6 primary categories

---

## Category 1: DATABASE & SCHEMA ERRORS

**Keywords:** `#database` `#schema` `#sql` `#postgresql` `#psycopg2` `#column` `#table` `#query` `#timezone` `#datetime`

### ERR-2026-02-24-002: Query Returns 0 Rooms - Silent Database Failure
**Severity:** HIGH  
**Tags:** `#timezone` `#datetime-comparison` `#silent-error` `#utc`  

**Error Message:**
```
"Query returned 0 rooms"
Available rooms dropdown: EMPTY
No error logged - silent failure
```

**Root Cause:** Timezone mismatch between database stored times (UTC) and query parameters (no timezone). Datetime comparison failing silently.

**Solution:**
```python
# Add timezone info to datetime objects
from datetime import timezone
start_dt = datetime.combine(start_date, datetime.min.time()).replace(
    hour=7, minute=30, tzinfo=timezone.utc
)
```

**Prevention:**
- Always use timezone-aware datetimes
- All database datetimes must be UTC
- Add warnings on queries returning 0 results unexpectedly

---

### ERR-2026-02-24-005: Schema Mismatch - Column Name Error
**Severity:** HIGH  
**Tags:** `#column-mismatch` `#schema` `#local-vs-server` `#max_capacity`  

**Error Message:**
```
"The column is called 'max_capacity', not 'capacity'. How did we not know this?"
```

**Root Cause:** Database has `max_capacity`, code uses `capacity`. Environment inconsistency between local and server.

**Solution:**
```python
# Use correct column name
SELECT max_capacity as capacity, name FROM rooms WHERE id = %s
```

**Prevention:**
- Run `\d table_name` on all tables before development
- Document schema in `schema.md`
- Environment parity: Local and server must match

---

### ERR-2026-02-27-001: NumPy Type Conversion Error
**Severity:** HIGH  
**Tags:** `#numpy` `#psycopg2` `#type-conversion` `#pandas` `#numpy.int64`  

**Error Message (Exact):**
```
psycopg2.ProgrammingError: can't adapt type 'numpy.int64'
```

**Root Cause:** Pandas DataFrame values return numpy types. psycopg2 cannot handle numpy types directly.

**Solution:**
```python
# Use automatic conversion
from src.numpy_type_converter import convert_params_to_native

# db.py now handles this automatically
result = db.run_transaction(
    "INSERT INTO bookings (room_id) VALUES (%s)",
    (room_id,)  # Automatically converted to int
)
```

**Files:**
- `src/numpy_type_converter.py` - Type conversion module
- `src/db.py` - Modified to auto-convert
- `tests/test_numpy_type_converter.py` - 51 test cases

---

### ERR-2026-02-24-012: Database Schema Assumptions
**Severity:** HIGH  
**Tags:** `#schema` `#assumptions` `#discovery` `#verification`  

**Error Message:**
```
Wrote database code based on assumptions rather than verified schema
```

**Root Cause:** LLM assumed column names, types, and relationships without verification.

**Solution:** Schema-first development protocol

**Prevention:**
```bash
# 1. Connect to database
# 2. Run inspection commands:
\dt                    # list tables
\d table_name          # describe each table
\di                    # list indexes
# 3. Document findings in schema.md
# 4. Verify against application code
# 5. Proceed with development
```

---

## Category 2: CODE & SYNTAX ERRORS

**Keywords:** `#syntax` `#code` `#python` `#function` `#corruption` `#replace-in-file` `#main-function`

### ERR-2026-02-24-001: Application Breakage - main() Function Corruption
**Severity:** CRITICAL  
**Tags:** `#syntax-error` `#main-function` `#corruption` `#replace-in-file-failure`  

**Error Message:**
```
Application completely unavailable
HTTP 500 errors on all endpoints
main() function corrupted during code insertion
```

**Root Cause:** `replace_in_file` inserted new function INSIDE `main()` instead of as separate function. Deleted navigation logic and entry point.

**Broken Code:**
```python
def main():
    init_session_state()
    # ... 9 lines only ...
def render_new_booking_form():  # WRONG! Inside main!
    """Enhanced booking form..."""
```

**Solution:**
```python
# Use separate file + import for large functions
# src/booking_form.py
def render_new_booking_form():
    # ... entire function ...

# src/app.py
from src.booking_form import render_new_booking_form
```

**Prevention:**
- Never use `replace_in_file` for >50 line replacements
- Verify `main()` function completeness before deployment
- Use `python3 -c "import ast; ast.parse(open('src/app.py').read())"`

---

### ERR-2026-02-24-004: Deployment Disaster - Ghost Inventory Implementation
**Severity:** CRITICAL  
**Tags:** `#deployment` `#production-down` `#corrupted-code` `#function-boundary`  

**Error Message:**
```
"The app is BROKEN. Completely broken."
Navigation logic DELETED
Entry point DELETED
```

**Root Cause:** Same as ERR-2026-02-24-001 - `replace_in_file` corrupted `main()` function.

**Solution:** Immediate rollback and re-implementation using separate file approach.

---

## Category 3: DEPLOYMENT & INFRASTRUCTURE ERRORS

**Keywords:** `#deployment` `#production` `#server` `#health-check` `#verification` `#rollback` `#outage`

### ERR-2026-02-24-011: Deployment Verification Failures
**Severity:** CRITICAL  
**Tags:** `#deployment` `#verification` `#silent-errors` `#health-check`  

**Error Message:**
```
"Deployment successful"
No server logs checked for errors
No health check endpoints called
Did not verify application actually running
```

**Root Cause:** LLM claimed deployment successful without proper verification.

**Solution:** Created verification scripts and health check automation.

**Prevention - Verification Checklist:**
```bash
# After any deployment:
[ ] Server logs checked for errors
[ ] Application health endpoint verified
[ ] Database connectivity confirmed
[ ] User acceptance testing performed
[ ] Rollback plan documented

# Commands:
tail -f /var/log/colab_erp/error.log
curl -f http://localhost:8501/_stcore/health
python3 -c "import src.db; print('DB OK')"
```

---

### ERR-2026-02-24-009: Local/Server Synchronization Issues
**Severity:** HIGH  
**Tags:** `#environment` `#local-vs-server` `#schema-sync` `#false-confidence`  

**Error Message:**
```
"Local works, server doesn't. Why?"
"Is the server using different code than local?"
```

**Root Cause:** Edits made to wrong files, server state not matching local changes, deployment confusion.

**Solution:** Schema alignment, explicit environment tagging.

**Prevention:**
- Explicit local vs server context on every operation
- Sync verification steps
- Staging environment for testing
- Schema validation before deployment

---

## Category 4: PROCESS & WORKFLOW ERRORS

**Keywords:** `#process` `#workflow` `#approval` `#micromanagement` `#autonomy` `#cdo` `#ux`

### ERR-2026-02-24-003: Approval Fatigue - Process Failure
**Severity:** MEDIUM  
**Tags:** `#process` `#ux` `#micromanagement` `#approval-fatigue` `#autonomy-failure`  

**Error Message:**
```
"Do I really need to approve this?"
"Why are you asking me? You're the expert!"
"I trust you, just DO IT."
```

**Root Cause:** AI asked for approval on every 2-line change. "Approval before fixes" interpreted as "stop and wait for every action."

**Solution:** Define approval levels clearly.

**Prevention - Approval Levels:**
```
Level 1 - Automatic (No approval needed):
  - Syntax fixes
  - Typo corrections
  - Error message interpretation
  - Log reading

Level 2 - Notify but Proceed:
  - Minor refactoring
  - Adding error handling
  - Documentation updates
  - Test additions

Level 3 - Explicit Approval Required:
  - Schema changes
  - Architecture modifications
  - Deleting code
  - Deployment to production
  - Database migrations
```

---

### ERR-2026-02-24-006: CDO Sub-Agent Failure - Documentation Abandonment
**Severity:** MEDIUM  
**Tags:** `#cdo` `#sub-agent` `#documentation` `#process-failure`  

**Error Message:**
```
"I asked for the CDO sub-agent. It's not running."
"What's the point of sub-agents if they don't activate?"
```

**Root Cause:** LLM failed to maintain CDO sub-agent as persistent background process.

**Solution:** Manual documentation creation post-session.

**Prevention:**
```
Activation Command:
"You are now the CDO. Your ONLY job is to document. 
Create a log file and record every action, error, and user frustration. 
You persist until session end. Acknowledge and begin logging."
```

---

### ERR-2026-02-24-010: Premature Task Completion
**Severity:** MEDIUM  
**Tags:** `#completion` `#verification` `#trust` `#assumption-based`  

**Error Message:**
```
"Task completed successfully!"
Reality: Silent errors, deployment not verified, issues persist
```

**Root Cause:** LLM declared tasks "completed" without sufficient verification.

**Solution:** Comprehensive test suite, manual verification.

**Prevention:**
```
FORBIDDEN:
"Task completed!"

REQUIRED:
"Task potentially complete. Verification steps:
  1. [Command to verify]
  2. [Check to perform]
  3. [User validation needed]
  
  Shall I proceed with verification?"
```

---

## Category 5: INTEGRATION & SERVICE ERRORS

**Keywords:** `#integration` `#service` `#import` `#initialization` `#dependency` `#booking-service` `#availability-service`

### ERR-2026-02-27-002: BookingService Missing AvailabilityService
**Severity:** MEDIUM  
**Tags:** `#integration` `#missing-import` `#service-dependency` `#initialization`  

**Error Message:**
```
BookingService initialization failed
AvailabilityService not properly imported/initialized
```

**Root Cause:** Missing dependency initialization in service constructor.

**Solution:**
```python
class BookingService:
    def __init__(self):
        self.availability_service = AvailabilityService()  # Added
```

**Prevention:** Verify all service dependencies on initialization.

---

### ERR-2026-02-27-003: created_by Field Error in Booking Form
**Severity:** MEDIUM  
**Tags:** `#form` `#validation` `#missing-field` `#booking-form`  

**Error Message:**
```
created_by field error in booking form
Missing required field 'created_by'
```

**Solution:** Removed `created_by` parameter from booking form submission.

---

## Category 6: LLM & AI BEHAVIOR ERRORS

**Keywords:** `#llm` `#ai` `#memory` `#context` `#session` `#cognitive-load` `#autonomy`

### ERR-2026-02-24-007: LLM Memory Management Failure
**Severity:** MEDIUM  
**Tags:** `#llm` `#memory` `#context` `#session-persistence`  

**Error Message:**
```
"Laptop just died mid-session. Please tell me you remember what we were working on?"
AI kept reverting to 'what do you remember' mode
```

**Root Cause:** LLM failed to maintain context across session. Context window overflow not managed.

**Solution:** User-driven context recovery, comprehensive documentation.

**Prevention:**
- Persistent session memory across reconnects
- State file maintenance
- Automatic checkpoint system

---

### ERR-2026-02-24-008: Silent Error Handling
**Severity:** HIGH  
**Tags:** `#silent-errors` `#debugging` `#error-handling` `#logging`  

**Error Message:**
```
Query returned 0 results with no error
2>&1 redirects without checking output
Commands reported success despite failures
```

**Root Cause:** Errors swallowed rather than surfaced.

**Solution:** Comprehensive debug output, enhanced error logging.

**Prevention:**
```bash
# WRONG:
result = run_command("deploy")

# RIGHT:
output=$(some_command 2>&1)
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "ERROR: Command failed with code $exit_code"
    echo "Output: $output"
    # Log to CDO, request user guidance
fi
```

---

## Quick Reference: Error by Severity

### CRITICAL (Production Impact)
| Error ID | Description | Category |
|----------|-------------|----------|
| ERR-2026-02-24-001 | main() Function Corruption | Code/Syntax |
| ERR-2026-02-24-004 | Deployment Disaster | Code/Syntax |
| ERR-2026-02-24-011 | Deployment Verification Failures | Deployment |

### HIGH (Feature/Functionality Impact)
| Error ID | Description | Category |
|----------|-------------|----------|
| ERR-2026-02-24-002 | Query Returns 0 Rooms | Database |
| ERR-2026-02-24-005 | Schema Mismatch | Database |
| ERR-2026-02-27-001 | NumPy Type Conversion | Database |
| ERR-2026-02-24-009 | Local/Server Sync | Deployment |
| ERR-2026-02-24-008 | Silent Error Handling | LLM/AI |
| ERR-2026-02-24-012 | Schema Assumptions | Database |

### MEDIUM (Process/UX Impact)
| Error ID | Description | Category |
|----------|-------------|----------|
| ERR-2026-02-24-003 | Approval Fatigue | Process |
| ERR-2026-02-24-006 | CDO Sub-Agent Failure | Process |
| ERR-2026-02-24-007 | LLM Memory Failure | LLM/AI |
| ERR-2026-02-24-010 | Premature Completion | Process |
| ERR-2026-02-27-002 | Service Initialization | Integration |
| ERR-2026-02-27-003 | Form Field Error | Integration |

---

## Search Index for LLM RAG

### By Error Message
- "can't adapt type 'numpy.int64'" → ERR-2026-02-27-001
- "Query returned 0 rooms" → ERR-2026-02-24-002
- "The app is BROKEN" → ERR-2026-02-24-001, ERR-2026-02-24-004
- "Local works, server doesn't" → ERR-2026-02-24-005, ERR-2026-02-24-009
- "Do I really need to approve this" → ERR-2026-02-24-003
- "CDO sub-agent not running" → ERR-2026-02-24-006

### By Root Cause
- `replace_in_file` → ERR-2026-02-24-001, ERR-2026-02-24-004
- Timezone mismatch → ERR-2026-02-24-002
- Column name mismatch → ERR-2026-02-24-005
- NumPy type conversion → ERR-2026-02-27-001
- Schema assumptions → ERR-2026-02-24-012
- Silent errors → ERR-2026-02-24-008

### By Solution
- Separate file + import → ERR-2026-02-24-001, ERR-2026-02-24-004
- Timezone-aware datetime → ERR-2026-02-24-002
- numpy_type_converter.py → ERR-2026-02-27-001
- Schema-first protocol → ERR-2026-02-24-005, ERR-2026-02-24-012
- Approval levels → ERR-2026-02-24-003

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-02-28  
**CDO Agent:** Active
