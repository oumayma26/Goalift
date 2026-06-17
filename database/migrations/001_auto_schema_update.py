"""
database/migrations/001_auto_schema_update.py
Migration 1 : Auto schema update
Generee automatiquement par schema_detector
"""

import sqlite3
from database.migrations.generator import migration


@migration(1, "Auto schema update")
def _migration_001(cursor: sqlite3.Cursor) -> None:
    """
    Migration auto-generee.
    """
