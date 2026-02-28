# Security Policy for Colab ERP

## Overview

Colab ERP is a Streamlit-based business application handling sensitive booking, inventory, and customer data. This document outlines security practices and reporting procedures.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.2.x   | :white_check_mark: |
| 2.1.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Security Features

### Authentication
- Database-backed bcrypt password hashing
- Role-based access control (RBAC)
- Session management via Streamlit session state
- No plaintext password storage (legacy migration catches plaintext)

### Data Protection
- All database queries use parameterized queries (SQL injection prevention)
- PostgreSQL exclusion constraints prevent double bookings
- Multi-tenancy with TECH/TRAINING divisions
- Audit logging for all agent actions

### Network Security
- Tailscale VPN required for production database access
- Database connections enforce UTC timezone
- PostgreSQL listens on VPN interface only

## Secrets Management

### Required Secrets (secrets.toml)

```toml
[postgres]
host = "YOUR_DB_HOST"
port = 5432
dbname = "colab_erp"
user = "your_db_user"
password = "your_secure_password"
timezone = "Africa/Johannesburg"
```

### Security Rules

1. **NEVER commit secrets.toml to version control**
2. **NEVER log or print credentials**
3. **NEVER hardcode passwords in source code**
4. **Rotate passwords quarterly**
5. **Use strong passwords (16+ characters, mixed case, numbers, symbols)**

## Reporting a Vulnerability

If you discover a security vulnerability, please report it to:

- **Email:** security@colabtechsolutions.co.za
- **Response Time:** Within 48 hours
- **Resolution Time:** Within 14 days for critical issues

### What to Include

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if applicable)
5. Your contact information (optional)

## Security Checklist for Developers

### Before Committing Code

- [ ] No hardcoded passwords or API keys
- [ ] No database dumps in the repository
- [ ] No .env files committed
- [ ] No SSH keys or certificates in the repo
- [ ] secrets.toml is in .gitignore
- [ ] All queries use parameterized statements

### Before Deployment

- [ ] secrets.toml configured on production server
- [ ] Database credentials rotated
- [ ] Tailscale VPN configured and active
- [ ] PostgreSQL configured for SSL connections
- [ ] Firewall rules verified
- [ ] Audit logging enabled

## Current Security Audit Status

**Last Audit:** 2026-02-17
**Status:** :warning: CRITICAL ISSUES FOUND

### Issues Requiring Immediate Attention

1. **Hardcoded credentials in .streamlit/secrets.toml** - MUST be removed from git history
2. **Weak passwords in secrets.toml** - Change all default passwords immediately
3. **Database host exposed** - Verify Tailscale IP is being used

### Remediation Steps

```bash
# 1. Change the exposed passwords immediately
# 2. Remove secrets from git history
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch .streamlit/secrets.toml' \
--prune-empty --tag-name-filter cat -- --all

# 3. Force push to remote
git push origin main --force

# 4. Update credentials on all environments
# 5. Enable branch protection rules on GitHub
```

## Compliance

This application follows:
- POPIA (Protection of Personal Information Act) - South Africa
- GDPR best practices for data handling
- SOC 2 Type II preparation guidelines

## Security Contacts

- **Security Officer:** Shuaib Adams
- **Database Administrator:** [DBA Contact]
- **Infrastructure:** [DevOps Contact]
- **Emergency:** 24/7 On-call rotation

---

**Document Version:** 2.2.0-SECURITY  
**Review Date:** Quarterly  
**Next Review:** 2026-05-17
