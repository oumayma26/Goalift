"""
database/migrations/__init__.py
Système de migrations versionné pour SQLite.
"""

import sqlite3
from typing import Callable, Dict, Tuple
from datetime import datetime


MigrationFn = Callable[[sqlite3.Cursor], None]


MIGRATIONS: Dict[int, Tuple[str, MigrationFn]] = {}


def migration(version: int, description: str) -> Callable[[MigrationFn], MigrationFn]:
    """Décorateur pour enregistrer une migration."""
    def decorator(fn: MigrationFn) -> MigrationFn:
        MIGRATIONS[version] = (description, fn)
        return fn
    return decorator


# ═══════════════════════════════════════════════════
# MIGRATION 001 : Schéma initial
# ═══════════════════════════════════════════════════

@migration(1, "Schéma initial - goals, tasks, vision_board")
def _migration_001(cursor: sqlite3.Cursor) -> None:
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

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_created_at ON goals(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at)")


# ═══════════════════════════════════════════════════
# MIGRATION 002 : Tables habits + habit_logs
# ═══════════════════════════════════════════════════

@migration(2, "Ajout tables habits et habit_logs")
def _migration_002(cursor: sqlite3.Cursor) -> None:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
            task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
            frequency TEXT DEFAULT 'daily'
                CHECK(frequency IN ('daily', 'weekly', 'custom')),
            target_days TEXT,
            color TEXT DEFAULT '#3B82F6',
            icon TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            archived_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            log_date TEXT NOT NULL,
            status TEXT NOT NULL
                CHECK(status IN ('done', 'missed', 'partial')),
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(habit_id, log_date)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habits_task ON habits(task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(habit_id, log_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habits_goal ON habits(goal_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habits_archived ON habits(archived_at)")


# ═══════════════════════════════════════════════════
# MIGRATION 003 : Ajout colonne updated_at à habits
# ═══════════════════════════════════════════════════

@migration(3, "Ajout colonne updated_at à habits")
def _migration_003(cursor: sqlite3.Cursor) -> None:
    """Idempotent : vérifie d'abord si la colonne existe."""
    cursor.execute("PRAGMA table_info(habits)")
    columns = {row[1] for row in cursor.fetchall()}

    if "updated_at" not in columns:
        cursor.execute("""
            ALTER TABLE habits ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        """)


# ═══════════════════════════════════════════════════
# MIGRATION 004 : Ajout colonne reminder_time à habits
# ═══════════════════════════════════════════════════

@migration(4, "Ajout colonne reminder_time à habits")
def _migration_004(cursor: sqlite3.Cursor) -> None:
    cursor.execute("PRAGMA table_info(habits)")
    columns = {row[1] for row in cursor.fetchall()}

    if "reminder_time" not in columns:
        cursor.execute("""
            ALTER TABLE habits ADD COLUMN reminder_time TEXT
        """)


# ═══════════════════════════════════════════════════
# MIGRATION 005 : Ajout table settings (app config)
# ═══════════════════════════════════════════════════

@migration(5, "Ajout table settings pour configuration app")
def _migration_005(cursor: sqlite3.Cursor) -> None:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)


class MigrationRunner:
    """Exécute les migrations de manière sécurisée."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _create_migrations_table(self, cursor: sqlite3.Cursor) -> None:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)

    def _get_current_version(self, cursor: sqlite3.Cursor) -> int:
        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        result = cursor.fetchone()[0]
        return result or 0

    def _backup_database(self) -> str:
        import shutil
        import os

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"

        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, backup_path)

        return backup_path

    def run(self) -> None:
        """Exécute toutes les migrations manquantes."""
        import os

        # Backup avant migration
        if os.path.exists(self.db_path):
            backup_path = self._backup_database()
            print(f"💾 Backup créé : {backup_path}")

        with self._get_connection() as conn:
            cursor = conn.cursor()

            self._create_migrations_table(cursor)
            current_version = self._get_current_version(cursor)

            pending = [v for v in sorted(MIGRATIONS.keys()) if v > current_version]

            if not pending:
                print(f"✅ Base à jour (version {current_version})")
                return

            print(f"🔄 Migrations en attente : {pending}")

            for version in pending:
                description, migration_fn = MIGRATIONS[version]
                print(f"  → Migration {version}: {description}")

                try:
                    migration_fn(cursor)
                    cursor.execute(
                        "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                        (version, description)
                    )
                    conn.commit()
                    print(f"    ✅ Appliquée")
                except Exception as e:
                    conn.rollback()
                    print(f"    ❌ Échec : {e}")
                    raise

            print(f"✅ Base migrée vers version {max(pending)}")


def run_migrations(db_path: str) -> None:
    """Point d'entrée simple."""
    runner = MigrationRunner(db_path)
    runner.run()