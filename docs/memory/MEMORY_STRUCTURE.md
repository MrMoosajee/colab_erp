# Memory File Structure & Usage Documentation

**Purpose:** Document the dual memory system structure and usage patterns  
**Location:** `/home/shuaibadams/Projects/colab_erp/docs/memory/`  
**Applies to:** `.cline/` and `.moa_memory/` directories  

---

## 🧠 Overview

The system uses a **dual memory architecture** to preserve context across sessions and model switches:

1. **`.cline/`** - Cline tool state and task history
2. **`.moa_memory/`** - MOA (Master Orchestrator Agent) architectural context

Both systems work together to ensure complete session continuity.

---

## 📁 Memory System 1: .cline/

### Location
`~/.cline/` (in user's home directory)

### Purpose
Cline CLI tool state persistence - managed automatically by Cline

### Structure
```
.cline/
├── data/
│   ├── globalState.json          # Global tool state
│   ├── secrets.json              # Encrypted secrets (if any)
│   ├── cache/                    # Cached data
│   │   ├── cline_recommended_models.json
│   │   └── openrouter_models.json
│   ├── logs/                     # Tool logs
│   │   ├── cline-cli.1.log
│   │   ├── cline-cli.2.log
│   │   └── ...
│   ├── settings/                 # User settings
│   │   └── cline_mcp_settings.json
│   ├── state/                    # Runtime state
│   │   └── taskHistory.json      # ← KEY FILE: Task history
│   ├── tasks/                    # Per-task data
│   │   ├── {task_id}/
│   │   │   ├── api_conversation_history.json
│   │   │   ├── task_metadata.json
│   │   │   ├── ui_messages.json
│   │   │   └── context_history.json
│   │   └── ...
│   └── workspaces/               # Workspace-specific data
│       └── {workspace_id}/
```

### Key Files for LLMs

#### `data/state/taskHistory.json`
**Purpose:** Complete history of all tasks/sessions  
**Format:** JSON array of task objects  
**Usage:** Read to understand recent task context

```json
[
  {
    "id": "1772227193408",
    "ulid": "01KJGFHTJ11VK9VCK1285EXAW1",
    "ts": 1772351872850,
    "task": "Can you help me, I am getting the same issues...",
    "tokensIn": 6741465,
    "tokensOut": 389355,
    "totalCost": 36.88,
    "size": 12529133,
    "cwdOnTaskInitialization": "/home/shuaibadams",
    "modelId": "moonshotai/kimi-k2.5"
  }
]
```

#### `data/tasks/{task_id}/task_metadata.json`
**Purpose:** Metadata for specific task  
**Usage:** Read for detailed task context

#### `data/tasks/{task_id}/api_conversation_history.json`
**Purpose:** Full conversation history  
**Usage:** Read to understand what was discussed

### Usage Pattern
```python
# Read task history for context
import json

task_history_path = Path.home() / ".cline/data/state/taskHistory.json"
with open(task_history_path) as f:
    history = json.load(f)

# Get most recent task
latest_task = history[-1]
print(f"Last task: {latest_task['task'][:100]}")
```

---

## 📁 Memory System 2: .moa_memory/

### Location
`~/.moa_memory/` (in user's home directory)

### Purpose
MOA architectural context - manually maintained for cross-model persistence

### Structure
```
.moa_memory/
├── 00_README.md                   # ← START HERE: Loading instructions
├── 01_architectural_principles.json # Core principles
├── 02_infrastructure.json         # Server connectivity
├── 03_projects_index.json         # 9 projects index
├── 04_colab_erp_structure.json    # Project structure & schema
├── 05_coding_standards.md         # Python coding standards
├── 06_agents_manifest.json        # Agent registry
├── chief_documentation_officer.py # CDO agent implementation
├── future_phases_memory.json      # Phase planning notes
├── load_memory.py                 # Memory loader utility
├── user_roles_requirements.json   # Role definitions
│
├── logs/                          # CDO action logs
│   ├── 2026-02-22.log            # Daily log files
│   ├── 2026-02-27.log
│   ├── 2026-02-22_action_*.json  # Individual action logs
│   ├── 2026-02-23_*.json          # Phase-specific logs
│   └── PHASE_1_COMPLETE_DOCUMENTATION.json
│
├── decisions/                     # HITL decision records
│   ├── 2026-02-22_decision_*.json
│   └── 2026-02-27_decision_*.json
│
├── errors/                        # Error tracking
├── thoughts/                      # Model reasoning logs
├── meetings/                      # User interaction logs
│
└── sessions/                      # Session summaries
    ├── session_2026-02-24_1912.md
    ├── session_2026-02-26_final.md
    └── session_2026-02-27_2332.md
```

### Core Memory Files

#### `00_README.md` (START HERE)
**Purpose:** Loading instructions for future MOA instances  
**Size:** ~5KB  
**Key Content:**
- Memory loading protocol
- File index with descriptions
- Critical rules reminder
- Infrastructure reminder
- Project index summary

**Usage:**
```python
# Always read this first when activating as new MOA instance
with open(Path.home() / ".moa_memory/00_README.md") as f:
    loading_instructions = f.read()
```

#### `01_architectural_principles.json`
**Purpose:** Core architectural rules  
**Format:** JSON  
**Key Content:**
- OOP Mandate (strict)
- Library Structure (main.py orchestration only)
- HITL Gate (absolute)
- Multi-agent protocol

```json
{
  "principles": {
    "oop_mandate": {
      "rule": "ALL logic must be encapsulated in Classes and Objects",
      "prohibition": "No procedural 'scripting' style code",
      "enforcement": "strict"
    },
    "hitl_gate": {
      "rule": "Human-in-the-Loop for ALL decision-making",
      "flow": "THOUGHT -> PROPOSED ACTION -> WAIT FOR AUTH"
    }
  }
}
```

#### `02_infrastructure.json`
**Purpose:** Server connectivity information  
**Format:** JSON  
**Key Content:**
- Tailscale VPN configuration
- SSH access details
- Server specifications

```json
{
  "servers": {
    "colab": {
      "alias": "colab",
      "hostname": "100.69.57.77",
      "user": "colabtechsolutions",
      "auth_method": "ssh_key",
      "identity_file": "~/.ssh/id_ed25519"
    }
  }
}
```

#### `03_projects_index.json`
**Purpose:** Index of all 9 projects  
**Format:** JSON  
**Key Content:**
- Project names and paths
- Completeness status
- Technology stacks
- Missing components

#### `04_colab_erp_structure.json`
**Purpose:** Detailed colab_erp file structure and schema  
**Format:** JSON  
**Key Content:**
- Source file organization
- Database schema details
- Missing implementations

#### `05_coding_standards.md`
**Purpose:** Python coding standards with examples  
**Format:** Markdown  
**Key Content:**
- OOP examples (correct vs prohibited)
- Type hints requirements
- HITL integration patterns
- Error handling standards
- File header templates

#### `06_agents_manifest.json`
**Purpose:** Sub-agents registry  
**Format:** JSON  
**Key Content:**
- CDO-001 (Chief Documentation Officer)
- Future agent definitions

### CDO Directories (Automatic Logging)

#### `logs/` - Action Logs
**Files:**
- `{date}.log` - Daily aggregated logs
- `{date}_action_{timestamp}_{id}.json` - Individual action records

**Format:**
```json
{
  "timestamp": "2026-02-27T19:30:23.367420",
  "agent_id": "CDO-001",
  "category": "action",
  "data": {
    "action_type": "file_write",
    "description": "Updated app.py",
    "metadata": {"lines": 5}
  }
}
```

#### `decisions/` - HITL Decisions
**Files:** `{date}_decision_{timestamp}_{id}.json`

**Format:**
```json
{
  "timestamp": "2026-02-27T19:30:23.367420",
  "agent_id": "CDO-001",
  "category": "decision",
  "data": {
    "decision_id": "docs_ready_for_review",
    "description": "Documentation suite complete",
    "authorized_by": "CDO-001",
    "alternatives": ["Push directly", "Present to MOA"],
    "rationale": "Following HITL protocol"
  }
}
```

#### `errors/` - Error Tracking
**Purpose:** Log errors with full context for debugging

#### `thoughts/` - Model Reasoning
**Purpose:** Capture model thought processes for analysis

#### `meetings/` - User Interactions
**Purpose:** Log user interactions and outcomes

### Session Summaries

#### `sessions/session_2026-02-27_2332.md`
**Purpose:** Comprehensive session summary  
**Content:**
- Session timeline
- Issues resolved
- Testing results
- System status
- Documentation created

---

## 🔄 Memory Loading Protocol

### For New MOA Instances

When you (a new LLM instance) are activated:

1. **Read `~/.moa_memory/00_README.md` first**
   - Understand the memory system
   - Learn loading protocol
   - Review critical rules

2. **Load core JSON files**
   ```python
   memory = {
       'principles': load_json('01_architectural_principles.json'),
       'infrastructure': load_json('02_infrastructure.json'),
       'projects': load_json('03_projects_index.json'),
       'structure': load_json('04_colab_erp_structure.json')
   }
   ```

3. **Read recent session summary**
   - Check `sessions/session_*.md` for latest context
   - Find most recent session by timestamp

4. **Verify SSH connectivity**
   ```bash
   ssh colab "echo 'Connected to colab server'"
   ```

5. **Check git history**
   ```bash
   git -C ~/Projects/colab_erp log --oneline -10
   ```

6. **Read PRD and ARCHITECTURE**
   - Understand current state
   - Know what's implemented

### Quick Loading Code

```python
import json
from pathlib import Path

class MOAMemoryLoader:
    """Loads persistent MOA memory from ~/.moa_memory/"""
    
    MEMORY_DIR = Path.home() / ".moa_memory"
    
    @classmethod
    def load_all(cls) -> dict:
        """Load all memory files. Returns consolidated memory dict."""
        memory = {}
        
        files = [
            "01_architectural_principles.json",
            "02_infrastructure.json",
            "03_projects_index.json",
            "04_colab_erp_structure.json",
            "05_coding_standards.md"
        ]
        
        for filename in files:
            filepath = cls.MEMORY_DIR / filename
            if filepath.exists():
                if filename.endswith('.json'):
                    with open(filepath) as f:
                        memory[filename.replace('.json', '')] = json.load(f)
                else:
                    with open(filepath) as f:
                        memory[filename.replace('.md', '')] = f.read()
        
        return memory
```

---

## 📝 Memory Update Patterns

### When to Update Memory

**Always update when:**
- Major architectural decisions made
- New infrastructure configured
- Project status changes significantly
- New coding standards established
- New agents defined

**Never update without:**
- User authorization (HITL gate)
- Clear rationale documented
- Backups of previous state

### CDO Automatic Logging

The Chief Documentation Officer (CDO) automatically logs:
- All file writes
- All command executions
- All HITL decisions
- All errors with context
- All user interactions

**Usage:**
```python
from chief_documentation_officer import get_cdo

cdo = get_cdo()
cdo.log_action("file_write", "Updated PRD.md", metadata={"lines": 50})
cdo.log_decision("user_authorized", "Deploy to production", authorized_by="shuaibadams")
```

---

## 🎯 Memory Retrieval for Common Scenarios

### Scenario 1: "What do you remember?"
1. Read `00_README.md` for overview
2. Read latest `sessions/session_*.md` for recent context
3. Check `.cline/data/state/taskHistory.json` for task list
4. Read `PRD.md` for current project state

### Scenario 2: "Check the code"
1. Read `04_colab_erp_structure.json` for file organization
2. Read `ARCHITECTURE.md` for system design
3. Check `logs/` for recent changes
4. Verify git log for commits

### Scenario 3: "I'm getting the same issues"
1. Read `logs/errors/` for error patterns
2. Check `CHANGELOG.md` incident log
3. Review `BOOKING_FORM_RESOLUTION_SUMMARY.md`
4. Verify current git commit vs known-good commits

### Scenario 4: "Can we pick up where we left off?"
1. Read latest `sessions/session_*.md`
2. Check `taskHistory.json` for last task
3. Read `DECISION_LOG.md` for pending decisions
4. Verify server status with SSH

---

## ⚠️ Memory Maintenance

### Storage Growth
- Logs grow continuously
- Rotate old logs monthly
- Archive sessions older than 3 months
- Keep only last 100 task entries

### Consistency Checks
- Verify JSON validity monthly
- Check for orphaned references
- Ensure git commits match log entries
- Validate server connectivity

### Backup Strategy
- `.moa_memory/` should be backed up
- `.cline/` is tool-managed (less critical)
- Critical: `01-06` core files
- Important: `sessions/` summaries

---

## 🔗 Integration with Project Documentation

### Cross-References

| Memory File | Project Document | Relationship |
|-------------|------------------|--------------|
| `04_colab_erp_structure.json` | `ARCHITECTURE.md` | Schema details |
| `03_projects_index.json` | `README.md` | Status summary |
| `sessions/session_*.md` | `CHANGELOG.md` | Timeline correlation |
| `logs/decisions/*.json` | `DECISION_LOG.md` | Decision details |

### Documentation Hierarchy

```
MEMORY (Context Preservation)
├── .cline/                     (Tool state)
└── .moa_memory/               (Architectural context)
    ├── Core files (01-06)     (Load first)
    ├── CDO logs               (Automatic)
    └── Sessions               (Summaries)

PROJECT (Current State)
├── docs/memory/               (This documentation)
├── PRD.md                    (Requirements)
├── ARCHITECTURE.md           (Design)
├── README.md                 (Status)
└── CHANGELOG.md              (History)
```

---

## 📊 Memory Statistics

### Current Size (February 2026)

| Category | Files | Size |
|----------|-------|------|
| Core files (01-06) | 6 | ~20KB |
| CDO logs | 20+ | ~50KB |
| Decisions | 2+ | ~5KB |
| Sessions | 3 | ~40KB |
| **Total** | **30+** | **~115KB** |

### Growth Rate
- Logs: ~10KB per week
- Sessions: ~15KB per major session
- Decisions: ~2KB per decision

### Retention Policy
- Logs: 3 months
- Sessions: 6 months
- Core files: Permanent

---

**Document Version:** 1.0.0  
**Created:** Current Session  
**Maintained by:** Chief Documentation Officer (CDO-001)  
**Next Review:** Monthly
