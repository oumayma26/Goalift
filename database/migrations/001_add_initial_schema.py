"""
database/migrations/001_initial_schema.py
Migration 1 : Schéma initial complet — goals, tasks, vision_board, habits, wirds
"""

import sqlite3
from database.migrations.generator import migration


@migration(1, "Schéma initial complet")
def migration_001(cursor: sqlite3.Cursor) -> None:
    """
    Crée toutes les tables du schéma initial.
    Idempotente : IF NOT EXISTS sur toutes les CREATE TABLE.
    """

    # ─── GOALS ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            target_date TEXT,
            priority TEXT NOT NULL DEFAULT 'Moyenne' 
                CHECK(priority IN ('Faible', 'Moyenne', 'Haute')),
            status TEXT NOT NULL DEFAULT 'Non commencé'
                CHECK(status IN ('Non commencé', 'En cours', 'Terminé')),
            color TEXT DEFAULT '#3B82F6',
            image_path TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ─── TASKS ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'À faire'
                CHECK(status IN ('À faire', 'En cours', 'Terminée')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)

    # ─── VISION BOARD ─────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vision_board (
            goal_id INTEGER PRIMARY KEY,
            motivation_text TEXT DEFAULT '',
            pos_x REAL DEFAULT 0,
            pos_y REAL DEFAULT 0,
            width INTEGER DEFAULT 300,
            height INTEGER DEFAULT 220,
            font_size INTEGER DEFAULT 13,
            text_position TEXT DEFAULT 'bottom',
            text_color TEXT DEFAULT '#FFFFFF',
            text_bold INTEGER DEFAULT 1,
            celebrated INTEGER DEFAULT 0,
            FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)

    # ─── VISION BOARD TEXTS ───────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vision_board_texts (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            x REAL DEFAULT 100,
            y REAL DEFAULT 100,
            font_family TEXT DEFAULT 'Arial',
            font_size INTEGER DEFAULT 16,
            bold INTEGER DEFAULT 0,
            italic INTEGER DEFAULT 0,
            color TEXT DEFAULT '#1E293B',
            background TEXT,
            opacity INTEGER DEFAULT 0
        )
    """)

    # ─── VISION BOARD MOOD ────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vision_board_mood (
            id INTEGER PRIMARY KEY,
            image_path TEXT NOT NULL,
            title TEXT DEFAULT '',
            x REAL DEFAULT 100,
            y REAL DEFAULT 100,
            width REAL DEFAULT 280,
            height REAL DEFAULT 190,
            color TEXT DEFAULT '#3B82F6',
            rotation REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ─── HABITS ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            goal_id INTEGER,
            task_id INTEGER,
            frequency TEXT DEFAULT 'daily' CHECK(frequency IN ('daily', 'weekly', 'custom')),
            target_days TEXT,
            color TEXT DEFAULT '#3B82F6',
            icon TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            archived_at TEXT,
            FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
        )
    """)

    # ─── HABIT LOGS ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            log_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('done', 'missed', 'partial')),
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(habit_id, log_date)
        )
    """)

    # ─── WIRDS ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wirds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            icon TEXT DEFAULT '📿',
            color TEXT DEFAULT '#3B82F6',
            schedule_type TEXT DEFAULT 'daily'
                CHECK(schedule_type IN ('daily', 'fajr', 'dhuhr', 'asr', 'maghrib', 'isha', 'custom')),
            target_days TEXT,
            is_template INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            archived_at TEXT
        )
    """)

    # ─── WIRD ITEMS ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wird_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wird_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            icon TEXT DEFAULT '✨',
            target_count INTEGER DEFAULT 1,
            unit TEXT DEFAULT 'fois',
            duration_seconds INTEGER,
            order_index INTEGER DEFAULT 0,
            is_optional INTEGER DEFAULT 0,
            FOREIGN KEY (wird_id) REFERENCES wirds(id) ON DELETE CASCADE
        )
    """)

    # ─── WIRD SESSIONS ────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wird_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wird_id INTEGER NOT NULL,
            session_date TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            total_duration_seconds INTEGER DEFAULT 0,
            items_completed INTEGER DEFAULT 0,
            items_total INTEGER DEFAULT 0,
            status TEXT DEFAULT 'in_progress'
                CHECK(status IN ('in_progress', 'completed', 'abandoned')),
            mood_after INTEGER,
            note TEXT,
            FOREIGN KEY (wird_id) REFERENCES wirds(id) ON DELETE CASCADE
        )
    """)

    # ─── WIRD SESSION LOGS ────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wird_session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            completed_at TEXT,
            actual_count INTEGER DEFAULT 1,
            duration_seconds INTEGER,
            status TEXT DEFAULT 'completed'
                CHECK(status IN ('completed', 'skipped', 'partial')),
            note TEXT,
            FOREIGN KEY (session_id) REFERENCES wird_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES wird_items(id) ON DELETE CASCADE
        )
    """)

    # ─── INDEXES ──────────────────────────────────────
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_created_at ON goals(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habits_task ON habits(task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habits_goal ON habits(goal_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habits_archived ON habits(archived_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(habit_id, log_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wirds_active ON wirds(is_active, archived_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wird_items_wird ON wird_items(wird_id, order_index)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wird_sessions_date ON wird_sessions(wird_id, session_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wird_session_logs ON wird_session_logs(session_id, item_id)")