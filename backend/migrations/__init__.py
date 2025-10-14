"""
Database migrations for Youth Attendance platform.

This package contains migration scripts for safely updating the database schema
while preserving existing data.

Migration principles:
- ADDITIVE-ONLY: Never drop or rename existing columns/tables
- SAFE DEFAULTS: All new columns have safe default values
- IDEMPOTENT: Migrations can be run multiple times safely
- BACKWARDS COMPATIBLE: Existing code continues to work

Available migrations:
- add_sms_fields_to_persons.py: Adds SMS consent and opt-out fields to persons table
"""

__version__ = "1.0.0"